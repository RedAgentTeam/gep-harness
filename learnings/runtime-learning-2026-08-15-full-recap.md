# Runtime Learning — gep-harness 完整复盘（2026-08-15）

> **日期**：2026-08-15 13:19
> **范围**：从微信文章 → 自进化 Harness → 协作网络/evomap → 跨学科 5 库
> **作者**：devagent
> **类型**：runtime learning（项目 runtime 阶段经验沉淀）

---

## 0. 元信息

| 字段 | 值 |
|---|---|
| 项目 | gep-harness |
| 路径 | `/data/disk/gep-harness/` |
| 阶段 | v0.4 → v14.0 |
| commit 数 | 60+ |
| Gene 数 | 152 (清理后 7 候选) |
| Event 数 | 13396+ |
| pytest | 16/16 |
| GEP strict | 7/7 |

---

## 1. 起点：一条微信文章（v0.4 — 借鉴阶段）

### 1.1 触发

```
mp.weixin.qq.com/s/hHCpyIlDiBHSzA3TzO5LmQ
《DeepSeek 把 Harness 开源了》
```

胡老师指示：**使用 5 个跨学科知识库作为分析视角，开 Plan，严格执行 GEP 协议**。

### 1.2 关键决策

**3 件不动的事**（v0.4 锁定）：

1. **不引入 Skill 抽象** —— OpenClaw 用 Gene/Capsule（~230 tokens 策略单元）
2. **不引入运行时插件加载** —— Cordis 式动态注入会稀释 Gene 信号匹配精度
3. **Solidify 必走人工审批** —— CognitivePsychology 9 大认知错觉 + Arrow 定理

### 1.3 教训

- 借鉴开源项目必须**先识别 3 件不能动的事**（防止破坏现有体系）
- 不要让借鉴变成"重新发明"

---

## 2. 自进化 Harness（v0.4 → v0.10）

### 2.1 阶段路径

```
v0.4  Append-only 事件流               ✅ 1 件
v0.6  工具调用流水线（Gene.tool_policy → PermissionCheck）  ✅ 1 件
v0.9  Evolver 半自动（Scan/Signal/Mutate 自动 + Solidify 人工）  ✅ 1 件
v0.10 全链路验证（45/45 pytest + 10/10 genes + 2/2 capsules）   ✅ 1 件
```

### 2.2 关键设计

**append-only event_stream**：
- sha256 content-addressable id 替代 uuid
- `events.jsonl` = 只读源，session fork 时复制事件流前缀
- 跨 session 引用可去重

**Evolver 3 阶段**：
- Scan：扫 events.jsonl 找高频 pattern
- Signal：signal → 信号匹配
- Mutate：mut → 生成候选 Gene
- Solidify：**人工审批**（不允许全自动）

### 2.3 教训

- 自进化 = **append-only + 人工审批**，缺一不可
- 全自动 = 必然污染路由精度（参考今晚 Plan B 推演）

---

## 3. 协作网络 / evomap（v1.0 → v10.1）

### 3.1 阶段路径

```
v1.0  Evolver semi-auto loop verified (3318 events)
v1.1  Evolver semi-auto loop with decay strategy
v1.3  7 hotpath candidate genes (exec/read/edit/write_file/process/write/message)
v3.0+ 65 期 ROADMAP 演化
v9.0  47% UNIQUE 下降（11391→5959）
v10.1 cron 6h cycle + Solidify safe reject (--non-interactive + EOFError)
```

### 3.2 关键设计

**Solidify safe reject (v10.1)**：
- cron 跑 Solidify 时遇到 EOF（无 stdin）= 自动 reject
- 守护 v10.1 = cron 6h cycle 不会污染 plan/genes/
- **今晚实战验证**：cron 跑出 6 候选 → 全部 auto-rejected ✅

**A2A 协作网络**：
- mock_peer.py + signature + behavior_feedback_proof
- 双向 157/157 验证（A→B + B→A）

### 3.3 教训

- 协作 = **协议 + 守护 + 人工审批**
- safe reject 是 v10.1 救命特性（cron 跑出 6 候选一次没污染 plan/genes/）

---

## 4. 跨学科 5 库（v12.0 → v14.0）

### 4.1 5 库清单

