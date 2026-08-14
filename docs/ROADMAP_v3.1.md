# ROADMAP v3.1 — GEP Harness Evolver 三连反弹（exec 19/19 + process 9/19 + edit 4/19）

> 日期：2026-08-14 10:45
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 62/62（57 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 3 new + 4 DUPLICATE |

## v3.0 → v3.1 三连反弹

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v3.0 | 2 | 5 | 71% dup |
| v3.1 | 3 | 4 | 57% dup |

**三连反弹**：exec + process + edit 三工具全部 UNIQUE。

## v3.1 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 3 个 (exec_hotpath_v31 + process_hotpath_v31 + edit_hotpath_v31) |
| DUPLICATE 处理 | 4 个 (read/write_file/write/message 与 v1/v2 同) |
| commit | a5456a5 |
| events | 7628 lines |

## 收敛趋势（v1.3~v3.1）

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
| **v3.1** | **3** | **4** | **三连反弹** |

## 高频工具累计 UNIQUE 次数（v1.3~v3.1 共 19 期）

| Tool | UNIQUE 次数 | 状态 |
|------|-------------|------|
| exec | 19 | 持续高频（必拆）|
| process | 9 | 反弹高频（建议拆）|
| read | 4 | 部分高频 |
| write_file | 5 | 部分高频 |
| edit | 4 | 连续反弹（v3.0/v3.1 连续 2 期）|
| write | 4 | 部分高频 |
| message | 5 | 反弹 |

**Exec 19 期 19 UNIQUE 持续高频**——结构性问题必拆。

## 关键观察（v3.2 必拆 exec + process + edit）

**v3.0 → v3.1 三连反弹**：
- exec 3177 calls（19 期 19 UNIQUE）
- process 115 calls（v2.4/v2.5/v2.8/v3.1 累计 9 期 UNIQUE）
- edit 89 calls（v2.0/v3.0/v3.1 累计 4 期 UNIQUE）

**v3.2 强烈建议拆解**：
1. **exec args 前缀聚类**（19 期 19 UNIQUE，必拆）
2. **process 超时防护场景细分**（9 期 UNIQUE，建议拆）
3. **edit 操作类型细分**（4 期 UNIQUE 连续反弹，建议拆）

## 下一步建议

- [ ] **v3.2: exec args 前缀聚类专项**（19 期 19 UNIQUE，必拆）
- [ ] **v3.2: process 超时防护场景细分**（9 期 UNIQUE，建议拆）
- [ ] **v3.2: edit 操作类型细分**（4 期 UNIQUE 连续反弹，建议拆）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
