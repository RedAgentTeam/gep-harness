"""Test cron_hourly_workflow.py — cron 6h 联动。"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import cron_hourly_workflow as chw


def test_constants():
    """模块常量正确。"""
    assert chw.REPO == REPO
    assert chw.LOG_FILE == REPO / "logs/cron_workflow.log"


def test_run_step_success():
    """run_step 跑成功命令 → True。"""
    ok = chw.run_step("test_echo", ["-c", "import sys; sys.exit(0)"])
    assert ok is True


def test_run_step_failure():
    """run_step 跑失败命令 → False。"""
    ok = chw.run_step("test_fails", ["-c", "import sys; sys.exit(1)"])
    assert ok is False


def test_run_step_real_check_5lib():
    """run_step 实际跑 check_5lib_assets.py → True。"""
    ok = chw.run_step("check_5lib_assets", ["scripts/check_5lib_assets.py"])
    assert ok is True


def test_main_skip_commit(monkeypatch):
    """main --skip-commit 跑通，无 commit。"""
    monkeypatch.setattr(sys, "argv", ["cron_hourly_workflow.py", "--skip-commit"])
    rc = chw.main()
    assert rc == 0


def test_log_to_file():
    """log_to_file 写入 logs/cron_workflow.log。"""
    log_path = chw.LOG_FILE
    chw.log_to_file("test_marker_XYZ")
    assert log_path.exists()
    content = log_path.read_text()
    assert "test_marker_XYZ" in content


def test_main_skip_5lib(monkeypatch):
    """main --skip-5lib 跳过 5 库检查 → 仍 OK。"""
    monkeypatch.setattr(sys, "argv", ["cron_hourly_workflow.py", "--skip-5lib"])
    rc = chw.main()
    assert rc == 0
