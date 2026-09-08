"""用户模块：info / rating / submissions / problem / friends。"""
import argparse
import sys
from collections import Counter
from typing import Optional

from core import (
    api_get, decode_source, fmt_unix, out, parse_problem_id,
    rating_str, require_handle,
)


def cmd_user_info(args: argparse.Namespace) -> None:
    handle = require_handle(args.handle)
    result = api_get("user.info", {"handles": handle})
    u = result[0]
    data = {
        "handle": u.get("handle"),
        "rating": u.get("rating"),
        "rank": u.get("rank"),
        "maxRating": u.get("maxRating"),
        "maxRank": u.get("maxRank"),
        "contribution": u.get("contribution"),
        "organization": u.get("organization"),
        "friendOfCount": u.get("friendOfCount"),
        "lastOnlineTimeSeconds": u.get("lastOnlineTimeSeconds"),
        "registrationTimeSeconds": u.get("registrationTimeSeconds"),
    }
    if args.human:
        print(f"handle: {data['handle']}")
        print(f"rating: {rating_str(data['rating'], data['rank'])}")
        print(f"max:    {rating_str(data['maxRating'], data['maxRank'])}")
        print(f"contribution: {data['contribution']}")
        print(f"organization: {data['organization'] or '-'}")
        return
    out({"handle": handle, "user": data})


def cmd_user_rating(args: argparse.Namespace) -> None:
    handle = require_handle(args.handle)
    changes = api_get("user.rating", {"handle": handle})
    data = {
        "handle": handle,
        "total": len(changes),
        "changes": [
            {
                "contestId": c.get("contestId"),
                "contestName": c.get("contestName"),
                "rank": c.get("rank"),
                "oldRating": c.get("oldRating"),
                "newRating": c.get("newRating"),
                "delta": c.get("newRating", 0) - c.get("oldRating", 0),
                "ratingUpdateTimeSeconds": c.get("ratingUpdateTimeSeconds"),
            }
            for c in changes
        ],
    }
    if args.human:
        print(f"{handle} 共 {data['total']} 场")
        for c in data["changes"]:
            date = fmt_unix(c["ratingUpdateTimeSeconds"])
            print(f"{date}  {c['contestName']}  rank {c['rank']!s:>4}: "
                  f"{c['oldRating']} -> {c['newRating']} ({c['delta']:+d})")
        return
    out(data)


