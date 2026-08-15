"""Example 04 — pytest 集成 + 跨库示例。

本脚本演示 gep-harness 测试覆盖：
1. 跑全部 pytest 测试
2. 显示 5 库 evidence 闭环验证
3. 列出跨学科关联强度

跑法：
    python3 examples/04_pytest_integration.py
"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=60)


def main() -> None:
    print("=== Example 04: pytest 集成 + 跨库示例 ===\n")

    # 1. 跑 pytest
    print("Step 1: pytest 全量测试")
    result = run(["python3", "-m", "pytest", "scripts/tests/", "openclaw-a2a/tests/", "-q"])
    passed = result.stdout.count("passed")
    failed = result.stdout.count("failed")
    print(f"  passed: {passed}\n  failed: {failed}\n")

    # 2. 5 库 evidence 闭环
    print("Step 2: 5 库 evidence v3.0 闭环验证")
    sys.path.insert(0, str(REPO / "scripts"))
    from cross_library_auto import auto_cross_library_evidence
    import json
    gene = json.load(open(REPO / "plan/genes/gene_candidate_000_hot_path:exec.json"))
    ev = auto_cross_library_evidence(gene, version="v3.0")
    libs_referenced = set()
    for e in ev:
        for lib in ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]:
            if f"[{lib}" in e:
                libs_referenced.add(lib)
    print(f"  5 库闭环: {libs_referenced == set(['BeautifulMathematics', 'cell-biology', 'CognitivePsychology', 'OpenStaxBiology', 'evomap'])}\n")

    # 3. 跨学科关联强度
    print("Step 3: 跨学科关联强度矩阵")
    from cross_library_auto import LIBRARY_GRAPH_EDGE
    for src, edges in LIBRARY_GRAPH_EDGE.items():
        print(f"  {src}:")
        for tgt, weight in edges.items():
            if src != tgt:
                print(f"    → {tgt}: {weight}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()