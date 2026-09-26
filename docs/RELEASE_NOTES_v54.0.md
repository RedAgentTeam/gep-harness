# Release Notes — gep-harness v54.0 (2026-09-26)

> **Tag:** `v54.0`
> **Commit:** 当前 `master`
> **Date:** 2026-09-26
> **Author:** RedAgentTeam
> **Protocol:** GEP v1.12.1 (strict)
> **License:** MIT

这个 Release 把 GitHub 上的最新发布对齐到当前 `master`。历史 Release `v33.0` 仍然保留。

## 自 v41.1 以来

- 5 库 trust score 的持久化、自动切换、查询和只读 Web（内部序号 v42–v53）。
- trust 切换成功后向事件流追加 `trust_audit`。
- 会话日志升级时保留原文件，新事件写入 `events.v2.jsonl`。
- read / write / edit / shell 之外的工具调用由人决定是否继续。
- 长命令在同一会话记录 `command_start` 与 `command_finish`，并区分正常退出和超时。
- LLM 填充只从环境变量或仓库根目录的 `.env` 读取密钥。

## 当前仓库计数

| 项 | 数 |
|---|---|
| commits | 477 |
| plan/genes | 64 |
| plan/capsules | 2 |
| plan/events | 28 |

生产节点未部署。
