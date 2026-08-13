"""Replay last 10 events — used by Makefile replay target."""
import json
import sys

for line in sys.stdin:
    try:
        e = json.loads(line)
    except Exception:
        continue
    kind = e.get("kind", "?")
    tool = e.get("tool_name", "-")
    print(f"  {kind:25s} tool={tool:15s}")
