"""5 库关联强度图谱可视化 — v23.0 v9.0 升级。

输入：LIBRARY_GRAPH_EDGE（cross_library_auto.py）
输出：ASCII + Markdown + DOT + PNG + SVG + PDF（6 种格式）
+ 自动嵌入 ROADMAP_INDEX.md

跑法：
    python3 scripts/visualize_5lib_graph.py
    python3 scripts/visualize_5lib_graph.py --png --svg --pdf
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cross_library_auto import LIBRARY_GRAPH_EDGE, LIBRARY_CHAPTER

LIBS = ["BeautifulMathematics", "cell-biology", "CognitivePsychology", "OpenStaxBiology", "evomap"]


def render_ascii_matrix() -> str:
    lines = ["5 库关联强度矩阵 (v5.0)\n"]
    header = "From \\ To".ljust(20) + "".join(lib[:6].ljust(8) for lib in LIBS)
    lines.append(header)
    lines.append("-" * len(header))
    for src in LIBS:
        row = src[:18].ljust(20)
        for tgt in LIBS:
            weight = LIBRARY_GRAPH_EDGE.get(src, {}).get(tgt, 0.0)
            row += f"{weight:.2f}".ljust(8)
        lines.append(row)
    return "\n".join(lines)


def render_markdown_table() -> str:
    lines = ["# 5 库关联强度图谱（v5.0）\n"]
    lines.append("| From \\ To | " + " | ".join(LIBS) + " |")
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


def render_via_graphviz(dot_content: str, fmt: str, output_path: Path) -> bool:
    if not shutil.which("dot"):
        return False
    result = subprocess.run(
        ["dot", f"-T{fmt}", "-o", str(output_path)],
        input=dot_content, capture_output=True, text=True, timeout=15,
    )
    return result.returncode == 0 and output_path.exists()


def embed_into_roadmap_index(repo: Path) -> bool:
    """自动嵌入 PNG/SVG/PDF 引用到 ROADMAP_INDEX.md。"""
    index = repo / "docs/ROADMAP_INDEX.md"
    if not index.exists():
        return False
    content = index.read_text()
    # 在文件末尾追加可视化引用段（避免重复）
    if "5LIB_GRAPH.png" in content:
        return False
    block = [
        "",
        "## 5 库关联图谱（v9.0 自动嵌入）",
        "",
        "| 格式 | 文件 | 大小 |",
        "|---|---|---|",
    ]
    for fmt, ext in [("PNG", "png"), ("SVG", "svg"), ("PDF", "pdf")]:
        p = repo / f"docs/5LIB_GRAPH.{ext}"
        if p.exists():
            size = p.stat().st_size
            block.append(f"| {fmt} | `5LIB_GRAPH.{ext}` | {size} bytes |")
    block.append("")
    index.write_text(content + "\n".join(block))
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, help="输出 Markdown 文件路径")
    parser.add_argument("--png", action="store_true", help="生成 PNG（需 graphviz）")
    parser.add_argument("--svg", action="store_true", help="生成 SVG（需 graphviz）")
    parser.add_argument("--pdf", action="store_true", help="生成 PDF（需 graphviz）")
    parser.add_argument("--embed-index", action="store_true", help="嵌入到 ROADMAP_INDEX.md")
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

    repo = Path(__file__).resolve().parent.parent
    dot_content = render_dot_format()
    for fmt, flag in [("png", args.png), ("svg", args.svg), ("pdf", args.pdf)]:
        if flag:
            out = repo / f"docs/5LIB_GRAPH.{fmt}"
            ok = render_via_graphviz(dot_content, fmt, out)
            print(f"\n{'✅' if ok else '❌'} {fmt.upper()}: {out}")

    if args.embed_index:
        ok = embed_into_roadmap_index(repo)
        print(f"\n{'✅' if ok else '⚠️'} ROADMAP_INDEX.md 嵌入完成")


if __name__ == "__main__":
    main()
