# ROADMAP v26.0 — 5 库 v12.0 完整 CI 集成

> 日期：2026-08-15 19:45
> 分支：master
> 状态：🟡 IN PROGRESS（v11.0 五格式嵌入完成，v12.0 CI 集成启动）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest scripts/ | ✅ 23/23 |
| pytest openclaw-a2a/ | ✅ 15/15 |
| 5 格式自动生成 | ✅ PNG/SVG/PDF/EPS + ROADMAP_INDEX 自动嵌入 |

## v26.0 变更明细

| # | 变更 | 状态 |
|---|------|------|
| 1 | 5 库 v12.0 完整 CI 集成（GitHub Actions）| ✅ |
| 2 | v26.0 ROADMAP | ✅ (本次) |

## GitHub Actions CI 集成

```yaml
name: gep-harness-ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install graphviz
        run: sudo apt-get install -y graphviz
      - name: Install dependencies
        run: pip install pytest pytest-cov
      - name: Run tests
        run: make verify && make test
      - name: Generate 5-format graph
        run: python3 scripts/visualize_5lib_graph.py --png --svg --pdf --embed-index
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: 5lib-graph
          path: |
            docs/5LIB_GRAPH.png
            docs/5LIB_GRAPH.svg
            docs/5LIB_GRAPH.pdf
            docs/5LIB_GRAPH.eps
```

## 下一步（v27.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | GitHub Phase 3 发布（需胡老师拍板仓库地址）| 阻塞 |
| B | 美机 <美机生产 IP> 跨节点真部署 | ❌ 严禁没确认 |
| C | 5 库 v13.0（CI 矩阵多 Python 版本）| 下次 |

## 严禁事项（5 条铁律 + 1 条新加）

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v26.0 是 **5 库 v12.0 CI 集成版本**：GitHub Actions 完整流水线（test + 5 格式生成 + artifact 上传）。下一步 v27.0 候选 A/B/C 待胡老师拍板。