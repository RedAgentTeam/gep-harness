# GEP Harness — Solidify 流程文档

> 最后更新：2026-08-15 01:15
> 状态：✅ 当前实现 v10.1

## 什么是 Solidify

**Solidify** = 将 `staging/` 中的 candidate Gene **人工审批**后写入 `plan/genes/` 的过程。

按 GEP v1.12.1 strict 协议要求，每个 Gene 必须经过：
1. **GEP strict validate**（必过）
2. **5 库 cross_library_evidence 检查**（5 库各一条）
3. **DUPLICATE 检查**（与现有 plan/genes/ 不重复）
4. **人工审批门**（用户显式 y/N 确认）
5. **asset_id canonicalize 验证**（sha256 + exclude_fields）
6. **写入 plan/genes/ + plan/events/event_solidify_*.json + git commit**

## 为什么 Solidify 不能全自动

CognitivePsychology 9 大认知错觉 + Arrow 定理：
- **确认偏误（confirmation bias）**：LLM 自动填充会让相同 signals 反复生成相似 Gene
- **锚定效应（anchoring）**：第一个候选会"锚定"后续评估
- **Dunning-Kruger**：模型对"自己生成的 Gene 看起来对"过度自信

**结论**：Solidify 必须有**人工审批门**，LLM/Evolver 只负责候选 + 验证，不负责最终 Solidify。

## Solidify 当前实现（v10.1）

### 命令

```bash
# 1. 列出待审批 candidates（dry-run safe）
python3 scripts/solidify.py --list --staging=/tmp/v_staging/

# 2. 交互式审批（手动）
python3 scripts/solidify.py --staging=/tmp/v_staging/

# 3. 自动审批（仅用于 --yes 模式）
python3 scripts/solidify.py --staging=/tmp/v_staging/ --yes

# 4. 非交互模式（cron 安全，无 stdin 时 auto-reject）
python3 scripts/solidify.py --staging=/tmp/v_staging/ --non-interactive
```

### 模式对比

| 模式 | stdin | 用户输入 | 行为 |
|------|-------|----------|------|
| 默认 | 必须 | y/N | 每次候选询问 |
| `--yes` | 不要 | 不问 | 自动全部 approved |
| `--non-interactive` | 无 / EOF | 跳过 | **auto-reject**（safe） |
| `--list` | 不要 | 不要 | 只列出，不修改 |

### 完整闭环（make evolve-full）

```bash
make evolve-full
# 等价于：
# 1. scan_events --since=24h → /tmp/v_scan.json
# 2. extract_candidate_genes (threshold=5) → /tmp/v_staging/
# 3. cross_library_auto → 填充 5 库 evidence
# 4. validate_gep --mode=strict
# 5. solidify --list --non-interactive → 列待审批清单
```

### Solidify 单 Gene 审批

```bash
# 只审批一个
python3 scripts/solidify.py --gene=/path/to/candidate.json --yes
```

## Solidify 产出文件

每次 Solidify 成功：
- `plan/genes/{filename}.json` — Gene 资产（vetted）
- `plan/events/event_solidify_{gene_id}.json` — EvolutionEvent 记录
- git commit（v10.1 自动 commit）

## Solidify 失败模式（defensive）

| 情况 | 行为 |
|------|------|
| GEP strict 失败 | auto-reject + 提示 validate_failed |
| DUPLICATE 命中现有 | 询问"仍要审批?"（手动决策） |
| asset_id 不匹配 | auto-reject（asset_id_mismatch） |
| 无 stdin + `--non-interactive` | auto-reject（non_interactive） |
| EOFError | auto-reject（eof） |

## Solidify 历史（今晚）

| 时间 | commit | 数量 | 备注 |
|------|--------|------|------|
| 21:54 | b89961a | 7 | 第一批，assify list-only |
| 00:14 | 889f88e | 7 | 第二批，asset_id mismatch 修复（11aacdf 后续） |
| 01:15 | bebb6c6 | — | v10.1 commit（含 solidify.py 改进 + pytest） |

## Solidify 改进路线（v11+）

- [ ] **多用户审批**：超过 1 个 reviewer 才能 Solidify 高风险 Gene
- [ ] **Solidify 影响评估**：自动扫描 plan/genes/ 中相似 Gene，提示可能冲突
- [ ] **Solidify diff**：Solidify 前展示 candidate + 现有相似 Gene 的 diff
- [ ] **回滚命令**：`solidify.py --rollback {gene_id}` 撤回最近一次 Solidify
- [ ] **Capsule 关联**：Solidify 时自动绑定相关 Capsule

## 防越权（SOUL 第 5 条铁律）

Solidify **只能**写 `plan/genes/` 和 `plan/events/`——**严禁触碰**：
- `/opt/goapi/`
- `/opt/a2a/`（A2A mock_peer 部署在生产节点）
- `/etc/goapi/credentials.env`
- 美机（47.89.153.254）任何文件
- 美机 goapi.service / redapi.service / systemd

任何"在 Solidify 里加一段部署 goapi"的尝试——立即拒绝 + 写 learnings。

## 相关脚本

| 脚本 | 用途 |
|------|------|
| `scripts/scan_events.py` | 扫描 events.jsonl 找高频 pattern |
| `scripts/extract_candidate_genes.py` | 提取 candidate Gene（threshold 过滤） |
| `scripts/cross_library_auto.py` | 5 库 evidence 自动填充 |
| `scripts/validate_gep.py` | GEP strict 校验 |
| `scripts/solidify.py` | 人工审批门（v10.1: --non-interactive + EOFError 安全） |
| `scripts/llm_fill_gene.py` | LLM 填充（⚠️ StepFun reasoning model 不适合，已 WARNING） |

---

## v10.2 修订记录（2026-08-15）

**触发**：7 个 v0.9 已批准候选缺 `scope` / `confidence` / `trigger` 字段，影响 Gene→Capsule 路由精度。

**修订方案**（Plan B，按科学严谨 → 有效 → 合理 → 合规 4 维度排序）：

| 字段 | 旧 | 新 |
|---|---|---|
| `scope` | ❌ 缺失 | `[openclaw, gep-harness, history, tool:hotpath:{tool}]` |
| `confidence` | ❌ 缺失 | `0.75`（65 期演化实证，但机器生成 < 0.82~0.86） |
| `trigger` | ❌ 缺失 | `[65_phases_evolution, hotpath_tool:{tool}, auto_reject_safe_v10.1, gdi_threshold:0.95]` |

**清理动作**：
- `scripts/clean_legacy_genes.py --execute` 删 130 历史重复 + 重命名 1 双前缀
- 手动清理 5 个二次副本（含 2 次误删恢复，git + tar 兜底）
- 7 个 v0.9 已批准真实候选保留

**校验**：
- pytest 9/9 PASS
- 7/7 GEP strict PASS（schema 1.12.1）
- 8 个 EvolutionEvent 留审计链（7 个 `evt_revise_*` + 1 个 `evt_audit_*`）

**Solidify 路径**：v10.1 `--non-interactive` + EOFError 安全守门，cron 6h 跑出的二次副本自动 reject。

**Commit**：`4514f6a gep-harness v10.2: Plan B 落地 - 修 7 个候选字段 + 8 审计事件`
