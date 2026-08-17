"""Test adaptive_gdi.py main() CLI (66%→100%)。

补 missing lines: 33, 54, 97-129, 133
- 33: compute_acceptance_rate 空 events → None
- 54: adaptive_threshold 边界
- 97-129: main() argparse + JSON/text 输出
- 133: if __name__ == "__main__": main()
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import adaptive_gdi as ag


def _write_audit(path: Path, events: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def _make_event(sent: int = 1, accepted: int = 1) -> dict:
    return {
        "action": "sync_to_peer",
        "sent": sent,
        "accepted": accepted,
        "timestamp": "2026-08-17T00:00:00Z",
        "min_gdi": 0.7,
    }


def test_main_no_events_keeps_current(capsys, tmp_path):
    """main: 无 audit events → 保持 current threshold。"""
    audit = tmp_path / "audit.jsonl"
    audit.write_text("")
    with patch.object(sys, "argv", ["ag.py", "--audit", str(audit), "--current=0.5"]):
        try:
            ag.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "no sync events found" in captured.out or "keep current=0.50" in captured.out


def test_main_json_output(capsys, tmp_path):
    """main --json: 输出 JSON dict (current / rate / new_threshold / events_considered / window)。"""
    audit = tmp_path / "audit.jsonl"
    _write_audit(audit, [_make_event(accepted=1), _make_event(accepted=1), _make_event(accepted=0)])
    with patch.object(sys, "argv", [
        "ag.py", "--audit", str(audit), "--current=0.7", "--window=5", "--json"
    ]):
        try:
            ag.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    # stdout 应该是合法 JSON
    out = json.loads(captured.out)
    assert "current" in out
    assert "acceptance_rate" in out
    assert "new_threshold" in out
    assert "events_considered" in out
    assert "window" in out
    assert out["window"] == 5
    assert abs(out["acceptance_rate"] - 2/3) < 0.01


def test_main_text_output(capsys, tmp_path):
    """main (无 --json): 打印文本格式。"""
    audit = tmp_path / "audit.jsonl"
    _write_audit(audit, [_make_event(accepted=1), _make_event(accepted=1)])
    with patch.object(sys, "argv", ["ag.py", "--audit", str(audit), "--current=0.7"]):
        try:
            ag.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "window=" in captured.out
    assert "acceptance_rate=" in captured.out
    assert "new_threshold=" in captured.out


def test_main_window_limits_events(capsys, tmp_path):
    """main --window=N: 只考虑最近 N 个 event。"""
    events = [_make_event(accepted=1)] * 10 + [_make_event(accepted=0)] * 5
    audit = tmp_path / "audit.jsonl"
    _write_audit(audit, events)
    with patch.object(sys, "argv", [
        "ag.py", "--audit", str(audit), "--current=0.7", "--window=3", "--json"
    ]):
        try:
            ag.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert out["events_considered"] == 3
    assert out["window"] == 3


def test_main_default_pool_dir(capsys, tmp_path):
    """main: --pool-dir 不影响输出（reserved, unused）。"""
    audit = tmp_path / "audit.jsonl"
    _write_audit(audit, [_make_event(accepted=1)])
    pool = tmp_path / "pool"
    pool.mkdir()
    with patch.object(sys, "argv", [
        "ag.py", "--audit", str(audit), "--pool-dir", str(pool)
    ]):
        try:
            ag.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "new_threshold=" in captured.out


def test_main_module_runs():
    """if __name__ == '__main__': main() → --help 能跑。"""
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/adaptive_gdi.py"), "--help"],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    assert "--audit" in r.stdout
    assert "--current" in r.stdout
    assert "--window" in r.stdout
    assert "--json" in r.stdout