# ROADMAP v16.0 — 5 库 v4.0 + A2A 真跑 + examples 扩展

> 日期：2026-08-15 14:05
> 分支：master
> 状态：🟡 IN PROGRESS（4 项内部验证推进完成）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest scripts/ | ✅ 37/37 |
| pytest openclaw-a2a/ | ✅ 15/15 |
| 5 库 v4.0 关联强度矩阵 | ✅ LIBRARY_GRAPH_EDGE |
| examples/ | ✅ 4 个（01-04）|

## v16.0 变更明细

| # | 变更 | 状态 | commit |
|---|------|------|--------|
| 1 | 5 库 v4.0 神经元网络扩展（LIBRARY_GRAPH_EDGE）| ✅ | (本次) |
| 2 | A2A 本机真跑 15/15 PASS | ✅ | (本次) |
| 3 | examples/04_pytest_integration.py | ✅ | (本次) |
| 4 | v16.0 ROADMAP | ✅ | (本次) |

## 5 库 v4.0 关联强度矩阵

```
BeautifulMathematics:
  → cell-biology: 0.85 (跨环新增)
  → CognitivePsychology: 0.9 (原闭环)
  → OpenStaxBiology: 0.7 (跨环关联)
  → evomap: 0.9 (原闭环)
  → self: 0.5 (自身反馈)

cell-biology:
  → BeautifulMathematics: 0.85 (原闭环)
  → CognitivePsychology: 0.7 (跨环关联)
  → OpenStaxBiology: 0.9 (原闭环)
  → evomap: 0.7 (跨环关联)
  → self: 0.5 (自身反馈)

CognitivePsychology:
  → BeautifulMathematics: 0.9 (原闭环)
  → cell-biology: 0.7 (原闭环)
  → OpenStaxBiology: 0.9 (原闭环)
  → evomap: 0.85 (跨环新增)
  → self: 0.5 (自身反馈)

OpenStaxBiology:
  → BeautifulMathematics: 0.7 (跨环关联)
  → cell-biology: 0.9 (原闭环)
  → CognitivePsychology: 0.9 (原闭环)
  → evomap: 0.9 (原闭环)
  → self: 0.5 (自身反馈)

evomap:
  → BeautifulMathematics: 0.9 (原闭环)
  → cell-biology: 0.7 (原闭环)
  → CognitivePsychology: 0.85 (跨环新增)
  → OpenStaxBiology: 0.9 (原闭环)
  → self: 0.5 (自身反馈)
```

## A2A 真跑验证（15/15 PASS）

```
test_gene_sync.py::test_audit_log_records_sync PASSED
test_gene_sync.py::test_discover_peers_aggregates_from_bootstrap PASSED
test_gene_sync.py::test_announce_peer_sends_announce_and_parses_ack PASSED
test_gene_sync.py::test_broadcast_to_peers_fans_out_to_all PASSED
test_gene_sync.py::test_announce_mutual_peers_learn_each_other PASSED
test_mock_peer.py::test_gene_sync_accepted_with_mock_peer PASSED
test_mock_peer.py::test_mock_peer_returns_decision_accepted PASSED
test_mock_peer.py::test_mock_peer_rejected_decision PASSED
... 15 passed in 6.49s
```

## examples/ 4 个案例

| 文件 | 内容 |
|------|------|
| 01_local_evolver.py | 本机 Evolver 一周期 |
| 02_cross_library_evidence.py | 5 库 evidence v3.0 自动生成 |
| 03_a2a_bidirectional.py | A2A 双向同步演示 |
| 04_pytest_integration.py | pytest 集成 + 跨库示例 |

## 下一步（v17.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | GitHub Phase 3 发布（需胡老师拍板仓库地址）| 阻塞 |
| B | 美机 47.89.153.254 跨节点真部署 | ❌ 严禁没确认 |
| C | 5 库 v5.0（增加 3 库关联强度 + 跨学科图谱可视化）| 下次 |

## 严禁事项（5 条铁律 + 1 条新加）

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v16.0 是 **5 库 v4.0 + A2A 真跑 + examples 扩展版本**：内部验证 100% 闭环。下一步 v17.0 候选 A/B/C 待胡老师拍板。