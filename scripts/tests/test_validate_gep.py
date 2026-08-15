"""Test validate_gep.py — GEP strict validation."""

import json
import sys
from pathlib import Path

sys.path.insert(0, "/data/disk/gep-harness/scripts")
sys.path.insert(0, "/data/disk/gep-harness/openclaw-harness/bin")

from validate_gep import validate_one, REQUIRED_BY_TYPE, VALID_GENE_CATEGORIES
from canonicalize import compute_asset_id


def _write_gene(tmp_path: Path, gene: dict) -> str:
    """写 Gene JSON 到临时文件，返回路径。"""
    f = tmp_path / "test_gene.json"
    f.write_text(json.dumps(gene))
    return str(f)


def test_validate_one_minimal_gene(tmp_path):
    """最小 Gene（所有必需字段 + asset_id 正确）。"""
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_minimal",
        "category": "repair",
        "signals_match": ["test_signal"],
        "preconditions": ["test_precondition"],
        "strategy": ["test_strategy"],
        "constraints": {"max_files": 10},
        "validation": ["test validation"],
        "summary": "test summary",
        "cross_library_evidence": ["ev1", "ev2", "ev3", "ev4", "ev5"],
    }
    gene["asset_id"] = compute_asset_id(gene)
    ok, errors = validate_one(_write_gene(tmp_path, gene))
    assert ok is True
    assert errors == []


def test_validate_one_missing_required(tmp_path):
    """缺必需字段 → ok=False + errors 列表。"""
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_incomplete",
    }
    ok, errors = validate_one(_write_gene(tmp_path, gene))
    assert ok is False
    assert len(errors) > 0


def test_required_by_type_has_gene():
    """REQUIRED_BY_TYPE 含 Gene 类型。"""
    assert "Gene" in REQUIRED_BY_TYPE
    gene_required = REQUIRED_BY_TYPE["Gene"]
    assert "type" in gene_required
    assert "schema_version" in gene_required
    assert "id" in gene_required
    assert "asset_id" in gene_required


def test_valid_gene_categories():
    """VALID_GENE_CATEGORIES 包含 4 类。"""
    assert "repair" in VALID_GENE_CATEGORIES
    assert "optimize" in VALID_GENE_CATEGORIES
    assert "innovate" in VALID_GENE_CATEGORIES
    assert "explore" in VALID_GENE_CATEGORIES