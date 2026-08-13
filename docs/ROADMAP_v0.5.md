# ROADMAP v0.5 — GEP Harness 迭代计划

> 日期：2026-08-14
> 分支：feat/auth-hardening

## 总览

| 优先级 | 任务 | 状态 | 完成时间 |
|---|---|---|---|
| P1 | CRDT LWW 合并 | ✅ done | 02:30 |
| P1 | LLM fill pytest（mock）| ✅ done | 02:45 |
| P2 | GDI 动态阈值 | ✅ done | 03:00 |
| P3 | A2A broadcast 模式 | ✅ done | 03:12 |

## 详细

### P1 — CRDT LWW 合并
- `a2a_protocol.py`: `GenePool._scan_conflicts()` + `_apply_lww()`
- `accept()` 中 LWW 覆盖写入 + loser → `conflicts/`
- 4 个 pytest（idempotent / overwrite / loser_move / audit）

### P1 — LLM fill pytest（mock）
- `test_llm_fill.py`: 8 个 pytest（mock API + protected fields + evidence/strategy count）
- `conftest.py`: auto sys.path inject
- Stepfun API 402 quota exceeded → mock 测试走通

### P2 — GDI 动态阈值
- `adaptive_gdi.py`: `acceptance_rate` → 步进 ±0.05，clamp [0.3, 0.85]
- `test_adaptive_gdi.py`: 11 个 pytest（threshold, rate, window, missing file）

### P3 — A2A broadcast 模式
- `gene_sync.py`: `discover_peers()` + `broadcast_to_peers()` + `announce_peer()`
- `a2a_protocol.py`: `GET /api/v1/a2a/nodes` + `POST /api/v1/a2a/announce`
- `gene_sync.py` CLI: `--broadcast` / `--bootstrap` / `--announce`
- `test_gene_sync.py`: 7 个 pytest（全部通过）

## 当前状态（2026-08-14 03:12）

- **pytest: 48/48 passed**（8 a2a + 7 gene_sync + 8 llm_fill + 4 harness + 10 tool_pipeline + 11 gdi）
- **git:** `68be020`（独立 repo bootstrap）
