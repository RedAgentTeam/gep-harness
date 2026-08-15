"""GEP strict validation runner — used by Makefile verify target.

Usage: python3 scripts/verify_assets.py
"""
import json
import sys
import glob

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openclaw-harness/bin"))
from canonicalize import compute_asset_id

total_ok = 0
total_fail = 0
for path in sorted(
    glob.glob(str(Path(__file__).resolve().parent.parent / "plan/genes/*.json"))
    + glob.glob(str(Path(__file__).resolve().parent.parent / "plan/capsules/*.json"))
    + glob.glob(str(Path(__file__).resolve().parent.parent / "plan/events/*.json"))
):
    obj = json.load(open(path))
    computed = compute_asset_id(obj)
    claimed = obj.get("asset_id", "")
    ok = "✅" if computed == claimed else "❌"
    if computed == claimed:
        total_ok += 1
    else:
        total_fail += 1
    print(f"{ok} {obj.get('type', '?'):14s} {obj.get('id', '?'):50s}")

print(f"\n=== {total_ok} ok, {total_fail} fail ===")
sys.exit(0 if total_fail == 0 else 1)
