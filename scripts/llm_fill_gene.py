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

def _require_key(name: str) -> str:
    """Read an API key from the environment. Never fall back to a literal."""
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(f"{name} is not set; export it before calling the provider")
    return val


STEPFUN_BASE_URL = os.environ.get("STEPFUN_BASE_URL", "https://api.stepfun.com/step_plan/v1")
STEPFUN_MODEL = os.environ.get("STEPFUN_MODEL", "step-3.5-flash")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/anthropic")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")

# ⚠️ 2026-08-15 WARNING:
# StepFun reasoning model (step-3.5-flash / step-3.7-flash) 不适合此任务
# 现象: content_len=0 + finish_reason="length"，model 陷入 "wait wait" 推理循环
# 实际请求会触发 LLM request timed out（>30s 网关超时）
# 替代方案: 本地 Python 生成 strategy + sha256(asset_id)，见 scripts/local_fill_gene.py
# 或: 换非 reasoning 模型（需先查 /v1/models 确认可用 id）

def _load_local_env() -> None:
    """Load KEY=value lines from a gitignored .env. Does not override the process env."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()

SCHEMA_VERSION = "1.12.1"
STRATEGY_STEP_MAX = 120
SIGNAL_MAX = 64

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
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{STEPFUN_BASE_URL}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_require_key('STEPFUN_API_KEY')}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    msg = data["choices"][0]["message"]
    content = msg.get("content", "").strip()
    if not content:
        # reasoning model: content is empty, fall back to reasoning_content
        rc = msg.get("reasoning_content", "").strip()
        # Try to extract the actual JSON from reasoning_content
        if rc:
            import re
            m = re.search(r"({.*?})", rc, re.DOTALL)
            if m:
                content = m.group(1)
    return content


def call_minimax(prompt: str, model: str = MINIMAX_MODEL) -> str:
    """MiniMax (Anthropic-compatible) provider。"""
    import urllib.request
    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "temperature": 0.1,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{MINIMAX_BASE_URL}/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": _require_key("MINIMAX_API_KEY"),
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # Anthropic format: content is a list of blocks
    blocks = data.get("content", [])
    parts = []
    for blk in blocks:
        if blk.get("type") == "text":
            parts.append(blk.get("text", ""))
    return "\n".join(parts).strip()


def call_llm(prompt: str, provider: str = "stepfun") -> str:
    """统一 LLM 调用入口。provider: 'minimax' | 'stepfun'。"""
    if provider == "stepfun":
        return call_stepfun(prompt)
    return call_minimax(prompt)


def fill_gene(gene: dict, provider: str = "stepfun") -> dict:
    prompt = FILL_PROMPT_TEMPLATE.format(
        ver=SCHEMA_VERSION,
        input_json=json.dumps(gene, indent=2, ensure_ascii=False),
    )
    raw = call_llm(prompt, provider=provider)
    # Strip markdown fences if present (handle ```json, ```, or no fence at all)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])
    if not raw:
        raise ValueError("LLM returned empty response")
    try:
        filled = json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to extract the first {...} block as fallback
        import re
        m = re.search(r'\{.*?\}', raw, re.DOTALL)
        if m:
            filled = json.loads(m.group())
        else:
            raise ValueError(f"LLM returned non-JSON: {raw[:200]}") from e
    # Merge: preserve protected fields, replace editable ones
    PROTECTED = {"type", "schema_version", "id", "signals_match", "preconditions",
                 "constraints", "validation", "summary"}
    for k, v in filled.items():
        if k not in PROTECTED:
            gene[k] = v
    if isinstance(gene.get("strategy"), list):
        gene["strategy"] = [
            str(step)[:STRATEGY_STEP_MAX] for step in gene["strategy"][:3]
        ]
    if isinstance(gene.get("signals_match"), list):
        gene["signals_match"] = [
            str(sig)[:SIGNAL_MAX] for sig in gene["signals_match"][:8]
        ]
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
    p.add_argument("--provider", choices=["minimax", "stepfun"], default="stepfun",
                   help="LLM provider (default: stepfun; set MINIMAX_API_KEY and pass minimax)")
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
        filled = fill_gene(gene, provider=args.provider)
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
        # Sidecar manifest tracks which genes have been LLM-filled,
        # avoiding writing _llm_filled into Gene JSON (would pollute asset_id hash).
        manifest_path = output_dir / "llm_filled_manifest.json"
        if manifest_path.exists():
            manifest = json.load(open(manifest_path))
        else:
            manifest = {"filled": [], "schema_version": "1.12.1"}
        for cand in candidates:
            if cand.name in manifest["filled"]:
                print(f"  ⊘ {cand.name} already filled, skipping")
                continue
            print(f"=== Filling {cand.name} ===")
            gene = json.load(open(cand))
            if args.dry_run:
                print(f"  [dry-run] Would fill category={gene.get('category')}")
                continue
            try:
                filled = fill_gene(gene, provider=args.provider)
                out_path = output_dir / cand.name
                json.dump(filled, open(out_path, "w"), ensure_ascii=False, indent=2)
                print(f"  ✅ category={filled.get('category')}  "
                      f"evidence={filled.get('cross_library_evidence')}")
                manifest["filled"].append(cand.name)
                filled_count += 1
            except Exception as e:
                print(f"  ❌ {e}")
        json.dump(manifest, open(manifest_path, "w"), ensure_ascii=False, indent=2)
        print(f"\n=== {filled_count}/{len(candidates)} candidates filled ===")


if __name__ == "__main__":
    main()
