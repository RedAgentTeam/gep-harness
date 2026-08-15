# GEP Harness — OpenClaw Self-Evolving Foundation

> **Version:** v14.0 (Phase 1-4 closed loop)
> **Date:** 2026-08-15
> **Author:** devagent @ Red Ho's instruction
> **Protocol:** GEP v1.12.1 (strict)
> **License:** MIT

## Project Positioning

**OpenClaw system borrows DeepSeek's open-source Harness. Without introducing Skill abstraction, plugin runtime, or breaking the Gene/Capsule system, it rebuilds OpenClaw's Harness foundation.**

4 phases complete + Phase 4 sub-stages all done:

| Phase | Goal | Status |
|-------|------|--------|
| **Phase 1** | Append-only event stream (session trajectory foundation) | ✅ DONE |
| **Phase 2** | Tool call pipeline (Hook→Permission→Timeout→Execute→Rewrite→Emit) | ✅ DONE |
| **Phase 3** | Evolver semi-auto (Scan/Signal/Mutate auto + Solidify manual) | ✅ DONE |
| **Phase 4** | Cross-discipline 5 libraries (BeautifulMathematics / cell-biology / CognitivePsychology / OpenStaxBiology / evomap) | ✅ DONE |

## 3 Untouchable Rules

1. **No Skill abstraction** — OpenClaw uses Gene/Capsule (~230 tokens policy unit)
2. **No runtime plugin loading** — Cordis-style dynamic injection dilutes Gene signal matching precision
3. **Solidify must go through manual approval** — 9 cognitive biases from CognitivePsychology + Arrow's theorem

## Current Status (2026-08-15 v14.0)

| Dimension | Data |
|-----------|------|
| ROADMAP versions | 75 (v0.5 ~ v14.0) |
| Genes | 152 (cleaned to 7 candidates) |
| Events | 19+ EvolutionEvent |
| pytest | 16/16 (test_cross_library_auto.py) |
| GEP strict | 7/7 |
| Cross-discipline 5 libraries | v3.0 neural network (closed-loop cross-reference) |
| Security | Local running / Production deployment NOT started |

## 4-Phase Closed Loop

1. **Borrow** (v0.4 ~ v1.0): DeepSeek Harness article + 3 untouchable rules
2. **Self-Evolve** (v1.0 ~ v10.0): Evolver semi-auto + 65 phases evolution + cron 6h
3. **Collaboration Network** (v10.0 ~ v10.1): A2A bidirectional 157/157 + safe reject guard
4. **Cross-Discipline 5 Libraries** (v12.0 ~ v14.0): v3.0 neural network + runtime learning recap

## Quick Start

```bash
cd /data/disk/gep-harness
make verify        # GEP strict validation
make test          # pytest 16/16
make evolve-full   # Full cycle + auto-fill + list pending Solidify
make solidify-pending  # Show pending Solidify candidates
```

## Documentation Index

- `docs/ROADMAP_INDEX.md` — 75-phase ROADMAP historical index
- `docs/ROADMAP_v14.md` — Latest ROADMAP
- `docs/SOLIDIFY.md` — Solidify guard rules + v10.2 revision record
- `learnings/runtime-learning-2026-08-15-full-recap.md` — 4-phase complete recap
- `OPEN_SOURCE_PLAN.md` — Open-source preparation checklist

## License

MIT — see `LICENSE`.