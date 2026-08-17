"""Test extract_candidate_genes.py — Signal→Candidate 转换。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def test_import_extract_candidate_genes():
    """extract_candidate_genes.py 可 import（不直接执行）。"""
    import extract_candidate_genes as ecg
    assert ecg.SCHEMA_VERSION == "1.12.1"
    assert "repair" in ecg.VALID_CATEGORIES
    assert "optimize" in ecg.VALID_CATEGORIES
    assert "innovate" in ecg.VALID_CATEGORIES
    assert "explore" in ecg.VALID_CATEGORIES


def test_infer_category_dangerous_high_freq():
    """危险工具 + 高频 → repair。"""
    from extract_candidate_genes import infer_category
    assert infer_category("exec", 10, []) == "repair"
    assert infer_category("write", 5, []) == "repair"
    assert infer_category("edit", 100, []) == "repair"
    assert infer_category("apply_patch", 50, []) == "repair"


def test_infer_category_dangerous_low_freq():
    """危险工具 + 低频 → optimize。"""
    from extract_candidate_genes import infer_category
    assert infer_category("exec", 3, []) == "optimize"
    assert infer_category("write", 1, []) == "optimize"


def test_infer_category_read_only():
    """只读工具 → optimize。"""
    from extract_candidate_genes import infer_category
    assert infer_category("read", 100, []) == "optimize"
    assert infer_category("web_fetch", 50, []) == "optimize"
    assert infer_category("wiki_search", 200, []) == "optimize"


def test_infer_category_high_count_other():
    """其他工具 + 极高频（>=10）→ repair。"""
    from extract_candidate_genes import infer_category
    assert infer_category("subagents", 15, []) == "repair"


def test_infer_category_low_count_other():
    """其他工具 + 低频 → optimize。"""
    from extract_candidate_genes import infer_category
    assert infer_category("subagents", 3, []) == "optimize"


def test_infer_strategy_exec():
    """exec 工具 → 3 concrete steps。"""
    from extract_candidate_genes import infer_strategy
    s = infer_strategy("exec", [])
    assert isinstance(s, list)
    assert len(s) == 3
    assert all(isinstance(x, str) for x in s)


def test_infer_strategy_unknown_tool():
    """未知工具 → fallback 通用 3 steps。"""
    from extract_candidate_genes import infer_strategy
    s = infer_strategy("unknown_tool_xyz", [])
    assert len(s) == 3
    assert all(isinstance(x, str) for x in s)


def test_infer_strategy_arg_keys_present():
    """infer_strategy 接受 arg_keys 参数（即使未使用）。"""
    from extract_candidate_genes import infer_strategy
    s = infer_strategy("exec", ["arg1", "arg2"])
    assert len(s) == 3


def test_infer_evidence_returns_5_strings():
    """infer_evidence → 5 strings（每库一条）。"""
    from extract_candidate_genes import infer_evidence
    ev = infer_evidence("exec")
    assert isinstance(ev, list)
    assert len(ev) == 5
    assert all(isinstance(x, str) for x in ev)


def test_infer_evidence_per_tool_differs():
    """不同工具的 evidence 应不同（或至少有内容）。"""
    from extract_candidate_genes import infer_evidence
    ev1 = infer_evidence("exec")
    ev2 = infer_evidence("read")
    assert len(ev1) == 5
    assert len(ev2) == 5


def test_make_candidate_structure():
    """make_candidate → 完整 Gene JSON 字段。"""
    from extract_candidate_genes import make_candidate
    cand = make_candidate("exec", 10, ["cmd"])
    assert cand["type"] == "Gene"
    assert cand["schema_version"] == "1.12.1"
    assert "id" in cand
    assert cand["category"] in ("repair", "optimize", "innovate", "explore")
    assert "signals_match" in cand
    assert isinstance(cand["signals_match"], list)
    assert "preconditions" in cand
    assert "strategy" in cand
    assert len(cand["strategy"]) >= 1
    assert "constraints" in cand
    assert "validation" in cand
    assert "summary" in cand
    assert "cross_library_evidence" in cand
    assert len(cand["cross_library_evidence"]) == 5
    assert "asset_id" in cand
    assert cand["asset_id"].startswith("sha256:")  # placeholder


def test_make_candidate_id_includes_tool_name():
    """make_candidate id 包含 tool name。"""
    from extract_candidate_genes import make_candidate
    cand = make_candidate("subagents", 8, [])
    assert "subagents" in cand["id"]


def test_main_writes_files(tmp_path):
    """main() 写 candidate 文件到 output dir。"""
    # 创建 scan.json 输入
    scan = {"by_tool": {"exec": 10, "read": 5}, "arg_keys_by_tool": {"exec": ["cmd"]}}
    scan_file = tmp_path / "scan.json"
    scan_file.write_text(json.dumps(scan))
    out_dir = tmp_path / "staging"

    result = subprocess.run(
        ["python3", str(REPO / "scripts/extract_candidate_genes.py"),
         "--scan-output", str(scan_file), "--output", str(out_dir), "--threshold", "5"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    files = list(out_dir.glob("gene_candidate_*.json"))
    assert len(files) == 2  # exec(10) + read(5) 满足 threshold=5


def test_main_threshold_filters_low_freq(tmp_path):
    """main() --threshold 过滤低频工具。"""
    scan = {"by_tool": {"exec": 10, "rare_tool": 1}, "arg_keys_by_tool": {}}
    scan_file = tmp_path / "scan.json"
    scan_file.write_text(json.dumps(scan))
    out_dir = tmp_path / "staging2"

    result = subprocess.run(
        ["python3", str(REPO / "scripts/extract_candidate_genes.py"),
         "--scan-output", str(scan_file), "--output", str(out_dir), "--threshold", "5"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    files = list(out_dir.glob("gene_candidate_*.json"))
    assert len(files) == 1  # 只 exec 通过


def test_main_missing_args_fails():
    """main() 缺 --scan-output / --output → argparse 错误。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/extract_candidate_genes.py")],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0


def test_main_creates_output_dir(tmp_path):
    """main() 创建不存在的 output 目录。"""
    scan = {"by_tool": {"exec": 5}, "arg_keys_by_tool": {}}
    scan_file = tmp_path / "scan.json"
    scan_file.write_text(json.dumps(scan))
    out_dir = tmp_path / "deeply" / "nested" / "staging"
    assert not out_dir.exists()

    result = subprocess.run(
        ["python3", str(REPO / "scripts/extract_candidate_genes.py"),
         "--scan-output", str(scan_file), "--output", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert out_dir.exists()
