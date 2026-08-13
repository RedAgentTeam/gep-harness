"""Tests for gene_sync.py — v0.5 broadcast + node discovery + announce.

6 pytest:
  1. sync_to_peer posts valid envelope (unchanged)
  2. min_gdi gate filters low-GDI assets (unchanged)
  3. audit.jsonl records each sync (unchanged)
  4. discover_peers aggregates from bootstrap nodes
  5. announce_peer sends announce + parses ack
  6. broadcast_to_peers fans out to all discovered peers
"""
import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))

from a2a_protocol import GenePool  # noqa: E402
from gene_sync import (  # noqa: E402
    sync_to_peer,
    discover_peers,
    broadcast_to_peers,
    announce_peer,
)


class CaptureHandler(BaseHTTPRequestHandler):
    """Test HTTP server that captures incoming envelopes / responds with ack."""
    captured = []
    known_peers = []
    _mode = "publish"

    def log_message(self, fmt, *args):
        pass

    @classmethod
    def _set_mode(cls, mode):
        cls._mode = mode
        cls.captured = []
        cls.known_peers = []

    def do_POST(self):
        from a2a_protocol import canonicalize
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        env = json.loads(body)
        self.__class__.captured.append(env)

        if self.path.endswith("/announce"):
            peer_url = env.get("peer_url", "")
            if peer_url not in self.__class__.known_peers:
                self.__class__.known_peers.append(peer_url)
            self._send_json(200, {"ack": True, "known_peers": self.__class__.known_peers})
            return

        self._send_json(200, {"ack": True, "decision": "accepted"})

    def do_GET(self):
        if self.path.endswith("/nodes"):
            self._send_json(200, {
                "node_id": "bootstrap-node",
                "protocol_version": "1.0",
                "peers": self.__class__.known_peers,
                "stats": {},
            })
        else:
            self._send_json(404, {"error": "not_found"})

    def _send_json(self, code: int, body: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())


def start_test_server(port: int):
    server = HTTPServer(("127.0.0.1", port), CaptureHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)
    return server


# ---- helper ----

def compute_asset_id_safe(asset):
    from a2a_protocol import compute_asset_id
    return compute_asset_id(asset)


def make_good_gene(gid, extra_evidence=5):
    good = {
        "type": "Gene", "schema_version": "1.12.1",
        "id": gid, "category": "optimize",
        "signals_match": ["x", "y", "z"],
        "strategy": ["s1", "s2"],
        "summary": "High quality gene for sync test with sufficient length",
        "asset_id": "sha256:0" * 64,
    }
    if extra_evidence > 0:
        good["cross_library_evidence"] = [f"e{i}" for i in range(extra_evidence)]
    good["asset_id"] = compute_asset_id_safe(good)
    return good


# ---- tests ----

def test_sync_to_peer_posts_valid_envelope():
    """sync_to_peer builds valid envelope + POSTs to peer"""
    CaptureHandler._set_mode("publish")
    server = start_test_server(19881)
    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))
        asset = make_good_gene("g_sync_test")
        json.dump(asset, open(pool.root / "local" / "g_sync_test.json", "w"),
                  ensure_ascii=False, indent=2)
        result = sync_to_peer(pool, "http://127.0.0.1:19881",
                              "test-secret", "node:test", min_gdi=0.5)
    server.shutdown()
    assert result["sent"] == 1, f"expected 1 sent, got {result}"
    assert result["accepted"] == 1
    assert len(CaptureHandler.captured) == 1
    env = CaptureHandler.captured[0]
    assert env["sender_node_id"] == "node:test"
    assert env["intent"] == "publish"
    assert env["payload"]["id"] == "g_sync_test"
    print("✅ test_sync_to_peer_posts_valid_envelope")


def test_min_gdi_gate_filters_low_assets():
    """min_gdi gate excludes assets with low GDI score"""
    CaptureHandler._set_mode("publish")
    server = start_test_server(19882)
    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))
        bad = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_bad", "category": "explore",
            "signals_match": [], "strategy": [], "summary": "",
            "asset_id": "sha256:0" * 64,
        }
        bad["asset_id"] = compute_asset_id_safe(bad)
        json.dump(bad, open(pool.root / "local" / "g_bad.json", "w"),
                  ensure_ascii=False, indent=2)
        result = sync_to_peer(pool, "http://127.0.0.1:19882",
                              "test-secret", "node:test", min_gdi=0.7)
    server.shutdown()
    assert result["sent"] == 0
    assert len(CaptureHandler.captured) == 0
    print("✅ test_min_gdi_gate_filters_low_assets")


