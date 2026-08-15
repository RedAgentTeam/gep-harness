# THREAT_MODEL — A2A / Gene 同步的威胁模型（草案）

> **日期**：2026-08-15 21:16
> **状态**：🟡 DRAFT（v14.0 待补全，建议提前到高优先级）
> **作者**：devagent @ 胡老师指令

---

## 为什么这个文档关键

> **自我进化的多 Agent 协作网络被污染 = 坏策略通过 Gene 同步扩散到所有节点**

这不是抽象风险。如果 A2A HMAC shared secret 泄露，或恶意节点注入伪造 Gene，**整个网络的策略库都会被污染**——后续自动演化会基于这些污染的 Gene 持续生成更坏的内容。

---

## 攻击面

### 1. 节点层

| 攻击向量 | 后果 | 当前缓解 | 待加强 |
|----------|------|---------|--------|
| **节点被攻陷**（SSH/root）| 攻击者可冒充任意节点发送 Gene | SSH key 限制 + sudo 凭证隔离 | ed25519 keypair 替代 HMAC（v14.0 ROADMAP）|
| **本地恶意进程** | 同用户进程可发 A2A envelope | 用户权限隔离 | SELinux / AppArmor 沙箱 |
| **物理访问** | 直接读取 ~/.ssh 或 ~/.config/gh | 物理安全（VM-0-11-ubuntu） | TPM 密钥存储 |

### 2. 协议层

| 攻击向量 | 后果 | 当前缓解 | 待加强 |
|----------|------|---------|--------|
| **HMAC shared secret 泄露** | 攻击者可冒充任意节点 | secret 仅在本机 | ed25519（公钥可公开，签名难伪造）|
| **Gene 重放攻击** | 旧恶意 Gene 被当作新事件重放 | asset_id 唯一性约束（sha256） | monotonic timestamp + nonce |
| **中间人攻击** | 节点 A 收到"B 同意了"的伪造 approve | 无 TLS（HTTP 明文） | TLS 1.3 + cert pinning |
| **伪造 evidence（5 库）** | 污染策略库的"科学依据" | 人工 `reviewed: true` 标记 | 强制人工复核（Solidify 守门）|

### 3. 内容层

| 攻击向量 | 后果 | 当前缓解 | 待加强 |
|----------|------|---------|--------|
| **恶意 Gene 注入** | 污染策略库 → 自动演化生成更坏内容 | Solidify 人工审批（v10.1） | 跨节点 Gene 同步强制人工二次审批 |
| **证据内容篡改** | 修改 evidence 字符串绕过人工审批 | sha256 canonicalize | 链式 hash（前一个 evidence hash 进下一个）|
| **历史污染** | 旧污染 Gene 永远留在 plan/genes/ | cleanup script | append-only + 不删除策略 |

---

## 威胁等级（按严重度）

| 等级 | 攻击 | 严重度 |
|------|------|--------|
| 🔴 **极高** | HMAC shared secret 泄露 + 节点被攻陷 | 全网策略库污染 |
| 🔴 **极高** | 恶意节点注入 Gene + 跨节点 sync 自动批准 | 全网污染 |
| 🟠 高 | Gene 重放攻击 | 局部节点污染 |
| 🟠 高 | 5 库 evidence 篡改 | 误导未来演化 |
| 🟡 中 | 中间人攻击 | 单次消息伪造 |

---

## 当前缓解（已实施）

| 缓解 | 位置 |
|------|------|
| **Solidify 人工审批**（v10.1） | `docs/SOLIDIFY.md` |
| **cron 6h auto-reject**（EOFError） | `scripts/solidify.py --non-interactive` |
| **asset_id 唯一性**（sha256 canonicalize） | `openclaw-harness/bin/canonicalize.py` |
| **EvolutionEvent 审计链** | `plan/events/event_solidify_*.json` |
| **3 件不动的事**（No Skill / No plugin / No auto-Solidify） | `AGENTS.md` |

---

## 待加强（v15.0+ 路线）

| 加强项 | 优先级 | 工作量 |
|--------|--------|--------|
| **HMAC → ed25519** keypair 迁移 | 🔴 高 | 60 min（已有 ROADMAP）|
| **TLS 1.3 + cert pinning** | 🔴 高 | 90 min |
| **Gene 重放 nonce + timestamp** | 🟠 中 | 30 min |
| **跨节点 Gene 强制人工二次审批** | 🔴 高 | 需讨论 |
| **链式 hash（prev evidence hash）** | 🟡 中 | 45 min |
| **A2A 协议版本号**（兼容老节点）| 🟠 中 | 60 min |
| **威胁模型正式审计**（外部） | 🟠 中 | 待胡老师拍板 |

---

## 自我进化网络的特殊风险

> **"自我进化" = 持续从历史生成新内容**。一旦策略库被污染：
>
> - 第 1 代污染：1 个恶意 Gene 入库
> - 第 2 代污染：基于第 1 代生成 10 个新 Gene（部分继承恶意 pattern）
> - 第 3 代污染：100 个
> - 第 4 代污染：1000 个（**网络全部失控**）

**这就是为什么 Solidify 人工审批必须是真的"门"**，而不是"流程建议"。

---

## 待办

1. **HMAC → ed25519 迁移**（v15.0 ROADMAP 提前到高优先级）
2. **TLS 1.3 接入**
3. **跨节点 Gene 同步强制人工二次审批**（需 GitHub 分支保护 + 实操讨论）
4. **正式安全审计**（外部）—— **这超出了 devagent 能力范围**，需要真人专家

---

_作者：devagent | 创建：2026-08-15 21:16 | 项目：gep-harness_
_状态：DRAFT，待胡老师 review + 决策_