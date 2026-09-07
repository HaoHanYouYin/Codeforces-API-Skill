#!/usr/bin/env python3
"""Codeforces API 命令行工具入口（薄壳：只做分发）。

内核在 core.py，四个业务模块：user.py / problem.py / contest.py / submission.py。

统一规则：
- 成功结果输出 JSON 到 stdout；错误信息输出到 stderr 且退出码非 0
- 所有命令支持 --human 输出人类可读文本
- 需要用户名的命令，--handle 优先，否则读取已绑定的 config/user.json

用法示例：
    python cf.py bind <handle>
    python cf.py credentials --key <key> --secret <secret>
    python cf.py user info [--handle x] [--human]
    python cf.py user rating [--handle x] [--human]
    python cf.py user submissions [--handle x] [--count n] [--recent n] [--solved-limit n] [--human]
    python cf.py user problem <题目ID> [--source] [--human]        # 如 2185A
    python cf.py user friends [--only-online] [--human]
    python cf.py problem info <题目ID> [--human]                    # 标签与难度
    python cf.py problem search [--tag t]... [--min-rating n] [--max-rating n] [--limit n] [--human]
    python cf.py contest upcoming [--limit n] [--human]
    python cf.py contest problems <contestId> [--human]
    python cf.py submission code <submission_id> [--depth n] [--human]
    python cf.py recommend unsolved [--tag t]... [--min-rating a] [--max-rating b] [--min-contest k] [--limit n] [--human]
    python cf.py recommend solved   [--tag t]... [--min-rating a] [--max-rating b] [--min-contest k] [--limit n] [--human]
    python cf.py recommend pick [-n 缺省 --count n] [--input 候选集.json] [--human]   # 从 stdin 或文件随机抽 n 道
"""
import argparse
import sys

import contest
import core
import problem
import recommend
import submission
import user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cf.py", description="Codeforces API 命令行工具（支持匿名与签名访问）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    core.register_core(sub)
    user.register_user(sub)
    problem.register_problem(sub)
    contest.register_contest(sub)
    submission.register_submission(sub)
    recommend.register_recommend(sub)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except core.ApiError as exc:
        sys.stderr.write(f"cf.py: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
