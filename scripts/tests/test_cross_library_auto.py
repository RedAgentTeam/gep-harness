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
