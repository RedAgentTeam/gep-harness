"""Test validate_gep.py 剩余 validate_one() 错误分支 + main() CLI。

补 68%→100%：missing lines 76, 95-117, 121
- line 76: validate_one JSON decode error 分支
- line 95-117: type-specific 校验 (Gene category, signals_match, Mutation risk_level)
- line 121: main() CLI (strict/loose mode)
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "openclaw-harness/bin"))

import validate_gep as vg
from canonicalize import compute_asset_id, SCHEMA_VERSION


def _make_valid_gene(gid: str = "g_test") -> dict:
    g = {
        "type": "Gene",
        "schema_version": SCHEMA_VERSION,
        "id": gid,
        "signals_match": ["x"],
        "summary": "y",
        "category": "repair",
        "strategy": ["a", "b", "c"],
        "constraints": ["c1"],
        "validation": {"check": "ok"},
    }
    g["asset_id"] = compute_asset_id(g)
    return g


def test_validate_one_json_decode_error(tmp_path):
    """validate_one: 无效 JSON → (False, ['JSON decode error: ...'])"""
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid json")
    ok, errors = vg.validate_one(str(bad))
    assert ok is False
    assert any("JSON decode" in e for e in errors)


def test_validate_one_unknown_type(tmp_path):
    """validate_one: 未知 type → fail。"""
    bad = tmp_path / "unknown.json"
    bad.write_text(json.dumps({"type": "UnknownThing"}))
    ok, errors = vg.validate_one(str(bad))
    assert ok is False
    assert any("unknown type" in e for e in errors)


def test_validate_one_wrong_schema_version(tmp_path):
    """validate_one: schema_version != 当前 → 报错但不阻塞 ok。"""
    g = _make_valid_gene()
    g["schema_version"] = "0.0.1"  # 不匹配
    bad = tmp_path / "wrong_ver.json"
    bad.write_text(json.dumps(g))
    ok, errors = vg.validate_one(str(bad))
    # schema_version 错误是 errors,但其他字段 ok → 整体 False
    assert any("schema_version" in e for e in errors)


def test_validate_one_invalid_gene_category(tmp_path):
    """validate_one: Gene category 非法值 → fail。"""
    g = _make_valid_gene()
    g["category"] = "invalid_category_xyz"
    # 重算 asset_id 因为 category 改了
    g["asset_id"] = compute_asset_id(g)
    p = tmp_path / "bad_cat.json"
    p.write_text(json.dumps(g))
    ok, errors = vg.validate_one(str(p))
    assert ok is False
    assert any("invalid category" in e for e in errors)


def test_validate_one_signals_match_not_list(tmp_path):
    """validate_one: signals_match 不是 list → fail。"""
    g = _make_valid_gene()
    g["signals_match"] = "should_be_list_not_string"
    g["asset_id"] = compute_asset_id(g)
    p = tmp_path / "bad_signals.json"
    p.write_text(json.dumps(g))
    ok, errors = vg.validate_one(str(p))
    assert ok is False
    assert any("signals_match must be a list" in e for e in errors)


def test_validate_one_mutation_invalid_risk_level(tmp_path):
    """validate_one: Mutation risk_level 非法 → fail。"""
    m = {
        "type": "Mutation",
        "schema_version": SCHEMA_VERSION,
        "id": "mut_x",
        "category": "repair",
        "trigger_signals": ["x"],
        "target": "y",
        "expected_effect": "z",
        "risk_level": "extreme",  # 非法
        "asset_id": "sha256:" + "a" * 64,
    }
    p = tmp_path / "bad_mut.json"
    p.write_text(json.dumps(m))
    ok, errors = vg.validate_one(str(p))
    assert ok is False
    assert any("risk_level" in e for e in errors)


def test_validate_one_mutation_invalid_intent(tmp_path):
    """validate_one: Mutation category/intent 非法 → fail。"""
    m = {
        "type": "Mutation",
        "schema_version": SCHEMA_VERSION,
        "id": "mut_y",
        "category": "invalid_intent",
        "trigger_signals": ["x"],
        "target": "y",
        "expected_effect": "z",
        "risk_level": "low",
        "asset_id": "sha256:" + "b" * 64,
    }
    p = tmp_path / "bad_mut_intent.json"
    p.write_text(json.dumps(m))
    ok, errors = vg.validate_one(str(p))
    assert ok is False
    assert any("category/intent" in e or "invalid category" in e for e in errors)


def test_validate_one_asset_id_mismatch(tmp_path):
    """validate_one: asset_id 与 compute_asset_id 不一致 → fail。"""
    g = _make_valid_gene()
    g["asset_id"] = "sha256:" + "0" * 64  # 错误 hash
    p = tmp_path / "mismatch.json"
    p.write_text(json.dumps(g))
    ok, errors = vg.validate_one(str(p))
    assert ok is False
    assert any("asset_id mismatch" in e for e in errors)


def test_validate_one_asset_id_placeholder_allowed(tmp_path):
    """validate_one: asset_id 是 PLACEHOLDER → 不做 hash 校验。"""
    g = _make_valid_gene()
    g["asset_id"] = "sha256:PLACEHOLDER_LLM_TO_FILL"
    p = tmp_path / "placeholder.json"
    p.write_text(json.dumps(g))
    ok, errors = vg.validate_one(str(p))
    # placeholder 跳过 hash 校验,其他字段对 → ok
    # 但缺必需字段(如 strategy)会 fail
    # 这里 _make_valid_gene 给齐了所有必需字段,应 ok
    assert ok is True, f"errors: {errors}"


def test_validate_one_ok(tmp_path):
    """validate_one: 完整合法 Gene → ok。"""
    g = _make_valid_gene()
    p = tmp_path / "good.json"
    p.write_text(json.dumps(g))
    ok, errors = vg.validate_one(str(p))
    assert ok is True
    assert errors == []


def test_validate_one_evolution_event(tmp_path):
    """validate_one: EvolutionEvent 合法 → ok。"""
    evt = {
        "type": "EvolutionEvent",
        "schema_version": SCHEMA_VERSION,
        "id": "evt_x",
        "intent": "repair",
        "signals": ["s1"],
        "genes_used": ["g1"],
        "mutation_id": "mut_x",
        "blast_radius": {"files": 1, "lines": 10},
        "outcome": {"status": "success", "score": 0.8},
        "source_type": "test",
        "asset_id": "",
    }
    evt["asset_id"] = compute_asset_id(evt)
    p = tmp_path / "evt.json"
    p.write_text(json.dumps(evt))
    ok, errors = vg.validate_one(str(p))
    assert ok is True, f"errors: {errors}"


def test_main_strict_ok(tmp_path):
    """main --mode=strict --input=ok.json → exit 0。"""
    g = _make_valid_gene()
    p = tmp_path / "ok.json"
    p.write_text(json.dumps(g))
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/validate_gep.py"),
         "--mode=strict", "--input", str(p)],
        capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0
    assert "1 ok, 0 fail" in result.stdout or "ok" in result.stdout


def test_main_strict_fail(tmp_path):
    """main --mode=strict --input=bad.json → exit 1。"""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"type": "Unknown"}))
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/validate_gep.py"),
         "--mode=strict", "--input", str(p)],
        capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 1
    assert "fail" in result.stdout


def test_main_glob_input(tmp_path):
    """main --input=*.json: 多个文件批量。"""
    g1 = _make_valid_gene("g1")
    g2 = _make_valid_gene("g2")
    (tmp_path / "g1.json").write_text(json.dumps(g1))
    (tmp_path / "g2.json").write_text(json.dumps(g2))
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/validate_gep.py"),
         "--mode=strict", "--input", str(tmp_path / "*.json")],
        capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0
    assert "2 ok" in result.stdout or result.stdout.count("✅") == 2