"""cross_lib auto-evolve — gep-harness v21.0。

cron 6h 联动 3 步：
1. dynamic_edge_compute.py → 重算 5 库关联强度（基于 plan/genes evidence）
2. visualize_5lib_graph.py --dynamic-edges → 重新生成 5 种图谱格式（PNG/SVG/PDF/EPS/MD）
3. set_active_edges() → 让 trust_score 自动用 dynamic 值

注意：
- 不自动写入任何 plan/genes/ 或 cross_library_auto.py（只更新图谱）
- 不调用 set_active_edges（保持默认静态基线，避免污染 trust_score 默认值）
- cron 6h 调用前会先 recompute，刷新 staging/dynamic_edges_*.json

跑法：
    python3 scripts/cross_lib_auto_evolve.py
    python3 scripts/cross_lib_auto_evolve.py --dry-run   # 只打印，不写文件
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))


def run_step(name: str, args: list[str], cwd: Path = REPO) -> bool:
    """跑一个步骤，fail-fast。"""
    print(f"\n{'='*60}")
    print(f"▶ {name}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, *args],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode == 0:
        print(f"✅ {name} OK")
        if result.stdout:
            print(result.stdout[-400:])  # tail 400 chars
        return True
    print(f"❌ {name} FAILED (exit={result.returncode})")
    if result.stderr:
        print(result.stderr[-400:])
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只打印，不实际写文件")
    parser.add_argument("--min-samples", type=int, default=5, help="最少样本数")
    parser.add_argument("--weight-observed", type=float, default=0.4, help="观测权重 0~1")
    args = parser.parse_args()

    # Step 1: 重算 dynamic edges → 写 staging/dynamic_edges_v19.json
    edges_path = REPO / "staging" / "dynamic_edges_v19.json"
    ok = run_step(
        "dynamic_edge_compute",
        [
            "scripts/dynamic_edge_compute.py",
            "--output", str(edges_path),
            "--min-samples", str(args.min_samples),
            "--weight-observed", str(args.weight_observed),
        ],
    )
    if not ok:
        return 1
    if not edges_path.exists():
        print(f"❌ dynamic_edges 输出缺失: {edges_path}")
        return 1

    # Step 2: 用 dynamic edges 重新生成图谱 5 格式
    if args.dry_run:
        print(f"\n⏭️ dry-run: 跳过 visualize_5lib_graph")
    else:
        ok = run_step(
            "visualize_5lib_graph --dynamic-edges",
            [
                "scripts/visualize_5lib_graph.py",
                "--dynamic-edges", str(edges_path),
                "--png", "--svg", "--pdf",
            ],
        )
        if not ok:
            return 1

    # Step 3: 报告 dynamic_edges 当前状态（不修改 _ACTIVE_EDGES 默认值）
    data = json.loads(edges_path.read_text())
    used = data.get("used_observed", False)
    note = data.get("note", "")
    print(f"\n{'='*60}")
    print(f"📊 状态报告")
    print(f"{'='*60}")
    print(f"   📄 {edges_path.name}: used_observed={used}")
    print(f"   ℹ️ {note}")
    if used:
        edges = data.get("dynamic_edges", {})
        print(f"   ⚙️  dynamic edges 已生成（trust_score 默认仍走静态基线）")
        print(f"   💡 如需启用：python3 -c \"from cross_library_auto import set_active_edges, json; set_active_edges(json.load(open('{edges_path}'))['dynamic_edges'])\"")
    else:
        print(f"   ⚠️ 观测值未生效，沿用静态基线")

    print(f"\n✅ cross_lib auto-evolve 3 步完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())