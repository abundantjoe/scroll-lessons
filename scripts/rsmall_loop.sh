#!/bin/bash
# RULES R-SMALL: interior seeds at a reduced growth budget (40; 20 was tried first and gave 0.49 cm2 patches,
# below QC 5.8's own 0.5 cm2 area bar, so it could not answer the question - see the RULES note), into patches/<scroll>_small/ so they can never be confused with
# the 60-generation traces. Same prediction volume, same density-gated seed file, same QC, R-CREST, reader and rule 5.5.
# RULES R-SMALL-2 reuses this loop rather than copying it, so its hard-won guards (the flock slot pool, the pause
# marker that stops a RUNNING loop, the trace cap) apply unchanged. RS_SUFFIX and RS_SEEDS select the campaign;
# the defaults are exactly R-SMALL's, so nothing about R-SMALL changes.
sc=$1; vol=$2; um=$3; D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
SUF=${RS_SUFFIX:-_small}
SEEDS=${RS_SEEDS:-$R/seeds/${sc}_interior.json}
mkdir -p $D/patches/${sc}${SUF}; echo $$ > $D/patches/${sc}${SUF}/rsmall_loop.pid
# The queue is materialised into an ARRAY and every command in the body has its stdin closed. A `while read` fed by
# a pipe hands its stdin to whatever runs inside it: that is how dense_loop.sh stopped after one trace on
# 2026-09-18 with 24 seeds eaten out from under it. This loop had the same shape and had not been bitten yet.
mapfile -t SEEDLIST < <(python3 -c "
import json; d=json.load(open('$SEEDS'))
for s in d['seeds']: print(s['x'], s['y'], s['z'])")
echo "[rsmall $(date -u +%FT%TZ)] $sc ${#SEEDLIST[@]} seeds from $SEEDS into patches/${sc}${SUF}"
for line in "${SEEDLIST[@]}"; do
  read -r X Y Z <<< "$line"
  [ -f $D/patches/${sc}${SUF}/logs/seed_${X}_${Y}_${Z}.done ] && continue
  # The rsmall_paused marker must stop a RUNNING loop too, not merely prevent the supervisor restarting one: R-SMALL's
  # bar was called on 2026-09-18 while this loop still had a queue, and every further trace was waste competing for the
  # single trace slot with the experiment that replaced it.
  [ -f $D/patches/${sc}${SUF}/rsmall_paused ] && { echo "[rsmall] $sc$SUF paused"; break; }
  n=$(ls -d $D/patches/${sc}${SUF}/auto_grown_* 2>/dev/null | wc -l)
  [ "$n" -ge "${RSMALL_MAX:-20}" ] && { echo "[rsmall] $sc$SUF: ${RSMALL_MAX:-20} traces done, stopping"; break; }
  # A ps-count check is racy: two loops that sample it in the same second both start, which is exactly what happened
  # on 2026-09-18 (two traces running under a cap of one). Use the same flock slot pool tracer_loop.sh uses, so the
  # cap holds across every loop on the box.
  slot=""
  while [ -z "$slot" ]; do
    for k in $(seq 1 ${TRACE_SLOTS:-1}); do
      exec 9>>$D/logs/tracer_slot_$k.lock
      if flock -n 9; then slot=$k; break; fi
      exec 9>&-
    done
    [ -z "$slot" ] && sleep 20
  done
  echo "[rsmall $(date -u +%FT%TZ)] $sc seed $X $Y $Z (generations ${TRACE_GENERATIONS:-40})"
  TRACE_GENERATIONS=${TRACE_GENERATIONS:-40} VC_THREADS=2 bash $R/scripts/vc_tools.sh trace $sc $vol $um $X $Y $Z $D/patches/${sc}${SUF} </dev/null >/dev/null 2>&1
  exec 9>&-   # release the slot
done
echo "[rsmall $(date -u +%FT%TZ)] $sc$SUF interior queue done"
