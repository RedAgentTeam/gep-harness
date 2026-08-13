# GEP Harness — Makefile
# 标准管理命令（Project Standard SOP）

.PHONY: help verify test replay clean status install uninstall

help:
	@echo "GEP Harness — available commands:"
	@echo "  make verify     — Re-run GEP strict validation on all 6 assets"
	@echo "  make test       — Run 4 pytest on event_stream"
	@echo "  make replay     — Show recent events from events.jsonl"
	@echo "  make status     — Show plugin + events count + verify result"
	@echo "  make install    — Install plugin to OpenClaw"
	@echo "  make uninstall  — Remove plugin from OpenClaw"
	@echo "  make clean      — Truncate events.jsonl (back up first!)"

verify:
	@echo "=== GEP strict validation (6 assets) ==="
	@cd /data/disk/gep-harness/plan && python3 -c "
import json, sys, glob
sys.path.insert(0, '/data/disk/gep-harness/openclaw-harness/bin')
from canonicalize import compute_asset_id
for path in sorted(glob.glob('genes/*.json') + glob.glob('capsules/*.json') + glob.glob('events/*.json')):
    obj = json.load(open(path))
    computed = compute_asset_id(obj)
    claimed = obj.get('asset_id','')
    ok = '✅' if computed == claimed else '❌'
    print(f'{ok} {obj.get(\"type\",\"?\"):14s} {obj.get(\"id\",\"?\"):50s}')
"

test:
	@echo "=== pytest 4/4 ==="
	cd /data/disk/gep-harness/openclaw-harness && python3 -m pytest tests/test_event_stream.py -v

replay:
	@echo "=== Last 10 events ==="
	@tail -10 /data/disk/gep-harness/openclaw-harness/events/events.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    e = json.loads(line)
    print(f\"  {e.get('kind','?'):25s} tool={e.get('tool_name','-'):15s} asset={e['asset_id'][:24]}...\")
"

status:
	@echo "=== Gateway status ==="
	@systemctl --user is-active openclaw-gateway 2>&1 | head -1
	@echo "=== Plugin status ==="
	@openclaw plugins list 2>&1 | grep -A 1 "Harness Event\|harness-event" | head -5
	@echo "=== events.jsonl count ==="
	@wc -l /data/disk/gep-harness/openclaw-harness/events/events.jsonl
	@echo "=== strict verify ==="
	@python3 /data/disk/gep-harness/openclaw-harness/bin/event_emitter.py verify

install:
	@echo "=== Installing plugin ==="
	openclaw plugins install /data/disk/gep-harness/openclaw-harness-plugin --force

uninstall:
	@echo "=== Uninstalling plugin ==="
	openclaw plugins uninstall harness-event-stream

clean:
	@echo "⚠️  This will truncate events.jsonl — back up first!"
	@echo "Run: cp /data/disk/gep-harness/openclaw-harness/events/events.jsonl /tmp/events.bak"
	@echo "Then: make clean-confirm"
	@echo "(intentionally not deleting in one step)"