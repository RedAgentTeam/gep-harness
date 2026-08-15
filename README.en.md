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
---

## Directory Structure

```
/data/disk/gep-harness/
├── README.md                          # Chinese README
├── README.en.md                       # English README (this file)
├── Makefile                           # Management commands
├── LICENSE                            # MIT
├── CONTRIBUTING.md                    # Contribution guide
├── AI_AUTHORSHIP.md                   # AI-driven development disclosure
├── OPEN_SOURCE_PLAN.md                # Open-source prep checklist
├── GITHUB_SETUP.md                    # GitHub publishing guide
├── .github/workflows/ci.yml           # GitHub Actions CI
│
├── plan/
│   ├── genes/                         # Solidified Gene assets
│   ├── capsules/                      # Capsule assets
│   └── events/                        # EvolutionEvent audit trail
│
├── scripts/                           # Core scripts
│   ├── cross_library_auto.py          # 5-library evidence auto-gen
│   ├── visualize_5lib_graph.py        # PNG/SVG/PDF/EPS visualization
│   ├── solidify.py                    # Solidify approval gate
│   ├── validate_gep.py                # GEP strict validation
│   ├── generate_changelog.py          # CHANGELOG auto-gen
│   ├── clean_legacy_genes.py          # Duplicate Gene cleanup
│   ├── auto_changelog_commit.py       # CHANGELOG auto-commit
│   └── tests/                         # pytest suite
│
├── openclaw-harness/                  # Phase 1: event stream
├── openclaw-a2a/                      # Phase 3: A2A collaboration
├── openclaw-harness-plugin/           # Phase 2: tool pipeline
├── openclaw-harness-tool-pipeline-plugin/
│
├── examples/                          # 7 reproducible examples (local-only)
├── docs/                              # ROADMAPs + SOLIDIFY + THREAT_MODEL + audit
├── learnings/                         # Runtime learning (e.g. simple-talk, verify-file-before-delete)
└── CHANGELOG.md                       # Auto-generated
```

## Quick Start

```bash
cd /data/disk/gep-harness
make verify        # GEP strict validation
make test          # pytest 59/59
make evolve-full   # Full cycle + auto-fill + list pending Solidify
```

## 3 Untouchable Rules

1. ❌ No Skill abstraction — OpenClaw uses Gene/Capsule (~230 tokens policy unit)
2. ❌ No runtime plugin loading — Cordis-style dynamic injection dilutes Gene signal precision
3. ❌ No automatic Solidify — manual approval only (Arrow's impossibility theorem)

## Cross-Discipline 5 Libraries (Heuristic, not Gate)

| Library | Chapter |
|---------|---------|
| BeautifulMathematics | Ch12 Algorithms |
| cell-biology | Ch15 Signal Transduction |
| CognitivePsychology | Ch6 Long-term Memory |
| OpenStaxBiology | Ch01 Evolution |
| evomap | GEP v1.12.1 §2.3 EvolutionEvent |

**Usage boundary**: 5-library mapping is a heuristic, not a gate. Required for irreversible architectural decisions and "automation vs human review" choices; optional for routine changes.

Each evidence entry should carry a `reviewed: bool` field distinguishing manually-verified analogies from LLM auto-generated candidates.

## Reproducible Scripts (Local, No Production Dependencies)

| Script | Description |
|--------|-------------|
| `examples/01_local_evolver.py` | Local Evolver one-cycle |
| `examples/02_cross_library_evidence.py` | 5-library evidence v3.0 auto-gen |
| `examples/03_a2a_bidirectional.py` | A2A bidirectional sync (port 19890/19891) |
| `examples/04_pytest_integration.py` | pytest integration + cross-library |
| `examples/05_png_generation.py` | 5-library PNG generation (needs graphviz) |
| `examples/06_safe_reject_demo.py` | Solidify safe-reject guard demo |
| `examples/07_png_svg_demo.py` | PNG + SVG dual-format visualization |

All scripts run on local <本机 dev IP> (VM-0-11-ubuntu), **not** on production node <美机生产 IP> (untouched).

## Current Roadmap (v14.0+ Pending)

| # | Task | Status |
|---|------|--------|
| 1 | HMAC → ed25519 keypair migration | 🟡 Pending (v15.0+) |
| 2 | TLS 1.3 for A2A protocol | 🟡 Pending |
| 3 | Replay protection (nonce + timestamp) | 🟡 Pending |
| 4 | Cross-node Gene sync human second-approval | 🟡 Pending |
| 5 | External security audit | 🔴 Critical |

## Key Design Decisions (Inherited Principles)

1. **Borrow from DeepSeek Harness** — 3 untouchable rules (see above)
2. **Self-evolve via Evolver + append-only event stream** — preserves auditability
3. **Manual Solidify + auto-reject guard** — Arrow's impossibility theorem (no full automation)
4. **A2A + Gene sync via ed25519** — multi-node collaboration with verifiable provenance
5. **Cross-discipline 5 libraries as heuristic** — reasoning aid, not gate

## Acknowledgments

> This project exists because of people who helped me at different stages.

### evomap.ai

My only knowledge source — I had no computer science background before. The project from zero to one stands on this system.

- Repo: https://github.com/EvoMap
- GEP SDK: https://github.com/EvoMap/gep-sdk-js

### Teacher Zhang Haoyang

Founder of evomap.ai. Without his support, this project would not have been possible.

> **Theoretical source**: The core theory of this project comes from Teacher Zhang Haoyang's *Self-Evolving Harness and Collaboration Networks*.

### Teacher Ba Rui

The article *《不会省Token的货车司机不是好极客》* (A Truck Driver Who Can't Save Tokens Is Not a Good Geek) helped amplify this direction to a wider audience.

### Teacher Klaus

Working at Baidu. Helped me clarify my thinking and direction, gave encouragement. In my most confused moments, these conversations were fuel to keep moving forward.

### Teacher Zhang Yuxin (善用佳软)

A well-known software recommendation blogger, deep IT efficiency-tools user (AutoHotkey / Total Commander), currently focused on Tsinghua history research. His AI-application philosophy (博观而约取, "read broadly and select carefully") shares roots with this project's Agent-autonomous development model. He represents the early practice of the engineering tradition of "AI-assisted personal cognition" that gep-harness inherits.

## Next Step Entry

After this commit, next steps are documented in:
- `docs/ROADMAP_INDEX.md` — 75+ ROADMAP history index
- `OPEN_SOURCE_PLAN.md` — open-source preparation checklist
- `docs/THREAT_MODEL.md` — A2A / Gene sync threat model

To enter "next iteration" mode: read `learnings/runtime-learning-2026-08-15-modification-recap.md` + `MEMORY.md` + `ROADMAP_INDEX.md` before continuing.

## About the Author

**RedAgentTeam** (Hu Lao-Shi / Red Ho)

- No computer science background — AI-assisted cognition is the project's foundational philosophy
- Driver (货拉拉) by trade, AI knowledge monetization as goal
- Project maintains strict SOUL + 3 Untouchable Rules
- See `AI_AUTHORSHIP.md` for the full AI-driven development disclosure

## License

MIT — see [LICENSE](./LICENSE).
