"""CHANGELOG 自动 commit — gep-harness v32.0。

跑法：
    python3 scripts/auto_changelog_commit.py --message="auto-update CHANGELOG"

特性：
- 仅在 CHANGELOG 的 commit 数与 HEAD 不一致时提交
- 提交前把 commit 数写成「当前 HEAD + 1」，提交后与 git rev-list 对齐
- 跳过只由上一次 changelog 提交自己引起的列表和时戳变化
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _changelog() -> Path:
    return REPO / "CHANGELOG.md"


def _readme() -> Path:
    return REPO / "README.md"

COUNT_RE = re.compile(r"^(>\s*总 commit 数[：:]\s*)(\d+)\s*$", re.M)
STAMP_RE = re.compile(r"^>\s*最后生成：")
VERSION_RE = re.compile(r"^>\s*版本：v\d")
BULLET_RE = re.compile(r"^- .+`([0-9a-f]{7,})`")


def git_has_changes() -> bool:
    """检查是否有未提交变更。"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO, capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def _read_count(text: str | None) -> int | None:
    if not text:
        return None
    match = COUNT_RE.search(text)
    return int(match.group(2)) if match else None


def _head_changelog() -> str | None:
    result = subprocess.run(
        ["git", "show", "HEAD:CHANGELOG.md"],
        cwd=REPO, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _rev_count() -> int:
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=REPO, capture_output=True, text=True, check=True,
    )
    return int(result.stdout.strip())


def _diff_is_listing_churn(current: str, head: str) -> bool:
    """True when the changelog diff is only count, stamp, version, or cron bullets."""
    import difflib

    diff = difflib.unified_diff(
        head.splitlines(),
        current.splitlines(),
        lineterm="",
    )
    saw = False
    for line in diff:
        if line.startswith(("+++", "---", "@@")):
            continue
        if not line.startswith(("+", "-")):
            continue
        body = line[1:]
        saw = True
        if body.strip() == "":
            continue
        if COUNT_RE.match(body) or STAMP_RE.match(body) or VERSION_RE.match(body):
            continue
        if "auto: cron 6h workflow" in body or "auto: CHANGELOG" in body:
            continue
        bullet = BULLET_RE.match(body)
        if bullet and _commit_is_docs_sync(bullet.group(1)):
            continue
        return False
    return saw


def _commit_is_docs_sync(sha: str) -> bool:
    result = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", sha],
        cwd=REPO, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    allowed = {"CHANGELOG.md", "README.md"}
    return bool(files) and set(files) <= allowed


def _sync_readme(count: int) -> bool:
    readme = _readme()
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    updated, n = re.subn(r"(commit 数\s*\|\s*)\d+", rf"\g<1>{count}", text, count=1)
    if n == 0 or updated == text:
        return False
    readme.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="auto: CHANGELOG 更新", help="commit message")
    args = parser.parse_args()

    changelog = _changelog()
    readme = _readme()
    if not changelog.exists():
        print("⚠️ 无变更，跳过")
        return

    current = changelog.read_text(encoding="utf-8")
    head = _head_changelog()
    if head is not None and current == head:
        print("⚠️ 无变更，跳过")
        return

    cur_count = _read_count(current)
    head_count = _read_count(head)
    if (
        head is not None
        and cur_count is not None
        and cur_count == head_count
        and _diff_is_listing_churn(current, head)
    ):
        subprocess.run(["git", "checkout", "--", "CHANGELOG.md"], cwd=REPO, check=False)
        print("⚠️ 仅 changelog 自更新，跳过")
        return

    to_add = ["CHANGELOG.md"]
    if cur_count is not None:
        nxt = _rev_count() + 1
        updated, n = COUNT_RE.subn(rf"\g<1>{nxt}", current, count=1)
        if n:
            changelog.write_text(updated, encoding="utf-8")
            if _sync_readme(nxt):
                to_add.append("README.md")

    subprocess.run(["git", "add", "--", *to_add], cwd=REPO, check=False)
    result = subprocess.run(
        ["git", "commit", "-m", args.message],
        cwd=REPO, capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"✅ auto-commit: {args.message}")
    else:
        print(f"❌ commit failed: {result.stderr}")


if __name__ == "__main__":
    main()
