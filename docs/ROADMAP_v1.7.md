# ROADMAP v1.7 — GEP Harness Evolver 收敛阶段（high decay）

> 日期：2026-08-14 06:20
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 36/36（31 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 1 new + 6 DUPLICATE |

## v1.6 → v1.7 收敛分析

| 项 | v1.6 | v1.7 |
|----|------|------|
| new UNIQUE | 4 | 1 |
| DUPLICATE | 3 | 6 |
| 占比 | 43% | 86% |

**观察**：v1.7 进入 **high decay 阶段**——6/7 候选与 v1.5/v1.6 重复，说明 hotpath 工具已基本被前几轮固化，只有 exec 持续高频产生新候选。

## v1.7 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 1 个 (exec_hotpath_v17) |
| DUPLICATE 处理 | 6 个跳过 |
| commit | 2cdd04b |
| events | 5948 lines |

## 高频工具稳定性分析

| Tool | 24h calls | v1.3 | v1.4 | v1.5 | v1.6 | v1.7 |
|------|-----------|------|------|------|------|------|
| exec | 2395 | new | new | new | new | new |
| read | 123 | new | dup | new | new | dup |
| process | 97 | new | new | new | new | dup |
| write_file | 90 | new | new | new | new | dup |
| edit | 81 | new | dup | new | new | dup |
| write | 44 | new | dup | new | dup | dup |
| message | 32 | new | dup | new | dup | dup |

**收敛趋势**：v1.7 仅 exec 维持 UNIQUE，其他 6 个工具已在 v1.3-v1.6 固化。exec 因为命令多样性高（不同 args），每次 scan 都产生新候选。

## 下一步建议

- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 合并 v0.5~v1.7 升级路径到 ROADMAP.md
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
- [ ] exec 多样性模式聚类（按 args 前缀拆分）
