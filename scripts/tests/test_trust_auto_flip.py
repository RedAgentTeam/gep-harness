"""Test trust_auto_flip.py — v22.0 trust 动态化自动切换。"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import trust_auto_flip as taf
import cross_library_auto as cla


def setup_function(_):
    """每个测试前重置 active_edges（保证隔离）。"""
    cla.set_active_edges(None)


def teardown_function(_):
    """每个测试后重置（防止污染其他测试）。"""
    cla.set_active_edges(None)


def test_constants():
    """模块常量正确。"""
    assert taf.REPO == REPO
    assert taf.DEFAULT_EDGES_PATH == REPO / "staging" / "dynamic_edges_v19.json"


def test_load_dynamic_edges_missing(tmp_path):
    """dynamic_edges 文件不存在 → 返回 None。"""
    result = taf.load_dynamic_edges(tmp_path / "nonexistent.json")
    assert result is None


def test_load_dynamic_edges_invalid(tmp_path):
    """dynamic_edges 文件 JSON 解析失败 → 返回 None。"""
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    result = taf.load_dynamic_edges(bad)
    assert result is None


def test_load_dynamic_edges_no_field(tmp_path):
    """dynamic_edges 文件无 dynamic_edges 字段 → 返回 None。"""
    f = tmp_path / "no_field.json"
    f.write_text('{"foo": "bar"}')
    result = taf.load_dynamic_edges(f)
    assert result is None


def test_load_dynamic_edges_unused(tmp_path):
    """dynamic_edges 文件 used_observed=False → 返回 None。"""
    f = tmp_path / "unused.json"
    f.write_text(json.dumps({
        "used_observed": False,
        "dynamic_edges": {"X": {"Y": 0.9}},
    }))
    result = taf.load_dynamic_edges(f)
    assert result is None


def test_load_dynamic_edges_ok(tmp_path):
    """dynamic_edges 文件完整 → 返回 edges dict。"""
    f = tmp_path / "ok.json"
    f.write_text(json.dumps({
        "used_observed": True,
        "dynamic_edges": {
            "BeautifulMathematics": {"cell-biology": 0.91},
            "cell-biology": {"BeautifulMathematics": 0.91},
        },
    }))
    result = taf.load_dynamic_edges(f)
    assert result is not None
    assert "BeautifulMathematics" in result


def test_restore_static():
    """restore_static() → 恢复到静态基线。"""
    # 先切到 dynamic
    dyn = {"X": {"Y": 0.9}}
    cla.set_active_edges(dyn)
    assert cla.get_active_edges() is dyn
    # 恢复
    rc = taf.restore_static()
    assert rc == 0
    assert cla.get_active_edges() is cla.LIBRARY_GRAPH_EDGE


def test_flip_dry_run(tmp_path, monkeypatch):
    """flip dry-run：不调用 set_active_edges。"""
    f = tmp_path / "ok.json"
    f.write_text(json.dumps({
        "used_observed": True,
        "dynamic_edges": {
            "BeautifulMathematics": {"cell-biology": 0.91},
        },
    }))
    edges_before = cla.get_active_edges()
    rc = taf.flip(f, dry_run=True)
    assert rc == 0
    # 验证未切换
    assert cla.get_active_edges() is edges_before


def test_flip_real_uses_staging_file():
    """flip 真实跑 staging/dynamic_edges_v19.json → 切换成功。"""
    if not taf.DEFAULT_EDGES_PATH.exists():
        # 先跑 cross_lib_auto_evolve 生成
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/cross_lib_auto_evolve.py", "--dry-run"],
            cwd=REPO, check=True,
        )
    cla.set_active_edges(None)
    rc = taf.flip(taf.DEFAULT_EDGES_PATH)
    assert rc == 0
    assert cla.get_active_edges() is not cla.LIBRARY_GRAPH_EDGE


def test_flip_missing_returns_1(tmp_path):
    """flip 文件不存在 → 返回 1。"""
    rc = taf.flip(tmp_path / "nonexistent.json")
    assert rc == 1


def test_cron_workflow_5_steps_order():
    """cron_hourly_workflow 5 步顺序：evolve → flip → check_5lib → changelog → commit。

    使用 AST 解析，仅匹配 run_step() 调用且被赋值给 ok（不是 return run_step）。
    """
    import ast
    import inspect
    src = inspect.getsource(__import__("cron_hourly_workflow").main)
    tree = ast.parse(src)

    step_prefixes = ("cross_lib_auto_evolve", "trust_auto_flip", "check_5lib_assets", "generate_changelog", "auto_changelog_commit")
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run_step":
            # 跳过 return run_step(...)（紧急回退分支）
            parent_is_return = False
            for parent in ast.walk(tree):
                if isinstance(parent, ast.Return) and parent.value is node:
                    parent_is_return = True
                    break
            if parent_is_return:
                continue
            if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                v = node.args[0].value
                if isinstance(v, str):
                    for prefix in step_prefixes:
                        if v == prefix or v.startswith(prefix + " "):
                            calls.append((node.lineno, prefix))
                            break
    calls.sort(key=lambda x: x[0])

    # 去重保留顺序
    seen = []
    for _, name in calls:
        if name not in seen:
            seen.append(name)

    assert seen == ["cross_lib_auto_evolve", "trust_auto_flip", "check_5lib_assets", "generate_changelog", "auto_changelog_commit"], f"顺序错误: {seen}"


def test_cron_workflow_has_skip_flip_flag():
    """cron_hourly_workflow 支持 --skip-flip flag。"""
    import inspect
    src = inspect.getsource(__import__("cron_hourly_workflow").main)
    assert "--skip-flip" in src


def test_cron_workflow_has_restore_static_flag():
    """cron_hourly_workflow 支持 --restore-static flag。"""
    import inspect
    src = inspect.getsource(__import__("cron_hourly_workflow").main)
    assert "--restore-static" in src


def test_cron_workflow_docstring_v22():
    """cron_workflow docstring 提到 v22.0/v23.0/v24.0 + 多步。"""
    chw = __import__("cron_hourly_workflow")
    doc = chw.__doc__ or ""
    # 兼容 v22.0 (5 步) / v23.0 (6 步) / v24.0 (7 步) 三个版本
    assert any(v in doc for v in ("v22.0", "v23.0", "v24.0"))
    assert any(s in doc for s in ("5 步", "5 个", "6 步", "6 个", "7 步", "7 个"))