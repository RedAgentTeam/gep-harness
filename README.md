# GEP Harness — OpenClaw 自进化底座

> **版本：** v0.5.0 (CRDT + gene_sync bugfix)  
> **日期：** 2026-08-14  
> **作者：** devagent @ 胡老师指令  
> **协议：** GEP v1.12.1 (strict)  
> **许可：** AGPL-3.0-or-later（项目代码）/ CC-BY-4.0（方法论文档）

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

### v0.5 路线图（优先级 P1→P3）

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
| ROADMAP 期数 | 75（v0.5 ~ v14.0） |
| Gene 数 | 152（清理后 7 候选） |
| Event 数 | 19+ EvolutionEvent |
| pytest | 16/16 (test_cross_library_auto.py) |
| GEP strict | 7/7 |
| 跨学科 5 库 | v3.0 神经元网络（闭环互引） |
| 安全 | 本机运行 / 生产部署未启动 |

## 4 阶段闭环

1. **借鉴**（v0.4 ~ v1.0）：DeepSeek Harness 文章 + 3 件不动的事
2. **自进化**（v1.0 ~ v10.0）：Evolver 半自动 + 65 期演化 + cron 6h
3. **协作网络**（v10.0 ~ v10.1）：A2A 双向 157/157 + safe reject 守护
4. **跨学科 5 库**（v12.0 ~ v14.0）：v3.0 神经元网络 + runtime learning 复盘

## 文档索引

- `docs/ROADMAP_INDEX.md` — 75 期 ROADMAP 历史索引
- `docs/ROADMAP_v14.md` — 最新一版 ROADMAP
- `docs/SOLIDIFY.md` — Solidify 守门规则 + v10.2 修订记录
- `learnings/runtime-learning-2026-08-15-full-recap.md` — 4 阶段完整复盘
