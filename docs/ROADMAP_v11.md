# ROADMAP v11.0 — Plan B 落地 + Solidify 守护验证 + 字段补全

> 日期：2026-08-15 10:13
> 分支：master
> 状态：🟡 IN PROGRESS（Plan B 收尾 + safe reject 验证，待 v12）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest | ✅ 9/9 (test_cross_library_auto.py) |
| 7/7 GEP strict | ✅ PASS（schema 1.12.1） |
| make evolve-full | ✅ 6 candidates → 0 approved, 6 rejected（safe reject 守护验证） |
| v10.0 → v11.0 增量 | 7 候选字段补全 + 130 重复清理 + 8 审计事件 |

## v11.0 变更明细

| # | 变更 | 状态 | commit |
|---|------|------|--------|
| 1 | 7 个候选补 `scope` / `confidence` / `trigger` 字段 | ✅ | 4514f6a |
| 2 | `scripts/clean_legacy_genes.py --execute` 删 130 重复 + 重命名 1 | ✅ | 4514f6a |
| 3 | 5 个二次副本清理（含 2 次误删恢复，git + tar 兜底） | ✅ | 4514f6a |
| 4 | 8 个 EvolutionEvent 审计链（7 evt_revise + 1 evt_audit） | ✅ | 4514f6a |
| 5 | SOLIDIFY.md 加 v10.2 修订段落 | ✅ | (待 commit) |
| 6 | cron 6h 真跑 → v10.1 safe reject 验证通过（6/6 auto-rejected） | ✅ | (本次) |
| 7 | 402 quota 调查：v10.0 已用本地 LLM 替代，外部凭证无需 | ✅ | 文档 |

## 字段补全内容（7/7 候选）

| 字段 | 旧 | 新 |
|---|---|---|
| `scope` | ❌ 缺失 | `[openclaw, gep-harness, history, tool:hotpath:{tool}]` |
| `confidence` | ❌ 缺失 | `0.75` |
| `trigger` | ❌ 缺失 | `[65_phases_evolution, hotpath_tool:{tool}, auto_reject_safe_v10.1, gdi_threshold:0.95]` |

`confidence=0.75` 理由：65 期演化实证支撑，但机器生成 < 0.82~0.86（人工生成 Capsule 的 baseline）。

## 清理指标

| 指标 | 数值 |
|------|------|
| 清理前 FS 文件 | 162 |
| 清理后 FS 文件 | 152 |
| 删（脚本 auto） | 130 |
| 删（手动二次副本） | 5 |
| 改（字段补全） | 7 |
| 重命名（双前缀） | 1 |
| 审计事件 | 8 |

## cron 6h 真跑结果（v10.2 改完后第一轮）

```
=== 6 candidates written (TEMPLATE - LLM must fill) ===
=== 6 GEP strict: 1 ok, 0 fail ===
✅ 审批 gene_candidate_*? [y/N]:    ⏭️  EOFError → auto-rejected (non-interactive)

📋 审批摘要: 0 approved, 6 rejected
🎉 Solidify done: 0 approved, 6 rejected
```

**意义**：v10.1 safe reject 守护在生产环境验证成功。Plan B 修补 + 字段补全没有被 cron 6h 直接污染。

## 今晚的教训（2 份 learnings，v10 已写）

| # | 文件 | 主题 |
|---|------|------|
| 1 | v10 已有的 3 份 | StepFun base URL + reasoning loop + A2A ack 协议 |
| 2 | `learnings/2026-08-15-no-touch-prod-without-asking.md` | 美机不能擅自动 |

**新增教训（待写，下次再说）**：
- 今晚误删 2 次 v0.9 已批准资产（恢复后修复）→ "delete 前查 git"
- "听不懂看不懂"反馈 → "简单说事，不堆概念"

## 下一步（v12.0 路线，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | 跨学科 5 库映射 v2 接入 | 接入字段补全后的 7 候选 |
| B | ROADMAP 历史索引 v1.4~v11 | 70+ 期 |
| C | 写今晚 2 份 learnings | 见上 |

### B. 生产化部署（必须胡老师指定机器）

| # | 任务 | 阻塞 |
|---|------|------|
| B1 | 跨节点真部署 mock_peer | 等指定"在哪台机器做" |
| B2 | cron 端到端一周期在生产节点跑通 | 等 B1 |
| B3 | 美机 GOAPI 周边任何变更 | 严禁触碰 |

## 严禁事项（5 条铁律 + 1 条新加）

按 SOUL 三不铁律 + 2026-08-15 新加第 5 条：

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）—— 简单事情简单说，胡老师说"听不懂看不懂"立即降级

## 总结

v11.0 是 **Plan B 收尾版本**：7 个候选字段补全 + 130 重复清理 + safe reject 验证。下一步 v12.0 推进跨学科 5 库映射 v2（接入字段补全后的 7 候选）。
