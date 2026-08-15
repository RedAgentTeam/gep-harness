"""Example 01 — 本机 Evolver 一周期。

本脚本演示 gep-harness 的核心能力：
1. 扫 events.jsonl 找高频 pattern
2. 提取候选 Gene
3. 走 Solidify 守门（手动 y/N）

跑法：
    python3 examples/01_local_evolver.py

注意：本脚本**仅读不写**，Solidify 由人工 y/N 决定。
"""

import sys
import subprocess
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """执行 gep-harness 命令。"""
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def main() -> None:
    print("=== Example 01: 本机 Evolver 一周期 ===\n")

    print("Step 1: 扫描 events.jsonl（24h）")
    result = run(["python3", "scripts/scan_events.py", "--since=24h"])
    print(f"  events scanned: {result.stdout[:200]}")

    print("\nStep 2: 提取候选 Gene（threshold=5）")
    result = run([
        "python3", "scripts/extract_candidate_genes.py",
        "--scan-output=/tmp/v_scan.json",
        "--output=/tmp/v_staging/",
        "--threshold=5"
    ])
    print(f"  candidates: {result.stdout[:200]}")

    print("\nStep 3: GEP strict 校验")
    result = run(["python3", "scripts/cross_library_auto.py", "--validate", "plan/genes/"])
    print(f"  validate: {'0 warning' if '0 个质量警告' in result.stdout else 'warning'}")

    print("\nStep 4: Solidify 守门（人工 y/N）")
    print("  ⚠️  本脚本不自动 Solidify；'y' 批准 'N' 拒绝")
    print("  跑 'make solidify-pending' 看待审候选")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()