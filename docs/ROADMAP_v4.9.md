# ROADMAP v4.9 — GEP Harness Evolver 三连反弹（exec + read + message）

> 日期：2026-08-14 16:00
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 93/93（88 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 3 new + 4 DUPLICATE |

## v4.8 → v4.9 反弹延续

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v4.8 | 3 | 4 | 57% dup |
| v4.9 | 3 | 4 | 57% dup |

**三连反弹**：v4.8/v4.9 连续 2 期 3 new 4 dup（不同组合）。

## v4.9 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 3 个 (exec_hotpath_v49 + read_hotpath_v49 + message_hotpath_v49) |
| DUPLICATE 处理 | 4 个 (process/write_file/edit/write 与 v1/v3/v4 同) |
| commit | f687a8d |
| events | 9224 lines |

## v4.9 新发现

**read 137→139 (+2 calls) 触发新 UNIQUE** — v4.2 之后首次反弹：
- v1.3~v1.8/v3.8/v4.2/v4.9 累计 7 期 UNIQUE

**message 52→54 (+2 calls) 触发新 UNIQUE** — v4.8 之后连续反弹：
- v1.3~v1.8/v2.6/v3.8/v4.0/v4.2/v4.8/v4.9 累计 10 期 UNIQUE

**v4.8/v4.9 三连反弹对比**：
- v4.8: exec + process + message
- v4.9: exec + read + message

## 收敛趋势（v1.3~v4.9）

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
| **v4.9** | **3** | **4** | **三连反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v4.9 共 37 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 37 | 持续高频（必拆）|
| process | 14 | 反弹高频（38% 占比，必拆）|
| read | 7 | 反弹（v3.8/v4.2/v4.9 反弹 3 次）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 10 | 反弹（v3.8/v4.0/v4.2/v4.8/v4.9 反弹 5 次）|

**Exec 37 期 37 UNIQUE 持续高频**——结构性问题必拆。
**Process 37 期 14 UNIQUE = 38%**——触发 UNIQUE 接近 4 成，强烈建议拆。
**Message 10 期 UNIQUE**（双位数），v3.8/v4.0/v4.2/v4.8/v4.9 累计 5 次反弹。

## 关键观察（v5.0 必拆 exec + process + message + read）

**v4.7 → v4.9 三期趋势**：
- v4.7: 1 new (exec) - 持续回稳
- v4.8: 3 new (exec + process + message) - 三连反弹
- v4.9: 3 new (exec + read + message) - 三连反弹

**Process/message 间歇反弹**：
- process: v3.6/v3.7/v4.0/v4.8 反弹 4 期，v4.1~v4.7/v4.9 都 DUPLICATE
- message: v3.8/v4.0/v4.2/v4.8/v4.9 反弹 5 期
- read: v3.8/v4.2/v4.9 反弹 3 期

**三连反弹工具约 4-5 期一次出现一次**。

## 下一步建议

- [ ] **v5.0: exec args 前缀聚类专项**（37 期 37 UNIQUE，必拆）
- [ ] **v5.0: process 超时防护场景细分**（14 期 UNIQUE，38% 占比，必拆）
- [ ] **v5.0: message 批量合并深挖**（10 期 UNIQUE，建议拆）
- [ ] **v5.0: read 模式聚类**（7 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
