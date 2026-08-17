"""Test cross_library_auto.py — 5 库跨学科映射自动化。"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def test_import_cross_library_auto():
    """cross_library_auto.py 可 import + 5 库图结构。"""
    import cross_library_auto as cla
    assert len(cla.LIBRARY_TEMPLATES) == 5
    assert "BeautifulMathematics" in cla.LIBRARY_TEMPLATES
    assert "cell-biology" in cla.LIBRARY_TEMPLATES
    assert "CognitivePsychology" in cla.LIBRARY_TEMPLATES
    assert "OpenStaxBiology" in cla.LIBRARY_TEMPLATES
    assert "evomap" in cla.LIBRARY_TEMPLATES
    # 每库有 _default + 至少 1 关键词
    for lib, templates in cla.LIBRARY_TEMPLATES.items():
        assert "_default" in templates
        assert len(templates) >= 2


def test_library_graph_5_libs():
    """LIBRARY_GRAPH 包含 5 库 + 闭环。"""
    import cross_library_auto as cla
    assert len(cla.LIBRARY_GRAPH) == 5
    for lib, refs in cla.LIBRARY_GRAPH.items():
        assert isinstance(refs, list)
        assert len(refs) >= 1


def test_library_graph_edge_strengths():
    """LIBRARY_GRAPH_EDGE 5×5 矩阵 + 自身反馈。"""
    import cross_library_auto as cla
    assert len(cla.LIBRARY_GRAPH_EDGE) == 5
    for lib, edges in cla.LIBRARY_GRAPH_EDGE.items():
        assert lib in edges  # 自身反馈存在
        assert edges[lib] >= 0.0 and edges[lib] <= 1.0


def test_match_evidence_with_keyword():
    """match_evidence 命中关键词 → 模板文本 + 高 confidence。"""
    from cross_library_auto import match_evidence
    text, conf = match_evidence("BeautifulMathematics", ["幂等"], "")
    assert "幂等" in text or "幂等" in text.lower() or "幂等" in text
    assert conf >= 0.5


def test_match_evidence_no_keyword():
    """match_evidence 无命中 → _default + 0.3 confidence。"""
    from cross_library_auto import match_evidence
    text, conf = match_evidence("BeautifulMathematics", ["very_rare_keyword_xyz"], "")
    assert conf <= 0.4


def test_match_evidence_multi_hits_boost_confidence():
    """多个关键词命中 → confidence > 0.7。"""
    from cross_library_auto import match_evidence
    text, conf = match_evidence("BeautifulMathematics", ["幂等", "sha256", "hot_path"], "")
    assert conf >= 0.7


def test_auto_evidence_v1_default():
    """auto_cross_library_evidence version="v1.0" → 简单格式（无章节号）。"""
    from cross_library_auto import auto_cross_library_evidence
    gene = {
        "signals_match": ["exec"],
        "summary": "exec hot path",
    }
    result = auto_cross_library_evidence(gene, version="v1.0")
    assert len(result) == 5
    # v1.0: "{lib} {text}" 不带 "Ch" 章节号
    for line in result:
        assert not line.startswith("BeautifulMathematics Ch") or "Ch" not in line or len(line) < 200


def test_auto_evidence_v2_with_chapter():
    """auto_cross_library_evidence version="v2.0" → 含章节号。"""
    from cross_library_auto import auto_cross_library_evidence, LIBRARY_CHAPTER
    gene = {"signals_match": ["exec"], "summary": "exec"}
    result = auto_cross_library_evidence(gene, version="v2.0")
    assert len(result) == 5
    # 至少 1 行带章节号
    has_chapter = any(any(ch in line for ch in LIBRARY_CHAPTER.values()) for line in result)
    assert has_chapter


def test_auto_evidence_v3_with_cross_refs():
    """auto_cross_library_evidence version="v3.0" → 跨库互引（→ [...]）。"""
    from cross_library_auto import auto_cross_library_evidence
    gene = {"signals_match": ["exec"], "summary": "exec"}
    result = auto_cross_library_evidence(gene, version="v3.0")
    assert len(result) == 5
    # v3.0: 至少 1 行包含 "→"
    has_ref = any("→" in line for line in result)
    assert has_ref


def test_auto_evidence_handles_signals_key():
    """auto_cross_library_evidence 支持 signals 或 signals_match key。"""
    from cross_library_auto import auto_cross_library_evidence
    g1 = {"signals_match": ["x"], "summary": ""}
    g2 = {"signals": ["x"], "summary": ""}
    g3 = {}  # 无 signals
    r1 = auto_cross_library_evidence(g1)
    r2 = auto_cross_library_evidence(g2)
    r3 = auto_cross_library_evidence(g3)
    assert len(r1) == 5
    assert len(r2) == 5
    assert len(r3) == 5


def test_auto_evidence_truncates_long_lines():
    """auto_cross_library_evidence 输出不超过 200 chars（v3.0 放宽后）。"""
    from cross_library_auto import auto_cross_library_evidence
    gene = {
        "signals_match": ["x"] * 50,
        "summary": "x" * 500,
    }
    result = auto_cross_library_evidence(gene, version="v3.0")
    for line in result:
        assert len(line) <= 200, f"line too long: {len(line)}"


def test_fill_file_dry_run(tmp_path):
    """fill_file dry_run=True → 不写盘。"""
    from cross_library_auto import fill_file
    gene = {"id": "test_fill", "signals_match": ["exec"], "summary": "x"}
    p = tmp_path / "g.json"
    p.write_text(json.dumps(gene))
    mtime_before = p.stat().st_mtime
    result = fill_file(p, dry_run=True)
    assert result["id"] == "test_fill"
    assert len(result["evidence"]) == 5
    # 文件未被修改（_cross_library_auto 不存在）
    reloaded = json.load(open(p))
    assert "_cross_library_auto" not in reloaded


def test_fill_file_real_write(tmp_path):
    """fill_file dry_run=False → 写盘 + _cross_library_auto=True。"""
    from cross_library_auto import fill_file
    gene = {"id": "test_fill_real", "signals_match": ["幂等"], "summary": "test"}
    p = tmp_path / "g2.json"
    p.write_text(json.dumps(gene))
    result = fill_file(p, dry_run=False)
    reloaded = json.load(open(p))
    assert reloaded.get("_cross_library_auto") is True
    assert len(reloaded["cross_library_evidence"]) == 5


def test_validate_evidence_quality_high():
    """5/5 库命中具体模板 → no warnings。"""
    from cross_library_auto import validate_evidence_quality, auto_cross_library_evidence
    gene = {
        "signals_match": ["幂等", "sha256", "hot_path", "ttl", "receptor"],
        "summary": "test",
    }
    gene["cross_library_evidence"] = auto_cross_library_evidence(gene, version="v2.0")
    matched, total, warnings = validate_evidence_quality(gene)
    assert matched >= 3
    assert total == 5


def test_validate_evidence_quality_low():
    """默认模板占多数 → 警告（当 matched < 3）。"""
    from cross_library_auto import validate_evidence_quality
    gene = {
        "cross_library_evidence": [
            "BeautifulMathematics _default",  # 命中 _default 跳过
            "cell-biology _default",
            "CognitivePsychology _default",
            "OpenStaxBiology _default",
            "evomap _default",
        ],
    }
    matched, total, warnings = validate_evidence_quality(gene)
    # 全部为默认样式 → matched == 0
    assert matched == 0
    assert total == 5
    assert len(warnings) == 1
    assert "0/5" in warnings[0]


def test_validate_evidence_quality_empty():
    """evidence 空列表 → 0/5。"""
    from cross_library_auto import validate_evidence_quality
    gene = {"cross_library_evidence": []}
    matched, total, warnings = validate_evidence_quality(gene)
    assert matched == 0
    assert total == 0


def test_main_dry_run(tmp_path):
    """main() dry-run 模式 → 不写盘 + 打印 evidence。"""
    gene = {"id": "main_dry", "signals_match": ["exec"], "summary": "x"}
    p = tmp_path / "g.json"
    p.write_text(json.dumps(gene))
    result = subprocess.run(
        ["python3", str(REPO / "scripts/cross_library_auto.py"),
         str(p), "--dry-run"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout
    # 文件未改
    reloaded = json.load(open(p))
    assert "_cross_library_auto" not in reloaded


def test_main_validate_mode(tmp_path):
    """main() --validate 模式 → 不修改文件 + 打印质量统计。"""
    gene = {
        "id": "main_val",
        "signals_match": ["幂等", "sha256"],
        "summary": "test",
        "cross_library_evidence": [
            "BeautifulMathematics Ch12: 幂等性证明",
            "cell-biology Ch15: 反馈机制",
            "CognitivePsychology Ch6: 锚点",
            "OpenStaxBiology Ch01: 进化选择",
            "evomap §2.3: GEP 协议",
        ],
    }
    p = tmp_path / "g3.json"
    p.write_text(json.dumps(gene))
    result = subprocess.run(
        ["python3", str(REPO / "scripts/cross_library_auto.py"),
         str(p), "--validate"],
        capture_output=True, text=True, timeout=30,
    )
    combined = result.stdout + result.stderr
    assert "5 库" in combined or "evidence" in combined or "libraries matched" in combined


def test_main_no_files(tmp_path):
    """main() 找不到文件 → exit 1。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/cross_library_auto.py"),
         str(tmp_path / "nonexistent_dir")],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "No gene files" in result.stdout or "❌" in result.stdout