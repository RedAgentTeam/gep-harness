"""Test adaptive_gdi.py — GDI 阈值自适应。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def _write_audit(tmp_path, events):
    p = tmp_path / "audit.jsonl"
    with open(p, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return p


def test_load_audit_events_missing_file(tmp_path):
    """audit.jsonl 不存在 → []。"""
    from adaptive_gdi import load_audit_events
    p = tmp_path / "missing.jsonl"
    result = load_audit_events(p, window=20)
    assert result == []


def test_load_audit_events_filters_non_sync(tmp_path):
    """仅保留 action=sync_to_peer 的事件。"""
    from adaptive_gdi import load_audit_events
    events = [
        {"action": "sync_to_peer", "sent": 5, "accepted": 4},
        {"action": "other_event", "sent": 100, "accepted": 100},  # 过滤
        {"action": "sync_to_peer", "sent": 3, "accepted": 1},
    ]
    p = _write_audit(tmp_path, events)
    result = load_audit_events(p, window=20)
    assert len(result) == 2


def test_load_audit_events_window_limit(tmp_path):
    """window=N → 只取末尾 N 条。"""
    from adaptive_gdi import load_audit_events
    events = [
        {"action": "sync_to_peer", "sent": i, "accepted": i}
        for i in range(1, 11)  # 10 条
    ]
    p = _write_audit(tmp_path, events)
    result = load_audit_events(p, window=3)
    assert len(result) == 3
    assert result[-1]["sent"] == 10  # 最后一条


def test_load_audit_events_skips_malformed(tmp_path):
    """非法 JSON 行被跳过。"""
    from adaptive_gdi import load_audit_events
    p = tmp_path / "audit.jsonl"
    with open(p, "w") as f:
        f.write("not json\n")
        f.write(json.dumps({"action": "sync_to_peer", "sent": 1, "accepted": 1}) + "\n")
    result = load_audit_events(p, window=20)
    assert len(result) == 1


def test_compute_acceptance_rate_no_events():
    """空 events → None。"""
    from adaptive_gdi import compute_acceptance_rate
    assert compute_acceptance_rate([]) is None


def test_compute_acceptance_rate_no_sent():
    """全 sent=0 → None。"""
    from adaptive_gdi import compute_acceptance_rate
    events = [{"sent": 0, "accepted": 0}, {"sent": 0, "accepted": 0}]
    assert compute_acceptance_rate(events) is None


def test_compute_acceptance_rate_normal():
    """sent=10 accepted=5 → 0.5。"""
    from adaptive_gdi import compute_acceptance_rate
    events = [{"sent": 10, "accepted": 5}]
    rate = compute_acceptance_rate(events)
    assert abs(rate - 0.5) < 1e-6


def test_compute_acceptance_rate_sum():
    """多事件求和：5/10 + 10/20 → 15/30 = 0.5。"""
    from adaptive_gdi import compute_acceptance_rate
    events = [
        {"sent": 10, "accepted": 5},
        {"sent": 20, "accepted": 10},
    ]
    rate = compute_acceptance_rate(events)
    assert abs(rate - 0.5) < 1e-6


def test_adaptive_threshold_none_keeps_current():
    """acceptance_rate=None → 保留 current（clamp 到 [lo, hi]）。"""
    from adaptive_gdi import adaptive_threshold
    assert adaptive_threshold(0.7, None) == 0.7
    assert adaptive_threshold(0.99, None, hi=0.85) == 0.85  # clamp
    assert adaptive_threshold(0.05, None, lo=0.3) == 0.3  # clamp


def test_adaptive_threshold_high_raises():
    """acceptance_rate > 0.8 → current + step_up。"""
    from adaptive_gdi import adaptive_threshold
    new = adaptive_threshold(0.7, 0.9, step_up=0.05)
    assert new == 0.75


def test_adaptive_threshold_low_lowers():
    """acceptance_rate < 0.3 → current - step_down。"""
    from adaptive_gdi import adaptive_threshold
    new = adaptive_threshold(0.7, 0.2, step_down=0.05)
    assert new == 0.65


def test_adaptive_threshold_healthy_keeps():
    """0.3 ≤ rate ≤ 0.8 → 保留 current。"""
    from adaptive_gdi import adaptive_threshold
    assert adaptive_threshold(0.7, 0.5) == 0.7
    assert adaptive_threshold(0.7, 0.3) == 0.7  # 边界
    assert adaptive_threshold(0.7, 0.8) == 0.7  # 边界


def test_adaptive_threshold_clamp_upper():
    """raise 后超出 hi → clamp 到 hi。"""
    from adaptive_gdi import adaptive_threshold
    new = adaptive_threshold(0.85, 0.9, step_up=0.05, hi=0.85)
    assert new == 0.85  # clamp


def test_adaptive_threshold_clamp_lower():
    """lower 后低于 lo → clamp 到 lo。"""
    from adaptive_gdi import adaptive_threshold
    new = adaptive_threshold(0.3, 0.1, step_down=0.05, lo=0.3)
    assert new == 0.3  # clamp


def test_adaptive_threshold_rounds_to_2():
    """结果 round 到 2 位小数。"""
    from adaptive_gdi import adaptive_threshold
    new = adaptive_threshold(0.7, 0.9, step_up=0.033)
    assert new == 0.73  # 0.7 + 0.033 = 0.733 → 0.73


def test_main_no_events(tmp_path):
    """main() 无 events → keep current。"""
    p = _write_audit(tmp_path, [])
    result = subprocess.run(
        ["python3", str(REPO / "scripts/adaptive_gdi.py"),
         "--audit", str(p), "--current", "0.7", "--window", "20"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "no sync events" in result.stdout or "0.70" in result.stdout


def test_main_high_rate_raises(tmp_path):
    """main() acceptance_rate > 0.8 → 抬高阈值。"""
    events = [
        {"action": "sync_to_peer", "sent": 10, "accepted": 9},  # 0.9
    ]
    p = _write_audit(tmp_path, events)
    result = subprocess.run(
        ["python3", str(REPO / "scripts/adaptive_gdi.py"),
         "--audit", str(p), "--current", "0.7"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    # 0.7 + 0.05 = 0.75
    assert "0.75" in result.stdout


def test_main_json_output(tmp_path):
    """main() --json 输出 JSON。"""
    events = [{"action": "sync_to_peer", "sent": 10, "accepted": 5}]
    p = _write_audit(tmp_path, events)
    result = subprocess.run(
        ["python3", str(REPO / "scripts/adaptive_gdi.py"),
         "--audit", str(p), "--current", "0.7", "--json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert "current" in parsed
    assert "acceptance_rate" in parsed
    assert "new_threshold" in parsed
    assert parsed["current"] == 0.7
    assert abs(parsed["acceptance_rate"] - 0.5) < 1e-6