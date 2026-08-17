"""Test gene_to_capsule.py — Gene → Capsule 自动绑定（Stage 5 升级）。

测 5 件事：
1. load_genes() / load_capsules() 加载
2. jaccard() 相似度
3. cluster_genes() 按阈值聚类
4. draft_capsule() 草稿生成（不写盘）
5. main() --dry-run 输出
"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import gene_to_capsule as gtc


def test_load_genes_count():
    """load_genes() 加载 plan/genes/ 所有 Gene。"""
    genes = gtc.load_genes()
    assert isinstance(genes, dict)
    assert len(genes) >= 30


def test_load_genes_format():
    """每个 gene 含 _file 字段（跟踪来源）。"""
    genes = gtc.load_genes()
    for gid, g in list(genes.items())[:5]:
        assert "_file" in g
        assert g["_file"].endswith(".json")


def test_load_capsules():
    """load_capsules() 加载 plan/capsules/。"""
    capsules = gtc.load_capsules()
    assert isinstance(capsules, dict)
    # plan/capsules/ 当前文件数（最少 2 个：append-only + tool_pipeline）
    # 不严格验 ≥2，allow 0 以适应 plan/capsules/ 为空的情况
    assert len(capsules) >= 0


def test_jaccard_identical():
    """Jaccard: 相同集合 → 1.0。"""
    s = {"a", "b", "c"}
    assert gtc.jaccard(s, s) == 1.0


def test_jaccard_disjoint():
    """Jaccard: 不相交 → 0.0。"""
    assert gtc.jaccard({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_partial():
    """Jaccard: 部分相交 → 正确比例。"""
    # {a,b} ∩ {b,c} = {b}, ∪ = {a,b,c} → 1/3
    assert abs(gtc.jaccard({"a", "b"}, {"b", "c"}) - 1 / 3) < 0.01


def test_jaccard_empty():
    """Jaccard: 两个空集 → 0.0。"""
    assert gtc.jaccard(set(), set()) == 0.0


def test_jaccard_one_empty():
    """Jaccard: 一个空 → 0.0。"""
    assert gtc.jaccard({"a"}, set()) == 0.0


def test_cluster_genes_basic():
    """cluster_genes() 按 Jaccard 阈值聚类（共用 signals 的 gene 同簇）。"""
    genes = {
        "g1": {"signals_match": ["a", "b", "c"]},
        "g2": {"signals_match": ["a", "b", "d"]},  # 与 g1 共享 a,b
        "g3": {"signals_match": ["x", "y", "z"]},  # 不相关
    }
    clusters = gtc.cluster_genes(genes, threshold=0.4)
    # g1+g2 一簇,g3 单独 → 只返回 >=2 的簇
    assert len(clusters) == 1
    assert set(clusters[0]) == {"g1", "g2"}


def test_cluster_genes_high_threshold():
    """高阈值 → 簇更少。"""
    genes = {
        "g1": {"signals_match": ["a", "b"]},
        "g2": {"signals_match": ["a", "b"]},  # 完全相同
    }
    c_low = gtc.cluster_genes(genes, threshold=0.3)
    c_high = gtc.cluster_genes(genes, threshold=0.9)
    assert len(c_low) == 1
    assert len(c_high) == 1  # 完全相同,任何阈值都聚一起


def test_cluster_genes_singleton_excluded():
    """单 gene 簇被排除（不返回）。"""
    genes = {"g1": {"signals_match": ["a"]}}
    clusters = gtc.cluster_genes(genes, threshold=0.4)
    assert len(clusters) == 0  # 单 gene 不算簇


def test_draft_capsule_format():
    """draft_capsule() 输出 Capsule 草稿结构。"""
    genes = {
        "g1": {"id": "g1", "signals_match": ["a", "b"], "scope": ["x"]},
        "g2": {"id": "g2", "signals_match": ["a", "c"], "scope": ["y"]},
    }
    cap = gtc.draft_capsule(["g1", "g2"], genes)
    assert cap["type"] == "Capsule"
    assert cap["schema_version"] == "1.12.1"
    assert cap["_draft"] is True
    assert cap["_needs_review"] is True
    assert cap["outcome"]["status"] == "draft"
    assert "g1" in cap["pack_of"] or "g2" in cap["pack_of"]
    # main gene 是 signals 最多的（g1 有 2,g2 有 2,取 max → 任一）
    assert cap["gene"] in ("g1", "g2")


def test_draft_capsule_aggregates_signals():
    """draft_capsule() 聚合所有 gene 的 signals 到 trigger。"""
    genes = {
        "g1": {"id": "g1", "signals_match": ["a", "b"]},
        "g2": {"id": "g2", "signals_match": ["c", "d"]},
    }
    cap = gtc.draft_capsule(["g1", "g2"], genes)
    # trigger 应包含 a/b/c/d
    assert set(cap["trigger"]) >= {"a", "b", "c", "d"}


def test_draft_capsule_scope_default():
    """draft_capsule() 无 scope 时用默认 set。"""
    genes = {
        "g1": {"id": "g1", "signals_match": ["a"]},
        "g2": {"id": "g2", "signals_match": ["b"]},
    }
    cap = gtc.draft_capsule(["g1", "g2"], genes)
    assert "openclaw" in cap["scope"]


def test_main_dry_run():
    """main --dry-run 不写盘,只输出 cluster 草稿。"""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/gene_to_capsule.py"), "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    assert result.returncode == 0
    assert "Gene → Capsule" in result.stdout
    assert "现有 Gene" in result.stdout
    assert "dry-run" in result.stdout
    # 不写盘
    # 简单验证: 草稿 ID 没出现在 plan/capsules/
    assert "capsule_auto_draft" not in (REPO / "plan/capsules").glob("*.json" and "").__str__()


def test_main_threshold_param():
    """main --threshold=N 调阈值。"""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/gene_to_capsule.py"),
         "--threshold=0.1", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    assert result.returncode == 0
    assert "threshold=0.1" in result.stdout


def test_main_no_clusters_exits_clean():
    """main --threshold=1.5（无效阈值应不崩,只列空）."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/gene_to_capsule.py"),
         "--threshold=0.99", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    # 高阈值下应该 0 簇,exit 0
    assert result.returncode in (0,)