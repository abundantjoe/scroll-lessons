#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-7 item 3(ii): ink_9um (hybrid_3d2d seed42 step-075000, both directions) on the held-out validation segment's
# 8.64 um organizer surface volume, scored against the pseudo-labels at the validation shard's crop positions.
# usage: lane_baseline.sh <manifest index, default 18 = PHerc0343P entry 0>   outputs: logs/fl7/baseline/<scroll>_<seg14>/
set -uo pipefail; I=${1:-18}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD)
PYB=/opt/hv/bin/python; PYT=/opt/hv-ink/bin/python; CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth; B=vesuvius-challenge-open-data
read SCROLL SEG SV < <($PYB -c "import json;x=json.load(open('logs/fl7_manifest.json'))[$I];print(x['scroll'],x['segment'],x['coarse_sv'])")
N=${SCROLL}_${SEG:0:14}; W=/dev/shm/bl_$N; O=logs/fl7/baseline/$N; mkdir -p $W $O /work/own /dev/shm/shards
log(){ echo "[$(date -u +%FT%TZ)] baseline $N $*" >> $O/pipeline.log; }
push(){ flock /work/own/git.lock -c "git add -f $O >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl7 baseline $N: $1'"; for d in 2 4 8 16 32; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>/dev/null && return 0; flock /work/own/git.lock git pull -q --rebase origin $BR 2>/dev/null; sleep $d; done; log "push failed"; }
fail(){ log "FAILED: $1"; echo "$1" > $O/FAILED; push "FAILED $1"; exit 1; }
[ -f $O/DONE ] && exit 0
if [ ! -f $CKPT ] || [ ! -x $PYT ]; then log "setup_env"; bash docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { tail -20 $W/setup_env.log > $O/env_fail.log.tail; fail "setup_env"; }; fi
SH=/dev/shm/shards/$N.npz
[ -f $SH ] || timeout 2400 $PYB tools/master/build_data.py $SCROLL $SEG $SV $SH --stride 48 --max 600 > $W/build.log 2>&1 || fail "shard build"
R=$W/sv.zarr
if [ ! -f $W/sv.ok ]; then rm -rf $R; log "fetch sv"
  $PYB - <<PY || fail "sv fetch"
import s3fs,os; fs=s3fs.S3FileSystem(anon=True); sv='$B/$SCROLL/segments/$SEG/surface-volumes/$SV'
os.makedirs('$R',exist_ok=True)
for f in ['.zattrs','.zgroup']: fs.get(sv+'/'+f,'$R/'+f)
fs.get(sv+'/0','$R/0',recursive=True); print('fetched')
PY
  touch $W/sv.ok; fi
if [ ! -f $W/ink_reverse.tif ]; then log "ink_9um both"; t0=$SECONDS
  ( cd $W && OMP_NUM_THREADS=4 $PYT -m vesuvius.ink_detection.inference.infer $R $CKPT $W/ink.tif --direction both --batch-size 4 --num-workers 1 --no-compile > $W/ink.log 2>&1 ) || { tail -5 $W/ink.log > $O/ink_fail.log.tail; fail "ink_9um"; }
  log "ink_9um done $((SECONDS-t0)) s"; fi
$PYB - <<PY || fail "mean map"
import tifffile,numpy as np,cv2
f=tifffile.imread('$W/ink.tif').astype(np.float32); r=tifffile.imread('$W/ink_reverse.tif').astype(np.float32)
s=255.0 if max(f.max(),r.max())>1.5 else 1.0; m=(f+r)/(2*s)
tifffile.imwrite('$W/ink_mean.tif',m.astype(np.float32)); cv2.imwrite('$O/ink9um_mean_q4.png',cv2.resize(np.clip(m*255,0,255).astype(np.uint8),None,fx=0.25,fy=0.25,interpolation=cv2.INTER_AREA))
PY
for v in ink:fwd ink_reverse:rev ink_mean:mean; do $PYB tools/master/baseline_eval.py $SH $W/${v%%:*}.tif $O/ink9um_s42_${v##*:}.json --name ink9um_s42_${v##*:} >> $O/pipeline.log 2>&1 || fail "eval ${v##*:}"; done
touch $O/DONE; log "DONE"; push "DONE"
