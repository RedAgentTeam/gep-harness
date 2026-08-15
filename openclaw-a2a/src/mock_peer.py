"""Standalone A2A mock peer — 用于本地验证 gene_sync.py 跨节点同步。

Usage:
    python3 mock_peer.py --port=19880
    python3 mock_peer.py --port=19880 --decision=rejected

Returns A2A-compatible ack envelope with `decision="accepted"` by default.
Compatible with gene_sync.py:111 expected behavior.
"""
import argparse
import json
import sys
import http.server
import socketserver
from datetime import datetime, timezone


class MockPeerHandler(http.server.BaseHTTPRequestHandler):
    decision = "accepted"
    received_count = 0
    received_log = []

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(n)
        try:
            data = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"invalid json")
            return

        MockPeerHandler.received_count += 1
        MockPeerHandler.received_log.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "envelope_id": data.get("envelope_id"),
            "asset_id": data.get("asset_id"),
            "intent": data.get("intent"),
        })

        # A2A ack envelope (gene_sync.py 期望 decision == "accepted")
        ack = {
            "schema_version": data.get("protocol_version", "1.0"),
            "envelope_id": f"ack-{data.get('envelope_id', '?')}",
            "parent_envelope_id": data.get("envelope_id"),
            "sender_node_id": "mock-peer-001",
            "recipient_node_id": data.get("sender_node_id"),
            "asset_id": data.get("asset_id"),
            "asset_type": data.get("asset_type"),
            "intent": "ack",
            "decision": self.decision,  # "accepted" / "rejected" / "quarantined"
            "reason": f"mock peer {self.decision}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        resp = json.dumps(ack).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

        # Print first 5 for visibility
        if MockPeerHandler.received_count <= 5:
            print(
                f"[mock #{MockPeerHandler.received_count}] "
                f"asset_id={data.get('asset_id', '?')[:24]} "
                f"intent={data.get('intent')}",
                file=sys.stderr,
                flush=True,
            )

    def log_message(self, *args):
        pass  # Suppress default request logs


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(description="A2A mock peer for local gene_sync testing")
    parser.add_argument("--port", type=int, default=19880, help="listen port")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="listen host (use 0.0.0.0 for cross-node deployment)",
    )
    parser.add_argument(
        "--decision",
        choices=["accepted", "rejected", "quarantined"],
        default="accepted",
        help="decision to return for every ack",
    )
    args = parser.parse_args()

    MockPeerHandler.decision = args.decision

    server = ReusableTCPServer((args.host, args.port), MockPeerHandler)
    print(f"[mock_peer] listening on 127.0.0.1:{args.port} decision={args.decision}", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[mock_peer] received {MockPeerHandler.received_count} envelopes", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
