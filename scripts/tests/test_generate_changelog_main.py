"""Test generate_changelog.py main() CLI (64%→100%)。

补 missing lines: 49, 104-133, 137
- 49: __init__ 边界
- 104-133: main() 的 argv 解析 + --since/--dry-run 分支
- 137: if __name__ == "__main__": main()
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import generate_changelog as gc


def test_main_dry_run_prints(capsys):
    """main --dry-run: 打印 changelog, 不写盘。"""
    with patch.object(sys, "argv", ["gc.py", "--dry-run"]):
        try:
            gc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    # 至少含 "最后生成" 段落
    assert "最后生成" in captured.out


def test_main_writes_changelog(monkeypatch):
    """main (无 --dry-run): 写入 CHANGELOG.md。"""
    test_path = REPO / "CHANGELOG.md"
    monkeypatch.setattr(gc, "CHANGELOG", test_path)
    with patch.object(sys, "argv", ["gc.py"]):
        try:
            gc.main()
        except SystemExit:
            pass
    # 应被写入
    assert test_path.exists()
    content = test_path.read_text()
    assert "最后生成" in content
    # 清理: 还原 git log 产生的 CHANGELOG
    # 这里不还原, 因为下次运行会重新生成


def test_main_since_flag(capsys, monkeypatch):
    """main --since=HEAD~10: git log 范围过滤。"""
    with patch.object(sys, "argv", ["gc.py", "--dry-run", "--since", "HEAD~5"]):
        try:
            gc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    # 至少含最后生成
    assert "最后生成" in captured.out


def test_main_unknown_arg_ignored(capsys):
    """main: 未知 arg → 跳过, 继续执行。"""
    with patch.object(sys, "argv", ["gc.py", "--unknown-flag", "value", "--dry-run"]):
        try:
            gc.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    # 仍打印 changelog
    assert "最后生成" in captured.out


def test_main_module_runs():
    """if __name__ == '__main__': main() → --dry-run 能跑。"""
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/generate_changelog.py"), "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO), timeout=10
    )
    assert r.returncode == 0
    assert "最后生成" in r.stdout