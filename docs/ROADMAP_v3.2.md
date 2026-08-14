# ROADMAP v3.2 — GEP Harness Evolver 回稳（exec 20/20 UNIQUE）

> 日期：2026-08-14 11:00
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 63/63（58 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 1 new + 6 DUPLICATE |

## v3.1 → v3.2 模式反转

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v3.1 | 3 | 4 | 57% dup |
| v3.2 | 1 | 6 | 86% dup |

**三连反弹中止**：v3.1 三工具反弹，v3.2 回到仅 exec 模式。

## v3.2 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 1 个 (exec_hotpath_v32) |
| DUPLICATE 处理 | 6 个 (read/process/write_file/edit/write/message 与 v1/v3 同) |
| commit | 8e65fe5 |
| events | 7828 lines |

## 收敛趋势（v1.3~v3.2）

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
| v3.0 | 2 | 5 | 反弹 |
| v3.1 | 3 | 4 | 三连反弹 |
| **v3.2** | **1** | **6** | **回稳** |

## 高频工具累计 UNIQUE 次数（v1.3~v3.2 共 20 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 20 | 持续高频（必拆）|
| process | 9 | 反弹高频（建议拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 5 | 反弹 |

**Exec 20 期 20 UNIQUE 持续高频**——结构性问题必拆。

## 关键观察（v3.3 必拆 exec + process 持续反弹）

**v3.1 → v3.2 反弹节奏**：
- v3.1: 3 new (exec + process + edit) - 三连反弹
- v3.2: 1 new (exec) - 回稳

process 累计 9/20 UNIQUE，edit 累计 4/20 UNIQUE 都是间歇反弹，但 exec 永远 20/20 持续高频。

## 下一步建议

- [ ] **v3.3: exec args 前缀聚类专项**（20 期 20 UNIQUE，必拆）
- [ ] **v3.3: process 超时防护场景细分**（9 期 UNIQUE，建议拆）
- [ ] **v3.3: edit 操作类型细分**（4 期 UNIQUE 连续反弹，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
