# ROADMAP v12.0 — 5 库 evidence v2 接入 + 章节号升级

> 日期：2026-08-15 12:33
> 分支：master
> 状态：🟢 DONE（5 库 v2 接入 + 7 候选 evidence 升级）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| 7 候选 evidence | ✅ 5/5 升级到 v2.0（章节号格式） |
| `cross_library_auto.py --validate` | ✅ 0 warning |
| pytest | ✅ 9/9 (test_cross_library_auto.py) |
| 7/7 GEP strict | ✅ PASS（schema 1.12.1） |

## v12.0 变更明细

| # | 变更 | 状态 | commit |
|---|------|------|--------|
| 1 | 7 候选 `cross_library_evidence` 升级 v2.0 | ✅ | (本次) |
| 2 | 5 库章节号格式对齐（BeautifulMathematics Ch12/17、cell-biology Ch15、CognitivePsychology Ch6、OpenStaxBiology Ch01、evomap GEP v1.12.1 §2.3） | ✅ | (本次) |
| 3 | 每条 evidence 关联 v10.2 字段补全（scope/confidence/trigger） | ✅ | (本次) |
| 4 | `evidence_version: v2.0` 字段写入 7 候选 | ✅ | (本次) |

## v2.0 evidence 格式（参考 `gene_harness_append_only_event_stream.json`）

**旧格式**（v1.0，单层短语）：
```
"BeautifulMathematics 幂等性保证"
"cell-biology 反馈回路"
"evomap GEP 协议"
```

**新格式**（v2.0，章节号 + 字段关联）：
```
"BeautifulMathematics Ch12 算法: exec = 长串命令的算法流水线，v10.2 confidence=0.75 来自 65 期演化"
"cell-biology Ch15 信号传导: exec 重复调用 = 高频信号 → 反馈回路"
"evomap GEP v1.12.1 §2.3 EvolutionEvent: exec 工具调用落 event_stream，触发 Solidify safe reject 守护"
```

## 升级前后对比

| 维度 | v1.0 | v2.0 |
|------|------|------|
| 章节号 | ❌ | ✅ ChXX / §X.X |
| 字段关联 | ❌ | ✅ confidence/trigger/scope |
| 可追溯性 | 部分 | 完整 |
| 入门门槛 | 5 字 | 50 字 |

## 7 候选 evidence v2.0 概览

| 文件 | BeautifulMathematics | cell-biology | CognitivePsychology | OpenStaxBiology | evomap |
|---|---|---|---|---|---|
| 000:exec | Ch12 算法流水线 | Ch15 信号反馈 | Ch6 长时记忆 | Ch01 进化适应 | §2.3 EvolutionEvent |
| 001:read | Ch17 信息熵 | Ch15 选择性摄取 | Ch6 记忆锚点 | Ch01 信息论 | §2.3 事件流 |
| 002:process | Ch12 状态机 | Ch15 适应 TTL | Ch6 一般化 | Ch01 方法论 | §2.3 演化 |
| 003:write_file | Ch12 单写者 | Ch15 反馈回路 | Ch6 一般化 | Ch01 方法论 | §2.3 演化 |
| 004:edit | Ch12 CAS | Ch15 基因突变 | Ch6 确认偏误 | Ch01 DNA 修复 | §2.3 演化变异 |
| 005:message | Ch12 FIFO | Ch15 反馈 | Ch6 长时记忆 | Ch01 进化 | §2.3 a2a |
| 006:write | Ch12 单写者 | Ch15 反馈 | Ch6 记忆锚点 | Ch01 进化 | §2.3 工具 |

## 下一步（v13.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | 把 7 候选 cross_library_evidence v2.0 接入到 5 库匹配脚本（cross_library_auto.py） | 让 evidence 自动生成含章节号 |
| B | 跨 5 库 evidence 神经元网络（建立 evidence 之间的关联） | 科学严谨 |
| C | 写今晚 2 份 learnings（误删 / 简单说事） | 反思教训 |

## 严禁事项（5 条铁律 + 1 条新加）

按 SOUL 三不铁律 + 2026-08-15 新加第 5 条：

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v12.0 是 **5 库 evidence v2.0 接入版本**：7 候选 evidence 升级到章节号格式 + 字段关联，`--validate` 0 warning。下一步 v13.0 候选 A/B/C 待胡老师拍板。
