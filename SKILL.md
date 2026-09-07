---
name: codeforces-skill
description: 查询 Codeforces 比赛、题目、用户信息与提交源码。当用户询问 CF rating、做题记录、题目难度/标签、比赛安排、提交代码等竞赛编程数据时调用。
compatibility: Python 3.8+, requests 库, 可访问网络
---

# Codeforces Skill

通过 Codeforces 官方 API 获取比赛、题目、用户、提交等信息。本 Skill 已将全部 API 能力封装为命令行脚本（`scripts/`），**所有信息一律通过脚本获取**，不要自行拼 URL 请求 API。脚本内部已处理官方 2 秒限速、请求签名、错误处理与数据裁剪。

## 运行环境

- Python 3.8+，已安装 `requests`
- 统一入口：`python scripts/cf.py ...`（工作目录为本 Skill 根目录）

## 使用约定

- **输出**：默认向 stdout 输出 JSON（供解析）；加 `--human` 输出人类可读文本；错误写入 stderr 且退出码非 0
- **默认用户**：命令未传 `--handle` 时使用已绑定用户
- **限速**：脚本内置跨进程 2 秒限速，连续调用自动排队
- **签名**：已配置 key/secret 则自动签名（访问私有数据），否则匿名访问，对调用者透明

## 一次性配置

```bash
python scripts/cf.py bind <handle>                # 绑定默认用户
python scripts/cf.py credentials --key <k> --secret <s>  # 可选：配置签名凭据
```

## 命令参考

### 用户模块 `user`

| 命令 | 用途 | 关键参数 |
|---|---|---|
| `user info` | 基本信息（rating/rank/max/贡献/组织） | `--handle` |
| `user rating` | rating 历史（每场时间/比赛/涨幅 delta） | `--handle` |
| `user submissions` | 提交统计 + 已做题目清单 + 最近提交 | `--handle` `--count`(500) `--recent`(10) `--solved-limit`(50) |
| `user problem <题目ID>` | 某题的提交记录（`total:0`=没做过） | `--source`(附最近AC源码) `--handle` |
| `user friends` | 好友列表（需签名） | `--only-online` |

### 题目模块 `problem`

| 命令 | 用途 | 关键参数 |
|---|---|---|
| `problem info <题目ID>` | 标签、难度、通过人数 | 题目ID 如 `2185A`/`2185/A` |
| `problem search` | 按标签/难度筛题 | `--tag`(可多次) `--min-rating` `--max-rating` `--limit`(20) |

### 比赛模块 `contest`

| 命令 | 用途 | 关键参数 |
|---|---|---|
| `contest upcoming` | 未开始的比赛 | `--limit`(10) |
| `contest problems <contestId>` | 某场比赛题目列表 | 比赛ID 如 `566` |

### 提交模块 `submission`

| 命令 | 用途 | 关键参数 |
|---|---|---|
| `submission code <id>` | 按提交ID取源码（需签名） | `--depth`(100) `--handle` |

### 复合模块 `recommend`

| 命令 | 用途 | 关键参数 |
|---|---|---|
| `recommend unsolved` | 带标签(任一)/难度区间/序号下限的**未做题** | `--tag`(可多次,OR) `--min-rating` `--max-rating` `--min-contest` `--limit`(20) `--count`(2000) `--handle` |
| `recommend solved` | 同上，但仅保留**已做题** | 同上 |
| `recommend pick` | 从候选集（stdin 管道 或 同格式 JSON 文件）**随机抽 n 道** | `--input`(文件) `--count`(3) |

说明：`--tag` 为任一匹配（OR）；`--min-contest k` 表示题目序号（场次号）≥ k；候选集 JSON 约定为 `{"problems": [...]}` 或问题列表。

## 典型场景

| 用户意图 | 应执行 |
|---|---|
| 查我的 rating / 涨跌 | `cf.py user rating --human` |
| 我做过哪些题 / 刷题统计 | `cf.py user submissions --human` |
| 某题做没做过 / 提交记录 | `cf.py user problem 2185A --human` |
| 某题的代码 | `cf.py user problem 2185A --source --human` 或 `submission code <id> --human` |
| 某题难度/标签 | `cf.py problem info 2185A --human` |
| 按标签难度找题 | `cf.py problem search --tag dp --min-rating 1200 --max-rating 1400 --human` |
| 最近比赛 | `cf.py contest upcoming --human` |
| 某场比赛的题 | `cf.py contest problems 566 --human` |
| 找 1600-1800 我还没做过的新题(场次≥2000) | `cf.py recommend unsolved --tag greedy --tag dp --min-rating 1600 --max-rating 1800 --min-contest 2000 --human` |
| 我做过哪些 1700+ 的题 | `cf.py recommend solved --min-rating 1700 --human` |
| 从候选里随机抽 3 道练 | `cf.py recommend unsolved ... \| cf.py recommend pick --count 3 --human` 或 `--input cands.json` |

## 解析约定

- 需要结构化字段（delta/rating/solvedCount 等）时用默认 JSON 输出，直接解析 stdout
- 以退出码判断成败；非 0 时读 stderr 原因转述用户
- `user problem` 的 `total: 0` 表示没做过该题，不是错误
- `submission code` 在最近 `--depth` 条内找不到提交会失败，可加大 `--depth`

## 详细数据规范

API 方法清单与参数、返回对象字段、签名/限速规范见 `reference/` 目录（按需加载）：

| 文件 | 内容 |
|---|---|
| `reference/Methods.md` | 全部 API 方法、参数、示例 |
| `reference/Return_objects.md` | 返回对象字段说明 |
| `reference/Introduction.md` | 签名算法、限速、JSONP 规范 |