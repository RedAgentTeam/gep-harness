"""LLM-fill candidate Gene JSONs.

Stage 3.5 (Evolver) - Signal→LLM phase.

Uses Stepfun API (OpenAI compatible) to fill in category, strategy[],
cross_library_evidence, and asset_id for candidate Genes produced by
extract_candidate_genes.py.

Usage:
  python3 llm_fill_gene.py --candidate=candidate_000_exec.json
  python3 llm_fill_gene.py --staging=/tmp/staging-candidates/ --output=filled/
  python3 llm_fill_gene.py --dry-run --staging=/tmp/staging-candidates/
"""
import argparse
import json
import os
import sys
from pathlib import Path

STEPFUN_API_KEY = os.environ.get(
    "STEPFUN_API_KEY",
    "CJahJE5zpT4Gl3tCR2Q9Ang2nlJR6CSkhS8yakQnBWShoWzp4QJND7Ig3QRX0cRH",
)
STEPFUN_BASE_URL = os.environ.get("STEPFUN_BASE_URL", "https://api.stepfun.com/v1")
STEPFUN_MODEL = os.environ.get("STEPFUN_MODEL", "step-3.5-flash")

SCHEMA_VERSION = "1.12.1"

FILL_PROMPT_TEMPLATE = """You are a GEP v{ver} Gene author.

Fill in the JSON fields below for a candidate Gene. Keep existing fields unchanged.
Rules:
1. category: one of "repair", "optimize", "innovate", "explore"
2. strategy: exactly 3 concrete, actionable steps (Chinese or English)
3. cross_library_evidence: exactly 5 strings, each "LibraryName <one-line reason>"
4. asset_id: compute a sha256 of the canonical JSON string (strategy+category sorted)

Return ONLY the JSON object, no markdown, no commentary.

Input Gene JSON:
{input_json}
"""


def call_stepfun(prompt: str, model: str = STEPFUN_MODEL) -> str:
    import urllib.request
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.1,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{STEPFUN_BASE_URL}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {STEPFUN_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def fill_gene(gene: dict) -> dict:
    prompt = FILL_PROMPT_TEMPLATE.format(
        ver=SCHEMA_VERSION,
        input_json=json.dumps(gene, indent=2, ensure_ascii=False),
    )
    raw = call_stepfun(prompt)
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])
    filled = json.loads(raw)
    # Merge: preserve protected fields, replace editable ones
    PROTECTED = {"type", "schema_version", "id", "signals_match", "preconditions",
                 "constraints", "validation", "summary"}
    for k, v in filled.items():
        if k not in PROTECTED:
            gene[k] = v
    gene["_llm_filled"] = True
    return gene


def fill_file(path: Path) -> dict:
    gene = json.load(open(path))
    return fill_gene(gene)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", help="Single candidate JSON to fill")
    p.add_argument("--staging", help="Directory of candidates to fill in-place")
    p.add_argument("--output", help="Output directory (default: --staging directory)")
    p.add_argument("--dry-run", action="store_true", help="Show what would be filled without calling API")
    p.add_argument("--model", default=STEPFUN_MODEL, help="Model to use")
    args = p.parse_args()

    if not args.candidate and not args.staging:
        p.error("Provide --candidate or --staging")

    if args.candidate:
        path = Path(args.candidate)
        gene = json.load(open(path))
        print(f"=== Filling {path.name} ===")
        print(f"  Before: category={gene.get('category')}  "
              f"strategy={gene.get('strategy')}  "
              f"evidence={gene.get('cross_library_evidence', 'N/A')}")
        if args.dry_run:
            print("  [dry-run] Would call LLM here")
            return
        filled = fill_gene(gene)
        print(f"  After:  category={filled.get('category')}  "
              f"strategy={filled.get('strategy')}  "
              f"evidence={filled.get('cross_library_evidence')}")
        out = Path(args.output or args.candidate)
        json.dump(filled, open(out, "w"), ensure_ascii=False, indent=2)
        print(f"  Saved to {out}")

    elif args.staging:
        staging = Path(args.staging)
        output_dir = Path(args.output) if args.output else staging
        output_dir.mkdir(parents=True, exist_ok=True)
        candidates = sorted(staging.glob("gene_candidate_*.json"))
        filled_count = 0
        for cand in candidates:
            gene = json.load(open(cand))
            if gene.get("_llm_filled"):
                print(f"  ⊘ {cand.name} already filled, skipping")
                continue
            print(f"=== Filling {cand.name} ===")
            if args.dry_run:
                print(f"  [dry-run] Would fill category={gene.get('category')}")
                continue
            try:
                filled = fill_gene(gene)
                out_path = output_dir / cand.name
                json.dump(filled, open(out_path, "w"), ensure_ascii=False, indent=2)
                print(f"  ✅ category={filled.get('category')}  "
                      f"evidence={filled.get('cross_library_evidence')}")
                filled_count += 1
            except Exception as e:
                print(f"  ❌ {e}")
        print(f"\n=== {filled_count}/{len(candidates)} candidates filled ===")


if __name__ == "__main__":
    main()
