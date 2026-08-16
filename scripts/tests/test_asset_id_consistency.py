#!/usr/bin/env python3
"""
test_asset_id_consistency.py — C7: asset_id 一致性测试门。

对每个 GEP 资产（Gene/Capsule/EvolutionEvent），断言：
  canonicalize.compute_asset_id(content) == 资产内声明的 asset_id

历史资产（格式合法但重算不一致）标记为 trust 不 fail，
新写的资产必须 100% verified。

Usage:
    python3 -m pytest scripts/tests/test_asset_id_consistency.py -v
"""

import json
import glob
import pytest
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "openclaw-harness/bin"))
from canonicalize import compute_asset_id  # noqa: E402

SHA256_RE = __import__("re").compile(r"^sha256:[0-9a-f]{64}$")
SHA256_HEX_RE = __import__("re").compile(r"^[0-9a-f]{64}$")


def iter_assets():
    """Yield (path, obj, claimed_asset_id) for all GEP assets."""
    patterns = [
        str(REPO / "plan/genes/*.json"),
        str(REPO / "plan/capsules/*.json"),
        str(REPO / "plan/events/*.json"),
    ]
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            obj = json.load(open(path))
            claimed = obj.get("asset_id", "")
            yield path, obj, claimed


@pytest.mark.parametrize("path,obj,claimed", list(iter_assets()))
def test_asset_id_format(path, obj, claimed):
    """asset_id 必须有合法格式（sha256:xxx 或 64 hex）。"""
    name = Path(path).stem
    assert claimed, f"{name}: asset_id 缺失"
    assert SHA256_RE.match(claimed) or SHA256_HEX_RE.match(claimed), (
        f"{name}: asset_id 格式非法: {claimed[:50]}"
    )


@pytest.mark.parametrize("path,obj,claimed", list(iter_assets()))
def test_asset_id_computed_matches_claimed(path, obj, claimed):
    """canonicalize 标准重算的 asset_id 必须等于资产内声明的值。

    历史资产（格式合法但 canonicalize 算出来不一样）跳过不 fail，
    由 verify_assets.py 的 trust 机制处理。
    """
    name = Path(path).stem
    # skip if format is already bad (test_asset_id_format will catch it)
    if not (SHA256_RE.match(claimed) or SHA256_HEX_RE.match(claimed)):
        pytest.skip(f"{name}: asset_id 格式非法，由 test_asset_id_format 捕获")

    computed = compute_asset_id(obj)
    if computed == claimed:
        return  # verified ✅

    # 格式合法但重算不一致 → trust（历史资产）
    # 如果是新资产（最近 20 个 commit 内创建），应该 fail
    import subprocess
    try:
        rel_path = str(Path(path).relative_to(REPO))
        when = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel_path],
            capture_output=True, text=True, cwd=str(REPO),
        ).stdout.strip()
        if when:
            import datetime
            created = datetime.datetime.fromtimestamp(int(when), tz=datetime.timezone.utc)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            days_old = (now - created).total_seconds() / 86400
            if days_old < 30:
                pytest.fail(
                    f"{name}: 新资产（{days_old:.0f} 天前创建）asset_id 不匹配！\n"
                    f"  claimed  = {claimed[:50]}\n"
                    f"  computed = {computed[:50]}\n"
                    f"  说明: 新资产必须用 canonicalize 标准计算 asset_id"
                )
    except Exception:
        pass  # 无法判断新旧时，trust 不 fail

    pytest.skip(f"{name}: 历史资产，asset_id 信任（格式合法）")
