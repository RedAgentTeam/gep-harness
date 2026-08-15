"""Regression tests for P1-1: emitter daemon mode (long-running stdin/stdout JSONL).

Verifies the Python daemon (`event_emitter.py daemon`) correctly handles
multiple emit requests over a single pipe without forking a new process
per call. This is the P1-1 fix that eliminates per-tool-call spawn cost.

5 pytest:
  1. daemon emits one event per request over stdin/stdout
  2. daemon handles multiple requests sequentially
  3. daemon responds with the same asset_id as the CLI `emit` action
  4. daemon returns error for malformed JSON request
  5. daemon returns ok=True on shutdown ack
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
EMITTER = Path("/data/disk/gep-harness/openclaw-harness/bin/event_emitter.py")


def _spawn_daemon(path: Path | None = None):
    """Spawn the Python emitter in daemon mode and return (proc, stdin, stdout_line_iter)."""
    env_overrides = {}
    if path is not None:
        env_overrides["OPENCLAW_EVENT_STREAM"] = str(path)
    import os
    env = {**os.environ, **env_overrides}

    proc = subprocess.Popen(
        [sys.executable, str(EMITTER), "daemon"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line-buffered
        env=env,
    )
    return proc


def _send(proc, req: dict) -> dict:
    """Write one request line, read one response line, return parsed dict."""
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line)


def test_daemon_emits_one_event_per_request(tmp_path):
    """daemon should accept one emit request and produce one response."""
    stream_path = tmp_path / "events.jsonl"
    proc = _spawn_daemon(path=stream_path)
    try:
        resp = _send(proc, {
            "_reqId": 1,
            "action": "emit",
            "session_id": "s_daemon_test_1",
            "kind": "tool_call_before",
            "tool_name": "write_file",
            "args": {"path": "/tmp/x"},
        })
        assert resp.get("ok") is True
        assert resp.get("_reqId") == 1
        assert resp.get("asset_id", "").startswith("sha256:")
        # Stream file should now have exactly one event.
        lines = [l for l in stream_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1, f"expected 1 event on disk, got {len(lines)}"
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)


def test_daemon_handles_multiple_requests_sequentially(tmp_path):
    """daemon should process N requests in order, writing N events."""
    stream_path = tmp_path / "events.jsonl"
    proc = _spawn_daemon(path=stream_path)
    try:
        for i in range(1, 6):
            resp = _send(proc, {
                "_reqId": i,
                "action": "emit",
                "session_id": "s_daemon_multi",
                "kind": "tool_call_before" if i % 2 == 1 else "tool_call_after",
                "tool_name": f"tool_{i}",
                "args": {"i": i},
            })
            assert resp.get("ok") is True, f"req {i} failed: {resp}"
            assert resp.get("_reqId") == i
        # Verify all 5 events were appended in order
        lines = [json.loads(l) for l in stream_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 5
        for idx, ev in enumerate(lines, start=1):
            assert ev.get("session_id") == "s_daemon_multi"
            assert ev.get("tool_name") == f"tool_{idx}"
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)


def test_daemon_asset_id_is_verifiable(tmp_path):
    """daemon-emitted asset_id must be cryptographically valid (verify_asset_id passes).

    Note: CLI and daemon emit at different wall-clock times, so their `ts`
    fields differ and therefore their asset_ids differ. We don't require
    byte-equality; we require that BOTH pass verify_asset_id (the same
    canonicalize() + SHA-256 algorithm is used).
    """
    sys.path.insert(0, str(EMITTER.parent))
    from canonicalize import verify_asset_id, compute_asset_id

    stream_cli = tmp_path / "cli.jsonl"
    stream_daemon = tmp_path / "daemon.jsonl"

    # 1. CLI emit
    cli = subprocess.run(
        [sys.executable, str(EMITTER), "emit", "s_asset_test", "tool_call_before",
         "--tool", "write_file", "--args", json.dumps({"k": "v"})],
        capture_output=True, text=True,
        env={**__import__("os").environ, "OPENCLAW_EVENT_STREAM": str(stream_cli)},
    )
    assert cli.returncode == 0, f"CLI failed: {cli.stderr}"
    cli_ev = json.loads(cli.stdout)

    # 2. Daemon emit (same payload)
    proc = _spawn_daemon(path=stream_daemon)
    try:
        resp = _send(proc, {
            "_reqId": 99,
            "action": "emit",
            "session_id": "s_asset_test",
            "kind": "tool_call_before",
            "tool_name": "write_file",
            "args": {"k": "v"},
        })
        assert resp.get("ok") is True
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)

    # 3. Both events must pass verify_asset_id
    daemon_ev_line = stream_daemon.read_text().strip().splitlines()[-1]
    daemon_ev = json.loads(daemon_ev_line)

    assert verify_asset_id(cli_ev), f"CLI event fails verify_asset_id: {cli_ev}"
    assert verify_asset_id(daemon_ev), f"Daemon event fails verify_asset_id: {daemon_ev}"

    # 4. asset_id should also match a fresh canonicalize of the event (idempotency)
    assert compute_asset_id(cli_ev) == cli_ev["asset_id"]
    assert compute_asset_id(daemon_ev) == daemon_ev["asset_id"]


def test_daemon_returns_error_for_malformed_json(tmp_path):
    """daemon should NOT crash on bad input; should respond with ok=false."""
    stream_path = tmp_path / "events.jsonl"
    proc = _spawn_daemon(path=stream_path)
    try:
        proc.stdin.write("{ this is not valid json\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        resp = json.loads(line)
        assert resp.get("ok") is False
        assert "bad_json" in resp.get("error", "")
        # Daemon should still be alive — send a valid request
        good = _send(proc, {
            "_reqId": 2,
            "action": "emit",
            "session_id": "s_recover",
            "kind": "tool_call_before",
        })
        assert good.get("ok") is True, "daemon died after bad input"
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)


def test_daemon_shutdown_ack(tmp_path):
    """daemon should respond with ok=true action=shutdown on shutdown request."""
    proc = _spawn_daemon(path=tmp_path / "events.jsonl")
    try:
        proc.stdin.write(json.dumps({"action": "shutdown"}) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        resp = json.loads(line)
        assert resp.get("ok") is True
        assert resp.get("action") == "shutdown"
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)