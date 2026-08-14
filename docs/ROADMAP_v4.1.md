# ROADMAP v4.1 — GEP Harness Evolver 回稳（exec 29/29 UNIQUE）

> 日期：2026-08-14 12:40
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 79/79（74 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 1 new + 6 DUPLICATE |

## v4.0 → v4.1 模式反转

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v4.0 | 3 | 4 | 57% dup |
| v4.1 | 1 | 6 | 86% dup |

**回稳**：v4.0 三连反弹，v4.1 回到 1 new 6 dup。

## v4.1 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 1 个 (exec_hotpath_v41) |
| DUPLICATE 处理 | 6 个 (read/process/write_file/edit/message/write 与 v1/v3/v4 同) |
| commit | f647f6f |
| events | 8812 lines |

## 收敛趋势（v1.3~v4.1）

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
| **v4.1** | **1** | **6** | **回稳** |

## 高频工具累计 UNIQUE 次数（v1.3~v4.1 共 29 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 29 | 持续高频（必拆）|
| process | 13 | 反弹高频（45% 占比，必拆）|
| read | 5 | 反弹（v3.8 反弹过）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 7 | 反弹（v3.8/v4.0 连续 2 期）|

**Exec 29 期 29 UNIQUE 持续高频**——结构性问题必拆。
**Process 29 期 13 UNIQUE = 45%**——接近半数触发 UNIQUE，强烈建议拆。

## 关键观察（v4.2 必拆 exec + process）

**v3.9 → v4.1 三期趋势**：
- v3.9: 1 new (exec) - 回稳
- v4.0: 3 new (exec + process + message) - 三连反弹
- v4.1: 1 new (exec) - 回稳

**Process/message 间歇反弹**：
- process: v3.6/v3.7/v4.0 反弹 3 期，v3.9/v4.1 DUPLICATE
- message: v3.8/v4.0 反弹 2 期，v3.9/v4.1 DUPLICATE

反弹工具约 4 期一次出现一次，回稳时回落。

## 下一步建议

- [ ] **v4.2: exec args 前缀聚类专项**（29 期 29 UNIQUE，必拆）
- [ ] **v4.2: process 超时防护场景细分**（13 期 UNIQUE，45% 占比，必拆）
- [ ] **v4.2: message 批量合并深挖**（7 期 UNIQUE，建议拆）
- [ ] **v4.2: read 模式聚类**（5 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