```
1. BeautifulMathematics（数学保证）     Ch12 算法 / Ch17 分形
2. cell-biology（生物保证）             Ch15 信号传导
3. CognitivePsychology（认知保证）      Ch6 长时记忆
4. OpenStaxBiology（进化保证）          Ch01 进化
5. evomap（协议保证）                   GEP v1.12.1 §2.3 EvolutionEvent
```

### 4.2 阶段路径

```
v12.0 evidence v2.0 接入（手写章节号）             7892769
v13.0 evidence v2.0 自动生成（cross_library_auto）  8a6a86d
v14.0 跨 5 库 evidence 神经元网络（闭环互引）       fdcb48e + 9afc310
```

### 4.3 神经元网络（v14.0）

```
BeautifulMathematics → CognitivePsychology → OpenStaxBiology → evomap → cell-biology → BeautifulMathematics
```

每条 evidence 末尾含 2 个 `→ [关联库 章节号]` 引用。

### 4.4 收益

| 维度 | v2.0 | v3.0 |
|------|------|------|
| 路径可追溯性 | 1 条 | 4 条（每条 evidence 可追溯 4 个关联） |
| 鲁棒性 | 1 evidence 失效断链 | 关联网络反推 |

---

## 5. 今晚 runtime learning（07:39 → 13:19, 5.5h）

### 5.1 进展

| commit | 主题 |
|---|---|
| `4514f6a` v10.2 | 7 候选字段补全 + 8 审计事件 + 130 重复清理 |
| `c332664` v11.0 | ROADMAP - Plan B 收尾 |
| `7892769` v12.0 | 5 库 evidence v2.0 接入 |
| `8a6a86d` v13.0 | evidence v2.0 自动生成 |
| `fdcb48e` + `9afc310` v14.0 | 跨 5 库 evidence 神经元网络 + ROADMAP |

### 5.2 关键技术节点

- **Plan B 决策路径**：发现 v0.9 已批准 7 候选 → 选 B 方案（修字段不撤销）
- **误删与恢复**：mtime 排序误删 005:message / 004:edit → tar + git 双备份救场
- **safe reject 验证**：cron 跑出 6 候选 → 全部 auto-rejected ✅

### 5.3 教训（2 份 learnings）

1. **误删教训**（`learnings/2026-08-15-verify-file-before-delete.md`）：
   - mtime 排序 ≠ 业务正确性
   - 删前必查 Solidify 批准列表
   - 备份：git + tar 双保险

2. **简单说事**（`learnings/2026-08-15-simple-talk.md`）：
   - 听到"听不懂" / "看不懂" → 立即降级到 3 句话
   - 长篇大论 → 一个明确动作

---

## 6. 闭环（runtime learning → 下次 runtime）

### 6.1 已闭环

- v10.2 字段补全 → 7 候选入库 ✅
- v12.0-v14.0 evidence v2.0/v3.0 升级 ✅
- cron safe reject 守护实战验证 ✅
- 误删教训 + 简单说事教训 写入 `learnings/` ✅

### 6.2 未闭环（下次 runtime 再做）

- 7 候选 evidence v3.0 重生成（覆盖 v12.0 手写版）
- AGENTS.md / SOUL.md 同步更新 5 库 v2.0/v3.0
- 历史索引 v1.4~v14 共 80+ 期 ROADMAP
- 美机 47.89.153.254 同步（**严禁没胡老师确认**）

### 6.3 runtime learning → 下次 runtime 入口

下次启动时读本文件 + `MEMORY.md` → 5 库 v3.0 闭环已建立 → 直接进入"v15.0 候选"。

---

## 7. 核心 takeaway

| 维度 | takeaway |
|---|---|
| 借鉴 | 3 件不动的事先识别 |
| 自进化 | append-only + 人工审批 |
| 协作 | 协议 + 守护 + 审批 |
| 跨学科 | 5 库闭环 = 路径可追溯性 ×4 |
| runtime | 误删靠备份兜底 / 啰嗦靠"3 句话" |

**gep-harness = 借鉴 + 自进化 + 协作 + 跨学科 = 完整闭环科研级 Harness。**

---

_作者：devagent | 创建：2026-08-15 13:19 | 项目：gep-harness_