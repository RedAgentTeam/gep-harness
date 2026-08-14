# ROADMAP v1.8 — GEP Harness Evolver 反弹期（exec 多样性 + 工具重启）

> 日期：2026-08-14 09:40
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 41/41（36 genes + 2 capsules + 3 events）|
| `make evolve` | ✅ 7 candidates, 5 new + 2 DUPLICATE |

## v1.7 → v1.8 反弹分析

| 期 | new | dup | 占比 |
|----|-----|-----|------|
| v1.7 | 1 | 6 | 86% dup |
| v1.8 | 5 | 2 | 29% dup |

**反弹原因**：3 小时累计（5948 → 6398，+450 events），高频工具出现新的 arg patterns：
- exec: 2395 → 2593（+198 calls，命令持续高频）
- read: 123 → 127（+4 calls）
- process: 97 → 101（+4 calls，超时防护新场景）
- write_file: 90 → 92（+2 calls）
- edit: 81 → 81（持平，DUPLICATE）
- write: 44 → 44（持平，DUPLICATE）
- message: 32 → 42（+10 calls，频率上升）

## v1.8 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 5 个 (exec/read/process/write_file/message hotpath_v18) |
| DUPLICATE 处理 | 2 个 (edit/write 与 v1.5 同) |
| commit | 137bd17 |
| events | 6398 lines |

## 收敛趋势（v1.3~v1.8）

| 期 | new | dup | 节点 |
|----|-----|-----|------|
| v1.3 | 7 | 0 | 爆发 |
| v1.4 | 3 | 4 | 收敛开始 |
| v1.5 | 6 | 1 | 震荡 |
| v1.6 | 4 | 3 | 二次收敛 |
| v1.7 | 1 | 6 | high decay |
| v1.8 | 5 | 2 | 反弹（exec 多样性） |

## 下一步建议

- [ ] LLM 真实填充（402 quota 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] 干掉 legacy `gene_candidate_*` 命名混乱
- [ ] exec 多样性模式聚类（按 args 前缀拆分）
- [ ] process 超时防护场景细化（process 长跑命令专项 Gene）
- [ ] message 频率上升 → 批量合并 Gene 深挖
