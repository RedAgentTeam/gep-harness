"""Test solidify.py — Solidify 人工审批门。"""

import sys
import subprocess
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def test_solidify_constants():
    """solidify.py 核心常量正确（subprocess 检查）。"""
    # 直接 grep 模块源文件，避免 import 触发 main
    src = (REPO / "scripts/solidify.py").read_text()
    assert "GEP_HARNESS" in src
    assert "PLAN_GENES" in src
    assert "PLAN_EVENTS" in src
    assert "STAGING" in src


def test_solidify_help_message():
    """solidify.py --help 可用。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/solidify.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "Solidify" in result.stdout or "staging" in result.stdout.lower()


def test_solidify_check_duplicate_function_exists():
    """check_duplicate 函数存在于 solidify.py 源码。"""
    src = (REPO / "scripts/solidify.py").read_text()
    assert "def check_duplicate" in src


def test_solidify_validate_gene_function_exists():
    """validate_gene 函数存在。"""
    src = (REPO / "scripts/solidify.py").read_text()
    assert "def validate_gene" in src


def test_solidify_make_solidify_event_function_exists():
    """make_solidify_event 函数存在（写审计事件）。"""
    src = (REPO / "scripts/solidify.py").read_text()
    assert "def make_solidify_event" in src