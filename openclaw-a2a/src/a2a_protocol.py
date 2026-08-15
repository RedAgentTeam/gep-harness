"""A2A Protocol v0.1.0 implementation.

Standalone A2A server (no OpenClaw framework dependency).
Reference: /data/disk/gep-harness/openclaw-a2a/docs/a2a_protocol.md
"""
import hashlib
import hmac
import json
import os
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
import shutil
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# P1-2: optional ed25519 backend (preferred over HMAC for new envelopes).
# If cryptography is unavailable, fall back to HMAC-SHA256 with a clear warning.
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519 as _ed25519
    from cryptography.exceptions import InvalidSignature as _InvalidSignature
    _ED25519_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ed25519 = None
    _InvalidSignature = Exception  # type: ignore
    _ED25519_AVAILABLE = False

PROTOCOL_VERSION = "1.0"

DEFAULT_PORT = 9877
DEFAULT_POOL_DIR = Path.home() / ".openclaw/gene-pool"

INTENTS = ("publish", "request", "ack", "reject")
ASSET_TYPES = ("Gene", "Capsule", "EvolutionEvent")

# GDI v2 weights
GDI_WEIGHTS = {
    "content_prior": 0.4,
    "offline_check": 0.2,
    "behavior_feedback": 0.4,
}
# v0.2: GDI_THRESHOLD back to 0.7 (was 0.6 in v0.1 due to behavior_feedback
# verification gap). Now that behavior_feedback_proof is signed, peers
# can verify and trust the 3rd dimension.
GDI_THRESHOLD = 0.7


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def canonicalize(obj):
    """GEP-compatible canonicalize (same algorithm as gep-sdk-js)."""
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        if isinstance(obj, float):
            import math
            if not math.isfinite(obj):
                return "null"
        return str(obj)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, list):
        return "[" + ",".join(canonicalize(x) for x in obj) + "]"
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        return "{" + ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + canonicalize(obj[k])
            for k in keys
        ) + "}"
    return "null"


def compute_asset_id(obj):
    if not isinstance(obj, dict):
        return None
    clean = {k: v for k, v in obj.items() if k != "asset_id"}
    return "sha256:" + hashlib.sha256(
        canonicalize(clean).encode("utf-8")
    ).hexdigest()


def get_node_id() -> str:
    return os.environ.get("A2A_NODE_ID") or f"node:{socket.gethostname()}"


def get_node_secret() -> str:
    # P0-2 fix: NO silent default. Missing shared secret is a fatal config error,
    # not a fallback to a public string that voids HMAC entirely.
    # v0.2: shared secret model (trust bootstrap via A2A_SHARED_SECRET env).
    # v0.3 should switch to per-node keypair + signed public key exchange.
    secret = (
        os.environ.get("A2A_SHARED_SECRET")
        or os.environ.get("A2A_NODE_SECRET")
    )
    if not secret:
        raise RuntimeError(
            "A2A_SHARED_SECRET (or A2A_NODE_SECRET) environment variable is required. "
            "Refusing to fall back to a default shared secret: that would make HMAC "
            "signatures trivially forgeable by anyone with source access. "
            "Set A2A_SHARED_SECRET=<random-string-from-password-manager> in your env "
            "before starting the A2A server."
        )
    return secret


def sign_message(payload: dict, secret: str, algorithm: str = "hmac-sha256") -> str:
    """Sign a message using the requested algorithm.

    Algorithms:
      - "hmac-sha256" (default, backward-compat): signature = "sha256:<hex>"
      - "ed25519": signature = "ed25519:<base64(64-byte signature)>",
        where `secret` is a raw 32-byte ed25519 private key.

    P1-2: ed25519 is the preferred algorithm for new envelopes.
    """
    payload_bytes = canonicalize(payload).encode("utf-8")
    if algorithm == "ed25519":
        if not _ED25519_AVAILABLE:
            raise RuntimeError(
                "ed25519 signing requested but `cryptography` package is not "
                "installed. Run: pip install cryptography"
            )
        priv = _ed25519.Ed25519PrivateKey.from_private_bytes(secret)
        sig_bytes = priv.sign(payload_bytes)
        return "ed25519:" + base64.b64encode(sig_bytes).decode("ascii")
    # default: hmac-sha256
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return "sha256:" + sig


