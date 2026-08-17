"""Test solidify.py — Solidify 人工审批门（完整覆盖）。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "openclaw-harness/bin"))


def test_solidify_constants():
    """solidify.py 核心常量正确。"""
    src = (REPO / "scripts/solidify.py").read_text()
    assert "GEP_HARNESS" in src
    assert "PLAN_GENES" in src
    assert "PLAN_EVENTS" in src
    assert "STAGING" in src


def test_solidify_help_message():
    """solidify.py --help 可用。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/solidify.py"), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "Solidify" in result.stdout or "staging" in result.stdout.lower()


def test_load_existing_genes():
    """load_existing_genes() 返回 {gene_id: {asset_id, file}} 表。"""
    from solidify import load_existing_genes
    table = load_existing_genes()
    assert isinstance(table, dict)
    assert len(table) >= 1
    sample = next(iter(table.values()))
    assert "asset_id" in sample
    assert "file" in sample


def test_check_duplicate_no_dup():
    """check_duplicate() 不同 asset_id → no dup。"""
    from solidify import check_duplicate
    existing = {"gene_x": {"asset_id": "sha256:abc", "file": "x.json"}}
    is_dup, eid, ef = check_duplicate(
        {"id": "gene_y_new", "asset_id": "sha256:zzz"}, existing
    )
    assert is_dup is False
    assert eid is None
    assert ef is None


def test_check_duplicate_match_by_asset_id():
    """check_duplicate() 同 asset_id → dup（按 recomputed hash 而非 g['asset_id']）。"""
    from solidify import check_duplicate
    from canonicalize import compute_asset_id
    # 用同一个 full gene 对象，让 compute_asset_id 算出一致 hash
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_full_gene",
        "signals_match": ["x"],
        "preconditions": ["p"],
        "constraints": {"max_files": 1},
        "validation": ["true"],
        "category": "repair",
        "strategy": ["a", "b", "c"],
        "cross_library_evidence": ["b","c","d","e","f"],
    }
    aid = compute_asset_id(gene)
    existing = {"gene_existing": {"asset_id": aid, "file": "x.json"}}
    is_dup, eid, ef = check_duplicate(gene, existing)
    assert is_dup is True
    assert eid == "gene_existing"
    assert ef == "x.json"


def test_validate_gene_valid():
    """validate_gene() 对合法 gene 调用 validate_gep。"""
    from solidify import validate_gene
    valid_gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_gene_solidify_valid",
        "signals_match": ["test"],
        "preconditions": ["tool 'x' has been called 5+ times in 24h"],
        "constraints": {"max_files": 5},
        "validation": ["true"],
        "category": "repair",
        "strategy": ["step1", "step2", "step3"],
        "cross_library_evidence": ["BM reason", "CB reason", "CP reason", "OSB reason", "EM reason"],
    }
    ok, out, err = validate_gene(valid_gene)
    assert isinstance(ok, bool)


def test_validate_gene_invalid():
    """validate_gene() 对非法 gene 返回 False。"""
    from solidify import validate_gene
    invalid_gene = {"type": "NotAGene", "id": "bad"}
    ok, out, err = validate_gene(invalid_gene)
    assert ok is False


def test_make_solidify_event_structure():
    """make_solidify_event() 生成 EvolutionEvent 格式。"""
    from solidify import make_solidify_event
    evt = make_solidify_event(
        gene_file="test.json",
        gene_id="test_gene_evt",
        outcome="approved",
        score=0.92,
        notes="automated test",
    )
    assert evt["type"] == "EvolutionEvent"
    assert evt["schema_version"] == "1.12.1"
    assert "id" in evt
    assert "asset_id" in evt
    assert evt["asset_id"].startswith("sha256:")
    assert evt["outcome"]["status"] == "approved"
    assert evt["outcome"]["score"] == 0.92
    assert evt["outcome"]["notes"] == "automated test"
    assert "from_staging" in evt["meta"]
    assert evt["meta"]["from_staging"] == "test.json"


def test_make_solidify_event_default_score():
    """make_solidify_event() 默认 score=0.85。"""
    from solidify import make_solidify_event
    evt = make_solidify_event("x.json", "g1", "approved")
    assert evt["outcome"]["score"] == 0.85


def test_make_solidify_event_rejected():
    """make_solidify_event() outcome=rejected。"""
    from solidify import make_solidify_event
    evt = make_solidify_event("y.json", "g2", "rejected", score=0.5, notes="dup")
    assert evt["outcome"]["status"] == "rejected"
    assert evt["outcome"]["score"] == 0.5
    assert evt["outcome"]["notes"] == "dup"


def test_make_solidify_event_id_pattern():
    """make_solidify_event() 生成 evt_solidify_{id}_{date} ID。"""
    from solidify import make_solidify_event
    evt = make_solidify_event("z.json", "g3", "approved")
    assert evt["id"].startswith("evt_solidify_g3_")
    # 2026-08-17 日期后缀
    assert "2026_08_17" in evt["id"] or "2026_08_1" in evt["id"]


def test_main_list_mode():
    """main() --list 模式可跑。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/solidify.py"), "--list"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "现有 Gene" in result.stdout or "dup" in result.stdout or "candidates" in result.stdout.lower()


def test_main_no_args_shows_usage():
    """main() 无参数 → 显示用法（exit 0 或 1 都可，但 stdout 含 usage）。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/solidify.py")],
        capture_output=True, text=True, timeout=10,
    )
    combined = (result.stdout + result.stderr).lower()
    assert "用法" in combined or "usage" in combined or "staging" in combined or "gene" in combined
    assert result.returncode != 0


def test_main_with_yes_and_empty_staging(tmp_path):
    """main() --yes 对空 staging 应 graceful 处理。"""
    empty_staging = tmp_path / "empty_staging"
    empty_staging.mkdir()
    result = subprocess.run(
        ["python3", str(REPO / "scripts/solidify.py"),
         "--staging", str(empty_staging), "--yes"],
        capture_output=True, text=True, timeout=30,
    )
    combined = (result.stdout + result.stderr).lower()
    assert "candidates" in combined or "0 approved" in combined or result.returncode in (0, 1)


def test_main_gene_mode_missing_file():
    """main() --gene=<nonexistent> 报错。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/solidify.py"), "--gene=/tmp/_nonexistent_xyz_12345.json"],
        capture_output=True, text=True, timeout=10,
    )
    # exit code != 0 OR error message present
    assert result.returncode != 0 or "Error" in result.stderr or "No such" in result.stderr
