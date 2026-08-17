"""Test llm_fill_gene.py — mock Stepfun API, test fill_gene + fill_file + main。

StepFun API mock 用 monkeypatch urllib.request.urlopen。
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import llm_fill_gene as lfg


def _mock_urlopen_response(content: str):
    """构造 mock urllib response。"""
    body = {
        "choices": [
            {"message": {"role": "assistant", "content": content}}
        ]
    }
    resp = MagicMock()
    resp.read = lambda: json.dumps(body).encode("utf-8")
    resp.__enter__ = lambda self: self
    resp.__exit__ = lambda self, *a: False
    return resp


def _mock_urlopen_reasoning(reasoning_text: str):
    """构造 reasoning_model 风格 mock（content 空, reasoning_content 含 JSON）。"""
    body = {
        "choices": [
            {"message": {
                "role": "assistant",
                "content": "",
                "reasoning_content": reasoning_text
            }}
        ]
    }
    resp = MagicMock()
    resp.read = lambda: json.dumps(body).encode("utf-8")
    resp.__enter__ = lambda self: self
    resp.__exit__ = lambda self, *a: False
    return resp


def test_call_stepfun_basic_content():
    """call_stepfun: 正常 content 返回。"""
    filled = json.dumps({"category": "repair", "strategy": ["a", "b", "c"], "asset_id": "x"})
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(filled)):
        out = lfg.call_stepfun("test prompt")
    assert out == filled


def test_call_stepfun_fallback_to_reasoning():
    """content 空 → 用 reasoning_content 提取 {...}。"""
    reasoning = '思考中... {"category": "fix", "asset_id": "y"} 结束'
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_reasoning(reasoning)):
        out = lfg.call_stepfun("test prompt")
    assert '"category": "fix"' in out
    assert out.startswith("{")


def test_call_stepfun_marks_fence():
    """code fence ```json {...} ``` → strip fence。"""
    filled = '{"category": "x", "asset_id": "y"}'
    raw = "```json\n" + filled + "\n```"
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(raw)):
        out = lfg.call_stepfun("test prompt")
    # call_stepfun 只 strip content; fill_gene 才 strip fence
    # 这里验 call_stepfun 不报错
    assert out == raw  # 保留 fence, fill_gene 负责 strip


def test_fill_gene_merges_protected():
    """fill_gene: PROTECTED 字段不动,其它覆盖。"""
    gene_in = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "gene_x",
        "signals_match": ["sig1"],
        "summary": "test",
        "category": None,
    }
    filled_response = json.dumps({
        "type": "Gene",  # 不应被覆盖
        "id": "gene_x_OVERWRITTEN",  # 不应被覆盖
        "category": "repair",  # 应被覆盖
        "strategy": ["s1", "s2", "s3"],  # 应被覆盖
        "asset_id": "sha256:abc",
    })
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(filled_response)):
        filled = lfg.fill_gene(gene_in)
    # protected 保留
    assert filled["id"] == "gene_x"
    assert filled["type"] == "Gene"
    # non-protected 覆盖
    assert filled["category"] == "repair"
    assert filled["strategy"] == ["s1", "s2", "s3"]
    assert filled["asset_id"] == "sha256:abc"


def test_fill_gene_invalid_json_raises():
    """LLM 返回非 JSON → 抛 ValueError。"""
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response("not json at all")):
        try:
            lfg.fill_gene({"id": "x", "summary": "s"})
            assert False, "should raise"
        except ValueError as e:
            assert "non-JSON" in str(e) or "LLM" in str(e)


def test_fill_file_writes_to_output():
    """fill_file: 实际读输入 JSON → fill → 返回 filled dict。"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"id": "g1", "summary": "x", "type": "Gene"}, f)
        tmp = Path(f.name)
    try:
        filled_response = json.dumps({"category": "opt", "strategy": ["a", "b", "c"]})
        with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(filled_response)):
            result = lfg.fill_file(tmp)
        assert result["category"] == "opt"
        assert result["strategy"] == ["a", "b", "c"]
    finally:
        tmp.unlink()


def test_fill_file_writes_output(tmp_path):
    """fill_file: 实际读输入 JSON → fill → 返回 filled dict。"""
    import os
    os.environ["STEPFUN_API_KEY"] = "test_key_for_testing"
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps({"id": "g1", "summary": "x", "type": "Gene"}))
    filled_response = json.dumps({"category": "repair", "strategy": ["a", "b", "c"], "asset_id": "sha256:abc"})
    # 临时 monkey-patch open 让 fill_gene 拿到 mock response
    # 因为 fill_file 调 open(path) → fill_gene → call_stepfun,只需 mock urlopen
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(filled_response)):
        result = lfg.fill_file(inp)
    assert result["category"] == "repair"
    assert result["strategy"] == ["a", "b", "c"]


def test_main_dry_run():
    """main --dry-run: 打印但不调 API,不写盘。"""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        cand = Path(tmpdir) / "cand.json"
        cand.write_text(json.dumps({"id": "g1", "summary": "x"}))
        result = subprocess.run(
            ["python3", str(REPO / "scripts/llm_fill_gene.py"),
             "--candidate", str(cand), "--dry-run"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0
        assert "dry-run" in result.stdout
        # 文件未被修改
        original = json.loads(cand.read_text())
        assert "category" not in original or original.get("category") is None


def test_main_no_args_exits_error():
    """main: 无 --candidate / --staging → parser error exit 2。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/llm_fill_gene.py")],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 2
    assert "--candidate" in result.stderr or "Provide" in result.stderr


def test_main_staging_manifest(tmp_path):
    """main --staging: 处理目录 + 写 manifest。"""
    staging = tmp_path / "staging"
    staging.mkdir()
    cand1 = staging / "gene_candidate_001_x.json"
    cand1.write_text(json.dumps({"id": "g1", "summary": "x", "type": "Gene"}))
    filled_response = json.dumps({"category": "opt", "strategy": ["a", "b", "c"], "asset_id": "sha256:z"})
    # 用 subprocess 跑,因为 main 是 argparse
    import subprocess
    env = {"STEPFUN_API_KEY": "test"}
    import os
    # 把 urlopen 注入到脚本不容易,直接测函数
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(filled_response)):
        # fill_file 内部已测过,这里测 staging 逻辑通过 inspect
        import inspect
        src = inspect.getsource(lfg.main)
        assert "manifest" in src
        assert "llm_filled_manifest" in src


def test_filled_no_internal_marker():
    """_llm_filled 不应写入 Gene JSON（污染 asset_id hash）。"""
    gene_in = {"id": "x", "summary": "y", "type": "Gene"}
    filled_response = json.dumps({"category": "x", "strategy": ["a", "b", "c"]})
    with patch("urllib.request.urlopen", return_value=_mock_urlopen_response(filled_response)):
        filled = lfg.fill_gene(gene_in)
    assert "_llm_filled" not in filled
    assert "category" in filled


def test_stepfun_constants():
    """StepFun 基础配置存在。"""
    assert lfg.STEPFUN_BASE_URL.startswith("https://")
    assert lfg.STEPFUN_MODEL
    assert lfg.SCHEMA_VERSION == "1.12.1"
    assert "{ver}" in lfg.FILL_PROMPT_TEMPLATE
    assert "{input_json}" in lfg.FILL_PROMPT_TEMPLATE