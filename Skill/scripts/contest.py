"""比赛模块：upcoming（未开始） / problems（某场比赛的题目列表）。"""
import argparse
import datetime

from core import ApiError, api_get, out, problem_brief


def cmd_contest_upcoming(args: argparse.Namespace) -> None:
    """查询接下来还未开始的比赛。"""
    contests = api_get("contest.list")
    upcoming = sorted(
        (c for c in contests if c.get("phase") == "BEFORE"),
        key=lambda c: c.get("startTimeSeconds") or 0,
    )[: args.limit]
    data = {
        "total": len(upcoming),
        "contests": [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "startTimeSeconds": c.get("startTimeSeconds"),
                "durationSeconds": c.get("durationSeconds"),
                "type": c.get("type"),
            }
            for c in upcoming
        ],
    }
    if args.human:
        if not data["contests"]:
            print("近期没有未开始的比赛")
            return
        for c in data["contests"]:
            start = datetime.datetime.fromtimestamp(c["startTimeSeconds"])
            hours = c["durationSeconds"] // 3600
            print(f"[{c['id']}] {c['name']}")
            print(f"    开始: {start:%Y-%m-%d %H:%M}  时长: {hours} 小时  赛制: {c['type']}")
        return
    out(data)


def cmd_contest_problems(args: argparse.Namespace) -> None:
    """查询某场比赛的题目列表（含标签与难度）。

    contest.standings 的 rows（榜单行）数据量巨大，这里只取 contest 概要
    与 problems 列表，丢弃 rows 以控制输出大小。
    """
    params = {"contestId": str(args.contest_id)}
    try:
        data = api_get("contest.standings", params)
    except ApiError:
        # 公开比赛仅支持"仅 contestId 一个参数"的匿名请求，签名请求可能被拒
        data = api_get("contest.standings", params, anon=True)
    c = data.get("contest") or {}
    problems = data.get("problems") or []
    result = {
        "contest": {
            "id": c.get("id"),
            "name": c.get("name"),
            "phase": c.get("phase"),
            "type": c.get("type"),
            "durationSeconds": c.get("durationSeconds"),
        },
        "total": len(problems),
        "problems": [problem_brief(p) for p in problems],
    }
    if args.human:
        print(f"[{result['contest']['id']}] {result['contest']['name']} "
              f"({result['contest']['phase']}, {result['contest']['type']})")
        print(f"共 {result['total']} 题:")
        for p in result["problems"]:
            rating = p["rating"] if p["rating"] is not None else "-"
            print(f"  {p['index']:3} {p['name']}  (rating {rating})")
            if p["tags"]:
                print(f"      标签: {', '.join(p['tags'])}")
        return
    out(result)


def register_contest(sub: argparse._SubParsersAction) -> None:
    p_contest = sub.add_parser("contest", help="比赛查询")
    c_sub = p_contest.add_subparsers(dest="subcommand", required=True)

    p_upcoming = c_sub.add_parser("upcoming", help="查询接下来还未开始的比赛")
    p_upcoming.add_argument("--limit", type=int, default=10, help="最多返回 N 场，默认 10")
    p_upcoming.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_upcoming.set_defaults(func=cmd_contest_upcoming)

    p_cproblems = c_sub.add_parser("problems", help="查询某场比赛的题目列表")
    p_cproblems.add_argument("contest_id", type=int, help="比赛 ID（如 566）")
    p_cproblems.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_cproblems.set_defaults(func=cmd_contest_problems)
