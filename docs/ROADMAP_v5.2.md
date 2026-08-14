# ROADMAP v5.2 — GEP Harness Evolver 四连反弹（exec + read + process + message）

> 日期：2026-08-14 19:40
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 102/102（97 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 4 new + 3 DUPLICATE |

## v5.1 → v5.2 四连反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v5.1 | 1 | 6 | 86% dup |
| v5.2 | 4 | 3 | 43% dup |

**四连反弹**：v5.1 短暂回稳后立即反弹，v5.2 再次 4 new 3 dup。

## v5.2 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 4 个 (exec_hotpath_v52 + read_hotpath_v52 + process_hotpath_v52 + message_hotpath_v52) |
| DUPLICATE 处理 | 3 个 (write_file/edit/write 与 v1/v3 同) |
| commit | 72b004c |
| events | 9612 lines |

## v5.2 新发现

**exec 4121 calls** — 突破 4000+持续高频。
**tools 字段从 13 → 14** — 新增 1 个工具。
**read 141→143 (+2) 触发新 UNIQUE** — v5.0 之后首次反弹。
**process 135→139 (+4) 触发新 UNIQUE** — v5.0 之后首次反弹。
**message 56→60 (+4) 触发新 UNIQUE** — v5.0 之后首次反弹。

## 收敛趋势（v1.3~v5.2）

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
| **v5.2** | **4** | **3** | **四连反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v5.2 共 40 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 40 | 持续高频（必拆）|
| process | 16 | 反弹高频（40% 占比，必拆）|
| read | 9 | 反弹（v3.8/v4.2/v4.9/v5.0/v5.2 反弹 5 次）|
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 12 | 反弹（v3.8/v4.0/v4.2/v4.8/v4.9/v5.0/v5.2 反弹 7 次）|

**Exec 40 期 40 UNIQUE 持续高频**——结构性问题必拆（突破 4000 calls/24h）。
**Process 40 期 16 UNIQUE = 40%**——触发 UNIQUE 接近半数，强烈建议拆。
**Message 12 期 UNIQUE**，v3.8/v4.0/v4.2/v4.8/v4.9/v5.0/v5.2 累计 7 次反弹。

## 关键观察（v5.3 必拆 exec + process + message + read）

**v4.9 → v5.2 四期趋势**：
- v4.9: 3 new (exec + read + message) - 三连反弹
- v5.0: 4 new (exec + read + process + message) - 四连反弹
- v5.1: 1 new (exec) - 短暂回稳
- v5.2: 4 new (exec + read + process + message) - 四连反弹（峰值）

**v5.0/v5.2 双四连反弹**：
- v5.0: 4 hotpath tools UNIQUE
- v5.2: 4 hotpath tools UNIQUE（同样组合）

**exec 累计 4121 calls/24h** — 突破 4000 持续高频。

## 下一步建议

- [ ] **v5.3: exec args 前缀聚类专项**（40 期 40 UNIQUE，4121 calls/24h，必拆）
- [ ] **v5.3: process 超时防护场景细分**（16 期 UNIQUE，40% 占比，必拆）
- [ ] **v5.3: message 批量合并深挖**（12 期 UNIQUE，建议拆）
- [ ] **v5.3: read 模式聚类**（9 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
