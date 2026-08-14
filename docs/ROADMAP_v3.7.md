# ROADMAP v3.7 — GEP Harness Evolver 持续反弹（exec 25/25 + process 12/25 UNIQUE）

> 日期：2026-08-14 11:10
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 71/71（66 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v3.6 → v3.7 持续反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v3.6 | 2 | 5 | 71% dup |
| v3.7 | 2 | 5 | 71% dup |

**持续反弹**：连续 2 期 2 new 5 dup。

## v3.7 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v37 + process_hotpath_v37) |
| DUPLICATE 处理 | 5 个 (read/write_file/edit/write/message 与 v1/v3 同) |
| commit | 87951ce |
| events | 8384 lines |

## 收敛趋势（v1.3~v3.7）

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
| **v3.7** | **2** | **5** | **持续反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v3.7 共 25 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 25 | 持续高频（必拆）|
| process | 12 | 反弹高频（48% 占比，必拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 5 | 反弹 |

**Exec 25 期 25 UNIQUE 持续高频**——结构性问题必拆。
**Process 25 期 12 UNIQUE = 48%**——接近半数触发 UNIQUE，强烈建议拆。

## 关键观察（v3.8 必拆 exec + process）

**v3.5 → v3.7 三期趋势**：
- v3.5: 1 new (exec) - 回稳
- v3.6: 2 new (exec + process) - 反弹
- v3.7: 2 new (exec + process) - 持续反弹

process 反弹持续 2 期（v3.6 + v3.7），触发 UNIQUE 接近半数 (48%)。

## 下一步建议

- [ ] **v3.8: exec args 前缀聚类专项**（25 期 25 UNIQUE，必拆）
- [ ] **v3.8: process 超时防护场景细分**（12 期 UNIQUE，48% 占比，必拆）
- [ ] **v3.8: edit 操作类型细分**（4 期 UNIQUE 连续反弹，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
