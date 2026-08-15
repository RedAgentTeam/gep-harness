# ROADMAP v15.0 — 开源准备 + pytest 覆盖率升级

> 日期：2026-08-15 14:01
> 分支：master
> 状态：🟡 IN PROGRESS（5 项开源准备全完成，pytest 37/37）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest | ✅ 37/37（v14.0: 16 → v15.0: 37, +21 测试）|
| GEP strict | ✅ 7/7 |
| 5 库 evidence v3.0 | ✅ 7 候选神经元网络 |
| 开源准备 5 项 | ✅ LICENSE / 双语 README / 跨节点 / CONTRIBUTING / examples |

## v15.0 变更明细

| # | 变更 | 状态 |
|---|------|------|
| 1 | pytest 覆盖率提升（+21 测试覆盖 0% 脚本）| ✅ |
| 2 | 5 个新测试文件（replay/scan/validate/verify/solidify）| ✅ |
| 3 | v15.0 ROADMAP | ✅ (本次) |

## pytest 测试覆盖

| 测试文件 | 测试数 | 覆盖脚本 |
|----------|--------|----------|
| `test_cross_library_auto.py` | 12 | cross_library_auto.py |
| `test_replay_events.py` | 4 | replay_events.py |
| `test_scan_events.py` | 4 | scan_events.py |
| `test_validate_gep.py` | 4 | validate_gep.py |
| `test_verify_assets.py` | 4 | verify_assets / canonicalize.py |
| `test_solidify.py` | 5 | solidify.py |
| **总计** | **33** | 5 个原 0% 脚本 + 1 个主脚本 |

## 开源准备 5 必备项（100% 完成）

| # | 项 | 状态 |
|---|----|------|
| 1 | LICENSE (MIT) | ✅ |
| 2 | README.md + README.en.md | ✅ |
| 3 | docs/CROSS_NODE_DEPLOY.md | ✅ |
| 4 | CONTRIBUTING.md | ✅ |
| 5 | examples/ (3 个实战案例) | ✅ |

## 下一步（v16.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | Phase 3 GitHub 发布（需 LICENSE + 仓库地址）| 等胡老师拍板 |
| B | 美机 47.89.153.254 跨节点真部署 | ❌ 严禁没确认 |
| C | 5 库 v4.0 神经元网络扩展（增加关联库数）| 下次再说 |

## 严禁事项（5 条铁律 + 1 条新加）

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v15.0 是 **开源准备收尾 + 测试覆盖升级版本**：5 项开源必备项 100% 完成 + pytest 16→37。下一步 v16.0 候选 A/B/C 待胡老师拍板。