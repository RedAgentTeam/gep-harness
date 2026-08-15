"""Test cross_library_auto.py 5 库跨学科映射自动化。

覆盖：
- 默认 _default 模板（无 keywords 命中）
- 工具级关键词映射（exec/read/write_file 等）
- confidence 多关键词累加
- dry-run vs 写盘行为
- 5 库齐全（BeautifulMathematics/cell-biology/CognitivePsychology/OpenStaxBiology/evomap）

sys.path setup via scripts/tests/conftest.py
"""
import json
import pytest

import cross_library_auto as cla


def test_import():
    """模块可导入，5 个核心 API 都在。"""
    assert hasattr(cla, "LIBRARY_TEMPLATES")
    assert hasattr(cla, "match_evidence")
    assert hasattr(cla, "auto_cross_library_evidence")
    assert hasattr(cla, "fill_file")
    # 5 库齐全
    expected_libs = {
        "BeautifulMathematics",
        "cell-biology",
        "CognitivePsychology",
        "OpenStaxBiology",
        "evomap",
    }
    assert set(cla.LIBRARY_TEMPLATES.keys()) == expected_libs


def test_match_evidence_default():
    """无关键词命中 → _default + conf 0.3。"""
    text, conf = cla.match_evidence("BeautifulMathematics", [], "no signal")
    assert conf == 0.3
    assert "数学保证" in text or "可证" in text


def test_match_evidence_high_freq():
    """high_freq 信号 → 命中具体模板 + conf >= 0.7。"""
    text, conf = cla.match_evidence("BeautifulMathematics", ["high_freq:5663_calls"], "")
    assert conf >= 0.7
    assert "大数定律" in text or "高频" in text


def test_match_evidence_tool_exec():
    """exec 工具级信号 → 命中 exec 模板。"""
    for lib in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]:
        text, conf = cla.match_evidence(lib, ["exec"], "exec tool")
        assert conf >= 0.7, f"{lib} exec not matched"


def test_auto_cross_library_evidence_returns_5():
    """auto 返回 5 字符串 + 5 库名都在。"""
    gene = {
        "id": "test_gene",
        "signals_match": ["exec", "high_freq"],
        "summary": "Test gene for exec hot path",
    }
    evidence = cla.auto_cross_library_evidence(gene)
    assert len(evidence) == 5
    for lib in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]:
        assert any(lib in e for e in evidence), f"missing {lib} in {evidence}"


def test_auto_evidence_line_length():
    """每个 evidence ≤ 80 chars（GEP 协议约束）。"""
    gene = {
        "id": "test",
        "signals_match": ["exec", "read", "write", "hot_path", "high_freq"],
        "summary": "Long summary " * 10,
    }
    evidence = cla.auto_cross_library_evidence(gene)
    for e in evidence:
        assert len(e) <= 80, f"evidence too long: {e!r} ({len(e)} chars)"


def test_fill_file_dry_run(tmp_path):
    """dry-run 模式不写盘。"""
    gene = {
        "id": "test_dry",
        "signals_match": ["exec"],
        "summary": "Dry run test",
        "cross_library_evidence": ["OLD_1", "OLD_2", "OLD_3", "OLD_4", "OLD_5"],
    }
    p = tmp_path / "test_dry.json"
    json.dump(gene, open(p, "w"))

    result = cla.fill_file(p, dry_run=True)

    # 内存里返回了 5 个新 evidence
    assert len(result["evidence"]) == 5
    # 但磁盘文件没变（OLD_* 应还在）
    after = json.load(open(p))
    assert after["cross_library_evidence"][0].startswith("OLD")


