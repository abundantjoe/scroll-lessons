#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-E2E-3 item 1: band-observability survey, one lane of N. usage: lane_obs.sh <L> <N>   (resumable; DONE marker logs/unr/obs/lane<L>.DONE; the sibling polls until DONE)
set -uo pipefail; L=$1; N=${2:-24}; REPO=/home/user/dominion; cd $REPO; PY=/opt/hv/bin/python; OUT=logs/unr/obs; mkdir -p $OUT /dev/shm/e2e; BR=claude/gifted-bell-gavnl5-fl4t
L4=/dev/shm/e2e/ct_L4_PHerc0268.npy; CFG=configs/pipeline/PHerc0268.json; PRM=configs/pipeline/ord3_params.json
log(){ echo "[$(date -u +%FT%TZ)] lane $L $*" | tee -a $OUT/lane$L.log; }
[ -f $L4 ] || { log "fetch level 4"; $PY tools/umb/fetch_zarr.py $($PY -c "import json;print(json.load(open('$CFG'))['ct_l4'])") $L4 > $OUT/lane${L}_fetchL4.log 2>&1 || { log "level-4 fetch failed"; exit 1; }; }
YS=$($PY -c "import numpy as np; ys=np.linspace(2500,10000,72).astype(int); print(' '.join(str(y) for y in ys[$L::$N]))")
push(){ git add $OUT >/dev/null 2>&1; git commit -q -m "obs survey lane $L: $1

Provenance: Project HERCULES | [id removed]" >/dev/null 2>&1 || true; for i in 1 2 3 4 5; do git pull -q --rebase origin $BR >/dev/null 2>&1; git push -q origin HEAD:$BR >/dev/null 2>&1 && return 0; sleep $((RANDOM % 20 + 5)); done; log "push failed"; }
for y in $YS; do
  if ls $OUT/obs_y${y}_w2.json >/dev/null 2>&1; then log "y $y exists"; continue; fi
  log "y $y start"; OMP_NUM_THREADS=3 $PY tools/unr/obs_survey.py $PRM $CFG $OUT --y $y --l4 $L4 >> $OUT/lane$L.log 2>&1 || log "y $y failed (recorded)"; push "y $y"
done
touch $OUT/lane$L.DONE; push "DONE"; log "DONE"
