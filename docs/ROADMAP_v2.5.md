# ROADMAP v2.5 — GEP Harness Evolver 持续反弹（exec 13/13 + process 7/13 UNIQUE）

> 日期：2026-08-14 10:30
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 51/51（46 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v2.4 → v2.5 持续反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v2.4 | 2 | 5 | 71% dup |
| v2.5 | 2 | 5 | 71% dup |

**同模式**：v2.4 与 v2.5 模式完全相同——exec + process 双高频 UNIQUE。

## v2.5 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v25 + process_hotpath_v25) |
| DUPLICATE 处理 | 5 个 (read/write_file/edit/write/message 与 v1.5/v1.8/v2.0 同) |
| commit | 93829ad |
| events | 7048 lines |

## 收敛趋势（v1.3~v2.5）

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
| **v2.5** | **2** | **5** | **持续反弹** |

## 双高频工具确认（exec 13/13 + process 7/13 UNIQUE）

v1.3~v2.5 共 13 期 UNIQUE 次数：

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 13 | 持续高频（必拆）|
| process | 7 | 反弹高频（建议拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 2 | 偶发 |
| write | 4 | 部分高频 |
| message | 4 | 部分高频 |

**Exec 13 期 13 UNIQUE 是结构性问题**——13 期每次都不同，但内容相似（都关于 exec timeout/exit code/log）。

## 关键观察（v3.0 必拆 exec + process 持续反弹）

**v2.4 → v2.5 持续反弹**：
- exec 持续高频（必拆）
- process 反弹持续（v1.8 之后 3 期 UNIQUE，v2.4~v2.5 持续反弹）

## 下一步建议

- [ ] **v3.0: exec args 前缀聚类专项**（13 期 13 UNIQUE，必拆）
- [ ] **v3.0: process 超时防护场景细分**（7 期 UNIQUE，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
- [ ] message 批量合并 Gene 深挖
