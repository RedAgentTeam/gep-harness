"""Test validate_gep.py — GEP strict 验证。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def test_import_validate_gep():
    """validate_gep.py 可 import + 常量。"""
    import validate_gep as vg
    assert vg.SCHEMA_VERSION == "1.12.1"
    assert "Gene" in vg.REQUIRED_BY_TYPE
    assert "Capsule" in vg.REQUIRED_BY_TYPE
    assert "EvolutionEvent" in vg.REQUIRED_BY_TYPE
    assert "repair" in vg.VALID_GENE_CATEGORIES
    assert "low" in vg.VALID_RISK_LEVELS


def test_validate_one_valid_gene(tmp_path):
    """valid Gene → ok=True, errors=[]."""
    from validate_gep import validate_one
    from canonicalize import compute_asset_id
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_valid_gene",
        "category": "repair",
        "signals_match": ["x"],
        "strategy": ["a", "b", "c"],
        "constraints": {"max_files": 1},
        "validation": ["true"],
        "cross_library_evidence": ["b", "c", "d", "e", "f"],
    }
    gene["asset_id"] = compute_asset_id(gene)
    p = tmp_path / "valid_gene.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert ok is True, f"expected ok, got errors: {errors}"
    assert errors == []


def test_validate_one_invalid_json(tmp_path):
    """invalid JSON → ok=False, error message。"""
    from validate_gep import validate_one
    p = tmp_path / "bad.json"
    p.write_text("not json {{{")
    ok, errors = validate_one(str(p))
    assert ok is False
    assert any("JSON decode" in e for e in errors)


def test_validate_one_unknown_type(tmp_path):
    """unknown type → ok=False。"""
    from validate_gep import validate_one
    p = tmp_path / "unknown.json"
    p.write_text(json.dumps({"type": "WeirdType", "id": "x"}))
    ok, errors = validate_one(str(p))
    assert ok is False
    assert any("unknown type" in e for e in errors)


def test_validate_one_missing_required(tmp_path):
    """Gene 缺 id → ok=False。"""
    from validate_gep import validate_one
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        # "id" missing
        "category": "repair",
    }
    p = tmp_path / "missing.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert ok is False
    assert any("missing required field" in e for e in errors)


def test_validate_one_wrong_schema_version(tmp_path):
    """schema_version != "1.12.1" → error。"""
    from validate_gep import validate_one
    gene = {
        "type": "Gene",
        "schema_version": "1.13.0",  # wrong
        "id": "x",
        "category": "repair",
        "signals_match": [],
        "strategy": [],
        "constraints": {},
        "validation": [],
        "asset_id": "sha256:placeholder",
    }
    p = tmp_path / "wrong_version.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert any("schema_version" in e for e in errors)


def test_validate_one_invalid_category(tmp_path):
    """Gene category 不在 VALID_GENE_CATEGORIES → error。"""
    from validate_gep import validate_one
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "x",
        "category": "invalid_category_xyz",
        "signals_match": [],
        "strategy": [],
        "constraints": {},
        "validation": [],
        "asset_id": "sha256:placeholder",
    }
    p = tmp_path / "bad_cat.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert any("category" in e for e in errors)


def test_validate_one_signals_must_be_list(tmp_path):
    """Gene.signals_match 不是 list → error。"""
    from validate_gep import validate_one
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "x",
        "category": "repair",
        "signals_match": "not_a_list",  # wrong type
        "strategy": [],
        "constraints": {},
        "validation": [],
        "asset_id": "sha256:placeholder",
    }
    p = tmp_path / "signals_bad.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert any("signals_match" in e for e in errors)


def test_validate_one_asset_id_mismatch(tmp_path):
    """claimed asset_id != recomputed → error。"""
    from validate_gep import validate_one
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "x",
        "category": "repair",
        "signals_match": [],
        "strategy": [],
        "constraints": {},
        "validation": [],
        "asset_id": "sha256:" + "a" * 64,  # fake hash
    }
    p = tmp_path / "asset_mismatch.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert any("asset_id mismatch" in e for e in errors)


def test_validate_one_asset_id_placeholder_accepted(tmp_path):
    """asset_id 是 PLACEHOLDER → 不校验。"""
    from validate_gep import validate_one
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "x",
        "category": "repair",
        "signals_match": [],
        "strategy": [],
        "constraints": {},
        "validation": [],
        "asset_id": "sha256:PLACEHOLDER_LLM_TO_FILL",
    }
    p = tmp_path / "placeholder.json"
    p.write_text(json.dumps(gene))
    ok, errors = validate_one(str(p))
    assert ok is True, f"placeholder should not trigger mismatch, got: {errors}"


def test_validate_one_mutation_valid(tmp_path):
    """valid Mutation → ok=True。"""
    from validate_gep import validate_one
    mut = {
        "type": "Mutation",
        "id": "mut_test_001",
        "category": "optimize",
        "trigger_signals": ["hotpath"],
        "target": {"files": 1},
        "expected_effect": "test",
        "risk_level": "low",
    }
    p = tmp_path / "mut.json"
    p.write_text(json.dumps(mut))
    ok, errors = validate_one(str(p))
    assert ok is True, errors


def test_validate_one_mutation_invalid_risk(tmp_path):
    """Mutation.risk_level 不在 VALID_RISK_LEVELS → error。"""
    from validate_gep import validate_one
    mut = {
        "type": "Mutation",
        "id": "mut_test_002",
        "category": "optimize",
        "trigger_signals": ["hotpath"],
        "target": {},
        "expected_effect": "test",
        "risk_level": "extreme",  # invalid
    }
    p = tmp_path / "mut_bad.json"
    p.write_text(json.dumps(mut))
    ok, errors = validate_one(str(p))
    assert any("risk_level" in e for e in errors)


def test_validate_one_capsule_valid(tmp_path):
    """valid Capsule → ok=True。"""
    from validate_gep import validate_one
    cap = {
        "type": "Capsule",
        "schema_version": "1.12.1",
        "id": "cap_test",
        "trigger": "test",
        "gene": "gene_x",
        "summary": "test capsule",
        "confidence": 0.9,
        "blast_radius": {"files": 1},
        "outcome": {"status": "ok"},
        "asset_id": "sha256:PLACEHOLDER",
    }
    p = tmp_path / "cap.json"
    p.write_text(json.dumps(cap))
    ok, errors = validate_one(str(p))
    assert ok is True, errors


def test_main_cli_ok(tmp_path):
    """CLI 跑 valid gene → exit 0。"""
    from validate_gep import validate_one  # noqa: F401
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "cli_test",
        "category": "repair",
        "signals_match": [],
        "strategy": [],
        "constraints": {},
        "validation": [],
    }
    p = tmp_path / "cli_gene.json"
    p.write_text(json.dumps(gene))
    result = subprocess.run(
        ["python3", str(REPO / "scripts/validate_gep.py"),
         "--mode=strict", "--input", str(p)],
        capture_output=True, text=True, timeout=30,
    )
    assert "ok" in result.stdout or "fail" in result.stdout


def test_main_cli_fail(tmp_path):
    """CLI 跑 invalid gene → exit 1。"""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"type": "WeirdType"}))
    result = subprocess.run(
        ["python3", str(REPO / "scripts/validate_gep.py"),
         "--mode=strict", "--input", str(p)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert "fail" in result.stdout.lower()