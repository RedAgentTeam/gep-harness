"""Test trust_persist.py — v23.0 trust_score 持久化。"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import trust_persist as tp


SAMPLE_EDGES = {
    "BeautifulMathematics": {"cell-biology": 0.91},
    "cell-biology": {"BeautifulMathematics": 0.91},
}


def setup_function(_):
    """每个测试前清掉持久化文件。"""
    tp.clear_active_edges()


def teardown_function(_):
    """每个测试后清掉持久化文件（防止污染）。"""
    tp.clear_active_edges()
    # 恢复 trust_score 默认静态
    from cross_library_auto import set_active_edges
    set_active_edges(None)


def test_get_persist_path_returns_path():
    """get_persist_path 返回 Path 对象。"""
    p = tp.get_persist_path()
    assert isinstance(p, Path)
    # 兼容 XDG 路径（active_edges.json）和 fallback 路径（.active_edges.json）
    assert p.name in ("active_edges.json", ".active_edges.json")


def test_save_active_edges():
    """save_active_edges 写文件 + 内容正确。"""
    path = tp.save_active_edges(SAMPLE_EDGES, source="test")
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["version"] == "v1"
    assert data["source"] == "test"
    assert data["libraries"] == 2
    assert data["dynamic_edges"] == SAMPLE_EDGES


def test_load_active_edges():
    """load_active_edges 读回保存的内容。"""
    tp.save_active_edges(SAMPLE_EDGES, source="test")
    loaded = tp.load_active_edges()
    assert loaded == SAMPLE_EDGES


def test_load_active_edges_no_file():
    """load_active_edges 文件不存在 → None。"""
    loaded = tp.load_active_edges()
    assert loaded is None


def test_clear_active_edges():
    """clear_active_edges 删除文件。"""
    tp.save_active_edges(SAMPLE_EDGES, source="test")
    assert tp.get_persist_path().exists()
    ok = tp.clear_active_edges()
    assert ok is True
    assert not tp.get_persist_path().exists()


def test_clear_active_edges_no_file():
    """clear_active_edges 文件不存在 → False。"""
    ok = tp.clear_active_edges()
    assert ok is False


def test_auto_load_active_edges_with_persist():
    """auto_load_active_edges 有持久化文件 → 切换 trust_score。"""
    tp.save_active_edges(SAMPLE_EDGES, source="test")
    from cross_library_auto import get_active_edges, LIBRARY_GRAPH_EDGE
    ok = tp.auto_load_active_edges()
    assert ok is True
    assert get_active_edges() is not LIBRARY_GRAPH_EDGE


def test_auto_load_active_edges_no_persist():
    """auto_load_active_edges 无持久化文件 → False（trust_score 不动）。"""
    from cross_library_auto import get_active_edges, LIBRARY_GRAPH_EDGE
    ok = tp.auto_load_active_edges()
    assert ok is False
    assert get_active_edges() is LIBRARY_GRAPH_EDGE


def test_save_atomic_write():
    """save_active_edges 用 temp+rename 原子写。"""
    path = tp.save_active_edges(SAMPLE_EDGES)
    # 验证没有遗留 .active_edges_*.json temp 文件
    parent = path.parent
    temps = list(parent.glob(".active_edges_*.json"))
    assert temps == [], f"发现遗留 temp 文件: {temps}"


def test_trust_auto_flip_persists():
    """trust_auto_flip flip 后应自动持久化。"""
    from trust_auto_flip import flip, restore_static
    # 跑 flip（用 staging 文件）
    staging = REPO / "staging" / "dynamic_edges_v19.json"
    if not staging.exists():
        # 先跑 cross_lib_auto_evolve 生成
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/cross_lib_auto_evolve.py", "--dry-run"],
            cwd=REPO, check=True,
        )
    rc = flip(staging)
    assert rc == 0
    # 验证持久化
    loaded = tp.load_active_edges()
    assert loaded is not None
    assert "BeautifulMathematics" in loaded
    # restore 应清持久化
    rc = restore_static()
    assert rc == 0
    assert tp.load_active_edges() is None


def test_trust_auto_flip_restore_clears():
    """trust_auto_flip --restore-static 应清持久化文件。"""
    from trust_auto_flip import flip, restore_static
    tp.save_active_edges(SAMPLE_EDGES, source="manual")
    assert tp.load_active_edges() is not None
    # restore
    rc = restore_static()
    assert rc == 0
    # 验证清掉
    assert tp.load_active_edges() is None


def test_cron_workflow_includes_persist_load():
    """cron_hourly_workflow 应包含 trust_persist load 步骤。"""
    import inspect
    src = inspect.getsource(__import__("cron_hourly_workflow").main)
    # 验证 trust_persist load 在步骤列表里
    assert "trust_persist" in src
    assert '"load"' in src


def test_cron_workflow_6_steps_message():
    """cron_hourly_workflow 末尾打印 "6 步全部 OK"。"""
    src = open(REPO / "scripts" / "cron_hourly_workflow.py").read()
    assert "6 步全部 OK" in src


def test_persist_path_xdg_priority():
    """XDG_CONFIG_HOME 设置时优先用 XDG 路径。"""
    import os
    os.environ["XDG_CONFIG_HOME"] = "/tmp/xdg_test_gep_harness"
    p = tp.get_persist_path()
    assert "xdg_test_gep_harness" in str(p)
    # 清理
    del os.environ["XDG_CONFIG_HOME"]