# Trust Audit API — v52.0

> gep-harness v52.0：trust audit 可视化（CLI + Web）
> 落地：`scripts/trust_query.py`（CLI）+ `scripts/trust_web.py`（Flask）

---

## 1. 背景

v50.0 trust audit（integrity + verify + audit log）和 v51.0 trust audit 轮转/查询/统计都只在**内部跑**。v52.0 补一个对外可读的查询接口，让人工/外部能"看得见"哪些 gene 长期没 verify、trust_score 分布如何。

不引入 Skill 抽象（与 OpenClaw Gene/Capsule 体系冲突），不引入运行时插件加载（边界稀释）。

---

## 2. CLI — `trust_query.py`

### 2.1 子命令

| 子命令 | 作用 |
|---|---|
| `query <gene_id>` | 单个 gene 详情（trust_score / verify_count / last_audit）|
| `stats` | 全量 gene 统计（分布 + active_edges）|
| `stale --days N` | 列出 N 天内未 verify 的 gene |

### 2.2 跑法

```bash
python3 scripts/trust_query.py stats
python3 scripts/trust_query.py query gene_candidate_exec
python3 scripts/trust_query.py stale --days 7
```

### 2.3 示例输出

```
📊 Trust Audit Stats
   total_genes: 60
   scores_computed: 60
   trust_score: min=0.231 max=0.770 mean=0.593
   no_audit_gene: 60/60
   active_edges: static
   audit_log_entries: 0
   events_total: 50078
```

```
📊 Gene: gene_candidate_exec
   asset_id: sha256:4fdfc2e3f48b3906e257253097fd0f991286011c6c4998d84a13c8ee03270b7b
   category: repair
   signals: ['high_freq:3266_calls', 'tool_frequent:exec', 'hot_path:exec', 'exec']
   trust_score: 0.77
   verify_count: 0
   active_edges: static
   last_audit: (无)
```

---

## 3. Web — `trust_web.py`（Flask，端口 8765）

### 3.1 路由

| 路径 | 方法 | 作用 |
|---|---|---|
| `/` | GET | 全量 gene 列表（按 trust_score 倒序）|
| `/gene/<gene_id>` | GET | 单个 gene 详情 |
| `/stats` | GET | 统计（分布 + active_edges + stale 名单）|
| `/health` | GET | 健康检查 |

### 3.2 跑法

```bash
python3 scripts/trust_web.py                  # 默认 127.0.0.1:8765
python3 scripts/trust_web.py --port 9000      # 自定义端口
python3 scripts/trust_web.py --host 0.0.0.0   # 暴露外网（不推荐）
```

### 3.3 示例请求

```bash
curl http://127.0.0.1:8765/health
# {"service":"trust_web","status":"ok","version":"v52.0"}

curl http://127.0.0.1:8765/stats | jq
# {
#   "total_genes": 60,
#   "trust_score": {"mean": 0.5929, "bins": {...}},
#   "active_edges": "static",
#   "stale_genes": [...]
# }

curl http://127.0.0.1:8765/gene/gene_candidate_exec | jq
# {"gene_id": "gene_candidate_exec", "trust_score": 0.77, ...}
```

---

## 4. 数据源

| 数据 | 路径 | 备注 |
|---|---|---|
| Gene 定义 | `plan/genes/*.json` | 含 `id` + `asset_id`（sha256）+ `signals_match` |
| 持久化 dynamic_edges | `~/.config/gep-harness/active_edges.json` | XDG 标准 |
| Audit log（append-only）| `~/.config/gep-harness/audit_trust.log` | JSONL |
| 事件流 | `openclaw-harness/events/events.jsonl` | SessionEvent 流水 |

---

## 5. 关键决策

- **trust_score 来源是 `cross_library_auto.trust_score(library, signals, summary, edges)`**（v20.0 接 dynamic edges），不重新造轮子
- **Gene 主键用 `id`（人类可读）+ `asset_id`（sha256 内容寻址）双键**：CLI 按 id 查，asset_id 用于跨进程/跨仓库引用
- **Web 只读，不修改状态**：trust_persist.py 才是写路径，CLI/Web 都只读
- **端口 8765**：避开 22/3000/443/8082 等已知端口

---

## 6. 测试覆盖

`scripts/tests/test_trust_query_web.py` — 10 个测试：

- 5 个 trust_query 单测（list_genes / resolve_gene / get_events）
- 5 个 trust_web 集成测（health / index / gene_detail / 404 / stats）

跑法：

```bash
python3 -m pytest scripts/tests/test_trust_query_web.py -v
```

---

## 7. 已知边界

| 项 | 现状 | 后续 |
|---|---|---|
| events.jsonl | 仅 read，不解析 verify 事件（当前 flow 没 emit verify 事件）| 待 v53+ 加 verify event emit |
| audit_trust.log | v50/v51 已写但本机从未真跑过 trust_persist | 待 cron 6h 真跑后激活 |
| active_edges.json | static 默认 | 待 cron 6h auto-flip 触发后变 dynamic |

---

**版本：** v52.0
**协议：** GEP v1.12.1 strict
**commit：** 待提交