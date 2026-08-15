"""Test replay_events.py — replay last 10 events."""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
SCRIPT = REPO / "scripts/replay_events.py"


def test_replay_empty_stdin():
    """空 stdin → 0 行输出。"""
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input="",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_replay_valid_events():
    """有效 JSONL → 输出 kind + tool_name。"""
    sample = "\n".join([
        json.dumps({"kind": "tool_call_before", "tool_name": "exec"}),
        json.dumps({"kind": "tool_call_after", "tool_name": "read"}),
        json.dumps({"kind": "session_event", "tool_name": "process"}),
    ])
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=sample,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "tool_call_before" in result.stdout
    assert "tool=exec" in result.stdout
    assert "tool_call_after" in result.stdout
    assert "tool=read" in result.stdout


def test_replay_invalid_json_skipped():
    """无效 JSON 行 → 跳过，不报错。"""
    sample = "\n".join([
        "this is not json",
        json.dumps({"kind": "tool_call_before", "tool_name": "exec"}),
        "{ broken json",
    ])
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=sample,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "tool=exec" in result.stdout
    assert "this is not json" not in result.stdout


def test_replay_event_missing_fields():
    """缺字段事件 → 用 ?/- 占位。"""
    sample = json.dumps({"kind": "session_event"})
    result = subprocess.run(
        ["python3", str(SCRIPT)],
        input=sample,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "session_event" in result.stdout
    assert "tool=-" in result.stdout