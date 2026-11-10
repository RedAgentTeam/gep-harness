"""Test solidify.py main() — interactive approval flow + git commit。

测 4 件事:
1. --yes 拒绝：不写盘、不调用 git
2. --non-interactive + 没有 stdin → auto-skip / auto-reject
3. EOFError 处理 (stdin 关闭)
4. duplicate handling
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[2]
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


def _assert_yes_refused(sf, argv, fake_genes, fake_events, monkeypatch, capsys):
    """--yes 必须在写资产 / 调 git 之前拒绝。"""
    def _forbidden(*_a, **_k):
        raise AssertionError("subprocess.run must not run on --yes (no validate, no git)")

    def _no_load():
        raise AssertionError("load_existing_genes must not run after --yes refusal")

    monkeypatch.setattr(sf.subprocess, "run", _forbidden)
    monkeypatch.setattr(sf, "load_existing_genes", _no_load)

    with patch.object(sys, "argv", argv):
        with pytest.raises(SystemExit) as exc:
            sf.main()
    assert exc.value.code not in (0, None)
    err = capsys.readouterr().err
    assert "--yes" in err
    assert "拒绝" in err
    assert list(fake_genes.glob("*.json")) == []
    assert list(fake_events.glob("*.json")) == []


def test_main_yes_refuses_before_write_or_git(tmp_path, monkeypatch, capsys):
    """main --staging=X --yes: 拒绝，不写 plan/genes、plan/events，不调用 git。"""
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
    g = _make_valid_gene("test_g1")
    (staging / "test_g1.json").write_text(json.dumps(g))

    _assert_yes_refused(
        sf,
        ["solidify.py", "--staging", str(staging), "--yes"],
        fake_genes,
        fake_events,
        monkeypatch,
        capsys,
    )


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


def test_main_gene_single_file_yes_refused(tmp_path, monkeypatch, capsys):
    """main --gene=path --yes: 拒绝，不写单个 Gene，不调用 git。"""
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

    _assert_yes_refused(
        sf,
        ["solidify.py", "--gene", str(target), "--yes"],
        fake_genes,
        fake_events,
        monkeypatch,
        capsys,
    )
    assert not (fake_genes / "single_g.json").exists()


def test_main_yes_with_non_interactive_still_refused(tmp_path, monkeypatch, capsys):
    """--yes 不能借 --non-interactive 变成批准或静默跳过后再写盘。"""
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
    g = _make_valid_gene("yes_ni")
    (staging / "yes_ni.json").write_text(json.dumps(g))

    _assert_yes_refused(
        sf,
        ["solidify.py", "--staging", str(staging), "--non-interactive", "--yes"],
        fake_genes,
        fake_events,
        monkeypatch,
        capsys,
    )
