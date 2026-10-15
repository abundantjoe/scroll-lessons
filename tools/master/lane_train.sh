#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-7 lane trainer. Round R: build this lane's shard subset (once, into /dev/shm), then train ONE epoch from the
# global checkpoint logs/fl7/global_r<R-1>.pt (or scratch), evaluate on the shared validation shard, push
# logs/fl7/lanes/<LANE>_r<R>.pt (+ .hist.json). usage: lane_train.sh <LANE 0..6> <ROUND> [epochs=1]
set -uo pipefail; L=$1; R=$2; E=${3:-1}; TAG=${4:-}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD)
PYB=/opt/hv/bin/python; PYT=/opt/hv-ink/bin/python; mkdir -p /dev/shm/shards logs/fl7/lanes /work/own; O=logs/fl7/lanes
log(){ echo "[$(date -u +%FT%TZ)] lane$L r$R $*" >> $O/lane${L}${TAG}.log; }
push(){ flock /work/own/git.lock -c "git add -f $O >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl7 lane$L$TAG r$R: $1'"; for d in 2 4 8 16 32; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>/dev/null && return 0; flock /work/own/git.lock git pull -q --rebase origin $BR 2>/dev/null; sleep $d; done; log "push failed"; }
# 1. shards: this lane takes PHerc0009B manifest entries i with i % 7 == L; everyone also builds the shared val shard (PHerc0343P entry 0)
$PYB - <<PY
import json,subprocess,os
m=[x for x in json.load(open('logs/fl7_manifest.json'))]; tr=[x for x in m if x['scroll']=='PHerc0009B']; va=[x for x in m if x['scroll']=='PHerc0343P']
jobs=[tr[i] for i in range(len(tr)) if i%7==$L]+[va[0]]
from concurrent.futures import ThreadPoolExecutor
def build(x):
    out=f"/dev/shm/shards/{x['scroll']}_{x['segment'][:14]}.npz"
    if os.path.exists(out): return
    subprocess.run(['timeout','2400','$PYB','tools/master/build_data.py',x['scroll'],x['segment'],x['coarse_sv'],out,'--stride','48','--max','600'])
list(ThreadPoolExecutor(4).map(build, jobs))                                   # the builds are network-bound: four at a time
print('shards ready')
PY
TR=$(ls /dev/shm/shards/PHerc0009B_*.npz 2>/dev/null | tr '\n' ' '); VA=$(ls /dev/shm/shards/PHerc0343P_*.npz | head -1); [ -n "$TR" ] && [ -n "$VA" ] || { log "no shards"; exit 1; }
INIT=""; [ -f logs/fl7/global_r$((R-1)).pt ] && INIT="--init logs/fl7/global_r$((R-1)).pt"
log "train on $(echo $TR | wc -w) shards, val $VA, $INIT"
$PYT tools/master/train_master.py sup --train $TR --val $VA --out $O/lane${L}${TAG}_r${R}.pt --epochs $E --bs 8 --base 16 --depth 16 $INIT > $O/lane${L}${TAG}_r${R}.train.log 2>&1 || { log "train failed: $(tail -2 $O/lane${L}${TAG}_r${R}.train.log | tr '\n' ' ')"; push "train failed"; exit 1; }
cp $O/lane${L}${TAG}_r${R}.pt.hist.json $O/lane${L}${TAG}_r${R}.hist.json 2>/dev/null; log "done: $(tail -1 $O/lane${L}${TAG}_r${R}.train.log)"; touch $O/lane${L}${TAG}_r${R}.DONE; push "round $R weights"