def cmd_user_submissions(args: argparse.Namespace) -> None:
    handle = require_handle(args.handle)
    rows = api_get("user.status", {"handle": handle, "from": 1, "count": args.count})

    # 统计基于拉取到的提交集合
    solved: dict[tuple, dict] = {}
    verdict_stats: Counter = Counter()
    language_stats: Counter = Counter()
    for s in rows:
        verdict = s.get("verdict")
        verdict_stats[verdict] += 1
        language_stats[s.get("programmingLanguage")] += 1
        if verdict == "OK":
            p = s.get("problem", {})
            key = (p.get("contestId"), p.get("index"))
            if key not in solved:
                solved[key] = {
                    "contestId": p.get("contestId"),
                    "index": p.get("index"),
                    "name": p.get("name"),
                    "rating": p.get("rating"),
                }

    recent = [
        {
            "id": s.get("id"),
            "timeSeconds": s.get("creationTimeSeconds"),
            "verdict": s.get("verdict"),
            "language": s.get("programmingLanguage"),
            "problem": {
                "contestId": s.get("problem", {}).get("contestId"),
                "index": s.get("problem", {}).get("index"),
                "name": s.get("problem", {}).get("name"),
            },
        }
        for s in rows[: args.recent]
    ]

    solved_list = sorted(solved.values(), key=lambda p: (p["contestId"] or 0, p["index"] or ""))
    data = {
        "handle": handle,
        "scanned": len(rows),
        "accepted": verdict_stats.get("OK", 0),
        "uniqueSolved": len(solved_list),
        "solvedTotal": len(solved_list),
        "solvedTruncated": len(solved_list) > args.solved_limit,
        "solved": solved_list[: args.solved_limit],
        "verdictStats": dict(verdict_stats),
        "languageStats": dict(language_stats),
        "recent": recent,
    }
    if args.human:
        print(f"{handle} 最近 {data['scanned']} 条提交:")
        print(f"通过提交: {data['accepted']}  不同题数: {data['uniqueSolved']}")
        if data["solvedTruncated"]:
            print(f"已做题目（前 {args.solved_limit} / 共 {data['uniqueSolved']}）:")
        else:
            print("已做题目:")
        for p in data["solved"]:
            pid = f"{p['contestId']}/{p['index']}" if p["contestId"] else p["index"]
            rating = p["rating"] if p["rating"] is not None else "-"
            print(f"  {pid:12} {p['name']}  (rating {rating})")
        top_langs = sorted(
            data["languageStats"].items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        if top_langs:
            print("常用语言: " + ", ".join(f"{k} x{v}" for k, v in top_langs))
        print("最近提交:")
        for s in data["recent"]:
            pid = s["problem"]
            label = f"{pid['contestId']}/{pid['index']}" if pid["contestId"] else pid["index"]
            print(f"  [{str(s['verdict']):15}] #{s['id']} {label} {pid['name']} ({s['language']})")
        return
    out(data)


def cmd_user_problem(args: argparse.Namespace) -> None:
    """按题目查提交记录；--source 附带该题最近一次 AC（或最近提交）的源码。

    多步骤整合：解析题目标识 → 扫描提交匹配该题 → （可选）复用扫描结果
    的行号，精确取一条带源码的提交，避免全量源码下载。
    """
    handle = require_handle(args.handle)
    contest_id, index = parse_problem_id(args.problem_id)

    rows = api_get("user.status", {"handle": handle, "from": 1, "count": args.count})
    hits = [
        {
            "id": s.get("id"),
            "timeSeconds": s.get("creationTimeSeconds"),
            "verdict": s.get("verdict"),
            "language": s.get("programmingLanguage"),
            "passedTestCount": s.get("passedTestCount"),
        }
        for s in rows
        if (s.get("problem", {}).get("contestId") == contest_id
            and (s.get("problem", {}).get("index") or "").upper() == index)
    ]
    if not hits:
        # 没做过这题：返回空结果而非报错，便于 agent 判断
        if args.human:
            print(f"{handle} 没有题目 {contest_id}{index} 的提交记录")
            return
        out({
            "handle": handle,
            "problem": {"contestId": contest_id, "index": index},
            "total": 0,
            "submissions": [],
        })
        return

    data = {
        "handle": handle,
        "problem": {"contestId": contest_id, "index": index},
        "total": len(hits),
        "submissions": hits,
    }
    if args.source:
        # 优先最近一次 AC，否则最近一次提交；用行号精确取一条源码
        target_id = next((h["id"] for h in hits if h["verdict"] == "OK"), hits[0]["id"])
        idx = next(i for i, s in enumerate(rows) if s.get("id") == target_id)
        src = api_get("user.status", {
            "handle": handle, "from": idx + 1, "count": 1, "includeSources": "true",
        })[0]
        p = src.get("problem", {})
        data["source"] = {
            "id": src.get("id"),
            "verdict": src.get("verdict"),
            "language": src.get("programmingLanguage"),
            "problem": {
                "contestId": p.get("contestId"),
                "index": p.get("index"),
                "name": p.get("name"),
            },
            "code": decode_source(src),
        }

    if args.human:
        print(f"{handle} 在 {contest_id}{index} 上共 {data['total']} 次提交:")
        for h in data["submissions"]:
            print(f"  #{h['id']}  {fmt_unix(h['timeSeconds'])}  "
                  f"{str(h['verdict']):17} {h['language']}")
        if args.source:
            s = data["source"]
            pid = f"{s['problem']['contestId']}/{s['problem']['index']}"
            print(f"\n----- 源码（#{s['id']} {pid} {s['problem']['name']} "
                  f"{s['verdict']} {s['language']}）-----")
            print(s["code"])
        return
    out(data)


def cmd_user_friends(args: argparse.Namespace) -> None:
    """好友列表为私有数据，需已配置 API key/secret。"""
    params = {"onlyOnline": "true" if args.only_online else "false"}
    friends = api_get("user.friends", params)
    data = {"total": len(friends), "handles": friends}
    if args.human:
        suffix = "（仅在线）" if args.only_online else ""
        print(f"共 {data['total']} 个好友{suffix}")
        for h in data["handles"]:
            print(f"  {h}")
        return
    out(data)


def register_user(sub: argparse._SubParsersAction) -> None:
    p_user = sub.add_parser("user", help="用户查询")
    u_sub = p_user.add_subparsers(dest="subcommand", required=True)

    p_info = u_sub.add_parser("info", help="查询用户基本信息")
    p_info.add_argument("--handle", help="指定用户名（默认取已绑定用户）")
    p_info.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_info.set_defaults(func=cmd_user_info)

    p_rating = u_sub.add_parser("rating", help="查询 rating 历史")
    p_rating.add_argument("--handle", help="指定用户名（默认取已绑定用户）")
    p_rating.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_rating.set_defaults(func=cmd_user_rating)

    p_sub = u_sub.add_parser("submissions", help="查询提交记录、统计与已做题目")
    p_sub.add_argument("--handle", help="指定用户名（默认取已绑定用户）")
    p_sub.add_argument("--count", type=int, default=500,
                       help="拉取最近 N 条提交做统计，默认 500")
    p_sub.add_argument("--recent", type=int, default=10,
                       help="附带最近 N 条提交详情，默认 10")
    p_sub.add_argument("--solved-limit", type=int, default=50,
                       help="已做题目清单最多列 N 题，默认 50")
    p_sub.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_sub.set_defaults(func=cmd_user_submissions)

    p_problem = u_sub.add_parser("problem", help="按题目查提交记录（--source 附带该题最近 AC 源码）")
    p_problem.add_argument("problem_id", help="题目ID，如 2185A")
    p_problem.add_argument("--source", action="store_true", help="附带该题最近一次 AC（或最近提交）的源码")
    p_problem.add_argument("--count", type=int, default=500,
                           help="在最近 N 条提交内搜索该题，默认 500")
    p_problem.add_argument("--handle", help="指定用户名（默认取已绑定用户）")
    p_problem.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_problem.set_defaults(func=cmd_user_problem)

    p_friends = u_sub.add_parser("friends", help="查询好友列表（需已配置 API 签名）")
    p_friends.add_argument("--only-online", action="store_true", help="仅显示在线好友")
    p_friends.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_friends.set_defaults(func=cmd_user_friends)
