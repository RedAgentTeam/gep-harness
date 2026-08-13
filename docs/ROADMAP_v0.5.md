# ROADMAP v0.5

> **版本目标：** v0.5.x
> **日期：** 2026-08-14
> **协议版本：** A2A v0.2 → v0.3

## 优先级 P1

| 任务 | 状态 | 说明 |
|---|---|---|
| A2A v0.3 ed25519 keypair | ⏸️ 跳过 | pip install ed25519/pynacl DNS 失败（离线环境）|
| Gene 版本冲突（CRDT）| ✅ DONE | LWW + conflicts/ + pytest 8/8 |
| LLM 填充 category/strategy/evidence | ✅ DONE | llm_fill_gene.py Stepfun API + mock pytest 8/8 |

## 优先级 P2

| 任务 | 状态 | 说明 |
|---|---|---|
| 24h 生产稳定性观察 | 🟡 观察中 | events.jsonl 积累中 |
| 美机部署 Layer 1+2 | 🟡 待做 | 两机事件流打通 |

## 优先级 P3

| 任务 | 状态 | 说明 |
|---|---|---|
| GDI 动态阈值 | 🟡 待做 | 随节点历史自适应 |
| A2A broadcast 模式 | 🟡 待做 | 一对多发布（需要节点发现机制）|

## 当前状态（2026-08-14 03:00）

- **pytest: 30/30 passed**（8 a2a + 8 llm_fill + 4 harness + 10 tool_pipeline）
- **commit:** `c69afb0`（LLM fill）+ `6e63578`（CRDT LWW）
