#!/usr/bin/env bash
# run.sh: ONE command for the PHerc0343 positive-control strip experiment (the d = +1 arms except the original run's exploratory X13) and its scoring.
#   ERWIN=<pherc343-first-letters @ e8370f1> PYH=... PYI=... CKPT=... VC_BIN=... bash scripts/control_strips/run.sh
# Env: OUT (default $BI_ROOT/out), BI_ROOT (default $PWD/bi_work), JOBS (3), EXPECT (results json to
# compare with; default results/control_strips/original_results.json). See docs/REPRODUCE.md.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
: "${ERWIN:?set ERWIN}"; PYH=${PYH:-python3}
# absolute paths: batch_ink.sh runs after cd "$BI_ROOT", and the arm lists store paths under ERWIN
ERWIN=$(cd "$ERWIN" && pwd) || exit 1; BI_ROOT=${BI_ROOT:-$PWD/bi_work}; mkdir -p "$BI_ROOT" && BI_ROOT=$(cd "$BI_ROOT" && pwd) || exit 1
if [ -n "${CKPT:-}" ]; then CKPT=$(cd "$CKPT" && pwd) || exit 1; export CKPT; fi
export BI_ROOT UMB_PHerc0343="$ERWIN/inputs/umbilicus_PHerc0343.json"
OUT=${OUT:-$BI_ROOT/out}; EXPECT=${EXPECT:-$REPO/results/control_strips/original_results.json}
mkdir -p "$OUT" "$BI_ROOT"; L="$OUT/run.log"; log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
log "start"
"$PYH" -I "$HERE/make_arms.py" --erwin "$ERWIN" --out "$BI_ROOT/arms" | tee "$OUT/make_arms.json" || { log "FAILED make_arms"; exit 1; }
(cd "$BI_ROOT" && JOBS=${JOBS:-3} DEPTHS=1 ENS_DEPTH=1 KEEP_RENDER=0 bash "$REPO/scripts/pipeline/batch_ink.sh" "$BI_ROOT/arms/plain.list") >> "$OUT/batch.log" 2>&1 \
  || { log "FAILED plain arms (see $OUT/batch.log)"; exit 1; }
log "plain arms done"
(cd "$BI_ROOT" && JOBS=${JOBS:-3} DEPTHS=1 ENS_DEPTH=1 KEEP_RENDER=0 RENDER_FILL=reflect bash "$REPO/scripts/pipeline/batch_ink.sh" "$BI_ROOT/arms/fill.list") >> "$OUT/batch.log" 2>&1 \
  || { log "FAILED fill arms (see $OUT/batch.log)"; exit 1; }
log "fill arms done"
"$PYH" -I "$HERE/score_arms.py" --bi "$BI_ROOT" --erwin "$ERWIN" --out "$OUT/results.json" --expect "$EXPECT" | tee "$OUT/score.out" \
  || { log "FAILED scoring (see $OUT/score.out)"; exit 1; }
cp "$BI_ROOT/arms/plain.list" "$BI_ROOT/arms/fill.list" "$OUT/"
log "done"
