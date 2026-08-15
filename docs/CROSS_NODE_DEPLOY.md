# Cross-Node A2A Protocol — gep-harness

> **Date:** 2026-08-15
> **Status:** Protocol spec verified on local (157/157 bidirectional); cross-node production deployment NOT started.

## Overview

`gep-harness` supports distributed evolution across multiple nodes via the A2A (Agent-to-Agent) protocol. This document specifies the protocol, message format, and signature scheme.

**Tested on:** local only (two mock_peer instances).
**Production deployment:** pending (requires operator confirmation).

## Architecture

```
┌─────────────┐         ┌─────────────┐
│  Node A     │  ←→     │  Node B     │
│  mock_peer  │  A2A    │  mock_peer  │
│  :19891     │         │  :19890     │
└─────────────┘         └─────────────┘
       │                       │
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│ plan/genes/ │         │ plan/genes/ │
│ plan/events/│         │ plan/events/│
└─────────────┘         └─────────────┘
```

Each node runs `mock_peer.py` listening on a port. Genes are wrapped in A2A envelopes with ed25519 signatures.

## Message Format

```json
{
  "type": "A2A_envelope",
  "schema_version": "1.12.1",
  "sender": {
    "handle": "devagent",
    "evox_install_id": "openclaw-devagent-001",
    "pubkey": "<ed25519 base64>"
  },
  "payload": {
    "type": "Gene",
    "asset_id": "sha256:...",
    "data": { ... }
  },
  "signature": "<ed25519 signature of canonicalize(payload)>",
  "behavior_feedback_proof": {
    "previous_asset_id": "sha256:...",
    "diff_summary": "..."
  },
  "ts": "2026-08-15T13:00:00+08:00"
}
```

## Signature Scheme

- **Algorithm:** ed25519
- **Canonicalize:** exclude `signature` field, sort keys lexicographically
- **Hash:** sha256 of canonical JSON
- **Sign:** ed25519 sign(sha256_digest)
- **Verify:** recompute canonicalize + hash + verify(recovered_pubkey, sig)

## Bidirectional Sync Protocol

1. Node A sends envelope to Node B's `:19890`.
2. Node B verifies signature + checks asset_id not seen before.
3. Node B emits ack back to Node A's `:19891`.
4. Node A logs accept/reject count.

## Test Results (local, 2026-08-15 01:00)

| Test | Result |
|------|--------|
| A→B send 19891 → B receive | sent=157 accepted=157 rejected=0 |
| B→A send 19890 → A receive | sent=157 accepted=157 rejected=0 |
| pytest test_mock_peer.py | 3/3 passed |

## Production Deployment Steps (PENDING OPERATOR APPROVAL)

⚠️ **DO NOT execute without explicit confirmation.** 美机 (<美机生产 IP>) 任何变更必须先问"在哪台机器做"。

1. Operator specifies target node IP and SSH credentials.
2. Deploy `mock_peer.py` to target node.
3. Configure port forwarding (`19890`/`19891`).
4. Exchange public keys.
5. Verify bidirectional with `make test`.

## Security

- All envelopes are signed; rejected envelopes log to `audit_logs`.
- Replay protection via `previous_asset_id` + monotonic ts.
- asset_id uniqueness enforced via sha256 canonicalize.

## See Also

- `openclaw-a2a/src/mock_peer.py` — mock implementation
- `openclaw-a2a/tests/test_mock_peer.py` — 3 pytest tests
- `gep-sdk-js` — official JS SDK reference