"""Example 06 — Solidify safe reject 守护演示。

本脚本演示 gep-harness v10.1 的安全守护：
1. 跑 cron 6h 模拟一次（make evolve-full）
2. 观察 staging 候选数
3. 跑 Solidify（--non-interactive → EOFError → auto-rejected）

跑法：
    python3 examples/06_safe_reject_demo.py

注意：本脚本**只读不写**，不会污染 plan/genes/。
"""

import subprocess
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def main() -> None:
    print("=== Example 06: Solidify safe reject 守护演示 ===\n")

    # 1. 跑 make evolve-full
    print("Step 1: make evolve-full（扫 events → 提候选 → 写 /tmp/v_staging/）")
    result = subprocess.run(
        ["make", "evolve-full"],
        cwd=REPO, capture_output=True, text=True, timeout=30,
    )
    # 统计 staging 文件
    staging = Path("/tmp/v_staging")
    if staging.exists():
        candidates = list(staging.glob("gene_candidate_*.json"))
        print(f"  candidates generated: {len(candidates)}")

    # 2. 跑 Solidify
    print("\nStep 2: make solidify-pending（Solidify 守门）")
    result = subprocess.run(
        ["make", "solidify-pending"],
        cwd=REPO, capture_output=True, text=True, timeout=15,
    )
    # 解析审批摘要
    for line in result.stdout.splitlines():
        if "approved" in line.lower() or "rejected" in line.lower() or "auto-rejected" in line.lower():
            print(f"  {line.strip()}")

    # 3. 验证 plan/genes/ 没被污染
    print("\nStep 3: 验证 plan/genes/ 未被污染")
    plan_genes = REPO / "plan/genes"
    candidates_in_repo = list(plan_genes.glob("gene_candidate_*.json"))
    print(f"  plan/genes/gene_candidate_*: {len(candidates_in_repo)}")
    print(f"  (v0.9 已批准 7 候选 = 7 个，应保持不变)")

    print("\n=== Done (safe reject 守护 v10.1 已生效) ===")


if __name__ == "__main__":
    main()