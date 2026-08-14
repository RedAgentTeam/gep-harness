# ROADMAP v2.4 — GEP Harness Evolver 反弹期（exec 12/12 + process 反弹）

> 日期：2026-08-14 10:25
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 49/49（44 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v2.3 → v2.4 反弹分析

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v2.3 | 1 | 6 | 86% dup |
| v2.4 | 2 | 5 | 71% dup |

**微反弹**：process 101→107（+6 calls）首次重新 UNIQUE。

## v2.4 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v24 + process_hotpath_v24) |
| DUPLICATE 处理 | 5 个 (read/write_file/edit/write/message 与 v1.5/v1.8/v2.0 同) |
| commit | ae7b6fb |
| events | 6944 lines |

## 收敛趋势（v1.3~v2.4）

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
| **v2.4** | **2** | **5** | **微反弹** |

## Process 反弹分析

process 趋势：

| 期 | process calls | 状态 |
|----|---------------|------|
| v1.3 | ~50 | new |
| v1.4 | ~70 | new |
| v1.5 | ~85 | new |
| v1.6 | ~95 | new |
| v1.7 | ~95 | 新高频 |
| v1.8 | 101 | new |
| v1.9~v2.3 | 101 | DUPLICATE |
| **v2.4** | **107** | **new (反弹)** |

**Process 累计 5 期 UNIQUE + 3 期反弹新 UNIQUE**——结构性问题持续。

## 双高频工具现状（exec 12/12 + process 6/12 UNIQUE）

v1.3~v2.4 共 12 期 UNIQUE 次数：

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 12 | 持续高频（必拆）|
| process | 6 | 反弹高频（建议拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 2 | 偶发 |
| write | 4 | 部分高频 |
| message | 4 | 部分高频 |

## 关键观察（v3.0 必拆 exec + process）

**exec 12 期 12 UNIQUE + process 6 期 UNIQUE 是结构性问题**：
- 双高频工具必须拆解
- exec 按 args 前缀（`ls/cat/grep/wc/head/tail/find`）
- process 按超时场景（`>30s/timeout/foreground/background`）

## 下一步建议

- [ ] **v3.0: exec args 前缀聚类专项**（12 期 12 UNIQUE，必拆）
- [ ] **v3.0: process 超时防护场景细分**（6 期 UNIQUE，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
- [ ] message 批量合并 Gene 深挖
