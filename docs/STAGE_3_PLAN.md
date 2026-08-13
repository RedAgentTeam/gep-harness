# STAGE_3_PLAN — Evolver 半自动

> **阶段：** 3 / 3  
> **对应 Gene：** `gene_harness_evolver_semiauto`  
> **状态：** ✅ DONE（2026-08-14 02:11）  
> **日期：** 2026-08-14

---

## 目标

实现 **Evolver 循环**：`Scan → Signal → Mutate → Validate → Solidify`

其中：
- **Scan / Signal / Mutate**：**LLM 自动**（写 Python 脚本，消费 events.jsonl）
- **Validate**：**GEP strict 校验**（自动）
- **Solidify**：**人工审批**（绝不豁免）

---

## 与 EvoMap 标准对齐

参考 `/data/disk/githubwiki/evomap/original/evolver-claude-code-plugin/`，其 4 阶段命令：

| EvoMap 命令 | 本项目对应 |
|---|---|
| `distill` | 从 events.jsonl 提取 pattern |
| `evolve` | LLM 生成 Gene 候选 |
| `solidify` | 把候选 Gene 写入 staging/ |
| `review` | 人工 Solidify 进 Gene 库 |

本项目 5 阶段：

| 阶段 | 自动化 | 输出 |
|---|---|---|
| **Scan** | 自动（Python）| 高频 tool_call 聚类 |
| **Signal** | 半自动（LLM 调用）| 候选 Gene JSON |
| **Mutate** | 自动（LLM 调用）| 保守+激进双变体 |
| **Validate** | 自动（GEP strict）| 通过/失败 |
| **Solidify** | 🛑 **人工** | 写入 plan/genes/ |

---

## 实施步骤

### 步骤 1：scan_events.py（Scan 阶段）

```bash
python3 /data/disk/gep-harness/scripts/scan_events.py --since=24h
```

输出：高频 tool_name + args pattern 聚类

### 步骤 2：extract_candidate_genes.py（Signal 阶段）

```bash
python3 /data/disk/gep-harness/scripts/extract_candidate_genes.py --input=scan-output --output=staging/
```

输出：`staging/gene_candidate_*.json`（GEP schema 兼容）

### 步骤 3：validate_gep.py（Validate 阶段）

```bash
python3 /data/disk/gep-harness/scripts/validate_gep.py --mode=strict --input=staging/*.json
```

校验：
- 9 个 required 字段齐全
- asset_id 计算正确
- constraints 在 max_files 之内
- forbidden_paths 不在 builtin 内

### 步骤 4：人工 Solidify

```
# 候选 Gene 通过校验后，在 staging/ 目录
# 胡老师 review 后：
cp staging/gene_candidate_xxx.json /data/disk/gep-harness/plan/genes/
```

---

## 关键边界（不豁免）

- ❌ **不引入 Skill 抽象**
- ❌ **不引入运行时插件加载**
- ❌ **不让 Solidify 全自动**
- ✅ **人工审批是硬性门**
- ✅ **5 库跨学科映射方法论**（每个新 Gene 必须含）

---

## 时间估算

- 步骤 1-3 实现：~2 天
- 步骤 4 流程固化：~1 周（边用边调）
- 阶段 3 pytest：~0.5 天

总计：**~3 天** + 持续迭代

---

## 不在本期做

- ❌ 完整的 plugin（仅写 Python CLI 脚本）
- ❌ 自动跑 Solidify（人工审批门）
- ❌ GDI 评分自动计算（手动）
- ❌ Gene 候选写回 wiki（人工）

---

## 依赖

- events.jsonl 必须先累积 24h+ 数据（阶段 1 已就位）
- harness-event-stream plugin 必须 enabled（已就位）
- harness-tool-pipeline 修复 false positive 后再启用（not in this stage）

---

## Next Action

1. 写 3 个 Python 脚本（scan_events / extract_candidate_genes / validate_gep）
2. 写 3 个 pytest
3. 写阶段 3 GEP 资产（plan/genes/ + plan/capsules/ + plan/events/）