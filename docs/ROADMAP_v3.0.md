# ROADMAP v3.0 — GEP Harness Evolver 反弹期（exec 18/18 + edit 二次 UNIQUE）

> 日期：2026-08-14 10:45
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 59/59（54 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v2.9 → v3.0 反弹分析

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v2.9 | 1 | 6 | 86% dup |
| v3.0 | 2 | 5 | 71% dup |

**反弹**：edit 81→87（+6 calls）重新触发 UNIQUE。

## v3.0 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v30 + edit_hotpath_v30) |
| DUPLICATE 处理 | 5 个 (read/process/write_file/write/message 与 v1/v2 同) |
| commit | 73da24d |
| events | 7532 lines |

## 收敛趋势（v1.3~v3.0）

| 期 | new | dup | 节点 |
|----|-----|-----|------|
| v1.3 | 7 | 0 | 爆发 |
| v1.4 | 3 | 4 | 收敛开始 |
| v1.5 | 6 | 1 | 震荡 |
| v1.6 | 4 | 3 | 二次收敛 |
| v1.7 | 1 | 6 | high decay |
| v1.8 | 5 | 2 | 反弹 |
| v1.9 | 1 | 6 | 回稳 |
| v2.0 | 2 | 5 | 稳定 |
| v2.1 | 1 | 6 | 持续稳定 |
| v2.2 | 1 | 6 | 完全稳定 |
| v2.3 | 1 | 6 | 完全稳定 |
| v2.4 | 2 | 5 | 微反弹 |
| v2.5 | 2 | 5 | 持续反弹 |
| v2.6 | 2 | 5 | 持续反弹 |
| v2.7 | 1 | 6 | 回稳 |
| v2.8 | 2 | 5 | 反弹再起 |
| v2.9 | 1 | 6 | 回稳 |
| **v3.0** | **2** | **5** | **反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v3.0 共 18 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 18 | 持续高频（必拆）|
| process | 8 | 反弹高频（建议拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 3 | 二次反弹（v2.0/v3.0 间隔反弹）|
| write | 4 | 部分高频 |
| message | 5 | 反弹 |

**Exec 18 期 18 UNIQUE 持续高频**——结构性问题必拆。

## 关键观察（v3.1 必拆 exec + process + edit）

**18 期 UNIQUE 趋势**：
- exec 18/18 持续高频 → 必拆
- process 8/18 反弹 → 建议拆
- edit 3/18 二次反弹 → 偶发但出现
- message 5/18 反弹 → 可拆

**v3.0 → v3.1 强烈建议**：
1. exec 按 args 前缀聚类（`ls/cat/grep/wc/head/tail/find`）
2. process 按超时场景（`>30s/timeout/foreground/background`）
3. edit 按操作类型（`replace/append/insert`）

## 下一步建议

- [ ] **v3.1: exec args 前缀聚类专项**（18 期 18 UNIQUE，必拆）
- [ ] **v3.1: process 超时防护场景细分**（8 期 UNIQUE，建议拆）
- [ ] **v3.1: edit 操作类型细分**（3 期 UNIQUE 反彈，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
