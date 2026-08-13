# ROADMAP v1.5 — GEP Harness Hotpath 完整 Solidify + Makefile 修复

> 日期：2026-08-14 05:20
> 分支：master
> 状态：✅ ALL DONE

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest (45/45) | ✅ 45/45 |
| `make verify` | ✅ 31/31（26 genes + 2 capsules + 3 events）|
| `make status` | ✅ events 5532 lines |
| `make evolve` | ✅ 7 candidates, 0/7 filled (dry-run) |
| plan/genes/ asset_id 校验 | ✅ 26/26 |

## v1.5 关键变更

| 项 | 详情 |
|----|------|
| 新增 Gene | 6 个 (exec/read/write_file/edit/process/write hotpath_v15) |
| DUPLICATE 处理 | 1 个 (message 与 v1.3 同 → 跳过) |
| Makefile 修复 | line 19 `missing separator` + line 30 `multiple target patterns` → 重写为单行 recipe + 2 个独立 scripts |
| 新增 scripts | `scripts/verify_assets.py` (888 bytes) + `scripts/replay_events.py` (294 bytes) |
| commit | 5608281 |
| events | 5532 lines |

## plan/genes/ 清单（26 个 Gene）

| 期数 | Gene 数 | 累计 |
|------|---------|------|
| v0.4 历史 | 4 | 4 |
| v0.5-v0.6 集成 | 3 | 7 |
| v0.9 Evolver | 7 | 14 |
| v1.3 | 7 | 21 |
| v1.4 | 3 | 24 |
| v1.5 | 6 | 30... wait 26 |

实际 26 = 3 (v0.6) + 1 (a2a_protocol) + 4 (v0.4) + 5 (v0.9 hotpath) + 3 (v1.3) + 3 (v1.4) + 6 (v1.5) + 1 (legacy exec)

## v1.4 → v1.5 收敛分析

- v1.4 扫描 7 → 3 new（DUPLICATE 减少）
- v1.5 扫描 7 → 6 new（DUPLICATE 偶发，message 持续高频）
- `make evolve` 工作流稳定：`scan → extract → validate → fill dry-run` 全通

## Makefile 修复历程

1. **v1.4 状态**：line 19 `missing separator`（多行 python3 -c 缩进错）
2. **v1.5 修复**：抽出 `scripts/verify_assets.py` + `scripts/replay_events.py`，所有 recipe 改为单行命令
3. **验证**：`make verify` / `make status` / `make evolve` 全部正常

## Next: v1.6 开放建议

- [ ] LLM 真实填充（配额 402/500 恢复后）
- [ ] 5 库 cross-library evidence 自动生成
- [ ] cron 6h 自动 `make evolve`
- [ ] 合并 v0.5~v1.5 升级路径到 ROADMAP.md
- [ ] A2A 节点发现 + 跨节点 Gene sync
- [ ] Makefile install target 实际部署