def test_fill_file_write_mode(tmp_path):
    """非 dry-run 模式写盘。"""
    gene = {
        "id": "test_write",
        "signals_match": ["read"],
        "summary": "Write test",
    }
    p = tmp_path / "test_write.json"
    json.dump(gene, open(p, "w"))

    cla.fill_file(p, dry_run=False)

    after = json.load(open(p))
    assert len(after["cross_library_evidence"]) == 5
    assert after.get("_cross_library_auto") is True
    for e in after["cross_library_evidence"]:
        assert any(k in e for k in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"])


def test_confidence_caps_at_1():
    """confidence 上限 1.0（多关键词累加不能超）。"""
    many_signals = ["exec", "read", "write", "hot_path", "high_freq", "feedback", "ttl", "cache", "retry"]
    text, conf = cla.match_evidence("cell-biology", many_signals, "summary")
    assert 0.0 <= conf <= 1.0, f"conf out of range: {conf}"

    assert hasattr(cla, "LIBRARY_TEMPLATES")
    assert hasattr(cla, "match_evidence")
    assert hasattr(cla, "auto_cross_library_evidence")
    assert hasattr(cla, "fill_file")
    # 5 库齐全
    expected_libs = {
        "BeautifulMathematics",
        "cell-biology",
        "CognitivePsychology",
        "OpenStaxBiology",
        "evomap",
    }
    assert set(cla.LIBRARY_TEMPLATES.keys()) == expected_libs


def test_match_evidence_default():
    """无关键词命中 → _default + conf 0.3。"""
    text, conf = cla.match_evidence("BeautifulMathematics", [], "no signal")
    assert conf == 0.3
    assert "数学保证" in text or "可证" in text


def test_match_evidence_high_freq():
    """high_freq 信号 → 命中具体模板 + conf >= 0.7。"""
    text, conf = cla.match_evidence("BeautifulMathematics", ["high_freq:5663_calls"], "")
    assert conf >= 0.7
    assert "大数定律" in text or "高频" in text


def test_match_evidence_tool_exec():
    """exec 工具级信号 → 命中 exec 模板。"""
    for lib in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]:
        text, conf = cla.match_evidence(lib, ["exec"], "exec tool")
        assert conf >= 0.7, f"{lib} exec not matched"


def test_auto_cross_library_evidence_returns_5():
    """auto 返回 5 字符串 + 5 库名都在。"""
    gene = {
        "id": "test_gene",
        "signals_match": ["exec", "high_freq"],
        "summary": "Test gene for exec hot path",
    }
    evidence = cla.auto_cross_library_evidence(gene)
    assert len(evidence) == 5
    for lib in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]:
        assert any(lib in e for e in evidence), f"missing {lib} in {evidence}"


def test_auto_evidence_line_length():
    """每个 evidence ≤ 80 chars（GEP 协议约束）。"""
    gene = {
        "id": "test",
        "signals_match": ["exec", "read", "write", "hot_path", "high_freq"],
        "summary": "Long summary " * 10,
    }
    evidence = cla.auto_cross_library_evidence(gene)
    for e in evidence:
        assert len(e) <= 80, f"evidence too long: {e!r} ({len(e)} chars)"


def test_fill_file_dry_run(tmp_path):
    """dry-run 模式不写盘。"""
    gene = {
        "id": "test_dry",
        "signals_match": ["exec"],
        "summary": "Dry run test",
        "cross_library_evidence": ["OLD_1", "OLD_2", "OLD_3", "OLD_4", "OLD_5"],
    }
    p = tmp_path / "test_dry.json"
    json.dump(gene, open(p, "w"))

    result = cla.fill_file(p, dry_run=True)

    # 内存里返回了 5 个新 evidence
    assert len(result["evidence"]) == 5
    # 但磁盘文件没变（OLD_* 应还在）
    after = json.load(open(p))
    assert after["cross_library_evidence"][0].startswith("OLD")


