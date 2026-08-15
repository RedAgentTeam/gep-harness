"""Example 07 — PNG + SVG 双格式可视化演示。

本脚本演示 gep-harness v22.0 的双格式可视化能力：
1. 一次调用生成 PNG + SVG（同一 DOT 源）
2. 验证文件存在 + magic bytes
3. 显示尺寸对比

跑法：
    python3 examples/07_png_svg_demo.py

依赖：graphviz (apt-get install -y graphviz)
"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def main() -> None:
    print("=== Example 07: PNG + SVG 双格式可视化 ===\n")

    # 1. 检查 graphviz
    dot = subprocess.run(["which", "dot"], capture_output=True, text=True)
    if not dot.stdout.strip():
        print("❌ graphviz 未装，跑：apt-get install -y graphviz")
        return
    print(f"Step 1: graphviz 已装 ({dot.stdout.strip()})")

    # 2. 一次调用生成双格式
    print("\nStep 2: 一次调用生成 PNG + SVG")
    result = subprocess.run(
        ["python3", "scripts/visualize_5lib_graph.py",
         "--png=docs/5LIB_GRAPH.png",
         "--svg=docs/5LIB_GRAPH.svg"],
        cwd=REPO, capture_output=True, text=True, timeout=15,
    )
    print(result.stdout)

    # 3. 验证双格式
    print("Step 3: 验证双格式")
    for fmt, path in [("PNG", REPO / "docs/5LIB_GRAPH.png"),
                       ("SVG", REPO / "docs/5LIB_GRAPH.svg")]:
        if path.exists():
            size = path.stat().st_size
            magic = path.read_bytes()[:8]
            ok = (fmt == "PNG" and magic[:4] == b"\x89PNG") or \
                 (fmt == "SVG" and b"<svg" in path.read_bytes()[:500])
            print(f"  {'✅' if ok else '❌'} {fmt}: {path.name} ({size} bytes)")

    # 4. 尺寸对比
    print("\nStep 4: 尺寸对比")
    png_size = (REPO / "docs/5LIB_GRAPH.png").stat().st_size
    svg_size = (REPO / "docs/5LIB_GRAPH.svg").stat().st_size
    print(f"  PNG: {png_size} bytes (位图)")
    print(f"  SVG: {svg_size} bytes (矢量)")
    print(f"  PNG/SVG ratio: {png_size/svg_size:.1f}x (SVG 更小)")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
