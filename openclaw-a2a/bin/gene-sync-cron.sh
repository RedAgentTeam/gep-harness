#!/bin/bash
# Gene Sync cron wrapper (stage 4.2)
# Usage in crontab:
#   0 */6 * * * /data/disk/gep-harness/openclaw-a2a/bin/gene-sync-cron.sh

set -e
LOG="/var/log/openclaw-gene-sync.log"
PEERS="${A2A_PEERS:-http://127.0.0.1:9877}"

echo "[$(date -Iseconds)] starting gene sync to peers: $PEERS" >> "$LOG"

# Loop over space-separated peers
for peer in $PEERS; do
  python3 /data/disk/gep-harness/openclaw-a2a/src/gene_sync.py \
    --peer "$peer" \
    --pool-dir "${A2A_GENE_POOL_DIR:-/root/.openclaw/gene-pool/}" \
    --min-gdi 0.7 \
    --timeout 10 2>&1 | tee -a "$LOG"
done

echo "[$(date -Iseconds)] gene sync done" >> "$LOG"
