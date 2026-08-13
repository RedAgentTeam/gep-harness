"""Tests for adaptive_gdi.py — adaptive GDI threshold logic."""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

from adaptive_gdi import (  # noqa: E402
    adaptive_threshold,
    compute_acceptance_rate,
    load_audit_events,
)


def _make_audit(accepted: int, sent: int, n_rounds: int = 1) -> list[dict]:
    """Build fake audit events with total accepted/sent across n_rounds."""
    events = []
    a_per_round = accepted // max(n_rounds, 1)
    s_per_round = sent // max(n_rounds, 1)
    for i in range(n_rounds):
        events.append({
            "ts": f"2026-08-14T0{i}:00:00Z",
            "action": "sync_to_peer",
            "sent": s_per_round,
            "accepted": a_per_round,
            "rejected": s_per_round - a_per_round,
        })
    return events


def test_adaptive_threshold_high_acceptance_raises():
    """acceptance_rate > 0.8 → threshold raised."""
    result = adaptive_threshold(current=0.7, acceptance_rate=0.9)
    assert result == 0.75, f"expected 0.75, got {result}"


def test_adaptive_threshold_low_acceptance_lowers():
    """acceptance_rate < 0.3 → threshold lowered."""
    result = adaptive_threshold(current=0.7, acceptance_rate=0.2)
    assert result == 0.65, f"expected 0.65, got {result}"


def test_adaptive_threshold_mid_keeps():
    """acceptance_rate in [0.3, 0.8] → threshold unchanged."""
    assert adaptive_threshold(current=0.7, acceptance_rate=0.5) == 0.7
    assert adaptive_threshold(current=0.7, acceptance_rate=0.3) == 0.7
    assert adaptive_threshold(current=0.7, acceptance_rate=0.8) == 0.7


def test_adaptive_threshold_clamped_floor():
    """Threshold should not go below lo=0.3."""
    result = adaptive_threshold(current=0.35, acceptance_rate=0.1)
    assert result >= 0.30, f"floor violated: {result}"


def test_adaptive_threshold_clamped_ceiling():
    """Threshold should not exceed hi=0.85."""
    result = adaptive_threshold(current=0.82, acceptance_rate=0.95)
    assert result <= 0.85, f"ceiling violated: {result}"


def test_adaptive_threshold_none_rate():
    """acceptance_rate=None → keep current."""
    result = adaptive_threshold(current=0.5, acceptance_rate=None)
    assert result == 0.5


def test_compute_acceptance_rate():
    """acceptance_rate = accepted / sent."""
    events = _make_audit(accepted=80, sent=100)
    rate = compute_acceptance_rate(events)
    assert rate == 0.80


def test_compute_acceptance_rate_no_sent():
    """No sent events → None."""
    rate = compute_acceptance_rate(_make_audit(accepted=0, sent=0))
    assert rate is None


def test_compute_acceptance_rate_empty():
    """Empty events → None."""
    assert compute_acceptance_rate([]) is None


def test_load_audit_events_window():
    """load_audit_events should return at most window events."""
    events = _make_audit(accepted=100, sent=100, n_rounds=50)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
        f.flush()
        loaded = load_audit_events(Path(f.name), window=20)
    assert len(loaded) == 20


def test_load_audit_events_missing_file():
    """Missing audit file → empty list."""
    result = load_audit_events(Path("/nonexistent/audit.jsonl"))
    assert result == []


if __name__ == "__main__":
    tests = [
        ("high_acceptance_raises", test_adaptive_threshold_high_acceptance_raises),
        ("low_acceptance_lowers", test_adaptive_threshold_low_acceptance_lowers),
        ("mid_keeps", test_adaptive_threshold_mid_keeps),
        ("clamped_floor", test_adaptive_threshold_clamped_floor),
        ("clamped_ceiling", test_adaptive_threshold_clamped_ceiling),
        ("none_rate", test_adaptive_threshold_none_rate),
        ("acceptance_rate", test_compute_acceptance_rate),
        ("no_sent", test_compute_acceptance_rate_no_sent),
        ("empty", test_compute_acceptance_rate_empty),
        ("window", test_load_audit_events_window),
        ("missing_file", test_load_audit_events_missing_file),
    ]
    for name, fn in tests:
        fn()
        print(f"✅ {name}")
    print(f"\n=== {len(tests)}/11 tests passed ===")
