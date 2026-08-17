"""Test clean_legacy_genes.py — Gene 命名清理。"""

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def _make_gene(tmp_path, gid, mtime_offset=0):
    """在 tmp_path/plan/genes/ 创建一个 Gene JSON，返回文件路径。"""
    plan_genes = tmp_path / "plan" / "genes"
    plan_genes.mkdir(parents=True, exist_ok=True)
    f = plan_genes / f"g_{gid}.json"
    f.write_text(json.dumps({"type": "Gene", "schema_version": "1.12.1", "id": gid}))
    # 调整 mtime 模拟新旧 (显式设置不同时间戳)
    import os
    if mtime_offset:
        ts_newer = time.time() - mtime_offset
        ts_older = time.time() - (mtime_offset + 1000)  # 老 1000 秒
        # 老文件 (mtime_offset > 0 表示这是较老的)
        os.utime(f, (ts_older, ts_older))
    return f


def _make_gene_with_mtime(tmp_path, gid, mtime):
    """创建 Gene 文件并显式设置 mtime。"""
    plan_genes = tmp_path / "plan" / "genes"
    plan_genes.mkdir(parents=True, exist_ok=True)
    f = plan_genes / f"g_{gid}_{mtime}.json"
    f.write_text(json.dumps({"type": "Gene", "schema_version": "1.12.1", "id": gid}))
    import os
    os.utime(f, (mtime, mtime))
    return f


def test_import_constants():
    """clean_legacy_genes.py 常量。"""
    import clean_legacy_genes as clg
    assert clg.REPO == REPO
    assert clg.PLAN_GENES == REPO / "plan" / "genes"


def test_main_dry_run_reports_no_dup(tmp_path, monkeypatch, capsys):
    """dry-run 无重复 → '✅ 无重复'。"""
    import clean_legacy_genes as clg
    _make_gene(tmp_path, "gene_a")
    _make_gene(tmp_path, "gene_b")
    monkeypatch.setattr(clg, "PLAN_GENES", tmp_path / "plan" / "genes")
    clg.main()
    captured = capsys.readouterr()
    assert "✅ 无重复" in captured.out or "重复 id 数: 0" in captured.out


def test_main_dry_run_finds_duplicates(tmp_path, monkeypatch, capsys):
    """dry-run 发现重复 → 打印 DEL/KEEP。"""
    import clean_legacy_genes as clg
    f_old = _make_gene_with_mtime(tmp_path, "gene_dup", mtime=1000000000)  # 明显旧
    f_new = _make_gene_with_mtime(tmp_path, "gene_dup", mtime=2000000000)  # 明显新
    monkeypatch.setattr(clg, "PLAN_GENES", tmp_path / "plan" / "genes")
    clg.main()
    captured = capsys.readouterr()
    assert "重复 id 数: 1" in captured.out or "DEL:" in captured.out
    assert "KEEP:" in captured.out
    # 老的标为 DEL，新的标为 KEEP
    assert f_old.name in captured.out
    assert f_new.name in captured.out


def test_main_execute_deletes_old(tmp_path, monkeypatch, capsys):
    """--execute 模式删除旧文件。"""
    import clean_legacy_genes as clg
    f_old = _make_gene_with_mtime(tmp_path, "gene_dup2", mtime=1000000000)
    f_new = _make_gene_with_mtime(tmp_path, "gene_dup2", mtime=2000000000)
    plan_genes = tmp_path / "plan" / "genes"
    print(f"DEBUG: plan_genes={plan_genes}, exists={plan_genes.exists()}")
    print(f"DEBUG: files={list(plan_genes.glob('*.json'))}")
    print(f"DEBUG: f_old={f_old}, exists={f_old.exists()}")
    monkeypatch.setattr(clg, "PLAN_GENES", plan_genes)
    monkeypatch.setattr("sys.argv", ["clean_legacy_genes.py", "--execute"])
    clg.main()
    print(f"DEBUG: after main: f_old.exists={f_old.exists()}, f_new.exists={f_new.exists()}")
    assert not f_old.exists(), "old file should be deleted"
    assert f_new.exists(), "new file should remain"


