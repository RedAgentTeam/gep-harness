"""Test gene_to_history_capsule.py — Gene 演化历史 → Capsule 打包。

测 2 件事：
1. extract_tool() 文件名解析
2. main() 生成 Capsule 草稿到 /tmp/capsule_drafts/（不写 plan/capsules/）
"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import gene_to_history_capsule as ghc


def test_extract_tool_hotpath_pattern():
    """'xxx_hotpath' 模式 → tool 名。"""
    assert ghc.extract_tool("gene_exec_hotpath_v21.json") == "exec"
    assert ghc.extract_tool("gene_read_hotpath_v72.json") == "read"
    assert ghc.extract_tool("gene_write_hotpath_v15.json") == "write"
    assert ghc.extract_tool("gene_message_hotpath_v18.json") == "message"


def test_extract_tool_hot_path_colon():
    """'hot_path:tool' 模式 → tool 名（候选 Gene 文件）。"""
    assert ghc.extract_tool("gene_candidate_001_hot_path:read.json") == "read"
    assert ghc.extract_tool("gene_candidate_002_hot_path:write.json") == "write"
    assert ghc.extract_tool("gene_candidate_005_hot_path:message.json") == "message"


def test_extract_tool_fallback():
    """兜底：取第一个 _ 分隔段。"""
    assert ghc.extract_tool("gene_unknown_pattern.json") == "unknown"


def test_extract_tool_no_gene_prefix():
    """无 gene_ 前缀 → 直接处理。"""
    # 匹配 _hotpath 在中间
    assert ghc.extract_tool("process_hotpath_v10.json") == "process"


def test_main_generates_drafts(tmp_path, monkeypatch):
    """main: 为每个 tool（≥2 版本）生成 Capsule 草稿。"""
    # 临时改 DRAFTS_DIR 到 tmp
    monkeypatch.setattr(ghc, "DRAFTS_DIR", tmp_path / "drafts")
    # 不能 monkeypatch PLAN_GENES 指向 tmp,因为需要真实 plan/genes/
    # 直接调 main
    try:
        ghc.main()
    except SystemExit:
        pass
    # 检查草稿目录创建
    assert ghc.DRAFTS_DIR.exists()
    drafts = list(ghc.DRAFTS_DIR.glob("*.json"))
    assert len(drafts) >= 1, f"expected ≥1 draft, got {len(drafts)}"


def test_main_drafts_have_required_fields(tmp_path, monkeypatch):
    """main 生成的草稿含必需字段。"""
    monkeypatch.setattr(ghc, "DRAFTS_DIR", tmp_path / "drafts2")
    try:
        ghc.main()
    except SystemExit:
        pass
    drafts = list(ghc.DRAFTS_DIR.glob("*.json"))
    if not drafts:
        return  # 没 draft 时跳过（plan/genes/ 文件少）
    d = json.loads(drafts[0].read_text())
    assert d["type"] == "Capsule"
    assert d["schema_version"] == "1.12.1"
    assert d["_draft"] is True
    assert d["_needs_review"] is True
    assert d["asset_id"].startswith("sha256:")
    assert "pack_of" in d
    assert isinstance(d["pack_of"], list)
    assert "scope" in d
    assert "openclaw" in d["scope"]


def test_main_drafts_not_in_plan_capsules(tmp_path, monkeypatch):
    """main 不写 plan/capsules/,只写 DRAFTS_DIR。"""
    monkeypatch.setattr(ghc, "DRAFTS_DIR", tmp_path / "drafts3")
    # 记录 plan/capsules/ 修改前 mtime
    plan_capsules = ghc.PLAN_CAPSULES
    files_before = set(plan_capsules.glob("*.json"))
    try:
        ghc.main()
    except SystemExit:
        pass
    files_after = set(plan_capsules.glob("*.json"))
    # 不应有新文件写入 plan/capsules/
    new_files = files_after - files_before
    # 过滤掉 tmp_path 里的(因为 monkeypatch)
    real_new = [f for f in new_files if str(f).startswith(str(plan_capsules))]
    assert len(real_new) == 0, f"main wrote to plan/capsules/: {real_new}"


def test_main_prints_summary(capsys, monkeypatch):
    """main 打印分组汇总 + 草稿列表 + 后续步骤。"""
    monkeypatch.setattr(ghc, "DRAFTS_DIR", Path("/tmp/_test_drafts_summary"))
    try:
        ghc.main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "演化历史" in captured.out
    assert "Capsule 草稿" in captured.out or "草稿" in captured.out
    assert "Solidify" in captured.out or "不删除" in captured.out


def test_main_groups_by_tool(monkeypatch):
    """main 按 tool 分组,至少 exec/read/write 各一个。"""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setattr(ghc, "DRAFTS_DIR", Path(td))
        try:
            ghc.main()
        except SystemExit:
            pass
        drafts = list(Path(td).glob("*.json"))
        tools = set()
        for d in drafts:
            name = d.stem
            # capsule_gene_{tool}_evolution_...
            if "evolution" in name:
                tool_part = name.split("capsule_gene_")[1].split("_evolution")[0]
                tools.add(tool_part)
        # 至少 3 个 tool 有 capsule
        assert len(tools) >= 3, f"only tools: {tools}"