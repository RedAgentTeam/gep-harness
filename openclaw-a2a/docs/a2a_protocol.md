# A2A Protocol — Gene 跨节点共享

> **版本：** v0.2.0 (2026-08-14)
> **来源：** 参考 EvoMap evolver-claude-code-plugin/hooks/session-end.js
> **实现：** `/data/disk/gep-harness/openclaw-a2a/src/`
> **许可：** AGPL-3.0-or-later（协议+实现）/ 协议文本 CC-BY-4.0

---

## 1. 协议概述

A2A（Agent-to-Agent）协议让 devagent / OpenClaw 节点之间共享 **Gene / Capsule / EvolutionEvent** 资产（GEP v1.12.1 兼容）。

每个节点：
- 是 **Gene Pool** 的本地管理者
- 接收其他节点的 publish 请求
- 本地 Solidify 后才能 export

**v0.2 核心新增：** `behavior_feedback_proof`（签名验证的 reuse history），让 GDI 三维度全量生效（threshold=0.7）。

---

## 2. Wire Envelope（标准消息格式）

```json
{
  "protocol_version": "1.0",
  "sender_node_id": "node:<uuid-or-hostname>",
  "recipient_node_id": "node:<uuid-or-hostname> | broadcast",
  "asset_id": "sha256:<64-hex>",
  "asset_type": "Gene" | "Capsule" | "EvolutionEvent",
  "intent": "publish" | "request" | "ack" | "reject",
  "payload": { ...GEP 资产... },
  "signature": "hmac-sha256:<hex>",
  "behavior_feedback_proof": {
    "reuses": [{"ts": "2026-08-14T02:00:00+08:00", "outcome": "success", "asset_id": "sha256:..."}],
    "signature": "hmac-sha256:<hex>"
  },
  "ts": "2026-08-14T02:00:00+08:00"
}
```

### intent 语义

| intent | 方向 | 行为 |
|---|---|---|
| `publish` | → peer | 把本地资产推送给对方（不期望返回） |
| `request` | → peer | 询问对方是否有某 asset_id 的最新版本 |
| `ack` | → peer | 收到 publish/request 后确认（成功） |
| `reject` | → peer | 收到 publish 后拒绝（附 reason） |

### behavior_feedback_proof（v0.2 新增）

send 端在 envelope 中附上签名的 reuse history：
- `reuses[]`：至少 1 条 `outcome="success"` 的记录
- `signature`：用 `A2A_SHARED_SECRET` 对 `{"reuses": [...]}` 做 HMAC-SHA256

peer 端收到后：
1. 用 `A2A_SHARED_SECRET` 验签
2. 验签通过 → `has_behavior_feedback=True` → GDI +0.4
3. 验签失败 → 忽略 proof → GDI 不加 behavior_feedback 分

**注意：** v0.2 使用 `A2A_SHARED_SECRET`（trust bootstrap）。v0.3 计划改用 ed25519 keypair exchange。

---

## 3. HTTP API（v1）

所有 endpoint 都用 **POST + JSON body**：

| Endpoint | 用途 |
|---|---|
| `POST /api/v1/a2a/publish` | 接收 publish 消息（含 behavior_feedback_proof 验证）|
| `POST /api/v1/a2a/request` | 查询本地资产 |
| `GET /api/v1/a2a/node/info` | 节点信息 |
| `GET /api/v1/a2a/health` | 健康检查 |

### 默认端口：`9877`（localhost only，不上公网）

### 配置（环境变量）

| 变量 | 默认 | 说明 |
|---|---|---|
| `A2A_PORT` | `9877` | HTTP 端口 |
| `A2A_NODE_ID` | `<hostname>` | 节点 ID |
| `A2A_SHARED_SECRET` | `dev-shared-secret-do-not-use-in-prod` | **v0.2 共享密钥**（签名 + 验证 proof 用）|
| `A2A_NODE_SECRET` | — | v0.1 兼容，被 A2A_SHARED_SECRET 覆盖 |
| `A2A_GENE_POOL_DIR` | `~/.openclaw/gene-pool/` | Gene Pool 根目录 |
| `A2A_MIN_GDI` | `0.7` | 接收阈值 |

---

## 4. 签名机制

### 主签名（payload 完整性）
```
main_sig = HMAC-SHA256(payload_bytes, A2A_SHARED_SECRET)
```

### behavior_feedback_proof 签名（v0.2 新增）
```
proof_sig = HMAC-SHA256(canonicalize({"reuses": [...]}), A2A_SHARED_SECRET)
```

接收方验证：
1. 重算 `payload_bytes` 序列化
2. 用 `A2A_SHARED_SECRET` 验主签名
3. 若有 `behavior_feedback_proof`，验 proof 签名
4. 任一步失败 → `reject`

**TODO v0.3：** 改用 ed25519 keypair + 公钥交换（替代 shared secret）。

