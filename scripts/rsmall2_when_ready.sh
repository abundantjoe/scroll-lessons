#!/bin/bash
# RULES R-SMALL-2: start the newly-admitted-band interior queue the moment G-GP part 5 releases a trace slot.
# It chooses nothing: the population, the budget and the bar are all declared. Fires once per scroll and is a
# no-op while part 5 still has seeds to trace.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
need=$($R/.venv/bin/python -c "
import json; print(len(json.load(open('$D/gates/ggp/part5_seeds.json'))['seeds']))")
have=$($R/.venv/bin/python -c "
import json, os
D='$D'; seeds=json.load(open(D+'/gates/ggp/part5_seeds.json'))['seeds']
print(sum(os.path.exists('%s/patches/PHerc0826_dense/logs/seed_%s_%s_%s.done' % (D, s['x'], s['y'], s['z'])) for s in seeds))")
if [ "$have" -lt "$need" ]; then
  echo "[rsmall2 $(date -u +%FT%TZ)] part 5 still tracing ($have/$need); not starting"; exit 0
fi
for spec in PHerc0826:20250821151701:9.362 PHerc0358:20250821151737:9.362; do
  IFS=: read sc vol um <<< "$spec"
  pf=$D/patches/${sc}_rs2/rsmall_loop.pid
  [ -f $D/patches/${sc}_rs2/rsmall_paused ] && { echo "[rsmall2] $sc paused"; continue; }
  if [ -f "$pf" ] && kill -0 "$(cat $pf)" 2>/dev/null; then echo "[rsmall2] $sc already running"; continue; fi
  n=$(ls -d $D/patches/${sc}_rs2/auto_grown_* 2>/dev/null | wc -l)
  # RSMALL_MAX 20 per scroll gives up to 40 traces across the two, against the bar's minimum of 15.
  [ "$n" -ge 20 ] && { echo "[rsmall2] $sc already has $n traces"; continue; }
  echo "[rsmall2 $(date -u +%FT%TZ)] starting $sc from seeds/${sc}_rsmall2.json"
  (RS_SUFFIX=_rs2 RS_SEEDS=$R/seeds/${sc}_rsmall2.json TRACE_GENERATIONS=40 RSMALL_MAX=20 \
     nohup bash $R/scripts/rsmall_loop.sh "$sc" "$vol" "$um" >> $D/logs/rsmall2_${sc}.log 2>&1 &)
done
