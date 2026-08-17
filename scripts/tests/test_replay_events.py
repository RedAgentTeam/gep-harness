"""Test replay_events.py — events.jsonl 末 10 行回放。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def test_replay_event_format():
    """replay_event() 格式化单个事件为字符串。"""
    from replay_events import replay_event
    line = replay_event({"kind": "tool_call_before", "tool_name": "exec"})
    assert "tool_call_before" in line
    assert "exec" in line


def test_replay_event_default_kind_tool():
    """缺 kind / tool_name 时使用 "?" / "-" 默认值。"""
    from replay_events import replay_event
    line = replay_event({})
    assert "?" in line
    assert "-" in line


def test_replay_stdin_counts_events():
    """replay_stdin() 返回处理事件数。"""
    from replay_events import replay_stdin
    events = [
        {"kind": "tool_call_before", "tool_name": "exec"},
        {"kind": "tool_call_after", "tool_name": "exec"},
    ]
    stdin_data = "\n".join(json.dumps(e) for e in events) + "\n"
    old_stdin = sys.stdin
    sys.stdin = iter(stdin_data.splitlines(keepends=False))
    try:
        count = replay_stdin()
    finally:
        sys.stdin = old_stdin
    assert count == 2


def test_replay_stdin_skips_malformed():
    """replay_stdin() 跳过非法 JSON 行。"""
    from replay_events import replay_stdin
    stdin_data = "not json {{{\n" + json.dumps({"kind": "x", "tool_name": "y"}) + "\n"
    old_stdin = sys.stdin
    sys.stdin = iter(stdin_data.splitlines(keepends=False))
    try:
        count = replay_stdin()
    finally:
        sys.stdin = old_stdin
    assert count == 1


def test_replay_stdin_empty():
    """replay_stdin() 空 stdin → count=0。"""
    from replay_events import replay_stdin
    old_stdin = sys.stdin
    sys.stdin = iter([])
    try:
        count = replay_stdin()
    finally:
        sys.stdin = old_stdin
    assert count == 0


def test_main_via_subprocess():
    """main() 走 __main__ 守卫（subprocess 仍跑通）。"""
    events = [{"kind": "tool_call_before", "tool_name": "exec"}]
    stdin_data = "\n".join(json.dumps(e) for e in events) + "\n"
    result = subprocess.run(
        ["python3", str(REPO / "scripts/replay_events.py")],
        input=stdin_data, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "tool_call_before" in result.stdout
    assert "exec" in result.stdout