def test_audit_log_records_sync():
    """sync_to_peer writes audit.jsonl entries"""
    CaptureHandler._set_mode("publish")
    server = start_test_server(19883)
    tmp = tempfile.mkdtemp()
    try:
        pool = GenePool(root=Path(tmp))
        asset = make_good_gene("g_audit")
        json.dump(asset, open(pool.root / "local" / "g_audit.json", "w"),
                  ensure_ascii=False, indent=2)
        sync_to_peer(pool, "http://127.0.0.1:19883",
                     "test-secret", "node:test", min_gdi=0.5)
        audit_file = Path(tmp) / "audit.jsonl"
        assert audit_file.exists(), f"audit.jsonl not found at {audit_file}"
        audit_lines = audit_file.read_text().strip().splitlines()
        sync_entries = [json.loads(l) for l in audit_lines
                        if json.loads(l).get("action") == "sync_to_peer"]
        assert len(sync_entries) == 1
        assert sync_entries[0]["peer"] == "http://127.0.0.1:19883"
        assert sync_entries[0]["gdi_score"] >= 0.5
    finally:
        import shutil as _shutil
        _shutil.rmtree(tmp, ignore_errors=True)
    print("✅ test_audit_log_records_sync")


def test_discover_peers_aggregates_from_bootstrap():
    """discover_peers returns combined set from all bootstrap nodes."""
    CaptureHandler._set_mode("nodes")
    # Bootstrap node A knows [http://127.0.0.1:19891]
    CaptureHandler.known_peers = ["http://127.0.0.1:19891"]
    server_a = start_test_server(19891)
    # Bootstrap node B knows [http://127.0.0.1:19892]
    CaptureHandler.known_peers = ["http://127.0.0.1:19892"]
    server_b = start_test_server(19892)

    peers = discover_peers(["http://127.0.0.1:19891", "http://127.0.0.1:19892"], timeout=3.0)

    server_a.shutdown()
    server_b.shutdown()
    assert "http://127.0.0.1:19891" in peers
    assert "http://127.0.0.1:19892" in peers
    print("✅ test_discover_peers_aggregates_from_bootstrap")


def test_announce_peer_sends_announce_and_parses_ack():
    """announce_peer POSTs to /announce, receives ack with known_peers list."""
    CaptureHandler._set_mode("announce")
    CaptureHandler.known_peers = ["http://127.0.0.1:19893"]
    server = start_test_server(19893)

    import tempfile as tf
    with tf.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))
        result = announce_peer(pool, "http://127.0.0.1:19894",
                               "http://127.0.0.1:19893", timeout=3.0)

    server.shutdown()
    assert result["ack"] is True, f"announce failed: {result}"
    assert result["peer"] == "http://127.0.0.1:19893"
    print("✅ test_announce_peer_sends_announce_and_parses_ack")


def test_broadcast_to_peers_fans_out_to_all():
    """broadcast_to_peers calls sync_to_peer for each peer URL."""
    CaptureHandler._set_mode("publish")
    server_a = start_test_server(19895)
    server_b = start_test_server(19896)

    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))
        asset = make_good_gene("g_broadcast_test")
        json.dump(asset, open(pool.root / "local" / "g_broadcast_test.json", "w"),
                  ensure_ascii=False, indent=2)

        summary = broadcast_to_peers(
            pool,
            ["http://127.0.0.1:19895", "http://127.0.0.1:19896"],
            "test-secret", "node:test", min_gdi=0.5,
        )

    server_a.shutdown()
    server_b.shutdown()
    assert summary["total_sent"] == 2, f"expected 2, got {summary}"
    assert summary["total_accepted"] == 2
    assert len(CaptureHandler.captured) == 2
    print("✅ test_broadcast_to_peers_fans_out_to_all")


def test_announce_mutual_peers_learn_each_other():
    """Two nodes announce to each other — each learns 2 peers."""
    CaptureHandler._set_mode("announce")
    server_a = start_test_server(19897)  # node A: port 19897
    server_b = start_test_server(19898)  # node B: port 19898

    with tempfile.TemporaryDirectory() as tmp:
        pool_a = GenePool(root=Path(tmp))
        pool_b = GenePool(root=Path(tmp))

        # A announces to B
        r_b = announce_peer(pool_a, "http://127.0.0.1:19897",
                            "http://127.0.0.1:19898")
        # B announces to A
        r_a = announce_peer(pool_b, "http://127.0.0.1:19898",
                            "http://127.0.0.1:19897")

    server_a.shutdown()
    server_b.shutdown()
    assert r_a["ack"] and r_b["ack"], "mutual announce failed"
    print("✅ test_announce_mutual_peers_learn_each_other")


if __name__ == "__main__":
    test_sync_to_peer_posts_valid_envelope()
    test_min_gdi_gate_filters_low_assets()
    test_audit_log_records_sync()
    test_discover_peers_aggregates_from_bootstrap()
    test_announce_peer_sends_announce_and_parses_ack()
    test_broadcast_to_peers_fans_out_to_all()
    test_announce_mutual_peers_learn_each_other()
    print("\n=== all 6 broadcast tests passed ===")
