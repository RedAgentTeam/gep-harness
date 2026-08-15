"""CHANGELOG 自动生成 — gep-harness v30.0。

从 git log 自动提取 commit → CHANGELOG.md。

跑法：
    python3 scripts/generate_changelog.py
    python3 scripts/generate_changelog.py --since=v25.0
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def run_git_log(since: str | None = None, limit: int = 50) -> list[str]:
    """跑 git log 提取 commit。"""
    cmd = ["git", "log", "--oneline", f"-{limit}"]
    if since:
        cmd.append(f"{since}..HEAD")
    result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line]


def categorize_commit(message: str) -> str:
    """按 commit message 关键词分类。"""
    msg = message.lower()
    if "test" in msg or "pytest" in msg:
        return "🧪 测试"
    if "docs" in msg or "roadmap" in msg:
        return "📚 文档"
    if "feat" in msg or "新增" in msg or "upgrade" in msg or "升级" in msg:
        return "✨ 功能"
    if "fix" in msg or "bug" in msg:
        return "🐛 修复"
    if "ci" in msg or "github" in msg:
        return "🔧 CI"
    return "📦 其他"


def render_changelog(commits: list[str]) -> str:
    """渲染 CHANGELOG.md。"""
    lines = [
        "# CHANGELOG — gep-harness",
        "",
        "> 自动生成（git log 提取）",
        f"> 总 commit 数：{len(commits)}",
        "",
    ]
    # 按 hash 分组
    for line in commits:
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        sha, message = parts
        cat = categorize_commit(message)
        lines.append(f"- {cat} `{sha}` — {message}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=str, help="起始 commit/tag")
    parser.add_argument("--limit", type=int, default=50, help="最大 commit 数")
    parser.add_argument("--output", type=str, default="CHANGELOG.md", help="输出文件")
    args = parser.parse_args()

    commits = run_git_log(since=args.since, limit=args.limit)
    if not commits:
        print("❌ 无 commit")
        return

    changelog = render_changelog(commits)
    out = REPO / args.output
    out.write_text(changelog)
    print(f"✅ CHANGELOG 写入: {out} ({len(commits)} commits)")


if __name__ == "__main__":
    main()
