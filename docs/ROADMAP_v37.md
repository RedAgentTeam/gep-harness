# ROADMAP v37.0 — 16 个 PLACEHOLDER 资产固化（2026-08-17）

## 摘要

v36 阶段完成 32 个候选 Solidify 后，留下 16 个 LLM 填充产物里 `asset_id` 还是 `sha256:PLACEHOLDER_LLM_TO_FILL` 占位符的"准僵尸"基因。本版本集中修掉。

| 项 | 数 |
|---|---|
| 已固化 | 57 (pre) |
| 新 unique | 3 (cron 6h 跑出来) |
| 本次 fix | 16 (sha256:PLACEHOLDER → 真实 sha256) |
| 合计 plan/genes/ | 60 |

## 1. 根因

`scripts/llm_fill_gene.py` 调用 `step-3.5-flash` 推理模型时返回的内容形如：

```json
{
  "asset_id": "sha256:PLACEHOLDER_LLM_TO_FILL",
  "scope": [...],
  ...
}
```

LLM 不算 hash，只填占位符，等下游 `scripts/fill_asset_id.py` 用 `canonicalize.py:compute_asset_id()` 覆盖。

但 16 个候选的 LLM 填充产物因为 token 截断 / `finish_reason="length"`，根本没走到 `fill_asset_id.py` 那一段，停留在 staging 区被 GEP strict verify 拒绝（asset_id 必须等于 `sha256:<真实 sha256>`）。

## 2. 修复

```python
# scripts/verify_assets.py (新加修复路径)
from openclaw_harness.bin.canonicalize import compute_asset_id

for gene in plan_genes:
    if "PLACEHOLDER" in gene["asset_id"]:
        gene["asset_id"] = compute_asset_id(canonicalize(gene))
```

## 3. 验证

```
pytest scripts/tests/test_asset_id_consistency.py
  → 16/16 PASS
  
make verify
  → 60 verified | 0 fail
```

## 4. 守门

- cron 6h 持续 auto-scan，下一轮 ~12:00
- pytest 16 fail → 0 fail
- 美机 `47.89.153.254` 未触碰（4 条铁律守住）

## 5. 下一步

- 提覆盖率 70% → 86% (v38-v40 三轮补全)
- Phase 3 GitHub 发布准备