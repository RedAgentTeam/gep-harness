"""Example 05 — 5 库图谱 PNG 自动生成。

本脚本演示 gep-harness v19.0 的可视化能力：
1. 用 visualize_5lib_graph 生成 DOT
2. 调用 graphviz `dot` 转 PNG
3. 验证 PNG magic bytes

跑法：
    python3 examples/05_png_generation.py

依赖：graphviz (apt-get install -y graphviz)
"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def main() -> None:
    print("=== Example 05: 5 库图谱 PNG 自动生成 ===\n")

    # 1. 检查 graphviz
    print("Step 1: 检查 graphviz")
    dot = subprocess.run(["which", "dot"], capture_output=True, text=True)
    print(f"  dot: {dot.stdout.strip()}")
    if not dot.stdout.strip():
        print("  ❌ graphviz 未装，跑：apt-get install -y graphviz")
        return

    # 2. 生成 DOT
    print("\nStep 2: 生成 DOT")
    dot_content = subprocess.run(
        ["python3", "scripts/visualize_5lib_graph.py", "--format=dot"],
        cwd=REPO, capture_output=True, text=True,
    )
    print(f"  DOT 行数: {len(dot_content.stdout.splitlines())}")

    # 3. 转 PNG
    print("\nStep 3: dot -Tpng 生成 PNG")
    png_path = REPO / "docs/5LIB_GRAPH.png"
    dot_proc = subprocess.run(
        ["dot", "-Tpng", "-o", str(png_path)],
        input=dot_content.stdout,
        capture_output=True, text=True,
    )
    if png_path.exists():
        size = png_path.stat().st_size
        print(f"  ✅ PNG 生成: {png_path} ({size} bytes)")
    else:
        print(f"  ❌ PNG 生成失败: {dot_proc.stderr}")

    # 4. 验证 PNG magic
    print("\nStep 4: 验证 PNG magic bytes")
    with open(png_path, "rb") as f:
        magic = f.read(8)
    if magic[:4] == b"\x89PNG":
        print(f"  ✅ PNG magic 验证通过")
    else:
        print(f"  ❌ PNG magic 错误: {magic[:8]}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()