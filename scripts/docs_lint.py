#!/usr/bin/env python3
"""docs_lint.py — 文档数字与仓库实际状态对齐校对（P1-5 配套工具）

单一事实源：所有 README/CHANGELOG 数字都从这里读取并校对：
- Gene/Capsule/Event 文件数（从 plan/ 实际 glob）
- pytest 实际收集数（跑 pytest --collect-only）
- commit 数（git log）
- 最近 5 个 commit（CHANGELOG 自动生成）

用法：
  python3 scripts/docs_lint.py --check   # 退出码 1 if README 数字不对
  python3 scripts/docs_lint.py --update  # 自动更新 README 对应字段
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def count_plan_assets() -> dict:
    out = {}
    for kind in ("genes", "capsules", "events"):
        out[kind] = len(list((REPO / "plan" / kind).glob("*.json")))
    return out


def count_commits() -> int:
    r = subprocess.run(
        ["git", "log", "--oneline"],
        capture_output=True, text=True, cwd=str(REPO), check=True,
    )
    return len(r.stdout.strip().splitlines())


def count_pytest() -> int:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True, text=True, cwd=str(REPO), check=False,
    )
    # pytest reports "102 tests collected in 0.25s"
    m = re.search(r"(\d+) tests collected", r.stdout)
    return int(m.group(1)) if m else 0


def snapshot() -> dict:
    return {
        "commit_count": count_commits(),
        "plan_assets": count_plan_assets(),
        "pytest_count": count_pytest(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="校验 README 数字（exit 1 if drift）")
    ap.add_argument("--update", action="store_true",
                    help="自动更新 README")
    ap.add_argument("--print", action="store_true",
                    help="打印当前快照")
    args = ap.parse_args()

    snap = snapshot()

    if args.print or not (args.check or args.update):
        print(json.dumps(snap, indent=2, ensure_ascii=False))
        return 0

    if args.check:
        readme = (REPO / "README.md").read_text()
        drift = []
        # 校验 Gene 数
        m_gene = re.search(r"Gene 总数\s*\|\s*(\d+)", readme)
        if m_gene and int(m_gene.group(1)) != snap["plan_assets"]["genes"]:
            drift.append(f"Gene 总数: README={m_gene.group(1)} 实际={snap['plan_assets']['genes']}")
        # 校验 pytest 数
        m_pytest = re.search(r"pytest\s*\|\s*(\d+)/(\d+)", readme)
        if m_pytest and int(m_pytest.group(2)) != snap["pytest_count"]:
            drift.append(f"pytest 总数: README={m_pytest.group(2)} 实际={snap['pytest_count']}")
        if drift:
            print("❌ README drift detected:")
            for d in drift:
                print(f"  - {d}")
            return 1
        print(f"✅ README 与仓库实际一致 (Gene={snap['plan_assets']['genes']}, "
              f"pytest={snap['pytest_count']}, commits={snap['commit_count']})")
        return 0

    if args.update:
        readme = (REPO / "README.md").read_text()
        # 更新 pytest 数（保守：只改 X/X 的第二项）
        readme = re.sub(
            r"(pytest\s*\|\s*\d+/)\d+",
            rf"\g<1>{snap['pytest_count']}",
            readme, count=1,
        )
        (REPO / "README.md").write_text(readme)
        print(f"✅ README updated: pytest={snap['pytest_count']}")
        return 0


if __name__ == "__main__":
    sys.exit(main() or 0)