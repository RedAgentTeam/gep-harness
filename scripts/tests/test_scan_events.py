"""Test scan_events.py — Scan events.jsonl for patterns."""

import json
import sys
from pathlib import Path

sys.path.insert(0, "/data/disk/gep-harness/scripts")

from scan_events import scan, parse_iso


def test_parse_iso_z_suffix():
    """Z 后缀 ISO 时间戳。"""
    dt = parse_iso("2026-08-15T10:00:00Z")
    assert dt is not None


def test_parse_iso_offset():
    """带时区偏移 ISO 时间戳。"""
    dt = parse_iso("2026-08-15T10:00:00+08:00")
    assert dt is not None


def test_scan_missing_file():
    """events.jsonl 不存在 → 返回 error。"""
    result = scan("/tmp/nonexistent_events_xyz.jsonl")
    assert "error" in result
    assert "not found" in result["error"]


def test_scan_empty_file(tmp_path):
    """空 events.jsonl → by_tool 为空。"""
    f = tmp_path / "empty.jsonl"
    f.write_text("")
    result = scan(str(f), since_hours=24.0)
    assert "by_tool" in result
    assert len(result["by_tool"]) == 0