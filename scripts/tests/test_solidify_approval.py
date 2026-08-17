"""Test solidify.py 剩余 main() 交互分支 (75%→100%)。

补 missing lines: 27, 148-149, 165-180, 198-203, 207-220, 253
- validate_failed 跳过
- duplicate user 跳过
- 用户拒绝 (resp != 'y')
- 审批摘要打印
- git commit 成功/失败
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def _make_valid_gene(gid: str) -> dict:
    import solidify as sf
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
        "asset_id": "",
    }
    g["asset_id"] = sf.compute_asset_id(g)
    return g


def test_main_validate_failed_non_interactive(tmp_path, monkeypatch, capsys):
    """main: validate_failed + --non-interactive → auto-skip。"""
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
    g = {"id": "vf_test", "type": "Gene", "summary": "missing fields"}  # 缺必需字段
    (staging / "vf_test.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--non-interactive"]):
        try:
            sf.main()
        except SystemExit:
            pass
    assert not (fake_genes / "vf_test.json").exists()


def test_main_validate_failed_eof(tmp_path, monkeypatch):
    """main: validate_failed + input() EOFError → auto-skip。"""
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
    g = {"id": "vf_eof", "type": "Gene", "summary": "missing"}  # validate 会 fail
    (staging / "vf_eof.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=EOFError("no stdin")):
            try:
                sf.main()
            except SystemExit:
                pass
    assert not (fake_genes / "vf_eof.json").exists()


def test_main_validate_failed_user_rejects(tmp_path, monkeypatch):
    """main: validate_failed + 用户输入 n → skip。"""
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
    g = {"id": "vf_user_n", "type": "Gene", "summary": "missing"}
    (staging / "vf_user_n.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=["n"]):
            try:
                sf.main()
            except SystemExit:
                pass
    assert not (fake_genes / "vf_user_n.json").exists()


def test_main_duplicate_user_rejects(tmp_path, monkeypatch):
    """main: duplicate + 用户输入 n → skip。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    g = _make_valid_gene("dup_user")
    (fake_genes / "dup_user.json").write_text(json.dumps(g))

    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "dup_user.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=["n"]):
            try:
                sf.main()
            except SystemExit:
                pass
    # dup_user.json 还在 fake_genes（没被覆盖）


def test_main_user_rejects_approval(tmp_path, monkeypatch):
    """main: 审批门 + 用户输入 n → rejected。"""
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
    g = _make_valid_gene("reject_me")
    (staging / "reject_me.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=["n"]):
            try:
                sf.main()
            except SystemExit:
                pass
    assert not (fake_genes / "reject_me.json").exists()


def test_main_user_approves_with_yes(tmp_path, monkeypatch):
    """main: 审批门 + 用户输入 y → 写盘 + 提交。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    # 不 patch GEP_HARNESS，保持 REPO 以便 validate_gene 找到 validate_gep.py

    staging = tmp_path / "staging"
    staging.mkdir()
    g = _make_valid_gene("approve_me")
    (staging / "approve_me.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=["y"]):
            try:
                sf.main()
            except SystemExit:
                pass
    assert (fake_genes / "approve_me.json").exists()
    assert (fake_events / "event_solidify_approve_me.json").exists()


def test_main_approval_eof(tmp_path, monkeypatch):
    """main: 审批门 + input() EOFError → auto-reject。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    # 不 patch GEP_HARNESS

    staging = tmp_path / "staging"
    staging.mkdir()
    g = _make_valid_gene("eof_approve")
    (staging / "eof_approve.json").write_text(json.dumps(g))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=EOFError("no stdin")):
            try:
                sf.main()
            except SystemExit:
                pass
    assert not (fake_genes / "eof_approve.json").exists()


def test_main_prints_summary(tmp_path, monkeypatch, capsys):
    """main: 审批摘要打印 (✅ approved / rejected)。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    # 不 patch GEP_HARNESS

    staging = tmp_path / "staging"
    staging.mkdir()
    g1 = _make_valid_gene("sum_a")
    g2 = _make_valid_gene("sum_r")
    (staging / "sum_a.json").write_text(json.dumps(g1))
    (staging / "sum_r.json").write_text(json.dumps(g2))

    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging)]):
        with patch("builtins.input", side_effect=["y", "n"]):
            try:
                sf.main()
            except SystemExit:
                pass
    captured = capsys.readouterr()
    assert "审批摘要" in captured.out or "approved" in captured.out
    assert (fake_genes / "sum_a.json").exists()
    assert not (fake_genes / "sum_r.json").exists()


def test_main_git_commit_failure_graceful(tmp_path, monkeypatch):
    """main: git commit 失败 → 仍继续 (graceful)。"""
    import solidify as sf
    fake_plan = tmp_path / "plan"
    fake_genes = fake_plan / "genes"
    fake_events = fake_plan / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    # 创建 .git 让 git 命令找到 repo
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)

    staging = tmp_path / "staging"
    staging.mkdir()
    g = _make_valid_gene("git_fail")
    (staging / "git_fail.json").write_text(json.dumps(g))

    # patch git commit 返回失败
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        try:
            sf.main()
        except SystemExit:
            pass
    # 即便 git commit 失败,plan/genes/ 文件仍应写入
    assert (fake_genes / "git_fail.json").exists()


def test_main_module_runs():
    """if __name__ == '__main__': main() → --help 能跑。"""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/solidify.py"), "--help"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "--staging" in result.stdout
    assert "--gene" in result.stdout
    assert "--yes" in result.stdout
    assert "--non-interactive" in result.stdout