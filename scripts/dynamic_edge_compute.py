"""5 库关联强度动态计算 — gep-harness v19.0 C。

从 plan/genes/*.json evidence 实际互引次数反推关联强度：
- 扫所有 gene 的 cross_library_evidence 5 字符串
- 统计每对库被同时引用的次数 → 共现矩阵
- 归一化到 0~1（min-max）
- 与静态基线 LIBRARY_GRAPH_EDGE 融合：dynamic = baseline * 0.6 + observed * 0.4

跑法：
    python3 scripts/dynamic_edge_compute.py
    python3 scripts/dynamic_edge_compute.py --output staging/dynamic_edges.json
    python3 scripts/dynamic_edge_compute.py --min-samples 5  # 至少 5 个样本才用观测值
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from cross_library_auto import LIBRARY_GRAPH_EDGE, LIBRARY_TEMPLATES

LIBS = list(LIBRARY_TEMPLATES.keys())


def normalize_lib(s: str) -> str | None:
    """从 evidence 字符串中识别库名（去空格、Chxx 前缀）。"""
    if not isinstance(s, str):
        return None
    s_lower = s.lower().replace("-", "").replace(" ", "")
    for lib in LIBS:
        if lib.lower().replace("-", "") in s_lower:
            return lib
    return None


def scan_evidence_cooccurrence(genes_dir: Path = REPO / "plan/genes") -> dict[str, dict[str, int]]:
    """扫所有 gene 的 evidence，返回 5x5 共现矩阵（次数）。"""
    co = defaultdict(lambda: defaultdict(int))
    total_per_lib = Counter()
    files_scanned = 0
    files_with_evidence = 0

    for f in genes_dir.glob("*.json"):
        files_scanned += 1
        try:
            with open(f) as fp:
                d = json.load(fp)
        except (json.JSONDecodeError, OSError):
            continue
        ev = d.get("cross_library_evidence", [])
        if not isinstance(ev, list) or len(ev) < 2:
            continue
        files_with_evidence += 1
        libs_in_gene = []
        for e in ev:
            lib = normalize_lib(e)
            if lib:
                libs_in_gene.append(lib)
                total_per_lib[lib] += 1
        # 共现
        for i, la in enumerate(libs_in_gene):
            for lb in libs_in_gene[i + 1:]:
                co[la][lb] += 1
                co[lb][la] += 1

    # 自身行也填上（归一化用）
    result = {}
    for lib in LIBS:
        result[lib] = {}
        for tgt in LIBS:
            if lib == tgt:
                result[lib][tgt] = total_per_lib[lib]
            else:
                result[lib][tgt] = co[lib][tgt]
    return {
        "matrix": result,
        "files_scanned": files_scanned,
        "files_with_evidence": files_with_evidence,
        "total_per_lib": dict(total_per_lib),
    }


def normalize_cooccurrence_to_edges(co_matrix: dict[str, dict[str, int]]) -> dict[str, dict[str, float]]:
    """把共现次数归一化到 0~1（除以 max）。"""
    max_co = 1
    for src, row in co_matrix.items():
        for tgt, c in row.items():
            if src != tgt and c > max_co:
                max_co = c
    if max_co == 0:
        max_co = 1
    edges = {}
    for src, row in co_matrix.items():
        edges[src] = {}
        for tgt, c in row.items():
            if src == tgt:
                edges[src][tgt] = 0.5
            else:
                edges[src][tgt] = round(c / max_co, 3)
    return edges


def merge_with_baseline(
    observed: dict[str, dict[str, float]],
    baseline: dict[str, dict[str, float]] = LIBRARY_GRAPH_EDGE,
    weight_observed: float = 0.4,
) -> dict[str, dict[str, float]]:
    """融合观测值与静态基线：dynamic = baseline * (1-w) + observed * w。"""
    w = weight_observed
    merged = {}
    for src in LIBS:
        merged[src] = {}
        for tgt in LIBS:
            b = baseline.get(src, {}).get(tgt, 0.5)
            o = observed.get(src, {}).get(tgt, 0.5)
            if src == tgt:
                merged[src][tgt] = 0.5  # 对角线恒定
            else:
                merged[src][tgt] = round(b * (1 - w) + o * w, 3)
    return merged


def compute(min_samples: int = 5, weight_observed: float = 0.4) -> dict:
    """主入口：扫 evidence → 归一化 → 融合 → 返回完整结果。"""
    scan = scan_evidence_cooccurrence()
    files_with_ev = scan["files_with_evidence"]
    co_matrix = scan["matrix"]

    if files_with_ev < min_samples:
        # 样本太少，全部用静态基线
        observed_edges = {src: {tgt: 0.5 for tgt in LIBS} for src in LIBS}
        used_observed = False
        note = f"样本不足（{files_with_ev} < {min_samples}），全部用静态基线"
    else:
        observed_edges = normalize_cooccurrence_to_edges(co_matrix)
        used_observed = True
        note = f"样本 {files_with_ev} 个，观测值生效（权重 {weight_observed}）"

    merged = merge_with_baseline(observed_edges, weight_observed=weight_observed)

    return {
        "scan_summary": {
            "files_scanned": scan["files_scanned"],
            "files_with_evidence": files_with_ev,
            "total_per_lib": scan["total_per_lib"],
            "cooccurrence": co_matrix,
        },
        "observed_edges": observed_edges,
        "baseline_edges": {src: {tgt: LIBRARY_GRAPH_EDGE.get(src, {}).get(tgt, 0.5) for tgt in LIBS} for src in LIBS},
        "dynamic_edges": merged,
        "used_observed": used_observed,
        "note": note,
        "version": "v19.0",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, help="输出 JSON 路径")
    parser.add_argument("--min-samples", type=int, default=5, help="最少样本数才用观测值")
    parser.add_argument("--weight-observed", type=float, default=0.4, help="观测值权重 0~1")
    parser.add_argument("--print-matrix", action="store_true", help="打印 dynamic 矩阵")
    args = parser.parse_args()

    result = compute(min_samples=args.min_samples, weight_observed=args.weight_observed)

    if args.print_matrix:
        print("\n═══ Dynamic Edges (v19.0) ═══")
        header = "From \\ To".ljust(22) + "".join(lib[:8].ljust(10) for lib in LIBS)
        print(header)
        for src in LIBS:
            row = src.ljust(22)
            for tgt in LIBS:
                row += f"{result['dynamic_edges'][src][tgt]:.2f}".ljust(10)
            print(row)
        print(f"\nℹ️ {result['note']}")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n✅ 写入: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())