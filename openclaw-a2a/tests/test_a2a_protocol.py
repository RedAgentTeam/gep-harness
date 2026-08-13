"""Tests for A2A Protocol v0.1.0 (stage 4.1).

4 pytest:
  1. sign + verify roundtrip
  2. make_envelope + payload validation
  3. gdi_score calculation
  4. GenePool accept (accept + quarantine paths)
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))

from a2a_protocol import (  # noqa: E402
    canonicalize,
    compute_asset_id,
    make_envelope,
    sign_message,
    verify_signature,
    gdi_score,
    GenePool,
    get_node_id,
)


def test_sign_verify_roundtrip():
    """HMAC sign + verify roundtrip"""
    payload = {"hello": "world", "n": 42, "list": [1, 2, 3]}
    sig = sign_message(payload, secret="my-secret")
    assert sig.startswith("sha256:")
    assert verify_signature(payload, sig, secret="my-secret")
    # tampered payload fails
    tampered = {"hello": "WORLD", "n": 42, "list": [1, 2, 3]}
    assert not verify_signature(tampered, sig, secret="my-secret")
    # wrong secret fails
    assert not verify_signature(payload, sig, secret="wrong-secret")


def test_make_envelope_validation():
    """make_envelope enforces asset_type and intent enums"""
    import pytest as P
    payload = {"type": "Gene", "schema_version": "1.12.1", "id": "g1",
               "asset_id": "sha256:0" * 16}
    # invalid asset_type
    try:
        make_envelope("node:A", "node:B", "sha256:x", "InvalidType", "publish",
                      payload, "secret")
        assert False, "should have raised"
    except ValueError as e:
        assert "asset_type" in str(e)
    # invalid intent
    try:
        make_envelope("node:A", "node:B", "sha256:x", "Gene", "bogus",
                      payload, "secret")
        assert False, "should have raised"
    except ValueError as e:
        assert "intent" in str(e)
    # valid
    env = make_envelope("node:A", "node:B", payload["asset_id"], "Gene",
                       "publish", payload, "secret")
    assert env["sender_node_id"] == "node:A"
    assert env["recipient_node_id"] == "node:B"
    assert env["intent"] == "publish"
    assert env["signature"].startswith("sha256:")


def test_gdi_score_calculation():
    """GDI v2 score must reflect 3 dimensions"""
    # Full credit asset
    good = {
        "type": "Gene", "schema_version": "1.12.1",
        "id": "g_good", "category": "optimize",
        "signals_match": ["x", "y", "z"],
        "strategy": ["step1", "step2"],
        "summary": "This is a sufficiently long summary with enough info",
        "asset_id": "sha256:" + "0" * 64,
        "cross_library_evidence": ["a", "b", "c", "d", "e"],
    }
    good["asset_id"] = compute_asset_id(good)
    score_with_feedback = gdi_score(good, has_behavior_feedback=True)
    score_no_feedback = gdi_score(good, has_behavior_feedback=False)
    assert score_with_feedback >= 0.9, f"good+feedback expected high, got {score_with_feedback}"
    assert score_no_feedback >= 0.5, f"good no-feedback mid, got {score_no_feedback}"
    assert score_with_feedback > score_no_feedback

    # Sparse asset
    sparse = {
        "type": "Gene", "schema_version": "1.12.1",
        "id": "g_sparse", "category": "optimize",
        "signals_match": ["x"],
        "strategy": ["one"],
        "summary": "short",
        "asset_id": "sha256:" + "1" * 64,
    }
    sparse["asset_id"] = compute_asset_id(sparse)
    sparse_score = gdi_score(sparse)
    assert sparse_score < 0.5, f"sparse expected low, got {sparse_score}"


def test_gene_pool_accept_and_quarantine():
    """Pool accepts high-GDI assets, quarantines low-GDI"""
    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))

        # High-GDI asset (5 evidence, full signals, long summary)
        good = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_high", "category": "optimize",
            "signals_match": ["x", "y", "z"],
            "strategy": ["step1", "step2", "step3"],
            "summary": "A comprehensive summary covering all aspects of the strategy with detail",
            "asset_id": "sha256:" + "0" * 64,
            "cross_library_evidence": ["a", "b", "c", "d", "e"],
        }
        good["asset_id"] = compute_asset_id(good)
        # v0.2 GDI design: threshold=0.7 + verified behavior_feedback_proof
        # Build a signed proof of reuse outcome=success
        from a2a_protocol import sign_message, verify_behavior_feedback_proof
        proof_payload = {"reuses": [{"ts": "2026-08-14T01:00:00+08:00", "outcome": "success"}]}
        proof = {
            **proof_payload,
            "signature": sign_message(proof_payload, "***"),
        }
        decision, path = pool.accept(
            good, source_node="node:peer1",
            behavior_feedback_proof=proof,
            peer_secret="***",
        )
        assert decision == "accepted", f"expected accepted, got {decision}"
        assert "imported" in path
        assert Path(path).exists()

        # Low-GDI asset (1 evidence, 1 signal)
        bad = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_low", "category": "explore",
            "signals_match": ["x"],
            "strategy": ["one"],
            "summary": "short",
            "asset_id": "sha256:" + "2" * 64,
        }
        bad["asset_id"] = compute_asset_id(bad)
        decision2, path2 = pool.accept(bad, source_node="node:peer2")
        assert decision2 == "quarantined_low_gdi"
        assert "quarantined" in path2

        # audit.jsonl 应有 2 条 (accept + quarantine)
        audit_lines = (Path(tmp) / "audit.jsonl").read_text().strip().splitlines()
        assert len(audit_lines) == 2
        audit1 = json.loads(audit_lines[0])
        assert audit1["action"] == "accepted"
        assert audit1["gdi_score"] >= 0.7
        assert audit1["behavior_feedback_verified"] is True
        audit2 = json.loads(audit_lines[1])
        assert audit2["action"] == "quarantined_low_gdi"


if __name__ == "__main__":
    test_sign_verify_roundtrip()
    print("✅ test_sign_verify_roundtrip")
    test_make_envelope_validation()
    print("✅ test_make_envelope_validation")
    test_gdi_score_calculation()
    print("✅ test_gdi_score_calculation")
    test_gene_pool_accept_and_quarantine()
    print("✅ test_gene_pool_accept_and_quarantine")
    print("\n=== all 4 tests passed ===")

def test_gene_pool_crdt_lww_conflict():
    """CRDT last-write-wins: duplicate asset_id → winner kept, loser → conflicts/"""
    import time as _time
    with tempfile.TemporaryDirectory() as tmp:
        pool = GenePool(root=Path(tmp))

        base = {
            "type": "Gene", "schema_version": "1.12.1",
            "id": "g_dup", "category": "optimize",
            "signals_match": ["a", "b"],
            "strategy": ["s1", "s2"],
            "summary": "A long enough summary for GDI scoring to pass threshold with feedback",
            "asset_id": "sha256:" + "f" * 64,
            "cross_library_evidence": ["a", "b", "c", "d", "e"],
        }
        base["asset_id"] = compute_asset_id(base)

        # Build proof for behavior_feedback
        from a2a_protocol import sign_message
        proof_payload = {"reuses": [{"ts": "2026-01-01T00:00:00+08:00", "outcome": "success"}]}
        proof = {**proof_payload, "signature": sign_message(proof_payload, "test-secret")}

        # First accept (from node:peer1)
        d1, p1 = pool.accept(base, source_node="node:peer1",
                              behavior_feedback_proof=proof, peer_secret="test-secret")
        assert d1 == "accepted"
        assert "imported" in p1

        # Second accept same asset_id from node:peer2 (same content, different node)
        # CRDT test: simulate two nodes importing the same Gene (same asset_id)
        import time as _t
        _t.sleep(0.01)
        dup = {**base, "id": "g_dup_from_peer2"}
        dup["asset_id"] = base["asset_id"]  # same content → same asset_id
        d2, p2 = pool.accept(dup, source_node="node:peer2",
                              behavior_feedback_proof=proof, peer_secret="test-secret")
        # d2 should be accepted OR conflict_lww_loser
        assert d2 in ("accepted", "conflict_lww_loser"), f"unexpected: {d2}"

        # conflicts/ dir must exist and contain at least one file
        conflicts_dir = pool._conflict_dir()
        conflict_files = list(conflicts_dir.glob("*.json"))
        assert len(conflict_files) >= 1, "expected ≥1 conflict file"

        # audit.jsonl must log the conflict
        audit_lines = (Path(tmp) / "audit.jsonl").read_text().strip().splitlines()
        conflict_actions = [json.loads(l) for l in audit_lines
                            if "conflict" in json.loads(l).get("action", "")]
        assert len(conflict_actions) >= 1, "expected conflict audit entry"
