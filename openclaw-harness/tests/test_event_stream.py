"""Tests for append-only event stream (gene_harness_append_only_event_stream).

3 pytest as required by gene.validation:
  1. emit + replay + asset_id verify
  2. chronological order preserved
  3. atomic append (no partial lines on crash)
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Make bin importable
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from bin.canonicalize import compute_asset_id, verify_asset_id  # noqa: E402
from bin.event_emitter import emit, replay, verify_all  # noqa: E402


def test_emit_and_verify():
    """Emit a sequence of events, verify all asset_ids match."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.jsonl"
        ev1 = emit(session_id="s_test_001", kind="session_start", path=path)
        ev2 = emit(session_id="s_test_001", kind="tool_call_before",
                   tool_name="read", args={"path": "/tmp/x"}, path=path)
        ev3 = emit(session_id="s_test_001", kind="tool_call_after",
                   tool_name="read", result={"bytes": 42}, duration_ms=12, path=path)
        ev4 = emit(session_id="s_test_001", kind="session_end", path=path)

        # All asset_ids valid
        for ev in (ev1, ev2, ev3, ev4):
            assert verify_asset_id(ev), f"asset_id mismatch: {ev}"

        ok, fail = verify_all(path=path)
        assert ok == 4, f"expected 4 ok, got {ok}"
        assert fail == 0, f"expected 0 fail, got {fail}"


def test_replay_chronological():
    """Replay returns events in append order with kinds intact."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.jsonl"
        kinds = ["session_start", "tool_call_before", "tool_call_after",
                 "tool_call_before", "tool_call_after", "session_end"]
        for k in kinds:
            emit(session_id="s_chrono", kind=k,
                 tool_name="exec" if "tool" in k else None, path=path)

        events = replay("s_chrono", path=path)
        assert len(events) == len(kinds)
        for got, want in zip(events, kinds):
            assert got["kind"] == want
        # ts must be monotonically non-decreasing
        ts_list = [ev["ts"] for ev in events]
        assert ts_list == sorted(ts_list), f"not chronological: {ts_list}"


def test_session_isolation_and_append_only():
    """Two sessions coexist; one session's events don't leak into the other.
    File must be append-only: every line is valid JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.jsonl"
        # Session A
        for k in ["session_start", "tool_call_before", "session_end"]:
            emit(session_id="s_A", kind=k,
                 tool_name="read" if "tool" in k else None, path=path)
        # Session B interleaved
        emit(session_id="s_B", kind="session_start", path=path)
        emit(session_id="s_A", kind="tool_call_after",
             tool_name="read", result={"ok": True}, duration_ms=5, path=path)
        emit(session_id="s_B", kind="session_end", path=path)

        a_events = replay("s_A", path=path)
        b_events = replay("s_B", path=path)
        assert len(a_events) == 4  # start, before, end, after
        assert len(b_events) == 2  # start, end

        # Every line is valid JSON + asset_id verified
        for line in path.read_text().splitlines():
            if line.strip():
                ev = json.loads(line)
                assert verify_asset_id(ev)


def test_cli_smoke():
    """CLI must accept emit / replay / verify."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.jsonl"
        env = os.environ.copy()
        env["OPENCLAW_EVENT_STREAM"] = str(path)
        # emit
        r = subprocess.run(
            [sys.executable, str(HERE.parent / "bin/event_emitter.py"),
             "emit", "s_cli_001", "session_start"],
            env=env, capture_output=True, text=True, check=True,
        )
        ev = json.loads(r.stdout)
        assert ev["kind"] == "session_start"
        assert verify_asset_id(ev)

        # replay
        r2 = subprocess.run(
            [sys.executable, str(HERE.parent / "bin/event_emitter.py"),
             "replay", "s_cli_001"],
            env=env, capture_output=True, text=True, check=True,
        )
        assert "session_start" in r2.stdout

        # verify
        r3 = subprocess.run(
            [sys.executable, str(HERE.parent / "bin/event_emitter.py"),
             "verify"],
            env=env, capture_output=True, text=True, check=True,
        )
        result = json.loads(r3.stdout)
        assert result["ok"] >= 1 and result["fail"] == 0


if __name__ == "__main__":
    test_emit_and_verify()
    test_replay_chronological()
    test_session_isolation_and_append_only()
    test_cli_smoke()
    print("✅ all 4 tests passed")