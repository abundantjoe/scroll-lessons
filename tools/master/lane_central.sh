#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-7 control: centralized training on ALL 18 PHerc0009B shards from the common checkpoint, to compare with the
# federated average. usage: lane_central.sh <ROUND> [epochs=4]   output: logs/fl7/central/central_r<R>.pt (+hist)
set -uo pipefail; R=$1; E=${2:-4}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD)
PYB=/opt/hv/bin/python; PYT=/opt/hv-ink/bin/python; mkdir -p /dev/shm/shards logs/fl7/central /work/own; O=logs/fl7/central
log(){ echo "[$(date -u +%FT%TZ)] central r$R $*" >> $O/central.log; }
push(){ flock /work/own/git.lock -c "git add -f $O >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl7 central r$R: $1'"; for d in 2 4 8 16 32; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>/dev/null && return 0; flock /work/own/git.lock git pull -q --rebase origin $BR 2>/dev/null; sleep $d; done; log "push failed"; }
log "building all shards"; push "start"
$PYB - <<PY
import json,subprocess,os
m=json.load(open('logs/fl7_manifest.json')); jobs=[x for x in m if x['scroll']=='PHerc0009B']+[x for x in m if x['scroll']=='PHerc0343P'][:1]
for x in jobs:
    out=f"/dev/shm/shards/{x['scroll']}_{x['segment'][:14]}.npz"
    if os.path.exists(out): continue
    subprocess.run(['timeout','2400','$PYB','tools/master/build_data.py',x['scroll'],x['segment'],x['coarse_sv'],out,'--stride','48','--max','600'])
print('shards ready')
PY
TR=$(ls /dev/shm/shards/PHerc0009B_*.npz | tr '\n' ' '); VA=$(ls /dev/shm/shards/PHerc0343P_*.npz | head -1); INIT=""; [ -f logs/fl7/global_r$((R-1)).pt ] && INIT="--init logs/fl7/global_r$((R-1)).pt"
log "train on $(echo $TR | wc -w) shards, $INIT"; push "shards built"
$PYT tools/master/train_master.py sup --train $TR --val $VA --out $O/central_r$R.pt --epochs $E --bs 8 --base 16 --depth 16 $INIT > $O/central_r$R.train.log 2>&1 || { log "train failed: $(tail -2 $O/central_r$R.train.log | tr '\n' ' ')"; push "train failed"; exit 1; }
cp $O/central_r$R.pt.hist.json $O/central_r$R.hist.json 2>/dev/null; log "done: $(tail -1 $O/central_r$R.train.log)"; touch $O/central_r$R.DONE; push "done"
