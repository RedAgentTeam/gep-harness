# ROADMAP v13.0 — 5 库 evidence v2.0 自动生成（章节号 + 字段关联）

> 日期：2026-08-15 12:55
> 分支：master
> 状态：🟢 DONE（5 库 v2.0 自动化 + 12/12 pytest）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest | ✅ 12/12 (test_cross_library_auto.py) |
| 7 候选 evidence | ✅ v2.0 章节号格式（hand-applied） |
| 自动生成 v2.0 | ✅ cross_library_auto.py `version=v2.0` |
| `cross_library_auto.py --validate` | ✅ 0 warning |

## v13.0 变更明细

| # | 变更 | 状态 | commit |
|---|------|------|--------|
| 1 | `cross_library_auto.py` 加 `LIBRARY_CHAPTER` 字典（5 库章节号） | ✅ | 8a6a86d |
| 2 | `auto_cross_library_evidence(gene, version="v2.0")` 字段支持 | ✅ | 8a6a86d |
| 3 | 3 个新测试（章节号齐全 / v1 vs v2 差异 / 字典完整） | ✅ | 8a6a86d |
| 4 | ROADMAP_v13.md | ✅ | (本次) |
| 5 | `make evolve-full` 验证 v2.0 自动化 | ✅ | (本次) |
| 6 | 写今晚 2 份 learnings | ✅ | (本次) |

## v2.0 evidence 输出格式

**v1.0**（旧）：
```
BeautifulMathematics 幂等性保证
cell-biology 反馈回路
evomap GEP 协议
```

**v2.0**（新）：
```
BeautifulMathematics Ch12 算法: 高频事件：大数定律 → 期望收敛
cell-biology Ch15 信号传导: 高频：neuronal firing rate 上限 ~200Hz
evomap GEP v1.12.1 §2.3 EvolutionEvent: 高频：batch merge 减少 round-trip
```

## 5 库章节号映射

| 库 | 章节号 | 来源 |
|---|---|---|
| BeautifulMathematics | Ch12 算法 | 算法流水线 + 哈希 |
| cell-biology | Ch15 信号传导 | 信号转导 + 反馈回路 |
| CognitivePsychology | Ch6 长时记忆 | 记忆锚点 + 长时记忆 |
| OpenStaxBiology | Ch01 进化 | 进化适应 + 自然选择 |
| evomap | GEP v1.12.1 §2.3 EvolutionEvent | GEP 协议 + 事件流 |

## 下一步（v14.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | 跨 5 库 evidence 神经元网络（建立 evidence 之间的关联） | B 路径 |
| B | 7 候选 evidence 自动跑 v2.0 重生成（覆盖 v12.0 手写） | 自动化升级 |
| C | 撤回今晚改的 7 候选 evidence，恢复 v10 旧版 | 回滚 |

## 严禁事项（5 条铁律 + 1 条新加）

按 SOUL 三不铁律 + 2026-08-15 新加第 5 条：

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v13.0 是 **5 库 evidence v2.0 自动化版本**：脚本支持 v2.0 输出 + 12/12 pytest + 0 warning。下一步 v14.0 候选 A/B/C 待胡老师拍板。
