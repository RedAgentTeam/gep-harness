"""Gene 命名清理 — 删除重复 + 修正双前缀。

按 v9 ROADMAP 待办：legacy gene_candidate_* 命名混乱。
本脚本：
1. 按 id 分组所有 plan/genes/*.json
2. 对每个 id 保留 mtime 最新的一份
3. 删除旧文件
4. 修正双 gene_ 前缀

注意：本脚本**只删除 plan/genes/ 内文件**，不触碰 plan/capsules/、plan/events/、美机。
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
PLAN_GENES = REPO / "plan" / "genes"


def main():
    print(f"=== Gene 命名清理 (dry-run 默认) ===\n")
    print(f"📂 目录: {PLAN_GENES}\n")

    # 1. 按 id 分组
    by_id = defaultdict(list)
    for f in PLAN_GENES.glob("*.json"):
        try:
            g = json.load(open(f))
            gid = g.get("id", "")
            if gid:
                by_id[gid].append((f, f.stat().st_mtime))
        except Exception as e:
            print(f"⚠️  skip {f.name}: {e}")

    duplicates = [(gid, files) for gid, files in by_id.items() if len(files) > 1]
    print(f"📦 总 Gene 数（按 id 唯一）: {len(by_id)}")
    print(f"📦 文件总数（含重复）: {sum(len(f) for f in by_id.values())}")
    print(f"⚠️  重复 id 数: {len(duplicates)}\n")

    if duplicates:
        print("=== 重复文件（保留最新，删除旧） ===\n")
        to_delete = []
        for gid, files in duplicates:
            files_sorted = sorted(files, key=lambda x: -x[1])  # 最新优先
            keep = files_sorted[0]
            for old_f, _ in files_sorted[1:]:
                print(f"  DEL: {old_f.name} (id={gid}, mtime={Path(old_f).stat().st_mtime:.0f})")
                to_delete.append(old_f)
            print(f"  KEEP: {keep[0].name} (id={gid}, mtime={keep[1]:.0f})\n")
        print(f"📊 将删除 {len(to_delete)} 个文件")
    else:
        print("✅ 无重复")

    # 2. 双 gene_ 前缀
    print("\n=== 双前缀修正 ===\n")
    to_rename = []
    for f in PLAN_GENES.glob("*.json"):
        if f.name.startswith("gene_gene_"):
            new_name = "gene_" + f.name[len("gene_gene_"):]
            print(f"  REN: {f.name} → {new_name}")
            to_rename.append((f, new_name))
    print(f"\n📊 将重命名 {len(to_rename)} 个文件")

    # 3. 实际执行（除非 --dry-run）
    if "--execute" in sys.argv:
        print("\n=== ⚠️  EXECUTING (--execute mode) ===\n")
        if duplicates:
            for old_f, _ in [(f, t) for f, t in files_sorted[1:]]:
                old_f.unlink()
                print(f"  ✓ deleted {old_f.name}")
        for old_f, new_name in to_rename:
            old_f.rename(old_f.parent / new_name)
            print(f"  ✓ renamed {old_f.name} → {new_name}")
        print(f"\n=== ✅ 清理完成 ===")
    else:
        print("\n=== dry-run 模式，未实际删除/重命名 ===")
        print("如需执行：python3 scripts/clean_legacy_genes.py --execute")


if __name__ == "__main__":
    main()
