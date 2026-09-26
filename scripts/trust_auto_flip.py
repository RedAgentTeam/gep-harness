"""trust auto-flip — gep-harness v53.0。

成功切换或恢复静态基线后，向 openclaw-harness/events/events.jsonl
追加一条 kind=trust_audit 的 append-only 事件。dry-run 不写事件。

v22.0 行为保留：

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

    # v23.0：清除持久化标记
    try:
        from trust_persist import clear_active_edges, get_persist_path
        if clear_active_edges():
            print(f"💾 已清除持久化文件: {get_persist_path()}")
    except Exception as e:
        print(f"⚠️ 清除持久化失败: {e}")

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

    # v23.0：持久化到 active_edges.json
    try:
        from trust_persist import save_active_edges, get_persist_path
        persist_path = save_active_edges(edges, source=str(edges_path))
        print(f"💾 已持久化 → {persist_path}")
    except Exception as e:
        print(f"⚠️ 持久化失败: {e}")

    if verify_flip():
        return 0
    return 1


def emit_trust_audit(
    action: str,
    *,
    ok: bool,
    library_count: int = 0,
    source: str | None = None,
    path: Path | None = None,
) -> dict:
    """Append one trust-flip audit line to the append-only event stream.

    v53: auto-flip must leave a trace in events.jsonl, not only in the process
    and the persist file. Dry-run callers should not call this.
    """
    bin_dir = REPO / "openclaw-harness" / "bin"
    if str(bin_dir) not in sys.path:
        sys.path.insert(0, str(bin_dir))
    from event_emitter import emit

    stream = path or (REPO / "openclaw-harness" / "events" / "events.jsonl")
    return emit(
        session_id="trust-audit",
        kind="trust_audit",
        tool_name="trust_auto_flip",
        result={
            "action": action,
            "ok": ok,
            "libraries": library_count,
            "source": source,
        },
        path=stream,
    )


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
        rc = restore_static()
        if rc == 0:
            emit_trust_audit("restore_static", ok=True, library_count=0, source="static")
        return rc

    edges_path = Path(args.edges_path)
    rc = flip(edges_path, dry_run=args.dry_run)
    if rc == 0 and not args.dry_run:
        edges = load_dynamic_edges(edges_path) or {}
        emit_trust_audit(
            "flip_dynamic",
            ok=True,
            library_count=len(edges),
            source=edges_path.name,
        )
    return rc


if __name__ == "__main__":
    sys.exit(main())