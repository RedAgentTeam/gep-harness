# ROADMAP v0.6 — GEP Harness 阶段 2 工具调用流水线

> 日期：2026-08-14
> 分支：feat/auth-hardening

## v0.5 完成 → v0.6 阶段 2

### P1（已完成）
- CRDT LWW → 4 pytest
- LLM fill pytest（mock）→ 8 pytest
- GDI 动态阈值 → 11 pytest
- A2A broadcast 模式 → 7 pytest

### P2 阶段 2：工具调用流水线（当前）
- `openclaw-harness-tool-pipeline-plugin/index.js`：before/after hook + permission check + redact
- `openclaw-harness/tests/test_tool_pipeline.py`：7 pytest（all passed）
- `openclaw-harness/scripts/scan_events.py`：工具调用聚类
- `openclaw-harness/scripts/extract_candidate_genes.py`：候选 Gene 模板
- `openclaw-harness/scripts/validate_gep.py`：GEP strict 校验
- `openclaw-harness/tests/test_evolver.py`：3 pytest（all passed）

## 全量结果（2026-08-14 03:13）

- **pytest: 45/45 passed**（8 a2a_protocol + 7 gene_sync + 10 adaptive_gdi + 4 event_stream + 3 evolver + 8 llm_fill + 7 tool_pipeline）
- **git:** `087a50d`（v0.5）→ 待 commit v0.6
