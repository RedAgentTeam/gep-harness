"""Validate candidate Gene/Capsule/EvolutionEvent/Mutation JSON against GEP strict.

Stage 3 (Evolver) - Validate phase.

Usage:
  python3 validate_gep.py --mode=strict --input=staging/*.json
"""
import argparse
import glob
import json
import sys
from pathlib import Path

# Add openclaw-harness/bin to path for canonicalize
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openclaw-harness/bin"))
from canonicalize import compute_asset_id, verify_asset_id, SCHEMA_VERSION  # noqa: E402

REQUIRED_BY_TYPE = {
    "Gene": [
        "type", "schema_version", "id", "category", "signals_match",
        "strategy", "constraints", "validation", "asset_id",
    ],
    "Capsule": [
        "type", "schema_version", "id", "trigger", "gene", "summary",
        "confidence", "blast_radius", "outcome", "asset_id",
    ],
    "EvolutionEvent": [
        "type", "schema_version", "id", "intent", "signals", "genes_used",
        "mutation_id", "blast_radius", "outcome", "source_type", "asset_id",
    ],
    "Mutation": [
        "type", "id", "category", "trigger_signals", "target",
        "expected_effect", "risk_level",
    ],
}

VALID_GENE_CATEGORIES = ("repair", "optimize", "innovate", "explore")
VALID_RISK_LEVELS = ("low", "medium", "high")


def validate_one(path: str) -> tuple[bool, list[str]]:
    """Return (ok, list_of_errors)."""
    errors = []
    try:
        obj = json.load(open(path))
    except json.JSONDecodeError as e:
        return False, [f"JSON decode error: {e}"]

    t = obj.get("type")
    if t not in REQUIRED_BY_TYPE:
        return False, [f"unknown type: {t!r}"]

    # 1. schema_version
    if obj.get("schema_version") and obj["schema_version"] != SCHEMA_VERSION:
        errors.append(
            f"schema_version {obj['schema_version']!r} != {SCHEMA_VERSION!r}"
        )

    # 2. required fields
    for k in REQUIRED_BY_TYPE[t]:
        if k not in obj:
            errors.append(f"missing required field: {k}")

    # 3. type-specific constraints
    if t == "Gene":
        cat = obj.get("category")
        if cat and cat not in VALID_GENE_CATEGORIES:
            errors.append(f"invalid category: {cat!r}")
        sm = obj.get("signals_match")
        if sm is not None and not isinstance(sm, list):
            errors.append("signals_match must be a list")

    if t in ("Mutation", "EvolutionEvent"):
        cat = obj.get("category") or obj.get("intent")
        if cat and cat not in VALID_GENE_CATEGORIES:
            errors.append(f"invalid category/intent: {cat!r}")
        rl = obj.get("risk_level")
        if rl and rl not in VALID_RISK_LEVELS:
            errors.append(f"invalid risk_level: {rl!r}")

    # 4. asset_id strict (only if not placeholder)
    claimed = obj.get("asset_id")
    placeholder_values = ("sha256:PLACEHOLDER_LLM_TO_FILL", "sha256:PLACEHOLDER")
    if claimed and claimed not in placeholder_values:
        if not verify_asset_id(obj):
            errors.append(
                f"asset_id mismatch: claimed={claimed[:24]}... "
                f"computed={compute_asset_id(obj)[:24]}..."
            )

    return (len(errors) == 0), errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["strict", "loose"], default="strict")
    p.add_argument("--input", nargs="+", required=True, help="Files or globs (shell will expand globs before passing)")
    args = p.parse_args()

    files = []
    for pattern in args.input:
        files.extend(glob.glob(pattern))

    ok_count = fail_count = 0
    for path in sorted(files):
        ok, errors = validate_one(path)
        if ok:
            ok_count += 1
            print(f"✅ {path}")
        else:
            fail_count += 1
            print(f"❌ {path}")
            for e in errors:
                print(f"   - {e}")

    print(f"\n=== {ok_count} ok, {fail_count} fail ===")
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()