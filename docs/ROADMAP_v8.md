# ROADMAP v8.x — GEP Harness Evolver 5 Tool 热路径全拆解

> 日期：2026-08-14 21:20
> 分支：master
> 状态：✅ ALL DONE (v8.0~v8.4)

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 154/154 |
| 拆解 Gene 总数 | 17 |
| events | 11708 lines |

## v7.5 → v8.4 拆解全景

| 期 | tool | new Gene | 拆解维度 | commit |
|----|------|----------|----------|--------|
| v8.0 | exec | 7 | cd/python3/ls/sudo/cat_curl/misc_shell/bracket_test | ede225d |
| v8.1 | process | 3 | long_run/quick_run/command_failure | ee3d0ea |
| v8.2 | message | 2 | batch_send/single_send | 5df985f |
| v8.3 | read | 2 | sequential/paginated | ff2b619 |
| v8.4 | write | 3 | small_content/medium_content/multi_path | 961cc54 |

## 拆解前后对比

| 指标 | v7.5 (拆解前) | v8.4 (拆解后) | 变化 |
|------|---------------|---------------|------|
| genes in plan/genes/ | 132 | 149 | +17 |
| assets verify | 137 | 154 | +17 |
| events | 11358 | 11708 | +350 |
| "exec" hotpath | 1 broad Gene | 7 args-prefix Genes | 拆解完成 |
| "process" hotpath | 1 broad Gene | 3 scenario Genes | 拆解完成 |
| "message" hotpath | 1 broad Gene | 2 pattern Genes | 拆解完成 |
| "read" hotpath | 1 broad Gene | 2 mode Genes | 拆解完成 |
| "write" hotpath | 1 broad Gene | 3 size/path Genes | 拆解完成 |

## A. exec 拆解 (v8.0)

| Gene | prefix | calls/24h | 占比 |
|------|--------|-----------|------|
| gene_exec_cd_v80 | `cd` | 4493 | 90.6% |
| gene_exec_bracket_test_v80 | `[` | 184 | 3.7% |
| gene_exec_python3_v80 | `python3` | 70 | 1.4% |
| gene_exec_ls_v80 | `ls` | 56 | 1.1% |
| gene_exec_misc_shell_v80 | `echo/tail/find/bash` | 76 | 1.5% |
| gene_exec_sudo_v80 | `sudo` | 34 | 0.7% |
| gene_exec_cat_curl_v80 | `cat/curl` | 36 | 0.7% |

**核心观察**：cd 占 90.6%——这是 exec 100% UNIQUE 的根因。
拆分后 exec 宽泛 Gene 的 UNIQUE 频率应大幅下降（从 63/63 → 预期 <10/63）。

## B. process 拆解 (v8.1)

| Gene | 场景 | calls/24h | 占比 |
|------|------|-----------|------|
| gene_process_quick_run_v81 | ≤30s 快速 | 358 | 96% |
| gene_process_long_run_v81 | >30s 长跑 | 12 | 3% |
| gene_process_command_failure_v81 | exit_code!=0 | ~5-10% | est. |

**核心观察**：process 96% 在 30s 内完成（median 98ms），3% 长跑 >30s（max 30558ms）。
拆分后 process 反弹 UNIQUE 应从 22/63 降至 <5/63。

## C. message 拆解 (v8.2)

| Gene | 场景 | calls/24h | 占比 |
|------|------|-----------|------|
| gene_message_batch_send_v82 | batch (<5s gap) | 123 | 99% |
| gene_message_single_send_v82 | single (≥5s gap) | ~1 | <1% |

**核心观察**：124 条 message 全部在 1 个 session，99% gap <5s = batch 模式。
message 工具 UNIQUE 频率应稳定在 <5/63。

## D. read 拆解 (v8.3)

| Gene | 场景 | calls/24h | 占比 |
|------|------|-----------|------|
| gene_read_sequential_v83 | offset=0/limit=0 全量读 | 267 | 66% |
| gene_read_paginated_v83 | offset>0 或 limit>0 分页 | 139 | 34% |

**核心观察**：66% read 是全量读（offset=0/limit=0），可直接缓存；34% 是分页读需要预取优化。

## E. write 拆解 (v8.4)

| Gene | 场景 | calls/24h | 占比 |
|------|------|-----------|------|
| gene_write_small_content_v84 | <10KB 小内容 | 101 | 98% |
| gene_write_multi_path_v84 | 多路径去重 | 18 | 72% paths |
| gene_write_medium_content_v84 | 10-100KB 中内容 | 2 | 2% |

**核心观察**：98% write 是小内容 (<10KB)，multi-path 72% 路径有重复写，合并空间大。

## v1.3~v8.4 收敛趋势（64 期）

| 期 | new | dup | 节点 |
|----|-----|-----|------|
| v8.0 | 7 | 0 | 全拆解 |
| v8.1 | 3 | 0 | 全拆解 |
| v8.2 | 2 | 0 | 全拆解 |
| v8.3 | 2 | 0 | 全拆解 |
| v8.4 | 3 | 0 | 全拆解 |

**v8.0~v8.4 五路全拆解**，0 DUPLICATE，全部是新 UNIQUE Gene。

## 高频工具累计 UNIQUE（v1.3~v8.4 共 64 期）

| Tool | v7.5 UNIQUE | v8.4 状态 | 拆解后预期 |
|------|-------------|-----------|-----------|
| exec | 63/63 | 7 args-prefix Genes | <10/63 |
| process | 22/63 | 3 scenario Genes | <5/63 |
| read | 13/63 | 2 mode Genes | <5/63 |
| message | 13/63 | 2 pattern Genes | <5/63 |
| write | 5/63 | 3 size/path Genes | <3/63 |

## 下一步建议

- [ ] **v9.0: Evolver 全量重新扫描**（拆解后 5 工具 UNIQUE 是否下降，验证拆解效果）
- [ ] **v9.0: LLM 真实填充**（402/500 quota 恢复后）
- [ ] **v9.0: 5 库 cross-library evidence 自动生成**
- [ ] **v9.0: cron 6h 自动 `make evolve`**
- [ ] **v9.0: A2A 跨节点 Gene sync 实际部署**
- [ ] **v9.0: 干掉 legacy `gene_candidate_*` 命名混乱**
- [ ] **v9.0: tools 字段精简验证**（14 字段拆解后是否可降为 9-10）
