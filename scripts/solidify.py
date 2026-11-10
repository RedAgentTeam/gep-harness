#!/usr/bin/env python3
"""Solidify — GEP Harness 候选 Gene 人工审批流

用法:
  python3 solidify.py --staging=/tmp/v_staging/         # 审批所有 staging candidates
  python3 solidify.py --gene=gene_exec_cd_v80.json      # 审批单个 Gene
  python3 solidify.py --list                              # 列出待审批 candidates

固化前申报（写入之前，缺一即拒绝，exit 1）:
  --change-kind fault_fix|new_capability
  --eval-name <同一评测名> --before <数字> --after <数字>
  --evidence <文件或日志路径> --rollback <commit/sha/备份>

  也可以写在候选 JSON 的 solidify_declaration 里（harness 字段，
  校验和入库前会去掉，不进 GEP asset_id）。

流程:
  1. scan plan/genes/ 现有 Gene → 建 DUPLICATE 检测表
  2. 提取 candidates → 逐条检查 DUPLICATE
  3. 逐条 GEP strict validate
  4. 固化前申报：change_kind + 同一评测的前后数字与证据路径 + 回滚点
  5. 打印审批摘要 → 等待用户 approved
  6. 复制到 plan/genes/ + 写 plan/events/ + commit

Solidify 是硬性人工审批门，不自动执行。
分数变好不一定是新能力：可能只是修掉了挡住原有能力的故障。
"""
import sys
import os
import math
import copy
from pathlib import Path

# P0-3 fix: ensure canonicalize.py (in openclaw-harness/bin) is importable
# both when this script is run directly AND when imported as a module.
_here = Path(__file__).resolve().parent
_bin = _here.parent / "openclaw-harness" / "bin"
if str(_bin) not in sys.path:
    sys.path.insert(0, str(_bin))

import argparse
import json
import hashlib
import argparse
import json
import hashlib
from cross_library_auto import LIBRARY_GRAPH_EDGE  # v20.0: trust 报告 baseline 识别
import subprocess
import sys
from pathlib import Path

# P0-4 fix: resolve repo root from this file's location, not a hard-coded absolute path.
# scripts/solidify.py lives at <repo>/scripts/solidify.py → parent.parent = <repo>.
GEP_HARNESS = Path(__file__).resolve().parent.parent
PLAN_GENES = GEP_HARNESS / 'plan/genes'
PLAN_EVENTS = GEP_HARNESS / 'plan/events'
STAGING = Path('/tmp/v_staging')

# P0-3/C1 fix: DIRECTLY use canonicalize.py's compute_asset_id as the single
# source of truth. Do NOT add a local wrapper that strips additional fields,
# because that creates TWO asset_id algorithms for the same Gene:
#   1. solidifypo's local compute_asset_id (strips 8 protected + asset_id)
#   2. canonicalize.py's compute_asset_id (strips only asset_id)
# Validate_gep uses #2, so any Gene solidified under #1 will fail verify.
#
# Now both solidify and validate_gep use the SAME algorithm.
from canonicalize import compute_asset_id  # noqa: E402


def load_existing_genes():
    """加载 plan/genes/ 所有现有 Gene，返回 {gene_id: asset_id}"""
    table = {}
    for gf in sorted(PLAN_GENES.glob('*.json')):
        try:
            g = json.load(open(gf))
            gid = g.get('id', gf.stem)
            aid = g.get('asset_id', compute_asset_id(g))
            table[gid] = {'asset_id': aid, 'file': gf.name}
        except Exception as e:
            print(f'  ⚠️  skip {gf.name}: {e}', file=sys.stderr)
    return table


def check_duplicate(g, existing):
    """检查 Gene 是否与现有 Gene 重复"""
    new_aid = compute_asset_id(g)
    for eid, einfo in existing.items():
        if einfo['asset_id'] == new_aid:
            return True, eid, einfo['file']
    return False, None, None


def validate_gene(g):
    """GEP strict 校验（调用 validate_gep.py）"""
    tmp = Path('/tmp/solidify_validate.json')
    json.dump(g, open(tmp, 'w'), ensure_ascii=False, indent=2)
    r = subprocess.run(
        ['python3', str(GEP_HARNESS / 'scripts/validate_gep.py'), '--mode=strict', '--input', str(tmp)],
        capture_output=True, text=True, cwd=str(GEP_HARNESS)
    )
    return r.returncode == 0, r.stdout.strip(), r.stderr.strip()


