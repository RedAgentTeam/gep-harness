"""Test verify_assets — verify all plan/ assets via canonicalize."""

import sys
sys.path.insert(0, "/data/disk/gep-harness/openclaw-harness/bin")

from canonicalize import compute_asset_id, verify_asset_id


def test_compute_asset_id_excludes_self():
    """compute_asset_id 排除 asset_id 自身（避免循环依赖）。"""
    obj = {"id": "test", "asset_id": "sha256:placeholder", "name": "foo"}
    aid = compute_asset_id(obj)
    assert aid != "sha256:placeholder"
    assert aid.startswith("sha256:")


def test_compute_asset_id_deterministic():
    """同样输入 → 同样输出（sha256 确定性）。"""
    obj = {"id": "test", "name": "foo", "value": 42}
    a1 = compute_asset_id(obj)
    a2 = compute_asset_id(obj)
    assert a1 == a2


def test_verify_asset_id_valid():
    """verify_asset_id 与 compute_asset_id 一致（返回 bool）。"""
    obj = {"id": "test_verify", "name": "bar"}
    expected_aid = compute_asset_id(obj)
    obj["asset_id"] = expected_aid
    ok = verify_asset_id(obj)
    assert ok is True


def test_verify_asset_id_mismatch():
    """asset_id 不匹配 → ok=False（返回 bool）。"""
    obj = {"id": "test_mismatch", "name": "baz", "asset_id": "sha256:wrong_value_xyz"}
    ok = verify_asset_id(obj)
    assert ok is False