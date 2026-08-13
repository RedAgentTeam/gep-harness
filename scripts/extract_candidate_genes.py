"""Extract candidate Gene JSONs from scan output.

Stage 3 (Evolver) - Signal phase.

This is a TEMPLATE-ONLY script. The actual Signal generation should be done
by an LLM (called separately or by a future orchestrator). This script
just shapes scan output into candidate Gene JSON form for review.

Usage:
  python3 extract_candidate_genes.py --scan-output=scan.json --output=staging/
"""
import argparse
import json
import sys
from pathlib import Path

SCHEMA_VERSION = "1.12.1"

# Per GEP §2.1, valid Gene.category values
VALID_CATEGORIES = ("repair", "optimize", "innovate", "explore")


def infer_category(tool_name: str, count: int, arg_keys: list) -> str:
    """Rule-based category inference (v0.5: replace with LLM call).

    Priority: high-frequency tools → repair/optimize; new tools → explore.
    """
    dangerous = {"exec", "write", "edit", "apply_patch", "exec"}
    read_only = {"read", "web_fetch", "web_search", "wiki_get", "wiki_search"}
    if tool_name in dangerous:
        return "repair" if count >= 5 else "optimize"
    if tool_name in read_only:
        return "optimize"
    if count >= 10:
        return "repair"
    return "optimize"


def infer_strategy(tool_name: str, arg_keys: list) -> list:
    """Rule-based strategy generation (v0.5: replace with LLM call).

    Maps tool category to 3 concrete strategy steps.
    """
    tool_strategies = {
        "exec": [
            "Check exit code before reading stdout",
            "Add timeout for long-running commands",
            "Log command + args + exit_code for replay",
        ],
        "read": [
            "Cache frequently read files (path, size > 1MB)",
            "Add offset/limit for large file reads",
            "Log file path + offset for replay",
        ],
        "web_fetch": [
            "Add retry with backoff for timeout",
            "Cache URL + status_code + content_hash",
            "Set maxChars to avoid OOM on large pages",
        ],
        "edit": [
            "Verify oldText uniqueness before replace",
            "Log oldText + newText diff for audit",
            "Keep edit atomic (one edit = one concern)",
        ],
    }
    return tool_strategies.get(
        tool_name,
        [
            f"Profile {tool_name} usage patterns",
            f"Add caching for {tool_name} with TTL",
            "Log all calls to events.jsonl",
        ],
    )


def infer_evidence(tool_name: str, schema_version: str = "1.12.1") -> list:
    """Rule-based cross_library_evidence (v0.5: replace with LLM call).

    Maps tool to 5 knowledge libraries for GDI offline_check.
    """
    evidence_map = {
        "exec": ["BeautifulMathematics 幂等性", "cell-biology 反馈回路", "CognitivePsychology 确认偏误", "OpenStaxBiology Ch01", "evomap GEP"],
        "read": ["OpenStaxBiology 信息论", "CognitivePsychology 记忆锚点", "BeautifulMathematics 信息熵", "evomap 事件流", "cell-biology 信号转导"],
        "web_fetch": ["OpenStaxBiology 信息传递", "CognitivePsychology 注意力机制", "BeautifulMathematics 熵减", "evomap A2A 协议", "cell-biology 受体"],
        "edit": ["cell-biology 基因突变", "CognitivePsychology 确认偏误", "BeautifulMathematics 精确性", "evomap 演化变异", "OpenStaxBiology DNA 修复"],
        "write": ["cell-biology 转录", "CognitivePsychology 记忆巩固", "BeautifulMathematics 算法正确性", "evomap 事件日志", "OpenStaxBiology Ch06"],
    }
    return evidence_map.get(tool_name, ["CognitivePsychology 一般化", "evomap GEP", "OpenStaxBiology 方法论", "cell-biology 适应", "BeautifulMathematics"])[:5]


def make_candidate(tool_name: str, count: int, arg_keys: list,
                   category: str | None = None,
                   strategy: list | None = None,
                   evidence: list | None = None) -> dict:
    """Generate a candidate Gene from a tool pattern.

    v0.5: category/strategy/evidence are LLM-generated (signal phase).
    Current: rule-based heuristics as a fallback.
    """
    if category is None:
        category = infer_category(tool_name, count, arg_keys)
    if strategy is None:
        strategy = infer_strategy(tool_name, arg_keys)
    if evidence is None:
        evidence = infer_evidence(tool_name)

    signals = [f"tool_frequent:{tool_name}", f"hot_path:{tool_name}", tool_name]
    if count >= 10:
        signals.insert(0, f"high_freq:{count}_calls")

    return {
        "type": "Gene",
        "schema_version": SCHEMA_VERSION,
        "id": f"gene_candidate_{tool_name}",
        "category": category,
        "signals_match": signals,
        "preconditions": [
            f"tool '{tool_name}' has been called {count}+ times in 24h"
        ],
        "strategy": strategy,
        "constraints": {
            "max_files": 10,
            "forbidden_paths": [".git", "node_modules", "/opt/goapi"],
        },
        "validation": [
            f"python3 -c \"assert 'GEP strict' in open('README.md').read()\"",
        ],
        "summary": f"Hot-path optimization for {tool_name} ({count} calls in 24h, {len(strategy)} strategies)",
        "cross_library_evidence": evidence,
        "asset_id": "sha256:PLACEHOLDER_LLM_TO_FILL",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scan-output", required=True, help="Path to scan.json")
    p.add_argument("--output", required=True, help="Output directory (will be created)")
    p.add_argument("--threshold", type=int, default=3, help="min calls to qualify")
    args = p.parse_args()

    scan_data = json.load(open(args.scan_output))
    by_tool = scan_data.get("by_tool", {})
    arg_keys = scan_data.get("arg_keys_by_tool", {})

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = []
    for tool, count in by_tool.items():
        if count < args.threshold:
            continue
        cand = make_candidate(tool, count, arg_keys.get(tool, []))
        candidates.append(cand)

    for i, c in enumerate(candidates):
        out_path = out_dir / f"gene_candidate_{i:03d}_{c['signals_match'][2]}.json"
        json.dump(c, open(out_path, "w"), ensure_ascii=False, indent=2)
        print(f"wrote {out_path} (asset_id={c['asset_id'][:24]}...)")

    print(f"\n=== {len(candidates)} candidates written (TEMPLATE - LLM must fill strategy + asset_id) ===")


if __name__ == "__main__":
    main()