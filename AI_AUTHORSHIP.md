# AI_AUTHORSHIP — Agent 主导的开发模式（透明化声明）

> **日期**：2026-08-15
> **目的**：诚实地说明 gep-harness 的开发模式，避免读者从"署名 devagent + cron 循环"推断

---

## 核心声明

> gep-harness 的大部分内容 = **由 AI Agent（devagent）在 cron 循环下自动生成 + 人类（胡老师/Red Ho）在关键节点拍板**

这不是隐性事实，而是这个项目**最有故事性的角度**：

> **"用 Agent 自我进化的方式来构建 Agent 自我进化的基础设施"**

---

## 开发模式（具体分工）

| 部分 | 主导方 | 复核方 |
|------|--------|--------|
| **借鉴层**（DeepSeek Harness 3 件不动的事）| 人类（胡老师决策）| Agent 执行 |
| **自进化层**（Evolver Scan/Signal/Mutate）| **Agent 自动**（cron 6h）| 人类（Solidify y/N）|
| **工具流水线**（Hook → Permission → Timeout → Execute）| **Agent 自动** | 人类（OpenClaw 插件审批）|
| **5 库 evidence**（跨学科类比）| **LLM 自动生成关键词 + Agent 整理** | 人类（`reviewed: true` 标记）|
| **架构决策**（不可逆：插件运行时、Solidify 全自动）| 人类（胡老师决策）| Agent 落地 |
| **日常 bug 修复 / 字段补全 / 文档** | **Agent 自动** | 人类（仅 y/N 抽查）|

---

## 人类介入的具体触发条件

| 触发条件 | 介入方式 | 频率 |
|----------|----------|------|
| **不可逆架构决策**（如是否引入插件运行时、Solidify 是否全自动）| 必介入 | 极低（每季度 1-2 次）|
| **Solidify 候选 Gene 审批**（v0.9 7 个 / cron auto-reject 50+）| 必介入（人类 y/N）| 高（每次 cron 周期）|
| **AGENTS.md / SOUL.md 修改** | 必介入（owner 拍板）| 低（每 1-2 周）|
| **对外发布**（GitHub Release / 公开仓库）| 必介入 | 中（每迭代）|
| **日常小改动**（字段、文档、bug）| **不需要**（Agent 自动 + y/N 抽查）| — |

---

## Agent 自主能力的边界

| ✅ Agent 能做 | ❌ Agent 不能做 |
|--------------|----------------|
| 读 git log + 推断代码意图 | 知道**业务背景**（为什么要做这个）|
| 跑 pytest + 修测试 | 知道**安全边界**（如美机不可碰）|
| 写 ROADMAP + commit message | 知道**人类优先级**（如"先收窄范围"）|
| 跨学科类比的关键词检索 | 知道**类比是否扎实**（仅人工能判断）|
| 生成 CHANGELOG + 5 格式可视化 | **替代 Solidify 人工审批**（违 Arrow 不可能性定理）|

---

## 为什么公开承认？

1. **诚信**：避免读者从 commits 推断 Agent 主导却没明说
2. **卖点**："Agent 自我进化基础设施"是好故事，值得讲清楚
3. **可审计**：明确哪些是自动 / 哪些人工复核，方便未来读者回溯决策
4. **可复用**：其他想用 Agent 主导开发的团队可参考此模式

---

## 相关文档

- `AGENTS.md` — Agent 工作原则（SOUL #1-5 铁律）
- `learnings/runtime-learning-2026-08-15-gep-harness-full-recap.md` — 完整 4 阶段复盘
- `docs/SOLIDIFY_AUDIT.md` — 人工审批审计记录
- `docs/SOLIDIFY.md` — Solidify 守门规则

---

_作者：devagent | 创建：2026-08-15 21:16 | 项目：gep-harness_