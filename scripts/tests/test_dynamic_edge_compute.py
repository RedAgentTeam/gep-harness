"""Test dynamic_edge_compute.py — 5 库关联强度动态计算。"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import dynamic_edge_compute as dec


def test_constants():
    """模块常量正确。"""
    assert dec.REPO == REPO
    from cross_library_auto import LIBRARY_TEMPLATES
    assert dec.LIBS == list(LIBRARY_TEMPLATES.keys())


def test_normalize_lib_basic():
    """库名识别：BeautifulMathematics Ch17 分形 → BeautifulMathematics。"""
    assert dec.normalize_lib("BeautifulMathematics Ch17 分形") == "BeautifulMathematics"
    assert dec.normalize_lib("cell-biology Ch15 信号传导") == "cell-biology"
    assert dec.normalize_lib("CognitivePsychology Ch5 工作记忆") == "CognitivePsychology"
    assert dec.normalize_lib("OpenStaxBiology Ch11 进化") == "OpenStaxBiology"
    assert dec.normalize_lib("evomap GEP v1.12.1") == "evomap"


def test_normalize_lib_robust():
    """库名识别：去空格/连字符/章节号/小写。"""
    assert dec.normalize_lib("beautiful mathematics") == "BeautifulMathematics"
    assert dec.normalize_lib("CellBiology") == "cell-biology"
    assert dec.normalize_lib("OPENSTAX BIOLOGY Ch01") == "OpenStaxBiology"


def test_normalize_lib_invalid():
    """无效字符串返回 None。"""
    assert dec.normalize_lib("unknown_lib") is None
    assert dec.normalize_lib("") is None
    assert dec.normalize_lib(None) is None  # type: ignore


def test_scan_evidence_cooccurrence():
    """扫 plan/genes 60 个 gene 应有 evidence。"""
    result = dec.scan_evidence_cooccurrence()
    assert result["files_scanned"] >= 50  # 至少 50
    assert result["files_with_evidence"] >= 50
    matrix = result["matrix"]
    for lib in dec.LIBS:
        assert lib in matrix
        for tgt in dec.LIBS:
            assert tgt in matrix[lib]


def test_normalize_cooccurrence_to_edges():
    """共现矩阵 → 0~1 边权，对角线恒为 0.5。"""
    co = {
        "A": {"A": 10, "B": 5, "C": 2},
        "B": {"A": 5, "B": 10, "C": 8},
        "C": {"A": 2, "B": 8, "C": 10},
    }
    edges = dec.normalize_cooccurrence_to_edges(co)
    assert edges["A"]["A"] == 0.5  # 对角线恒定
    assert edges["B"]["B"] == 0.5
    # max_co = max(5, 2, 5, 8, 2, 8) = 8 (跨行非对角线的最大值)
    assert abs(edges["A"]["B"] - 5/8) < 0.01  # 5/8
    assert edges["B"]["C"] == 1.0  # 8/8 = 1.0
    assert abs(edges["A"]["C"] - 2/8) < 0.01  # 2/8


def test_normalize_cooccurrence_empty():
    """空矩阵 → 全 0.5 fallback。"""
    co = {"A": {"A": 0, "B": 0}, "B": {"A": 0, "B": 0}}
    edges = dec.normalize_cooccurrence_to_edges(co)
    assert edges["A"]["A"] == 0.5
    assert edges["A"]["B"] == 0.0  # max_co=1 fallback，0/1=0
    assert edges["B"]["A"] == 0.0


def test_merge_with_baseline():
    """baseline 0.5 + observed 1.0 weight 0.4 → 0.5*0.6+1.0*0.4=0.7。"""
    # 用真 5 库结构测试
    LIBS_5 = ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]
    baseline = {lib: {tgt: 0.5 for tgt in LIBS_5} for lib in LIBS_5}
    observed = {lib: {tgt: 0.5 for tgt in LIBS_5} for lib in LIBS_5}
    # BM ↔ cell-biology 观测 1.0
    observed["BeautifulMathematics"]["cell-biology"] = 1.0
    observed["cell-biology"]["BeautifulMathematics"] = 1.0
    merged = dec.merge_with_baseline(observed, baseline, weight_observed=0.4)
    assert merged["BeautifulMathematics"]["BeautifulMathematics"] == 0.5  # 对角线
    assert abs(merged["BeautifulMathematics"]["cell-biology"] - 0.7) < 0.01  # 0.5*0.6+1.0*0.4=0.7


def test_compute_real_repo():
    """compute() 在当前 repo 跑通：60 个样本，观测值生效。"""
    result = dec.compute(min_samples=5, weight_observed=0.4)
    assert result["version"] == "v19.0"
    assert result["used_observed"] is True
    assert "dynamic_edges" in result
    for src in dec.LIBS:
        assert src in result["dynamic_edges"]
        for tgt in dec.LIBS:
            v = result["dynamic_edges"][src][tgt]
            assert 0.0 <= v <= 1.0, f"{src}→{tgt}={v} 越界"


def test_compute_low_samples_fallback():
    """样本不足 → 全部用静态基线。"""
    result = dec.compute(min_samples=10000, weight_observed=0.4)
    assert result["used_observed"] is False
    assert "样本不足" in result["note"]


def test_visualize_load_dynamic_edges_missing(tmp_path):
    """visualize load_dynamic_edges 不存在 → None。"""
    from visualize_5lib_graph import load_dynamic_edges
    result = load_dynamic_edges(tmp_path / "nonexistent.json")
    assert result is None


def test_visualize_load_dynamic_edges_invalid(tmp_path):
    """visualize load_dynamic_edges 无效 JSON → None。"""
    from visualize_5lib_graph import load_dynamic_edges
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    result = load_dynamic_edges(bad)
    assert result is None


def test_visualize_load_dynamic_edges_no_field(tmp_path):
    """visualize load_dynamic_edges 无 dynamic_edges 字段 → None。"""
    from visualize_5lib_graph import load_dynamic_edges
    f = tmp_path / "no_field.json"
    f.write_text('{"foo": "bar"}')
    result = load_dynamic_edges(f)
    assert result is None


def test_visualize_load_dynamic_edges_ok(tmp_path):
    """visualize load_dynamic_edges 正常 JSON → 返回 edges。"""
    from visualize_5lib_graph import load_dynamic_edges
    f = tmp_path / "ok.json"
    f.write_text(json.dumps({
        "dynamic_edges": {
            "A": {"A": 0.5, "B": 0.9},
            "B": {"A": 0.9, "B": 0.5},
        }
    }))
    result = load_dynamic_edges(f)
    assert result is not None
    assert result["A"]["B"] == 0.9