#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# D3 stage 2 watcher (RULES.md DECL-D3-A3 item 1): for ARM in CTRL FA NULLA REVA (training order), wait (poll every
# 60 s) until /work/d3/runs/$ARM/model_final.pth exists AND the arm's summary.json records model_final (path and
# sha256 equal to the file's sha256), then run d3_infer.py --arm $ARM on the 8 D1 windows with --threads 1 if any
# d3_train.py process is alive, else --threads 3. Idempotent and resumable: an arm whose record
# /work/d3/work/infer_$ARM.json has returncode 0 on all 8 windows is skipped, and d3_infer.py skips completed
# windows. A failing d3_infer.py run is retried once after 60 s; a second failure stops the watcher (exit 1).
# Log: /work/d3/logs/infer_arms.log (UTC stamps). Start it with start_d3_stage2.sh (nohup + pgrep guard).
# d3_infer.py writes its own ledger rows (inference and decode) to /work/d3/work/ledger.tsv; this watcher adds one row
# per d3_infer.py invocation (output sha256 = the arm's infer record).
set -u
LOG=/work/d3/logs/infer_arms.log
LEDGER=/work/d3/work/ledger.tsv
PY=/opt/hv-ink/bin/python
WINDOWS="J1 J2 J3 J4 J5 blank_w053_y256_x1536 blank_w053_y256_x7168 canary_w044_y2816_x2816"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(ts) $*" >> "$LOG"; }
cd /work/d3/work || exit 1
log "infer_arms start pid $$"

arm_ready() {  # model_final.pth exists and summary.json records it with the file's sha256
  local d=/work/d3/runs/$1
  [ -f "$d/model_final.pth" ] && [ -f "$d/summary.json" ] || return 1
  local rec
  rec=$($PY -c "import json,sys; s=json.load(open('$d/summary.json')); m=s.get('model_final') or {}; print(m.get('sha256',''))" 2>/dev/null) || return 1
  [ -n "$rec" ] || return 1
  [ "$rec" = "$(sha256sum "$d/model_final.pth" | cut -d' ' -f1)" ]
}

arm_done() {  # infer record has returncode 0 on all 8 windows
  local f=/work/d3/work/infer_$1.json
  [ -f "$f" ] || return 1
  $PY -c "
import json,sys
r=json.load(open('$f'))
w=r.get('windows',{})
sys.exit(0 if all(w.get(k,{}).get('returncode')==0 for k in '$WINDOWS'.split()) else 1)" 2>/dev/null
}

for ARM in CTRL FA NULLA REVA; do
  if arm_done "$ARM"; then log "arm $ARM: inference already complete, skipped"; continue; fi
  n=0
  until arm_ready "$ARM"; do
    if [ $((n % 30)) -eq 0 ]; then log "arm $ARM: waiting for model_final.pth + summary.json (poll 60 s)"; fi
    n=$((n + 1)); sleep 60
  done
  log "arm $ARM: model_final ready sha256 $(sha256sum /work/d3/runs/$ARM/model_final.pth | cut -d' ' -f1)"
  attempt=0
  while :; do
    attempt=$((attempt + 1))
    if pgrep -f "python.*d3_train\.py" > /dev/null; then T=1; else T=3; fi
    CMD="$PY /work/d3/scripts/d3_infer.py --arm $ARM --threads $T"
    START=$(ts)
    log "arm $ARM: start d3_infer attempt $attempt threads $T"
    env -u PYTHONPATH OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T NUMEXPR_NUM_THREADS=$T \
      PYTHONDONTWRITEBYTECODE=1 $CMD >> /work/d3/logs/infer_$ARM.log 2>&1
    RC=$?
    END=$(ts)
    if [ -f /work/d3/work/infer_$ARM.json ]; then SHA=$(sha256sum /work/d3/work/infer_$ARM.json | cut -d' ' -f1); else SHA=missing; fi
    CPU="cpus=$T/$(getconf _NPROCESSORS_ONLN) $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(hostname)" "$CPU" "OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T NUMEXPR_NUM_THREADS=$T $CMD" "$START" "$END" "$RC" "$SHA" >> "$LEDGER"
    log "arm $ARM: end d3_infer attempt $attempt rc $RC record sha256 $SHA"
    if [ "$RC" -eq 0 ] && arm_done "$ARM"; then break; fi
    if [ "$attempt" -ge 2 ]; then log "infer_arms ABORT at $ARM (two failed attempts)"; exit 1; fi
    sleep 60
  done
done
log "infer_arms all done"
