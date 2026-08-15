"""Regression tests for C1: solidify.py and canonicalize.py MUST agree.

Before C1 fix, solidify.py had a local compute_asset_id wrapper that stripped
8 "protected" fields before passing to canonicalize.py. The wrapper produced
a DIFFERENT asset_id than canonicalize.py's standard compute_asset_id,
meaning every Gene solidified would FAIL verify when checked by validate_gep.

After C1: solidify.py imports compute_asset_id from canonicalize.py directly.
This test pins down the agreement so future refactors don't reintroduce the bug.

3 pytest:
  1. solidify.compute_asset_id is canonicalize.compute_asset_id (identity)
  2. For a Gene with all 8 protected fields populated, asset_id is the same
     from both modules
  3. canonicalize.py's compute_asset_id only excludes asset_id (not 8 fields)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "openclaw-harness" / "bin"))

from canonicalize import compute_asset_id as canonical_compute_asset_id  # noqa: E402


def test_solidify_compute_asset_id_is_canonical_compute_asset_id():
    """After C1 fix, solidify.compute_asset_id must be the canonical one."""
    from solidify import compute_asset_id as solidify_compute_asset_id
    # Identity check: must be the same function object
    assert solidify_compute_asset_id is canonical_compute_asset_id, (
        "solidify.compute_asset_id should be canonicalize.compute_asset_id "
        "(C1 fix); they are currently different objects"
    )


def test_gene_with_all_protected_fields_produces_same_asset_id():
    """For a Gene with all 8 protected fields populated, the asset_id computed
    by solidify and by canonicalize must match.

    This is the regression test for the bug where solidify stripped the 8
    protected fields, producing a different hash than validate_gep (which
    uses canonicalize's standard exclude_fields=("asset_id",)).
    """
    from solidify import compute_asset_id as solidify_compute_asset_id

    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_gene_c1_regression",
        "signals_match": ["test"],
        "preconditions": {"python": "3.12"},
        "constraints": {"max_files": 5},
        "validation": {"pytest": "scripts/tests/test_canonicalize_unified.py"},
        "category": "repair",
        "strategy": "do_something",
        "nested": {"b": 2, "a": 1},  # recursive sort must apply
        "list": [{"y": 2, "x": 1}],
    }
    asset_id_solidify = solidify_compute_asset_id(gene)
    asset_id_canonical = canonical_compute_asset_id(gene)
    assert asset_id_solidify == asset_id_canonical, (
        f"asset_id mismatch (C1 fix): solidify={asset_id_solidify} "
        f"canonical={asset_id_canonical}"
    )


def test_canonicalize_excludes_only_asset_id():
    """Pinned invariant: canonicalize.compute_asset_id default exclude_fields
    is ONLY ('asset_id',). If a future refactor adds more fields to that tuple,
    solidify and validate_gep would diverge again — fail loud here.
    """
    import inspect
    sig = inspect.signature(canonical_compute_asset_id)
    exclude_default = sig.parameters["exclude_fields"].default
    assert exclude_default == ("asset_id",), (
        f"canonicalize.compute_asset_id default exclude_fields changed to "
        f"{exclude_default!r}. This will re-break C1 invariant. Re-coordinate "
        f"with solidify.py and validate_gep.py if this change is intentional."
    )