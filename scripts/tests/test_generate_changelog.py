"""Test generate_changelog.py — 自动从 git log 生成 CHANGELOG.md。

测试 4 件事：
1. categorize() 关键词匹配
2. parse_commit_log() 解析 git log 格式
3. build_changelog() 输出格式
4. main() dry-run 模式 + --since 参数
"""

import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import generate_changelog as gc


def test_categorize_test():
    """'fix/test/feat/ci/docs' 关键词 → 对应分类。"""
    assert gc.categorize("fix: bug") == "fix"
    assert gc.categorize("test: add pytest") == "test"
    assert gc.categorize("feat: new feature") == "feat"
    assert gc.categorize("docs: update README") == "docs"
    assert gc.categorize("ci: github actions") == "ci"
    # 多关键词取首个（按 CAT_ORDER 顺序）
    assert gc.categorize("fix and feat") in ("fix", "feat")


def test_categorize_chore_default():
    """无匹配 → 'chore'。"""
    assert gc.categorize("random commit message") == "chore"
    assert gc.categorize("") == "chore"


def test_categorize_uses_first_line():
    """只读第一行（subject）。"""
    msg = "fix: bug\n\nlong body with feat: keyword"
    assert gc.categorize(msg) == "fix"


def test_parse_commit_log_basic():
    """解析标准格式：sha|||subject|||author。"""
    raw = "abc1234|||fix: bug|||Red\ndef5678|||feat: new|||Ho\n"
    commits = gc.parse_commit_log(raw)
    assert len(commits) == 2
    assert commits[0]["sha"] == "abc1234"
    assert commits[0]["subject"] == "fix: bug"
    assert commits[0]["author"] == "Red"
    assert commits[0]["cat"] == "fix"
    assert commits[1]["cat"] == "feat"


def test_parse_commit_log_skips_invalid():
    """无效行（少于 3 字段）跳过。"""
    raw = "abc1234|||fix: bug|||Red\ninvalid_line\ndef5678|||feat|||Ho\n"
    commits = gc.parse_commit_log(raw)
    assert len(commits) == 2


def test_parse_commit_log_sha_truncated_to_9():
    """sha 截断到 9 字符。"""
    raw = "abcdef1234567|||fix: x|||Red\n"
    commits = gc.parse_commit_log(raw)
    assert commits[0]["sha"] == "abcdef123"


def test_parse_commit_log_empty():
    """空输入返回空列表。"""
    assert gc.parse_commit_log("") == []
    assert gc.parse_commit_log("\n\n\n") == []


def test_build_changelog_format():
    """build_changelog 输出含 header + 列表 + footer。"""
    commits = [{"sha": "abc123", "subject": "fix: x", "author": "Red", "cat": "fix"}]
    out = gc.build_changelog(commits, total_commits=1)
    assert "# CHANGELOG — gep-harness" in out
    assert "总 commit 数：1" in out
    assert "最后生成" in out
    assert "abc123" in out
    assert "fix: x" in out


def test_build_changelog_uses_icons():
    """每个 cat 有对应 emoji。"""
    commits = [
        {"sha": "a", "subject": "fix: x", "author": "R", "cat": "fix"},
        {"sha": "b", "subject": "test: y", "author": "R", "cat": "test"},
        {"sha": "c", "subject": "feat: z", "author": "R", "cat": "feat"},
        {"sha": "d", "subject": "ci: w", "author": "R", "cat": "ci"},
        {"sha": "e", "subject": "docs: v", "author": "R", "cat": "docs"},
    ]
    out = gc.build_changelog(commits, 5)
    for icon in ["🐛", "🧪", "✨", "🔧", "📚"]:
        assert icon in out, f"missing icon {icon}"


def test_main_dry_run():
    """main --dry-run 打印但不写盘。"""
    import subprocess, tempfile
    # 用本仓库作为 cwd,跑 dry-run
    result = subprocess.run(
        ["python3", str(REPO / "scripts/generate_changelog.py"), "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    assert result.returncode == 0
    assert "CHANGELOG" in result.stdout


def test_main_since():
    """main --since=v36.0 只取该 commit 之后的。"""
    import subprocess
    result = subprocess.run(
        ["python3", str(REPO / "scripts/generate_changelog.py"), "--since=v36.0", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    assert result.returncode == 0
    # v36.0 之后应该至少有 v36.x / v37 / v38 commit
    assert result.stdout.count("- ") >= 5  # 至少 5 条 commit


def test_run_git_works():
    """run_git 在本仓库能跑 rev-list。"""
    n = gc.run_git("rev-list", "--count", "HEAD")
    assert n.isdigit()
    assert int(n) >= 30  # 至少 30 commits