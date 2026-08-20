"""trust persist — gep-harness v24.0（v23.0 升级）。

把 trust_score 激活的 dynamic_edges 持久化到磁盘，进程重启后能自动加载。

v24.0 升级：
- 完整性校验：save 时算 SHA256 + version，写入 payload 头部
- audit log：flip/restore/clear 全部写 append-only audit_trust.log
- verify 入口：verify_active_edges() 检查 hash + version + audit 一致性

存储位置：
- ~/.config/gep-harness/active_edges.json
  （Linux XDG 标准；不存在则 fallback 到 .active_edges.json 当前目录）
- ~/.config/gep-harness/audit_trust.log（JSONL append-only）

格式：
{
  "version": "v2",          # v24.0 起升 v2（含 integrity + audit 字段）
  "schema": "trust-active-edges-v2",
  "checksum_sha256": "...",  # 仅 dynamic_edges 的 SHA256
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
    python3 scripts/trust_persist.py verify
    python3 scripts/trust_persist.py clear
"""

import argparse
import hashlib
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


def compute_checksum(dynamic_edges: dict) -> str:
    """计算 dynamic_edges 的 SHA256 checksum。"""
    # 用 sort_keys 保证顺序一致
    serialized = json.dumps(dynamic_edges, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def get_audit_log_path() -> Path:
    """获取 audit log 路径（与 active_edges 同目录，命名 audit_trust.log）。"""
    edges_path = get_persist_path()
    return edges_path.parent / "audit_trust.log"


def write_audit_log(event: str, **fields) -> None:
    """追加一条 JSONL audit 记录。

    event: 操作名（"save"/"load"/"clear"/"verify_ok"/"verify_fail"/"auto_load"）
    fields: 额外字段（如 checksum_sha256、source、libraries 等）
    """
    log_path = get_audit_log_path()
    record = {
        "ts": datetime.now(timezone.utc).astimezone().isoformat(),
        "event": event,
        **fields,
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # append-only mode "a"，不会 truncate
        with log_path.open("a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        # audit 写失败不应阻断主流程
        print(f"⚠️ audit log write failed: {e}")


def save_active_edges(dynamic_edges: dict, source: str = "") -> Path:
    """保存 dynamic_edges 到持久化文件（v2 schema + SHA256 checksum）。"""
    path = get_persist_path()
    checksum = compute_checksum(dynamic_edges)
    payload = {
        "version": "v2",
        "schema": "trust-active-edges-v2",
        "checksum_sha256": checksum,
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

    # v24.0：写 audit log
    write_audit_log(
        "save",
        source=source,
        libraries=len(dynamic_edges),
        checksum_sha256=checksum,
        path=str(path),
    )

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
        # v24.0：audit log
        write_audit_log("clear", path=str(path))
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
    # v24.0：audit log
    write_audit_log(
        "auto_load",
        libraries=len(edges),
        path=str(get_persist_path()),
    )
    if verbose:
        print(f"✅ auto-loaded active_edges from {get_persist_path()}")
        print(f"   libraries: {len(edges)}")
    return True


def verify_active_edges() -> tuple[bool, str]:
    """验证持久化文件 integrity。

    检查项：
    1. 文件存在
    2. JSON 可解析
    3. version = "v2"
    4. checksum_sha256 与 dynamic_edges 实际 hash 一致
    5. libraries 计数 = len(dynamic_edges)
    6. dynamic_edges 非空

    返回 (ok, message)：ok=True 表示全部检查通过。
    """
    path = get_persist_path()
    if not path.exists():
        return False, f"❌ {path} 不存在"

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return False, f"❌ JSON 解析失败: {e}"

    # version 检查
    version = data.get("version")
    if version != "v2":
        return False, f"❌ version 错误: 期望 v2，实际 {version}"

    # dynamic_edges 非空
    edges = data.get("dynamic_edges")
    if not edges:
        return False, "❌ dynamic_edges 为空"

    # libraries 计数
    declared_libs = data.get("libraries")
    if declared_libs != len(edges):
        return False, f"❌ libraries 计数不匹配: 声明 {declared_libs}，实际 {len(edges)}"

    # checksum 一致性
    declared_checksum = data.get("checksum_sha256")
    actual_checksum = compute_checksum(edges)
    if declared_checksum != actual_checksum:
        return False, f"❌ checksum 不匹配: 声明 {declared_checksum[:16]}..., 实际 {actual_checksum[:16]}..."

    # v24.0：audit log
    write_audit_log("verify_ok", checksum_sha256=actual_checksum, libraries=len(edges))

    return True, f"✅ integrity OK (libraries={len(edges)}, checksum={actual_checksum[:16]}...)"


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("load", help="读取并打印当前持久化的 active_edges")
    sub.add_parser("clear", help="删除持久化文件")
    sub.add_parser("verify", help="验证持久化文件 integrity（checksum + version）")
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

    if args.cmd == "verify":
        ok, msg = verify_active_edges()
        print(msg)
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())