# GEP Harness — Makefile
# 标准管理命令（Project Standard SOP）
# 所有 recipe 都是单行命令；复杂 python 逻辑在 scripts/ 目录下

.PHONY: help verify test replay clean status install uninstall evolve

help:
	@echo "GEP Harness — available commands:"
	@echo "  make verify     — Re-run GEP strict validation on all assets"
	@echo "  make test       — Run pytest on event_stream"
	@echo "  make replay     — Show recent events from events.jsonl"
	@echo "  make status     — Show events count + verify result"
	@echo "  make install    — Install plugin to OpenClaw"
	@echo "  make uninstall  — Remove plugin from OpenClaw"
	@echo "  make clean      — Truncate events.jsonl (back up first!)"
	@echo "  make evolve     — Run Evolver (Scan → Extract → Validate → Fill dry-run)"

verify:
	@echo "=== GEP strict validation ==="
	@python3 /data/disk/gep-harness/scripts/verify_assets.py

test:
	@echo "=== pytest ==="
	@cd /data/disk/gep-harness/openclaw-harness && python3 -m pytest tests/ -q

replay:
	@echo "=== Last 10 events ==="
	@tail -n 10 /data/disk/gep-harness/openclaw-harness/events/events.jsonl | python3 /data/disk/gep-harness/scripts/replay_events.py

status:
	@echo "=== events.jsonl count ==="
	@wc -l /data/disk/gep-harness/openclaw-harness/events/events.jsonl
	@echo "=== strict verify ==="
	@python3 /data/disk/gep-harness/scripts/verify_assets.py

install:
	@echo "=== Installing plugin ==="
	@openclaw plugins install /data/disk/gep-harness/openclaw-harness-plugin --force

uninstall:
	@echo "=== Uninstalling plugin ==="
	@openclaw plugins uninstall harness-event-stream

clean:
	@echo "⚠️  This will truncate events.jsonl — back up first!"
	@echo "Run: cp /data/disk/gep-harness/openclaw-harness/events/events.jsonl /tmp/events.bak"
	@echo "Then: make clean-confirm"
	@echo "(intentionally not deleting in one step)"

evolve:
	@echo "=== Evolver full workflow ==="
	@python3 /data/disk/gep-harness/scripts/scan_events.py --since=24h > /tmp/v_scan.json
	@rm -rf /tmp/v_staging && mkdir -p /tmp/v_staging
	@python3 /data/disk/gep-harness/scripts/extract_candidate_genes.py --scan-output=/tmp/v_scan.json --output=/tmp/v_staging/ --threshold=5
	@python3 /data/disk/gep-harness/scripts/validate_gep.py --mode=strict --input="/tmp/v_staging/*.json"
	@python3 /data/disk/gep-harness/scripts/llm_fill_gene.py --staging=/tmp/v_staging/ --dry-run
	@echo "=== evolve done (Solidify requires manual review) ==="
