"""Example 02 — 5 库 evidence v3.0 自动生成。

本脚本演示 gep-harness 的跨学科 5 库映射：
1. 加载 Gene JSON
2. 用 cross_library_auto 生成 v3.0 evidence（含章节号 + 跨库互引）
3. 验证 --validate 0 warning

跑法：
    python3 examples/02_cross_library_evidence.py
"""

import sys
sys.path.insert(0, "/data/disk/gep-harness/scripts")

from cross_library_auto import auto_cross_library_evidence, validate_evidence_quality
import json
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def main() -> None:
    print("=== Example 02: 5 库 evidence v3.0 自动生成 ===\n")

    # 1. 挑 1 个候选基因（exec）
    gene_path = REPO / "plan/genes/gene_candidate_000_hot_path:exec.json"
    gene = json.load(open(gene_path))
    print(f"Loaded: {gene['id']}\n")

    # 2. 生成 v3.0 evidence
    print("Generating v3.0 evidence (章节号 + 跨库互引)...\n")
    evidence_v3 = auto_cross_library_evidence(gene, version="v3.0")
    for e in evidence_v3:
        print(f"  • {e}\n")

    # 3. 验证质量
    print("Validating...")
    ok, total, warnings = validate_evidence_quality(gene)
    print(f"  ok: {ok}/{total}")
    print(f"  warnings: {warnings if warnings else 'none'}")

    # 4. 对比 v2.0 vs v3.0
    print("\nv2.0 vs v3.0:")
    evidence_v2 = auto_cross_library_evidence(gene, version="v2.0")
    print(f"  v2.0 avg length: {sum(len(e) for e in evidence_v2) / len(evidence_v2):.0f} chars")
    print(f"  v3.0 avg length: {sum(len(e) for e in evidence_v3) / len(evidence_v3):.0f} chars")
    print(f"  v3.0 includes 闭环: {'→ [' in evidence_v3[0]}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()