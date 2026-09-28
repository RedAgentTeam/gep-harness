"""Test check_5lib_assets.py — 5 库产物自动检查。"""

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import check_5lib_assets as c5a


def test_constants():
    """模块常量正确。"""
    assert c5a.REPO == REPO
    assert c5a.DOCS == REPO / "docs"
    assert set(c5a.ALL_FORMATS) == {"png", "svg", "pdf", "eps", "md", "dot"}
    assert set(c5a.GRAPHVIZ_FORMATS) == {"png", "svg", "pdf", "eps"}
    assert set(c5a.TEXT_FORMATS) == {"md", "dot"}


def test_all_assets_exist_current_repo():
    """当前 repo 6 格式产物全部存在（v19.0 fix 跑过）。"""
    exists = c5a.all_assets_exist()
    for ext, ok in exists.items():
        assert ok, f"5LIB_GRAPH.{ext} 缺失"


def test_any_too_old_default_fresh():
    """当前产物应全部新鲜（age < 1h 默认）。"""
    old = c5a.any_too_old(3600)
    for ext, is_old in old.items():
        assert not is_old, f"5LIB_GRAPH.{ext} 已过时"


def test_any_too_old_tiny_threshold():
    """阈值极小（1s）→ 所有文件都视为旧。"""
    import os
    import time as t
    # 强制把一个文件 mtime 设为 100s 前
    target = REPO / "docs/5LIB_GRAPH.png"
    old_time = t.time() - 100
    os.utime(target, (old_time, old_time))
    old = c5a.any_too_old(1)
    assert old["png"] is True
    assert any(old.values())


def test_has_graphviz():
    """graphviz 应已安装（gep-harness 依赖）。"""
    assert c5a.has_graphviz() is True


def test_check_only_returns_zero_when_fresh():
    """check_only 在新鲜状态下应返回 0。"""
    rc = c5a.check_only(3600)
    assert rc == 0


def test_check_only_missing_file(tmp_path, monkeypatch):
    """人为让一个文件不存在 → check_only 返回 1。"""
    fake_docs = tmp_path / "docs"
    fake_docs.mkdir()
    # 改 REPO 和 DOCS 指向 tmp
    monkeypatch.setattr(c5a, "DOCS", fake_docs)
    rc = c5a.check_only(3600)
    assert rc == 1
    assert "缺失" in _capture(lambda: c5a.check_only(3600))


def _capture(fn):
    """捕获 stdout。"""
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            fn()
    except SystemExit:
        pass
    return buf.getvalue()


def test_all_assets_exist_with_missing(tmp_path, monkeypatch):
    """缺一个文件 → all_assets_exist 标记为 False。"""
    fake_docs = tmp_path / "docs"
    fake_docs.mkdir()
    (fake_docs / "5LIB_GRAPH.png").touch()
    monkeypatch.setattr(c5a, "DOCS", fake_docs)
    exists = c5a.all_assets_exist()
    assert exists["png"] is True
    assert exists["svg"] is False
    assert exists["md"] is False


def test_fix_when_already_fresh():
    """fix 在全齐+新鲜时 → 直接返回 0，无副作用。"""
    # 记录 mtime
    target = REPO / "docs/5LIB_GRAPH.png"
    mtime_before = target.stat().st_mtime
    rc = c5a.fix(3600)
    assert rc == 0
    mtime_after = target.stat().st_mtime
    # 不应被改动（fresh 跳过）
    assert mtime_before == mtime_after


def test_regenerate_via_visualize_updates_mtime():
    """regenerate_via_visualize 跑通 + 文件 mtime 更新。"""
    target = REPO / "docs/5LIB_GRAPH.png"
    mtime_before = target.stat().st_mtime
    # 强制设置旧时间确保触发
    import os
    old_time = time.time() - 7200  # 2h 前
    os.utime(target, (old_time, old_time))
    ok = c5a.regenerate_via_visualize()
    assert ok is True
    mtime_after = target.stat().st_mtime
    assert mtime_after > mtime_before
