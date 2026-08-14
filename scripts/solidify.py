#!/usr/bin/env python3
"""Solidify — GEP Harness 候选 Gene 人工审批流

用法:
  python3 solidify.py --staging=/tmp/v_staging/         # 审批所有 staging candidates
  python3 solidify.py --gene=gene_exec_cd_v80.json      # 审批单个 Gene
  python3 solidify.py --list                              # 列出待审批 candidates

流程:
  1. scan plan/genes/ 现有 Gene → 建 DUPLICATE 检测表
  2. 提取 candidates → 逐条检查 DUPLICATE
  3. 逐条 GEP strict validate
  4. 打印审批摘要 → 等待用户 approved
  5. 复制到 plan/genes/ + 写 plan/events/ + commit

Solidify 是硬性人工审批门，不自动执行。
"""
import argparse
import json
import hashlib
import subprocess
import sys
from pathlib import Path

GEP_HARNESS = Path('/data/disk/gep-harness')
PLAN_GENES = GEP_HARNESS / 'plan/genes'
PLAN_EVENTS = GEP_HARNESS / 'plan/events'
STAGING = Path('/tmp/v_staging')


def compute_asset_id(g):
    """GEP strict canonicalize (same as canonicalize.py)"""
    protected = {'type', 'schema_version', 'id', 'signals_match', 'preconditions',
                 'constraints', 'validation', 'asset_id'}
    payload = {k: v for k, v in g.items() if k not in protected and not k.startswith('_')}
    return 'sha256:' + hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',',':')).encode()
    ).hexdigest()


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


def make_solidify_event(gene_file, gene_id, outcome, score=0.85, notes=''):
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
    evt['asset_id'] = compute_asset_id(evt)
    return evt


def main():
    parser = argparse.ArgumentParser(description='Solidify — GEP Harness 人工审批流')
    parser.add_argument('--staging', type=str, help='审批整个 staging 目录所有 candidates')
    parser.add_argument('--gene', type=str, help='审批单个 Gene 文件')
    parser.add_argument('--list', action='store_true', help='列出待审批 candidates')
    parser.add_argument('--yes', action='store_true', help='跳过确认直接执行（用于自动化）')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式：无 stdin 时自动拒绝（默认 dry-run safe）')
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
            g = json.load(open(c))
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
    for cand in candidates:
        g = json.load(open(cand))
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

        approved.append((gid, cand))

    # 执行批准
    print(f'\n{"="*60}')
    print(f'📋 审批摘要: {len(approved)} approved, {len(rejected)} rejected')
    for gid, cand in approved:
        dest = PLAN_GENES / cand.name
        json.dump(json.load(open(cand)), open(dest, 'w'), ensure_ascii=False, indent=2)
        print(f'   ✅ {cand.name} → plan/genes/{cand.name}')

        # 写 solidify event
        evt = make_solidify_event(cand.name, gid, 'approved')
        evt_path = PLAN_EVENTS / f'event_solidify_{gid}.json'
        json.dump(evt, open(evt_path, 'w'), ensure_ascii=False, indent=2)
        print(f'   📝 plan/events/event_solidify_{gid}.json')

    # git commit
    if approved:
        subprocess.run(['git', 'add'] + [str(PLAN_GENES / c.name) for _, c in approved] +
                       [str(PLAN_EVENTS / f'event_solidify_{g}.json') for g, _ in approved],
                       cwd=str(GEP_HARNESS), capture_output=True)
        r = subprocess.run(
            ['git', 'commit', '-m', f'gep-harness solidify: {len(approved)} genes approved ({",".join(g for g,_ in approved)})'],
            cwd=str(GEP_HARNESS), capture_output=True, text=True
        )
        print(f'   🔖 git: {r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr.strip().splitlines()[-1]}')

    print(f'\n🎉 Solidify done: {len(approved)} approved, {len(rejected)} rejected')


if __name__ == '__main__':
    main()
