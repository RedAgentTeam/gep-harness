#!/bin/bash
# A2A server startup script
# Usage: A2A_SHARED_SECRET=<secret> [GEP_HARNESS=/path/to/repo] ./gene-sync-start.sh
#
# P0-2 fix: A2A_SHARED_SECRET has NO default value; missing it is a fatal error.
# P0-4 fix: GEP_HARNESS defaults to this script's parent of parent (i.e. <repo>),
#           not /data/disk/gep-harness.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GEP_HARNESS="${GEP_HARNESS:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# P0-2: refuse to start without a real shared secret.
if [ -z "${A2A_SHARED_SECRET:-}" ]; then
  echo "FATAL: A2A_SHARED_SECRET is not set." >&2
  echo "       Refusing to start with a default/empty shared secret, which would" >&2
  echo "       make HMAC signatures trivially forgeable." >&2
  echo "       Set A2A_SHARED_SECRET=<random-string> in your env before starting." >&2
  exit 1
fi

A2A_GENE_POOL_DIR="${A2A_GENE_POOL_DIR:-$HOME/.openclaw/gene-pool}"
HOST="${A2A_HOST:-0.0.0.0}"
PORT="${A2A_PORT:-9877}"

echo "=== A2A server starting ==="
echo "  node_id: $(hostname)"
echo "  pool_dir: $A2A_GENE_POOL_DIR"
echo "  listen: $HOST:$PORT"
echo "  secret: ${A2A_SHARED_SECRET:0:8}..."

# Ensure GenePool directories exist
mkdir -p "$A2A_GENE_POOL_DIR"/{local,imported,quarantined,conflicts}

# Start A2A server (background)
cd "$SCRIPT_DIR"
exec python3 -m openclaw-a2a.src.a2a_protocol --host "$HOST" --port "$PORT" \
  -e A2A_SHARED_SECRET="$A2A_SHARED_SECRET" \
  -e A2A_GENE_POOL_DIR="$A2A_GENE_POOL_DIR" \
  2>&1