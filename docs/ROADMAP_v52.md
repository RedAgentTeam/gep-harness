# ROADMAP v52.0 — trust audit 可视化（CLI + Web）

> gep-harness v52.0
> 时间：2026-09-01
> 上一版：v51.0（trust audit 轮转 + 查询 + 统计）

---

## 1. 目标

把 trust audit 从**只在内跑**升级到**对外可读**：
- CLI：trust_query.py（query / stats / stale 三个子命令）
- Web：trust_web.py（Flask，端口 8765，路由 / /gene/<id> /stats /health）

不引入 Skill 抽象（与 OpenClaw Gene/Capsule 体系冲突），不引入运行时插件加载（边界稀释）。

---

## 2. 新增/修改

### 2.1 新增

| 文件 | 行数 | 作用 |
|---|---|---|
| `scripts/trust_query.py` | ~220 | CLI（query/stats/stale）|
| `scripts/trust_web.py` | ~180 | Flask Web（4 路由）|
| `scripts/tests/test_trust_query_web.py` | ~130 | 10 个 pytest |
| `docs/TRUST_API.md` | ~150 | API 文档 |

### 2.2 复用（v51.0 已有）

- `scripts/cross_library_auto.py::trust_score()` — 信任评分计算
- `scripts/trust_persist.py` — 持久化 dynamic_edges
- `scripts/trust_auto_flip.py` — dynamic 切换
- `~/.config/gep-harness/active_edges.json` — 持久化数据
- `~/.config/gep-harness/audit_trust.log` — audit log

---

## 3. 关键设计

### 3.1 Gene 双主键

- `id`（人类可读，如 `gene_candidate_exec`）— CLI/Web 主键
- `asset_id`（`sha256:xxx`）— 内容寻址 + 跨仓库唯一

`_resolve_gene()` 同时按 id / asset_id 前缀 / 模糊匹配三种方式查找。

### 3.2 Web 只读

trust_web.py 只读，不修改 trust_score / audit_log / active_edges。**写路径只有 trust_persist.py**（CLI 写入，cron 6h 触发）。

### 3.3 端口 8765

避让已知服务：22 / 80 / 443 / 3000 / 3001 / 3002 / 8082 / 9090。

---

## 4. 测试

```
scripts/tests/test_trust_query_web.py::test_list_genes_non_empty PASSED
scripts/tests/test_trust_query_web.py::test_list_genes_has_signals_match PASSED
scripts/tests/test_trust_query_web.py::test_resolve_gene_by_id PASSED
scripts/tests/test_trust_query_web.py::test_resolve_gene_not_found PASSED
scripts/tests/test_trust_query_web.py::test_get_events_readable PASSED
scripts/tests/test_trust_query_web.py::test_web_health PASSED
scripts/tests/test_trust_query_web.py::test_web_index PASSED
scripts/tests/test_trust_query_web.py::test_web_gene_detail PASSED
scripts/tests/test_trust_query_web.py::test_web_gene_404 PASSED
scripts/tests/test_trust_query_web.py::test_web_stats PASSED

============================= 10 passed in 15.73s =============================
```

全量 pytest：`656 passed, 3 failed`（3 个失败是 test_check_5lib_assets.py 时间戳断言顺序问题，单跑全过，与 v52.0 无关）。

---

## 5. 烟测（curl）

```bash
$ curl http://127.0.0.1:8765/health
{"service":"trust_web","status":"ok","version":"v52.0"}

$ curl http://127.0.0.1:8765/stats | jq .trust_score.bins
{
  "0.0-0.2": 0,
  "0.2-0.4": 5,
  "0.4-0.6": 31,
  "0.6-0.8": 24,
  "0.8-1.0": 0
}

$ curl http://127.0.0.1:8765/gene/gene_candidate_exec
{"gene_id": "gene_candidate_exec", "trust_score": 0.77, ...}

$ curl -o /dev/null -w "%{http_code}" http://127.0.0.1:8765/gene/bogus
404
```

---

## 6. 与既有体系的对齐

| 项 | v52.0 是否触碰 | 备注 |
|---|---|---|
| Gene/Capsule 抽象 | ❌ | 复用 cross_library_auto.trust_score |
| Skill 抽象 | ❌ | 严格遵守"不引入 Skill 抽象"原则 |
| 运行时插件加载 | ❌ | 静态 import |
| GEP v1.12.1 strict | ✅ | asset_id sha256 链路完整 |
| cron 6h 联动 | ⚠ | 待 v53+ 加（auto-flip 后 emit audit event 到 events.jsonl）|

---

## 7. 后续 TODO（v53+）

| # | 项 | 优先级 |
|---|---|---|
| 1 | cron 6h auto-flip 后 emit audit 事件到 events.jsonl | P1 |
| 2 | gene 扩到 25-30 个 hotpath gene（evolver Scan→Signal→Mutate）| P1 |
| 3 | trust_web 加 /flip 端点（写路径，需鉴权）| P2 |
| 4 | Web UI 改成 SPA（Vue 3）| P3 |

---

**版本：** v52.0
**协议：** GEP v1.12.1 strict
**测试：** 10/10 PASS（v52.0 新增）
**全量：** 656/659 PASS（3 个 pre-existing 时间戳顺序问题）
**作者：** devagent