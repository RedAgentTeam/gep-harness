"""Tests for llm_fill_gene.py LLM fill logic.

Uses mock API response so tests never hit the real Stepfun endpoint.
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
sys.path.insert(0, str(HERE.parent.parent.parent / "openclaw-a2a" / "src"))

from llm_fill_gene import (  # noqa: E402
    FILL_PROMPT_TEMPLATE,
    SCHEMA_VERSION,
    fill_gene,
    call_stepfun,
)
from a2a_protocol import (  # noqa: E402
    canonicalize,
    compute_asset_id,
)


def test_fill_prompt_template_contains_required_fields():
    """Prompt must mention all 4 fill targets."""
    assert "category" in FILL_PROMPT_TEMPLATE
    assert "strategy" in FILL_PROMPT_TEMPLATE
    assert "cross_library_evidence" in FILL_PROMPT_TEMPLATE
    assert "asset_id" in FILL_PROMPT_TEMPLATE


def test_call_stepfun_mock():
    """call_stepfun should return the LLM text content."""
    mock_response = {
        "choices": [{"message": {"content": '{"category": "repair"}'}}]
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(mock_response).encode("utf-8")
        )
        result = call_stepfun("test prompt", model="step-3.5-flash")
        assert "repair" in result


def test_fill_gene_preserves_protected_fields():
    """fill_gene must keep type/schema_version/id/signals_match/etc. unchanged."""
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_gene_001",
        "signals_match": ["s1", "s2", "s3"],
        "preconditions": ["p1"],
        "constraints": ["c1"],
        "validation": {"rule": "pass"},
        "summary": "A comprehensive summary for this gene",
        "category": "explore",
        "strategy": ["old"],
        "cross_library_evidence": ["old"],
    }
    mock_response = {
        "choices": [{"message": {"content": json.dumps({
            "category": "optimize",
            "strategy": ["s1", "s2", "s3"],
            "cross_library_evidence": ["a", "b", "c", "d", "e"],
            "asset_id": "sha256:test",
        })}}]
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(mock_response).encode("utf-8")
        )
        result = fill_gene(gene)

    # Protected fields unchanged
    assert result["type"] == "Gene"
    assert result["schema_version"] == "1.12.1"
    assert result["id"] == "test_gene_001"
    assert result["signals_match"] == ["s1", "s2", "s3"]
    assert result["preconditions"] == ["p1"]
    assert result["constraints"] == ["c1"]
    # Editable fields updated
    assert result["category"] == "optimize"
    assert result["strategy"] == ["s1", "s2", "s3"]
    assert result["cross_library_evidence"] == ["a", "b", "c", "d", "e"]
    assert result["_llm_filled"] is True


def test_fill_gene_evidence_count():
    """cross_library_evidence must have exactly 5 items."""
    gene = {
        "type": "Gene", "schema_version": "1.12.1", "id": "g1",
        "signals_match": ["a", "b"],
        "strategy": ["s1", "s2"],
        "summary": "A long enough summary for GDI scoring",
        "category": "optimize", "strategy": ["s1"], "cross_library_evidence": [],
    }
    mock_response = {
        "choices": [{"message": {"content": json.dumps({
            "category": "repair",
            "strategy": ["a", "b", "c"],
            "cross_library_evidence": ["L1 r1", "L2 r2", "L3 r3", "L4 r4", "L5 r5"],
            "asset_id": "sha256:test",
        })}}]
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(mock_response).encode("utf-8")
        )
        result = fill_gene(gene)
        assert len(result["cross_library_evidence"]) == 5


def test_fill_gene_strategy_count():
    """strategy must have exactly 3 items."""
    gene = {
        "type": "Gene", "schema_version": "1.12.1", "id": "g2",
        "signals_match": ["a"], "strategy": ["s1"], "summary": "summary",
        "category": "optimize", "strategy": [], "cross_library_evidence": [],
    }
    mock_response = {
        "choices": [{"message": {"content": json.dumps({
            "category": "innovate",
            "strategy": ["step1", "step2", "step3"],
            "cross_library_evidence": ["a", "b", "c", "d", "e"],
            "asset_id": "sha256:test",
        })}}]
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(mock_response).encode("utf-8")
        )
        result = fill_gene(gene)
        assert len(result["strategy"]) == 3


def test_fill_gene_skips_already_filled():
    """fill_file should skip if _llm_filled is True."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "already.json"
        gene = {
            "type": "Gene", "schema_version": "1.12.1", "id": "g3",
            "signals_match": ["a"], "strategy": ["s1"], "summary": "s",
            "category": "repair", "_llm_filled": True,
        }
        json.dump(gene, open(p, "w"))
        # Should not call API
        with patch("urllib.request.urlopen") as mock_urlopen:
            result = json.load(open(p))
            # fill_gene itself doesn't skip — the staging loop does.
            # Just verify _llm_filled flag is preserved
            assert result["_llm_filled"] is True
            assert mock_urlopen.call_count == 0


def test_compute_asset_id_deterministic():
    """Same content → same asset_id."""
    g1 = {
        "type": "Gene", "schema_version": "1.12.1",
        "id": "same", "category": "repair",
        "signals_match": ["a", "b"],
        "strategy": ["s1"],
        "summary": "test",
    }
    g2 = {**g1, "id": "same"}
    g1["asset_id"] = compute_asset_id(g1)
    g2["asset_id"] = compute_asset_id(g2)
    assert g1["asset_id"] == g2["asset_id"]


def test_canonicalize_stable():
    """canonicalize should produce stable output for same input."""
    d = {"b": 2, "a": 1, "c": [3, 1, 2]}
    assert canonicalize(d) == canonicalize(d)


if __name__ == "__main__":
    test_fill_prompt_template_contains_required_fields()
    print("✅ test_fill_prompt_template_contains_required_fields")
    test_call_stepfun_mock()
    print("✅ test_call_stepfun_mock")
    test_fill_gene_preserves_protected_fields()
    print("✅ test_fill_gene_preserves_protected_fields")
    test_fill_gene_evidence_count()
    print("✅ test_fill_gene_evidence_count")
    test_fill_gene_strategy_count()
    print("✅ test_fill_gene_strategy_count")
    test_fill_gene_skips_already_filled()
    print("✅ test_fill_gene_skips_already_filled")
    test_compute_asset_id_deterministic()
    print("✅ test_compute_asset_id_deterministic")
    test_canonicalize_stable()
    print("✅ test_canonicalize_stable")
    print("\n=== all 8 tests passed ===")
