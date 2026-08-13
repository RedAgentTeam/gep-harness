"""Tests for stage 3 evolver scripts (Scan / Signal / Validate).

3 pytest:
  1. scan_events: aggregate tool_calls correctly
  2. extract_candidate_genes: template output is GEP-compatible
  3. validate_gep: detect all required-field violations
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
SCRIPTS_DIR = Path("/data/disk/gep-harness/scripts")


def test_scan_events():
    """scan_events.py 聚类 tool_call correctly"""
    # 写一份 mock events.jsonl
    with tempfile.TemporaryDirectory() as tmp:
        events_path = Path(tmp) / "events.jsonl"
        events = [
            {"type": "SessionEvent", "schema_version": "1.12.1",
             "session_id": "s1", "kind": "tool_call_before",
             "ts": "2026-08-14T01:00:00+08:00",
             "tool_name": "read", "args": {"path": "/tmp/x"},
             "asset_id": "sha256:" + "0" * 64},
            {"type": "SessionEvent", "schema_version": "1.12.1",
             "session_id": "s1", "kind": "tool_call_before",
             "ts": "2026-08-14T01:01:00+08:00",
             "tool_name": "exec", "args": {"command": "ls"},
             "asset_id": "sha256:" + "1" * 64},
            {"type": "SessionEvent", "schema_version": "1.12.1",
             "session_id": "s1", "kind": "tool_call_before",
             "ts": "2026-08-14T01:02:00+08:00",
             "tool_name": "read", "args": {"path": "/tmp/y"},
             "asset_id": "sha256:" + "2" * 64},
        ]
        for e in events:
            events_path.write_text(
                "\n".join(json.dumps(e) for e in events) + "\n"
            )

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "scan_events.py"),
             "--input", str(events_path), "--since", "8760"],  # 1 year
            capture_output=True, text=True, check=True,
        )
        out = json.loads(result.stdout)
        assert out["total_events"] == 3
        assert out["by_tool"]["read"] == 2
        assert out["by_tool"]["exec"] == 1
        assert "path" in out["arg_keys_by_tool"]["read"]
        assert "command" in out["arg_keys_by_tool"]["exec"]


def test_extract_candidate_genes():
    """extract_candidate_genes.py 输出 GEP 兼容的候选 JSON"""
    with tempfile.TemporaryDirectory() as tmp:
        scan_out = Path(tmp) / "scan.json"
        scan_out.write_text(json.dumps({
            "total_events": 10,
            "by_tool": {"read": 5, "exec": 3, "write": 2},
            "arg_keys_by_tool": {
                "read": ["path"], "exec": ["command"], "write": ["path"]
            },
        }))
        out_dir = Path(tmp) / "staging"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "extract_candidate_genes.py"),
             "--scan-output", str(scan_out), "--output", str(out_dir),
             "--threshold", "3"],
            capture_output=True, text=True, check=True,
        )
        files = list(out_dir.glob("gene_candidate_*.json"))
        assert len(files) == 2  # read (5) and exec (3), write (2) excluded
        for f in files:
            cand = json.load(open(f))
            assert cand["type"] == "Gene"
            assert cand["schema_version"] == "1.12.1"
            assert cand["category"] in ("repair", "optimize", "innovate", "explore")
            assert isinstance(cand["signals_match"], list)
            assert "max_files" in cand["constraints"]


def test_validate_gep():
    """validate_gep.py 检测缺字段 + 假 asset_id"""
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "staging"
        staging.mkdir()

        # 故意少 required 字段 + 错的 asset_id
        bad = {
            "type": "Gene",
            "schema_version": "1.12.1",
            "id": "gene_bad",
            # 故意缺: category, signals_match, strategy, constraints, validation
            "asset_id": "sha256:WRONG",
        }
        (staging / "bad.json").write_text(json.dumps(bad))

        # 真的 valid Gene
        good = {
            "type": "Gene",
            "schema_version": "1.12.1",
            "id": "gene_good",
            "category": "optimize",
            "signals_match": ["x"],
            "strategy": ["step1"],
            "constraints": {"max_files": 1, "forbidden_paths": []},
            "validation": ["echo ok"],
            "asset_id": "sha256:PLACEHOLDER",  # 不参与校验
        }
        (staging / "good.json").write_text(json.dumps(good))

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "validate_gep.py"),
             "--mode", "strict", "--input", str(staging / "*.json")],
            capture_output=True, text=True,
        )
        out = result.stdout
        assert "1 ok" in out, f"expected 1 ok: {out}"
        assert "1 fail" in out, f"expected 1 fail: {out}"
        assert "bad.json" in out
        assert "good.json" in out
        # bad 的缺字段应被列出
        assert "missing required field" in out


if __name__ == "__main__":
    test_scan_events()
    print("✅ test_scan_events")
    test_extract_candidate_genes()
    print("✅ test_extract_candidate_genes")
    test_validate_gep()
    print("✅ test_validate_gep")
    print("\n=== all 3 tests passed ===")