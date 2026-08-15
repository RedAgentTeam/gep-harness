# ROADMAP v20.0 — 5 库 v6.0 图谱 PNG + examples 扩展

> 日期：2026-08-15 16:38
> 分支：master
> 状态：🟡 IN PROGRESS（5 库 PNG 已生成，examples 6 个齐备）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest scripts/ | ✅ 21/21 |
| pytest openclaw-a2a/ | ✅ 15/15 |
| 5 库图谱 PNG | ✅ docs/5LIB_GRAPH.png (133K) |
| examples/ | ✅ 6 个（01-06）|

## v20.0 变更明细

| # | 变更 | 状态 |
|---|------|------|
| 1 | 5 库 v6.0 图谱 PNG 自动生成（graphviz）| ✅ |
| 2 | examples/05_png_generation.py | ✅ |
| 3 | examples/06_safe_reject_demo.py | ✅ |
| 4 | v20.0 ROADMAP | ✅ (本次) |

## examples/ 6 个案例

| 文件 | 内容 |
|------|------|
| 01_local_evolver.py | 本机 Evolver 一周期 |
| 02_cross_library_evidence.py | 5 库 evidence v3.0 自动生成 |
| 03_a2a_bidirectional.py | A2A 双向同步演示 |
| 04_pytest_integration.py | pytest 集成 + 跨库示例 |
| 05_png_generation.py | 5 库图谱 PNG 自动生成 |
| 06_safe_reject_demo.py | Solidify safe reject 守护演示 |

## 下一步（v21.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | GitHub Phase 3 发布（需胡老师拍板仓库地址）| 阻塞 |
| B | 美机 47.89.153.254 跨节点真部署 | ❌ 严禁没确认 |
| C | 5 库 v7.0（DOT → SVG 矢量化）| 下次 |

## 严禁事项（5 条铁律 + 1 条新加）

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v20.0 是 **5 库 PNG 自动生成 + examples 扩展版本**：6 个 examples + 21/21 pytest。下一步 v21.0 候选 A/B/C 待胡老师拍板。