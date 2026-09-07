"""复合模块 recommend：结合用户做题记录与题库标签/难度筛选，支持随机抽取。

- recommend unsolved —— 带指定标签(任一)/难度区间 [a,b]/序号下限 k 且 未做过的题
- recommend solved   —— 同上，但仅保留 做过的题
- recommend pick     —— 从候选集（stdin 或 --input JSON）随机抽取 n 道

候选集 JSON 约定：dict 含 "problems" 列表（unsolved/solved 的输出格式），
或直接为问题对象列表。
"""
import argparse
import json
import random
import sys

from core import api_get, out, problem_brief, require_handle


def _fetch_problems_with_stats() -> tuple:
    """拉取全量题库与统计表。标签 OR 匹配需在本地过滤（服务端仅支持 AND）。"""
    data = api_get("problemset.problems")
    problems = data.get("problems") or []
    stats = {
        (s.get("contestId"), (s.get("index") or "").upper()): s.get("solvedCount")
        for s in data.get("problemStatistics") or []
    }
    return problems, stats


def _fetch_solved(handle: str, count: int) -> set:
    """扫描用户最近 count 条提交，返回已 AC 题目 (contestId, index) 集合。"""
    rows = api_get("user.status", {"handle": handle, "from": 1, "count": count})
    solved = set()
    for s in rows:
        if s.get("verdict") == "OK":
            p = s.get("problem", {})
            solved.add((p.get("contestId"), (p.get("index") or "").upper()))
    return solved


def _filter_problems(problems, tags, min_rating, max_rating, min_contest) -> list:
    """本地过滤：任一标签匹配 / 难度区间 / 序号(场次号)下限。"""
    want = {t for t in tags if t} if tags else None
    matched = []
    for p in problems:
        rating = p.get("rating")
        cid = p.get("contestId")
        if min_rating is not None and (rating is None or rating < min_rating):
            continue
        if max_rating is not None and (rating is None or rating > max_rating):
            continue
        if min_contest is not None and (cid or 0) < min_contest:
            continue
        if want and not (set(p.get("tags") or []) & want):
            continue
        key = (cid, (p.get("index") or "").upper())
        matched.append((key, p))
    return matched


def _run_query(args, want_solved: bool) -> None:
    """unsolved / solved 共同实现：筛选后按做没做过取子集。"""
    handle = require_handle(args.handle)
    problems, stats = _fetch_problems_with_stats()
    solved = _fetch_solved(handle, args.count)

    matched = _filter_problems(
        problems, args.tag, args.min_rating, args.max_rating, args.min_contest
    )
    briefs = [
        problem_brief(p, stats.get(key))
        for key, p in matched
        if (key in solved) == want_solved
    ]

    briefs.sort(key=lambda b: (b["rating"] is None, b["rating"] or 0,
                               b["contestId"] or 0))
    data = {
        "handle": handle,
        "mode": "solved" if want_solved else "unsolved",
        "total": len(briefs),
        "truncated": len(briefs) > args.limit,
        "problems": briefs[: args.limit],
    }
    if args.human:
        tail = f"（已截断，共 {data['total']}）" if data["truncated"] else ""
        label = "做过的" if want_solved else "未做过的"
        print(f"{handle} 符合条件的{label}题 {data['total']} 道{tail}:")
        for b in data["problems"]:
            pid = f"{b['contestId']}/{b['index']}"
            rating = b["rating"] if b["rating"] is not None else "-"
            print(f"  {pid:12} {b['name']}  (rating {rating}, 通过 {b['solvedCount']})")
        return
    out(data)


def cmd_recommend_unsolved(args: argparse.Namespace) -> None:
    _run_query(args, want_solved=False)


def cmd_recommend_solved(args: argparse.Namespace) -> None:
    _run_query(args, want_solved=True)


def cmd_recommend_pick(args: argparse.Namespace) -> None:
    """从候选集随机抽 n 道；候选集读自 --input 文件或 stdin JSON。"""
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = json.load(sys.stdin)
    problems = raw.get("problems", raw) if isinstance(raw, dict) else raw
    if not isinstance(problems, list):
        sys.stderr.write('候选集格式错误：需要 {"problems": [...]} 或问题列表\n')
        sys.exit(1)

    n = min(args.count, len(problems))
    picked = random.sample(problems, n)
    picked.sort(key=lambda b: (b.get("rating") is None, b.get("rating") or 0,
                               b.get("contestId") or 0))
    data = {"total": len(problems), "count": n, "picked": picked}
    if args.human:
        if n < len(problems):
            print(f"从 {data['total']} 道候选中随机抽出 {n} 道:")
        else:
            print(f"候选仅 {data['total']} 道，全部抽出:")
        for b in data["picked"]:
            pid = f"{b['contestId']}/{b['index']}"
            rating = b["rating"] if b.get("rating") is not None else "-"
            print(f"  {pid:12} {b.get('name')}  (rating {rating})")
        return
    out(data)


def register_recommend(sub: argparse._SubParsersAction) -> None:
    p_rec = sub.add_parser("recommend", help="复合筛选：标签/难度/序号+做题状态，随机抽取")
    rec_sub = p_rec.add_subparsers(dest="subcommand", required=True)

    def _add_query_args(p) -> None:
        p.add_argument("--tag", action="append",
                       help="标签过滤（任一匹配，可多次，如 --tag greedy --tag dp）")
        p.add_argument("--min-rating", type=int, help="难度下限 a（含）")
        p.add_argument("--max-rating", type=int, help="难度上限 b（含）")
        p.add_argument("--min-contest", type=int, help="题目序号下限 k（场次号 >= k）")
        p.add_argument("--limit", type=int, default=20, help="最多返回 N 题，默认 20")
        p.add_argument("--count", type=int, default=2000,
                       help="扫描用户最近 N 条提交判定做题状态，默认 2000")
        p.add_argument("--handle", help="指定用户名（默认取已绑定用户）")
        p.add_argument("--human", action="store_true")

    p_u = rec_sub.add_parser("unsolved", help="符合条件的未做题")
    _add_query_args(p_u)
    p_u.set_defaults(func=cmd_recommend_unsolved)

    p_s = rec_sub.add_parser("solved", help="符合条件的已做题")
    _add_query_args(p_s)
    p_s.set_defaults(func=cmd_recommend_solved)

    p_pick = rec_sub.add_parser("pick", help="从候选集（stdin 或 --input 文件 JSON）随机抽 n 道")
    p_pick.add_argument("--count", type=int, default=3, help="抽取数量 n，默认 3")
    p_pick.add_argument("--input", help="候选集 JSON 文件路径（缺省从 stdin 读）")
    p_pick.add_argument("--human", action="store_true")
    p_pick.set_defaults(func=cmd_recommend_pick)