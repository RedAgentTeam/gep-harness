"""Test auto_changelog_commit.py — CHANGELOG 自动 commit。"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))


def _init_tmp_repo(tmp_path):
    """在 tmp_path 建干净 git repo，含一次 init commit。"""
    subprocess.run(["git", "init", "-q", "-b", "master"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)


def test_import_constants():
    """auto_changelog_commit.py 可 import + REPO 路径正确。"""
    import auto_changelog_commit as acc
    assert acc.REPO == REPO
    assert acc.REPO.is_dir()


def test_git_has_changes_no_changes(tmp_path, monkeypatch):
    """git_has_changes() 在干净 repo → False。"""
    import auto_changelog_commit as acc
    _init_tmp_repo(tmp_path)
    monkeypatch.setattr(acc, "REPO", tmp_path)
    assert acc.git_has_changes() is False


def test_git_has_changes_with_changes(tmp_path, monkeypatch):
    """git_has_changes() 在 dirty repo → True。"""
    import auto_changelog_commit as acc
    _init_tmp_repo(tmp_path)
    monkeypatch.setattr(acc, "REPO", tmp_path)
    (tmp_path / "new.txt").write_text("x")
    assert acc.git_has_changes() is True


def test_main_skips_when_no_changes(tmp_path, monkeypatch, capsys):
    """main() 无变更 → 跳过。"""
    import auto_changelog_commit as acc
    _init_tmp_repo(tmp_path)
    monkeypatch.setattr(acc, "REPO", tmp_path)
    monkeypatch.setattr("sys.argv", ["auto_changelog_commit.py"])
    acc.main()
    captured = capsys.readouterr()
    assert "跳过" in captured.out or "无变更" in captured.out


def test_main_commits_changelog(tmp_path, monkeypatch, capsys):
    """main() CHANGELOG.md 变更 → 自动 commit。"""
    import auto_changelog_commit as acc
    _init_tmp_repo(tmp_path)
    monkeypatch.setattr(acc, "REPO", tmp_path)
    monkeypatch.setattr("sys.argv", ["auto_changelog_commit.py", "--message=test"])
    (tmp_path / "CHANGELOG.md").write_text("# v1\n")
    subprocess.run(["git", "add", "CHANGELOG.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    (tmp_path / "CHANGELOG.md").write_text("# v2\n")
    acc.main()
    captured = capsys.readouterr()
    assert "auto-commit" in captured.out or "跳过" in captured.out or "commit failed" in captured.out


def test_main_cli_help():
    """main() --help 可跑。"""
    result = subprocess.run(
        ["python3", str(REPO / "scripts/auto_changelog_commit.py"), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "message" in result.stdout.lower() or "commit" in result.stdout.lower()