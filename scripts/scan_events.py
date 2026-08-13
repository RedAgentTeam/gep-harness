"""Scan events.jsonl to extract tool_call patterns.

Stage 3 (Evolver) - Scan phase.

Usage:
  python3 scan_events.py --since=24h
  python3 scan_events.py --input=/data/disk/gep-harness/openclaw-harness/events/events.jsonl
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_EVENTS = "/data/disk/gep-harness/openclaw-harness/events/events.jsonl"


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def scan(events_path: str, since_hours: float = 24.0) -> dict:
    """Aggregate tool_call patterns from events.jsonl."""
    if not Path(events_path).exists():
        return {"error": f"events.jsonl not found at {events_path}"}

    cutoff = datetime.now(timezone.utc).timestamp() - since_hours * 3600

    by_tool = Counter()
    by_session = Counter()
    arg_keys_by_tool = defaultdict(set)
    error_count = 0
    total = 0

    with open(events_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = parse_iso(ev["ts"]).timestamp()
            if ts < cutoff:
                continue

            total += 1
            kind = ev.get("kind", "")
            tool = ev.get("tool_name", "")

            if kind == "tool_call_before":
                by_tool[tool] += 1
                by_session[ev.get("session_id", "")[:20]] += 1
                args = ev.get("args", {})
                if isinstance(args, dict):
                    for k in args.keys():
                        arg_keys_by_tool[tool].add(k)
            elif kind == "tool_call_after":
                result = ev.get("result", {})
                if isinstance(result, dict) and result.get("error"):
                    error_count += 1

    return {
        "total_events": total,
        "by_tool": dict(by_tool.most_common()),
        "by_session_prefix": dict(by_session.most_common(10)),
        "arg_keys_by_tool": {k: sorted(v) for k, v in arg_keys_by_tool.items()},
        "errors": error_count,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=DEFAULT_EVENTS)
    p.add_argument("--since", type=str, default="24h", help="since N hours (e.g. 24h, 7d)")
    args = p.parse_args()

    # parse --since: "24h" → 24.0, "7d" → 168.0
    s = str(args.since).strip()
    if s.endswith("d"):
        since_h = float(s[:-1]) * 24
    elif s.endswith("h"):
        since_h = float(s[:-1])
    else:
        since_h = float(s)
    result = scan(args.input, since_h)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()