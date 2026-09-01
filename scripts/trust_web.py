"""trust web — gep-harness v52.0。

trust audit Web UI（Flask，只读）：
- GET /                 → 全量 gene 列表 + trust_score + 审计标记
- GET /gene/<gene_id>   → 单个 gene 详情（score / verify_count / last_audit）
- GET /stats            → 统计（分布 + 长期未 verify 名单）
- GET /health           → 健康检查

端口：默认 8765（避免和 goAPI 3000 / caddy 443 / sshd 22 冲突）

跑法：
    python3 scripts/trust_web.py            # 端口 8765
    python3 scripts/trust_web.py --port 9000
    python3 scripts/trust_web.py --debug    # 启用 Flask debug
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from flask import Flask, jsonify, abort  # noqa: E402

# 复用 trust_query 的查询函数（保证 CLI 和 Web 一致）
from trust_query import (  # noqa: E402
    list_genes,
    _get_active_edges,
    _get_audit_log,
    _get_events,
    compute_trust,
    get_gene_verify_count,
    get_last_audit,
    _resolve_gene,
)

app = Flask(__name__)


def _enrich_genes() -> list[dict]:
    """给每个 gene 加 trust_score / verify_count / has_audit。"""
    edges, _ = _get_active_edges()
    audit_log = _get_audit_log()
    events = _get_events()

    out = []
    for g in list_genes():
        score = compute_trust(g["signals"], g["summary"], edges)
        vc = get_gene_verify_count(g["asset_id"] or g["gene_id"], events)
        last = get_last_audit(g["gene_id"], audit_log)
        out.append({
            "gene_id": g["gene_id"],
            "asset_id": g["asset_id"],
            "category": g["category"],
            "signals": g["signals"],
            "trust_score": score,
            "verify_count": vc,
            "has_audit": last is not None,
            "last_audit": last,
        })
    return out


@app.route("/")
def index():
    """全量 gene 列表 + trust_score。"""
    genes = _enrich_genes()
    # 按 trust_score 倒序
    genes.sort(key=lambda g: (g["trust_score"] is None, -(g["trust_score"] or 0)))
    return jsonify({
        "total": len(genes),
        "active_edges_dynamic": _get_active_edges()[0] is not None,
        "genes": genes,
    })


@app.route("/gene/<gene_id>")
def gene_detail(gene_id: str):
    """单个 gene 详情。"""
    target = _resolve_gene(list_genes(), gene_id)
    if target is None:
        abort(404, description=f"gene 不存在: {gene_id}")

    edges, meta = _get_active_edges()
    audit_log = _get_audit_log()
    events = _get_events()

    score = compute_trust(target["signals"], target["summary"], edges)
    verify_count = get_gene_verify_count(target["asset_id"] or target["gene_id"], events)
    last_audit = get_last_audit(target["gene_id"], audit_log)

    return jsonify({
        "gene_id": target["gene_id"],
        "asset_id": target["asset_id"],
        "category": target["category"],
        "signals": target["signals"],
        "summary": target["summary"],
        "trust_score": score,
        "verify_count": verify_count,
        "active_edges": "dynamic" if edges else "static",
        "active_edges_meta": meta,
        "last_audit": last_audit,
        "path": target["path"],
    })


@app.route("/stats")
def stats():
    """统计视图。"""
    genes = _enrich_genes()
    edges, meta = _get_active_edges()

    scores = [g["trust_score"] for g in genes if g["trust_score"] is not None]
    verify_counts = [g["verify_count"] for g in genes]
    no_audit = sum(1 for g in genes if not g["has_audit"])

    # trust_score 分布（0.0~0.2 / 0.2~0.4 / 0.4~0.6 / 0.6~0.8 / 0.8~1.0）
    bins = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for s in scores:
        if s < 0.2:
            bins["0.0-0.2"] += 1
        elif s < 0.4:
            bins["0.2-0.4"] += 1
        elif s < 0.6:
            bins["0.4-0.6"] += 1
        elif s < 0.8:
            bins["0.6-0.8"] += 1
        else:
            bins["0.8-1.0"] += 1

    # 长期未 verify 名单
    stale = [g for g in genes if g["verify_count"] == 0 and not g["has_audit"]]

    return jsonify({
        "total_genes": len(genes),
        "scores_computed": len(scores),
        "trust_score": {
            "min": min(scores) if scores else None,
            "max": max(scores) if scores else None,
            "mean": round(sum(scores) / len(scores), 4) if scores else None,
            "bins": bins,
        },
        "verify_count": {
            "min": min(verify_counts) if verify_counts else 0,
            "max": max(verify_counts) if verify_counts else 0,
            "mean": round(sum(verify_counts) / len(verify_counts), 2) if verify_counts else 0,
        },
        "no_audit_gene": no_audit,
        "stale_genes": [g["gene_id"] for g in stale],
        "active_edges": "dynamic" if edges else "static",
        "active_edges_meta": meta,
        "audit_log_entries": len(_get_audit_log()),
        "events_total": len(_get_events()),
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "trust_web", "version": "v52.0"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not_found", "description": str(e.description)}), 404


def main():
    parser = argparse.ArgumentParser(description="trust audit Web UI")
    parser.add_argument("--port", type=int, default=8765, help="监听端口（默认 8765）")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    parser.add_argument("--debug", action="store_true", help="启用 Flask debug")
    args = parser.parse_args()

    print(f"🌐 trust_web v52.0: http://{args.host}:{args.port}")
    print(f"   路由: / /gene/<id> /stats /health")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()