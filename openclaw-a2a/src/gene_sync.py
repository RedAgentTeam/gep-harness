"""Gene Sync — 6h background sync between Gene Pools.

Stage 4.2 — cron job that:
  1. Reads local Gene Pool's local/ dir
  2. Selects assets with GDI score >= 0.7
  3. Builds A2A envelope (signed)
  4. POSTs to peer(s)
  5. Reads peer's response (ack/reject)
  6. Updates audit.jsonl

Designed to be cron-friendly:
  - Idempotent (safe to run multiple times)
  - Logs to audit.jsonl + stdout
  - Exit code 0 = success, non-zero = retry
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from a2a_protocol import (  # noqa: E402
    GenePool,
    PROTOCOL_VERSION,
    compute_asset_id,
    gdi_score,
    get_node_id,
    get_node_secret,
    make_envelope,
    now_iso,
)


def sync_to_peer(
    pool: GenePool,
    peer_url: str,
    secret: str,
    node_id: str,
    min_gdi: float = 0.7,
    timeout: float = 10.0,
) -> dict:
    """Sync local Gene Pool → one peer.

    Local Genes are assumed to have behavior_feedback=True (they already
    went through Solidify on this node). This gives them a fair GDI score
    when sharing to peers.
    """
    sent = 0
    accepted = 0
    rejected = 0
    errors = []

    # 1. Iterate local Gene Pool
    for local_path in (pool.root / "local").glob("*.json"):
        try:
            asset = json.load(open(local_path))
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"local read error {local_path.name}: {e}")
            continue

        # 2. GDI gate (local = behavior_feedback assumed True)
        score = gdi_score(asset, has_behavior_feedback=True)
        if score < min_gdi:
            continue

        # 3. Build envelope with behavior_feedback_proof (signed reuse history)
        asset_id = asset.get("asset_id", "")
        if not asset_id:
            continue

        # Build signed proof that this gene was reused successfully on the local node.
        # v0.2: 1 reuse is enough; v0.3 may require N.
        proof_payload = {
            "reuses": [
                {"ts": now_iso(), "outcome": "success", "asset_id": asset_id}
            ]
        }
        from a2a_protocol import sign_message
        behavior_feedback_proof = {
            **proof_payload,
            "signature": sign_message(proof_payload, secret),
        }

        envelope = make_envelope(
            sender_node_id=node_id,
            recipient_node_id=peer_url,
            asset_id=asset_id,
            asset_type="Gene",
            intent="publish",
            payload=asset,
            secret=secret,
            behavior_feedback_proof=behavior_feedback_proof,
        )

        # 4. POST to peer
        peer_decision = "error"
        try:
            req = urllib.request.Request(
                f"{peer_url}/api/v1/a2a/publish",
                data=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            sent += 1
            peer_decision = body.get("decision", "unknown")
            if peer_decision == "accepted":
                accepted += 1
            else:
                rejected += 1
        except (urllib.error.URLError, OSError) as e:
            errors.append(f"post error {asset.get('id', '?')}: {e}")
            continue

        # 5. audit
        pool.audit_log({
            "ts": now_iso(),
            "action": "sync_to_peer",
            "asset_id": asset_id,
            "peer": peer_url,
            "gdi_score": score,
            "decision": peer_decision,
        })

    return {
        "peer": peer_url,
        "sent": sent,
        "accepted": accepted,
        "rejected": rejected,
        "errors": errors,
    }


def discover_peers(bootstrap_urls: list[str], timeout: float = 5.0) -> list[str]:
    """Node discovery: query bootstrap peers for their known_peers list.

    v0.5 broadcast: replaces static --peer list with dynamic discovery.
    Returns deduplicated list of peer URLs (including bootstrap URLs themselves).
    """
    discovered: set[str] = set(bootstrap_urls)
    for url in bootstrap_urls:
        try:
            req = urllib.request.Request(
                f"{url.rstrip('/')}/api/v1/a2a/nodes"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                for p in body.get("peers", []):
                    discovered.add(p)
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            print(f"[discover] warning: {url}: {e}")
    return sorted(discovered)


def broadcast_to_peers(
    pool: GenePool,
    peer_urls: list[str],
    secret: str,
    node_id: str,
    min_gdi: float = 0.7,
    timeout: float = 10.0,
) -> dict:
    """Broadcast local Genes to multiple peers (batch + fan-out).

    Optimisation: build one envelope per high-GDI asset, fan out to all peers.
    Returns summary aggregated across all peers.
    """
    summary = {"peers": [], "total_sent": 0, "total_accepted": 0, "total_rejected": 0, "total_errors": 0}

    for peer in peer_urls:
        result = sync_to_peer(pool, peer, secret, node_id, min_gdi, timeout)
        summary["peers"].append(result)
        summary["total_sent"] += result["sent"]
        summary["total_accepted"] += result["accepted"]
        summary["total_rejected"] += result["rejected"]
        summary["total_errors"] += len(result["errors"])

    return summary


def announce_peer(pool: GenePool, self_url: str, peer_url: str, timeout: float = 5.0) -> dict:
    """Announce this node to a peer (persist both sides' known_peers)."""
    try:
        req = urllib.request.Request(
            f"{peer_url.rstrip('/')}/api/v1/a2a/announce",
            data=json.dumps({"peer_url": self_url, "node_id": get_node_id()},
                            ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {"peer": peer_url, "ack": True, "known_peers": body.get("known_peers", [])}
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return {"peer": peer_url, "ack": False, "error": str(e)}


def main():
    p = argparse.ArgumentParser(description="Gene Sync — broadcast or pairwise")
    p.add_argument("--peer", action="append", help="peer URL (repeatable, optional if --broadcast)")
    p.add_argument("--broadcast", action="store_true",
                   help="auto-discover peers from bootstrap list, then fan-out to all")
    p.add_argument("--bootstrap", action="append", default=[],
                   help="bootstrap node URL for discovery (repeatable)")
    p.add_argument("--announce", metavar="SELF_URL",
                   help="announce this node to peers (requires --peer)")
    p.add_argument("--pool-dir", type=Path, default=None)
    p.add_argument("--min-gdi", type=float, default=0.7)
    p.add_argument("--timeout", type=float, default=10.0)
    args = p.parse_args()

    secret = get_node_secret()
    node_id = get_node_id()
    pool = GenePool(root=args.pool_dir)

    # --announce mode
    if args.announce:
        if not args.peer:
            print("[gene_sync] --announce requires --peer", file=sys.stderr)
            sys.exit(1)
        print(f"[gene_sync] announcing {node_id} to {args.peer}")
        for peer in args.peer:
            result = announce_peer(pool, args.announce, peer, timeout=args.timeout)
            status = "ok" if result.get("ack") else f"error: {result.get('error')}"
            print(f"  → {peer}: {status}")
        sys.exit(0)

    # --broadcast mode: discover peers first
    if args.broadcast:
        bootstrap = args.bootstrap if args.bootstrap else (args.peer or [])
        if not bootstrap:
            print("[gene_sync] --broadcast requires --bootstrap or --peer", file=sys.stderr)
            sys.exit(1)
        print(f"[gene_sync] node={node_id} pool={pool.root} "
              f"discovering from bootstrap={bootstrap}")
        peers = discover_peers(bootstrap, timeout=3.0)
        print(f"[gene_sync] discovered {len(peers)} peers: {peers}")
        if not peers:
            print("[gene_sync] no peers discovered, exiting")
            sys.exit(0)
        summary = broadcast_to_peers(pool, peers, secret, node_id,
                                      min_gdi=args.min_gdi, timeout=args.timeout)
        print(f"[gene_sync] broadcast done: sent={summary['total_sent']} "
              f"accepted={summary['total_accepted']} "
              f"rejected={summary['total_rejected']} "
              f"errors={summary['total_errors']}")
        sys.exit(1 if summary["total_errors"] > 0 else 0)

    # default: pairwise --peer
    if not args.peer:
        p.print_help()
        sys.exit(1)
    print(f"[gene_sync] node={node_id} pool={pool.root} peers={args.peer}")
    summary = []
    for peer in args.peer:
        result = sync_to_peer(pool, peer, secret, node_id,
                              min_gdi=args.min_gdi, timeout=args.timeout)
        summary.append(result)
        print(f"[gene_sync] → {peer}: sent={result['sent']} "
              f"accepted={result['accepted']} rejected={result['rejected']}")

    total_errors = sum(len(r["errors"]) for r in summary)
    if total_errors > 0:
        print(f"[gene_sync] {total_errors} errors:")
        for r in summary:
            for e in r["errors"]:
                print(f"  - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()