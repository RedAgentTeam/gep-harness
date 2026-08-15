"""Append-only event stream emitter for OpenClaw sessions.

Each emission:
  1. Constructs a GEP-compatible SessionEvent dict
  2. Calls compute_asset_id() to derive a content-addressable id
  3. Appends the JSON line to events.jsonl (atomic write, append-only)

Schema (subset of GEP EvolutionEvent v1.12.1):
  - type: "SessionEvent"
  - schema_version: "1.12.1"
  - id: <asset_id-derived event id>
  - session_id: str
  - kind: "tool_call_before" | "tool_call_after" | "session_start" | "session_end"
  - ts: ISO 8601 timestamp
  - tool_name: str | None
  - args: dict | None (before only)
  - result: dict | None (after only)
  - duration_ms: int | None (after only)
  - asset_id: sha256:...

Implements gene_harness_append_only_event_stream (low risk).
"""
import os, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from canonicalize import compute_asset_id, verify_asset_id, SCHEMA_VERSION  # noqa: E402

DEFAULT_PATH = Path(
    os.environ.get(
        "OPENCLAW_EVENT_STREAM",
        str(Path.home() / ".openclaw/workspace/devagent/openclaw-harness/events/events.jsonl"),
    )
)


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


def emit(
    session_id: str,
    kind: str,
    tool_name: str | None = None,
    args: dict | None = None,
    result: dict | None = None,
    duration_ms: int | None = None,
    path: Path | None = None,
) -> dict:
    """Construct, hash, append, return event dict."""
    if path is None:
        path = DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "type": "SessionEvent",
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "kind": kind,
        "ts": _now_iso(),
    }
    if tool_name is not None:
        event["tool_name"] = tool_name
    if args is not None:
        event["args"] = args
    if result is not None:
        event["result"] = result
    if duration_ms is not None:
        event["duration_ms"] = duration_ms

    event["asset_id"] = compute_asset_id(event)

    # Append-only atomic write
    line = json.dumps(event, ensure_ascii=False, sort_keys=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())

    return event


def replay(session_id: str, path: Path | None = None) -> list[dict]:
    """Return all events for a session, in append order."""
    if path is None:
        path = DEFAULT_PATH
    events = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if ev.get("session_id") == session_id:
            events.append(ev)
    return events


def verify_all(path: Path | None = None) -> tuple[int, int]:
    """Verify every line's asset_id. Returns (ok_count, fail_count)."""
    if path is None:
        path = DEFAULT_PATH
    ok = fail = 0
    if not path.exists():
        return ok, fail
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if verify_asset_id(ev):
            ok += 1
        else:
            fail += 1
    return ok, fail


def _daemon_mode() -> int:
    """P1-1: long-running stdin/stdout JSONL daemon.

    Protocol:
      input (stdin): one JSON object per line
        {"action": "emit", "session_id": "...", "kind": "...",
         "tool_name": "...", "args": {...}, "result": {...},
         "duration_ms": 123}
      output (stdout): one JSON object per line
        {"ok": true, "asset_id": "sha256:..."}     on success
        {"ok": false, "error": "..."}              on failure
        {"ok": true, "action": "shutdown"}          on shutdown ack

    Reads until EOF (parent closes stdin) or a {"action": "shutdown"} line.
    """
    out = sys.stdout
    err = sys.stderr
    try:
        for raw in sys.stdin:
            line = raw.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError as e:
                err.write(f"[emitter-daemon] bad json: {e}\n")
                # can't echo _reqId — bad line wasn't valid json to begin with
                out.write(json.dumps({"ok": False, "error": f"bad_json:{e}"}) + "\n")
                out.flush()
                continue
            action = req.get("action")
            req_id = req.get("_reqId")  # pass-through for caller correlation
            if action == "shutdown":
                out.write(json.dumps({"ok": True, "action": "shutdown", "_reqId": req_id}) + "\n")
                out.flush()
                return 0
            if action == "emit":
                try:
                    ev = emit(
                        session_id=req["session_id"],
                        kind=req["kind"],
                        tool_name=req.get("tool_name"),
                        args=req.get("args"),
                        result=req.get("result"),
                        duration_ms=req.get("duration_ms"),
                    )
                    out.write(json.dumps(
                        {"ok": True, "asset_id": ev.get("asset_id"), "_reqId": req_id},
                        ensure_ascii=False,
                    ) + "\n")
                    out.flush()
                except Exception as e:
                    out.write(json.dumps({"ok": False, "error": str(e), "_reqId": req_id}) + "\n")
                    out.flush()
                continue
            # Unknown action
            out.write(json.dumps({"ok": False, "error": f"unknown_action:{action}", "_reqId": req_id}) + "\n")
            out.flush()
    except BrokenPipeError:
        # Parent died; exit cleanly.
        return 0
    return 0


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["emit", "replay", "verify", "daemon"])
    p.add_argument("session_id", nargs="?")
    p.add_argument("kind", nargs="?")
    p.add_argument("--tool")
    p.add_argument("--args")
    p.add_argument("--result")
    p.add_argument("--duration", type=int)
    args = p.parse_args()

    if args.action == "daemon":
        sys.exit(_daemon_mode())

    if args.action == "emit":
        ev = emit(
            session_id=args.session_id,
            kind=args.kind,
            tool_name=args.tool,
            args=json.loads(args.args) if args.args else None,
            result=json.loads(args.result) if args.result else None,
            duration_ms=args.duration,
        )
        print(json.dumps(ev, ensure_ascii=False))
    elif args.action == "replay":
        for ev in replay(args.session_id):
            print(json.dumps(ev, ensure_ascii=False))
    elif args.action == "verify":
        ok, fail = verify_all()
        print(json.dumps({"ok": ok, "fail": fail}))