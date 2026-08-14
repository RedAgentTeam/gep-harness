# ROADMAP v7.2 — GEP Harness Evolver 三连反弹（exec + read + process）

> 日期：2026-08-14 21:10
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 132/132（127 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 3 new + 4 DUPLICATE |

## v7.1 → v7.2 三连反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v7.1 | 1 | 6 | 86% dup |
| v7.2 | 3 | 4 | 57% dup |

**三连反弹**：v7.1 持续回稳 7 期中断，v7.2 反弹（read + process 双反弹）。

## v7.2 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 3 个 (exec_hotpath_v72 + read_hotpath_v72 + process_hotpath_v72) |
| 累计 Gene | 127 个 |
| DUPLICATE 处理 | 4 个 (write_file/edit/message/write 与 v1/v3/v5.0/v5.2/v6.0/v6.2/v6.5/v6.6/v6.7/v6.8/v6.9/v7.0/v7.1 同) |
| commit | 5f2269f |
| events | 11150 lines |

## v7.2 新发现

**exec 4785 calls** — 突破 4700 持续高频。
**read 199→203 (+4 calls, 突破 200) 触发新 UNIQUE** — v6.0 之后首次反弹（60 期累计 13 期 UNIQUE）。
**process 161→171 (+10 calls, 突破 170) 触发新 UNIQUE** — v6.9 之后首次反弹（60 期累计 20 期 UNIQUE）。
**write_file/edit/message/write 持平 DUPLICATE**（v7.0/v7.1 同样 asset_id）。

## 收敛趋势（v1.3~v7.2）

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
| v6.5 | 2 | 5 | 反弹（message 反弹）|
| v6.6 | 1 | 6 | 短暂回稳 |
| v6.7 | 1 | 6 | 持续回稳 |
| v6.8 | 1 | 6 | 持续回稳（120 genes）|
| v6.9 | 2 | 5 | 反弹（process 反弹）|
| v7.0 | 1 | 6 | 短暂回稳 |
| v7.1 | 1 | 6 | 持续回稳 |
| **v7.2** | **3** | **4** | **三连反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v7.2 共 60 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 60 | 持续高频（必拆）|
| process | 20 | 反弹高频（33% 占比，必拆）|
| read | 13 | 反弹（累计 9 次反弹）|
| message | 13 | 反弹（累计 8 次反弹）|
| write | 5 | 反弹（v1.5/v6.1 反弹 2 次）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|

**Exec 60 期 60 UNIQUE 持续高频**——结构性问题必拆（4785 calls/24h）。
**Process 60 期 20 UNIQUE = 33%**——触发 UNIQUE 接近半数，强烈建议拆。
**Read 13 期 UNIQUE**（双位数）— v7.2 反弹，累计 9 次。
**Message 13 期 UNIQUE**（双位数）— 累计 8 次反弹。
**Write 5 期 UNIQUE** — v1.5 之后 v6.1 反弹。

## 关键观察（v7.3 必拆 exec + process + message + read + write）

**v6.0 → v7.2 十三期趋势（双四连反弹周期 + 持续回稳 + 新反弹 + v6.3~v7.2 周期模式）**：
- v6.0: 2 new (exec + read) - 反弹延续
- v6.1: 2 new (exec + write) - 反弹延续（write 反弹）
- v6.2: 2 new (exec + process) - 反弹延续（process 反弹）
- v6.3: 1 new (exec) - 短暂回稳
- v6.4: 1 new (exec) - 持续回稳
- v6.5: 2 new (exec + message) - 反弹（message 反弹）
- v6.6: 1 new (exec) - 短暂回稳
- v6.7: 1 new (exec) - 持续回稳
- v6.8: 1 new (exec) - 持续回稳（120 genes）
- v6.9: 2 new (exec + process) - 反弹（process 反弹）
- v7.0: 1 new (exec) - 短暂回稳
- v7.1: 1 new (exec) - 持续回稳
- v7.2: 3 new (exec + read + process) - 三连反弹（read + process 双反弹）

**v6.3~v7.1 持续回稳 7 期 → v7.2 三连反弹**——反弹周期约 7-8 期一次。

## 下一步建议

- [ ] **v7.3: exec args 前缀聚类专项**（60 期 60 UNIQUE，4785 calls/24h，必拆）
- [ ] **v7.3: process 超时防护场景细分**（20 期 UNIQUE，33% 占比，必拆）
- [ ] **v7.3: message 批量合并深挖**（13 期 UNIQUE，建议拆）
- [ ] **v7.3: read 模式聚类**（13 期 UNIQUE，可拆）
- [ ] **v7.3: write 模式聚类**（5 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
