"""trust query — gep-harness v52.0。

trust audit 可视化（只读，不修改状态）：
- query <gene_id>   → 单个 gene 的 trust_score / verify 次数 / 最近 audit
- stats             → 全量 gene 统计
- stale --days N    → 列出 N 天内未 verify 的 gene

数据源：
- plan/genes/*.json（gene 定义 + asset_id）
- audit_trust.log（JSONL append-only）
- active_edges.json（持久化的 dynamic edges）
- events.jsonl（事件流）

跑法：
    python3 scripts/trust_query.py query gene_exec
    python3 scripts/trust_query.py stats
    python3 scripts/trust_query.py stale --days 7
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _get_active_edges() -> tuple[dict | None, dict | None]:
    """读取持久化的 active_edges，返回 (edges_dict, raw_meta)。"""
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    target = Path(xdg) / "gep-harness" / "active_edges.json"
    if not target.exists():
        fallback = REPO / ".active_edges.json"
        if fallback.exists():
            target = fallback
        else:
            return None, None
    try:
        data = json.loads(target.read_text())
        return data.get("dynamic_edges"), data
    except (json.JSONDecodeError, OSError):
        return None, None


def _get_audit_log() -> list[dict]:
    """读取 audit_trust.log。"""
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    target = Path(xdg) / "gep-harness" / "audit_trust.log"
    if not target.exists():
        fallback = REPO / "audit_trust.log"
        if not fallback.exists():
            return []
        target = fallback
    return _read_jsonl(target)


def _get_events() -> list[dict]:
    """读取 events.jsonl（实际路径 openclaw-harness/events/events.jsonl）。"""
    candidates = [
        REPO / "openclaw-harness" / "events" / "events.jsonl",
        REPO / "openclaw-harness" / "data" / "events.jsonl",
        REPO / "events.jsonl",
    ]
    for p in candidates:
        if p.exists():
            return _read_jsonl(p)
    return []


def list_genes() -> list[dict]:
    """列出 plan/genes/ 下所有 gene。

    Gene 主键设计：
    - gene_id：人类可读 id（data["id"]，如 "gene_candidate_exec"）
    - asset_id：sha256 内容寻址（data["asset_id"]，如 "sha256:..."）
    - 优先用 id 查；fallback 到 asset_id 前缀匹配
    """
    genes_dir = REPO / "plan" / "genes"
    if not genes_dir.exists():
        return []
    out = []
    for p in sorted(genes_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        gid = data.get("id") or p.stem
        out.append({
            "gene_id": gid,
            "asset_id": data.get("asset_id"),
            "signals": data.get("signals_match", []),
            "category": data.get("category", ""),
            "summary": (data.get("strategy") or [""])[0] if isinstance(data.get("strategy"), list) else str(data.get("strategy", "")),
            "path": str(p.relative_to(REPO)),
        })
    return out


def compute_trust(gene_signals: list[str], summary: str, edges: dict | None, library: str = "BeautifulMathematics") -> float | None:
    """调 cross_library_auto.trust_score（取指定 library）。"""
    if not gene_signals:
        return None
    try:
        from cross_library_auto import trust_score, LIBRARY_GRAPH_EDGE
    except ImportError:
        return None
    try:
        base_edges = edges if edges else LIBRARY_GRAPH_EDGE
        return trust_score(library, gene_signals, summary, base_edges)
    except Exception:
        return None


def get_gene_verify_count(gene_id: str, events: list[dict]) -> int:
    """从 events.jsonl 数 verify 次数（event.kind == 'verify' 且含 gene_id）。"""
    count = 0
    for e in events:
        kind = e.get("kind") or e.get("type") or ""
        if "verify" not in str(kind).lower():
            continue
        # 多种字段兼容
        for k in ("gene_id", "asset_id", "target", "name"):
            v = e.get(k)
            if v == gene_id:
                count += 1
                break
    return count


def get_last_audit(gene_id: str, audit_log: list[dict]) -> dict | None:
    """从 audit_trust.log 找最近一条匹配 gene_id 的记录。"""
    matches = [a for a in audit_log if a.get("gene_id") == gene_id or a.get("asset_id") == gene_id]
    if not matches:
        return None
    return matches[-1]


def _resolve_gene(genes: list[dict], gene_id: str) -> dict | None:
    """按 gene_id 或 asset_id 前缀查找。"""
    for g in genes:
        if g["gene_id"] == gene_id:
            return g
        if g["asset_id"] and g["asset_id"].startswith(gene_id):
            return g
    # 模糊匹配（id 包含）
    for g in genes:
        if gene_id in g["gene_id"]:
            return g
    return None


def cmd_query(gene_id: str) -> int:
    genes = list_genes()
    target = _resolve_gene(genes, gene_id)
    if target is None:
        print(f"❌ gene 不存在: {gene_id}")
        print(f"   可用 gene: {[g['gene_id'] for g in genes[:5]]}...（共 {len(genes)} 个）")
        return 1

    edges, meta = _get_active_edges()
    audit_log = _get_audit_log()
    events = _get_events()

    score = compute_trust(target["signals"], target["summary"], edges)
    verify_count = get_gene_verify_count(gene_id, events)
    last_audit = get_last_audit(target["gene_id"], audit_log)

    print(f"📊 Gene: {target['gene_id']}")
    print(f"   asset_id: {target['asset_id']}")
    print(f"   category: {target['category']}")
    print(f"   signals: {target['signals']}")
    print(f"   trust_score: {score}")
    print(f"   verify_count: {verify_count}")
    print(f"   active_edges: {'dynamic' if edges else 'static'}")
    if meta and meta.get("applied_at"):
        print(f"   edges_applied_at: {meta['applied_at']}")
    if last_audit:
        print(f"   last_audit: {last_audit.get('action', '?')} @ {last_audit.get('timestamp', '?')}")
    else:
        print(f"   last_audit: (无)")
    return 0


def cmd_stats() -> int:
    genes = list_genes()
    edges, meta = _get_active_edges()
    audit_log = _get_audit_log()
    events = _get_events()

    scores = []
    verify_counts = []
    no_audit = 0
    for g in genes:
        s = compute_trust(g["signals"], g["summary"], edges)
        if s is not None:
            scores.append(s)
        vc = get_gene_verify_count(g["asset_id"] or g["gene_id"], events)
        verify_counts.append(vc)
        if not get_last_audit(g["gene_id"], audit_log):
            no_audit += 1

    print(f"📊 Trust Audit Stats")
    print(f"   total_genes: {len(genes)}")
    print(f"   scores_computed: {len(scores)}")
    if scores:
        print(f"   trust_score: min={min(scores):.3f} max={max(scores):.3f} mean={sum(scores)/len(scores):.3f}")
    if verify_counts:
        print(f"   verify_count: min={min(verify_counts)} max={max(verify_counts)} mean={sum(verify_counts)/len(verify_counts):.1f}")
    print(f"   no_audit_gene: {no_audit}/{len(genes)}")
    print(f"   active_edges: {'dynamic' if edges else 'static'}")
    if meta and meta.get("applied_at"):
        print(f"   edges_applied_at: {meta['applied_at']}")
    print(f"   audit_log_entries: {len(audit_log)}")
    print(f"   events_total: {len(events)}")
    return 0


# 主入口子命令注册（保持 main 单一）
def _run_subcmd(name: str, args: argparse.Namespace) -> int:
    if name == "query":
        return cmd_query(args.gene_id)
    if name == "stats":
        return cmd_stats()
    if name == "stale":
        return cmd_stale(args.days)
    return 0


def cmd_stale(days: int) -> int:
    """列出 N 天内未 verify 的 gene。"""
    genes = list_genes()
    events = _get_events()

    # 找每个 gene 最后一次 verify 时间
    last_verify = {}
    for e in events:
        kind = e.get("kind") or e.get("type") or ""
        if "verify" not in str(kind).lower():
            continue
        ts = e.get("timestamp") or e.get("ts") or e.get("time")
        for k in ("gene_id", "asset_id", "target", "name"):
            v = e.get(k)
            if v:
                # 取最大（最近）
                if v not in last_verify or (ts and ts > last_verify[v]):
                    last_verify[v] = ts

    now = datetime.now(timezone.utc)
    stale = []
    for g in genes:
        gid = g["gene_id"]
        ts = last_verify.get(gid)
        if not ts:
            stale.append((gid, "never"))
            continue
        # 尝试解析 ISO 时间
        try:
            last_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if (now - last_dt).days > days:
                stale.append((gid, str(ts)))
        except (ValueError, TypeError):
            stale.append((gid, f"unparseable:{ts}"))

    if not stale:
        print(f"✅ 所有 gene 都在 {days} 天内 verify 过")
        return 0

    print(f"⚠️  {len(stale)} 个 gene 超过 {days} 天未 verify:")
    for gid, when in sorted(stale, key=lambda x: x[1]):
        print(f"   - {gid} (last: {when})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="trust audit 可视化查询")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_query = sub.add_parser("query", help="查询单个 gene 的 trust 信息")
    p_query.add_argument("gene_id", help="gene asset_id 或文件名（去 .json）")

    sub.add_parser("stats", help="全量 gene 统计")

    p_stale = sub.add_parser("stale", help="列出 N 天内未 verify 的 gene")
    p_stale.add_argument("--days", type=int, default=7, help="天数阈值（默认 7）")

    args = parser.parse_args()

    if args.cmd == "query":
        return cmd_query(args.gene_id)
    elif args.cmd == "stats":
        return cmd_stats()
    elif args.cmd == "stale":
        return cmd_stale(args.days)
    return 0


if __name__ == "__main__":
    sys.exit(main())