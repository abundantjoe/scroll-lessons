#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-7 item 1(a): DINO-3D self-distillation on this lane's shards (labels unused), pushed as logs/fl7/ssl/ssl_<TAG>.pt
# usage: lane_ssl.sh <LANE> <TAG> [steps=3000] [width=16]
set -uo pipefail; L=$1; TAG=$2; ST=${3:-3000}; WD=${4:-16}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD)
PYB=/opt/hv/bin/python; PYT=/opt/hv-ink/bin/python; O=logs/fl7/ssl; mkdir -p /dev/shm/shards $O /work/own
log(){ echo "[$(date -u +%FT%TZ)] lane$L ssl $TAG $*" >> $O/lane${L}_ssl.log; }
push(){ flock /work/own/git.lock -c "git add -f $O >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl7 lane$L ssl $TAG: $1'"; for d in 2 4 8 16 32; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>/dev/null && return 0; flock /work/own/git.lock git pull -q --rebase origin $BR 2>/dev/null; sleep $d; done; log "push failed"; }
$PYB - <<PY
import json,subprocess,os
m=json.load(open('logs/fl7_manifest.json')); tr=[x for x in m if x['scroll']=='PHerc0009B']; va=[x for x in m if x['scroll']=='PHerc0343P']
for x in [tr[i] for i in range(len(tr)) if i%7==$L]+[va[0]]:
    out=f"/dev/shm/shards/{x['scroll']}_{x['segment'][:14]}.npz"
    if not os.path.exists(out): subprocess.run(['timeout','2400','$PYB','tools/master/build_data.py',x['scroll'],x['segment'],x['coarse_sv'],out,'--stride','48','--max','600'])
PY
S=$(ls /dev/shm/shards/*.npz | grep -v PHerc0343P | tr "\n" " "); [ -n "$S" ] || { log "no shards"; exit 1; }   # the held-out scroll never enters pretraining (lane 2 flagged the leak)
log "start on $(echo $S | wc -w) shards, $ST steps, width $WD"
OMP_NUM_THREADS=4 $PYT tools/master/train_master.py ssl --shards $S --out $O/ssl_$TAG.pt --steps $ST --bs 8 --width $WD --lr 1e-4 > $O/ssl_$TAG.train.log 2>&1 || { log "failed: $(tail -2 $O/ssl_$TAG.train.log | tr '\n' ' ')"; push "failed"; exit 1; }
log "done: $(grep -c 'non-finite' $O/ssl_$TAG.train.log) skipped steps; last $(grep '^ssl step' $O/ssl_$TAG.train.log | tail -1)"; touch $O/ssl_$TAG.DONE; push "done"
