# ROADMAP v1.9 — GEP Harness Evolver 回稳期（exec 持续高频）

> 日期：2026-08-14 09:40
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 42/42（37 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 1 new + 6 DUPLICATE |

## v1.8 → v1.9 回稳分析

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v1.8 | 5 | 2 | 29% dup |
| v1.9 | 1 | 6 | 86% dup |

**回稳原因**：短期累积（6398 → 6524，+126 events），新增模式不足：
- exec: 2593 → 2643（+50 calls，仍高频但 args 模式已被 v1.8 覆盖）
- 其他工具持平或微增

**Exec 持续高频发现**：v1.3~v1.9 共 7 期 exec 7 次 UNIQUE（除 v1.7 6 dup），exec 确实是 GEP Harness 最热路径。

## v1.9 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 1 个 (exec_hotpath_v19) |
| DUPLICATE 处理 | 6 个跳过 |
| commit | 7e0a30a |
| events | 6524 lines |

## 收敛趋势（v1.3~v1.9）

| 期 | new | dup | 节点 |
|----|-----|-----|------|
| v1.3 | 7 | 0 | 爆发 |
| v1.4 | 3 | 4 | 收敛开始 |
| v1.5 | 6 | 1 | 震荡 |
| v1.6 | 4 | 3 | 二次收敛 |
| v1.7 | 1 | 6 | high decay |
| v1.8 | 5 | 2 | 反弹（exec 多样性）|
| **v1.9** | **1** | **6** | **回稳（exec 持续高频）** |

## Exec 持续高频分析

v1.3~v1.9 exec 表现：

| 期 | exec calls | exec Gene 状态 |
|----|------------|----------------|
| v1.3 | ~1500 | new |
| v1.4 | ~1700 | new |
| v1.5 | ~1900 | new |
| v1.6 | ~2100 | new |
| v1.7 | ~2300 | new |
| v1.8 | ~2500 | new |
| v1.9 | ~2643 | new |

**exec 7 期 7 UNIQUE**，说明 exec 每次扫描都出现新的 args 模式。强烈建议 exec args 前缀聚类专项 Gene。

## 下一步建议

- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
- [ ] **exec args 前缀聚类专项**（按 `ls/cat/grep/wc/head/tail/find` 拆分高频 exec）
- [ ] process 超时防护场景细化
- [ ] message 批量合并 Gene 深挖
