"""内核：请求、签名、限速、绑定与共享工具。

统一规则：
- 跨进程 2 秒限速（config/.rate_limit 时间戳文件），防止 "Call limit exceeded"
- 已配置 key/secret 时自动 apiSig 签名，否则匿名访问
- 成功结果输出 JSON 到 stdout；错误信息输出到 stderr 且退出码非 0
"""
import argparse
import base64
import datetime
import hashlib
import json
import pathlib
import random
import re
import string
import sys
import time
from typing import Any, Optional

import requests

BASE_URL = "https://codeforces.com/api"
API_MIN_INTERVAL = 2.0  # 官方限速：每 2 秒最多 1 次请求

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
USER_FILE = CONFIG_DIR / "user.json"
RATE_FILE = CONFIG_DIR / ".rate_limit"  # 跨进程限速用的时间戳文件
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"  # API key/secret（明文，后续再加保护）


class ApiError(Exception):
    """Codeforces API 返回错误（status == FAILED）或网络错误。"""


# ---------------------------------------------------------------- 限速

def _rate_limit() -> None:
    """保证两次请求间隔不小于 2 秒。

    用 config/.rate_limit 时间戳文件做跨进程限速：agent 每次调用都是
    新进程，若只用进程内变量，连续调用会绕过官方 2 秒限制。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        last = float(RATE_FILE.read_text(encoding="ascii").strip() or 0)
    except (OSError, ValueError):
        last = 0.0
    wait = last + API_MIN_INTERVAL - time.time()
    if wait > 0:
        time.sleep(wait)
    RATE_FILE.write_text(str(time.time()), encoding="ascii")


# ---------------------------------------------------------------- 签名与请求

def _sign(method: str, params: dict, key: str, secret: str) -> dict:
    """生成带 apiSig 签名的请求参数（规范见 reference/Introduction.md）。"""
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    now = str(int(time.time()))
    signed = dict(params)
    signed["apiKey"] = key
    signed["time"] = now
    # 先按参数名、再按参数值字典序排序后拼接
    items = sorted(signed.items(), key=lambda kv: (str(kv[0]), str(kv[1])))
    query = "&".join(f"{k}={v}" for k, v in items)
    digest = hashlib.sha512(f"{rand}/{method}?{query}#{secret}".encode()).hexdigest()
    signed["apiSig"] = rand + digest
    return signed


def load_credentials() -> Optional[tuple]:
    """读取 config/credentials.json；未配置或配置损坏时返回 None。"""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        key, secret = data.get("key"), data.get("secret")
        return (key, secret) if key and secret else None
    except (ValueError, OSError):
        return None


def api_get(method: str, params: Optional[dict] = None, anon: bool = False) -> Any:
    """调用指定方法并返回 result，失败时抛出 ApiError。

    若已配置 key/secret，自动带 apiSig 签名（可访问当前账号私有数据）；
    否则以匿名身份请求，只能访问公开数据。anon=True 强制匿名（个别方法
    只接受仅含业务参数的匿名请求）。
    """
    _rate_limit()
    creds = None if anon else load_credentials()
    if creds:
        params = _sign(method, params or {}, creds[0], creds[1])
    try:
        resp = requests.get(f"{BASE_URL}/{method}", params=params, timeout=60)
        data = resp.json()
    except requests.RequestException as exc:
        raise ApiError(f"请求失败: {exc}") from exc
    except ValueError as exc:
        raise ApiError(f"无法解析响应 (HTTP {resp.status_code})") from exc
    if data.get("status") != "OK":
        raise ApiError(data.get("comment") or "未知错误")
    return data["result"]


# ---------------------------------------------------------------- 绑定管理

def load_bound_handle() -> Optional[str]:
    """读取已绑定的用户名；未绑定或文件损坏时返回 None。"""
    if USER_FILE.exists():
        try:
            return json.loads(USER_FILE.read_text(encoding="utf-8")).get("handle")
        except (ValueError, OSError):
            return None
    return None


def require_handle(cli_handle: Optional[str]) -> str:
    """取用户名：--handle 优先，否则回退到绑定；都没有则提示并退出。"""
    handle = cli_handle or load_bound_handle()
    if not handle:
        sys.stderr.write("未绑定用户：请先运行 python cf.py bind <handle>\n")
        sys.exit(1)
    return handle


def out(obj: Any) -> None:
    """向 stdout 输出 JSON 结果。"""
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- 命令：bind / credentials

def cmd_bind(args: argparse.Namespace) -> None:
    handle = args.handle.strip()
    if not handle:
        sys.stderr.write("用户名不能为空\n")
        sys.exit(1)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_FILE.write_text(
        json.dumps({"handle": handle}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    out({"status": "OK", "handle": handle})


def cmd_credentials(args: argparse.Namespace) -> None:
    """保存/更新 API key 与 secret（明文写入 config/credentials.json）。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(
        json.dumps({"key": args.key, "secret": args.secret}, indent=2),
        encoding="utf-8",
    )
    out({"status": "OK", "message": "凭据已保存"})


def register_core(sub: argparse._SubParsersAction) -> None:
    p_bind = sub.add_parser("bind", help="绑定/改绑 Codeforces 用户名")
    p_bind.add_argument("handle")
    p_bind.set_defaults(func=cmd_bind)

    p_cred = sub.add_parser("credentials", help="保存/更新 API key 与 secret")
    p_cred.add_argument("--key", required=True)
    p_cred.add_argument("--secret", required=True)
    p_cred.set_defaults(func=cmd_credentials)


# ---------------------------------------------------------------- 共享工具

def rating_str(rating: Optional[int], rank: Optional[str]) -> str:
    return "未定级" if rating is None else f"{rating} ({rank})"


def fmt_unix(seconds: Optional[int]) -> str:
    """unix 秒 → 日期字符串，便于人类阅读。"""
    if not seconds:
        return "-"
    return datetime.datetime.fromtimestamp(seconds).strftime("%Y-%m-%d")


def parse_problem_id(text: str) -> tuple:
    """解析题目标识（如 2185A / 2185/A）为 (contestId, index)。"""
    m = re.fullmatch(r"(\d+)[/_-]?([A-Za-z]\d*)", text.strip())
    if not m:
        sys.stderr.write(f"无法解析题目标识: {text}（示例: 2185A 或 2185/A）\n")
        sys.exit(1)
    return int(m.group(1)), m.group(2).upper()


def decode_source(target: dict) -> str:
    """解析 submission 中的源码（sourceBase64 解码，兼容老字段 source）。"""
    raw = target.get("source") or target.get("sourceBase64") or ""
    if target.get("sourceBase64"):
        try:
            return base64.b64decode(raw).decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            return ""
    return raw


def problem_brief(p: dict, solved: Optional[int] = None) -> dict:
    """题目精简字段（标签/难度等查询核心字段）。"""
    d = {
        "contestId": p.get("contestId"),
        "index": p.get("index"),
        "name": p.get("name"),
        "rating": p.get("rating"),
        "tags": p.get("tags") or [],
    }
    if solved is not None:
        d["solvedCount"] = solved
    return d