# Harness-only. Not a GEP protocol field: fault_fix = 修故障, new_capability = 新能力.
SOLIDIFY_CHANGE_KINDS = ('fault_fix', 'new_capability')


def load_candidate(path):
    """Load a candidate and detach harness-only ``solidify_declaration``.

    The declaration is not part of the GEP asset. Removing it before
    duplicate detection, strict validate, and the write into plan/genes
    keeps asset_id on the protocol fields.
    """
    g = json.load(open(path))
    declaration = None
    if isinstance(g, dict):
        declaration = g.pop('solidify_declaration', None)
    return g, declaration


def cli_declaration(args):
    """Flags explicitly passed on the solidify command. None means 'not set'."""
    cli = {}
    if getattr(args, 'change_kind', None) is not None:
        cli['change_kind'] = args.change_kind
    if getattr(args, 'before', None) is not None:
        cli['before'] = args.before
    if getattr(args, 'after', None) is not None:
        cli['after'] = args.after
    if getattr(args, 'before_eval', None) is not None:
        cli['before_eval'] = args.before_eval
    elif getattr(args, 'eval_name', None) is not None:
        cli['before_eval'] = args.eval_name
    if getattr(args, 'after_eval', None) is not None:
        cli['after_eval'] = args.after_eval
    elif getattr(args, 'eval_name', None) is not None:
        cli['after_eval'] = args.eval_name
    if getattr(args, 'evidence', None) is not None:
        cli['evidence_path'] = args.evidence
    if getattr(args, 'rollback', None) is not None:
        cli['rollback'] = args.rollback
    return cli


def merge_declaration(gene_decl, cli_decl):
    """CLI flags override the same field on the candidate declaration."""
    base = copy.deepcopy(gene_decl) if isinstance(gene_decl, dict) else {}
    if not cli_decl:
        return base
    if 'change_kind' in cli_decl:
        base['change_kind'] = cli_decl['change_kind']
    if 'evidence_path' in cli_decl:
        base['evidence_path'] = cli_decl['evidence_path']
    if 'rollback' in cli_decl:
        base['rollback'] = cli_decl['rollback']
    for side in ('before', 'after'):
        eval_key = f'{side}_eval'
        has_eval = eval_key in cli_decl
        has_value = side in cli_decl
        if not has_eval and not has_value:
            continue
        current = base.get(side)
        node = dict(current) if isinstance(current, dict) else {}
        if not isinstance(current, dict) and current is not None:
            node['value'] = current
        if has_eval:
            node['eval'] = cli_decl[eval_key]
        if has_value:
            node['value'] = cli_decl[side]
        base[side] = node
        base.pop(eval_key, None)
    return base


def _extract_side(decl, name):
    """Return (eval_missing, eval_raw, value_missing, value_raw)."""
    eval_missing = True
    value_missing = True
    eval_raw = None
    value_raw = None
    node = decl.get(name) if isinstance(decl, dict) else None
    if isinstance(node, dict):
        if 'eval' in node:
            eval_missing = False
            eval_raw = node.get('eval')
        if 'value' in node:
            value_missing = False
            value_raw = node.get('value')
    elif isinstance(decl, dict) and name in decl and decl[name] is not None:
        value_missing = False
        value_raw = decl[name]
    alias = f'{name}_eval'
    if isinstance(decl, dict) and alias in decl:
        eval_missing = False
        eval_raw = decl.get(alias)
    return eval_missing, eval_raw, value_missing, value_raw


def _classify_number(missing, raw):
    """Return ('missing'|'invalid'|'ok', number or None)."""
    if missing or raw is None:
        return 'missing', None
    if isinstance(raw, bool):
        return 'invalid', None
    if isinstance(raw, (int, float)):
        if isinstance(raw, float) and not math.isfinite(raw):
            return 'invalid', None
        return 'ok', raw
    if isinstance(raw, str):
        text = raw.strip()
        if text == '':
            return 'missing', None
        try:
            number = float(text)
        except ValueError:
            return 'invalid', None
        if not math.isfinite(number):
            return 'invalid', None
        if text[1:].isdigit() if text.startswith('-') else text.isdigit():
            return 'ok', int(text)
        return 'ok', number
    return 'invalid', None


def _classify_text(decl, keys):
    """Return ('missing'|'empty'|'invalid'|'ok', stripped text or None)."""
    if not isinstance(decl, dict):
        return 'missing', None
    present_key = next((key for key in keys if key in decl), None)
    if present_key is None or decl[present_key] is None:
        return 'missing', None
    raw = decl[present_key]
    if not isinstance(raw, str):
        return 'invalid', None
    text = raw.strip()
    if text == '':
        return 'empty', None
    return 'ok', text


