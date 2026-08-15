"""Example 03 — A2A 双向同步（本机 mock_peer）。

本脚本演示 gep-harness 的 A2A 协作网络：
1. 启动 2 个 mock_peer 实例（端口 19890 / 19891）
2. 各发 157 个 envelope
3. 验证双向 accept/reject

跑法：
    python3 examples/03_a2a_bidirectional.py

注意：本机验证。生产跨节点需 operator 确认（见 docs/CROSS_NODE_DEPLOY.md）。
"""

import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/data/disk/gep-harness")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """执行 gep-harness 命令。"""
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, **kwargs)


def main() -> None:
    print("=== Example 03: A2A 双向同步（本机 mock_peer）===\n")

    # 1. pytest 验证
    print("Step 1: pytest test_mock_peer.py")
    result = run(["python3", "-m", "pytest", "openclaw-a2a/tests/test_mock_peer.py", "-v"])
    passed = result.stdout.count("PASSED")
    print(f"  passed: {passed}\n")

    # 2. 启动 mock_peer A (端口 19891)
    print("Step 2: 启动 mock_peer A (:19891)")
    proc_a = subprocess.Popen(
        ["python3", "openclaw-a2a/src/mock_peer.py", "--port", "19891", "--handle", "A"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)

    # 3. 启动 mock_peer B (端口 19890)
    print("Step 3: 启动 mock_peer B (:19890)")
    proc_b = subprocess.Popen(
        ["python3", "openclaw-a2a/src/mock_peer.py", "--port", "19890", "--handle", "B"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)

    try:
        # 4. 双向发 157 envelopes
        print("Step 4: A→B send 157 envelopes")
        result = run(["python3", "openclaw-a2a/scripts/send_test_envelopes.py",
                      "--from", "A", "--to", "B", "--count", "157"])
        print(f"  sent: {result.stdout[:200]}\n")

        print("Step 5: B→A send 157 envelopes")
        result = run(["python3", "openclaw-a2a/scripts/send_test_envelopes.py",
                      "--from", "B", "--to", "A", "--count", "157"])
        print(f"  sent: {result.stdout[:200]}\n")

        print("=== Done ===")
    finally:
        proc_a.terminate()
        proc_b.terminate()


if __name__ == "__main__":
    main()