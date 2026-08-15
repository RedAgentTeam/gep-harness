# ROADMAP v14.0 — 跨 5 库 evidence 神经元网络（闭环互引）

> 日期：2026-08-15 13:00
> 分支：master
> 状态：🟢 DONE（5 库闭环互引 + 16/16 pytest）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest | ✅ 16/16 (test_cross_library_auto.py) |
| 5 库闭环 | ✅ 每库被引 ≥1 次（无自引） |
| `cross_library_auto.py --validate` | ✅ 0 warning |
| 7 候选 evidence v2.0 | ✅ 章节号手写版（v12.0 commit） |

## v14.0 变更明细

| # | 变更 | 状态 | commit |
|---|------|------|--------|
| 1 | `cross_library_auto.py` 加 `LIBRARY_GRAPH` 字典（5 库关联图） | ✅ | fdcb48e |
| 2 | `auto_cross_library_evidence(gene, version="v3.0")` 支持 | ✅ | fdcb48e |
| 3 | 4 个新测试（互引 / 闭环 / 无自引 / 5 库齐全） | ✅ | fdcb48e |
| 4 | v3.0 evidence 输出：v2.0 + 跨库互引 | ✅ | fdcb48e |

## 5 库闭环路径

```
BeautifulMathematics → CognitivePsychology → OpenStaxBiology → evomap → cell-biology → BeautifulMathematics
```

每库指向 2 个相关库，形成 cross-reference ring（神经元网络）。

## v3.0 evidence 输出格式

```
BeautifulMathematics Ch12 算法: 高频事件：大数定律 → 期望收敛
  → [CognitivePsychology Ch6 长时记忆] → [evomap GEP v1.12.1 §2.3 EvolutionEvent]
cell-biology Ch15 信号传导: 高频：neuronal firing rate 上限 ~200Hz
  → [BeautifulMathematics Ch12 算法] → [OpenStaxBiology Ch01 进化]
CognitivePsychology Ch6 长时记忆: 高频：practice effect 自动化
  → [OpenStaxBiology Ch01 进化] → [cell-biology Ch15 信号传导]
OpenStaxBiology Ch01 进化: 高频：r/K selection r-strategist
  → [evomap GEP v1.12.1 §2.3 EvolutionEvent] → [BeautifulMathematics Ch12 算法]
evomap GEP v1.12.1 §2.3 EvolutionEvent: 高频：batch merge 减少 round-trip
  → [cell-biology Ch15 信号传导] → [CognitivePsychology Ch6 长时记忆]
```

每条 evidence 末尾含 2 个 `→ [关联库 章节号]` 引用。

## 收益对比

| 维度 | v2.0 | v3.0 |
|------|------|------|
| 章节号 | ✅ | ✅ |
| 字段关联 | ✅ | ✅ |
| 跨库互引 | ❌ | ✅ |
| 路径可追溯性 | 1 条 | 4 条（每条 evidence 可追溯 4 个关联） |
| 鲁棒性 | 1 evidence 失效断链 | 关联网络反推 |

## 下一步（v15.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | 7 候选 evidence 自动跑 v3.0 重生成（覆盖 v12.0 手写版） | 升级一致 |
| B | 撤回今晚 2 次误删（git history 已留，但写 1 份 learnings） | 反思 |
| C | 历史索引 v1.4~v14 共 80+ 期 ROADMAP | 文档 |

## 严禁事项（5 条铁律 + 1 条新加）

按 SOUL 三不铁律 + 2026-08-15 新加第 5 条：

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v14.0 是 **跨 5 库 evidence 神经元网络版本**：5 库闭环互引，每条 evidence 含 2 个 `→ [关联库]` 引用。下一步 v15.0 候选 A/B/C 待胡老师拍板。