def verify_signature(payload: dict, signature: str, secret: str) -> bool:
    """Verify a signature regardless of its algorithm prefix.

    Accepts both "sha256:<hex>" (HMAC) and "ed25519:<base64>" signatures.
    """
    if signature.startswith("ed25519:"):
        if not _ED25519_AVAILABLE:
            return False
        try:
            sig_bytes = base64.b64decode(signature[len("ed25519:"):], validate=True)
            pub = _ed25519.Ed25519PublicKey.from_public_bytes(secret)
            pub.verify(sig_bytes, canonicalize(payload).encode("utf-8"))
            return True
        except (_InvalidSignature, ValueError, TypeError):
            return False
    # default: hmac-sha256
    expected = sign_message(payload, secret, algorithm="hmac-sha256")
    return hmac.compare_digest(expected, signature)


def make_envelope(
    sender_node_id: str,
    recipient_node_id: str,
    asset_id: str,
    asset_type: str,
    intent: str,
    payload: dict,
    secret: str,
    behavior_feedback_proof: dict | None = None,
) -> dict:
    """Build a signed A2A envelope.

    behavior_feedback_proof (optional): signed proof of reuse outcome=success.
        Format: {"reuses": [{"ts": ISO8601, "outcome": "success"}], "signature": "..."}
        Peer should verify signature before trusting feedback claim.
    """
    if asset_type not in ASSET_TYPES:
        raise ValueError(f"invalid asset_type: {asset_type!r}")
    if intent not in INTENTS:
        raise ValueError(f"invalid intent: {intent!r}")

    env = {
        "protocol_version": PROTOCOL_VERSION,
        "sender_node_id": sender_node_id,
        "recipient_node_id": recipient_node_id,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "intent": intent,
        "payload": payload,
        "ts": now_iso(),
    }
    if behavior_feedback_proof is not None:
        env["behavior_feedback_proof"] = behavior_feedback_proof
    env["signature"] = sign_message(payload, secret)
    return env


def gdi_score(asset: dict, has_behavior_feedback: bool = False) -> float:
    """Compute GDI v2 score for an incoming Gene asset.

    Args:
        asset: The Gene (or Capsule/EvolutionEvent) payload
        has_behavior_feedback: Whether this gene has been confirmed by
                               reuse outcome=success on this node
                               (e.g. via verified behavior_feedback_proof)

    Returns:
        float in [0, 1]

    Logic:
        - content_prior is REQUIRED (max weight 0.4, 0 if not met)
        - offline_check adds up to 0.2
        - behavior_feedback adds 0.4 if confirmed
        - A gene with poor content can NEVER reach 0.7 threshold,
          even with behavior_feedback=True.
    """
    score = 0.0

    # 1. content_prior (0.4) — required
    sm = asset.get("signals_match", [])
    strategy = asset.get("strategy", [])
    summary = asset.get("summary", "")
    if len(sm) >= 2 and len(strategy) >= 2 and len(summary) >= 20:
        score += GDI_WEIGHTS["content_prior"]
    elif len(sm) >= 1 and len(strategy) >= 1:
        score += GDI_WEIGHTS["content_prior"] * 0.5
    # else: 0 (insufficient content)

    # 2. offline_check (0.2)
    if compute_asset_id(asset) == asset.get("asset_id"):
        score += GDI_WEIGHTS["offline_check"] * 0.5
    if len(asset.get("cross_library_evidence", [])) >= 5:
        score += GDI_WEIGHTS["offline_check"] * 0.5

    # 3. behavior_feedback (0.4)
    if has_behavior_feedback:
        score += GDI_WEIGHTS["behavior_feedback"]

    return min(score, 1.0)


