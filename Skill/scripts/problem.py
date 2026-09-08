"""题目模块：info（标签/难度） / search（按标签与难度筛题）。"""
import argparse
import sys
from typing import Optional

from core import api_get, out, parse_problem_id, problem_brief


def _fetch_problemset(tags: Optional[list]) -> tuple:
    """拉取题库（可选按 tag 服务端过滤以减小响应），返回 (problems, 统计表)。"""
    params = {"tags": ";".join(tags)} if tags else None
    data = api_get("problemset.problems", params)
    problems = data.get("problems") or []
    stats = {
        (s.get("contestId"), s.get("index")): s.get("solvedCount")
        for s in data.get("problemStatistics") or []
    }
    return problems, stats


def cmd_problem_info(args: argparse.Namespace) -> None:
    """查询指定题目的标签与难度。"""
    contest_id, index = parse_problem_id(args.problem_id)
    problems, stats = _fetch_problemset(None)
    key = (contest_id, index)
    p = next(
        (p for p in problems if (p.get("contestId"), p.get("index")) == key), None
    )
    if p is None:
        sys.stderr.write(f"题库中未找到题目 {contest_id}{index}\n")
        sys.exit(1)
    info = problem_brief(p, stats.get(key))
    if args.human:
        pid = f"{info['contestId']}/{info['index']}"
        rating = info["rating"] if info["rating"] is not None else "未定级"
        print(f"{pid}  {info['name']}")
        print(f"难度: {rating}  通过人数: {info['solvedCount']}")
        print(f"标签: {', '.join(info['tags']) or '-'}")
        return
    out(info)


def cmd_problem_search(args: argparse.Namespace) -> None:
    """按标签与难度区间筛题（tag 在服务端过滤，rating 在本地过滤）。"""
    problems, stats = _fetch_problemset(args.tag)
    matched = []
    for p in problems:
        rating = p.get("rating")
        if args.min_rating is not None and (rating is None or rating < args.min_rating):
            continue
        if args.max_rating is not None and (rating is None or rating > args.max_rating):
            continue
        matched.append(problem_brief(p, stats.get((p.get("contestId"), p.get("index")))))
    matched.sort(key=lambda p: (p["rating"] is None, p["rating"] or 0, p["contestId"] or 0))
    data = {
        "total": len(matched),
        "truncated": len(matched) > args.limit,
        "problems": matched[: args.limit],
    }
    if args.human:
        tail = f"（已截断，共 {data['total']}）" if data["truncated"] else ""
        print(f"筛选出 {data['total']} 题{tail}:")
        for p in data["problems"]:
            pid = f"{p['contestId']}/{p['index']}" if p["contestId"] else p["index"]
            rating = p["rating"] if p["rating"] is not None else "-"
            print(f"  {pid:12} {p['name']}  (rating {rating}, 通过 {p['solvedCount']})")
        return
    out(data)


def register_problem(sub: argparse._SubParsersAction) -> None:
    p_prob = sub.add_parser("problem", help="题目查询")
    prob_sub = p_prob.add_subparsers(dest="subcommand", required=True)

    p_pinfo = prob_sub.add_parser("info", help="查询题目的标签与难度")
    p_pinfo.add_argument("problem_id", help="题目ID，如 2185A")
    p_pinfo.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_pinfo.set_defaults(func=cmd_problem_info)

    p_psearch = prob_sub.add_parser("search", help="按标签与难度筛选题目")
    p_psearch.add_argument("--tag", action="append",
                           help="标签过滤，可多次出现（如 --tag dp --tag greedy）")
    p_psearch.add_argument("--min-rating", type=int, help="难度下限（含）")
    p_psearch.add_argument("--max-rating", type=int, help="难度上限（含）")
    p_psearch.add_argument("--limit", type=int, default=20, help="最多返回 N 题，默认 20")
    p_psearch.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_psearch.set_defaults(func=cmd_problem_search)
