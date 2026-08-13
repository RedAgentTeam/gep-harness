# STAGE_4_PLAN — A2A 协议 + Gene Pool（群体层）

> **阶段：** 4 / 4  
> **对应 EvoMap 张昊阳 GIAC 2026 Layer 3（群体层）**  
> **状态：** ✅ DONE（2026-08-14 02:11）
> **子阶段完成情况：**
> - 4.1 A2A 协议定义 + 单节点验证 ✅
> - 4.2 Gene Pool 目录 + import 流程 + cron sync ✅
> - 4.3 GDI v2 评分系统 ✅
> - 4.4 双节点集成测试 ✅
> - 4.5 behavior_feedback_proof 签名 ✅
> - 4.6 版本 release（CHANGELOG v0.4.0 + 协议 v0.2）✅  
> **日期：** 2026-08-14

---

## 目标

把 devagent 演进出来的 Gene **跨 agent / 跨节点共享**，让 OpenClaw 多 agent 网络形成"群体智能"。

---

## EvoMap 三层 Harness 完整图

```
┌─────────────────────────────────────────────────────────────┐
│              Layer 3: 群体层  ← 阶段 4                      │
│   A2A 协议 · Gene Pool · GDI 评分 · 选择压力                │
│   - 节点间 Gene 共享（MIT/Apache 协议）                    │
│   - Capsule 跨节点 replay                                  │
│   - GDI v2: 内容先验 + 离线检查 + 行为反馈                  │
├─────────────────────────────────────────────────────────────┤
│              Layer 2: 进化层  ← 阶段 3 已完成               │
│   Evolver · Gene · Map · 变异/验证/固化                     │
├─────────────────────────────────────────────────────────────┤
│              Layer 1: 连接层  ← 阶段 1+2 已完成            │
│   MCP · Tool-use · 执行环境 · 信号提取                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 阶段 4 三个核心组件

### 1. A2A 协议（Agent-to-Agent）

参考 `/data/disk/githubwiki/evomap/original/gep-mcp-server/`（GEP v1.12.1 §A2A）

| 字段 | 说明 |
|---|---|
| `protocol_version` | `"1.0"` |
| `sender_node_id` | 节点唯一标识（可基于 hostname + ip） |
| `recipient_node_id` | 目标节点（"broadcast" 表示广播） |
| `asset_id` | 携带的 Gene/Capsule asset_id |
| `asset_type` | `"Gene" / "Capsule" / "EvolutionEvent"` |
| `intent` | `"publish" / "request" / "ack" / "reject"` |
| `signature` | 节点对 asset 内容签名（防止伪造） |

**载体**：HTTP（`/api/v1/a2a/{publish,request}`）

### 2. Gene Pool（基因池）

每个节点维护 3 个目录：

```
~/.openclaw/gene-pool/
├── local/        # 本节点 Solidify 的 Gene（canonical）
├── imported/     # 从其他节点 import 的 Gene（带 source_node 标记）
└── quarantined/  # 被本节点 reject 的 Gene（等待人工 review）
```

**同步策略**：
- 每 6h 一次 background sync（cron job）
- 仅 import `intent: publish` 且 `GDI.score >= 0.7` 的 Gene
- import 时自动 audit log 进 `~/.openclaw/gene-pool/audit.jsonl`

### 3. GDI v2 评分（Gene Diagnostic Index）

继承 zhanghaoyang 项目的方法论：

| 维度 | 检查项 | 权重 |
|---|---|---|
| **内容先验** | 具体、完整、可迁移 | 高（0.4）|
| **离线检查** | GEP strict 校验通过 + 5 库 evidence | 中（0.2）|
| **行为反馈** | 本节点已成功 reuse 1+ 次（outcome=success）| 高（0.4）|

**GDI.score** = 加权求和，>= 0.7 才可 publish；>= 0.85 标记为"高质量 Gene"可 broadcast。

---

## 实施步骤（拆分）

### 阶段 4.1：A2A 协议定义 + 单节点验证
- 写 `a2a_protocol.md`（协议规范）
- 写 `a2a_server.py`（HTTP server，绑定 localhost:9877）
- 写 4 个 pytest：protocol / publish / request / reject

### 阶段 4.2：Gene Pool 目录 + import 流程
- 写 `gene_pool.py`（CRUD + audit）
- 写 `gene_sync.py`（6h cron job，sync 自固定 peer）
- 写 3 个 pytest：local / imported / quarantined

### 阶段 4.3：GDI v2 评分系统
- 写 `gdi_v2.py`（加权评分）
- 集成进 Solidify 流程（仅 score >= 0.7 才可 publish）
- 写 3 个 pytest：content_prior / offline_check / behavior_feedback

### 阶段 4.4：双节点测试（可选）
- 在本机跑两个 OpenClaw 实例（端口 27518 + 27519）
- 测 A2A 跨节点 Gene 共享
- 不上美机（避免生产风险）

---

## 关键边界（不豁免）

- ❌ **不引入 Skill 抽象**（Gene 是统一单位）
- ❌ **不引入运行时插件加载**（A2A 只是 schema 层）
- ❌ **不让 Solidify 全自动**（人工审批门）
- ❌ **Gene Pool 不接受未签名资产**（防伪造）
- ❌ **Gene Pool 不写入 OpenClaw 框架源码**（standalone 服务）
- ✅ **A2A 协议必须 MIT 协议开源**（生态化）

---

## 5 库跨学科映射

| 借鉴点 | 5 库映射 |
|---|---|
| **A2A 协议** | BeautifulMathematics Ch12 算法（消息队列）+ cell-biology Ch15 信号传导（cell-cell signaling）+ CognitivePsychology Ch11 推理决策（agent 间协作）+ OpenStaxBiology Ch11 进化（群体遗传）+ evomap GEP §A2A |
| **Gene Pool** | BeautifulMathematics Ch17 分形（局部 + 全局相似性）+ cell-biology Ch12 跨膜运输（选择性交换）+ CognitivePsychology Ch6 长时记忆（跨 session 复用）+ OpenStaxBiology Ch11 进化（基因流）+ evomap evolver-claude-code-plugin |
| **GDI v2 评分** | BeautifulMathematics Ch22 Arrow 定理（多维加权）+ cell-biology Ch9 基因演化（突变选择压力）+ CognitivePsychology Ch11 推理决策（行为反馈偏差）+ OpenStaxBiology Ch11 进化（自然选择阈值）+ evomap GEP §1.4 blast_radius |

---

## 时间估算

| 子阶段 | 工作量 |
|---|---|
| 4.1 A2A 协议 | 2 天 |
| 4.2 Gene Pool | 1.5 天 |
| 4.3 GDI v2 | 1 天 |
| 4.4 双节点测试 | 0.5 天 |
| **总计** | **5 天** |

---

## 与 OpenClaw 现有架构的兼容性

| 组件 | 兼容性 |
|---|---|
| MCP | ✅ A2A 可视为 MCP over HTTP |
| genelab | 🟡 现有 genelab 是单节点搜索，Gene Pool 是分布式——共存 |
| memory-wiki | ✅ Gene Pool audit log 可写进 wiki |
| memory-lancedb | 🟡 可用 LanceDB 存 Gene vector，做语义检索 |

---

## 不在本期做

- ❌ 上美机（只在本机测）
- ❌ 公网 A2A（只 localhost + 本地 peer）
- ❌ 商业化（只科研级 prototype）
- ❌ Gene NFT / 代币化（不引入区块链）

---

## Next Action

启动阶段 4.1（A2A 协议定义 + 单节点验证）：
1. 写 `a2a_protocol.md`
2. 写 `a2a_server.py`（HTTP server）
3. 写 4 个 pytest
4. 写 Gene 资产 `gene_harness_a2a_protocol`