# GEP Harness — Makefile
#
# C2 fix (P0-4 真闭环): all recipes use $(CURDIR) — the directory where
# `make` is invoked — instead of hard-coded absolute paths. This lets the
# Makefile work in any clone location, including the GitHub Actions runner
# which clones to /home/runner/work/gep-harness/gep-harness.

.PHONY: help verify test replay clean status install uninstall evolve evolve-full solidify-pending docs-lint docs-update

help:
	@echo "GEP Harness — available commands:"
	@echo "  make verify       — Re-run GEP strict validation on all assets"
	@echo "  make test         — Run pytest on all suites"
	@echo "  make replay       — Show recent events from events.jsonl"
	@echo "  make status       — Show events count + verify result"
	@echo "  make install      — Install plugin to OpenClaw"
	@echo "  make uninstall    — Remove plugin from OpenClaw"
	@echo "  make clean        — Truncate events.jsonl (back up first!)"
	@echo "  make evolve       — Run Evolver (Scan → Extract → Validate, dry-run)"
	@echo "  make evolve-full  — Run full cycle + auto-fill + list pending Solidify"
	@echo "  make solidify-pending — Show pending Solidify candidates (manual approval)"
	@echo "  make docs-lint    — Check README/CHANGELOG consistency"
	@echo "  make docs-update  — Auto-update README from repo state"

verify:
	@echo "=== GEP strict validation ==="
	@python3 $(CURDIR)/scripts/verify_assets.py

test:
	@echo "=== pytest (openclaw-harness) ==="
	@cd $(CURDIR)/openclaw-harness && python3 -m pytest tests/ -q
	@echo "=== pytest (scripts/ + openclaw-a2a/) ==="
	@cd $(CURDIR) && python3 -m pytest scripts/tests/ openclaw-a2a/tests/ -q

replay:
	@echo "=== Last 10 events ==="
	@tail -n 10 $(CURDIR)/openclaw-harness/events/events.jsonl | python3 $(CURDIR)/scripts/replay_events.py

status:
	@echo "=== events.jsonl count ==="
	@wc -l $(CURDIR)/openclaw-harness/events/events.jsonl
	@echo "=== strict verify ==="
	@python3 $(CURDIR)/scripts/verify_assets.py

install:
	@echo "=== Installing plugin ==="
	@openclaw plugins install $(CURDIR)/openclaw-harness-plugin --force

uninstall:
	@echo "=== Uninstalling plugin ==="
	@openclaw plugins uninstall harness-event-stream

clean:
	@echo "⚠️  This will truncate events.jsonl — back up first!"
	@echo "Run: cp $(CURDIR)/openclaw-harness/events/events.jsonl /tmp/events.bak"
	@echo "Then: make clean-confirm"
	@echo "(intentionally not deleting in one step)"

evolve:
	@echo "=== Evolver full workflow (dry-run) ==="
	@python3 $(CURDIR)/scripts/scan_events.py --since=24h > /tmp/v_scan.json
	@rm -rf /tmp/v_staging && mkdir -p /tmp/v_staging
	@python3 $(CURDIR)/scripts/extract_candidate_genes.py --scan-output=/tmp/v_scan.json --output=/tmp/v_staging/ --threshold=5
	@python3 $(CURDIR)/scripts/validate_gep.py --mode=strict --input="/tmp/v_staging/*.json"
	@echo "=== Staging candidates ready (Solidify + LLM fill required) ==="
	@echo "  Run: python3 scripts/cross_library_auto.py /tmp/v_staging/"
	@echo "  Run: python3 scripts/solidify.py --list --staging=/tmp/v_staging/"

evolve-full:
	@echo "=== Evolver full cycle (auto-fill + list pending Solidify) ==="
	@python3 $(CURDIR)/scripts/scan_events.py --since=24h > /tmp/v_scan.json
	@rm -rf /tmp/v_staging && mkdir -p /tmp/v_staging
	@python3 $(CURDIR)/scripts/extract_candidate_genes.py --scan-output=/tmp/v_scan.json --output=/tmp/v_staging/ --threshold=5
	@python3 $(CURDIR)/scripts/cross_library_auto.py /tmp/v_staging/ > /tmp/v_fill.log 2>&1
	@python3 $(CURDIR)/scripts/validate_gep.py --mode=strict --input="/tmp/v_staging/*.json"
	@echo "=== ✅ staging filled + validated ==="
	@echo "=== ⏳ Pending: manual Solidify approval ==="
	@python3 $(CURDIR)/scripts/solidify.py --list --staging=/tmp/v_staging/

solidify-pending:
	@echo "=== Pending Solidify candidates ==="
	@python3 $(CURDIR)/scripts/solidify.py --list --staging=/tmp/v_staging/

docs-lint:
	@echo "=== docs lint (README/CHANGELOG consistency) ==="
	@python3 $(CURDIR)/scripts/docs_lint.py --print

docs-update:
	@echo "=== docs update (auto-sync README numbers) ==="
	@python3 $(CURDIR)/scripts/docs_lint.py --update