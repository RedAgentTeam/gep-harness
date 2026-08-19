# Release Notes — gep-harness v41.1 (2026-08-19)

> **Tag:** `v41.1`
> **Date:** 2026-08-19
> **Author:** RedAgentTeam (@胡老师 / Red Ho)
> **Protocol:** GEP v1.12.1 (strict)
> **License:** MIT

**首个 GitHub 发布版本。** 本版本完成 Phase 3 GitHub-standard publish prep —— 仓库已具备公开可读、可贡献、可复现的全部要素。

---

## 🎯 核心数据

| 指标 | 数值 |
|---|---|
| 总 commits | 214+ |
| Plan assets (genes) | 60 |
| Plan assets (capsules) | 2 |
| Plan assets (events) | 28 |
| pytest 总数 | 557 passed |
| GEP strict 验证 | 90 verified / 0 FAIL |
| 文档 ROADMAP | v0.4 ~ v41 (90 期) |
| 5 库 evidence 闭环 | ✅ BeautifulMathematics / cell-biology / CognitivePsychology / OpenStaxBiology / evomap |

---

## 🆕 v41.0 + v41.1 增量（最近 2 个版本）

### v41.1 — Phase 3 GitHub-standard publish prep (`954ff41`)

- `.gitignore`：untrack `openclaw-harness/events/events.jsonl`（append-only 本地累积，15M+，不入库）
- 新增 5 个 main() 入口测试，覆盖 scripts/ 黑盒路径：
  - `test_adaptive_gdi_main.py` (135 lines)
  - `test_gene_to_capsule_main.py` (284 lines)
  - `test_generate_changelog_main.py` (80 lines)
  - `test_llm_fill_gene_main.py` (279 lines)
  - `test_verify_assets_runpy.py` (68 lines)
- 删除 `events.jsonl` 历史累积 32268 行（本地审计流，从 git history 移除）
- pytest 总数：511 → 557 (+46)

### v41.0 — Phase 3 pre-push cleanup (`7f6bb9a`)

- `scripts/llm_fill_gene.py`：在 `dry_run` 分支前 `load gene JSON`（之前漏了一处，dry_run 模式直接 `NameError`）
- `CHANGELOG.md`：重新生成到 v40.0

---

## 📋 v37 ~ v40 增量（Phase 3 准备 4 版本）

| Version | 主题 |
|---|---|
| **v40.0** | 覆盖率 88%→89% + 第三轮测试补全 (511 tests) |
| **v39.0** | 覆盖率 70%→86% + verify_assets 重构 + 第二轮测试补全 |
| **v38.0** | 5 库 v13 trust_score + 覆盖率补全第一轮 |
| **v37.0** | 修复 16 个 PLACEHOLDER_LLM_TO_FILL asset_ids |

---

## 🚀 Quick Start（GitHub clone 后 5 分钟上手）

```bash
git clone https://github.com/RedAgentTeam/gep-harness.git
cd gep-harness
make verify        # GEP strict 验证
make test          # pytest 557/557
python3 examples/08_github_quickstart.py    # 路径无关 quickstart
```

---

## 📦 What's Inside

```
gep-harness/
├── README.md / README.en.md       # 中英双语项目说明
├── LICENSE (MIT)                  # MIT 许可
├── CONTRIBUTING.md                # 贡献指南（含 Solidify 守门 + 4 条铁律）
├── CHANGELOG.md                   # 自动生成（git log 提取，214 commits）
├── OPEN_SOURCE_PLAN.md            # 开源准备清单（5 必备项 + 3 加分项）
├── AI_AUTHORSHIP.md               # Agent 主导开发模式透明声明
├── .github/workflows/ci.yml       # CI（多 Python × 多 OS 矩阵）
├── docs/
│   ├── ROADMAP_v0.4 ~ v41         # 90 期迭代档案
│   ├── 5LIB_GRAPH.{png,svg,pdf,eps,md}  # 5 库关联图谱多格式
│   ├── CROSS_NODE_DEPLOY.md       # A2A 跨节点协议
│   ├── SOLIDIFY.md / SOLIDIFY_AUDIT.md  # Solidify 守门规则
│   ├── THREAT_MODEL.md            # 威胁模型
│   └── RELEASE_NOTES_v41.1.md     # 本文件
├── openclaw-harness/              # 阶段 1 产出（事件流 + canonicalize）
├── openclaw-a2a/                  # 阶段 4 产出（A2A 协议 + mock_peer）
├── openclaw-harness-plugin/       # OpenClaw 插件源码
├── openclaw-harness-tool-pipeline-plugin/  # 工具流水线插件
├── plan/
│   ├── genes/  (60)
│   ├── capsules/  (2)
│   └── events/  (28)
├── scripts/                       # Evolver / Solidify / 5 库 / 可视化
│   ├── verify_assets.py          # GEP strict 验证
│   ├── extract_candidate_genes.py
│   ├── cross_library_auto.py     # 5 库 evidence v2.0/v3.0/v13.0
│   ├── solidify.py               # 人工审批守门
│   ├── visualize_5lib_graph.py   # 5 库图谱可视化
│   └── tests/  (45+ test files)
└── examples/  (01-08)             # 实战 demo
```

---

## 🛡️ 3 Untouchable Rules（项目基石）

1. ❌ **No Skill abstraction** — use Gene/Capsule (~230 tokens policy unit)
2. ❌ **No runtime plugin loading** — Cordis-style dynamic injection dilutes Gene signal matching precision
3. ❌ **No automatic Solidify** — must go through manual approval (CognitivePsychology 9 biases + Arrow's theorem)

详见 `CONTRIBUTING.md` §3 Untouchable Rules。

---

## 🔒 Production Deployment

⚠️ **跨节点生产部署（美机 `47.89.153.254`）** 待 operator（胡老师）确认。

`docs/CROSS_NODE_DEPLOY.md` 已写完整协议（HMAC + ed25519 + A2A envelope），本地 157/157 双向测试通过，但生产部署未启动。

---

## 🧪 Reproducibility

所有测试一键复现：

```bash
make verify && make test
```

CI 在 `.github/workflows/ci.yml` 跑多 Python (3.10/3.11/3.12/3.13) × 多 OS (ubuntu-latest + macos-latest) 矩阵。

---

## 🙏 致谢

- **DeepSeek Harness 开源项目** —— 借鉴的源头（3 件不动的事）
- **msitarzewski (MAS Wiki)** —— GEP 协议标准制定
- **evomap** —— GEP v1.12.1 协议规范
- **OpenClaw 生态** —— Harness 集成宿主

---

## 📝 License

MIT License (c) 2026 RedAgentTeam

详见 [LICENSE](./LICENSE)。