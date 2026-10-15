#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-UMB-2 lane job: native-resolution core at this lane's share of 48 y positions (level 0, in-domain y 1536..11136).
# usage: lane_core.sh <LANE 0..N-1> <NLANES>    output: logs/umb/native/lane<LANE>/core_native.json (+ log), pushed to the branch
set -uo pipefail; L=$1; N=$2; OFF=${3:-0}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD); O=logs/umb/native/lane${L}_o${OFF}; mkdir -p $O /work/own
log(){ echo "[$(date -u +%FT%TZ)] core lane$L $*" >> $O/lane.log; }
push(){ flock /work/own/git.lock -c "git add -f $O >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'umb native core lane$L: $1'"; for d in 2 4 8 16 32; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>/dev/null && return 0; flock /work/own/git.lock git pull -q --rebase origin $BR 2>/dev/null; sleep $d; done; log "push failed"; }
[ -x /opt/hv/bin/python ] || { log "setup_env"; bash docker/env/setup_env.sh > /dev/shm/setup_env.log 2>&1 || { log "setup failed"; push "setup failed"; exit 1; }; }
YS=$(/opt/hv/bin/python -c "import numpy as np; ys=[int(round(v)) for v in np.linspace(1536+$OFF,11136+$OFF,48)]; print(' '.join(str(y) for y in ys[$L::$N]))")
log "start y: $YS"; push "start"
/opt/hv/bin/python tools/umb/core_native.py $O --l3 /nonexistent --y $YS > $O/core_native.log 2>&1 || { log "failed: $(tail -2 $O/core_native.log | tr '\n' ' ')"; push "failed"; exit 1; }
log "done: $(grep -c "\"y\"" $O/core_native.log) records; fields cached in /dev/shm/umb_fields ($(ls /dev/shm/umb_fields 2>/dev/null | wc -l) files)"; push "done"
