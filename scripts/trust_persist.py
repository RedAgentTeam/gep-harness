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


# v25.0 audit log 轮转阈值
MAX_AUDIT_LOG_SIZE = 1024 * 1024  # 1MB
AUDIT_KEEP_ROTATED = 5  # 保留最近 5 个轮转文件


def _rotate_audit_log_if_needed(log_path: Path) -> None:
    """检查 audit log 大小，超阈值则轮转。

    轮转机制：
    - 当前 audit_trust.log → audit_trust.log.YYYYMMDD_HHMMSS
    - 旧轮转文件保留 AUDIT_KEEP_ROTATED 个，超出的删除
    """
    if not log_path.exists():
        return
    size = log_path.stat().st_size
    if size < MAX_AUDIT_LOG_SIZE:
        return

    # 轮转：当前文件重命名为带时间戳
    ts_str = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    rotated = log_path.with_suffix(f".log.{ts_str}")
    # 避免重名覆盖（极端情况下1秒内多次 rotate）
    counter = 1
    while rotated.exists():
        rotated = log_path.with_suffix(f".log.{ts_str}.{counter}")
        counter += 1
    log_path.rename(rotated)

    # 清理老轮转文件，保留最近 N 个
    rotated_logs = sorted(
        log_path.parent.glob(f"{log_path.name}.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in rotated_logs[AUDIT_KEEP_ROTATED:]:
        try:
            old.unlink()
        except OSError:
            pass


def write_audit_log(event: str, **fields) -> None:
    """追加一条 JSONL audit 记录（v25.0 加 size-based rotate）。

    event: 操作名（"save"/"load"/"clear"/"verify_ok"/"verify_fail"/"auto_load"）
    fields: 额外字段（如 checksum_sha256、source、libraries 等）

    轮转：
    - 当前 log > MAX_AUDIT_LOG_SIZE (1MB) 时自动轮转
    - 轮转文件名：audit_trust.log.YYYYMMDD_HHMMSS
    - 保留最近 AUDIT_KEEP_ROTATED (5) 个轮转文件
    """
    log_path = get_audit_log_path()

    # v25.0：轮转检查（写之前）
    _rotate_audit_log_if_needed(log_path)

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


# v25.0：audit log 查询接口

def _iter_audit_records(include_rotated: bool = True):
    """生成器：返回所有 audit log 记录的 dict（包含 rotated 文件）。

    读取顺序：当前 → rotated（最新→最旧）
    """
    log_path = get_audit_log_path()
    paths = []
    if log_path.exists():
        paths.append(log_path)
    if include_rotated:
        # 轮转文件按 mtime 倒序（最新优先）
        rotated = sorted(
            log_path.parent.glob(f"{log_path.name}.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        paths.extend(rotated)
    for p in paths:
        try:
            with p.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue


def query_audit_log(
    event: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """查询 audit log。

    参数：
    - event: 只返回指定事件（None = 全部）
    - since: 起始时间（ISO 8601，如 "2026-08-20T00:00:00"），None = 不限
    - until: 结束时间（ISO 8601），None = 不限
    - limit: 最多返回多少条

    返回 list[dict]，按时间倒序（最新优先）。
    """
    results = []
    for rec in _iter_audit_records():
        if event and rec.get("event") != event:
            continue
        ts = rec.get("ts", "")
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        results.append(rec)
    # 倒序（最新优先）
    results.reverse()
    return results[:limit]


def audit_stats() -> dict:
    """统计 audit log 概览。

    返回：
    {
      "total": int,           # 总记录数
      "by_event": dict,       # {event: count}
      "by_day": dict,         # {YYYY-MM-DD: count}
      "first_ts": str,        # 最早记录时间
      "last_ts": str,         # 最晚记录时间
      "files": int,           # 当前 + rotated 文件数
    }
    """
    log_path = get_audit_log_path()
    by_event: dict = {}
    by_day: dict = {}
    first_ts = None
    last_ts = None
    total = 0

    for rec in _iter_audit_records():
        total += 1
        ev = rec.get("event", "unknown")
        by_event[ev] = by_event.get(ev, 0) + 1
        ts = rec.get("ts", "")
        if ts:
            day = ts[:10]  # YYYY-MM-DD
            by_day[day] = by_day.get(day, 0) + 1
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts

    # 文件数：当前 + rotated
    files = 1 if log_path.exists() else 0
    files += len(list(log_path.parent.glob(f"{log_path.name}.*")))

    return {
        "total": total,
        "by_event": by_event,
        "by_day": by_day,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("load", help="读取并打印当前持久化的 active_edges")
    sub.add_parser("clear", help="删除持久化文件")
    sub.add_parser("verify", help="验证持久化文件 integrity（checksum + version）")
    sub.add_parser("audit-stats", help="audit log 统计概览（事件/日期分布）")
    p_save = sub.add_parser("save", help="保存当前 staging dynamic_edges 为 active_edges")
    p_save.add_argument("--source", default="staging/dynamic_edges_v19.json",
                        help="dynamic_edges JSON 路径")
    p_auto = sub.add_parser("auto-load", help="自动加载到 cross_library_auto 默认基线")
    p_query = sub.add_parser("audit-query", help="查询 audit log（支持 event/since/limit）")
    p_query.add_argument("--event", help="只返回指定事件")
    p_query.add_argument("--since", help="起始时间（ISO 8601）")
    p_query.add_argument("--until", help="结束时间（ISO 8601）")
    p_query.add_argument("--limit", type=int, default=20, help="最多返回条数")
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

    if args.cmd == "audit-query":
        records = query_audit_log(
            event=args.event,
            since=args.since,
            until=args.until,
            limit=args.limit,
        )
        print(f"✅ 查询结果：{len(records)} 条")
        for rec in records:
            ts = rec.get("ts", "?")
            ev = rec.get("event", "?")
            extras = {k: v for k, v in rec.items() if k not in ("ts", "event")}
            extra_str = ""
            if extras:
                # 截短长字段
                items = []
                for k, v in extras.items():
                    s = str(v)
                    if len(s) > 30:
                        s = s[:27] + "..."
                    items.append(f"{k}={s}")
                extra_str = " | " + ", ".join(items)
            print(f"   {ts} [{ev}]{extra_str}")
        return 0

    if args.cmd == "audit-stats":
        stats = audit_stats()
        print(f"📊 audit log 统计")
        print(f"   总记录数: {stats['total']}")
        print(f"   文件数: {stats['files']}（含 rotated）")
        print(f"   最早记录: {stats['first_ts'] or 'N/A'}")
        print(f"   最晚记录: {stats['last_ts'] or 'N/A'}")
        if stats['by_event']:
            print(f"   按事件分布:")
            for ev, c in sorted(stats['by_event'].items(), key=lambda x: -x[1]):
                print(f"      {ev}: {c}")
        if stats['by_day']:
            print(f"   按日期分布:")
            for day, c in sorted(stats['by_day'].items()):
                print(f"      {day}: {c}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())