def test_fill_file_write_mode(tmp_path):
    """非 dry-run 模式写盘。"""
    gene = {
        "id": "test_write",
        "signals_match": ["read"],
        "summary": "Write test",
    }
    p = tmp_path / "test_write.json"
    json.dump(gene, open(p, "w"))

    cla.fill_file(p, dry_run=False)

    after = json.load(open(p))
    assert len(after["cross_library_evidence"]) == 5
    assert after.get("_cross_library_auto") is True
    for e in after["cross_library_evidence"]:
        assert any(k in e for k in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"])


def test_confidence_caps_at_1():
    """confidence 上限 1.0（多关键词累加不能超）。"""
    many_signals = ["exec", "read", "write", "hot_path", "high_freq", "feedback", "ttl", "cache", "retry"]
    text, conf = cla.match_evidence("cell-biology", many_signals, "summary")
    assert 0.0 <= conf <= 1.0, f"conf out of range: {conf}"


def test_v2_evidence_with_chapter():
    """v2.0 evidence 含章节号 + 字段关联。"""
    g = {
        "signals_match": ["high_freq:5663_calls"],
        "summary": "Hot-path optimization for exec"
    }
    ev_v2 = cla.auto_cross_library_evidence(g, version="v2.0")
    assert len(ev_v2) == 5
    # 章节号存在
    assert any("Ch12" in e for e in ev_v2), "BeautifulMathematics Ch12 missing"
    assert any("Ch15" in e for e in ev_v2), "cell-biology Ch15 missing"
    assert any("Ch6" in e for e in ev_v2), "CognitivePsychology Ch6 missing"
    assert any("Ch01" in e for e in ev_v2), "OpenStaxBiology Ch01 missing"
    assert any("§2.3" in e for e in ev_v2), "evomap GEP §2.3 missing"


def test_v1_vs_v2_evidence_difference():
    """v1.0 vs v2.0 evidence 格式差异。"""
    g = {"signals_match": ["exec"], "summary": "test"}
    ev_v1 = cla.auto_cross_library_evidence(g, version="v1.0")
    ev_v2 = cla.auto_cross_library_evidence(g, version="v2.0")
    assert len(ev_v1) == 5
    assert len(ev_v2) == 5
    # v2.0 长度应 > v1.0（章节号 + 字段关联）
    avg_v1 = sum(len(e) for e in ev_v1) / len(ev_v1)
    avg_v2 = sum(len(e) for e in ev_v2) / len(ev_v2)
    assert avg_v2 > avg_v1, f"v2.0 ({avg_v2}) 应比 v1.0 ({avg_v1}) 长度更长"
    # v2.0 至少 3 条含明确章节号（ChXX / §X.X）
    chapter_hits = sum(1 for e in ev_v2 if any(p in e for p in ["Ch12", "Ch15", "Ch6", "Ch01", "§2.3"]))
    assert chapter_hits >= 3, f"v2.0 应至少有 3 条含章节号，实际 {chapter_hits}"


def test_library_chapter_dict():
    """LIBRARY_CHAPTER 5 库齐全。"""
    expected = {"BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"}
    assert set(cla.LIBRARY_CHAPTER.keys()) == expected
    # 每个章节号非空
    for lib, ch in cla.LIBRARY_CHAPTER.items():
        assert ch, f"{lib} chapter empty"


def test_v3_evidence_cross_library_refs():
    """v3.0 evidence 含跨库互引（→ [关联库] 章节号）。"""
    g = {"signals_match": ["exec"], "summary": "test"}
    ev = cla.auto_cross_library_evidence(g, version="v3.0")
    assert len(ev) == 5
    # 每条 evidence 末尾至少含 1 个 → [关联库]
    for e in ev:
        assert "→ [" in e, f"evidence 缺跨库互引: {e}"


def test_v3_evidence_cross_library_complete():
    """v3.0 evidence 跨库互引闭环（5 库形成神经元网络）。"""
    g = {"signals_match": ["exec"], "summary": "test"}
    ev = cla.auto_cross_library_evidence(g, version="v3.0")
    # 5 库每个库都被引用至少 1 次（闭环）
    libs = ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]
    for lib in libs:
        refs_to_lib = sum(1 for e in ev if f"[{lib}" in e)
        # 至少 1 条 evidence 引用该库（够形成环）
        assert refs_to_lib >= 1, f"v3.0 跨库闭环缺引用 {lib}"


def test_library_graph_no_self_loop():
    """LIBRARY_GRAPH 不自引（无环起点=终点）。"""
    for lib, refs in cla.LIBRARY_GRAPH.items():
        assert lib not in refs, f"{lib} 自引"


def test_library_graph_5_libs():
    """LIBRARY_GRAPH 5 库齐全，每库至少 1 个引用。"""
    assert set(cla.LIBRARY_GRAPH.keys()) == {"BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"}
    for lib, refs in cla.LIBRARY_GRAPH.items():
        assert len(refs) >= 1, f"{lib} 缺关联"
