"""Test cross_library_auto.py v13.0 — trust_score + v13.0 evidence format."""

import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import cross_library_auto as cla


def test_trust_score_returns_float_0_to_1():
    """trust_score 返回 0~1 之间的 float。"""
    for lib in cla.LIBRARY_GRAPH_EDGE:
        ts = cla.trust_score(lib, ["membrane", "channel"], "selective permeability")
        assert isinstance(ts, float)
        assert 0.0 <= ts <= 1.0


def test_trust_score_higher_for_relevant_signals():
    """trust_score 在命中相关关键词时更高。"""
    ts_high = cla.trust_score("cell-biology", ["membrane", "channel", "lipid"], "channel selectivity")
    ts_low = cla.trust_score("cell-biology", [], "")
    assert ts_high > ts_low, f"high={ts_high}, low={ts_low}"


def test_trust_score_all_libraries():
    """5 库都能算出 trust_score。"""
    for lib in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]:
        ts = cla.trust_score(lib, ["test"], "summary")
        assert ts >= 0.0


def test_v13_evidence_format():
    """v13.0 evidence 包含章节 + 互引 + trust_score。"""
    gene = {"signals_match": ["membrane", "channel"], "summary": "channel"}
    lines = cla.auto_cross_library_evidence(gene, version="v13.0")
    assert len(lines) == 5
    for line in lines:
        assert "[trust=" in line, f"missing trust_score: {line}"
        assert "Ch" in line or "§" in line, f"missing chapter: {line}"


def test_v13_backward_compatible_v2():
    """v2.0/v3.0/v13.0 都可用。"""
    gene = {"signals_match": ["membrane"], "summary": ""}
    v2 = cla.auto_cross_library_evidence(gene, version="v2.0")
    v3 = cla.auto_cross_library_evidence(gene, version="v3.0")
    v13 = cla.auto_cross_library_evidence(gene, version="v13.0")
    assert len(v2) == len(v3) == len(v13) == 5
    # v2: 无 trust_score 无互引
    for l in v2:
        assert "[trust=" not in l
    # v3: 无 trust_score 但有互引
    for l in v3:
        assert "[trust=" not in l
        assert "→" in l or "[" in l  # 跨库互引
    # v13: 都有
    for l in v13:
        assert "[trust=" in l


def test_v13_trust_score_format():
    """trust_score 格式: [trust=0.85]。"""
    gene = {"signals_match": ["asset_id", "canonicalize"], "summary": "verify"}
    lines = cla.auto_cross_library_evidence(gene, version="v13.0")
    for line in lines:
        # 提取最后一个 [trust=X.XX]
        import re
        m = re.search(r"\[trust=(\d+\.\d{2})\]$", line)
        assert m is not None, f"trust format wrong: {line}"


def test_v13_truncated_to_200_chars():
    """v13.0 行不超过 200 chars。"""
    gene = {"signals_match": ["x"] * 50, "summary": "y" * 200}
    lines = cla.auto_cross_library_evidence(gene, version="v13.0")
    for line in lines:
        assert len(line) <= 200, f"line too long ({len(line)}): {line[:50]}..."