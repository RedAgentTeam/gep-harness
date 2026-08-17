"""Test verify_assets.py 重构后的单元测试。

verify_assets.py 已 refactor: 提取 validate_asset(obj) + run_verify(plan_dirs) 函数。
测 5 件事:
1. validate_asset() 三种返回值 (ok/trust/fail)
2. validate_asset() 缺字段 / 格式错误 / hash mismatch → fail
3. validate_asset() 不可变 obj（不会污染）
4. run_verify() 返回 (ok, trust, fail) 元组
5. CLI exit code 一致
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "openclaw-harness/bin"))

import verify_assets as va
from canonicalize import compute_asset_id


def _make_valid_gene() -> dict:
    """构造一个 GEP strict 合法的 Gene。"""
    g = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_g",
        "signals_match": ["x"],
        "summary": "y",
        "category": "repair",
        "strategy": ["a", "b", "c"],
        "constraints": ["c1"],
        "validation": {"check": "ok"},
        "asset_id": "",
    }
    g["asset_id"] = compute_asset_id(g)
    return g


def test_validate_asset_ok():
    """validate_asset: asset_id 重算一致 → 'ok'。"""
    g = _make_valid_gene()
    assert va.validate_asset(g) == "ok"


def test_validate_asset_missing_fields():
    """validate_asset: 缺必需字段 → 'fail'。"""
    g = {"type": "Gene", "id": "x"}  # 缺 schema_version, asset_id
    assert va.validate_asset(g) == "fail"


def test_validate_asset_bad_format():
    """validate_asset: asset_id 格式错（短） → 'fail'。"""
    g = _make_valid_gene()
    g["asset_id"] = "sha256:short"
    assert va.validate_asset(g) == "fail"


def test_validate_asset_bad_format_no_prefix():
    """validate_asset: asset_id 无 sha256: 前缀且不是 64 hex → 'fail'。"""
    g = _make_valid_gene()
    g["asset_id"] = "PLACEHOLDER_LLM_TO_FILL"
    assert va.validate_asset(g) == "fail"


def test_validate_asset_hash_mismatch_trust():
    """validate_asset: hash mismatch (历史资产) → 'trust'。"""
    g = _make_valid_gene()
    g["asset_id"] = "sha256:" + "a" * 64  # 错误的 asset_id
    # 不传 _rel_path,validate_asset 不会调 git log → 走 trust 路径
    assert va.validate_asset(g) == "trust"


def test_validate_asset_does_not_mutate_obj():
    """validate_asset 不得修改 obj (会污染 hash)。"""
    g = _make_valid_gene()
    snapshot = json.dumps(g, sort_keys=True)
    va.validate_asset(g)
    after = json.dumps(g, sort_keys=True)
    assert snapshot == after, "validate_asset mutated obj!"


def test_validate_asset_with_real_plan_gene():
    """validate_asset: 对真实 plan/genes/ 里的 Gene 返回 'ok'。"""
    genes = list((REPO / "plan/genes").glob("*.json"))[:5]
    for path in genes:
        obj = json.loads(path.read_text())
        status = va.validate_asset(obj)
        assert status in ("ok", "trust"), f"{path.name}: {status}"


def test_run_verify_returns_tuple(tmp_path):
    """run_verify: 返回 (ok, trust, fail) 计数元组。"""
    plan_dir = tmp_path / "plan"
    for sub in ["genes", "capsules", "events"]:
        (plan_dir / sub).mkdir(parents=True)
    # 写一个合法 gene
    g = _make_valid_gene()
    (plan_dir / "genes" / "ok.json").write_text(json.dumps(g))
    # 写一个 fail gene
    bad = {"type": "Gene"}  # 缺必需字段
    (plan_dir / "genes" / "bad.json").write_text(json.dumps(bad))

    ok, trust, fail = va.run_verify([plan_dir / "genes", plan_dir / "capsules", plan_dir / "events"])
    assert ok == 1
    assert fail == 1


def test_run_verify_counts_ok_and_trust(tmp_path):
    """run_verify: ok + trust 都不算 fail。"""
    plan_dir = tmp_path / "plan"
    (plan_dir / "genes").mkdir(parents=True)
    g = _make_valid_gene()
    g["asset_id"] = "sha256:" + "0" * 64  # mismatch
    (plan_dir / "genes" / "mismatch.json").write_text(json.dumps(g))

    ok, trust, fail = va.run_verify([plan_dir / "genes", plan_dir / "capsules", plan_dir / "events"])
    # mismatch → trust (因为 plan_dir 不在 git repo 内)
    assert trust == 1
    assert fail == 0


def test_cli_exit_code_clean():
    """CLI: 当前真实数据下 exit 0。"""
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/verify_assets.py")],
        capture_output=True, text=True, cwd=str(REPO), timeout=60
    )
    # 90 verified (我们之前跑过),exit 0
    assert result.returncode == 0
    assert "verified" in result.stdout


def test_validate_asset_existing_module_attributes():
    """验证 refactor 后所有原 module-level 常量还在。"""
    assert va.SHA256_RE is not None
    assert va.SHA256_HEX_RE is not None
    assert va.REQUIRED_TOP_FIELDS == {"type", "schema_version", "asset_id"}
    assert hasattr(va, "compute_asset_id")