def _classify_name(missing, raw):
    if missing or raw is None:
        return 'missing', None
    if not isinstance(raw, str):
        return 'invalid', None
    text = raw.strip()
    if text == '':
        return 'missing', None
    return 'ok', text


def parse_solidify_declaration(decl):
    """Check a solidify request. Return (problems, normalized or None).

    problems is empty only when change_kind, the before/after evidence
    (same eval name, both numbers, a non-empty evidence path), and a
    non-empty rollback point are all present and well-formed.
    """
    problems = []
    if not isinstance(decl, dict):
        decl = {}

    kind_raw = decl.get('change_kind') if 'change_kind' in decl else None
    kind_missing = 'change_kind' not in decl or kind_raw is None or (
        isinstance(kind_raw, str) and kind_raw.strip() == ''
    )
    kind = None
    if kind_missing:
        problems.append('missing change_kind')
    elif not isinstance(kind_raw, str) or kind_raw.strip() not in SOLIDIFY_CHANGE_KINDS:
        shown = kind_raw.strip() if isinstance(kind_raw, str) else kind_raw
        problems.append(
            f'invalid change_kind: {shown!r} '
            f'(expected fault_fix or new_capability)'
        )
    else:
        kind = kind_raw.strip()

    parsed_sides = {}
    for side in ('before', 'after'):
        eval_missing, eval_raw, value_missing, value_raw = _extract_side(decl, side)
        eval_status, eval_name = _classify_name(eval_missing, eval_raw)
        if eval_status == 'missing':
            problems.append(f'missing {side}.eval')
        elif eval_status == 'invalid':
            problems.append(f'invalid {side}.eval: {eval_raw!r}')
        value_status, number = _classify_number(value_missing, value_raw)
        if value_status == 'missing':
            problems.append(f'missing {side}.value')
        elif value_status == 'invalid':
            problems.append(f'invalid {side}.value: {value_raw!r}')
        parsed_sides[side] = (eval_name, number)

    before_name, before_number = parsed_sides['before']
    after_name, after_number = parsed_sides['after']
    if before_name is not None and after_name is not None and before_name != after_name:
        problems.append(
            f'eval name mismatch: before.eval={before_name!r} after.eval={after_name!r}'
        )

    evidence_status, evidence_path = _classify_text(decl, ('evidence_path', 'evidence'))
    if evidence_status == 'missing':
        problems.append('missing evidence_path')
    elif evidence_status == 'empty':
        problems.append('empty evidence_path')
    elif evidence_status == 'invalid':
        raw = decl.get('evidence_path', decl.get('evidence'))
        problems.append(f'invalid evidence_path: {raw!r}')

    rollback_status, rollback = _classify_text(decl, ('rollback',))
    if rollback_status == 'missing':
        problems.append('missing rollback')
    elif rollback_status == 'empty':
        problems.append('empty rollback')
    elif rollback_status == 'invalid':
        problems.append(f'invalid rollback: {decl.get("rollback")!r}')

    if problems:
        return problems, None
    return [], {
        'change_kind': kind,
        'before': {'eval': before_name, 'value': before_number},
        'after': {'eval': after_name, 'value': after_number},
        'evidence_path': evidence_path,
        'rollback': rollback,
    }


def make_solidify_event(gene_file, gene_id, outcome, score=0.85, notes='', declaration=None):
    """生成 plan/events/ solidify event JSON"""
    evt = {
        'schema_version': '1.12.1',
        'type': 'EvolutionEvent',
        'id': f'evt_solidify_{gene_id}_{__import__("datetime").datetime.now().strftime("%Y_%m_%d")}',
        'parent': 'evt_plan_gep_harness_cycle_001',
        'intent': 'optimize',
        'signals': ['solidify_approved', 'hotpath_gene'],
        'genes_used': [gene_id],
        'mutation_id': f'mut_solidify_{gene_id}_{__import__("datetime").datetime.now().strftime("%Y_%m_%d")}',
        'personality_state': {'rigor': 0.9, 'risk_tolerance': 0.3, 'creativity': 0.5},
        'blast_radius': {'files': 1, 'lines': 60},
        'outcome': {'status': outcome, 'score': score, 'notes': notes},
        'source_type': 'solidify_approved',
        'meta': {
            'ts': __import__('datetime').datetime.now().isoformat(),
            'signal_key': f'solidify_{gene_id}',
            'from_staging': gene_file,
            'to_plan': f'plan/genes/{gene_file}',
        },
        'asset_id': '',
    }
    if declaration:
        evt['meta']['solidify_declaration'] = declaration
    evt['asset_id'] = compute_asset_id(evt)
    return evt


