"""Gene → Capsule 自动绑定 — Stage 5 升级。

按 GEP v1.12.1 协议，Capsule 是"一组相关 Gene 的封装"，用于：
1. 复用一组 Gene 作为整体（如 append-only event_stream + tool_pipeline + evolver）
2. 沉淀经验（success_reason + strategy + execution_trace）
3. A2A 跨节点传递整组能力

本脚本：
1. 扫描 plan/genes/*.json
2. 按 signals_match 关键词相似度聚类（共享 ≥2 signals 的 Gene 一组）
3. 对每组生成 Capsule 草稿（不自动写盘，只输出 --dry-run）
4. 列出已存在 Capsule 与潜在新 Capsule 的覆盖 gap

注意：本脚本**不自动写盘**——Capsule 是经验资产，必须人工审批生成。
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
PLAN_GENES = REPO / "plan" / "genes"
PLAN_CAPSULES = REPO / "plan" / "capsules"
SCHEMA_VERSION = "1.12.1"


def load_genes() -> dict:
    """加载 plan/genes/ 所有 Gene，返回 {gene_id: gene_dict}。"""
    genes = {}
    for f in sorted(PLAN_GENES.glob("*.json")):
        try:
            g = json.load(open(f))
            gid = g.get("id")
            if gid:
                genes[gid] = {**g, "_file": f.name}
        except Exception as e:
            print(f"⚠️  skip {f.name}: {e}")
    return genes


def load_capsules() -> dict:
    """加载 plan/capsules/，返回 {capsule_id: capsule_dict}。"""
    capsules = {}
    for f in sorted(PLAN_CAPSULES.glob("*.json")):
        try:
            c = json.load(open(f))
            cid = c.get("id")
            if cid:
                capsules[cid] = {**c, "_file": f.name}
        except Exception:
            pass
    return capsules


def jaccard(set_a: set, set_b: set) -> float:
    """Jaccard 相似度。"""
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def cluster_genes(genes: dict, threshold: float = 0.4) -> list:
    """按 signals_match Jaccard 相似度聚类 Gene。

    threshold=0.4 表示共享 signals 占比 40% 以上聚为一组。
    返回 [[gene_id1, gene_id2, ...], ...]
    """
    # 提取每 gene 的 signal set（signals_match + signals 兼容）
    gene_signals = {}
    for gid, g in genes.items():
        sigs = set(g.get("signals_match", []) or g.get("signals", []) or [])
        gene_signals[gid] = sigs

    # 简单 union-find 聚类
    parent = {gid: gid for gid in genes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    gids = list(genes.keys())
    for i, gi in enumerate(gids):
        for gj in gids[i + 1:]:
            sim = jaccard(gene_signals[gi], gene_signals[gj])
            if sim >= threshold:
                union(gi, gj)

    # 按 root 收集
    clusters = defaultdict(list)
    for gid in gids:
        root = find(gid)
        clusters[root].append(gid)

    # 只返回 >= 2 gene 的簇（单 gene 不值得打包）
    return [c for c in clusters.values() if len(c) >= 2]


def draft_capsule(cluster_gene_ids: list, genes: dict) -> dict:
    """根据一组 Gene IDs 草拟 Capsule（不写盘）。"""
    cluster_genes = [genes[gid] for gid in cluster_gene_ids]
    # 找主 gene（signals 最多的）
    main_gene = max(cluster_genes, key=lambda g: len(g.get("signals_match", []) or []))

    # 聚合 signals
    all_signals = set()
    for g in cluster_genes:
        all_signals.update(g.get("signals_match", []) or g.get("signals", []) or [])

    # scope 聚合
    scopes = set()
    for g in cluster_genes:
        scopes.update(g.get("scope", []) or [])
    if not scopes:
        scopes = {"openclaw", "devagent", "harness", "gep"}

    return {
        "schema_version": SCHEMA_VERSION,
        "id": f"capsule_auto_draft_{len(cluster_gene_ids)}_genes",
        "type": "Capsule",
        "trigger": sorted(list(all_signals))[:10],
        "gene": main_gene.get("id"),
        "summary": f"Auto-drafted Capsule from {len(cluster_gene_ids)} related Genes: " +
                   ", ".join(gid for gid in cluster_gene_ids[:5]),
        "confidence": 0.5,  # 草稿默认 confidence
        "blast_radius": {"files": len(cluster_gene_ids), "lines": 0},
        "outcome": {"status": "draft", "score": 0.0},
        "success_streak": 0,
        "pack_of": sorted(cluster_gene_ids),
        "scope": sorted(scopes),
        "_draft": True,
        "_needs_review": True,
    }


def main():
    parser = argparse.ArgumentParser(description="Gene → Capsule 自动绑定")
    parser.add_argument("--threshold", type=float, default=0.4, help="signals 相似度阈值")
    parser.add_argument("--dry-run", action="store_true", default=True, help="只输出，不写盘")
    parser.add_argument("--limit", type=int, default=10, help="最多输出多少 Capsule 草稿")
    args = parser.parse_args()

    print(f"=== Gene → Capsule 自动绑定 (threshold={args.threshold}) ===\n")
    genes = load_genes()
    capsules = load_capsules()
    print(f"📦 现有 Gene: {len(genes)} 个")
    print(f"📦 现有 Capsule: {len(capsules)} 个")
    ratio = len(capsules) / max(len(genes), 1) * 100
    print(f"📊 Capsule/Gene 比例: {ratio:.1f}% (目标 >= 50%)\n")

    clusters = cluster_genes(genes, threshold=args.threshold)
    print(f"🔍 聚类结果: {len(clusters)} 个簇 (>= 2 Gene)\n")

    if not clusters:
        print("ℹ️  无可打包的 Gene 簇")
        sys.exit(0)

    drafts = []
    for i, cluster in enumerate(clusters[:args.limit], 1):
        cap = draft_capsule(cluster, genes)
        drafts.append(cap)
        print(f"📄 草稿 #{i}: {cap['id']}")
        print(f"   gene count: {len(cluster)}")
        print(f"   main gene: {cap['gene']}")
        print(f"   trigger (前 5): {cap['trigger'][:5]}")
        print(f"   pack_of: {cap['pack_of']}")
        print()

    # 覆盖率统计
    covered_genes = set()
    for c in drafts:
        covered_genes.update(c["pack_of"])
    coverage = len(covered_genes) / max(len(genes), 1) * 100
    print(f"📊 草稿覆盖率: {coverage:.1f}% ({len(covered_genes)}/{len(genes)} Genes)")
    print(f"📊 目标 50% → 差 {50 - coverage:.1f}% (需 {int(len(genes) * 0.5) - len(capsules)} 个新 Capsule)")

    print(f"\n=== dry-run 模式，未写盘 ===")
    print(f"如需采纳某个草稿：")
    print(f"  1. 复制草稿到 plan/capsules/{{custom_id}}.json")
    print(f"  2. 修改 id / summary / confidence / strategy / execution_trace")
    print(f"  3. 添加 author + trigger_context + a2a 字段")
    print(f"  4. 跑 make verify 校验 GEP strict")
    print(f"  5. 走 Solidify 人工审批门")


if __name__ == "__main__":
    main()
