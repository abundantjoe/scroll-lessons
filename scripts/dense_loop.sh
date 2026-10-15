#!/bin/bash
# RULES G-GP part 4: trace the seeds that scripts/sheet_seeds.py sampled from ONE patch's own surface points, so every
# trace starts on the same physical sheet. Output goes to patches/<scroll>_dense/ so it can never be confused with the
# breadth-first coverage traces. Same volume, same tracer, same parameters, same budget -- only the seeds differ.
#   dense_loop.sh <scroll> <vol> <um> <seeds.json>
#
# The seed list is read into an ARRAY, not piped into `while read`, and every command in the body has its stdin closed.
# A `while read` fed by a pipe hands its stdin to whatever runs inside it: the first version of this loop stopped after
# ONE trace on 2026-09-18 and reported its queue done, having had the remaining 24 seeds eaten out from under it.
set -uo pipefail
# DENSE_PARTS/DENSE_PART split the seed list between concurrent loops (seed index % PARTS == PART), so two loops
# never contend for the same seed. Concentrated seeding is all on ONE scroll, so a second slot costs no extra normal
# grids -- both traces read the same cache -- which is why the slot pool is worth widening here and was not for the
# breadth queues.
sc=$1; vol=$2; um=$3; seedfile=$4; D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
PART=${DENSE_PART:-0}; PARTS=${DENSE_PARTS:-1}
mkdir -p $D/patches/${sc}_dense; echo $$ > $D/patches/${sc}_dense/dense_loop_$PART.pid
cp -n "$seedfile" $D/patches/${sc}_dense/seeds.json 2>/dev/null || true
mapfile -t SEEDS < <(python3 -c "
import json; d=json.load(open('$seedfile'))
for s in d['seeds']: print(s['x'], s['y'], s['z'])")
echo "[dense $(date -u +%FT%TZ)] $sc part $PART/$PARTS of ${#SEEDS[@]} seeds from $seedfile"
for i in "${!SEEDS[@]}"; do
  [ $(( i % PARTS )) -eq "$PART" ] || continue
  read -r X Y Z <<< "${SEEDS[$i]}"
  [ -f $D/patches/${sc}_dense/logs/seed_${X}_${Y}_${Z}.done ] && continue
  [ -f $D/patches/${sc}_dense/dense_paused ] && { echo "[dense $(date -u +%FT%TZ)] $sc part $PART paused"; break; }
  slot=""
  while [ -z "$slot" ]; do
    for k in $(seq 1 ${TRACE_SLOTS:-1}); do
      exec 9>>$D/logs/tracer_slot_$k.lock
      if flock -n 9; then slot=$k; break; fi
      exec 9>&-
    done
    [ -z "$slot" ] && sleep 20
  done
  # A trace for this seed may already be running with no loop behind it: the supervisor kills a loop holding a stale
  # HTTPS_PROXY, which orphans its in-flight docker trace and releases the flock slot, and the restarted loop would
  # then trace the same seed again. Two traces of one seed are the same observation twice -- patch_agreement.py now
  # refuses to count them twice, but they should not be made in the first place. Wait for the orphan instead.
  while ps -eo args | grep -q "[v]c_grow_seg_from_seed .*--target-dir /data/patches/${sc}_dense .*--seed $X $Y $Z"; do
    echo "[dense $(date -u +%FT%TZ)] $sc seed $X $Y $Z already being traced (orphaned run); waiting"
    sleep 60
  done
  [ -f $D/patches/${sc}_dense/logs/seed_${X}_${Y}_${Z}.done ] && { exec 9>&-; continue; }
  echo "[dense $(date -u +%FT%TZ)] $sc seed $X $Y $Z (generations ${TRACE_GENERATIONS:-60})"
  TRACE_GENERATIONS=${TRACE_GENERATIONS:-60} VC_THREADS=2 \
    bash $R/scripts/vc_tools.sh trace $sc $vol $um $X $Y $Z $D/patches/${sc}_dense </dev/null >/dev/null 2>&1
  exec 9>&-   # release the slot
  n=$(ls -d $D/patches/${sc}_dense/auto_grown_* 2>/dev/null | wc -l)
  echo "[dense $(date -u +%FT%TZ)] $sc seed $X $Y $Z finished; $n patches so far"
done
echo "[dense $(date -u +%FT%TZ)] $sc part $PART dense queue done ($(ls -d $D/patches/${sc}_dense/auto_grown_* 2>/dev/null | wc -l) patches)"
