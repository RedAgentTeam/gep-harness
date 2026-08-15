# Contributing to gep-harness

> **Date:** 2026-08-15
> **Status:** v14.0 active development
> **License:** MIT

## Quick Start

```bash
git clone https://github.com/<owner>/gep-harness.git
cd gep-harness
make verify        # GEP strict validation (7/7)
make test          # pytest 16/16
```

## Development Workflow

```
PLAN → BUILD → DIFF → QA → APPROVAL → APPLY → DOCS
```

### 1. PLAN

- Identify if your change requires new files (avoid creating unnecessary files)
- Cite existing code patterns and `docs/` references
- Propose plan; wait for operator approval

### 2. BUILD

- Implement on a sandbox branch
- Minimize changes; follow existing patterns
- Do NOT modify `master` directly

### 3. DIFF

- Show unified diff
- Explain rationale, integration points, references

### 4. QA

- Run `make verify` (GEP strict)
- Run `make test` (pytest)
- Check `--validate` for 5-library cross-references

### 5. APPROVAL

- Operator (Red Ho) approves with `y/N` per asset
- Solidify is manual; auto-fill by cron is safe-rejected by `--non-interactive`

### 6. APPLY

- Apply to sandbox branch
- Verify result

### 7. DOCS

- Update `docs/ROADMAP_vN.md` (one version per milestone)
- Create `learnings/` entry if you discovered a new failure mode

## 3 Untouchable Rules

**DO NOT** violate these — they are the project's foundation:

1. ❌ **No Skill abstraction** — use Gene/Capsule (~230 tokens policy unit)
2. ❌ **No runtime plugin loading** — Cordis-style dynamic injection dilutes Gene signal matching precision
3. ❌ **No automatic Solidify** — must go through manual approval (CognitivePsychology 9 biases + Arrow's theorem)

## Coding Style

| Aspect | Convention |
|--------|-----------|
| File naming | snake_case.json for assets |
| Python | PEP 8 + type hints |
| Commit format | `gep-harness v{N}: <topic>` |
| ROADMAP | One file per version in `docs/` |
| Tests | `scripts/tests/test_*.py` with pytest |

## Testing Requirements

Before submitting a PR:

- [ ] `make verify` passes (GEP strict 7/7)
- [ ] `make test` passes (pytest 16/16+)
- [ ] `cross_library_auto.py --validate` shows 0 warnings
- [ ] If you modified `plan/genes/`, include `--validate` output in PR description

## Adding a New Gene

```python
# scripts/extract_candidate_genes.py
# Use the existing template; do not bypass Solidify
# New genes must include:
# - scope: list of contexts (e.g. ['openclaw', 'gep-harness', 'history', 'tool:hotpath:{tool}'])
# - confidence: 0.0-1.0
# - trigger: list of trigger conditions
# - cross_library_evidence: 5 entries (one per library with chapter reference)
```

## Production Deployment Restrictions

⚠️ **Production nodes (e.g. 美机 <美机生产 IP>) require explicit operator confirmation.**

Before any production change:

1. Ask the operator: "在哪台机器做？"
2. Wait for explicit `y` approval
3. Document the change in `plan/events/`
4. Verify rollback path

## Code Review

- 2 reviewers for `plan/genes/` changes
- 1 reviewer for docs/scripts changes
- Operator final approval for Solidify

## Reporting Issues

Use GitHub Issues with labels:
- `bug` — confirmed defect
- `enhancement` — proposed improvement
- `docs` — documentation issue
- `runtime-learning` — agent runtime failure mode

## Communication

- 中文 / English both supported
- Avoid jargon without definition
- Reference `docs/ROADMAP_v*.md` and `learnings/` when discussing history

## See Also

- `README.md` (中文) / `README.en.md` (English)
- `OPEN_SOURCE_PLAN.md` — open-source preparation checklist
- `docs/SOLIDIFY.md` — Solidify guard rules
- `learnings/runtime-learning-2026-08-15-full-recap.md` — 4-phase recap