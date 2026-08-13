"""Tests for gene_sync.py (stage 4.2 — 6h cron background sync).

3 pytest:
  1. sync_to_peer posts valid envelope
  2. min_gdi gate filters out low-GDI assets
  3. audit.jsonl records each sync
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
from gene_sync import sync_to_peer  # noqa: E402


class CaptureHandler(BaseHTTPRequestHandler):
    """Test HTTP server that captures incoming envelopes."""
    captured = []

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        from a2a_protocol import canonicalize
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        env = json.loads(body)
        self.__class__.captured.append(env)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ack": True, "decision": "accepted"}).encode())


def start_test_server(port: int):
    server = HTTPServer(("127.0.0.1", port), CaptureHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)
    return server


def test_sync_to_peer_posts_valid_envelope():
    """sync_to_peer builds valid envelope + POSTs to peer"""
    CaptureHandler.captured = []
    server = start_test_server(19871)

    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))

        # Add a high-GDI asset to local/
        good = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_sync_test", "category": "optimize",
            "signals_match": ["x", "y", "z"],
            "strategy": ["s1", "s2"],
            "summary": "High quality gene for sync test with sufficient length",
            "asset_id": "sha256:0" * 64,
            "cross_library_evidence": ["a", "b", "c", "d", "e"],
        }
        good["asset_id"] = compute_asset_id_safe(good)
        json.dump(good, open(pool.root / "local" / "g_sync_test.json", "w"),
                  ensure_ascii=False, indent=2)

        result = sync_to_peer(
            pool=pool,
            peer_url="http://127.0.0.1:19871",
            secret="test-secret",
            node_id="node:test",
            min_gdi=0.5,
        )

        server.shutdown()

    assert result["sent"] == 1, f"expected 1 sent, got {result}"
    assert result["accepted"] == 1
    assert len(CaptureHandler.captured) == 1
    env = CaptureHandler.captured[0]
    assert env["sender_node_id"] == "node:test"
    assert env["intent"] == "publish"
    assert env["asset_type"] == "Gene"
    assert env["payload"]["id"] == "g_sync_test"


def test_min_gdi_gate_filters_low_assets():
    """min_gdi gate excludes assets with low GDI score"""
    CaptureHandler.captured = []
    server = start_test_server(19872)

    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))

        # Low-GDI asset (empty signals + empty strategy → content_prior = 0)
        bad = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_bad", "category": "explore",
            "signals_match": [],  # empty → 0
            "strategy": [],       # empty → 0
            "summary": "",        # empty → 0
            "asset_id": "sha256:0" * 64,
        }
        bad["asset_id"] = compute_asset_id_safe(bad)
        json.dump(bad, open(pool.root / "local" / "g_bad.json", "w"),
                  ensure_ascii=False, indent=2)

        # With min_gdi=0.7 (strict), bad should be filtered out
        result = sync_to_peer(
            pool=pool,
            peer_url="http://127.0.0.1:19872",
            secret="test-secret",
            node_id="node:test",
            min_gdi=0.7,
        )

        server.shutdown()

    assert result["sent"] == 0, f"bad gene should be filtered, got {result}"
    assert len(CaptureHandler.captured) == 0


def test_audit_log_records_sync():
    """sync_to_peer writes audit.jsonl entries"""
    CaptureHandler.captured = []
    server = start_test_server(19873)

    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))

        good = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_audit", "category": "optimize",
            "signals_match": ["x", "y", "z"],
            "strategy": ["s1", "s2", "s3"],
            "summary": "Long enough summary to pass content_prior gate in sync test",
            "asset_id": "sha256:0" * 64,
            "cross_library_evidence": ["a", "b", "c", "d", "e"],
        }
        good["asset_id"] = compute_asset_id_safe(good)
        json.dump(good, open(pool.root / "local" / "g_audit.json", "w"),
                  ensure_ascii=False, indent=2)

        result = sync_to_peer(
            pool=pool,
            peer_url="http://127.0.0.1:19873",
            secret="test-secret",
            node_id="node:test",
            min_gdi=0.5,
        )

        server.shutdown()

        # Check audit.jsonl
        audit_lines = (Path(tmp) / "audit.jsonl").read_text().strip().splitlines()
        sync_entries = [json.loads(l) for l in audit_lines
                        if json.loads(l).get("action") == "sync_to_peer"]
        assert len(sync_entries) == 1
        assert sync_entries[0]["peer"] == "http://127.0.0.1:19873"
        assert sync_entries[0]["gdi_score"] >= 0.5


def compute_asset_id_safe(asset):
    from a2a_protocol import compute_asset_id
    return compute_asset_id(asset)


if __name__ == "__main__":
    test_sync_to_peer_posts_valid_envelope()
    print("✅ test_sync_to_peer_posts_valid_envelope")
    test_min_gdi_gate_filters_low_assets()
    print("✅ test_min_gdi_gate_filters_low_assets")
    test_audit_log_records_sync()
    print("✅ test_audit_log_records_sync")
    print("\n=== all 3 tests passed ===")