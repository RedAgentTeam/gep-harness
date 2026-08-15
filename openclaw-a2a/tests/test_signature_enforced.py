"""Regression tests for P0-1 (signature enforced) and P0-2 (no default secret).

  5 pytest:
  1. get_node_secret() raises when env is not configured (P0-2)
  2. _handle_publish rejects envelope with no signature (P0-1)
  3. _handle_publish rejects envelope with invalid signature (P0-1)
  4. _handle_publish accepts envelope with valid signature (P0-1, end-to-end)
  5. _handle_publish returns 503 when server has no shared secret (P0-2 end-to-end)
"""
import importlib
import json
import os
import sys
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))

import a2a_protocol  # noqa: E402
from a2a_protocol import (  # noqa: E402
    get_node_secret,
    get_node_id,
    sign_message,
    verify_signature,
    compute_asset_id,
    make_envelope,
    PROTOCOL_VERSION,
    ASSET_TYPES,
)


# ----- P0-2: get_node_secret() must NOT silently fall back to a public string -----

def test_p02_get_node_secret_raises_when_unconfigured(monkeypatch):
    """P0-2 fix: missing A2A_SHARED_SECRET raises RuntimeError, no silent fallback."""
    monkeypatch.delenv("A2A_SHARED_SECRET", raising=False)
    monkeypatch.delenv("A2A_NODE_SECRET", raising=False)
    try:
        get_node_secret()
    except RuntimeError as e:
        assert "A2A_SHARED_SECRET" in str(e) or "A2A_NODE_SECRET" in str(e), (
            f"error message should explain which env var is needed; got: {e}"
        )
        assert "dev-shared-secret" not in str(e), (
            "error message must NOT mention the old default secret string"
        )
        return
    raise AssertionError(
        "get_node_secret() must raise when A2A_SHARED_SECRET is unset "
        "(P0-2 fix); instead it returned a value silently"
    )


def test_p02_get_node_secret_returns_env_value(monkeypatch):
    """When env is configured, get_node_secret() returns that value (no surprise)."""
    monkeypatch.setenv("A2A_SHARED_SECRET", "test-secret-from-env-xyz")
    monkeypatch.delenv("A2A_NODE_SECRET", raising=False)
    assert get_node_secret() == "test-secret-from-env-xyz"


# ----- P0-1: _handle_publish must actually verify the signature -----

def _build_payload():
    """Build a minimal Gene-like payload that GEP-strict would accept."""
    return {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": "test_gene_p01",
        "signals_match": ["test"],
        "category": "repair",
        "strategy": "do_something",
        "preconditions": {},
        "constraints": {"max_files": 5},
        "validation": {"pytest": "scripts/tests/test_canonicalize_unified.py"},
    }


def _build_envelope(sender, intent, payload, secret):
    """Use make_envelope (real signing) — that's the path real callers go through."""
    return make_envelope(
        sender_node_id=sender,
        recipient_node_id="node:other",
        asset_id=payload["asset_id"],
        asset_type="Gene",
        intent=intent,
        payload=payload,
        secret=secret,
    )


class _FakeServer:
    """Minimal stand-in for the HTTPServer instance _handle_publish expects."""
    def __init__(self, gene_pool):
        self.gene_pool = gene_pool


def test_p01_handle_publish_rejects_missing_signature(monkeypatch, tmp_path):
    """Envelopes with no signature must return 401, not silently accept."""
    monkeypatch.setenv("A2A_SHARED_SECRET", "real-test-secret-abc")
    # Re-import so get_node_secret picks up the env var
    importlib.reload(a2a_protocol)

    from a2a_protocol import GenePool, A2AHandler  # noqa: E402
    payload = _build_payload()
    payload["asset_id"] = compute_asset_id(payload)

    # Build envelope with REAL signature, then strip it to simulate attacker
    env = _build_envelope("node:attacker", "publish", payload, "real-test-secret-abc")
    env["signature"] = ""  # attacker drops signature

    handler = A2AHandler.__new__(A2AHandler)
    captured = {}
    handler._send_json = lambda code, body: captured.setdefault("responses", []).append((code, body))
    handler._read_body = lambda: env
    handler.server = _FakeServer(GenePool(root=tmp_path / "pool"))

    handler._handle_publish()

    last_code, last_body = captured["responses"][-1]
    assert last_code == 401, f"missing signature must be 401, got {last_code} {last_body}"
    assert last_body.get("error") == "missing_signature"


def test_p01_handle_publish_rejects_invalid_signature(monkeypatch, tmp_path):
    """Envelopes with a wrong signature must return 401."""
    monkeypatch.setenv("A2A_SHARED_SECRET", "real-test-secret-abc")
    importlib.reload(a2a_protocol)

    from a2a_protocol import GenePool, A2AHandler  # noqa: E402
    payload = _build_payload()
    payload["asset_id"] = compute_asset_id(payload)

    # Sign with wrong secret
    env = _build_envelope("node:attacker", "publish", payload, "WRONG-secret-from-attacker")
    assert env["signature"] != ""

    handler = A2AHandler.__new__(A2AHandler)
    captured = {}
    handler._send_json = lambda code, body: captured.setdefault("responses", []).append((code, body))
    handler._read_body = lambda: env
    handler.server = _FakeServer(GenePool(root=tmp_path / "pool"))

    handler._handle_publish()

    last_code, last_body = captured["responses"][-1]
    assert last_code == 401, f"invalid signature must be 401, got {last_code} {last_body}"
    assert last_body.get("error") == "signature_invalid"


def test_p01_handle_publish_accepts_valid_signature(monkeypatch, tmp_path):
    """End-to-end: correctly signed envelope is accepted."""
    monkeypatch.setenv("A2A_SHARED_SECRET", "real-test-secret-abc")
    importlib.reload(a2a_protocol)

    from a2a_protocol import GenePool, A2AHandler  # noqa: E402
    payload = _build_payload()
    payload["asset_id"] = compute_asset_id(payload)

    env = _build_envelope("node:sender", "publish", payload, "real-test-secret-abc")

    handler = A2AHandler.__new__(A2AHandler)
    captured = {}
    handler._send_json = lambda code, body: captured.setdefault("responses", []).append((code, body))
    handler._read_body = lambda: env
    handler.server = _FakeServer(GenePool(root=tmp_path / "pool"))

    handler._handle_publish()

    last_code, last_body = captured["responses"][-1]
    assert last_code == 200, f"valid signed envelope must be 200, got {last_code} {last_body}"
    assert last_body.get("ack") is True


def test_p01_handle_publish_503_when_server_unconfigured(monkeypatch, tmp_path):
    """If server itself has no shared secret, return 503 (not crash, not accept)."""
    monkeypatch.delenv("A2A_SHARED_SECRET", raising=False)
    monkeypatch.delenv("A2A_NODE_SECRET", raising=False)
    importlib.reload(a2a_protocol)

    from a2a_protocol import GenePool, A2AHandler  # noqa: E402
    payload = _build_payload()
    payload["asset_id"] = compute_asset_id(payload)

    # Use a secret value just for signing — server side will fail to load one.
    env = _build_envelope("node:sender", "publish", payload, "any-secret")

    handler = A2AHandler.__new__(A2AHandler)
    captured = {}
    handler._send_json = lambda code, body: captured.setdefault("responses", []).append((code, body))
    handler._read_body = lambda: env
    handler.server = _FakeServer(GenePool(root=tmp_path / "pool"))

    handler._handle_publish()

    last_code, last_body = captured["responses"][-1]
    assert last_code == 503, f"unconfigured server must be 503, got {last_code} {last_body}"
    assert last_body.get("error") == "server_misconfigured"