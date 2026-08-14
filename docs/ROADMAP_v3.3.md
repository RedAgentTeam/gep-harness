# ROADMAP v3.3 — GEP Harness Evolver 反弹（exec 21/21 + process 10/21 UNIQUE）

> 日期：2026-08-14 11:00
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 65/65（60 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 2 new + 5 DUPLICATE |

## v3.2 → v3.3 反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v3.2 | 1 | 6 | 86% dup |
| v3.3 | 2 | 5 | 71% dup |

**反弹**：process 115→117（+2 calls）重新触发 UNIQUE。

## v3.3 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 2 个 (exec_hotpath_v33 + process_hotpath_v33) |
| DUPLICATE 处理 | 5 个 (read/write_file/edit/write/message 与 v1/v3 同) |
| commit | fae3884 |
| events | 7880 lines |

## 收敛趋势（v1.3~v3.3）

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
| **v3.3** | **2** | **5** | **反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v3.3 共 21 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 21 | 持续高频（必拆）|
| process | 10 | 反弹高频（必拆 - 21 期 10 UNIQUE = 48%）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 5 | 反弹 |

**Exec 21 期 21 UNIQUE 持续高频**——结构性问题必拆。
**Process 21 期 10 UNIQUE = 48%**——接近半数触发 UNIQUE，强烈建议拆。

## 关键观察（v3.4 必拆 exec + process）

**v3.0 → v3.3 四期趋势**：
- v3.0: 2 new (exec + edit) - 反弹
- v3.1: 3 new (exec + process + edit) - 三连反弹
- v3.2: 1 new (exec) - 回稳
- v3.3: 2 new (exec + process) - 反弹

process 累积 10/21 UNIQUE（48%）接近半数反弹，强烈建议 v3.4 拆 process。

## 下一步建议

- [ ] **v3.4: exec args 前缀聚类专项**（21 期 21 UNIQUE，必拆）
- [ ] **v3.4: process 超时防护场景细分**（10 期 UNIQUE，48% 占比，必拆）
- [ ] **v3.4: edit 操作类型细分**（4 期 UNIQUE 连续反弹，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
