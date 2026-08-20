"""Test v20.0 Phase 4: trust_score 接入 dynamic edges + Solidify 报告升级。"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import cross_library_auto as cla


def test_active_edges_default_static():
    """默认 _ACTIVE_EDGES = LIBRARY_GRAPH_EDGE（identity）。"""
    assert cla.get_active_edges() is cla.LIBRARY_GRAPH_EDGE


def test_set_active_edges_with_dict():
    """set_active_edges(dict) → get_active_edges 返回新 dict。"""
    dyn = {"X": {"Y": 0.9}}
    cla.set_active_edges(dyn)
    assert cla.get_active_edges() is dyn
    # 恢复
    cla.set_active_edges(None)


def test_set_active_edges_none_resets():
    """set_active_edges(None) → 恢复到静态基线。"""
    cla.set_active_edges({"X": {"Y": 0.9}})
    cla.set_active_edges(None)
    assert cla.get_active_edges() is cla.LIBRARY_GRAPH_EDGE


def test_set_active_edges_empty_resets():
    """set_active_edges({}) → 恢复静态。"""
    cla.set_active_edges({})
    assert cla.get_active_edges() is cla.LIBRARY_GRAPH_EDGE


def test_trust_score_default_static():
    """trust_score 默认从 _ACTIVE_EDGES 读（静态基线）。"""
    ts = cla.trust_score("BeautifulMathematics", ["幂等"], "test")
    # 静态基线 BM 出度均值 = (0.85+0.9+0.7+0.9+0.5)/5 = 0.77
    # conf 应 > 0.7，product 期望 [0.4, 0.85]
    assert 0.0 <= ts <= 1.0


def test_trust_score_with_dynamic_edges_param():
    """trust_score 显式传入 edges 参数 → 用传入的。"""
    custom = {"BeautifulMathematics": {"BeautifulMathematics": 0.5, "cell-biology": 1.0, "CognitivePsychology": 1.0, "OpenStaxBiology": 1.0, "evomap": 1.0}}
    ts_static = cla.trust_score("BeautifulMathematics", ["幂等"], "test")
    ts_dynamic = cla.trust_score("BeautifulMathematics", ["幂等"], "test", edges=custom)
    # 动态 edges 出度均值 = (0.5+1+1+1+1)/5 = 0.9，比静态高
    assert ts_dynamic > ts_static


def test_trust_score_active_edges_affects_default():
    """set_active_edges 后 trust_score 默认行为变化。"""
    dyn = {"BeautifulMathematics": {"BeautifulMathematics": 0.5, "cell-biology": 1.0, "CognitivePsychology": 1.0, "OpenStaxBiology": 1.0, "evomap": 1.0}}
    ts_before = cla.trust_score("BeautifulMathematics", ["幂等"], "test")
    cla.set_active_edges(dyn)
    ts_after = cla.trust_score("BeautifulMathematics", ["幂等"], "test")
    cla.set_active_edges(None)  # 恢复
    assert ts_after > ts_before


def test_trust_score_returns_in_range():
    """trust_score 永远返回 0~1。"""
    cla.set_active_edges({
        "X": {"Y": 0.0, "Z": 0.0},
    })
    ts = cla.trust_score("X", ["未知信号"], "")
    cla.set_active_edges(None)
    assert 0.0 <= ts <= 1.0


def test_trust_score_unknown_library_fallback():
    """未知库 → fallback 0.5 * conf。"""
    ts = cla.trust_score("Unknown_Lib", ["幂等"], "test")
    assert 0.0 <= ts <= 1.0


def test_auto_cross_library_evidence_uses_dynamic_trust():
    """auto_cross_library_evidence v13.0 的 trust_score 跟随 _ACTIVE_EDGES。"""
    dyn = {"BeautifulMathematics": {"BeautifulMathematics": 0.5, "cell-biology": 1.0, "CognitivePsychology": 1.0, "OpenStaxBiology": 1.0, "evomap": 1.0}}
    gene = {
        "signals_match": ["幂等"],
        "summary": "测试"
    }
    cla.set_active_edges(None)
    ev_static = cla.auto_cross_library_evidence(gene, version="v13.0")
    cla.set_active_edges(dyn)
    ev_dynamic = cla.auto_cross_library_evidence(gene, version="v13.0")
    cla.set_active_edges(None)
    # 找到 BM 那行（含 [trust=...] 尾部）
    bm_static = next(e for e in ev_static if "BeautifulMathematics" in e and "trust=" in e)
    bm_dynamic = next(e for e in ev_dynamic if "BeautifulMathematics" in e and "trust=" in e)
    # 提取 trust 数值
    trust_static = float(bm_static.split("trust=")[1].rstrip("]"))
    trust_dynamic = float(bm_dynamic.split("trust=")[1].rstrip("]"))
    assert trust_dynamic > trust_static


def test_solidify_imports_library_graph_edge():
    """solidify.py 导入 LIBRARY_GRAPH_EDGE（v20.0 报告识别用）。"""
    import solidify
    assert hasattr(solidify, "LIBRARY_GRAPH_EDGE")
    assert solidify.LIBRARY_GRAPH_EDGE is cla.LIBRARY_GRAPH_EDGE


def test_solidify_module_loads():
    """solidify.py 模块可导入不报错。"""
    import solidify
    assert hasattr(solidify, "main")


def test_get_active_edges_is_comparable():
    """Solidify 报告用 `is` 比较边源 → 必须 identity。"""
    default_edges = cla.get_active_edges()
    assert default_edges is cla.LIBRARY_GRAPH_EDGE
    # dynamic 时 is 应为 False
    cla.set_active_edges({"X": {"Y": 0.5}})
    assert cla.get_active_edges() is not cla.LIBRARY_GRAPH_EDGE
    cla.set_active_edges(None)
    assert cla.get_active_edges() is cla.LIBRARY_GRAPH_EDGE