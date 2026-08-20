"""cron 6h 联动 — gep-harness v22.0（v21.0 升级）。

聚合 5 个自动任务到一个脚本，由 cron 6h 调用：
0. cross_lib_auto_evolve.py: 重算 dynamic edges + 重新生成图谱 5 格式（v21.0）
1. trust_auto_flip.py: set_active_edges(dynamic_edges) 让 trust_score 用 dynamic 值（v22.0）
2. check_5lib_assets.py --fix: 6 格式产物检查 + 自动补
3. generate_changelog.py: CHANGELOG 自动生成
4. auto_changelog_commit.py: CHANGELOG 自动 commit

跑法：
    python3 scripts/cron_hourly_workflow.py
    python3 scripts/cron_hourly_workflow.py --skip-commit  # 仅生成不 commit
    python3 scripts/cron_hourly_workflow.py --skip-evolve  # 跳过 cross_lib auto-evolve
    python3 scripts/cron_hourly_workflow.py --skip-flip    # 跳过 trust_auto_flip
    python3 scripts/cron_hourly_workflow.py --restore-static  # 紧急回退 trust 静态
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG_FILE = REPO / "logs/cron_workflow.log"


def run_step(name: str, args: list[str], cwd: Path = REPO) -> bool:
    """跑一个步骤，fail-fast。"""
    print(f"\n{'='*60}")
    print(f"▶ {name}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, *args],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode == 0:
        print(f"✅ {name} OK")
        if result.stdout:
            print(result.stdout[-500:])  # tail 500 chars
        return True
    print(f"❌ {name} FAILED (exit={result.returncode})")
    if result.stderr:
        print(result.stderr[-500:])
    return False


def log_to_file(line: str) -> None:
    """追加日志到 logs/cron_workflow.log。"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(line + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-commit", action="store_true", help="跳过 auto commit")
    parser.add_argument("--skip-5lib", action="store_true", help="跳过 5 库产物检查")
    parser.add_argument("--skip-evolve", action="store_true", help="跳过 cross_lib auto-evolve")
    parser.add_argument("--skip-flip", action="store_true", help="跳过 trust_auto_flip")
    parser.add_argument("--restore-static", action="store_true", help="紧急回退：trust_score 恢复静态基线后退出")
    args = parser.parse_args()

    log_to_file(f"\n--- {REPO.name} cron_hourly_workflow start ---")

    # --restore-static：紧急回退，跳过所有自动任务，仅恢复静态基线
    if args.restore_static:
        print("⚠️ 紧急回退模式：跳过所有自动任务，仅恢复静态")
        return run_step(
            "trust_auto_flip --restore-static",
            ["scripts/trust_auto_flip.py", "--restore-static"],
        )

    # Step 0: v21.0 cross_lib auto-evolve（重算 dynamic edges + 重生成图谱）
    if not args.skip_evolve:
        ok = run_step(
            "cross_lib_auto_evolve",
            ["scripts/cross_lib_auto_evolve.py"],
        )
        if not ok:
            log_to_file("cross_lib_auto_evolve FAILED")
            return 1
        log_to_file("cross_lib_auto_evolve OK")
    else:
        print("⏭️ 跳过 cross_lib auto-evolve")

    # Step 1: v22.0 trust_auto_flip（set_active_edges 让 trust_score 用 dynamic）
    if not args.skip_flip:
        ok = run_step(
            "trust_auto_flip",
            ["scripts/trust_auto_flip.py"],
        )
        if not ok:
            log_to_file("trust_auto_flip FAILED")
            return 1
        log_to_file("trust_auto_flip OK")
    else:
        print("⏭️ 跳过 trust_auto_flip")

    # Step 2: 5 库产物检查 + 自动补
    if not args.skip_5lib:
        ok = run_step(
            "check_5lib_assets --fix",
            ["scripts/check_5lib_assets.py", "--fix"],
        )
        if not ok:
            log_to_file("check_5lib_assets FAILED")
            return 1
        log_to_file("check_5lib_assets OK")
    else:
        print("⏭️ 跳过 5 库检查")

    # Step 3: CHANGELOG 自动生成
    ok = run_step(
        "generate_changelog",
        ["scripts/generate_changelog.py"],
    )
    if not ok:
        log_to_file("generate_changelog FAILED")
        return 1
    log_to_file("generate_changelog OK")

    # Step 4: CHANGELOG 自动 commit
    if not args.skip_commit:
        ok = run_step(
            "auto_changelog_commit",
            ["scripts/auto_changelog_commit.py", "--message=auto: cron 6h workflow"],
        )
        if not ok:
            log_to_file("auto_changelog_commit FAILED")
            return 1
        log_to_file("auto_changelog_commit OK")
    else:
        print("⏭️ 跳过 commit")

    log_to_file("--- cron_hourly_workflow DONE ---\n")
    print("\n✅ cron 6h 联动 5 步全部 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
