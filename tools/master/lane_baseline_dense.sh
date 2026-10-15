#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-7 item 3(ii), public-model comparison on the held-out scroll: the public dense-native 9 um ink model
# (Hugging Face Nieuwlaar/ink9um-dense-native, weights/dense_native_016000.safetensors, commit b894a04) run with villa's
# vesuvius.ink_detection.inference.infer (the merged koine_machines pipeline, villa 41701aa) on the 8.64 um organizer
# surface volume of PHerc0343P 20250511003658, scored against the pseudo-labels of the validation shard at its crop
# positions (tools/master/baseline_eval.py). Recipe per the model card: overlap 0.5, Hann blending, no compile,
# default (center) 17-layer window forward + reverse, then the 4-window z-ensemble (card windows for 28-slice native
# volumes, mapped to this 31-slice volume at the same physical offsets from the mid-plane; see recipe.json).
# usage: lane_baseline_dense.sh [stage]   stage = default | zavg | all (default all)   outputs: logs/fl7/baseline_dense/<N>/
set -uo pipefail; STAGE=${1:-all}; REPO=/home/user/dominion; cd $REPO
PYB=/opt/hv/bin/python; PYT=/opt/hv-ink/bin/python
SAFE=/work/ckpt/dense_native/dense_native_016000.safetensors; CKPT=/work/ckpt/dense_native/dense_native_016000.pth
CFG=$REPO/logs/fl7/baseline_dense/train_dense_native.json
N=PHerc0343P_20250511003658; W=/dev/shm/bl_$N; O=logs/fl7/baseline_dense/$N; SH=/dev/shm/shards/$N.npz; R=$W/sv.zarr
mkdir -p $W $O; log(){ echo "[$(date -u +%FT%TZ)] baseline_dense $N $*" | tee -a $O/pipeline.log; }
[ -f $SH ] || { log "shard missing $SH"; exit 1; }; [ -f $W/sv.ok ] || { log "sv missing"; exit 1; }
echo "d3d95dc41dcb24ed76b84b5e12ca5dae25d7fb34edf1dfbb93e0186f91e6fc6d  $SAFE" | sha256sum -c --quiet || { log "weights sha mismatch"; exit 1; }
[ -f $CKPT ] || $PYT - <<PY
import json, torch; from safetensors.torch import load_file
torch.save({"model": load_file("$SAFE"), "config": json.load(open("$CFG")), "step": 16000}, "$CKPT")
PY
run(){ # run <out.tif> <direction> [layer-start layer-end]
  local out=$1 dir=$2; shift 2; local extra=(); [ $# -ge 2 ] && extra=(--layer-start $1 --layer-end $2)
  [ -s $out ] && return 0; log "infer $(basename $out) dir=$dir ${extra[*]:-}"; local t0=$SECONDS
  ( cd $W && OMP_NUM_THREADS=4 $PYT -m vesuvius.ink_detection.inference.infer $R $CKPT $out --overlap 0.5 --blend-mode hann \
      --direction $dir --batch-size 4 --num-workers 1 --no-compile "${extra[@]}" > $W/$(basename $out .tif).log 2>&1 ) \
    || { tail -5 $W/$(basename $out .tif).log >> $O/pipeline.log; log "FAILED $(basename $out)"; return 1; }
  log "done $(basename $out) $((SECONDS-t0)) s"; }
score(){ $PYB tools/master/baseline_eval.py $SH $1 $O/$2.json --name $2 >> $O/pipeline.log 2>&1 || log "eval FAILED $2"; }
png(){ $PYB - <<PY
import tifffile,numpy as np,cv2; m=tifffile.imread('$1').astype(np.float32); m=m if m.max()<=1.0 else m/255.0
cv2.imwrite('$O/$2_q4.png',cv2.resize(np.clip(m*255,0,255).astype(np.uint8),None,fx=0.25,fy=0.25,interpolation=cv2.INTER_AREA))
PY
}
if [ $STAGE = default ] || [ $STAGE = all ]; then
  run $W/dense_fwd.tif forward && run $W/dense_rev.tif reverse || exit 1
  $PYB - <<PY
import tifffile,numpy as np; f=tifffile.imread('$W/dense_fwd.tif').astype(np.float32)/255; r=tifffile.imread('$W/dense_rev.tif').astype(np.float32)/255
tifffile.imwrite('$W/dense_mean.tif',((f+r)/2).astype(np.float32))
PY
  for v in fwd rev mean; do score $W/dense_$v.tif dense016k_$v; png $W/dense_$v.tif dense016k_$v; done
fi
if [ $STAGE = zavg ] || [ $STAGE = all ]; then
  for dir in forward reverse; do d=${dir:0:3}; tifs=()
    for win in 3:20 6:23 9:26 11:28; do t=$W/dense_${d}_z${win%%:*}-${win##*:}.tif; run $t $dir ${win%%:*} ${win##*:} || exit 1; tifs+=($t); done
    $PYB - $W/dense_${d}_zavg.tif "${tifs[@]}" <<'PY'
import sys,tifffile,numpy as np; out=sys.argv[1]; m=np.mean([tifffile.imread(t).astype(np.float32)/255 for t in sys.argv[2:]],axis=0); tifffile.imwrite(out,m.astype(np.float32))
PY
    for win in 3-20 6-23 9-26 11-28; do score $W/dense_${d}_z$win.tif dense016k_${d}_z$win; done
    score $W/dense_${d}_zavg.tif dense016k_${d}_zavg; png $W/dense_${d}_zavg.tif dense016k_${d}_zavg
  done
fi
log "STAGE $STAGE done"
