# ROADMAP v2.3 — GEP Harness Evolver 持续稳定（exec 11 期 11 UNIQUE）

> 日期：2026-08-14 10:25
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 47/47（42 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 1 new + 6 DUPLICATE |

## v2.2 → v2.3 稳定分析

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v2.2 | 1 | 6 | 86% dup |
| v2.3 | 1 | 6 | 86% dup |

**完全稳定**：v2.2 与 v2.3 收敛特征完全相同，exec 持续高频 UNIQUE。

## v2.3 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 1 个 (exec_hotpath_v23) |
| DUPLICATE 处理 | 6 个 (read/process/write_file/edit/write/message 与 v1.5/v1.8/v2.0 同) |
| commit | 51020cf |
| events | 6870 lines |

## 收敛趋势（v1.3~v2.3）

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
| **v2.3** | **1** | **6** | **完全稳定** |

## Exec 11 期 11 UNIQUE — 强烈拆解信号

v1.3~v2.3 共 11 期 exec 表现：

| 期 | exec calls | 增量 | UNIQUE |
|----|------------|------|--------|
| v1.3 | ~1500 | — | ✅ |
| v1.4 | ~1700 | +200 | ✅ |
| v1.5 | ~1900 | +200 | ✅ |
| v1.6 | ~2100 | +200 | ✅ |
| v1.7 | ~2300 | +200 | ✅ |
| v1.8 | ~2500 | +200 | ✅ |
| v1.9 | ~2643 | +143 | ✅ |
| v2.0 | ~2699 | +56 | ✅ |
| v2.1 | ~2719 | +20 | ✅ |
| v2.2 | ~2785 | +66 | ✅ |
| v2.3 | ~2833 | +48 | ✅ |

**Exec 11 期 11 UNIQUE 已确定**——这是结构性问题，必须拆解。

## 关键观察（v3.0 必拆 exec）

**exec 11 期 11 UNIQUE 是结构性问题**：
- exec 命令多样性高（不同 args），单 exec Gene 覆盖不全
- 11 期每次都 different，但内容相似（都关于 exec timeout/exit code/log）
- v3.0 必须拆 exec：按 args 前缀（`ls/cat/grep/wc/head/tail/find`）

## 下一步建议

- [ ] **v3.0: exec args 前缀聚类专项**（必拆——exec 11 期 11 UNIQUE）
- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
- [ ] process 超时防护场景细化
- [ ] message 批量合并 Gene 深挖
