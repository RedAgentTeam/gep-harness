"""GEP v1.12.1 compatible canonicalize + computeAssetId + verifyAssetId.

References:
  - @evomap/gep-sdk 1.12.1 (Apache-2.0)
  - /root/.openclaw/workspace/devagent/plan-gep-harness/factory.py

Field-tested: produced 6 strict-validated assets on 2026-08-14.
"""
import json, hashlib

SCHEMA_VERSION = "1.12.1"


def canonicalize(obj):
    if obj is None:
        return 'null'
    if isinstance(obj, bool):
        return 'true' if obj else 'false'
    if isinstance(obj, (int, float)):
        if isinstance(obj, float):
            import math
            if not math.isfinite(obj):
                return 'null'
        return str(obj)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, list):
        return '[' + ','.join(canonicalize(x) for x in obj) + ']'
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        return '{' + ','.join(
            json.dumps(k, ensure_ascii=False) + ':' + canonicalize(obj[k])
            for k in keys
        ) + '}'
    return 'null'


def compute_asset_id(obj, exclude_fields=("asset_id",)):
    if not isinstance(obj, dict):
        return None
    clean = {k: v for k, v in obj.items() if k not in exclude_fields}
    h = hashlib.sha256(canonicalize(clean).encode('utf-8')).hexdigest()
    return 'sha256:' + h


def verify_asset_id(obj):
    if not isinstance(obj, dict):
        return False
    claimed = obj.get('asset_id')
    if not isinstance(claimed, str):
        return False
    return claimed == compute_asset_id(obj)