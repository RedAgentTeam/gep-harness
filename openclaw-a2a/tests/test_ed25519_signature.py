"""Regression tests for P1-2: A2A ed25519 signature support.

The legacy HMAC-SHA256 path must still work (backward-compat for already-deployed
peers). The new ed25519 path must round-trip sign+verify, reject tampered payloads,
and reject mismatched public keys.

5 pytest:
  1. ed25519 sign + verify roundtrip
  2. ed25519 verify rejects tampered payload
  3. ed25519 verify rejects mismatched public key
  4. HMAC backward-compat still works
  5. Cross-algorithm: ed25519-signed envelope rejected by HMAC-only verify
"""
import base64
import importlib
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))

import a2a_protocol  # noqa: E402
from a2a_protocol import sign_message, verify_signature, canonicalize  # noqa: E402


# Skip the whole module if ed25519 backend is not available
pytestmark = pytest.mark.skipif(
    not a2a_protocol._ED25519_AVAILABLE,
    reason="cryptography package not installed; ed25519 backend disabled",
)


@pytest.fixture
def ed25519_keypair():
    """Generate a fresh ed25519 keypair for testing."""
    from cryptography.hazmat.primitives import serialization
    priv = a2a_protocol._ed25519.Ed25519PrivateKey.generate()
    raw_priv = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return raw_priv, raw_pub


def test_ed25519_sign_verify_roundtrip(ed25519_keypair):
    """ed25519 sign → verify roundtrip succeeds."""
    priv, pub = ed25519_keypair
    payload = {"hello": "world", "n": 42, "list": [1, 2, 3]}
    sig = sign_message(payload, secret=priv, algorithm="ed25519")
    assert sig.startswith("ed25519:"), f"signature should be ed25519-prefixed, got {sig[:20]}"
    # verify with matching public key
    assert verify_signature(payload, sig, secret=pub)


def test_ed25519_verify_rejects_tampered_payload(ed25519_keypair):
    """ed25519 verify must fail if payload was modified after signing."""
    priv, pub = ed25519_keypair
    payload = {"hello": "world", "n": 42}
    sig = sign_message(payload, secret=priv, algorithm="ed25519")
    tampered = {"hello": "WORLD", "n": 42}  # value changed
    assert not verify_signature(tampered, sig, secret=pub)


def test_ed25519_verify_rejects_mismatched_public_key(ed25519_keypair):
    """ed25519 verify must fail if the public key doesn't match the signing key."""
    priv, _ = ed25519_keypair
    payload = {"x": 1}
    sig = sign_message(payload, secret=priv, algorithm="ed25519")

    # Different keypair
    from cryptography.hazmat.primitives import serialization
    other_priv = a2a_protocol._ed25519.Ed25519PrivateKey.generate()
    other_pub = other_priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    assert not verify_signature(payload, sig, secret=other_pub)


def test_hmac_backward_compat_still_works():
    """Legacy HMAC-SHA256 path must still work (P0-1 tests already cover this,
    but we re-assert here to make the backward-compat contract explicit)."""
    payload = {"k": "v"}
    sig = sign_message(payload, secret="legacy-shared-secret", algorithm="hmac-sha256")
    assert sig.startswith("sha256:")
    assert verify_signature(payload, sig, secret="legacy-shared-secret")


def test_cross_algorithm_rejection(ed25519_keypair):
    """An ed25519-signed envelope presented as HMAC must not pass HMAC verify.

    This is the security property: the algorithm prefix disambiguates, so an
    attacker can't downgrade ed25519→HMAC and forge a valid HMAC for the same
    payload (HMAC and ed25519 produce completely different signatures).
    """
    priv, pub = ed25519_keypair
    payload = {"k": "v"}
    sig_ed = sign_message(payload, secret=priv, algorithm="ed25519")
    # Trying to verify the ed25519 sig with HMAC must fail (no sha256: prefix match)
    assert not verify_signature(payload, sig_ed, secret="any-shared-secret")