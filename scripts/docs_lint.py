#!/usr/bin/env python3
"""
docs_lint.py — 文档口径一致性检查。

单一事实源 = CHANGELOG.md 头部元数据。
README 现状区必须与之匹配（版本号、commit 数、pytest）。

Usage:
    python3 scripts/docs_lint.py           # 检查，不修
    python3 scripts/docs_lint.py --fix      # 自动修复 README
    python3 scripts/docs_lint.py --check-changelog  # 只检查 CHANGELOG 是否已生成
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
README = REPO / "README.md"
CHANGELOG = REPO / "CHANGELOG.md"


def run_git(*args):
    result = subprocess.run(
        ["git"] + list(args), cwd=REPO,
        capture_output=True, text=True,
    )
    return result.stdout.strip(), result.returncode


def parse_changelog_header() -> dict:
    """从 CHANGELOG.md 头部提取元数据。"""
    text = CHANGELOG.read_text(encoding="utf-8")
    header = {}
    for line in text.split("\n")[:10]:
        m = re.match(r"^>\s*总 commit 数[：:]\s*(\d+)", line)
        if m:
            header["commit_count"] = int(m.group(1))
    # version from first commit line
    m = re.search(r"v(\d+\.\d+(?:\.\d+)?)", text)
    if m:
        header["version"] = m.group(1)
    return header


def parse_readme_status() -> dict:
    """从 README.md 现状区提取当前值。"""
    text = README.read_text(encoding="utf-8")
    status = {}
    m = re.search(r"版本[：:]\s*v([\d.]+)", text)
    if m:
        status["version"] = m.group(1)
    m = re.search(r"commit 数\s*\|\s*(\d+)", text)
    if m:
        status["commit_count"] = int(m.group(1))
    m = re.search(r"pytest\s*\|\s*(\d+)/(\d+)", text)
    if m:
        status["pytest"] = f"{m.group(1)}/{m.group(2)}"
    return status


def get_actual_pytest() -> str:
    """跑 make test 获取真实 pytest 总数。"""
    result = subprocess.run(
        ["make", "test"],
        cwd=REPO, capture_output=True, text=True, timeout=120,
    )
    # 匹配多行 "N passed"，取总数
    matches = re.findall(r"(\d+)\s+passed", result.stdout)
    if matches:
        total = sum(int(m) for m in matches)
        return f"{total}/{total}"
    return "?"


def lint():
    cl = parse_changelog_header()
    rm = parse_readme_status()
    actual = get_actual_pytest()

    errors = []

    # 1. CHANGELOG 存在
    if not CHANGELOG.exists():
        errors.append("❌ CHANGELOG.md 不存在，运行 python3 scripts/generate_changelog.py")

    # 2. CHANGELOG commit_count vs git rev-list
    git_count_str, _ = run_git("rev-list", "--count", "HEAD")
    git_count = int(git_count_str)
    cl_count = cl.get("commit_count", "?")
    if cl_count != git_count:
        errors.append(
            f"❌ CHANGELOG commit_count={cl_count} ≠ git rev-list={git_count}\n"
            f"   修复：python3 scripts/generate_changelog.py"
        )

    # 3. README 版本 vs CHANGELOG
    if "version" in cl and "version" in rm:
        if cl["version"] != rm["version"]:
            errors.append(
                f"❌ README 版本=v{rm['version']} ≠ CHANGELOG=v{cl['version']}\n"
                f"   修复：python3 scripts/docs_lint.py --fix"
            )

    # 4. README commit 数 vs CHANGELOG
    if "commit_count" in cl and "commit_count" in rm:
        if cl["commit_count"] != rm["commit_count"]:
            errors.append(
                f"❌ README commit_count={rm['commit_count']} ≠ CHANGELOG={cl['commit_count']}\n"
                f"   修复：python3 scripts/docs_lint.py --fix"
            )

    # 5. README pytest vs 实际
    if "pytest" in rm and actual != "?":
        if rm["pytest"] != actual:
            errors.append(
                f"❌ README pytest={rm['pytest']} ≠ 实际={actual}\n"
                f"   修复：python3 scripts/docs_lint.py --fix"
            )

    if errors:
        print("\n".join(errors))
        return 1
    else:
        print("✅ 文档口径一致")
        return 0


def fix_readme():
    """自动修复 README 现状区。"""
    cl = parse_changelog_header()
    actual = get_actual_pytest()
    text = README.read_text(encoding="utf-8")

    # 更新版本号
    text = re.sub(
        r"版本[：:]\s*v[\d.]+（迭代轮次.*?）",
        f"版本：v{cl.get('version', '?')}（自动同步）",
        text,
    )

    # 更新 commit 数
    text = re.sub(
        r"commit 数\s*\|\s*\d+",
        f"commit 数 | {cl.get('commit_count', '?')}",
        text,
    )

    # 更新 pytest
    text = re.sub(
        r"pytest\s*\|\s*\d+/\d+[^\n]*",
        f"pytest | {actual}",
        text,
    )

    README.write_text(text, encoding="utf-8")
    print(f"✅ README.md 已同步：版本=v{cl.get('version','?')} commit={cl.get('commit_count','?')} pytest={actual}")


def main():
    check_only = "--check-changelog" in sys.argv
    if check_only:
        if not CHANGELOG.exists():
            print("❌ CHANGELOG.md 不存在")
            sys.exit(1)
        cl = parse_changelog_header()
        git_count_str, _ = run_git("rev-list", "--count", "HEAD")
        if cl.get("commit_count", -1) != int(git_count_str):
            print(f"❌ CHANGELOG commit_count={cl.get('commit_count')} ≠ git={git_count_str}")
            sys.exit(1)
        print("✅ CHANGELOG 与 git 一致")
        sys.exit(0)

    if "--fix" in sys.argv:
        fix_readme()
        sys.exit(0)

    sys.exit(lint())


if __name__ == "__main__":
    main()
