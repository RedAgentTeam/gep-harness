#!/bin/bash
# A2A server startup script
# Usage: A2A_SHARED_SECRET=<secret> ./gene-sync-start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GEP_HARNESS="${GEP_HARNESS:-/data/disk/gep-harness}"
A2A_SHARED_SECRET="${A2A_SHARED_SECRET:-dev-shared-secret-do-not-use-in-prod}"
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
