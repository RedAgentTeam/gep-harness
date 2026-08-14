# ROADMAP v2.8 — GEP Harness Evolver 持续反弹（exec 16/16 + process 8/16 UNIQUE）

> 日期：2026-08-14 10:40
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 56/56（51 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v2.7 → v2.8 模式分析

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v2.7 | 1 | 6 | 86% dup |
| v2.8 | 2 | 5 | 71% dup |

**回到 v2.4~v2.6 反弹模式**：exec + process 双高频 UNIQUE。

## v2.8 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v28 + process_hotpath_v28) |
| DUPLICATE 处理 | 5 个 (read/write_file/edit/write/message 与 v1/v2 同) |
| commit | 93f9029 |
| events | 7296 lines |

## 收敛趋势（v1.3~v2.8）

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
| **v2.8** | **2** | **5** | **反弹再起** |

## 高频工具累计 UNIQUE 次数（v1.3~v2.8 共 16 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 16 | 持续高频（必拆）|
| process | 8 | 反弹高频（建议拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 2 | 偶发 |
| write | 4 | 部分高频 |
| message | 5 | 反弹 |

**Exec 16 期 16 UNIQUE 持续高频**——结构性问题必拆。

## 关键观察（v3.0 必拆 exec + process 持续高频）

**v2.7 → v2.8 模式反转**：
- v2.7: 1 new (exec) - 回稳
- v2.8: 2 new (exec + process) - 反弹再起

process 109→113（+4 calls）再次触发 UNIQUE——v3.0 强烈建议拆 process。

## 下一步建议

- [ ] **v3.0: exec args 前缀聚类专项**（16 期 16 UNIQUE，必拆）
- [ ] **v3.0: process 超时防护场景细分**（8 期 UNIQUE，建议拆）
- [ ] **v3.0: message 批量合并深挖**（5 期 UNIQUE，可拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
