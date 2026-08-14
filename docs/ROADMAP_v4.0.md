# ROADMAP v4.0 — GEP Harness Evolver 三连反弹（exec + process + message）

> 日期：2026-08-14 12:35
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 78/78（73 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 3 new + 4 DUPLICATE |

## v3.9 → v4.0 三连反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v3.9 | 1 | 6 | 86% dup |
| v4.0 | 3 | 4 | 57% dup |

**三连反弹**：v4.0 同样三连反弹（exec + process + message）。

## v4.0 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 3 个 (exec_hotpath_v40 + process_hotpath_v40 + message_hotpath_v40) |
| DUPLICATE 处理 | 4 个 (read/write_file/edit/write 与 v1/v3 同) |
| commit | 040f2c0 |
| events | 8788 lines |

## v4.0 新发现

**process 123→129 (+6 calls) 触发新 UNIQUE** — 持续反弹：
- v3.6 → v3.7 → v3.9 → v4.0 累计 4 期反弹

**message 46→48 (+2 calls) 触发新 UNIQUE** — v3.8 之后再次反弹：
- v1.3~v1.8/v2.6/v3.8/v4.0 累计 7 期 UNIQUE

## 收敛趋势（v1.3~v4.0）

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
| **v4.0** | **3** | **4** | **三连反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v4.0 共 28 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 28 | 持续高频（必拆）|
| process | 13 | 反弹高频（46% 占比，必拆）|
| read | 5 | 反弹（v3.8 反弹过）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 7 | 反弹（v3.8/v4.0 连续 2 期）|

**Exec 28 期 28 UNIQUE 持续高频**——结构性问题必拆。
**Process 28 期 13 UNIQUE = 46%**——接近半数触发 UNIQUE，强烈建议拆。
**Message 7 期 UNIQUE** — v3.8/v4.0 连续 2 期反弹。

## 关键观察（v4.1 必拆 exec + process）

**v3.8 → v4.0 三期趋势**：
- v3.8: 3 new (exec + read + message) - 三连反弹
- v3.9: 1 new (exec) - 回稳
- v4.0: 3 new (exec + process + message) - 三连反弹

**v3.8 / v4.0 三连反弹对比**：
- v3.8: exec + read + message
- v4.0: exec + process + message

message 连续 2 期反弹（v3.8 + v4.0），process 持续高频反弹。

## 下一步建议

- [ ] **v4.1: exec args 前缀聚类专项**（28 期 28 UNIQUE，必拆）
- [ ] **v4.1: process 超时防护场景细分**（13 期 UNIQUE，46% 占比，必拆）
- [ ] **v4.1: message 批量合并深挖**（7 期 UNIQUE，建议拆）
- [ ] **v4.1: read 模式聚类**（5 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
