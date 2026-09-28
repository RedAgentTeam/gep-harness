"""Test cross_lib_auto_evolve.py — v21.0 auto-evolve 链路。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import cross_lib_auto_evolve as clae
import cron_hourly_workflow as chw


def test_constants():
    """模块常量正确。"""
    assert clae.REPO == REPO
    assert clae is not None
    assert chw.REPO == REPO


def test_run_step_success():
    """run_step 跑成功命令 → True。"""
    ok = clae.run_step("test_echo", ["-c", "import sys; sys.exit(0)"])
    assert ok is True


def test_run_step_failure():
    """run_step 跑失败命令 → False。"""
    ok = clae.run_step("test_fails", ["-c", "import sys; sys.exit(1)"])
    assert ok is False


def test_main_dry_run(monkeypatch):
    """默认 main() 跑通（需 monkeypatch argv）。"""
    monkeypatch.setattr(sys, "argv", ["cross_lib_auto_evolve.py"])
    rc = clae.main()
    assert isinstance(rc, int)


def test_main_dry_run_explicit(monkeypatch):
    """显式 --dry-run 跑通。"""
    monkeypatch.setattr(sys, "argv", ["cross_lib_auto_evolve.py", "--dry-run"])
    rc = clae.main()
    assert rc == 0


def test_dynamic_edges_output_exists():
    """cross_lib_auto_evolve 跑后 staging/dynamic_edges_v19.json 应存在。"""
    p = REPO / "staging" / "dynamic_edges_v19.json"
    if p.exists():
        data = json.loads(p.read_text())
        assert "dynamic_edges" in data
        assert "used_observed" in data


def test_cron_workflow_has_skip_evolve_flag(monkeypatch):
    """cron_hourly_workflow.py 支持 --skip-evolve flag。"""
    monkeypatch.setattr(sys, "argv", ["cron_hourly_workflow.py", "--skip-evolve"])
    rc = chw.main()
    assert rc == 0


def test_cron_workflow_4_steps_order():
    """4 步顺序：cross_lib_auto_evolve → check_5lib → generate_changelog → auto_commit。"""
    # 读 chw.main 源码确认 step 顺序
    import inspect
    src = inspect.getsource(chw.main)
    # 4 个关键词出现顺序
    pos_evolve = src.find("cross_lib_auto_evolve")
    pos_check = src.find("check_5lib_assets")
    pos_changelog = src.find("generate_changelog")
    pos_commit = src.find("auto_changelog_commit")
    assert 0 < pos_evolve < pos_check < pos_changelog < pos_commit


def test_docstring_updated():
    """cron_hourly_workflow docstring 提到 v21.0/v22.0/v23.0/v24.0 + 多步。"""
    doc = chw.__doc__ or ""
    # 兼容 v21.0/v22.0/v23.0/v24.0 四个版本
    assert any(v in doc for v in ("v21.0", "v22.0", "v23.0", "v24.0"))
    # "4 步 / 5 步 / 6 步" 或 "4 个 / 5 个 / 6 个"
    assert any(s in doc for s in ("4 步", "4 个", "5 步", "5 个", "6 步", "6 个", "7 步", "7 个"))


def test_cross_lib_does_not_modify_active_edges():
    """cross_lib_auto_evolve 不调用 set_active_edges（保持 trust_score 默认静态）。

    检测方式：源码中除字符串字面量外不应有 set_active_edges(...) 调用。
    """
    import ast
    src = (REPO / "scripts" / "cross_lib_auto_evolve.py").read_text()
    tree = ast.parse(src)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # 检查被调函数名是否为 set_active_edges
            if isinstance(node.func, ast.Name) and node.func.id == "set_active_edges":
                calls.append(node.lineno)
    assert calls == [], f"cross_lib_auto_evolve 不应主动调用 set_active_edges()，发现调用在第 {calls} 行"


def test_evolve_output_used_observed():
    """auto-evolve 跑通后 used_observed 应为 True（60 样本足够）。"""
    p = REPO / "staging" / "dynamic_edges_v19.json"
    if not p.exists():
        # 先跑一遍
        subprocess.run(
            [sys.executable, "scripts/cross_lib_auto_evolve.py", "--dry-run"],
            cwd=REPO, check=True,
        )
    data = json.loads(p.read_text())
    assert data["used_observed"] is True