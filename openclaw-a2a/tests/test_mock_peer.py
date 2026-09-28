"""Test mock_peer.py + gene_sync.py 跨节点同步端到端测试。

使用 pytest + subprocess + threading 启动 mock_peer.py 作为后台 HTTP server，
然后跑 gene_sync.py 验证 157 Gene 全链路通过。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
MOCK_PEER = REPO / "openclaw-a2a" / "src" / "mock_peer.py"
GENE_SYNC = REPO / "openclaw-a2a" / "src" / "gene_sync.py"


def _pool_with_one_gene(tmp_path: Path) -> Path:
    """A Gene Pool the test can read on any machine, including GitHub Actions."""
    pool = tmp_path / "gene-pool"
    local = pool / "local"
    local.mkdir(parents=True)
    src = next((REPO / "plan" / "genes").glob("*.json"))
    (local / src.name).write_bytes(src.read_bytes())
    return pool


def _wait_for_port(host: str, port: int, timeout: float = 5.0):
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


@pytest.fixture
def mock_peer():
    """Start mock_peer on a free port and tear down after test."""
    import socket
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    proc = subprocess.Popen(
        [sys.executable, str(MOCK_PEER), "--port", str(port), "--decision", "accepted"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "A2A_SHARED_SECRET": "mock-test-secret-for-pytest"},
    )
    assert _wait_for_port("127.0.0.1", port), "mock_peer failed to start"
    yield port
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_gene_sync_accepted_with_mock_peer(mock_peer, tmp_path):
    """End-to-end: gene_sync POSTs the temp pool, mock_peer accepts all."""
    port = mock_peer
    pool = _pool_with_one_gene(tmp_path)
    result = subprocess.run(
        [
            sys.executable, "-u", str(GENE_SYNC),
            f"--peer=http://127.0.0.1:{port}/a2a/receive",
            f"--pool-dir={pool}",
            "--min-gdi=0.7",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "A2A_SHARED_SECRET": "mock-test-secret-for-pytest"},
    )
    assert "sent=" in result.stdout
    # Parse last line of stdout: "... sent=N accepted=A rejected=R"
    last_line = [l for l in result.stdout.splitlines() if "sent=" in l][-1]
    sent = int(last_line.split("sent=")[1].split()[0])
    accepted = int(last_line.split("accepted=")[1].split()[0])
    rejected = int(last_line.split("rejected=")[1].split()[0])
    assert sent > 0, f"gene_sync sent no envelopes: {result.stdout}"
    assert accepted == sent, f"not all accepted: accepted={accepted} sent={sent}"
    assert rejected == 0, f"unexpected rejections: {rejected}"


def test_mock_peer_returns_decision_accepted(mock_peer):
    """Direct check: mock_peer POST returns decision='accepted'."""
    import urllib.request
    import json

    port = mock_peer
    payload = json.dumps({
        "protocol_version": "1.0",
        "sender_node_id": "test-sender",
        "envelope_id": "test-env-1",
        "asset_id": "sha256:test",
        "asset_type": "Gene",
        "intent": "publish",
        "payload": {},
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/a2a/receive",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        ack = json.loads(r.read().decode())
    assert ack["decision"] == "accepted", f"expected 'accepted', got {ack['decision']!r}"
    assert "ack-test-env-1" == ack["envelope_id"]


def test_mock_peer_rejected_decision(tmp_path):
    """Mock peer with --decision=rejected returns 'rejected' to gene_sync."""
    pool = _pool_with_one_gene(tmp_path)
    import socket
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    proc = subprocess.Popen(
        [sys.executable, str(MOCK_PEER), "--port", str(port), "--decision", "rejected"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "A2A_SHARED_SECRET": "mock-test-secret-for-pytest"},
    )
    try:
        assert _wait_for_port("127.0.0.1", port)
        result = subprocess.run(
            [
                sys.executable, str(GENE_SYNC),
                f"--peer=http://127.0.0.1:{port}/a2a/receive",
                f"--pool-dir={pool}",
                "--min-gdi=0.7",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "A2A_SHARED_SECRET": "mock-test-secret-for-pytest"},
        )
        last_line = [l for l in result.stdout.splitlines() if "sent=" in l][-1]
        rejected = int(last_line.split("rejected=")[1].split()[0])
        sent = int(last_line.split("sent=")[1].split()[0])
        assert sent > 0
        assert rejected == sent, f"rejected_decision: rejected={rejected} sent={sent}"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
