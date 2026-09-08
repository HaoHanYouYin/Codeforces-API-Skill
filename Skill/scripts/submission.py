"""提交模块：code（按提交 ID 获取源码）。"""
import argparse
import sys

from core import api_get, decode_source, out, require_handle


def cmd_submission_code(args: argparse.Namespace) -> None:
    """按提交 ID 获取源码（两阶段拉取，避免全量源码下载）。

    官方 API 没有按 ID 定向返回提交的方法。提交按 id 降序返回，因此：
    1. 先不带源码扫描最近 N 条（--depth），定位目标提交的行号；
    2. 按 from=行号&count=1 精确取那一条带源码，数据量最小。
    """
    handle = require_handle(args.handle)
    rows = api_get("user.status", {
        "handle": handle, "from": 1, "count": args.depth,
    })
    idx = next(
        (i for i, s in enumerate(rows) if s.get("id") == args.submission_id), None
    )
    if idx is None:
        sys.stderr.write(
            f"未找到提交 {args.submission_id}（最近 {len(rows)} 条内没有，"
            f"可用 --depth 扩大扫描范围）\n"
        )
        sys.exit(1)
    target = api_get("user.status", {
        "handle": handle,
        "from": idx + 1,
        "count": 1,
        "includeSources": "true",
    })[0]
    p = target.get("problem", {})
    data = {
        "id": target.get("id"),
        "timeSeconds": target.get("creationTimeSeconds"),
        "verdict": target.get("verdict"),
        "language": target.get("programmingLanguage"),
        "problem": {
            "contestId": p.get("contestId"),
            "index": p.get("index"),
            "name": p.get("name"),
        },
        "source": decode_source(target),
    }
    if args.human:
        pid = f"{data['problem']['contestId']}/{data['problem']['index']}"
        print(f"#{data['id']}  {pid} {data['problem']['name']}")
        print(f"verdict: {data['verdict']}  language: {data['language']}")
        print("----- 源码 -----")
        print(data["source"])
        return
    out(data)


def register_submission(sub: argparse._SubParsersAction) -> None:
    p_submission = sub.add_parser("submission", help="提交查询")
    s_sub = p_submission.add_subparsers(dest="subcommand", required=True)

    p_code = s_sub.add_parser("code", help="按提交 ID 获取源码（需已配置 API 签名）")
    p_code.add_argument("submission_id", type=int, help="提交 ID（来自 user submissions 的 recent.id）")
    p_code.add_argument("--depth", type=int, default=100,
                        help="在最近 N 条提交内扫描目标，默认 100")
    p_code.add_argument("--handle", help="指定用户名（默认取已绑定用户）")
    p_code.add_argument("--human", action="store_true", help="输出人类可读文本")
    p_code.set_defaults(func=cmd_submission_code)
