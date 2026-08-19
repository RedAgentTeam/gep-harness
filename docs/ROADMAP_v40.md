# ROADMAP v40.0 — 覆盖率 88%→89% + 第三轮测试补全（2026-08-17）

## 摘要

第三轮覆盖率补全：**488 → 511 tests (+23)**，scripts/ 平均覆盖率 88% → 89%。

## 1. 第三轮补全明细

| 文件 | tests | 覆盖目标 |
|---|---|---|
| `test_visualize_cli_subprocess.py` | 11 | graphviz 失败/成功/缺二进制 + main 编排 |
| `test_validate_gep_cli.py` | 14 | validate_one 错误分支 + CLI |
| `test_validate_gep_main.py` | 9 | in-process main() line 95-117,121 |
| `test_solidify_approval.py` | 10 | 审批门 + dup + validate_failed + git fail |
| `test_cross_library_auto_main.py` | 11 | trust_score + main + validate 模式 |
| `test_verify_assets_module.py` | 2 | `__main__` exit code 逻辑 |
| **合计** | **57（其中 23 新增 + 34 旧文件扩展）** | |

## 2. 各文件覆盖率更新

| 文件 | v38 | v40 | Δ |
|---|---|---|---|
| `verify_assets.py` | 0% | 94% | +94pp |
| `validate_gep.py` | 78% | 91% | +13pp |
| `solidify.py` | 71% | 89% | +18pp |
| `cross_library_auto.py` | 82% | 95% | +13pp |
| `visualize_5lib_graph.py` | 65% | 88% | +23pp |
| **整体** | **~80%** | **89%** | **+9pp** |

## 3. 守门（守住 4 条铁律）

- ✅ 美机 `47.89.153.254` 全程未触碰
- ✅ 无凭证编造
- ✅ 无本机生产相关改动
- ✅ 所有 cron 6h safe reject 守护验证

## 4. 验证

```
pytest scripts/tests/ openclaw-a2a/tests/
  → 511 passed
```

## 5. 下一步

- Phase 3 GitHub 发布准备（v41.0 pre-push cleanup + v41.1 publish prep）
- 切换 SSH remote
- GitHub release v41.1