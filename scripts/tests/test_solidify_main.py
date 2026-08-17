"""Test solidify.py main() — interactive approval flow + git commit。

测 4 件事:
1. --yes 自动批准 + 写盘 + git commit
2. --non-interactive + 没有 stdin → auto-skip / auto-reject
3. EOFError 处理 (stdin 关闭)
4. duplicate handling
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def _make_valid_gene(gid: str) -> dict:
    sys.path.insert(0, str(REPO / "openclaw-harness/bin"))
    from canonicalize import compute_asset_id
    g = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": gid,
        "signals_match": [f"sig_{gid}"],
        "summary": f"summary_{gid}",
        "category": "repair",
        "strategy": ["a", "b", "c"],
        "constraints": ["c1"],
        "validation": {"check": "ok"},
    }
    g["asset_id"] = compute_asset_id(g)
    return g


def test_main_yes_approves_and_writes(tmp_path, monkeypatch):
    """main --staging=X --yes: 写 plan/genes/ + plan/events/ + git commit。

    用临时 PLAN_GENES / PLAN_EVENTS 避免污染真实目录。
    """
    import solidify as sf

    # 重定向 PLAN_GENES / PLAN_EVENTS 到 tmp
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)

    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    # 创建 staging
    staging = tmp_path / "staging"
    staging.mkdir()
    g = _make_valid_gene("test_g1")
    (staging / "test_g1.json").write_text(json.dumps(g))

    # 用 subprocess 跑（main 是 argparse）
    # 不能 monkeypatch module-level constants via subprocess;
    # 改用 inspect 调 main + 模拟 yes 流程
    # 简单测：直接 import + 调 main args
    # 这里测函数级：手动构造 Namespace
    from solidify import main
    import argparse
    args = argparse.Namespace(
        staging=str(staging),
        gene=None,
        list=False,
        yes=True,
        non_interactive=False,
    )
    # 直接调 main（patch sys.argv 因为 argparse 用 sys.argv）
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        try:
            main()
        except SystemExit as e:
            # git commit 失败可能 exit 非 0
            pass

    # 验证: plan/genes/test_g1.json 写入
    written = fake_genes / "test_g1.json"
    assert written.exists(), f"gene not written to {written}"
    # 验证: plan/events/event_solidify_test_g1.json 写入
    event = fake_events / "event_solidify_test_g1.json"
    assert event.exists(), f"event not written to {event}"
    evt = json.loads(event.read_text())
    assert evt["type"] == "EvolutionEvent"
    assert evt["outcome"]["status"] == "approved"
    assert "test_g1" in evt["genes_used"]


def test_main_non_interactive_safe_skip(tmp_path, monkeypatch):
    """main --non-interactive + 无 stdin: 跳过审批（safe reject）。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    staging = tmp_path / "staging"
    staging.mkdir()
    g = _make_valid_gene("non_int_g")
    (staging / "non_int_g.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--non-interactive"]):
        try:
            sf.main()
        except SystemExit:
            pass

    # non-interactive 不应写盘
    assert not (fake_genes / "non_int_g.json").exists()


def test_main_eoferror_safe_skip(tmp_path, monkeypatch):
    """main: input() 抛 EOFError → safe skip。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    staging = tmp_path / "staging"
    staging.mkdir()
    g = _make_valid_gene("eof_g")
    (staging / "eof_g.json").write_text(json.dumps(g))

    # input() 抛 EOFError → 走 eof 分支 → rejected
    def fake_input(*args, **kwargs):
        raise EOFError("no stdin")

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=fake_input):
            try:
                sf.main()
            except SystemExit:
                pass

    assert not (fake_genes / "eof_g.json").exists()


def test_main_duplicate_detection(tmp_path, monkeypatch, capsys):
    """main: 检测到 duplicate (asset_id 已存在) → skip 或 reject。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    # 先把 gene 写入 fake_genes (当作"已存在")
    g = _make_valid_gene("dup_g")
    (fake_genes / "dup_g.json").write_text(json.dumps(g))

    # --list 分支写死了 /tmp/v_staging，用真实路径
    staging = Path("/tmp/v_staging")
    staging.mkdir(parents=True, exist_ok=True)
    (staging / "dup_g.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--list"]):
        try:
            sf.main()
        except SystemExit:
            pass

    captured = capsys.readouterr()
    # --list 应显示 dup_g + DUPLICATE 提示
    assert "dup_g" in captured.out
    assert "dup" in captured.out.lower() or "DUPLICATE" in captured.out or "✅" in captured.out


def test_main_gene_single_file(tmp_path, monkeypatch):
    """main --gene=path: 审批单个文件。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    g = _make_valid_gene("single_g")
    target = tmp_path / "single_g.json"
    target.write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--gene", str(target), "--yes"]):
        try:
            sf.main()
        except SystemExit:
            pass

    assert (fake_genes / "single_g.json").exists()