def test_main_dry_run_finds_double_prefix(tmp_path, monkeypatch, capsys):
    """dry-run 发现双 gene_ 前缀 → 建议 rename。"""
    import clean_legacy_genes as clg
    plan_genes = tmp_path / "plan" / "genes"
    plan_genes.mkdir(parents=True, exist_ok=True)
    # 创建一个 gene_gene_* 文件
    (plan_genes / "gene_gene_xyz.json").write_text(json.dumps({
        "type": "Gene", "schema_version": "1.12.1", "id": "g_x",
    }))
    # 创建另一个正常文件（避免"无重复"判断影响输出）
    (plan_genes / "g_normal.json").write_text(json.dumps({
        "type": "Gene", "schema_version": "1.12.1", "id": "g_n",
    }))
    monkeypatch.setattr(clg, "PLAN_GENES", plan_genes)
    clg.main()
    captured = capsys.readouterr()
    assert "REN:" in captured.out
    assert "gene_gene_xyz" in captured.out
    assert "gene_xyz" in captured.out


def test_main_execute_deletes_old(tmp_path, monkeypatch, capsys):
    """--execute 模式删除旧文件。"""
    import clean_legacy_genes as clg
    f_old = _make_gene_with_mtime(tmp_path, "gene_dup2", mtime=1000000000)
    f_new = _make_gene_with_mtime(tmp_path, "gene_dup2", mtime=2000000000)
    plan_genes = tmp_path / "plan" / "genes"
    monkeypatch.setattr(clg, "PLAN_GENES", plan_genes)
    monkeypatch.setattr("sys.argv", ["clean_legacy_genes.py", "--execute"])
    clg.main()
    assert not f_old.exists(), "old file should be deleted"
    assert f_new.exists(), "new file should remain"


def test_main_execute_renames_double_prefix(tmp_path, monkeypatch, capsys):
    """--execute 模式重命名 gene_gene_* 文件。"""
    import clean_legacy_genes as clg
    plan_genes = tmp_path / "plan" / "genes"
    plan_genes.mkdir(parents=True, exist_ok=True)
    f_old = plan_genes / "gene_gene_abc.json"
    f_old.write_text(json.dumps({"id": "g_abc"}))
    # 加一个普通文件避免 main() 提前退出
    (plan_genes / "g_normal2.json").write_text(json.dumps({"id": "g_n2"}))
    monkeypatch.setattr(clg, "PLAN_GENES", plan_genes)
    monkeypatch.setattr("sys.argv", ["clean_legacy_genes.py", "--execute"])
    clg.main()
    assert not f_old.exists(), "old name should be renamed"
    assert (plan_genes / "gene_abc.json").exists(), "new name should exist"


def test_main_handles_invalid_json(tmp_path, monkeypatch, capsys):
    """无效 JSON 文件被跳过，不 crash。"""
    import clean_legacy_genes as clg
    plan_genes = tmp_path / "plan" / "genes"
    plan_genes.mkdir(parents=True, exist_ok=True)
    (plan_genes / "bad.json").write_text("not json {{{")
    (plan_genes / "good.json").write_text(json.dumps({"id": "g1"}))
    monkeypatch.setattr(clg, "PLAN_GENES", plan_genes)
    clg.main()
    captured = capsys.readouterr()
    assert "skip" in captured.out or "⚠️" in captured.out
    # bad 文件未被删
    assert (plan_genes / "bad.json").exists()


def test_main_handles_gene_without_id(tmp_path, monkeypatch, capsys):
    """Gene 缺 id → 跳过该文件。"""
    import clean_legacy_genes as clg
    plan_genes = tmp_path / "plan" / "genes"
    plan_genes.mkdir(parents=True, exist_ok=True)
    (plan_genes / "no_id.json").write_text(json.dumps({"type": "Gene"}))
    (plan_genes / "with_id.json").write_text(json.dumps({"id": "g1"}))
    monkeypatch.setattr(clg, "PLAN_GENES", plan_genes)
    clg.main()
    # 不会 crash，统计中只算 with_id
    captured = capsys.readouterr()
    assert "Gene 数" in captured.out


def test_cli_subprocess_dry_run():
    """CLI dry-run 跑通。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/clean_legacy_genes.py")],
        capture_output=True, text=True, timeout=30,
    )
    # 在真 repo 上跑，输出应包含 Gene 统计
    assert result.returncode == 0
    assert "Gene 数" in result.stdout or "目录" in result.stdout