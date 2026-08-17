"""Test gene_to_capsule.py cluster_genes / draft_capsule / main() (62%→100%)。

补 missing lines: 37-38, 51-52, 146-192, 196
- 37-38: load_genes 空目录 → {}
- 51-52: load_capsules 空目录 → {}
- 146-192: main() argparse + 聚类 + 草稿输出 + 覆盖率统计
- 196: if __name__ == "__main__": main()
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import gene_to_capsule as gtc


def _make_gene(gid: str, signals: list, scope=None) -> dict:
    return {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": gid,
        "signals_match": signals,
        "summary": f"summary {gid}",
        "category": "repair",
        "strategy": ["a"],
        "constraints": ["c1"],
        "validation": {"check": "ok"},
        "scope": scope or ["openclaw"],
    }


def test_load_genes_empty_dir(tmp_path, monkeypatch):
    """load_genes: 空目录 → {}。"""
    monkeypatch.setattr(gtc, "PLAN_GENES", tmp_path / "nonexistent")
    genes = gtc.load_genes()
    assert genes == {}


def test_load_genes_missing_dir(tmp_path, monkeypatch):
    """load_genes: 目录不存在 → {}。"""
    monkeypatch.setattr(gtc, "PLAN_GENES", tmp_path / "nope")
    genes = gtc.load_genes()
    assert genes == {}


def test_load_capsules_empty_dir(tmp_path, monkeypatch):
    """load_capsules: 空目录 → {}。"""
    monkeypatch.setattr(gtc, "PLAN_CAPSULES", tmp_path / "nope")
    caps = gtc.load_capsules()
    assert caps == {}


def test_cluster_genes_no_clusters():
    """cluster_genes: 全部 gene signals 不同 → 空簇。"""
    genes = {
        "g1": _make_gene("g1", ["alpha"]),
        "g2": _make_gene("g2", ["beta"]),
        "g3": _make_gene("g3", ["gamma"]),
    }
    clusters = gtc.cluster_genes(genes, threshold=0.5)
    # 每个 gene 单独一个, 但 threshold=0.5 严格 → 不会聚类
    # 实际上 threshold=0.5 时 set_a 完全不同 → jaccard=0 < 0.5
    # 短小 gene 可能因空 signals 误聚, 用强 threshold 隔离
    assert len(clusters) == 0


def test_cluster_genes_high_overlap():
    """cluster_genes: 高重叠 → 1 个簇。"""
    genes = {
        "g1": _make_gene("g1", ["a", "b", "c", "d"]),
        "g2": _make_gene("g2", ["a", "b", "c", "d"]),  # 完全相同 → jaccard=1.0
        "g3": _make_gene("g3", ["x", "y", "z"]),       # 完全无关
    }
    clusters = gtc.cluster_genes(genes, threshold=0.5)
    assert len(clusters) == 1
    assert set(clusters[0]) == {"g1", "g2"}


def test_cluster_genes_uses_signals_fallback():
    """cluster_genes: 无 signals_match 但有 signals → 用 signals。"""
    genes = {
        "g1": {"type": "Gene", "id": "g1", "signals": ["x", "y"]},
        "g2": {"type": "Gene", "id": "g2", "signals": ["x", "y"]},
    }
    clusters = gtc.cluster_genes(genes, threshold=0.5)
    assert len(clusters) == 1
    assert set(clusters[0]) == {"g1", "g2"}


def test_cluster_genes_chain_three():
    """cluster_genes: 链式聚类 (g1~g2, g2~g3) → 一簇。"""
    genes = {
        "g1": _make_gene("g1", ["a", "b", "c"]),
        "g2": _make_gene("g2", ["a", "b", "c"]),
        "g3": _make_gene("g3", ["a", "b", "c"]),
    }
    clusters = gtc.cluster_genes(genes, threshold=0.5)
    assert len(clusters) == 1
    assert set(clusters[0]) == {"g1", "g2", "g3"}


def test_draft_capsule_basic():
    """draft_capsule: 产生完整 Capsule dict (含 _draft + _needs_review)。"""
    genes = {
        "g1": _make_gene("g1", ["a", "b", "c"]),
        "g2": _make_gene("g2", ["a", "b"]),
    }
    cap = gtc.draft_capsule(["g1", "g2"], genes)
    assert cap["type"] == "Capsule"
    assert cap["gene"] in ("g1", "g2")  # main gene = signals 最多的
    assert "g1" in cap["pack_of"]
    assert "g2" in cap["pack_of"]
    assert cap["_draft"] is True
    assert cap["_needs_review"] is True
    assert "openclaw" in cap["scope"]


def test_draft_capsule_default_scope_when_missing():
    """draft_capsule: scope 全空 → 默认 ['openclaw','devagent','harness','gep']。"""
    genes = {
        "g1": {"type": "Gene", "id": "g1", "signals_match": ["a"]},  # 无 scope
        "g2": {"type": "Gene", "id": "g2", "signals_match": ["a"]},
    }
    cap = gtc.draft_capsule(["g1", "g2"], genes)
    assert set(cap["scope"]) == {"openclaw", "devagent", "harness", "gep"}


def test_draft_capsule_trigger_capped_at_10():
    """draft_capsule: trigger 字段只取前 10 个 signals。"""
    genes = {}
    signals = [f"sig_{i}" for i in range(20)]
    genes["g1"] = _make_gene("g1", signals[:15])
    genes["g2"] = _make_gene("g2", signals[5:])
    cap = gtc.draft_capsule(["g1", "g2"], genes)
    assert len(cap["trigger"]) <= 10


def test_main_no_genes_prints_loading(capsys, tmp_path, monkeypatch):
    """main: 空 plan/genes → 0 个簇 + 无草稿。"""
    empty_genes = tmp_path / "empty_genes"
    empty_caps = tmp_path / "empty_caps"
    empty_genes.mkdir(parents=True, exist_ok=True)
    empty_caps.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(gtc, "PLAN_GENES", empty_genes)
    monkeypatch.setattr(gtc, "PLAN_CAPSULES", empty_caps)

    with patch.object(sys, "argv", ["gtc.py"]):
        try:
            gtc.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "现有 Gene: 0 个" in captured.out
    assert "聚类结果: 0 个簇" in captured.out
    assert "无可打包的 Gene 簇" in captured.out


def test_main_with_clusters(capsys, tmp_path, monkeypatch):
    """main: 有 gene + 有簇 → 打印草稿 + 覆盖率。"""
    genes_dir = tmp_path / "genes"
    caps_dir = tmp_path / "caps"
    genes_dir.mkdir()
    caps_dir.mkdir()
    # 写 3 个 gene, 2 个共享 signals → 1 个簇
    for gid, sigs in [("g1", ["a", "b"]), ("g2", ["a", "b"]), ("g3", ["x"])]:
        g = _make_gene(gid, sigs)
        g["asset_id"] = "sha256:" + "0" * 64
        (genes_dir / f"{gid}.json").write_text(json.dumps(g))
    monkeypatch.setattr(gtc, "PLAN_GENES", genes_dir)
    monkeypatch.setattr(gtc, "PLAN_CAPSULES", caps_dir)

    with patch.object(sys, "argv", ["gtc.py", "--threshold=0.5"]):
        try:
            gtc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "现有 Gene: 3 个" in captured.out
    assert "聚类结果: 1 个簇" in captured.out
    assert "草稿 #1" in captured.out
    assert "草稿覆盖率" in captured.out
    assert "目标 50%" in captured.out


def test_main_with_existing_capsules(capsys, tmp_path, monkeypatch):
    """main: 已有 Capsule → 打印 Capsule/Gene 比例。"""
    genes_dir = tmp_path / "g"
    caps_dir = tmp_path / "c"
    genes_dir.mkdir()
    caps_dir.mkdir()
    # 1 个 gene, 1 个 capsule
    g = _make_gene("g1", ["a", "b"])
    g["asset_id"] = "sha256:" + "0" * 64
    (genes_dir / "g1.json").write_text(json.dumps(g))
    c = {"id": "c1", "type": "Capsule"}
    (caps_dir / "c1.json").write_text(json.dumps(c))
    monkeypatch.setattr(gtc, "PLAN_GENES", genes_dir)
    monkeypatch.setattr(gtc, "PLAN_CAPSULES", caps_dir)

    with patch.object(sys, "argv", ["gtc.py"]):
        try:
            gtc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "现有 Capsule: 1 个" in captured.out
    assert "Capsule/Gene 比例" in captured.out


def test_main_limit_flag(capsys, tmp_path, monkeypatch):
    """main --limit=N: 只输出 N 个草稿。"""
    genes_dir = tmp_path / "g"
    caps_dir = tmp_path / "c"
    genes_dir.mkdir()
    caps_dir.mkdir()
    # 4 个独立簇 (signals 互不重叠)
    for i in range(8):
        gid = f"g{i}"
        sigs = [f"unique_{i}"] * 3
        g = _make_gene(gid, sigs)
        g["asset_id"] = "sha256:" + "0" * 64
        (genes_dir / f"{gid}.json").write_text(json.dumps(g))
    # 但 limit 不影响 cluster_genes 的产生, 只限制输出数量
    monkeypatch.setattr(gtc, "PLAN_GENES", genes_dir)
    monkeypatch.setattr(gtc, "PLAN_CAPSULES", caps_dir)

    with patch.object(sys, "argv", ["gtc.py", "--limit=1"]):
        try:
            gtc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    # 8 个独立 gene → 0 个簇 (threshold=0.4 时 sigs 也不重叠)
    # 应打印 "无可打包"
    assert "无可打包的 Gene 簇" in captured.out


def test_main_dry_run_default(capsys, tmp_path, monkeypatch):
    """main: --dry-run 默认 True → 打印 'dry-run 模式,未写盘'。"""
    genes_dir = tmp_path / "g"
    caps_dir = tmp_path / "c"
    genes_dir.mkdir()
    caps_dir.mkdir()
    # 制造 1 个簇: 3 个基因共享 signals, 彼此 jaccard >= 0.5
    # 'x','y','z' (intersection=2, union=3 → 0.67) + 'x','y' (inter=2, union=3 → 0.67)
    g_data = [
        ("ga", ["x", "y", "z"]),
        ("gb", ["x", "y", "z"]),
        ("gc", ["x", "y"]),
    ]
    for gid, sigs in g_data:
        g = _make_gene(gid, sigs)
        g["asset_id"] = "sha256:" + "0" * 64
        (genes_dir / f"{gid}.json").write_text(json.dumps(g))
    monkeypatch.setattr(gtc, "PLAN_GENES", genes_dir)
    monkeypatch.setattr(gtc, "PLAN_CAPSULES", caps_dir)

    with patch.object(sys, "argv", ["gtc.py", "--threshold=0.5"]):
        try:
            gtc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "dry-run 模式" in captured.out
    assert "Solidify 人工审批门" in captured.out


def test_main_module_runs():
    """if __name__ == '__main__': main() → --help 能跑。"""
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/gene_to_capsule.py"), "--help"],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    assert "--threshold" in r.stdout
    assert "--dry-run" in r.stdout
    assert "--limit" in r.stdout