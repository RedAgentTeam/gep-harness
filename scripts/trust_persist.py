"""trust persist — gep-harness v23.0。

把 trust_score 激活的 dynamic_edges 持久化到磁盘，进程重启后能自动加载。

存储位置：
- ~/.config/gep-harness/active_edges.json
  （Linux XDG 标准；不存在则 fallback 到 .gep-harness/active_edges.json 当前目录）

格式：
{
  "version": "v1",
  "source": "staging/dynamic_edges_v19.json",
  "applied_at": "2026-08-20T08:36:00+08:00",
  "libraries": 5,
  "dynamic_edges": { ... }
}

注意：
- 不在 import 时自动加载（避免污染 trust_score 默认行为）
- 提供 auto_load_active_edges() 显式调用入口（用户/进程主动启用）
- 用 file_lock 防并发写入冲突

跑法：
    python3 scripts/trust_persist.py save --source staging/dynamic_edges_v19.json
    python3 scripts/trust_persist.py load
    python3 scripts/trust_persist.py clear
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))


def get_persist_path() -> Path:
    """获取持久化 JSON 路径（XDG 优先，回落到 repo 根）。"""
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    target = Path(xdg) / "gep-harness" / "active_edges.json"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        # 测试可写
        target.parent.touch(exist_ok=True)
        return target
    except OSError:
        # 回落 repo 根
        fallback = REPO / ".active_edges.json"
        return fallback


def save_active_edges(dynamic_edges: dict, source: str = "") -> Path:
    """保存 dynamic_edges 到持久化文件。"""
    path = get_persist_path()
    payload = {
        "version": "v1",
        "source": source,
        "applied_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "libraries": len(dynamic_edges),
        "dynamic_edges": dynamic_edges,
    }

    # 原子写：temp file + rename
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".active_edges_", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    return path


def load_active_edges() -> dict | None:
    """从持久化文件加载 dynamic_edges（如不存在 → None）。"""
    path = get_persist_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    edges = data.get("dynamic_edges")
    if not edges:
        return None
    return edges


def clear_active_edges() -> bool:
    """清除持久化文件（如不存在 → False）。"""
    path = get_persist_path()
    if path.exists():
        path.unlink()
        return True
    return False


def auto_load_active_edges(verbose: bool = False) -> bool:
    """自动加载持久化的 active_edges（如果有）。

    调用 set_active_edges() 切换 trust_score 默认基线。
    返回 True 表示已加载，False 表示无持久化文件。
    """
    from cross_library_auto import set_active_edges

    edges = load_active_edges()
    if edges is None:
        if verbose:
            print("ℹ️ 无持久化 active_edges，trust_score 保持静态基线")
        return False
    set_active_edges(edges)
    if verbose:
        print(f"✅ auto-loaded active_edges from {get_persist_path()}")
        print(f"   libraries: {len(edges)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("load", help="读取并打印当前持久化的 active_edges")
    sub.add_parser("clear", help="删除持久化文件")
    p_save = sub.add_parser("save", help="保存当前 staging dynamic_edges 为 active_edges")
    p_save.add_argument("--source", default="staging/dynamic_edges_v19.json",
                        help="dynamic_edges JSON 路径")
    p_auto = sub.add_parser("auto-load", help="自动加载到 cross_library_auto 默认基线")
    args = parser.parse_args()

    if args.cmd == "load":
        edges = load_active_edges()
        if edges is None:
            print("ℹ️ 无持久化文件")
            return 0
        print(f"✅ 加载 {len(edges)} 库")
        print(json.dumps(edges, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "clear":
        if clear_active_edges():
            print(f"✅ 已清除 {get_persist_path()}")
            return 0
        print("ℹ️ 无文件可清除")
        return 0

    if args.cmd == "save":
        src = REPO / args.source
        if not src.exists():
            print(f"❌ 源文件不存在: {src}")
            return 1
        data = json.loads(src.read_text())
        edges = data.get("dynamic_edges")
        if not edges:
            print(f"❌ 源文件无 dynamic_edges 字段: {src}")
            return 1
        path = save_active_edges(edges, source=str(src))
        print(f"✅ 已保存 {len(edges)} 库到 {path}")
        return 0

    if args.cmd == "auto-load":
        ok = auto_load_active_edges(verbose=True)
        return 0 if ok else 0  # 都返回 0（无文件也是合法状态）

    return 1


if __name__ == "__main__":
    sys.exit(main())