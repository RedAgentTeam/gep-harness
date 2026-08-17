"""Test validate_gep.py main() in-process (覆盖率补全)。

补 70%→100%: missing lines 95-117 + 121
- main() 的 argparse + glob + 循环 + sys.exit
- if __name__ == "__main__": main()
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "openclaw-harness/bin"))

import validate_gep as vg


def _make_valid_gene(gid: str = "g_test") -> dict:
    from canonicalize import compute_asset_id, SCHEMA_VERSION
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


def test_main_in_process_ok(tmp_path):
    """main() in-process: 合法 Gene → exit 0。"""
    g = _make_valid_gene()
    p = tmp_path / "ok.json"
    p.write_text(json.dumps(g))
    with patch.object(sys, "argv", ["vg.py", "--input", str(p)]):
        try:
            vg.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 0


def test_main_in_process_fail(tmp_path):
    """main() in-process: 未知 type → exit 1。"""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"type": "Unknown"}))
    with patch.object(sys, "argv", ["vg.py", "--input", str(bad)]):
        try:
            vg.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 1


def test_main_in_process_multiple_files(tmp_path):
    """main() in-process: 多文件批量校验。"""
    g1 = _make_valid_gene("g1")
    g2 = _make_valid_gene("g2")
    (tmp_path / "g1.json").write_text(json.dumps(g1))
    (tmp_path / "g2.json").write_text(json.dumps(g2))
    with patch.object(sys, "argv", [
        "vg.py", "--mode=strict",
        "--input", str(tmp_path / "g1.json"), str(tmp_path / "g2.json")
    ]):
        try:
            vg.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 0


def test_main_in_process_glob_pattern(tmp_path):
    """main() in-process: --input='*.json' 用 glob 展开。"""
    g = _make_valid_gene()
    (tmp_path / "test.json").write_text(json.dumps(g))
    (tmp_path / "other.json").write_text(json.dumps(g))
    with patch.object(sys, "argv", [
        "vg.py", "--input", str(tmp_path / "*.json")
    ]):
        try:
            vg.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 0


def test_main_in_process_prints_summary(capsys, tmp_path):
    """main() in-process: 输出 summary。"""
    g1 = _make_valid_gene("ok1")
    g2 = _make_valid_gene("ok2")
    (tmp_path / "ok1.json").write_text(json.dumps(g1))
    (tmp_path / "ok2.json").write_text(json.dumps(g2))
    with patch.object(sys, "argv", [
        "vg.py", "--input", str(tmp_path / "ok1.json"), str(tmp_path / "ok2.json")
    ]):
        try:
            vg.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "2 ok, 0 fail" in captured.out


def test_main_in_process_loose_mode(tmp_path):
    """main() in-process: --mode=loose 也工作。"""
    g = _make_valid_gene()
    p = tmp_path / "ok.json"
    p.write_text(json.dumps(g))
    with patch.object(sys, "argv", [
        "vg.py", "--mode=loose", "--input", str(p)
    ]):
        try:
            vg.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 0


def test_main_in_process_no_files(capsys, tmp_path):
    """main() in-process: --input='nonexistent/*.json' → 0 ok, 0 fail + exit 0。"""
    with patch.object(sys, "argv", [
        "vg.py", "--input", str(tmp_path / "*.json")
    ]):
        try:
            vg.main()
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code
    assert exit_code == 0


def test_main_in_process_prints_errors(capsys, tmp_path):
    """main() in-process: fail 文件打印错误行。"""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"type": "Unknown"}))
    with patch.object(sys, "argv", ["vg.py", "--input", str(bad)]):
        try:
            vg.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "unknown type" in captured.out


def test_main_module_runs():
    """if __name__ == '__main__': main() → 直接执行也能跑。"""
    # 通过 subprocess 跑 --help 验证模块可执行
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/validate_gep.py"), "--help"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "--mode" in result.stdout
    assert "--input" in result.stdout