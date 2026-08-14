# ROADMAP v6.5 — GEP Harness Evolver 反弹（exec + message）

> 日期：2026-08-14 20:50
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 122/122（117 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v6.4 → v6.5 反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v6.4 | 1 | 6 | 86% dup |
| v6.5 | 2 | 5 | 71% dup |

**反弹**：v6.3/v6.4 持续回稳 2 期中断，v6.5 反弹。

## v6.5 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v65 + message_hotpath_v65) |
| 累计 Gene | 117 个 |
| DUPLICATE 处理 | 5 个 (read/process/write_file/edit/write 与 v1/v3/v5.0/v5.2/v6.0/v6.2/v6.3/v6.4 同) |
| commit | 41f92bb |
| events | 10472 lines |

## v6.5 新发现

**exec 4473 calls** — 突破 4400 持续高频。
**message 60→62 (+2 calls) 触发新 UNIQUE** — v5.2 之后 v6.4 之前一直 DUPLICATE，v6.5 再次反弹（52 期累计 13 期 UNIQUE）。
**read/process/write 持平 DUPLICATE**（v6.0/v6.2/v6.3/v6.4 同样 asset_id）。

## 收敛趋势（v1.3~v6.5）

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
| v4.2 | 3 | 4 | 三连反弹 |
| v4.3 | 1 | 6 | 回稳 |
| v4.4 | 1 | 6 | 持续回稳 |
| v4.5 | 1 | 6 | 持续回稳 |
| v4.6 | 1 | 6 | 持续回稳 |
| v4.7 | 1 | 6 | 持续回稳 |
| v4.8 | 3 | 4 | 三连反弹 |
| v4.9 | 3 | 4 | 三连反弹 |
| v5.0 | 4 | 3 | 四连反弹 |
| v5.1 | 1 | 6 | 短暂回稳 |
| v5.2 | 4 | 3 | 四连反弹 |
| v5.3 | 1 | 6 | 回稳 |
| v5.4 | 1 | 6 | 持续回稳 |
| v5.5 | 1 | 6 | 持续回稳（100 genes）|
| v5.6 | 1 | 6 | 持续回稳 |
| v5.7 | 1 | 6 | 持续回稳 |
| v5.8 | 3 | 4 | 三连反弹 |
| v5.9 | 2 | 5 | 反弹延续（10000 events）|
| v6.0 | 2 | 5 | 反弹延续 |
| v6.1 | 2 | 5 | 反弹延续（write 反弹）|
| v6.2 | 2 | 5 | 反弹延续（process 反弹）|
| v6.3 | 1 | 6 | 短暂回稳 |
| v6.4 | 1 | 6 | 持续回稳 |
| **v6.5** | **2** | **5** | **反弹（message 反弹）** |

## 高频工具累计 UNIQUE 次数（v1.3~v6.5 共 53 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 53 | 持续高频（必拆）|
| process | 18 | 反弹高频（34% 占比，必拆）|
| read | 12 | 反弹（累计 8 次反弹）|
| message | 13 | 反弹（v3.8/v4.0/v4.2/v4.8/v4.9/v5.0/v5.2/v6.5 反弹 8 次）|
| write | 5 | 反弹（v1.5/v6.1 反弹 2 次）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|

**Exec 53 期 53 UNIQUE 持续高频**——结构性问题必拆（4473 calls/24h）。
**Process 53 期 18 UNIQUE = 34%**——触发 UNIQUE 接近半数，强烈建议拆。
**Read 12 期 UNIQUE**（双位数）— 累计 8 次反弹。
**Message 13 期 UNIQUE**（双位数）— v6.5 反弹，累计 8 次。
**Write 5 期 UNIQUE** — v1.5 之后 v6.1 反弹。

## 关键观察（v6.6 必拆 exec + process + message + read + write）

**v6.0 → v6.5 六期趋势（双四连反弹周期 + 持续回稳 + 新反弹 + v6.3~v6.5 周期模式）**：
- v6.0: 2 new (exec + read) - 反弹延续
- v6.1: 2 new (exec + write) - 反弹延续（write 反弹）
- v6.2: 2 new (exec + process) - 反弹延续（process 反弹）
- v6.3: 1 new (exec) - 短暂回稳
- v6.4: 1 new (exec) - 持续回稳
- v6.5: 2 new (exec + message) - 反弹（message 反弹）

**v6.3~v6.4 短暂回稳 2 期后 v6.5 反弹（message 累计 13 期 UNIQUE）**。

## 下一步建议

- [ ] **v6.6: exec args 前缀聚类专项**（53 期 53 UNIQUE，4473 calls/24h，必拆）
- [ ] **v6.6: process 超时防护场景细分**（18 期 UNIQUE，34% 占比，必拆）
- [ ] **v6.6: message 批量合并深挖**（13 期 UNIQUE，建议拆）
- [ ] **v6.6: read 模式聚类**（12 期 UNIQUE，可拆）
- [ ] **v6.6: write 模式聚类**（5 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
