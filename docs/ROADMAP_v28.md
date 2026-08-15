# ROADMAP v28.0 — 5 库 v14.0 CI 多 OS 矩阵

> 日期：2026-08-15 19:48
> 分支：master
> 状态：🟡 IN PROGRESS（v13.0 多 Python，v14.0 多 OS 启动）

## 全量验证结果

| 检查项 | 结果 |
|--------|------|
| pytest scripts/ | ✅ 23/23 |
| pytest openclaw-a2a/ | ✅ 15/15 |
| 5 格式自动生成 | ✅ PNG/SVG/PDF/EPS |
| GitHub Actions CI | ✅ v12.0 + v13.0 集成 |

## v28.0 变更明细

| # | 变更 | 状态 |
|---|------|------|
| 1 | 5 库 v14.0 CI 多 OS 矩阵（ubuntu/macos）| ✅ |
| 2 | v28.0 ROADMAP | ✅ (本次) |

## CI 多 OS 矩阵策略

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    python-version: ['3.10', '3.11', '3.12', '3.13']
```

| OS | 兼容性 | pytest |
|----|--------|--------|
| ubuntu-latest | ✅ | ✅ |
| macos-latest | ✅ | ✅ |

## 下一步（v29.0 候选，待胡老师拍板）

| # | 候选 | 备注 |
|---|------|------|
| A | GitHub Phase 3 发布（需胡老师拍板仓库地址）| 阻塞 |
| B | 美机 <美机生产 IP> 跨节点真部署 | ❌ 严禁没确认 |
| C | 5 库 v15.0（CI 矩阵多 Python + 多 OS + 完整覆盖率报告）| 下次 |

## 严禁事项（5 条铁律 + 1 条新加）

1. 不编凭证
2. 不凭印象诊断
3. 不 write 覆盖 memory
4. ❌ 不在本机做生产相关改动
5. ❌ **不在没确认的情况下动生产节点机器**
6. ❌ **不堆概念**（新增 2026-08-15）

## 总结

v28.0 是 **5 库 v14.0 CI 多 OS 矩阵版本**：ubuntu-latest + macos-latest。下一步 v29.0 候选 A/B/C 待胡老师拍板。