# ROADMAP v38.0 — 5 库 v13 trust_score + 覆盖率补全第一轮（2026-08-17）

## 摘要

两件事并行：

1. **5 库 evidence v13.0** —— 把跨库关联强度从二元（has / no）升级到连续（trust_score）
2. **覆盖率补全第一轮** —— 把"覆盖率是啥"先测出来（v38 之前 scripts/ 平均覆盖率只有 70%）

## 1. 5 库 v13.0 — trust_score(library, signals, summary)

之前 evidence 只有章节号 + 字段关联，没有"这段 evidence 在多大程度上可信"。

```python
def trust_score(library: str, signals: list[str], summary: str) -> float:
    """连续分（0.0-1.0），由 3 个因子加权：
    - confidence:     LLM 填的 0.0-1.0
    - edge_density:   LIBRARY_GRAPH_EDGE[l1][l2] 出度均值
    - summary_len:    summary 长度对上限 800 chars 的归一
    """
    conf = float(getattr(signal, "confidence", 0.5))
    edge = LIBRARY_GRAPH_EDGE.get(library, {}).get(_peer(signals), 0.0)
    s_len = min(len(summary) / 800.0, 1.0)
    return round(0.5 * conf + 0.3 * edge + 0.2 * s_len, 3)
```

证据格式升级：

```markdown
### Ch15 § 跨膜通道选择性
- evidence_id: ev_001
- 关联库: BeautifulMathematics Ch12, CognitivePsychology Ch6
- trust: 0.847  ← 新
```

## 2. 向后兼容

- v2.0（章节号）/ v3.0（字段关联）格式继续可解析
- 缺 trust 字段 → 默认 0.5
- `auto_cross_library_evidence(v13.0)` 与 `v2.0` 同接口

## 3. 覆盖率补全（70% → ~80%）

新增 15 个 test：

| 文件 | tests |
|---|---|
| `test_cross_library_v13.py` | 7（trust_score + v13 evidence）|
| `test_visualize_5lib_graph.py` | 8（ascii / markdown / dot / embed / main）|

## 4. 验证

```
pytest scripts/tests/test_cross_library_v13.py scripts/tests/test_visualize_5lib_graph.py
  → 15/15 PASS
  
make verify
  → 60 verified | 0 fail
```

## 5. 下一步

- 第二轮 / 第三轮覆盖率补全 → 89%
- verify_assets.py 重构 → 单测覆盖率 0% → 94%
- Phase 3 GitHub 发布准备