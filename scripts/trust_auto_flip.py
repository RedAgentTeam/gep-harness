"""trust auto-flip — gep-harness v22.0。

cron 6h 联动：在 cross_lib_auto_evolve 之后，自动让 trust_score 用 dynamic_edges。

行为：
- 读取 staging/dynamic_edges_v19.json
- 提取 dynamic_edges 字段
- 调用 set_active_edges(dynamic_edges) → 全局切换 trust_score 基线
- 验证切换生效（sample trust_score）

回退：
- --restore-static flag → set_active_edges(None) 恢复静态

注意：
- 进程级全局状态：进程结束后丢失（但 cron 6h 每 6h 重新切换）
- 不影响 cross_library_auto.py 默认行为（仅当前进程）

跑法：
    python3 scripts/trust_auto_flip.py             # 切到 dynamic
    python3 scripts/trust_auto_flip.py --restore-static  # 恢复静态
    python3 scripts/trust_auto_flip.py --dry-run   # 只打印，不切换
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

DEFAULT_EDGES_PATH = REPO / "staging" / "dynamic_edges_v19.json"


def load_dynamic_edges(path: Path) -> dict | None:
    """从 dynamic_edge_compute.py 输出的 JSON 读取 dynamic_edges。"""
    if not path.exists():
        print(f"❌ {path} 不存在")
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ {path} 解析失败: {e}")
        return None
    edges = data.get("dynamic_edges")
    if not edges:
        print(f"❌ {path} 无 dynamic_edges 字段")
        return None
    if not data.get("used_observed"):
        print(f"⚠️ {path} 观测值未生效（used_observed=False），跳过切换")
        return None
    return edges


def restore_static() -> int:
    """恢复 trust_score 默认静态基线。"""
    from cross_library_auto import set_active_edges, get_active_edges, LIBRARY_GRAPH_EDGE
    set_active_edges(None)
    if get_active_edges() is LIBRARY_GRAPH_EDGE:
        print("✅ trust_score 已恢复静态基线")
        return 0
    print("❌ 恢复失败")
    return 1


def verify_flip() -> bool:
    """验证 trust_score 已切换到 dynamic。"""
    from cross_library_auto import trust_score, get_active_edges, LIBRARY_GRAPH_EDGE
    if get_active_edges() is LIBRARY_GRAPH_EDGE:
        print("⚠️ 当前仍为静态基线")
        return False
    # 拿 BM trust 作为 sanity check
    ts = trust_score("BeautifulMathematics", ["幂等"], "test")
    print(f"   ✓ trust_score(BM) = {ts:.3f}")
    return True


def flip(edges_path: Path, dry_run: bool = False) -> int:
    """载入 dynamic_edges 并设置 active。"""
    from cross_library_auto import set_active_edges

    edges = load_dynamic_edges(edges_path)
    if edges is None:
        return 1

    if dry_run:
        print(f"⏭️ dry-run: 跳过 set_active_edges")
        print(f"   loaded {len(edges)} libraries from {edges_path}")
        return 0

    set_active_edges(edges)
    print(f"✅ set_active_edges(dynamic_edges) 已应用")
    print(f"   source: {edges_path}")
    print(f"   libraries: {len(edges)}")
    if verify_flip():
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edges-path", type=str, default=str(DEFAULT_EDGES_PATH),
                        help="dynamic_edges JSON 路径")
    parser.add_argument("--restore-static", action="store_true",
                        help="恢复静态基线（紧急回退）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印，不切换")
    args = parser.parse_args()

    if args.restore_static:
        return restore_static()

    return flip(Path(args.edges_path), dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())