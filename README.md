# GEP Harness — OpenClaw 自进化底座

[![CI Status](https://github.com/RedAgentTeam/gep-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/RedAgentTeam/gep-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/RedAgentTeam/gep-harness)](https://github.com/RedAgentTeam/gep-harness/releases)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)

> **版本：** v14.0（迭代轮次 #75）  
> **日期：** 2026-08-14  
> **作者：** RedAgentTeam（@胡老师 / Red Ho）  
> **协议：** GEP v1.12.1 (strict)  — 跨协议/项目不变字段  
> **许可：** MIT（见 [LICENSE](./LICENSE)）

---

## 项目定位

**OpenClaw 系统借鉴 DeepSeek 开源 Harness，在不引入 Skill 抽象、不引入插件运行时、保留 Gene/Capsule 体系的前提下，重构 OpenClaw 的 Harness 底座。**

4 阶段完成 + 阶段 4 子阶段全部完成：

| 阶段 | 目标 | 状态 |
|---|---|---|
| **阶段 1** | Append-only 事件流（session 轨迹底座）| ✅ DONE |
| **阶段 2** | 工具调用流水线（Hook→Permission→Timeout→Execute→Rewrite→Emit）| ✅ DONE |
| **阶段 3** | Evolver 半自动（Scan/Signal/Mutate/Validate 自动 + Solidify 人工）| ✅ DONE |
| **阶段 4** | A2A 协议（HMAC + GDI v2 + Gene Pool + cron sync + 双节点集成）| ✅ DONE |

---

## 目录结构

```
/data/disk/gep-harness/
├── README.md                          # 本文件
├── Makefile                           # 管理命令（verify / replay / clean）
├── CHANGELOG.md                       # 变更记录
├── 数据溯源.md                          # 引用源头（DeepSeek 文章 + GEP 协议 + 5 库）
├── 方法论.md                          # 5 库跨学科映射方法
├── plan/                              # GEP 资产（PLAN 阶段产出）
│   ├── genes/                         # 5 个 Gene
│   ├── capsules/                      # 2 个 Capsule
│   └── events/                        # 3 EvolutionEvent + 1 Mutation
├── openclaw-harness/                  # 阶段 1 BUILD 产出
│   ├── bin/                           # canonicalize.py + event_emitter.py
│   ├── events/                        # append-only events.jsonl
│   ├── tests/                         # 4 pytest
│   └── docs/                          # stage 1 文档
├── openclaw-harness-plugin/           # OpenClaw plugin 源码（注册到 Gateway）
│   ├── index.js                       # api.on("before_tool_call") / api.on("after_tool_call")
│   ├── openclaw.plugin.json           # manifest
│   └── package.json
├── scripts/                           # 验证脚本
└── docs/                              # 项目文档
```

---

## 关键设计决策（继承原则）

| 决策 | 依据 |
|---|---|
| **不引入 Skill 抽象** | OpenClaw 用 Gene/Capsule（~230 tokens 策略单元），Skill 是人类理解载体（~2500 tokens）。两者是 test-time control vs 知识载体的不同尺度 |
| **不引入运行时插件加载** | Cordis 式动态注入会稀释 Gene 信号匹配精度。cell-biology "膜选择性通透" 原则要求稳定边界 |
| **保留 Gene/Capsule 体系** | GEP §1-§5 + EvoMap evolver-claude-code-plugin 标准 |
| **Solidify 必走人工审批** | CognitivePsychology 9 大认知错觉 + Arrow 定理：不存在完美聚合方法 |
| **5 库跨学科映射** | BeautifulMathematics / cell-biology / CognitivePsychology / OpenStaxBiology / evomap |

---

## 当前状态

| 项 | 值 |
|---|---|
| 协议版本 | A2A v0.2（behavior_feedback_proof 签名验证）|
| 阶段 1（事件流） | ✅ DONE — 2 个 plugin runtime registered |
| events.jsonl 行数 | 1146+（持续增长）|
| GEP strict 校验 | ✅ 11/11 通过 |
| pytest | ✅ 21/21 PASSED（3.2s）|
| E2E 双节点 | A↔B 双向 accepted=1，score=1.0，verified=True |

---

## 快速使用

```bash
# 看 plugin 状态
openclaw plugins list | grep harness-event-stream

# 看 events
python3 /data/disk/gep-harness/openclaw-harness/bin/event_emitter.py verify
python3 /data/disk/gep-harness/openclaw-harness/bin/event_emitter.py replay <session_id>

# 重跑严格校验
make verify

# 看 README/数据溯源/方法论
cat 数据溯源.md
cat 方法论.md
```

---

## 下一阶段入口

### 当前阶段路线图（v14.0+ 待办）

| 优先级 | 任务 | 说明 |
|---|---|---|
| **P1** | `extract_candidate_genes.py` LLM 填充 | category/evidence 从占位符改为 LLM 生成 |
| **P1** | A2A v0.3 ed25519 keypair | 替代 shared secret |
| **P1** | Gene 版本冲突（CRDT）| import 时同 ID 冲突处理 |
| **P2** | 美机部署 Layer 1+2 | 两机事件流打通 |
| **P2** | A2A 跨机器 E2E | 美机 ↔ 本机真公网 sync |
| **P3** | A2A broadcast 模式 | 一对多发布 |
| **P3** | GDI 动态阈值 | 随节点历史自适应 |

详见 `docs/ROADMAP_v0.5.md`（待写）。
---

## 现状（2026-08-15 v14.0 收尾）

| 维度 | 数据 |
|------|------|
| ROADMAP 期数 | 75（迭代轮次 #1 ~ #75） |
| Gene 总数 | 152¹ |
| Event 数 | 19+ EvolutionEvent |
| pytest | 16/16 (test_cross_library_auto.py) |
| GEP strict | 7/7 |
| 跨学科 5 库 | v3.0 神经元网络（闭环互引） |
| 安全 | 本机运行 / 生产部署未启动 |

## 4 阶段闭环（收窄范围优先级：阶段 1+2 最成熟）

1. **借鉴**（迭代 #1 ~ #16）：DeepSeek Harness 文章 + 3 件不动的事
2. **自进化**（迭代 #17 ~ #65）：Evolver 半自动 + cron 6h
3. **协作网络**（迭代 #66 ~ #70）：A2A 双向 157/157 + safe reject 守护 **[实验性]**
4. **跨学科 5 库**（迭代 #71 ~ #75）：v3.0 神经元网络 + runtime learning 复盘 **[实验性]**

> **优先聚焦阶段 1+2**（事件流 + 工具流水线）——这两个阶段有真实 OpenClaw 插件落地，风险最低。先积累真实用户和 Star，再逐步开放阶段 3+4 的实验性部分。

## 文档索引

- `docs/ROADMAP_INDEX.md` — 75 期 ROADMAP 历史索引
- `docs/ROADMAP_v14.md` — 最新一版 ROADMAP
- `docs/SOLIDIFY.md` — Solidify 守门规则 + v10.2 修订记录
- `learnings/runtime-learning-2026-08-15-full-recap.md` — 4 阶段完整复盘

## 复现脚本（本地跑通，不依赖生产节点）

| 脚本 | 内容 | 验证 |
|------|------|------|
| `examples/01_local_evolver.py` | 本机 Evolver 一周期（scan → extract → validate） | `[SIMULATED: 本地]` |
| `examples/02_cross_library_evidence.py` | 5 库 evidence v3.0 自动生成 | `[SIMULATED: 本地]` |
| `examples/03_a2a_bidirectional.py` | A2A 双向同步（端口 19890/19891）| `[SIMULATED: 本地]` |
| `examples/04_pytest_integration.py` | pytest 集成 + 跨库示例 | `[SIMULATED: 本地]` |
| `examples/05_png_generation.py` | 5 库图谱 PNG 自动生成（需 graphviz） | `[SIMULATED: 本地]` |
| `examples/06_safe_reject_demo.py` | Solidify safe reject 守护演示 | `[SIMULATED: 本地]` |
| `examples/07_png_svg_demo.py` | PNG + SVG 双格式可视化 | `[SIMULATED: 本地]` |

> 所有脚本跑在本机 <本机 dev IP>（VM-0-11-ubuntu），**不依赖** 美机 <美机生产 IP>（生产节点未启动）。

---

## 资产分类说明（脚注）

¹ **Gene 总数 152 = 外部知识库导入 Gene (145) + Evolver 候选 Gene (7)**

| 类别 | 数量 | 来源 | 变化性 |
|------|------|------|--------|
| **外部知识库导入 Gene** | 145 | 5 库 (BeautifulMathematics / cell-biology / CognitivePsychology / OpenStaxBiology / evomap) 静态导入 | 相对固定 |
| **Evolver 候选 Gene** | 7 | cron 6h 从 `events.jsonl` 挖掘高频工具调用模式 | **每次 cron 周期动态变化** |

> **口径说明**：旧文档中出现的 "149 / 154 / 132 / 494" 等数字 = 不同时间点 Evolver 累积候选数（包含已被 reject 或已被 Solidify 覆盖的版本）。**当前可见候选数 = 7**（清理后）。如需"全期累积数"，看 `docs/ROADMAP_INDEX.md` 历史。

**SemVer vs 迭代轮次说明**：
- **迭代轮次 #1 ~ #75**：gep-harness 内部版本（commit 序号，文档用）
- **SemVer v0.1.0 / v1.0.0**：仅在 GitHub Release tag 使用（如 v33.0）

## 5 库跨学科映射方法论

**使用边界（启发式，不是门禁）**：

| 场景 | 是否需要 5 库 mapping |
|------|---------------------|
| **不可逆架构决策**（如是否引入插件运行时）| ✅ 强制 |
| **自动化 vs 人工审批**（如是否全自动 Solidify）| ✅ 强制（重锤场合）|
| **日常小改动**（如给 Gene 加个字段）| ❌ 不需要 |
| **一般技术权衡**（库选择、性能 vs 可读性）| ❌ 不需要 |

**证据质量分层**：

每条 `cross_library_evidence` 字段带 `reviewed` 标记：

```json
{
  "cross_library_evidence": [
    {
      "library": "BeautifulMathematics",
      "evidence": "Ch12 算法: ...",
      "reviewed": true   // ← 人工复核确认这个类比成立
    },
    {
      "library": "cell-biology",
      "evidence": "Ch15 信号传导: ...",
      "reviewed": false  // ← LLM 自动生成关键词，未经复核
    }
  ]
}
```

> **未复核的证据 = 启发信号，不等于论证**。跨学科类比经常是弱类比，强行凑 5 条会降低整体证据信噪比。**至少 1-2 条真正相关即可**。

**保留的"重锤"**：Arrow 不可能性证明 Solidify 不能全自动 = 扎实的数学论证，**只用在"自动化 vs 人工审批"类高风险决策**。其他场合用轻量工程评审代替。

---

## 致谢

> 本项目的诞生，源于一群在不同领域给予我帮助的人。

### evomap.ai

在我没有任何计算机基础的情况下，evomap.ai 是我唯一的知识来源。这个项目从零到一，都建立在这套系统之上。

- 仓库：https://github.com/EvoMap
- GEP SDK：https://github.com/EvoMap/gep-sdk-js

### 张昊阳老师

evomap.ai 创始人。给我提供了各方面的很多帮助，没有他的支持就没有这个项目的可能。

> **理论来源**：本项目的核心理论来自张昊阳老师的《自进化 Harness 与协作网络》。

### 巴芮老师

文章《不会省Token的货车司机不是好极客》对我进行了加持与推广，让更多人看到这个方向。

### Klaus 老师

在百度工作。帮助我梳理思路和方向，给我鼓励。在我最迷茫的时候，这些对话是我继续往前开的燃料之一。

### 张玉新老师（善用佳软）

知名软件推荐博客作者、IT 效率工具深度用户（AutoHotkey / Total Commander）


