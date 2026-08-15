"""5 库关联强度图谱可视化 — v17.0 5 库 v5.0 升级。

输入：LIBRARY_GRAPH_EDGE（cross_library_auto.py）
输出：ASCII 矩阵 + Markdown 表格 + DOT 格式（Graphviz 可视化）

跑法：
    python3 scripts/visualize_5lib_graph.py
    python3 scripts/visualize_5lib_graph.py --output=docs/5LIB_GRAPH.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, "/data/disk/gep-harness/scripts")

from cross_library_auto import LIBRARY_GRAPH_EDGE, LIBRARY_CHAPTER

LIBS = ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]


def render_ascii_matrix() -> str:
    """ASCII 5×5 关联强度矩阵。"""
    lines = ["5 库关联强度矩阵 (v5.0)\n"]
    # 表头
    header = "From \\ To".ljust(20) + "".join(lib[:6].ljust(8) for lib in LIBS)
    lines.append(header)
    lines.append("-" * len(header))
    # 行
    for src in LIBS:
        row = src[:18].ljust(20)
        for tgt in LIBS:
            weight = LIBRARY_GRAPH_EDGE.get(src, {}).get(tgt, 0.0)
            row += f"{weight:.2f}".ljust(8)
        lines.append(row)
    return "\n".join(lines)


def render_markdown_table() -> str:
    """Markdown 表格（含章节号）。"""
    lines = ["# 5 库关联强度图谱（v5.0）\n"]
    lines.append("| From \\\\ To | " + " | ".join(LIBS) + " |")
    lines.append("|" + "---|" * (len(LIBS) + 1))
    for src in LIBS:
        row = [src]
        for tgt in LIBS:
            weight = LIBRARY_GRAPH_EDGE.get(src, {}).get(tgt, 0.0)
            row.append(f"{weight:.2f}")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("\n## 章节号映射\n")
    lines.append("| 库 | 章节号 |")
    lines.append("|---|---|")
    for lib, ch in LIBRARY_CHAPTER.items():
        lines.append(f"| {lib} | {ch} |")
    lines.append("\n## 强关联（≥0.85）路径\n")
    for src in LIBS:
        for tgt, w in LIBRARY_GRAPH_EDGE.get(src, {}).items():
            if w >= 0.85 and src != tgt:
                lines.append(f"- {src} → {tgt}: {w:.2f}")
    return "\n".join(lines)


def render_dot_format() -> str:
    """DOT 格式（Graphviz 输入）。"""
    lines = ["digraph G {", "  rankdir=LR;", "  node [shape=box, style=filled, fillcolor=lightblue];"]
    for lib in LIBS:
        label = f"{lib}\\n{LIBRARY_CHAPTER.get(lib, '')}"
        lines.append(f'  "{lib}" [label="{label}"];')
    for src in LIBS:
        for tgt, w in LIBRARY_GRAPH_EDGE.get(src, {}).items():
            if w >= 0.7 and src != tgt:
                lines.append(f'  "{src}" -> "{tgt}" [label="{w:.2f}", penwidth={w * 3}];')
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, help="输出 Markdown 文件路径")
    parser.add_argument("--format", type=str, default="ascii", choices=["ascii", "markdown", "dot"])
    args = parser.parse_args()

    if args.format == "ascii":
        print(render_ascii_matrix())
    elif args.format == "markdown":
        print(render_markdown_table())
    elif args.format == "dot":
        print(render_dot_format())

    if args.output:
        Path(args.output).write_text(render_markdown_table())
        print(f"\n✅ Markdown 写入: {args.output}")


if __name__ == "__main__":
    main()