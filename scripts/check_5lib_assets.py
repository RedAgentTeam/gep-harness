"""5 库产物自动检查 — gep-harness v19.0 A。

扫描 docs/5LIB_GRAPH.* 6 种格式（PNG/SVG/PDF/EPS/MD/DOT）是否齐备 + 时间新鲜度：
- 缺哪种 → 自动调用 visualize_5lib_graph.py 补
- 旧于阈值 → 重新生成全部

跑法：
    python3 scripts/check_5lib_assets.py           # 只检查（不补）
    python3 scripts/check_5lib_assets.py --fix     # 自动补缺
    python3 scripts/check_5lib_assets.py --max-age 600  # 10 min 阈值
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
GRAPHVIZ_FORMATS = ["png", "svg", "pdf", "eps"]  # 4 种需 graphviz
TEXT_FORMATS = ["md", "dot"]  # 2 种纯文本

ALL_FORMATS = GRAPHVIZ_FORMATS + TEXT_FORMATS


def all_assets_exist() -> dict[str, bool]:
    """检查 6 种格式是否都存在。"""
    return {ext: (DOCS / f"5LIB_GRAPH.{ext}").exists() for ext in ALL_FORMATS}


def any_too_old(max_age_seconds: int) -> dict[str, bool]:
    """检查是否有文件超过 max_age_seconds 没更新。"""
    now = time.time()
    result = {}
    for ext in ALL_FORMATS:
        p = DOCS / f"5LIB_GRAPH.{ext}"
        if not p.exists():
            result[ext] = True  # 缺 = 旧
            continue
        age = now - p.stat().st_mtime
        result[ext] = age > max_age_seconds
    return result


def has_graphviz() -> bool:
    return shutil.which("dot") is not None


def regenerate_via_visualize() -> bool:
    """重新调用 visualize_5lib_graph.py 生成全部格式。"""
    if not has_graphviz():
        print("⚠️ graphviz 未安装，跳过 PNG/SVG/PDF/EPS")

    script = REPO / "scripts/visualize_5lib_graph.py"
    if not script.exists():
        print(f"❌ visualize_5lib_graph.py 不存在: {script}")
        return False

    # 1) 生成 Markdown 文本（走 --output 路径）
    md_path = DOCS / "5LIB_GRAPH.md"
    result = subprocess.run(
        [sys.executable, str(script), "--output", str(md_path), "--format", "markdown"],
        capture_output=True, text=True, cwd=REPO,
    )
    if result.returncode != 0:
        print(f"❌ Markdown 生成失败: {result.stderr}")
        return False
    print(f"✅ Markdown 写入: {md_path}")

    # 2) 生成 DOT 文本（直接捕获 stdout，因为 visualize 的 --output 永远写 markdown）
    dot_path = DOCS / "5LIB_GRAPH.dot"
    result = subprocess.run(
        [sys.executable, str(script), "--format", "dot"],
        capture_output=True, text=True, cwd=REPO,
    )
    if result.returncode != 0:
        print(f"❌ DOT 生成失败: {result.stderr}")
        return False
    dot_path.write_text(result.stdout)
    print(f"✅ DOT 写入: {dot_path}")

    # 3) 生成 4 种 graphviz 格式（从 dot 文件直接转，不依赖 visualize 的 --eps 参数）
    if has_graphviz():
        dot_file = DOCS / "5LIB_GRAPH.dot"
        for fmt in GRAPHVIZ_FORMATS:
            out = DOCS / f"5LIB_GRAPH.{fmt}"
            r = subprocess.run(
                ["dot", f"-T{fmt}", str(dot_file), "-o", str(out)],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0 and out.exists():
                print(f"✅ {fmt.upper()} 重新生成")
            else:
                print(f"❌ {fmt.upper()} 失败: {r.stderr.strip()}")
    return True


def check_only(max_age: int) -> int:
    """检查模式：返回 0=全齐 + 新鲜，1=缺或旧。"""
    exists = all_assets_exist()
    old = any_too_old(max_age)
    missing = [ext for ext, ok in exists.items() if not ok]
    stale = [ext for ext, ok in old.items() if ok]

    print(f"📋 6 格式产物状态（max_age={max_age}s）")
    for ext in ALL_FORMATS:
        p = DOCS / f"5LIB_GRAPH.{ext}"
        if not exists[ext]:
            print(f"  ❌ {ext}: 缺失")
        elif old[ext]:
            age = int(time.time() - p.stat().st_mtime)
            print(f"  ⚠️ {ext}: 旧（{age}s > {max_age}s）")
        else:
            age = int(time.time() - p.stat().st_mtime)
            print(f"  ✅ {ext}: 新鲜（{age}s）")

    if missing:
        print(f"\n❌ 缺失 {len(missing)} 种: {missing}")
        return 1
    if stale:
        print(f"\n⚠️ 过时 {len(stale)} 种: {stale}")
        return 1
    print("\n✅ 6 格式产物全齐 + 新鲜")
    return 0


def fix(max_age: int) -> int:
    """修复模式：自动补缺或重新生成。"""
    exists = all_assets_exist()
    old = any_too_old(max_age)
    missing = [ext for ext, ok in exists.items() if not ok]
    stale = [ext for ext, ok in old.items() if ok]

    if not missing and not stale:
        print("✅ 6 格式产物全齐 + 新鲜，无需修复")
        return 0

    print(f"🔧 修复: 缺失 {missing}, 旧 {stale}")
    ok = regenerate_via_visualize()
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="自动补缺/重新生成")
    parser.add_argument("--max-age", type=int, default=3600, help="新鲜度阈值（秒），默认 1h")
    args = parser.parse_args()

    if args.fix:
        return fix(args.max_age)
    return check_only(args.max_age)


if __name__ == "__main__":
    sys.exit(main())
