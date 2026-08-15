"""CHANGELOG 自动 commit — gep-harness v32.0。

跑法：
    python3 scripts/auto_changelog_commit.py --message="auto-update CHANGELOG"

特性：
- 生成 CHANGELOG.md（如有变更）
- 自动 git add + commit
- 跳过无变更情况
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def git_has_changes() -> bool:
    """检查是否有未提交变更。"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO, capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="auto: CHANGELOG 更新", help="commit message")
    args = parser.parse_args()

    if not git_has_changes():
        print("⚠️ 无变更，跳过")
        return

    # 仅 add CHANGELOG.md（避免误提交其他）
    subprocess.run(["git", "add", "CHANGELOG.md"], cwd=REPO)
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
