"""Test llm_fill_gene.py main() CLI + fill_gene 边界分支 (46%→100%)。

补 missing lines: 93-95, 97, 105, 125-186, 190
- 93-97: call_stepfun 边界 + markdown fence strip
- 105: empty response → ValueError
- 109-115: JSON parse fail → regex 提取 fallback
- 125-186: main() argparse + --candidate + --staging + --dry-run + manifest sidecar
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import llm_fill_gene as lfg


def test_fill_gene_strips_markdown_fences_json():
    """fill_gene: LLM 返回 ```json ... ``` → strip。"""
    gene_in = {
        "type": "Gene", "id": "fence",
        "signals_match": ["x"], "summary": "y",
        "category": "", "strategy": [],
    }
    fenced = "```json\n" + json.dumps({"category": "repair", "strategy": ["a"]}) + "\n```"
    with patch.object(lfg, "call_stepfun", return_value=fenced):
        out = lfg.fill_gene(gene_in)
    assert out["category"] == "repair"
    assert out["strategy"] == ["a"]


def test_fill_gene_strips_no_lang_fence():
    """fill_gene: LLM 返回 ```...``` (无 json 标签) → strip。"""
    gene_in = {
        "type": "Gene", "id": "nofence",
        "signals_match": ["x"], "summary": "y",
        "category": "", "strategy": [],
    }
    fenced = "```\n" + json.dumps({"category": "optimize"}) + "\n```"
    with patch.object(lfg, "call_stepfun", return_value=fenced):
        out = lfg.fill_gene(gene_in)
    assert out["category"] == "optimize"


def test_fill_gene_empty_response_raises():
    """fill_gene: LLM 返回空 → ValueError('LLM returned empty response')。"""
    gene_in = {"type": "Gene", "id": "empty", "signals_match": ["x"], "summary": "y"}
    with patch.object(lfg, "call_stepfun", return_value=""):
        try:
            lfg.fill_gene(gene_in)
            raised = False
        except ValueError as e:
            raised = True
            assert "empty response" in str(e)
    assert raised


def test_fill_gene_non_json_raises():
    """fill_gene: LLM 返回非 JSON + 无 {...} 块 → ValueError。"""
    gene_in = {"type": "Gene", "id": "bad", "signals_match": ["x"], "summary": "y"}
    with patch.object(lfg, "call_stepfun", return_value="just text no json here"):
        try:
            lfg.fill_gene(gene_in)
            raised = False
        except ValueError as e:
            raised = True
            assert "non-JSON" in str(e)
    assert raised


def test_fill_gene_garbage_json_with_object_fallback():
    """fill_gene: JSON 解析失败但文本含 {...} → regex fallback。"""
    gene_in = {
        "type": "Gene", "id": "fb",
        "signals_match": ["x"], "summary": "y",
        "category": "", "strategy": [],
    }
    bad_json = 'preamble {"category": "explore", "strategy": ["b"]} trailing garbage not json'
    with patch.object(lfg, "call_stepfun", return_value=bad_json):
        out = lfg.fill_gene(gene_in)
    assert out["category"] == "explore"


def test_fill_gene_protects_protected_fields():
    """fill_gene: PROTECTED 字段 (id, signals_match, ...) 不被覆盖。"""
    gene_in = {
        "type": "Gene", "id": "protect",
        "signals_match": ["original"], "summary": "original_summary",
        "category": "", "strategy": [],
        "constraints": ["c1"], "validation": {"check": "ok"},
    }
    llm_out = {
        "id": "HACKED_BY_LLM",
        "signals_match": ["HACKED"],
        "summary": "HACKED summary",
        "category": "repair",
        "constraints": ["HACKED constraint"],
        "validation": {"check": "HACKED"},
        "strategy": ["new strategy"],
    }
    with patch.object(lfg, "call_stepfun", return_value=json.dumps(llm_out)):
        out = lfg.fill_gene(gene_in)
    # protected 不变
    assert out["id"] == "protect"
    assert out["signals_match"] == ["original"]
    assert out["summary"] == "original_summary"
    assert out["constraints"] == ["c1"]
    assert out["validation"] == {"check": "ok"}
    # 非 protected 被覆盖
    assert out["strategy"] == ["new strategy"]


def test_fill_file():
    """fill_file: 读 JSON 文件 → fill_gene。"""
    gene = {"type": "Gene", "id": "ff", "signals_match": ["x"], "summary": "y",
            "category": "", "strategy": []}
    p = Path("/tmp/__test_ff.json")
    p.write_text(json.dumps(gene))
    with patch.object(lfg, "call_stepfun", return_value=json.dumps({"category": "repair"})):
        out = lfg.fill_file(p)
    p.unlink(missing_ok=True)
    assert out["category"] == "repair"


def test_main_no_args_errors():
    """main: 没 --candidate/--staging → argparse error。"""
    with patch.object(sys, "argv", ["lfg.py"]):
        try:
            lfg.main()
            raised = False
        except SystemExit:
            raised = True
    assert raised


def test_main_candidate_dry_run(tmp_path, capsys):
    """main --candidate=path --dry-run → 打印但不调 API。"""
    gene = {"type": "Gene", "id": "cand_dr", "signals_match": ["x"], "summary": "y"}
    p = tmp_path / "cand_dr.json"
    p.write_text(json.dumps(gene))
    with patch.object(sys, "argv", ["lfg.py", "--candidate", str(p), "--dry-run"]):
        try:
            lfg.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


def test_main_candidate_real_fill(tmp_path, capsys):
    """main --candidate=path 真 fill → 写盘 + 打印 After。"""
    gene = {"type": "Gene", "id": "cand_real", "signals_match": ["x"], "summary": "y",
            "category": "", "strategy": []}
    p = tmp_path / "cand_real.json"
    p.write_text(json.dumps(gene))
    with patch.object(sys, "argv", ["lfg.py", "--candidate", str(p)]):
        with patch.object(lfg, "call_stepfun",
                          return_value=json.dumps({"category": "repair", "strategy": ["s"]})):
            try:
                lfg.main()
            except SystemExit:
                pass
    out = json.loads(p.read_text())
    assert out["category"] == "repair"


def test_main_staging_empty(capsys, tmp_path):
    """main --staging=empty → 0/0 + manifest 创建。"""
    staging = tmp_path / "empty_staging"
    staging.mkdir()
    with patch.object(sys, "argv", ["lfg.py", "--staging", str(staging)]):
        try:
            lfg.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "0/" in captured.out
    assert (staging / "llm_filled_manifest.json").exists()


def test_main_staging_skip_already_filled(tmp_path, capsys):
    """main --staging: 已在 manifest → skip。"""
    staging = tmp_path / "skip_staging"
    staging.mkdir()
    gene = {"type": "Gene", "id": "skip_me", "signals_match": ["x"], "summary": "y"}
    (staging / "gene_candidate_skip_me.json").write_text(json.dumps(gene))
    # 写 manifest 标记已填
    manifest = staging / "llm_filled_manifest.json"
    manifest.write_text(json.dumps({"filled": ["gene_candidate_skip_me.json"],
                                     "schema_version": "1.12.1"}))
    with patch.object(sys, "argv", ["lfg.py", "--staging", str(staging)]):
        try:
            lfg.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "already filled" in captured.out


def test_main_staging_dry_run(tmp_path, capsys):
    """main --staging --dry-run → 打印 dry-run 不调 API。"""
    staging = tmp_path / "dr_staging"
    staging.mkdir()
    gene = {"type": "Gene", "id": "dr1", "signals_match": ["x"], "summary": "y",
            "category": "", "strategy": []}
    (staging / "gene_candidate_dr1.json").write_text(json.dumps(gene))
    with patch.object(sys, "argv", ["lfg.py", "--staging", str(staging), "--dry-run"]):
        try:
            lfg.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "dry-run" in captured.out
    # manifest 应被写, 但 filled=[] (没真 fill)
    manifest = json.loads((staging / "llm_filled_manifest.json").read_text())
    assert manifest["filled"] == []


def test_main_staging_real_fill(tmp_path, capsys):
    """main --staging: 真 fill 多个 candidate。"""
    staging = tmp_path / "real_staging"
    staging.mkdir()
    for i in range(2):
        gene = {"type": "Gene", "id": f"r{i}", "signals_match": ["x"], "summary": "y",
                "category": "", "strategy": []}
        (staging / f"gene_candidate_r{i}.json").write_text(json.dumps(gene))
    with patch.object(sys, "argv", ["lfg.py", "--staging", str(staging)]):
        with patch.object(lfg, "call_stepfun",
                          return_value=json.dumps({"category": "repair"})):
            try:
                lfg.main()
            except SystemExit:
                pass
    captured = capsys.readouterr()
    assert "2/2" in captured.out
    manifest = json.loads((staging / "llm_filled_manifest.json").read_text())
    assert "gene_candidate_r0.json" in manifest["filled"]
    assert "gene_candidate_r1.json" in manifest["filled"]


def test_main_staging_fill_error_continues(tmp_path, capsys):
    """main --staging: 某个 fill 失败 → continue, 不阻塞其他。"""
    staging = tmp_path / "err_staging"
    staging.mkdir()
    gene = {"type": "Gene", "id": "err1", "signals_match": ["x"], "summary": "y"}
    (staging / "gene_candidate_err1.json").write_text(json.dumps(gene))
    with patch.object(sys, "argv", ["lfg.py", "--staging", str(staging)]):
        with patch.object(lfg, "call_stepfun", side_effect=Exception("API down")):
            try:
                lfg.main()
            except SystemExit:
                pass
    captured = capsys.readouterr()
    assert "API down" in captured.out or "❌" in captured.out


def test_main_staging_custom_output(tmp_path, capsys):
    """main --staging=X --output=Y → 写到 Y 目录, manifest 也写到 Y。"""
    staging = tmp_path / "in"
    output = tmp_path / "out"
    staging.mkdir()
    output.mkdir()
    gene = {"type": "Gene", "id": "co", "signals_match": ["x"], "summary": "y",
            "category": "", "strategy": []}
    (staging / "gene_candidate_co.json").write_text(json.dumps(gene))
    with patch.object(sys, "argv", [
        "lfg.py", "--staging", str(staging), "--output", str(output),
    ]):
        with patch.object(lfg, "call_stepfun",
                          return_value=json.dumps({"category": "repair"})):
            try:
                lfg.main()
            except SystemExit:
                pass
    assert (output / "gene_candidate_co.json").exists()
    assert (output / "llm_filled_manifest.json").exists()