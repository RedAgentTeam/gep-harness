# ROADMAP v4.2 — GEP Harness Evolver 三连反弹（exec + read + message）

> 日期：2026-08-14 13:55
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 82/82（77 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 3 new + 4 DUPLICATE |

## v4.1 → v4.2 三连反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v4.1 | 1 | 6 | 86% dup |
| v4.2 | 3 | 4 | 57% dup |

**三连反弹**：v4.2 再次 3 new（exec + read + message）。

## v4.2 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 3 个 (exec_hotpath_v42 + read_hotpath_v42 + message_hotpath_v42) |
| DUPLICATE 处理 | 4 个 (process/write_file/edit/write 与 v1/v3/v4 同) |
| commit | e8a207c |
| events | 8924 lines |

## v4.2 新发现

**read 135→137 (+2 calls) 触发新 UNIQUE** — v3.8 之后第二次反弹：
- v1.3 累计 4 期 + v3.8 + v4.2 = 6 期 UNIQUE

**message 48→50 (+2 calls) 触发新 UNIQUE** — v4.0 之后再次反弹：
- v1.3~v1.8/v2.6/v3.8/v4.0/v4.2 累计 8 期 UNIQUE

**tools 字段从 12 → 13** — 新增一个工具。

## 收敛趋势（v1.3~v4.2）

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
| v3.2 | 1 | 6 | 回稳 |
| v3.3 | 2 | 5 | 反弹 |
| v3.4 | 1 | 6 | 回稳 |
| v3.5 | 1 | 6 | 回稳 |
| v3.6 | 2 | 5 | 反弹 |
| v3.7 | 2 | 5 | 持续反弹 |
| v3.8 | 3 | 4 | 三连反弹 |
| v3.9 | 1 | 6 | 回稳 |
| v4.0 | 3 | 4 | 三连反弹 |
| v4.1 | 1 | 6 | 回稳 |
| **v4.2** | **3** | **4** | **三连反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v4.2 共 30 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 30 | 持续高频（必拆）|
| process | 13 | 反弹高频（43% 占比，必拆）|
| read | 6 | 反弹（v3.8/v4.2 反弹 2 次）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 8 | 反弹（v3.8/v4.0/v4.2 反弹 3 次）|

**Exec 30 期 30 UNIQUE 持续高频**——结构性问题必拆。
**Process 30 期 13 UNIQUE = 43%**——接近半数触发 UNIQUE，强烈建议拆。
**Message 8 期 UNIQUE**，v3.8/v4.0/v4.2 累计 3 次反弹。

## 关键观察（v4.3 必拆 exec + process + message）

**v4.0 → v4.2 三期趋势**：
- v4.0: 3 new (exec + process + message) - 三连反弹
- v4.1: 1 new (exec) - 回稳
- v4.2: 3 new (exec + read + message) - 三连反弹

**v4.0/v4.2 三连反弹工具对比**：
- v4.0: exec + process + message
- v4.2: exec + read + message

message 连续 3 期反弹（v3.8/v4.0/v4.2 中间经过 v3.9/v4.1 回稳）。

## 下一步建议

- [ ] **v4.3: exec args 前缀聚类专项**（30 期 30 UNIQUE，必拆）
- [ ] **v4.3: process 超时防护场景细分**（13 期 UNIQUE，43% 占比，必拆）
- [ ] **v4.3: message 批量合并深挖**（8 期 UNIQUE，建议拆）
- [ ] **v4.3: read 模式聚类**（6 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