def main():
    parser = argparse.ArgumentParser(description='Solidify — GEP Harness 人工审批流')
    parser.add_argument('--staging', type=str, help='审批整个 staging 目录所有 candidates')
    parser.add_argument('--gene', type=str, help='审批单个 Gene 文件')
    parser.add_argument('--list', action='store_true', help='列出待审批 candidates')
    parser.add_argument('--yes', action='store_true', help='跳过确认直接执行（用于自动化）')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式：无 stdin 时自动拒绝（默认 dry-run safe）')
    parser.add_argument('--change-kind', default=None, help='固化申报：fault_fix（修故障）或 new_capability（新能力）')
    parser.add_argument('--eval-name', default=None, help='前后两侧使用的同一个评测名')
    parser.add_argument('--before-eval', default=None, help='固化前评测名（必须与 --after-eval 相同）')
    parser.add_argument('--after-eval', default=None, help='固化后评测名（必须与 --before-eval 相同）')
    parser.add_argument('--before', default=None, help='固化前的评测数字')
    parser.add_argument('--after', default=None, help='固化后的评测数字')
    parser.add_argument('--evidence', default=None, help='证据文件或日志路径')
    parser.add_argument('--rollback', default=None, help='回滚点（commit、sha 或备份引用）')
    args = parser.parse_args()

    # 加载现有 Gene 表
    existing = load_existing_genes()
    print(f'📦 现有 Gene: {len(existing)} 个')

    # 确定待审批列表
    candidates = []
    if args.staging:
        staging = Path(args.staging)
        candidates = sorted(staging.glob('*.json'))
    elif args.gene:
        candidates = [Path(args.gene)]
    elif args.list:
        staging = Path('/tmp/v_staging')
        candidates = sorted(staging.glob('*.json'))
        for c in candidates:
            g, _decl = load_candidate(c)
            dup, eid, ef = check_duplicate(g, existing)
            valid, vout, verr = validate_gene(g)
            print(f'  {c.name}: id={g.get("id")} | dup={"✅ "+eid if dup else "❌ new"} | valid={"✅" if valid else "❌"}')
        return
    else:
        print('用法: solidify.py --staging=/path/ | --gene=xxx.json | --list')
        sys.exit(1)

    # 逐条审批
    approved = []
    rejected = []
    refused = []
    cli_decl = cli_declaration(args)
    for cand in candidates:
        g, gene_decl = load_candidate(cand)
        gid = g.get('id', cand.stem)
        print(f'\n{"="*60}')
        print(f'📄 {cand.name} → {gid}')
        print(f'   category: {g.get("category")}')
        print(f'   summary: {g.get("summary", "")[:80]}')

        # 检查 DUPLICATE
        dup, eid, ef = check_duplicate(g, existing)
        if dup:
            print(f'   ⚠️  DUPLICATE: matches existing {eid} ({ef})')
            if not args.yes:
                if args.non_interactive:
                    print('   ⏭️  auto-skip duplicate (non-interactive)')
                    rejected.append((gid, 'non_interactive'))
                    continue
                try:
                    resp = input('   仍要审批? [y/N]: ').strip().lower()
                except EOFError:
                    print('   ⏭️  EOFError → auto-skip')
                    rejected.append((gid, 'eof'))
                    continue
                if resp != 'y':
                    print('   ⏭️  skip')
                    rejected.append((gid, 'duplicate'))
                    continue

        # GEP strict validate
        valid, vout, verr = validate_gene(g)
        if not valid:
            print(f'   ❌ VALIDATE FAILED:')
            print(f'   {vout}')
            if not args.yes:
                if args.non_interactive:
                    print('   ⏭️  auto-skip validate_failed (non-interactive)')
                    rejected.append((gid, 'non_interactive'))
                    continue
                try:
                    resp = input('   仍要审批? [y/N]: ').strip().lower()
                except EOFError:
                    print('   ⏭️  EOFError → auto-skip')
                    rejected.append((gid, 'eof'))
                    continue
                if resp != 'y':
                    print('   ⏭️  skip')
                    rejected.append((gid, 'validate_failed'))
                    continue
        else:
            print(f'   ✅ GEP strict: {vout.splitlines()[-1]}')

        # 人工审批门
        if not args.yes:
            if args.non_interactive:
                print('   ⏭️  auto-rejected (non-interactive mode)')
                rejected.append((gid, 'non_interactive'))
                continue
            try:
                resp = input(f'   ✅ 审批 {gid}? [y/N]: ').strip().lower()
            except EOFError:
                print('   ⏭️  EOFError → auto-rejected (non-interactive)')
                rejected.append((gid, 'eof'))
                continue
            if resp != 'y':
                print('   ⏭️  rejected')
                rejected.append((gid, 'user_rejected'))
                continue

        # 固化前申报。人工同意和 --yes 都不能跳过。
        # 分数跳高可能只是修掉了故障，而不是新能力。
        problems, declaration = parse_solidify_declaration(
            merge_declaration(gene_decl, cli_decl)
        )
        if problems:
            print(f'   ❌ 拒绝固化 {gid}：申报不完整或格式错误')
            for problem in problems:
                print(f'      - {problem}')
            refused.append((gid, problems))
            continue

        approved.append((gid, cand, g, declaration))

    # 执行批准
    print(f'\n{"="*60}')
    print(f'📋 审批摘要: {len(approved)} approved, {len(rejected)} rejected, {len(refused)} declaration_refused')

    if refused:
        print('拒绝固化：申报不完整或格式错误，未写入任何 Gene。')
        for rid, problems in refused:
            for problem in problems:
                print(f'  {rid}: {problem}')
        sys.exit(1)

    # v20.0：输出 5 库 dynamic edge 贡献（仅在 approved 存在时）
    if approved:
        from cross_library_auto import get_active_edges
        active = get_active_edges()
        if active is not LIBRARY_GRAPH_EDGE:
            source = 'dynamic_edges (live)'
        else:
            source = 'static baseline (LIBRARY_GRAPH_EDGE)'
        print(f'   📊 信任度贡献: 5 库出度均值 × match_evidence confidence')
        print(f'   ⚙️  当前边权源: {source}')
        print(f'   ┌─────────────┬─────────┐')
        print(f'   │ 库名        │ trust   │')
        print(f'   ├─────────────┼─────────┤')
        try:
            # 拿首个 approved gene 算 trust_score
            sample_gene = approved[0][2]
            from cross_library_auto import trust_score
            signals = sample_gene.get('signals_match', []) or sample_gene.get('signals', []) or []
            summary = sample_gene.get('summary', '')
            for lib in ['BeautifulMathematics', 'cell-biology', 'CognitivePsychology', 'OpenStaxBiology', 'evomap']:
                ts = trust_score(lib, signals, summary)
                print(f'   │ {lib[:13]:13s}│ {ts:.3f}   │')
        except Exception as e:
            print(f'   │ (trust unavailable: {e})            │')
        print(f'   └─────────────┴─────────┘')

    for gid, cand, gene, declaration in approved:
        dest = PLAN_GENES / cand.name
        json.dump(gene, open(dest, 'w'), ensure_ascii=False, indent=2)
        print(f'   ✅ {cand.name} → plan/genes/{cand.name}')

        # 写 solidify event
        evt = make_solidify_event(cand.name, gid, 'approved', declaration=declaration)
        evt_path = PLAN_EVENTS / f'event_solidify_{gid}.json'
        json.dump(evt, open(evt_path, 'w'), ensure_ascii=False, indent=2)
        print(f'   📝 plan/events/event_solidify_{gid}.json')

    # git commit
    if approved:
        subprocess.run(
            ['git', 'add']
            + [str(PLAN_GENES / cand.name) for _, cand, _, _ in approved]
            + [str(PLAN_EVENTS / f'event_solidify_{gid}.json') for gid, _, _, _ in approved],
            cwd=str(GEP_HARNESS), capture_output=True,
        )
        r = subprocess.run(
            ['git', 'commit', '-m',
             f'gep-harness solidify: {len(approved)} genes approved ({",".join(gid for gid, _, _, _ in approved)})'],
            cwd=str(GEP_HARNESS), capture_output=True, text=True
        )
        print(f'   🔖 git: {r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr.strip().splitlines()[-1]}')

    print(f'\n🎉 Solidify done: {len(approved)} approved, {len(rejected)} rejected')


if __name__ == '__main__':
    main()
