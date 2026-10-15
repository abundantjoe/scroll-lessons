#!/bin/bash
# Trace the CT-gated seeds of a 2.4 um rescan (seeds/<scroll>_2um.json) on its L2 surface prediction, one at a time,
# outer -> middle -> inner, skipping seeds with a .done marker. Waits for an older trace_queue.sh of the scroll to end.
# Usage: trace_seeds_2um.sh <scroll> <rescan-volume-id>
sc=$1; vol=$2; D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
export SURF_SUFFIX=-surface-20260413222639-surface-m7-L2-th0.2 VC_CACHE_SUFFIX=_L2 VC_THREADS=2
while pgrep -f "patches_2um/$sc/trace_queue.sh" >/dev/null; do sleep 60; done
for pass in 1 2; do   # second pass retraces seeds whose tracer was interrupted (no .done marker)
python3 - "$R/seeds/${sc}_2um.json" <<'PY' | while read X Y Z cls; do
import json, sys
d = json.load(open(sys.argv[1])); order = {"outer": 0, "middle": 1, "inner": 2}
for s in sorted(d["seeds"], key=lambda s: (order[s["radius"]], s["z"])):
    if s.get("skip"): continue
    print(s["x"], s["y"], s["z"], s["radius"])
PY
  [ -f $D/patches_2um/$sc/logs/seed_${X}_${Y}_${Z}.done ] && continue
  gb=$(du -sm $D/normal_grids/$sc | cut -f1)
  if [ "$gb" -gt 1200 ]; then
    echo "[trace_seeds_2um] pruning normal-grid cache of $sc ($gb MB)"
    find $D/normal_grids/$sc -type f ! -name metadata.json ! -name normal-grids-remote.json -delete
  fi
  echo "[trace_seeds_2um $(date -u +%FT%TZ)] seed $X $Y $Z ($cls)"
  ( sleep 60; for tp in $(ps -eo pid,args | grep '[/]opt/vc/bin/vc_grow_seg_from_seed' | grep "patches_2um/$sc" | awk '{print $1}'); do renice -n 15 -p $(ls /proc/$tp/task 2>/dev/null) >/dev/null 2>&1; done ) &
  nice -n 5 bash $R/scripts/vc_tools.sh trace $sc $vol 9.612 $X $Y $Z $D/patches_2um/$sc
done; done; echo "[trace_seeds_2um $(date -u +%FT%TZ)] all seeds done"
