# ROADMAP v41.0 / v41.1 — Phase 3 GitHub-standard publish prep（2026-08-18）

## 摘要

Phase 3 GitHub 发布的最后两步：

| Version | Commit | 内容 |
|---|---|---|
| **v41.0** | `7f6bb9a` | Phase 3 pre-push cleanup |
| **v41.1** | `954ff41` | Phase 3 GitHub-standard publish prep |

## 1. v41.0 — pre-push cleanup

```diff
 scripts/llm_fill_gene.py | 1 +
 CHANGELOG.md             | 14 ++++++++++++--
```

- `scripts/llm_fill_gene.py`：在 `dry_run` 分支前 `load gene JSON`（之前漏了一处，dry_run 模式直接报 `NameError`）
- `CHANGELOG.md`：重新生成到 v40.0（212 commits 总数）

## 2. v41.1 — publish prep

### 2.1 .gitignore 新增

```gitignore
# Append-only audit event stream (本地累积,不入库)
openclaw-harness/events/events.jsonl
```

这条之前漏了 —— `events.jsonl` 已经 15M+，会拖慢 clone 速度，事件流是 append-only 本地审计用的，不应该入库。

**本次删除：** `32268 lines`（历史累积的事件，从 git history 中移除）

### 2.2 scripts/tests/ 新增 5 个文件

| 文件 | 行 | 用途 |
|---|---|---|
| `test_adaptive_gdi_main.py` | 135 | `adaptive_gdi.py` main() 覆盖 |
| `test_gene_to_capsule_main.py` | 284 | `gene_to_capsule.py` main() 覆盖 |
| `test_generate_changelog_main.py` | 80 | `generate_changelog.py` CLI 覆盖 |
| `test_llm_fill_gene_main.py` | 279 | `llm_fill_gene.py` main() + dry_run + fill 路径 |
| `test_verify_assets_runpy.py` | 68 | `python -m verify_assets` 入口覆盖 |

合计 **846 行新增测试**，覆盖 scripts/ 的 main() 入口 + 干路径。

## 3. Phase 3 状态

| 检查项 | 状态 |
|---|---|
| LICENSE (MIT) | ✅ v34 |
| README.md / README.en.md | ✅ v35 |
| CONTRIBUTING.md | ✅ v41（本次更新版本号+pytest 数） |
| CHANGELOG.md | ✅ v41 自动生成 |
| `.github/workflows/ci.yml` | ✅ v26 |
| `.gitignore` 脱敏 | ✅ v35.3 |
| `docs/CROSS_NODE_DEPLOY.md` | ✅ v14 |
| `docs/5LIB_GRAPH.{png,svg,pdf,eps,md}` | ✅ v19-v25 |
| `AI_AUTHORSHIP.md` | ✅ v34 |
| `OPEN_SOURCE_PLAN.md` | ✅ v14 |
| `ROADMAP_v0.4 ~ v41` | ✅ 本次补 v37-v41 |
| `docs/RELEASE_NOTES_v41.1.md` | ⏳ 待写 |
| `git tag v41.1` | ⏳ 待打 |
| 切换 SSH remote | ⏳ 待胡老师在网页加 SSH key |
| `git push origin master` | ⏳ 待执行 |
| GitHub release v41.1 | ⏳ 待胡老师在网页操作 |

## 4. 守门

- ✅ 557 tests pass（v41.1 后）
- ✅ `make verify` 90 verified / 0 fail
- ✅ 美机未触碰
- ✅ 无凭证编造

## 5. 下一步（必须胡老师介入）

1. **胡老师在 GitHub 网页加 SSH key**（参考 `GITHUB_SETUP.md` Step 3）
2. devagent 切 remote：HTTPS PAT → SSH
3. `git push origin master` + `git push origin v41.1`
4. 胡老师在 GitHub 网页创建 release（粘 `docs/RELEASE_NOTES_v41.1.md`）