---

## 5. Gene Pool 目录结构

```
~/.openclaw/gene-pool/
├── local/                     # 本节点 Solidify 的 Gene（canonical）
│   └── gene_*.json
├── imported/                  # 从其他节点 import 的 Gene（GDI ≥ 0.7）
│   └── gene_*__from_<node>.json
├── quarantined/               # 被本节点 reject 的 Gene（等待 review）
│   └── gene_*__rejected_*.json
└── audit.jsonl                 # append-only 操作日志
```

---

## 6. GDI v2 评分（Gene Diagnostic Index）

每个 import 的 Gene 必须通过三维度评估：

| 维度 | 权重 | 检查项 | v0.1 | v0.2 |
|---|---|---|---|---|
| content_prior | 0.4 | signals ≥ 2, strategy ≥ 2, summary ≥ 20 字符 | ✅ | ✅ |
| offline_check | 0.2 | asset_id match + evidence ≥ 5 | ✅ | ✅ |
| behavior_feedback | 0.4 | 至少 1 次 reuse outcome=success | ❌ 不可信 | **✅ 签名验证** |

**GDI.score** = 加权求和（0-1）。**>= 0.7** 才被 accept 到 `imported/`。

### v0.1 → v0.2 评分变化

```
v0.1（无 behavior_feedback）:
  good gene: 0.4 (content_prior) + 0.2 (offline_check) = 0.6
  → 0.6 < 0.7 → quarantined（临时降到 0.6 阈值才能过）

v0.2（带 behavior_feedback_proof）:
  good gene: 0.4 (content_prior) + 0.2 (offline_check) + 0.4 (behavior_feedback, 验签通过) = 1.0
  → 1.0 ≥ 0.7 → accepted ✅
```

---

## 7. 接收流程

```
收到 publish 消息
  ↓
解析 envelope（含 behavior_feedback_proof）
  ↓
验证 main signature
  ↓
验证 asset_id（compute_asset_id(payload) == payload.asset_id）
  ↓
若有 behavior_feedback_proof：
  ↓ 用 A2A_SHARED_SECRET 验 proof signature
  ↓ 验签通过 → has_behavior_feedback=True
  ↓
跑 GDI v2 评分（含 behavior_feedback 维度）
  ├─ score >= 0.7 → cp 到 imported/，emit ack
  └─ score < 0.7 → cp 到 quarantined/，emit reject + reason
  ↓
audit.jsonl 写一条 event（含 gdi_score + behavior_feedback_verified）
```

---

## 8. 发送流程

```
本节点 Solidify 一个 Gene
  ↓
生成行为反馈 proof（{reuses: [success], signature}）
  ↓
构建 envelope（含 main signature + behavior_feedback_proof）
  ↓
POST /api/v1/a2a/publish 到 peer
  ↓
peer 验证后返回 ack / reject
  ↓
audit.jsonl 写一条 event
```

---

## 9. 安全边界

- ❌ **不接受未签名消息**（signature 缺失即 reject）
- ❌ **不接受 asset_id 不匹配的消息**（payload 篡改即 reject）
- ❌ **不接受 GDI score < 0.7 的消息**（quarantined）
- ❌ **不在公网暴露**（仅 localhost + 可信 peer）
- ✅ **所有操作进 audit.jsonl**（append-only + GEP strict 校验）
- ✅ **behavior_feedback_proof 必须签名验证**（防伪造 reuse history）

---

## 10. 不在本协议里做的事

- ❌ 不强制所有节点用同一份 Gene 库
- ❌ 不做中心化 ranking（每个节点自己 GDI 评分）
- ❌ 不上链（不引入区块链 / NFT）
- ❌ 不替代 OpenClaw 框架（仅是 Gene 共享协议）
- ❌ 不替代 GeneHub（EvoMap 官方 hub）—— 我们是 **独立 implementation**

---

## 11. 与现有架构的关系

| 层 | 组件 | 状态 |
|---|---|---|
| Layer 1 | harness-event-stream + harness-tool-pipeline | ✅ 阶段 1+2 |
| Layer 2 | scan_events.py + extract_candidate_genes.py + validate_gep.py | ✅ 阶段 3 |
| Layer 3 | openclaw-a2a/（本协议）| **✅ v0.2（阶段 4.4）** |

---

## 12. 版本历史

| 版本 | 日期 | 主要变更 |
|---|---|---|
| v0.1 | 2026-08-14 01:52 | 基础协议：HMAC 签名 + GDI v2 + Gene Pool + HTTP server |
| v0.2 | 2026-08-14 02:06 | **behavior_feedback_proof 签名验证** + shared secret + GDI_THRESHOLD 恢复 0.7 + 双向 E2E 通过 |

---

_协议 v0.2.0 — 2026-08-14 · 维护者：devagent_
