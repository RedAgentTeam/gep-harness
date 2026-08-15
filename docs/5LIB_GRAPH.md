# 5 库关联强度图谱（v5.0）

| From \\ To | BeautifulMathematics | cell-biology | CognitivePsychology | OpenStaxBiology | evomap |
|---|---|---|---|---|---|
| BeautifulMathematics | 0.50 | 0.85 | 0.90 | 0.70 | 0.90 |
| cell-biology | 0.85 | 0.50 | 0.70 | 0.90 | 0.70 |
| CognitivePsychology | 0.90 | 0.70 | 0.50 | 0.90 | 0.85 |
| OpenStaxBiology | 0.70 | 0.90 | 0.90 | 0.50 | 0.90 |
| evomap | 0.90 | 0.70 | 0.85 | 0.90 | 0.50 |

## 章节号映射

| 库 | 章节号 |
|---|---|
| BeautifulMathematics | Ch12 算法 |
| cell-biology | Ch15 信号传导 |
| CognitivePsychology | Ch6 长时记忆 |
| OpenStaxBiology | Ch01 进化 |
| evomap | GEP v1.12.1 §2.3 EvolutionEvent |

## 强关联（≥0.85）路径

- BeautifulMathematics → cell-biology: 0.85
- BeautifulMathematics → CognitivePsychology: 0.90
- BeautifulMathematics → evomap: 0.90
- cell-biology → BeautifulMathematics: 0.85
- cell-biology → OpenStaxBiology: 0.90
- CognitivePsychology → BeautifulMathematics: 0.90
- CognitivePsychology → OpenStaxBiology: 0.90
- CognitivePsychology → evomap: 0.85
- OpenStaxBiology → cell-biology: 0.90
- OpenStaxBiology → CognitivePsychology: 0.90
- OpenStaxBiology → evomap: 0.90
- evomap → BeautifulMathematics: 0.90
- evomap → CognitivePsychology: 0.85
- evomap → OpenStaxBiology: 0.90