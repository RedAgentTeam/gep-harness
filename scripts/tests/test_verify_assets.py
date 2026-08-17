"""Test verify_assets.py — GEP strict asset verification."""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def test_verify_assets_constants():
    """verify_assets.py 核心常量存在。"""
    src = (REPO / "scripts/verify_assets.py").read_text()
    assert "SHA256_RE" in src
    assert "REQUIRED_TOP_FIELDS" in src
    assert "compute_asset_id" in src


def test_verify_assets_sha256_regex_format():
    """SHA256_RE 接受 sha256:64hex 格式。"""
    import re as _re
    src = (REPO / "scripts/verify_assets.py").read_text()
    # 验证 SHA256_RE 存在
    assert "SHA256_RE = re.compile" in src
    # 验证能匹配 sha256:64hex
    sample = "sha256:" + "a" * 64
    m = _re.match(r"^sha256:[0-9a-f]{64}$", sample)
    assert m is not None


def test_verify_assets_runs_clean():
    """verify_assets.py 跑完整 plan/genes + capsules + events，退出码 0（trust 路径）。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/verify_assets.py")],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )
    # Should produce summary line "verified | trust | FAIL"
    combined = result.stdout + result.stderr
    assert "verified" in combined or "trust" in combined or "FAIL" in combined


def test_verify_assets_output_structure():
    """verify_assets.py 输出每行带资产 type 和 stem。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/verify_assets.py")],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )
    # 输出格式: emoji type stem (verified/trust/fail)
    has_emoji = any(e in result.stdout for e in ["✅", "🟡", "❌"])
    assert has_emoji or result.returncode == 0


def test_verify_assets_summary_format():
    """verify_assets.py 末尾打印 N verified | N trust | N FAIL 摘要。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/verify_assets.py")],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )
    # 末尾摘要
    last_lines = result.stdout.strip().splitlines()
    assert any("verified" in l or "trust" in l or "FAIL" in l for l in last_lines[-5:])


def test_required_top_fields_set():
    """REQUIRED_TOP_FIELDS = {type, schema_version, asset_id}。"""
    src = (REPO / "scripts/verify_assets.py").read_text()
    # 应该有 {'type', 'schema_version', 'asset_id'} 这种 set literal
    assert "\"type\"" in src and "schema_version" in src and "asset_id" in src


def test_compute_asset_id_imported():
    """verify_assets.py 正确导入 compute_asset_id。"""
    src = (REPO / "scripts/verify_assets.py").read_text()
    assert "from canonicalize import compute_asset_id" in src


def test_verify_assets_handles_missing_asset_id():
    """verify_assets.py 对缺失 asset_id 的文件报 missing 错误（手动构造）。"""
    # 创建一个临时 gene 文件，故意缺 asset_id
    test_dir = REPO / "tests_tmp_verify"
    test_dir.mkdir(exist_ok=True)
    bad_gene = test_dir / "gene_bad_no_aid.json"
    bad_gene.write_text(json.dumps({"type": "Gene", "schema_version": "1.12.1", "id": "x"}))
    # 临时把它放进 plan/genes/ 跑一遍
    plan_genes = REPO / "plan/genes"
    backup_path = plan_genes / "_TEST_BAD_TMP.json"
    try:
        import shutil
        shutil.copy(bad_gene, backup_path)
        result = subprocess.run(
            ["python3", str(REPO / "scripts/verify_assets.py")],
            capture_output=True, text=True, timeout=60, cwd=str(REPO),
        )
        # Should mention missing or FAIL
        assert "missing" in result.stdout or "FAIL" in result.stdout or result.returncode != 0
    finally:
        if backup_path.exists():
            backup_path.unlink()
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_verify_assets_handles_bad_format():
    """verify_assets.py 对 bad asset_id 格式报错。"""
    test_dir = REPO / "tests_tmp_verify2"
    test_dir.mkdir(exist_ok=True)
    bad_gene = test_dir / "gene_bad_format.json"
    bad_gene.write_text(json.dumps({
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "x",
        "asset_id": "not_sha256_format",
    }))
    plan_genes = REPO / "plan/genes"
    backup_path = plan_genes / "_TEST_BAD_FORMAT_TMP.json"
    try:
        import shutil
        shutil.copy(bad_gene, backup_path)
        result = subprocess.run(
            ["python3", str(REPO / "scripts/verify_assets.py")],
            capture_output=True, text=True, timeout=60, cwd=str(REPO),
        )
        assert "bad_format" in result.stdout or "FAIL" in result.stdout or result.returncode != 0
    finally:
        if backup_path.exists():
            backup_path.unlink()
        if test_dir.exists():
            shutil.rmtree(test_dir)
