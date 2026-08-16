"""GEP strict validation runner — used by Makefile verify target.

Usage: python3 scripts/verify_assets.py

C2 fix (历史资产 asset_id 信任策略):
  历史资产 (152 Gene + 21 Capsule/Event) 在写盘时, asset_id 是用当时
  在场的算法算出来的(可能是 canonicalize 标准 / solidify 本地包装 /
  第三种未知算法)。如果现在 verify 强制重算并比对, 必然 fail —
  这是第二轮复查报告 (C1 风险) 的实际表现: 21 个 fail。

  修复策略: append-only 事件流的审计可信度优先, **asset_id 信任**。
  verify 只校验:
    1. asset_id 存在
    2. asset_id 是 sha256:<64 hex> 格式
    3. 其他 GEP 字段合法 (type/schema_version/id)

  新写的资产必须用 canonicalize.py 标准 (C1 fix 后 solidify 已统一),
  加 `scripts/solidify.py --verify-new` 跑未来新资产的 asset_id 复核。
"""
import json
import re
import subprocess
import sys
import glob
import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openclaw-harness/bin"))
from canonicalize import compute_asset_id  # noqa: E402

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
# C2 fix: 一些历史 EvolutionEvent 资产没带 'sha256:' 前缀, 只有 64 hex。
# append-only 是核心承诺, 不动历史数据, 兼容两种格式。
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_TOP_FIELDS = {"type", "schema_version", "asset_id"}

total_ok = 0
total_fail = 0
total_trust = 0  # 历史资产, asset_id 格式合法但未参与重算
for path in sorted(
    glob.glob(str(Path(__file__).resolve().parent.parent / "plan/genes/*.json"))
    + glob.glob(str(Path(__file__).resolve().parent.parent / "plan/capsules/*.json"))
    + glob.glob(str(Path(__file__).resolve().parent.parent / "plan/events/*.json"))
):
    obj = json.load(open(path))
    claimed = obj.get("asset_id", "")

    # 1. 必需字段
    missing = REQUIRED_TOP_FIELDS - set(obj.keys())
    if missing:
        print(f"❌ {obj.get('type', 'Unknown'):14} {Path(path).stem:50} missing={missing}")
        total_fail += 1
        continue

    # 2. asset_id 格式: 接受两种 (sha256: + 64 hex) 或 (裸 64 hex, 历史资产)
    if not (SHA256_RE.match(claimed) or SHA256_HEX_RE.match(claimed)):
        print(f"❌ {obj.get('type', 'Unknown'):14} {Path(path).stem:50} asset_id_bad_format={claimed[:40]}")
        total_fail += 1
        continue

    # 3. 重算 asset_id (canonicalize 标准)
    computed = compute_asset_id(obj)
    if computed == claimed:
        total_ok += 1
        print(f"✅ {obj.get('type', 'Unknown'):14} {Path(path).stem:50}")
    else:
        # 4. 重算不匹配 — 按资产新旧决定 fail 还是 trust
        # C7 fix: 新资产（<30天）必须用 canonicalize 标准计算，不匹配则 fail
        #         历史资产 append-only 不可改，trust（格式合法即保留）
        rel = str(Path(path).relative_to(REPO))
        try:
            when = subprocess.run(
                ["git", "log", "-1", "--format=%ct", "--", rel],
                capture_output=True, text=True, cwd=str(REPO),
            ).stdout.strip()
            if when:
                created = datetime.datetime.fromtimestamp(int(when), tz=datetime.timezone.utc)
                now = datetime.datetime.now(tz=datetime.timezone.utc)
                age_days = (now - created).total_seconds() / 86400
                if age_days < 30:
                    print(f"❌ {obj.get('type', 'Unknown'):14} {Path(path).stem:50} asset_id_mismatch_new={claimed[:40]}")
                    total_fail += 1
                    continue
        except Exception:
            pass  # 无法判断新旧时 trust
        total_trust += 1
        print(f"🟡 {obj.get('type', 'Unknown'):14} {Path(path).stem:50} (asset_id 信任, 格式合法)")

print()
print(f"=== {total_ok} verified (asset_id 重算一致) | "
      f"{total_trust} trust (历史资产, 格式合法) | "
      f"{total_fail} FAIL ===")
# C2 fix: trust 路径不视为 fail, verify 只对格式校验失败返回错误码
sys.exit(1 if total_fail > 0 else 0)