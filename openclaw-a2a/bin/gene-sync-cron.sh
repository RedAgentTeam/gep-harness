#!/bin/bash
# Gene Sync cron wrapper (stage 4.2)
# Usage in crontab (set GEP_HARNESS to your repo root):
#   0 */6 * * * GEP_HARNESS=/path/to/gep-harness /path/to/gep-harness/openclaw-a2a/bin/gene-sync-cron.sh
#
# P0-4 fix: path resolved from $GEP_HARNESS env var, falling back to parent
# of this script's directory (so a symlink or relative deploy still works).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEP_HARNESS="${GEP_HARNESS:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
LOG="/var/log/openclaw-gene-sync.log"
PEERS="${A2A_PEERS:-http://127.0.0.1:9877}"

echo "[$(date -Iseconds)] starting gene sync (GEP_HARNESS=$GEP_HARNESS) to peers: $PEERS" >> "$LOG"

# Loop over space-separated peers
for peer in $PEERS; do
  python3 "$GEP_HARNESS/openclaw-a2a/src/gene_sync.py" \
    --peer "$peer" \
    --pool-dir "${A2A_GENE_POOL_DIR:-/root/.openclaw/gene-pool/}" \
    --min-gdi 0.7 \
    --timeout 10 2>&1 | tee -a "$LOG"
done

echo "[$(date -Iseconds)] gene sync done" >> "$LOG"