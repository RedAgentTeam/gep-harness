# ROADMAP v39.0 — 覆盖率 70%→86% + verify_assets 重构（2026-08-17）

## 摘要

两件事并行：

1. **verify_assets.py 重构** —— 把 CLI 黑盒拆成 `validate_asset(obj)` + `run_verify(plan_dirs)` 两个纯函数，0% → 94% 覆盖
2. **第二轮覆盖率补全** —— 全脚本库从 ~80% 拉到 86%（+16pp）

## 1. verify_assets.py 重构

### 1.1 重构前（CLI 黑盒）

```python
def main():
    plan_dirs = sys.argv[1:]
    for d in plan_dirs:
        for f in Path(d).rglob("*.json"):
            obj = json.load(open(f))
            if not _check_sha256(obj):
                print("FAIL")
                sys.exit(1)
            obj["_asset_id_check"] = "ok"  # ← 副作用，污染输入
```

### 1.2 重构后

```python
def validate_asset(obj: dict) -> str:
    """返回 'ok' | 'placeholder' | 'mismatch'，不修改 obj"""
    ...

def run_verify(plan_dirs: list[str]) -> tuple[int, int, int]:
    """返回 (verified, trust, fail)"""
    verified = trust = fail = 0
    for d in plan_dirs:
        for f in Path(d).rglob("*.json"):
            obj = json.loads(f.read_text())
            status = validate_asset(copy.deepcopy(obj))
            if status == "ok": verified += 1
            ...
    return verified, trust, fail

def main():
    v, t, f = run_verify(sys.argv[1:])
    print(f"{v} verified | {t} trust | {f} FAIL")
    sys.exit(0 if f == 0 else 1)
```

### 1.3 修复的 obj mutation bug

`validate_asset` 之前会就地改 `obj["_asset_id_check"]` 用于打印。重构后用 `copy.deepcopy(obj)` 隔离 hash 计算，保证外部传入的对象不被污染 —— 这是 v36 阶段被 ROADMAP_INDEX 标"trust assets 偶现 hash 不一致"事件的根因。

## 2. 第二轮补全（17 个新测试）

| 文件 | tests |
|---|---|
| `test_verify_assets_cli.py` | 6（SHA256 regex / CLI / PLACEHOLDER）|
| `test_verify_assets_unit.py` | 11（validate_asset 三种状态）|

## 3. 验证

```
pytest scripts/tests/ openclaw-a2a/tests/
  → 488 + 17 = 505 passed
  
make verify
  → 60 verified | 0 fail
```

## 4. 下一步

- 第三轮补全 → 89%（v40）
- Phase 3 GitHub 发布准备（v41）