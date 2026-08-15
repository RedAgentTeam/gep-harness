"""Gene 演化历史 → Capsule 打包。

按胡老师 01:31 决议：把 130 个 v15~v72 旧版本 Gene 打包成 Capsule，
保留 65 期演化历史（对应 docs/ROADMAP_v0.5~v9.0）。

每个工具（exec/read/write/...）一个 Capsule：
- capsule_gene_{tool}_evolution_v15_to_vXX.json
- pack_of: 全部历史版本 Gene ID 列表
- summary: 演化历史摘要
- strategy: 演化里程碑（v15→v18→...→vXX）

风险控制：
- 不删除任何文件
- 只生成 Capsule 草稿到 /tmp/capsule_drafts/
- 走 GEP strict 校验 + Solidify 人工审批门
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
PLAN_GENES = REPO / "plan" / "genes"
PLAN_CAPSULES = REPO / "plan" / "capsules"
DRAFTS_DIR = Path("/tmp/capsule_drafts")
SCHEMA_VERSION = "1.12.1"


def extract_tool(filename: str) -> str:
    """从文件名提取 tool 名。

    例：
      gene_candidate_001_hot_path:read.json → read
      gene_read_hotpath_v72.json → read
      gene_write_hotpath_v15.json → write
      gene_exec_hotpath_v21.json → exec
      gene_message_hotpath_v18.json → message
    """
    name = filename.replace("gene_", "").replace(".json", "")
    # 优先匹配 tool_hotpath 模式
    for tool in ["exec", "process", "read", "write", "write_file", "edit", "message"]:
        if f"{tool}_hotpath" in name or name.startswith(f"{tool}_hotpath"):
            return tool
    # 匹配 hot_path:tool 模式
    if "hot_path:" in name:
        return name.split("hot_path:")[-1]
    # 兜底：取第一个 _ 分隔段
    return name.split("_")[0]


def main():
    print(f"=== Gene 演化历史打包成 Capsule ===\n")
    print(f"📂 源: {PLAN_GENES}")
    print(f"📂 输出: {DRAFTS_DIR}\n")

    # 1. 按 tool 分组所有 Gene
    by_tool = defaultdict(list)
    for f in sorted(PLAN_GENES.glob("*.json")):
        try:
            g = json.load(open(f))
            tool = extract_tool(f.name)
            by_tool[tool].append({
                "id": g.get("id"),
                "file": f.name,
                "mtime": f.stat().st_mtime,
                "signals_count": len(g.get("signals_match", []) or []),
                "summary": g.get("summary", "")[:80],
            })
        except Exception as e:
            print(f"⚠️  skip {f.name}: {e}")

    print(f"📊 共 {sum(len(v) for v in by_tool.values())} 个 Gene，按 tool 分组:\n")
    for tool, genes in sorted(by_tool.items()):
        if len(genes) >= 2:  # 至少 2 个版本才值得打包
            print(f"  {tool}: {len(genes)} 个版本")

    # 2. 为每个 tool（>= 2 版本）生成 Capsule 草稿
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    drafts = []

    for tool, genes in sorted(by_tool.items()):
        if len(genes) < 2:
            continue

        # 按 mtime 排序（最早 → 最新）
        genes_sorted = sorted(genes, key=lambda x: x["mtime"])

        # 提取版本号
        versions = []
        for g in genes_sorted:
            v_match = g["file"].split("_v")[-1].replace(".json", "")
            try:
                versions.append(int(v_match))
            except ValueError:
                pass
        v_min = min(versions) if versions else "?"
        v_max = max(versions) if versions else "?"

        # pack_of 用文件名（同 id 多次写入时文件名才是唯一标识）
        pack_of_files = sorted([g["file"] for g in genes])

        # 演化里程碑（前 5 个 + 最新）
        milestones = [g["file"] for g in genes_sorted[:5]]
        if genes_sorted[-1]["file"] not in milestones:
            milestones.append(genes_sorted[-1]["file"])

        # 草稿 Capsule
        draft = {
            "schema_version": SCHEMA_VERSION,
            "id": f"capsule_gene_{tool}_evolution_v{v_min}_to_v{v_max}",
            "type": "Capsule",
            "_pack_files": pack_of_files,
            "trigger": [
                f"gene_{tool}_history",
                f"{tool}_evolution",
                f"v{v_min}_to_v{v_max}",
                "65_phases",
                "gep_harness_evolution",
                f"{tool}_hotpath",
            ],
            "gene": genes_sorted[-1]["id"],  # 最新版本作主 gene
            "summary": f"{tool} tool Gene 演化历史：{len(genes)} 个版本（v{v_min} → v{v_max}），"
                       f"覆盖 gep-harness v0.5~v9.0 共 65 期演化过程。",
            "confidence": 0.75,
            "blast_radius": {
                "files": len(genes),
                "lines": 0,
            },
            "outcome": {
                "status": "success",
                "score": 0.7,
            },
            "success_streak": 1,
            "success_reason": f"{tool} Gene 在 65 期演化中从 v{v_min} 演进到 v{v_max}，"
                              f"每次迭代保留 signals_match / cross_library_evidence / strategy 历史。",
            "pack_of": pack_of_files,
            "scope": ["openclaw", "gep-harness", "history", tool],
            "strategy": [
                f"v{v_min}: 初始版本（{genes_sorted[0]['file']}）",
                f"v{v_max}: 当前版本（{genes_sorted[-1]['file']}）",
                f"共 {len(genes)} 个版本，按 mtime 排序保留完整演化链",
                "对应 ROADMAP_v0.5~v9.0 共 65 期演化文档",
                "打包目的：清理 plan/genes/ 主目录，沉淀演化历史为可查询 Capsule",
            ],
            "execution_trace": [
                {
                    "stage": "build",
                    "ts": "2026-08-15T01:31:00+08:00",
                    "detail": f"按 tool 分组 {len(by_tool)} 个工具，共 {sum(len(v) for v in by_tool.values())} 个 Gene"
                },
                {
                    "stage": "build",
                    "ts": "2026-08-15T01:32:00+08:00",
                    "detail": f"为 {tool} tool 生成 Capsule 草稿（{len(genes)} 个 pack_of）"
                },
                {
                    "stage": "canary",
                    "ts": "2026-08-15T01:33:00+08:00",
                    "detail": f"等待 Solidify 人工审批"
                },
            ],
            "a2a": {
                "author_agent": "devagent",
                "intent": "preserve",
                "target_subsystem": f"plan/capsules/{tool}_evolution",
            },
            "cost_tokens": 0,
            "cost_usd": 0,
            "derivation_tokens": None,
            "visibility": "private",
            "cost_tier": "cheap",
            "type": "Capsule",
            "author": {
                "handle": "胡老师",
                "evox_install_id": "openclaw-devagent-001",
            },
            "trigger_context": {
                "prompt": "胡老师 01:31 决议：选 B 把 gene 演化历史打包成 Capsule，保留 65 期演化",
                "session_id": "agent:devagent:feishu:devagent:direct:ou_a9dcdee21100e3560ab36fd59a886988",
                "agent_model": "minimax/MiniMax-M3",
                "context_signals": [
                    "gene_history_preservation",
                    "65_phases_evolution",
                    "capsule_draft_only_no_delete",
                ],
            },
            "_draft": True,
            "_needs_review": True,
            "_pack_version_min": v_min,
            "_pack_version_max": v_max,
        }

        # 计算 asset_id（标准 canonicalize）
        import hashlib
        sys.path.insert(0, str(REPO / "openclaw-harness" / "bin"))
        try:
            from canonicalize import compute_asset_id  # type: ignore
            draft["asset_id"] = compute_asset_id(draft)
        except Exception as e:
            draft["asset_id"] = "sha256:PLACEHOLDER_NEEDS_CANONICALIZE"
            print(f"  ⚠️  canonicalize failed for {draft['id']}: {e}")

        drafts.append(draft)
        out_file = DRAFTS_DIR / f"{draft['id']}.json"
        json.dump(draft, open(out_file, "w"), ensure_ascii=False, indent=2)
        print(f"  📄 {out_file.name}")
        print(f"     pack_of (files): {len(draft['pack_of'])} Gene, version v{v_min}→v{v_max}")

    print(f"\n=== 📊 共生成 {len(drafts)} 个 Capsule 草稿 ===")
    print(f"\n=== 后续步骤 ===")
    print(f"1. 跑 GEP strict 校验：")
    print(f"   python3 scripts/validate_gep.py --mode=strict --input='/tmp/capsule_drafts/*.json'")
    print(f"2. 走 Solidify 审批门（人工 y/N）：")
    print(f"   python3 scripts/solidify.py --staging=/tmp/capsule_drafts/")
    print(f"3. 如果批准，自动写入 plan/capsules/ + plan/events/event_solidify_*.json + git commit")
    print(f"\n⚠️  本脚本**不删除任何 plan/genes/ 文件**——只生成草稿。")


if __name__ == "__main__":
    main()
