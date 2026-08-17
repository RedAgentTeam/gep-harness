"""Test verify_assets.py __main__ block via runpy (94%→100%)。

补 missing lines: 75, 111-113
- 75: plan_dirs = [repo / "plan/genes", ...]
- 111-113: if __name__ == "__main__": ok,trust,fail = run_verify(); sys.exit(1 if fail > 0 else 0)

用 runpy.run_path(..., run_name='__main__') 让 coverage.py 在 in-process 看到 __main__ 块的执行。
"""

import runpy
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
VERIFY = REPO / "scripts" / "verify_assets.py"


def test_main_block_all_ok():
    """__main__: 正常情况 → sys.exit(0)。"""
    saved_argv = sys.argv[:]
    try:
        sys.argv = [str(VERIFY)]
        try:
            runpy.run_path(str(VERIFY), run_name="__main__")
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    finally:
        sys.argv = saved_argv
    assert exit_code == 0


def test_main_block_with_fail():
    """__main__: 写个坏 asset_id → sys.exit(1)。"""
    plan = REPO / "plan" / "genes"
    bad = plan / "__test_runpy_fail_xyz.json"
    bad.write_text(
        '{"type":"Gene","id":"__test_runpy_fail_xyz","asset_id":"sha256:0000000000000000000000000000000000000000000000000000000000000000"}'
    )
    saved_argv = sys.argv[:]
    try:
        sys.argv = [str(VERIFY)]
        try:
            runpy.run_path(str(VERIFY), run_name="__main__")
            exit_code = 0
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    finally:
        sys.argv = saved_argv
        bad.unlink(missing_ok=True)
    assert exit_code == 1


def test_main_block_plan_dirs_default():
    """__main__: line 75 plan_dirs default [plan/genes, plan/capsules, plan/events] 被实际访问。

    runpy 调 main 块时 plan_dirs=None → 走 default 分支, 命中 line 75。
    """
    saved_argv = sys.argv[:]
    try:
        sys.argv = [str(VERIFY)]
        try:
            runpy.run_path(str(VERIFY), run_name="__main__")
        except SystemExit:
            pass
    finally:
        sys.argv = saved_argv
    # 如果上面没 crash, 说明 plan_dirs default 正常工作