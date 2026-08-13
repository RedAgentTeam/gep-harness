"""Adaptive GDI threshold — adjusts min_gdi based on peer acceptance rate.

Stage 4.3 — v0.5 enhancement.

Logic:
  - Reads audit.jsonl for the last N sync rounds (default 20).
  - Computes acceptance_rate = accepted / sent (clamped 0.05–0.95).
  - If acceptance_rate > 0.8 → raise threshold (send only strong genes).
  - If acceptance_rate < 0.3 → lower threshold (give peer more to work with).
  - Otherwise → keep current threshold.
  - Clamps result to [0.3, 0.85].

Usage:
  python3 adaptive_gdi.py --pool-dir=data/pool --audit=data/audit.jsonl
  python3 adaptive_gdi.py --pool-dir=data/pool --audit=data/audit.jsonl --current=0.7 --window=10
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_audit_events(audit_path: Path, window: int = 20) -> list[dict]:
    """Load last N sync audit events from audit.jsonl."""
    if not audit_path.exists():
        return []
    events = []
    with open(audit_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                if evt.get("action") == "sync_to_peer":
                    events.append(evt)
            except json.JSONDecodeError:
                continue
    return events[-window:]


def compute_acceptance_rate(events: list[dict]) -> float | None:
    """Compute acceptance rate from audit events.

    Returns None if no valid events.
    """
    sent_events = [e for e in events if e.get("sent", 0) > 0]
    if not sent_events:
        return None
    total_sent = sum(e.get("sent", 0) for e in sent_events)
    total_accepted = sum(e.get("accepted", 0) for e in sent_events)
    if total_sent == 0:
        return None
    return total_accepted / total_sent


def adaptive_threshold(
    current: float = 0.7,
    acceptance_rate: float | None = None,
    *,
    lo: float = 0.3,
    hi: float = 0.85,
    step_up: float = 0.05,
    step_down: float = 0.05,
) -> float:
    """Compute adaptive GDI threshold.

    Args:
        current: current threshold (used when acceptance_rate is None)
        acceptance_rate: peer acceptance rate in [0, 1] (None = keep current)
        lo: floor for threshold
        hi: ceiling for threshold
        step_up: how much to raise when rate is high
        step_down: how much to lower when rate is low

    Returns:
        New threshold in [lo, hi]
    """
    if acceptance_rate is None:
        return max(lo, min(hi, current))

    if acceptance_rate > 0.8:
        # Peer is generous — raise bar to only send high-quality genes
        new_threshold = current + step_up
    elif acceptance_rate < 0.3:
        # Peer is rejecting most — lower bar to feed more candidates
        new_threshold = current - step_down
    else:
        # Healthy range — keep current
        new_threshold = current

    return round(max(lo, min(hi, new_threshold)), 2)


def main():
    p = argparse.ArgumentParser(description="Adaptive GDI threshold calculator")
    p.add_argument("--pool-dir", type=Path, default=Path("data/pool"),
                   help="Gene Pool directory (unused, reserved)")
    p.add_argument("--audit", type=Path, default=Path("data/audit.jsonl"),
                   help="Audit log path")
    p.add_argument("--current", type=float, default=0.7,
                   help="Current min_gdi threshold")
    p.add_argument("--window", type=int, default=20,
                   help="Number of recent sync rounds to consider")
    p.add_argument("--json", action="store_true",
                   help="Output as JSON")
    args = p.parse_args()

    events = load_audit_events(args.audit, window=args.window)
    rate = compute_acceptance_rate(events)
    new_threshold = adaptive_threshold(args.current, rate)

    if args.json:
        print(json.dumps({
            "current": args.current,
            "acceptance_rate": rate,
            "new_threshold": new_threshold,
            "events_considered": len(events),
            "window": args.window,
        }, indent=2))
    else:
        print(f"[adaptive_gdi] window={args.window} events={len(events)}")
        if rate is not None:
            print(f"[adaptive_gdi] acceptance_rate={rate:.1%} "
                  f"current={args.current:.2f} → new={new_threshold:.2f}")
        else:
            print(f"[adaptive_gdi] no sync events found, keep current={args.current:.2f}")
        print(f"[adaptive_gdi] new_threshold={new_threshold:.2f}")


if __name__ == "__main__":
    main()
