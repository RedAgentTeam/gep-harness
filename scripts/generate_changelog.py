#!/usr/bin/env python3
"""
generate_changelog.py — auto-generate CHANGELOG.md from git log.

Single source of truth: CHANGELOG.md first entry sets version/commit_count/pytest.
README 现状区 must match these values (enforced by docs_lint.py).

Usage:
    python3 scripts/generate_changelog.py              # regenerate CHANGELOG
    python3 scripts/generate_changelog.py --dry-run     # print without writing
    python3 scripts/generate_changelog.py --since v36.0  # only new commits
"""

import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
CHANGELOG = REPO / "CHANGELOG.md"

# Category emoji mapping (by commit subject keyword)
CAT_ICONS = {
    "ci": "🔧",
    "test": "🧪",
    "docs": "📚",
    "fix": "🐛",
    "feat": "✨",
    "refactor": "♻️",
    "chore": "📦",
    "perf": "⚡",
    "security": "🔒",
    "dep": "📦",
    "pkg": "📦",
}

CAT_ORDER = ["fix", "feat", "test", "ci", "docs", "refactor", "perf", "security", "chore", "dep", "pkg"]


def run_git(*args):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout.strip()


def categorize(commit_msg: str) -> str:
    subject = commit_msg.split("\n")[0].lower()
    for cat in CAT_ORDER:
        if cat in subject:
            return cat
    return "chore"


def parse_commit_log(raw: str) -> list[dict]:
    """Parse `git log --pretty=format:...` into list of entries."""
    lines = raw.split("\n")
    commits = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        parts = line.split("|||")
        if len(parts) < 3:
            i += 1
            continue
        sha = parts[0][:9]
        subject = parts[1]
        author = parts[2] if len(parts) > 2 else "unknown"
        cat = categorize(subject)
        commits.append({"sha": sha, "subject": subject, "author": author, "cat": cat})
        i += 1
    return commits


def build_changelog(commits: list[dict], total_commits: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# CHANGELOG — gep-harness",
        "",
        "> 自动生成（git log 提取）",
        f"> 总 commit 数：{total_commits}",
        "",
    ]

    for c in commits:
        icon = CAT_ICONS.get(c["cat"], "📦")
        lines.append(f"- {icon} `{c['sha']}` — {c['subject']}")

    lines += ["", f"> 最后生成：{now}", ""]
    return "\n".join(lines)


def main():
    since = None
    dry_run = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--since" and i + 1 < len(args):
            since = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    fmt = "%H|||%s|||%an"
    git_args = ["log", f"--pretty=format:{fmt}"]
    if since:
        git_args.append(f"{since}..HEAD")

    raw = run_git(*git_args)
    commits = parse_commit_log(raw)
    total = int(run_git("rev-list", "--count", "HEAD"))
    changelog = build_changelog(commits, total)

    if dry_run:
        print(changelog)
        return

    CHANGELOG.write_text(changelog)
    print(f"✅ CHANGELOG.md 已更新：{len(commits)} entries, {total} total commits")


if __name__ == "__main__":
    main()
