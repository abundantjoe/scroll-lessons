#!/bin/bash
# RULES G-GP part 6: read the threshold-8 and threshold-10 consensus surfaces, both ADMITTED by the declared
# geometry gate (0.00 transverse/cm2; p90 sag 5.05 and 5.24 um against the control's 9.93).
# Waits for G-OWN's read to finish first: G-OWN is the decisive experiment and the box has 4 cores.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
CKPT=$D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth
log(){ echo "[ggp6read $(date -u +%FT%TZ)] $*"; }
while [ ! -f $D/gates/gown/gown_result.json ]; do sleep 60; done
log "G-OWN read finished; reading part 6 and 6b"
for part in 6 6b; do
  pd=$D/patches/PHerc0826_cons_part${part}
  [ -d "$pd" ] || { log "no part $part directory"; continue; }
  for s in "$pd"/auto_*; do
    [ -d "$s" ] || continue
    [ -f "$s/read_ink9um_seed42_plain/.read_complete" ] && { log "$(basename "$s") already read"; continue; }
    log "reading $(basename "$s")"
    HERCULES_INFER_LOCK=$D/logs/infer_prod.lock nice -n 12 $R/.venv/bin/python $R/scripts/run_patch_dir.py "$pd" \
      --scroll PHerc0826 --vol 20250821151701 --ckpt "$CKPT" --tag ink9um_seed42+plain --no-tta \
      --only "$(basename "$s")" --ledger $R/LEDGER.md --records $R/records/throughput.jsonl \
      --delete-renders </dev/null 2>&1 | tail -4
  done
done
log "part 6 reads complete"
