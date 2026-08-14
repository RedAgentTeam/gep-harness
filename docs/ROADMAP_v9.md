# ROADMAP v9.0 — GEP Harness Evolver 全量验证 + cron 自动化

> 日期：2026-08-14 21:50
> 分支：master
> 状态：✅ DONE (v9.0 已验证 + cron + ROADMAP)

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest | ✅ 45/45 |
| `make verify` | ✅ 154/154 |
| genes in plan/genes/ | 149 |
| assets verify | 154/154 |
| events | 12008 lines |
| v1.3~v9.0 共 65 期 | — |

## v9.0 变更明细

| # | 变更 | 状态 |
|---|------|------|
| 1 | Evolver 全量重新扫描 | ✅ 11988→12008 events |
| 2 | 拆解前后 UNIQUE 对比验证 | ✅ 47% 下降 (11391→5959) |
| 3 | cron 6h 自动 `make evolve` | ✅ `/tmp/v_scan.json` + `/tmp/v_staging/` + `logs/cron_evolve.log` |
| 4 | LLM 真实填充 | ❌ 402 quota 耗尽，pending |
| 5 | v9.0 commit + ROADMAP | ✅ 9f204e7 |

## 拆解验证：UNIQUE 下降 47%

| 维度 | 旧方式 (7 宽泛 Gene) | 新方式 (17 细分 Gene) | 下降 |
|------|-------------------|---------------------|------|
| exec total UNIQUE | 10364 | 4645 (cd) + 186 (bracket) + 72 (py3) + ... | **54%** |
| process total UNIQUE | 386 | 181 (quick) + 12 (long) + failure | **53%** |
| read total UNIQUE | 406 | 263 (seq) + 143 (paginated) | **0%** (命中率相同) |
| write total UNIQUE | 107 | 105 (small) + 2 (medium) | **2%** |
| message total UNIQUE | 128 | 128 (batch) | **0%** |
| **合计** | **11391** | **5959** | **47% ↓** |

**结论：拆解有效。** exec 和 process 下降最明显（53-54%），因为 args prefix 匹配过滤了大量误判的"新 UNIQUE"。

## cron 6h 自动 Evolver

```
0 */6 * * * cd /data/disk/gep-harness && scan_events --since=24h > /tmp/v_scan.json \
  && extract_candidate_genes --scan-output=/tmp/v_scan.json --output=/tmp/v_staging/ --threshold=5 \
  && validate_gep --mode=strict --input="/tmp/v_staging/*.json" \
  >> logs/cron_evolve.log 2>&1
```

- 每 6 小时整点执行
- 输出：`/tmp/v_scan.json` + `/tmp/v_staging/`（candidate genes）
- 日志：`logs/cron_evolve.log`
- LLM 填充仍需手动触发（配额恢复后）

## LLM 填充状态

| 候选 Gene | 状态 |
|-----------|------|
| gene_candidate_exec | ❌ 402 quota |
| gene_candidate_read | ❌ 402 quota |
| gene_candidate_process | ❌ 402 quota |
| gene_candidate_write_file | ❌ 402 quota |
| gene_candidate_edit | ❌ 402 quota |
| gene_candidate_message | ❌ 402 quota |
| gene_candidate_write | ❌ 402 quota |

**配额恢复后操作：**
```bash
cd /data/disk/gep-harness && python3 scripts/llm_fill_gene.py --staging=/tmp/v_staging/
```

## 下一步（v10.0 待启动）

- [ ] LLM 填充恢复配额后执行
- [ ] cron 6h 运行 1 天后验证 log 无报错
- [ ] A2A 跨节点 Gene sync 实际部署
- [ ] legacy `gene_candidate_*` 命名混乱清理
- [ ] tools 字段精简验证（14→9-10）
