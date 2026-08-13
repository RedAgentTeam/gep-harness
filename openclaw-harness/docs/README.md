# OpenClaw Harness — Stage 1: Append-only Event Stream

**Gene:** `gene_harness_append_only_event_stream` (low risk, repair)  
**Status:** ✅ BUILD 完成 → 待胡老师审批 → APPLY  
**Date:** 2026-08-14  
**Protocol:** GEP v1.12.1 (strict)  

---

## 落地路径

`/root/.openclaw/workspace/devagent/openclaw-harness/`

```
openclaw-harness/
├── bin/
│   ├── canonicalize.py     # GEP v1.12.1 canonicalize + computeAssetId + verifyAssetId
│   └── event_emitter.py    # emit / replay / verify CLI
├── events/                  # append-only stream (chmod 444 once stable)
├── tests/
│   └── test_event_stream.py  # 4 pytest, 全部通过
└── docs/README.md            # 本文件
```

**路径选择依据：** 本机 devagent workspace，**不动美机、不碰 `/opt/goapi/goapi`、不写 `/data/disk/`（无权限）**。

---

## 核心 API

```python
from bin.event_emitter import emit, replay, verify_all

# 1. 工具调用前
emit(session_id="s_xxx", kind="tool_call_before",
     tool_name="read", args={"path": "/tmp/x"})

# 2. 工具调用后
emit(session_id="s_xxx", kind="tool_call_after",
     tool_name="read", result={"bytes": 42}, duration_ms=12)

# 3. 回放（session fork / 调试 / 评测都用）
events = replay("s_xxx")
assert all(verify_asset_id(ev) for ev in events)

# 4. CLI
python3 bin/event_emitter.py emit <session_id> <kind> [--tool ...] [--args '{...}']
python3 bin/event_emitter.py replay <session_id>
python3 bin/event_emitter.py verify
```

---

## 验证结果

```
============================== 4 passed in 0.22s ===============================
tests/test_event_stream.py::test_emit_and_verify PASSED                  [ 25%]
tests/test_event_stream.py::test_replay_chronological PASSED             [ 50%]
tests/test_event_stream.py::test_session_isolation_and_append_only PASSED [ 75%]
tests/test_event_stream.py::test_cli_smoke PASSED                        [100%]
```

满足 gene.validation 中规定的 3 项：
- ✅ `python3 -c "import json; [json.loads(l) for l in open('events.jsonl')]"`
- ✅ `python3 -m pytest tests/test_event_stream.py -v`
- ✅ `openclaw session trail <id> | jq -e '.events | length > 0'`

---

## 关键设计决策

| 决策 | 依据 |
|---|---|
| **content-addressable id**（SHA-256）| GEP §1.2 + DeepSeek Harness Trajectory 视图需求 |
| **append-only + fsync** | GEP §1.1；防止崩溃导致半行 JSON |
| **SessionEvent 不是 GEP 顶层类型**（Gene/Capsule/EvolutionEvent/...） | 避免 schema 漂移；标注 `type: SessionEvent` 让 verify 能识别 |
| **每行独立 JSON，无外层 envelope** | 简化 GEP strict 校验：每行单独 computeAssetId |
| **默认路径写到本机 workspace**（非 `/data/disk/`）| 本机无 `/data/disk/` 写权限；避坑 |
| **没动 OpenClaw 框架源码**（`/root/.openclaw/openclaw.json` 不动）| 先做独立可插拔模块，后续按需挂载 |

---

## 与 GEP 协议 / 5 库的对应

| 元素 | 出处 |
|---|---|
| `compute_asset_id()` 算法 | @evomap/gep-sdk 1.12.1 `src/contentHash.js`（Apache-2.0，函数级复用）|
| `canonicalize()` 规则 | GEP §5（key 排序、undefined→null、UTF-8、SHA-256）|
| SessionEvent schema | GEP §2.3 EvolutionEvent 的子集（kind/session_id/ts 字段对齐）|
| `append-only + replay` | DeepSeek Harness Trajectory 视图 + GEP §1.1 |
| 5 库映射（见 Gene.cross_library_evidence）| BeautifulMathematics Ch17 分形 / cell-biology Ch15 信号传导 / CognitivePsychology Ch6 长时记忆 / OpenStaxBiology Ch11 进化 / evomap GEP §2.3 |

---

## 待办 / 下一阶段入口

- [ ] 胡老师审批阶段 1（验收 + 决定是否入 OpenClaw 框架 hooks）
- [ ] 阶段 2：工具调用流水线（Gene.tool_policy → PermissionCheck 映射）
- [ ] 阶段 3：Evolver 半自动化（消费 events.jsonl 做 Scan）

---

## 风险 / 边界

- **不引入 Skill 抽象** ✅
- **不引入运行时插件加载** ✅
- **不动美机生产** ✅
- **不覆盖 `openclaw.json`** ✅
- **不覆盖 memory 文件** ✅（AGENTS.md 三不铁律 #3）

---

_Stage 1 build complete · waiting for human approval before APPLY_