def verify_behavior_feedback_proof(
    proof: dict, secret: str
) -> bool:
    """Verify a behavior_feedback_proof object.

    Format: {"reuses": [{"ts": ISO8601, "outcome": "success"}], "signature": "..."}
    The signature is HMAC over canonicalize({"reuses": [...]}).
    Returns True if signature is valid AND at least 1 reuse outcome=success.
    """
    if not isinstance(proof, dict):
        return False
    reuses = proof.get("reuses", [])
    signature = proof.get("signature", "")
    if not reuses or not signature:
        return False
    # Verify signature
    expected = sign_message({"reuses": reuses}, secret)
    if not hmac.compare_digest(expected, signature):
        return False
    # At least 1 success outcome
    return any(r.get("outcome") == "success" for r in reuses)


class GenePool:
    """Local Gene Pool manager."""

    def __init__(self, root: Path | None = None):
        self.root = root or Path(
            os.environ.get("A2A_GENE_POOL_DIR") or DEFAULT_POOL_DIR
        )
        for sub in ("local", "imported", "quarantined"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def audit_log(self, event: dict):
        """Append to audit.jsonl."""
        line = json.dumps(event, ensure_ascii=False) + "\n"
        with open(self.root / "audit.jsonl", "a", encoding="utf-8") as f:
            f.write(line)

    def _conflict_dir(self) -> Path:
        return self.root / "conflicts"

    def _scan_conflicts(self) -> dict[str, list[Path]]:
        """Scan imported/ for asset_id collisions.

        Returns {asset_id: [paths]} — includes single entries so callers can
        detect "existing winner" even before a second file arrives.
        """
        collisions: dict[str, list[Path]] = {}
        for p in (self.root / "imported").glob("*.json"):
            try:
                asset = json.load(open(p))
            except (json.JSONDecodeError, FileNotFoundError):
                continue
            aid = asset.get("asset_id", "unknown")
            collisions.setdefault(aid, []).append(p)
        return collisions

    def _apply_lww(self, asset_id: str, paths: list[Path]) -> Path:
        """Last-Write-Wins conflict resolution for duplicate asset_ids.

        Winner = highest modified_at timestamp.
        Losers = moved to conflicts/ with __conflict_<ts> suffix.
        Returns the winner path.
        """
        existing = [(p, p.stat().st_mtime) for p in paths if p.exists()]
        if not existing:
            # Nothing to resolve yet — first import
            return paths[0] if paths else Path(".")
        existing.sort(key=lambda x: x[1], reverse=True)
        winner_path = existing[0][0]
        loser_paths = existing[1:]

        conflict_dir = self._conflict_dir()
        conflict_dir.mkdir(parents=True, exist_ok=True)
        ts = now_iso().replace(":", "-")
        for loser_path, _ in loser_paths:
            new_name = loser_path.stem + f"__conflict_{ts}"
            shutil.move(loser_path, conflict_dir / (new_name + loser_path.suffix))
            self.audit_log({
                "ts": now_iso(),
                "action": "conflict_lww_loser",
                "asset_id": asset_id,
                "winner": str(winner_path),
                "loser": str(loser_path),
                "resolution": "last_write_wins",
            })
        return winner_path

    def accept(
        self,
        asset: dict,
        source_node: str,
        behavior_feedback_proof: dict | None = None,
        peer_secret: str | None = None,
    ) -> tuple[str, str]:
        """Accept an incoming asset to imported/ or quarantined/.

        CRDT: if asset_id already exists in imported/, last-write-wins
        (newer mtime replaces older). Loser moved to conflicts/.
        """
        has_feedback = False
        if behavior_feedback_proof and peer_secret:
            has_feedback = verify_behavior_feedback_proof(
                behavior_feedback_proof, peer_secret
            )

        gdi = gdi_score(asset, has_behavior_feedback=has_feedback)
        asset_id = asset.get("asset_id", "unknown")
        if gdi >= GDI_THRESHOLD:
            sub = "imported"
            decision = "accepted"
        else:
            sub = "quarantined"
            decision = "quarantined_low_gdi"

        # Filename: gene_<id>__from_<node>.json
        short_id = asset.get("id", asset_id[:16]).replace("/", "_")
        fname = f"{short_id}__from_{source_node.replace(':', '_')}.json"
        out = self.root / sub / fname

        # CRDT: check imported/ for existing same asset_id before write
        if sub == "imported":
            existing = self._scan_conflicts().get(asset_id, [])
            if existing:
                # LWW among existing files only (new file not written yet)
                winner = self._apply_lww(asset_id, existing)
                winner_mtime = winner.stat().st_mtime if winner.exists() else 0
                new_mtime = time.time()  # this write is newer by definition
                if new_mtime > winner_mtime:
                    # New file wins — move existing winner to conflicts/, write new
                    ts = now_iso().replace(":", "-")
                    conflict_dir = self._conflict_dir()
                    conflict_dir.mkdir(parents=True, exist_ok=True)
                    loser_name = winner.stem + f"__conflict_{ts}"
                    shutil.move(winner, conflict_dir /
                                  (loser_name + winner.suffix))
                    self.audit_log({
                        "ts": now_iso(),
                        "action": "conflict_lww_existing_loser",
                        "asset_id": asset_id,
                        "winner": str(out),
                        "loser": str(winner),
                        "resolution": "last_write_wins",
                    })
                else:
                    # Existing winner is newer — new file is a loser
                    ts = now_iso().replace(":", "-")
                    loser_name = out.stem + f"__conflict_{ts}"
                    # Don't write out at all — log and return
                    self.audit_log({
                        "ts": now_iso(),
                        "action": "conflict_lww_new_loser",
                        "asset_id": asset_id,
                        "new_file": str(out),
                        "winner": str(winner),
                        "resolution": "last_write_wins",
                    })
                    return "conflict_lww_loser", str(out)

        json.dump(asset, open(out, "w"), ensure_ascii=False, indent=2)

        self.audit_log({
            "ts": now_iso(),
            "action": decision,
            "asset_id": asset_id,
            "source_node": source_node,
            "gdi_score": gdi,
            "behavior_feedback_verified": has_feedback,
            "stored_at": str(out),
        })
        return decision, str(out)

    def list_local(self) -> list[dict]:
        return [
            json.load(open(p)) for p in (self.root / "local").glob("*.json")
        ]


class A2AHandler(BaseHTTPRequestHandler):
    """HTTP handler for A2A server."""

    def log_message(self, fmt, *args):
        pass  # silence default logging

    # ---- node discovery (v0.5 broadcast) ----
    def _handle_node_discovery(self):
        """Respond with this node's identity + known peers.

        GET /api/v1/a2a/nodes
        Returns:
          {
            "node_id": ...,
            "protocol_version": "1.0",
            "peers": ["http://127.0.0.1:9878", ...],
            "gene_pool": "...",
            "stats": {"local": N, "imported": M, "quarantined": K}
          }
        """
        pool: GenePool = self.server.gene_pool
        peer_file = pool.root / "known_peers.json"
        peers = []
        if peer_file.exists():
            try:
                peers = json.load(open(peer_file))
            except (json.JSONDecodeError, OSError):
                peers = []
        stats = {
            "local": len(list((pool.root / "local").glob("*.json"))),
            "imported": len(list((pool.root / "imported").glob("*.json"))),
            "quarantined": len(list((pool.root / "quarantined").glob("*.json"))),
        }
        self._send_json(200, {
            "node_id": get_node_id(),
            "protocol_version": PROTOCOL_VERSION,
            "peers": peers,
            "gene_pool": str(pool.root),
            "stats": stats,
        })

    def _handle_announce(self):
        """Accept a peer announce and persist to known_peers.json.

        POST /api/v1/a2a/announce
        Body: {"peer_url": "http://...", "node_id": "..."}
        """
        env = self._read_body()
        peer_url = env.get("peer_url", "")
        if not peer_url:
            self._send_json(400, {"error": "missing peer_url"})
            return
        pool: GenePool = self.server.gene_pool
        peer_file = pool.root / "known_peers.json"
        peers = []
        if peer_file.exists():
            try:
                peers = json.load(open(peer_file))
            except (json.JSONDecodeError, OSError):
                peers = []
        if peer_url not in peers:
            peers.append(peer_url)
            json.dump(peers, open(peer_file, "w"), ensure_ascii=False, indent=2)
        self._send_json(200, {"ack": True, "known_peers": peers})

    # ---- original handlers ----
    def _send_json(self, code: int, body: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/v1/a2a/health":
            self._send_json(200, {"status": "ok", "node_id": get_node_id()})
        elif self.path == "/api/v1/a2a/node/info":
            self._send_json(200, {
                "node_id": get_node_id(),
                "protocol_version": PROTOCOL_VERSION,
                "gene_pool": str(self.server.gene_pool.root),
            })
        elif self.path == "/api/v1/a2a/nodes":
            self._handle_node_discovery()
        else:
            self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/api/v1/a2a/publish":
            self._handle_publish()
        elif self.path == "/api/v1/a2a/request":
            self._handle_request()
        elif self.path == "/api/v1/a2a/announce":
            self._handle_announce()
        else:
            self._send_json(404, {"error": "not_found"})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    def _handle_publish(self):
        env = self._read_body()
        sender = env.get("sender_node_id", "?")
        intent = env.get("intent", "?")
        asset_type = env.get("asset_type", "?")
        payload = env.get("payload", {})
        signature = env.get("signature", "")
        behavior_feedback_proof = env.get("behavior_feedback_proof")

        # Validate intent
        if intent != "publish":
            self._send_json(400, {"error": "intent_must_be_publish", "got": intent})
            return

        # P0-1 fix: actually verify the signature.
        # v0.2: shared/trusted mode (HMAC over shared secret) — see get_node_secret().
        # v0.3 should switch to per-node keypair + peer public-key lookup.
        if not signature:
            self._send_json(401, {"error": "missing_signature", "sender": sender})
            return
        try:
            verify_ok = verify_signature(payload, signature, get_node_secret())
        except RuntimeError as e:
            # get_node_secret() raised because shared secret is not configured.
            self._send_json(503, {"error": "server_misconfigured", "detail": str(e)})
            return
        if not verify_ok:
            self._send_json(401, {"error": "signature_invalid", "sender": sender})
            return

        # Validate asset_id
        computed = compute_asset_id(payload)
        if computed != payload.get("asset_id"):
            self._send_json(400, {"error": "asset_id_mismatch", "computed": computed})
            return

        # Accept asset (passes proof for behavior_feedback verification)
        # peer_secret is the recipient node's OWN secret for v0.2 (shared/trusted mode);
        # in v0.3 use peer public key lookup.
        decision, stored_at = self.server.gene_pool.accept(
            payload, sender,
            behavior_feedback_proof=behavior_feedback_proof,
            peer_secret=get_node_secret(),
        )
        self._send_json(200, {
            "ack": True,
            "decision": decision,
            "stored_at": stored_at,
            "recipient_node_id": get_node_id(),
        })

    def _handle_request(self):
        env = self._read_body()
        requested_id = env.get("asset_id", "?")
        intent = env.get("intent", "?")
        if intent != "request":
            self._send_json(400, {"error": "intent_must_be_request"})
            return
        # Look up local asset
        for p in (self.server.gene_pool.root / "local").glob("*.json"):
            asset = json.load(open(p))
            if asset.get("asset_id") == requested_id:
                self._send_json(200, {
                    "ack": True,
                    "intent": "ack",
                    "payload": asset,
                })
                return
        self._send_json(404, {"error": "not_found_locally"})


def make_server(host: str = "127.0.0.1", port: int | None = None, pool_dir: Path | None = None):
    port = port or int(os.environ.get("A2A_PORT", DEFAULT_PORT))
    server = HTTPServer((host, port), A2AHandler)
    server.gene_pool = GenePool(root=pool_dir)
    return server


def main():
    """Run the A2A server (CLI entry)."""
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--pool-dir", type=Path, default=None)
    args = p.parse_args()

    server = make_server(args.host, args.port, args.pool_dir)
    print(
        f"A2A server listening on {args.host}:{server.server_port} "
        f"(node_id={get_node_id()}, pool={server.gene_pool.root})"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.server_close()


if __name__ == "__main__":
    main()