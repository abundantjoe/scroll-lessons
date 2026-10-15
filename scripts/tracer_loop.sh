#!/bin/bash
# Run the tracer over every seed of seeds/<scroll>.json, N at a time, skipping seeds already done (marker in logs/).
sc=$1; vol=$2; um=$3; N=${4:-1}; D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
mkdir -p $D/patches/$sc; echo $$ > $D/patches/$sc/tracer_loop.pid
# self-clean: kill any other tracer_loop.sh instance for this scroll (orphaned subshells survive a parent kill)
python3 - "$sc" $$ <<'PY'
import os, sys, signal
sc, me = sys.argv[1], int(sys.argv[2])
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) == me: continue
    try: cmd = open(f'/proc/{pid}/cmdline','rb').read().replace(b'\0', b' ').decode(errors='ignore')
    except Exception: continue
    if 'tracer_loop.sh %s' % sc in cmd and 'snapshot-bash' not in cmd:
        try:
            ppid = int(open(f'/proc/{pid}/stat').read().split(')')[1].split()[1])
            if ppid == me: continue
            os.kill(int(pid), signal.SIGTERM); print('[tracer_loop] killed stale instance', pid)
        except Exception: pass
PY
python3 -c "
import json; d=json.load(open('$R/seeds/$sc.json'))
for s in d['seeds']:
    if s.get('skip'): continue
    print(s['x'], s['y'], s['z'])" | while read X Y Z; do
  [ -f $D/patches/$sc/logs/seed_${X}_${Y}_${Z}.done ] && continue
  # concurrency among the 9 um tracers only (the 2.4 um rescan queue under patches_2um runs on its own slot);
  # the random stagger keeps two scroll loops from passing the check in the same second
  sleep $((RANDOM % 45))
  while [ "$(ps -eo args | grep '^/opt/vc/bin/vc_grow_seg_from_seed' | grep -vc 'patches_2um')" -ge "$N" ]; do sleep $((20 + RANDOM % 25)); done
  # backlog cap: do not trace faster than the reader can read (CPU is the limit); wait while >= BACKLOG QC-PASS
  # patches of this scroll have no completed read yet (patches without qc.json count as pending too)
  BACKLOG=${BACKLOG:-6}
  while true; do
    n=$(python3 - "$D/patches/$sc" <<'PY'
import sys, os, glob, json
root=sys.argv[1]; n=0
for p in glob.glob(os.path.join(root, 'auto_grown_*')) + glob.glob(os.path.join(root, 'team_*')):
    q=os.path.join(p, 'qc.json')
    v=json.load(open(q)).get('verdict') if os.path.exists(q) else 'PASS'
    if v!='PASS': continue
    if not glob.glob(os.path.join(p, 'read_*', '.read_complete')): n+=1
print(n)
PY
)
    [ "$n" -lt "$BACKLOG" ] && break
    sleep 120
  done
  # grid-cache cap: the lazily fetched normal grids reach several GB per band; above 900 MB drop the grid files (the disk guard tightens to 500 MB when free disk is actually at risk)
  # (metadata.json and the remote marker stay; the tracer refetches what the next seed needs)
  gb=$(du -sm $D/normal_grids/$sc | cut -f1); if [ "$gb" -gt 900 ]; then echo "[tracer_loop] pruning normal-grid cache of $sc (${gb} MB)"; find $D/normal_grids/$sc -type f ! -name metadata.json ! -name normal-grids-remote.json -delete; fi
  echo "[tracer_loop $(date -u +%FT%TZ)] seed $X $Y $Z"
  # A slot pool caps concurrent 9 um traces across ALL scroll loops at TRACE_SLOTS (default 1; see RULES, trace
  # and normal-grid chunks, and too many at once fill this 30 GB disk faster than the guard can prune. Each trace runs
  # in the foreground of its subshell, so a slot is held for exactly the trace's duration.
  ( slot=""
    while [ -z "$slot" ]; do
      for k in $(seq 1 ${TRACE_SLOTS:-1}); do
        exec 9>>$D/logs/tracer_slot_$k.lock
        if flock -n 9; then slot=$k; break; fi
        exec 9>&-
      done
      [ -z "$slot" ] && sleep 20
    done
    VC_THREADS=2 bash $R/scripts/vc_tools.sh trace $sc $vol $um $X $Y $Z $D/patches/$sc >/dev/null 2>&1 ) &
  tpid=$!
  sleep 90   # docker start-up: give the tracer process time to appear before it is reniced
  # the container process is a child of containerd, not of this nice'd shell: put the tracer's threads below the readers
  for tp in $(ps -eo pid,args | grep '[/]opt/vc/bin/vc_grow_seg_from_seed' | grep "/$sc/" | awk '{print $1}'); do renice -n 15 -p $(ls /proc/$tp/task 2>/dev/null) >/dev/null 2>&1; done
  wait $tpid   # the lock is released when this trace ends; the next loop iteration queues behind any other scroll
done
while ps -eo args | grep '^/opt/vc/bin/vc_grow_seg_from_seed' | grep -v 'patches_2um' | grep -q "/$sc/"; do sleep 60; done; echo "[tracer_loop] all seeds of $sc done"
