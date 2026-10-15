#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-UMB-2 + A1 lane job, PASS 2: U-turn operator at native resolution, windows from each mask edge to the section's
# mid-x, at this lane's share of 48 y positions (+ offset). The operator self-test must pass first (A1 item 3).
# usage: lane_core2.sh <LANE 0..N-1> <NLANES> [OFF] [fwd|rev]   output: logs/umb/native2/lane<LANE>_o<OFF>/core_native.json (+ logs), pushed
set -uo pipefail; L=$1; N=$2; OFF=${3:-0}; DIR=${4:-fwd}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD); O=logs/umb/native2/lane${L}_o${OFF}; [ "$DIR" = rev ] && O=${O}_rev; mkdir -p $O /work/own
log(){ echo "[$(date -u +%FT%TZ)] core2 lane$L $*" >> $O/lane.log; }
push(){ flock /work/own/git.lock -c "git add -f $O >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'umb native core2 lane$L: $1'"; for i in $(seq 1 20); do flock /work/own/git.lock git push -q origin HEAD:$BR 2>/dev/null && return 0; flock /work/own/git.lock git pull -q --rebase origin $BR 2>/dev/null; sleep $((RANDOM % 20 + 5)); done; log "push failed"; }
[ -x /opt/hv/bin/python ] || { log "setup_env"; bash docker/env/setup_env.sh > /dev/shm/setup_env.log 2>&1 || { log "setup failed"; push "setup failed"; exit 1; }; }
OMP_NUM_THREADS=2 /opt/hv/bin/python tools/umb/uturns.py --selftest > $O/selftest.json 2>&1 || { log "operator self-test FAILED: $(tail -1 $O/selftest.json)"; push "selftest failed"; exit 1; }
log "self-test: $(tail -1 $O/selftest.json | cut -c1-200)"
YS=$(/opt/hv/bin/python -c "import numpy as np; ys=[int(round(v)) for v in np.linspace(1536+$OFF,11136+$OFF,48)][$L::$N]; ys=ys[::-1] if '$DIR'=='rev' else ys; print(' '.join(str(y) for y in ys))")   # rev: the same y positions from the other end (a second lane halves the wall-clock; the union is complete when they meet)
for i in $(seq 1 120); do [ "$(ps -eo args | grep -c '^/opt/hv/bin/python tools/umb/core_native.py logs/umb/native/')" -eq 0 ] && break; [ $i -eq 1 ] && log "waiting for the pass-1 run to finish"; sleep 60; done
log "start y: $YS"; push "start"
/opt/hv/bin/python tools/umb/core_native.py $O --l3 /nonexistent --depth_mm 0 --cache "" --y $YS > $O/core_native.log 2>&1 || { log "failed: $(tail -2 $O/core_native.log | tr '\n' ' ')"; push "failed"; exit 1; }
log "done: $(python3 -c "import json;print(len(json.load(open('$O/core_native.json'))['records']))" 2>/dev/null) records; marker $O/DONE"; push "done"
