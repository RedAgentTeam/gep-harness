"""Test scan_events.py — events.jsonl 扫描聚合。"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def _make_event(kind, tool_name, ts, args=None, result=None, session_id="sess_test"):
    return {
        "ts": ts,
        "kind": kind,
        "tool_name": tool_name,
        "session_id": session_id,
        "args": args or {},
        "result": result or {},
    }


def _write_events(tmp_path, events):
    """Write events.jsonl into tmp_path/events.jsonl."""
    p = tmp_path / "events.jsonl"
    with open(p, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return str(p)


def test_parse_iso():
    """parse_iso 把 ISO 时间戳转 datetime。"""
    from scan_events import parse_iso
    dt = parse_iso("2026-08-17T00:00:00+00:00")
    assert dt.tzinfo is not None
    assert dt.year == 2026


def test_scan_empty_events(tmp_path):
    """events.jsonl 不存在 → error 返回。"""
    from scan_events import scan
    result = scan(str(tmp_path / "missing.jsonl"), since_hours=24)
    assert "error" in result


def test_scan_empty_file(tmp_path):
    """events.jsonl 空 → total=0。"""
    from scan_events import scan
    path = _write_events(tmp_path, [])
    result = scan(path, since_hours=24)
    assert result["total_events"] == 0
    assert result["by_tool"] == {}


def test_scan_counts_tool_calls(tmp_path):
    """tool_call_before → by_tool 计数。"""
    from scan_events import scan
    now = datetime.now(timezone.utc).isoformat()
    events = [
        _make_event("tool_call_before", "exec", now, {"cmd": "ls"}),
        _make_event("tool_call_before", "exec", now, {"cmd": "pwd"}),
        _make_event("tool_call_before", "read", now, {"path": "/tmp/x"}),
    ]
    path = _write_events(tmp_path, events)
    result = scan(path, since_hours=24)
    assert result["by_tool"]["exec"] == 2
    assert result["by_tool"]["read"] == 1


def test_scan_filters_old_events(tmp_path):
    """超过 since_hours 的事件不计。"""
    from scan_events import scan
    old = "2024-01-01T00:00:00+00:00"
    recent = datetime.now(timezone.utc).isoformat()
    events = [
        _make_event("tool_call_before", "old_tool", old),
        _make_event("tool_call_before", "new_tool", recent),
    ]
    path = _write_events(tmp_path, events)
    result = scan(path, since_hours=24)
    assert "old_tool" not in result["by_tool"]
    assert "new_tool" in result["by_tool"]


def test_scan_collects_arg_keys(tmp_path):
    """arg_keys_by_tool 累积 args key。"""
    from scan_events import scan
    now = datetime.now(timezone.utc).isoformat()
    events = [
        _make_event("tool_call_before", "exec", now, {"cmd": "x", "timeout": 30}),
        _make_event("tool_call_before", "exec", now, {"cmd": "y", "workdir": "/"}),
    ]
    path = _write_events(tmp_path, events)
    result = scan(path, since_hours=24)
    assert "cmd" in result["arg_keys_by_tool"]["exec"]
    assert "timeout" in result["arg_keys_by_tool"]["exec"]
    assert "workdir" in result["arg_keys_by_tool"]["exec"]


def test_scan_counts_errors_from_after(tmp_path):
    """tool_call_after with result.error → errors 计数。"""
    from scan_events import scan
    now = datetime.now(timezone.utc).isoformat()
    events = [
        _make_event("tool_call_after", "exec", now, result={"error": "fail1"}),
        _make_event("tool_call_after", "exec", now, result={"error": "fail2"}),
        _make_event("tool_call_after", "exec", now, result={}),  # no error
    ]
    path = _write_events(tmp_path, events)
    result = scan(path, since_hours=24)
    assert result["errors"] == 2


def test_scan_skips_malformed_json(tmp_path):
    """非法 JSON 行被跳过（不 crash）。"""
    from scan_events import scan
    now = datetime.now(timezone.utc).isoformat()
    events = [
        _make_event("tool_call_before", "exec", now),
    ]
    p = tmp_path / "events.jsonl"
    with open(p, "w") as f:
        f.write("not json {{{\n")
        for e in events:
            f.write(json.dumps(e) + "\n")
    result = scan(str(p), since_hours=24)
    assert result["by_tool"]["exec"] == 1


def test_scan_session_prefix(tmp_path):
    """session_id 前 20 字符作 by_session_prefix key。"""
    from scan_events import scan
    now = datetime.now(timezone.utc).isoformat()
    events = [
        _make_event("tool_call_before", "exec", now, session_id="abcdefghij1234567890long_id"),
        _make_event("tool_call_before", "exec", now, session_id="xyz_short"),
    ]
    path = _write_events(tmp_path, events)
    result = scan(path, since_hours=24)
    assert "abcdefghij1234567890" in result["by_session_prefix"]
    assert "xyz_short" in result["by_session_prefix"]


def test_main_cli_runs(tmp_path):
    """CLI 跑可输出 JSON。"""
    now = datetime.now(timezone.utc).isoformat()
    events = [_make_event("tool_call_before", "exec", now)]
    path = _write_events(tmp_path, events)
    result = subprocess.run(
        ["python3", str(REPO / "scripts/scan_events.py"),
         "--input", path, "--since", "24h"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    # 输出应是合法 JSON
    parsed = json.loads(result.stdout)
    assert "by_tool" in parsed


def test_main_cli_since_days(tmp_path):
    """--since 7d → since_hours=168。"""
    now = datetime.now(timezone.utc).isoformat()
    events = [_make_event("tool_call_before", "exec", now)]
    path = _write_events(tmp_path, events)
    result = subprocess.run(
        ["python3", str(REPO / "scripts/scan_events.py"),
         "--input", path, "--since", "7d"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0


def test_main_cli_since_raw_hours(tmp_path):
    """--since 12 → since_hours=12（裸数字）。"""
    now = datetime.now(timezone.utc).isoformat()
    events = [_make_event("tool_call_before", "exec", now)]
    path = _write_events(tmp_path, events)
    result = subprocess.run(
        ["python3", str(REPO / "scripts/scan_events.py"),
         "--input", path, "--since", "12"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0