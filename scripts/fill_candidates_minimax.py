"""fill_candidates_minimax — gep-harness v52.1。

Stepfun quota 耗尽后 fallback 到 MiniMax (Anthropic-compatible) 跑候选 fill。
直接从 cmdline 接：--staging /tmp/candidates.json --output plan/genes-fresh

只填 category/strategy/cross_library_evidence/asset_id，保留 protected 字段。
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def _require_key() -> str:
    val = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not val:
        raise RuntimeError("MINIMAX_API_KEY is not set; export it before filling candidates")
    return val
URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic") + "/v1/messages"
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")

SCHEMA_VERSION = "1.12.1"
PROTECTED = {"type", "schema_version", "id", "signals_match", "preconditions",
             "constraints", "validation", "summary"}

PROMPT = """You are a GEP v{ver} Gene author.

Fill in the JSON fields for a candidate Gene. Return ONLY the JSON object (no markdown, no commentary).

Rules:
1. category: one of "repair", "optimize", "innovate", "explore"
2. strategy: exactly 3 concrete, actionable steps (English or Chinese)
3. cross_library_evidence: exactly 5 strings, each like "LibraryName: <one-line reason>"
   The 5 libraries are: BeautifulMathematics, cell-biology, CognitivePsychology, OpenStaxBiology, evomap
4. asset_id: compute sha256 of canonical JSON (strategy array sorted + category) prefixed with "sha256:"

Input Gene JSON:
{input_json}
"""


def call_minimax(prompt: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "temperature": 0.1,
    }).encode("utf-8")
    req = urllib.request.Request(
        URL, data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": _require_key(),
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    blocks = data.get("content", [])
    parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    return "\n".join(parts).strip()


def compute_asset_id(strategy: list[str], category: str) -> str:
    """sha256(canonical_json) → 'sha256:xxx'."""
    s = sorted(strategy) if strategy else ["?"]
    c = category or "repair"
    canonical = json.dumps(
        {"category": c, "strategy": s},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def parse_llm_json(raw: str) -> dict:
    """容错：剥 markdown fence + 兜底正则。"""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(l for l in lines if not l.strip().startswith("```"))
    import re
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[^{}]*(\{[^{}]*\}[^{}]*)*\}", raw, re.DOTALL)
        if not m:
            raise ValueError(f"LLM returned non-JSON: {raw[:200]}")
        return json.loads(m.group(0))



def compute_asset_id_canonical(gene: dict) -> str:
    """用 canonicalize 全 dict 算法算 asset_id，与 verify_assets 严格一致。"""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openclaw-harness"))
    from bin.canonicalize import compute_asset_id as _ci
    return _ci(gene)


def fill_one(path: Path) -> dict:
    gene = json.load(open(path))
    prompt = PROMPT.format(ver=SCHEMA_VERSION, input_json=json.dumps(gene, indent=2, ensure_ascii=False))
    raw = call_minimax(prompt)
    filled = parse_llm_json(raw)
    # asset_id 统一本地重算（用 canonicalize 全 dict 算法，与 verify_assets 严格一致）
    # 这样不依赖 LLM 是否算对 hash，verify_assets 100% 重算通过
    filled["asset_id"] = compute_asset_id_canonical(filled)
    # 保留 protected
    for k in PROTECTED:
        if k in gene and k not in filled:
            filled[k] = gene[k]
    return filled


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--staging", required=True, help="candidate 目录")
    p.add_argument("--output", required=True, help="filled 输出目录")
    p.add_argument("--limit", type=int, default=0, help="最多填几个（0=全部）")
    args = p.parse_args()

    staging = Path(args.staging)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = sorted(staging.glob("gene_candidate_*.json"))
    if args.limit:
        candidates = candidates[: args.limit]

    filled_count = 0
    for cand in candidates:
        print(f"=== {cand.name} ===")
        try:
            filled = fill_one(cand)
            out_path = output_dir / cand.name
            json.dump(filled, open(out_path, "w"), ensure_ascii=False, indent=2)
            print(f"  ✅ category={filled.get('category')}  asset_id={filled.get('asset_id','')[:30]}...")
            filled_count += 1
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")
            continue

    print(f"\n=== {filled_count}/{len(candidates)} filled ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())