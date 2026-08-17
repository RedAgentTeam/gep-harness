"""Test verify_assets.py __main__ block (94%→100%)。

补 missing lines: 75, 111-113
- 75: plan_dirs = [repo / "plan/genes", ...] (in __main__)
- 111-113: if __name__ == "__main__": ok,trust,fail = run_verify(); sys.exit(...)
"""

import subprocess
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
VERIFY = REPO / "scripts" / "verify_assets.py"


def test_module_main_all_ok():
    """__main__: plan/genes 全 ok → exit 0。"""
    r = subprocess.run(
        [sys.executable, str(VERIFY)],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    # 最后一行应是 === ... verified ... FAIL ===
    last = r.stdout.strip().splitlines()[-1]
    assert "verified" in last
    assert "FAIL ===" in last or "FAIL" in last





def test_module_main_exit_code_logic():
    """__main__: sys.exit(1 if fail > 0 else 0) → 真 exit code。"""
    # 模拟 fail > 0 场景: 写个 plan/genes/foo.json 含坏 asset_id
    plan = REPO / "plan" / "genes"
    bad = plan / "__test_fail_xyz__.json"
    bad.write_text(
        '{"type":"Gene","id":"__test_fail_xyz__","asset_id":"sha256:0000000000000000000000000000000000000000000000000000000000000000"}'
    )
    try:
        r = subprocess.run(
            [sys.executable, str(VERIFY)],
            capture_output=True, text=True, cwd=str(REPO), timeout=30
        )
        assert r.returncode == 1, f"expected exit 1, got {r.returncode}"
        assert "__test_fail_xyz__" in r.stdout
    finally:
        bad.unlink(missing_ok=True)
    # 删掉坏文件后再跑, 应 exit 0
    r2 = subprocess.run(
        [sys.executable, str(VERIFY)],
        capture_output=True, text=True, cwd=str(REPO), timeout=30
    )
    assert r2.returncode == 0