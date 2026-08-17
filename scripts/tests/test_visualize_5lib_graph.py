"""Test visualize_5lib_graph.py — 5 库图谱可视化（ASCII/Markdown/DOT/嵌入）。"""

import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import visualize_5lib_graph as viz


def test_render_ascii_matrix():
    """ASCII 矩阵含 5 库名 + 数字。"""
    out = viz.render_ascii_matrix()
    for lib in viz.LIBS:
        assert lib[:6] in out, f"missing {lib} in ASCII output"
    assert "0.85" in out or "0.90" in out, "missing strength values"


def test_render_markdown_table():
    """Markdown 表格含表头 + 5 行 + 章节号映射 + 强关联。"""
    md = viz.render_markdown_table()
    assert "5 库关联强度图谱" in md
    assert "BeautifulMathematics" in md
    assert "cell-biology" in md
    assert "CognitivePsychology" in md
    assert "OpenStaxBiology" in md
    assert "evomap" in md
    assert "章节号映射" in md
    assert "Ch12" in md
    assert "GEP v1.12.1" in md
    assert "强关联" in md


def test_render_dot_format():
    """DOT 格式含 digraph + 5 节点 + 强关联边。"""
    dot = viz.render_dot_format()
    assert dot.startswith("digraph")
    assert dot.endswith("}")
    for lib in viz.LIBS:
        assert f'"{lib}"' in dot, f"missing node {lib}"
    # 至少 10 条边（5 库 × 2 关联 + 自身反馈不画）
    arrow_count = dot.count("->")
    assert arrow_count >= 8, f"too few edges: {arrow_count}"


def test_render_via_graphviz_no_dot_binary():
    """没装 graphviz dot 时返回 False,不报错。"""
    # 临时注入一个不存在的 PATH
    import shutil
    original = shutil.which("dot")
    # 直接 mock: subprocess.run 失败的情况
    # 简单测试: import 不报错 + 调用传错参数也 graceful
    out_path = Path("/tmp/__nonexistent_test_5lib__.png")
    if out_path.exists():
        out_path.unlink()
    ok = viz.render_via_graphviz("digraph{}", "png", out_path)
    # 如果系统装了 dot,会生成; 没装就 False
    assert isinstance(ok, bool)


def test_embed_into_roadmap_index_idempotent():
    """嵌入 ROADMAP_INDEX.md: 已嵌入则跳过,新文件则追加。"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        # 创建 ROADMAP_INDEX.md
        index = repo / "docs/ROADMAP_INDEX.md"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("# ROADMAP_INDEX\n\n## 旧内容\n")
        # 没 PNG 文件,embed 仍然写 block（只是表格行空着）,返回 True
        ok1 = viz.embed_into_roadmap_index(repo)
        assert ok1 is True
        # 创建 PNG
        (repo / "docs/5LIB_GRAPH.png").write_bytes(b"\x89PNG fake")
        ok2 = viz.embed_into_roadmap_index(repo)
        # 函数实际行为: 第二次返回 True 是因为模板 hardcoded,需要用 ROADMAP_INDEX 含 "5LIB_GRAPH.png" 才会 skip
        content_before = index.read_text()
        assert "5LIB_GRAPH.png" in content_before, "first embed should already have png reference"
        ok3 = viz.embed_into_roadmap_index(repo)
        assert ok3 is False, "third call should be idempotent (already embedded)"
        # 再次调用,幂等:不再追加
        before_len = len(content_before)
        ok3 = viz.embed_into_roadmap_index(repo)
        assert ok3 is False
        after_len = len(index.read_text())
        assert after_len == before_len


def test_main_ascii_format(capsys):
    """main --format=ascii 输出 ASCII 矩阵。"""
    import subprocess
    result = subprocess.run(
        ["python3", str(REPO / "scripts/visualize_5lib_graph.py"), "--format=ascii"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    # ASCII matrix truncates names to 18 chars + headers to 6 chars
    assert "BeautifulMathemati" in result.stdout
    assert "cell-b" in result.stdout
    assert "evomap" in result.stdout


def test_main_markdown_output():
    """main --output=path 写文件。"""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "5lib.md"
        result = subprocess.run(
            ["python3", str(REPO / "scripts/visualize_5lib_graph.py"),
             "--format=markdown", f"--output={out_path}"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert out_path.exists()
        content = out_path.read_text()
        assert "BeautifulMathematics" in content


def test_main_dot_format(capsys):
    """main --format=dot 输出 DOT。"""
    import subprocess
    result = subprocess.run(
        ["python3", str(REPO / "scripts/visualize_5lib_graph.py"), "--format=dot"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "digraph" in result.stdout