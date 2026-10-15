#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-7 item 3(ii), public-model comparison: Hecate 9.6 um (HF scrollprize/hecate @ 9cb86e500e944b11a06a7020403cde5dffb5bcb2,
# hecate_9.6um.pth sha256 809f4f10...) on the held-out validation segment's 8.64 um organizer surface volume, both directions,
# scored against the pseudo-labels at the validation shard's crop positions (baseline_eval.py: pixel AUC / AP, tile AUC).
# Recipe (model card): the render must be sampled at 9.6 um on all three axes and hecate.py refuses anything >2 % off, so the
# 8.64 um volume is resampled by 0.9 (trilinear, grid_mode) to 9.6 um first; inference = the released hecate.py unmodified
# (tools/master/hecate/), fp32, default XY stride 32 (half patch, Hann blend), central 16 of 28 planes, --reverse for the
# second direction, run through tools/master/hecate_tiled.py (resumable re-implementation of hecate.predict, byte-identical,
# see tiled_identity.json) because a container restart kills in-flight passes; the 2-D map is mapped back to the 8.64 um canvas (bilinear) for scoring. The NATIVE-spacing run
# (hecate_crops.py, shard crops fed as 9.6 um) is the mismatch experiment and is reported separately.
# usage: lane_hecate.sh <manifest index, default 18 = PHerc0343P entry 0>   outputs: logs/fl7/baseline_hecate/<scroll>_<seg14>/
set -uo pipefail; I=${1:-18}; REPO=/home/user/dominion; cd $REPO; BR=$(git rev-parse --abbrev-ref HEAD)
PYB=/opt/hv/bin/python; PYH=${PYH:-/work/hecate-venv/bin/python}; CKPT=/work/ckpt/hecate/hecate_9.6um.pth; HEC=tools/master/hecate/hecate.py; B=vesuvius-challenge-open-data
CKSHA=809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d
read SCROLL SEG SV < <($PYB -c "import json;x=json.load(open('logs/fl7_manifest.json'))[$I];print(x['scroll'],x['segment'],x['coarse_sv'])")
# W on disk, not tmpfs: /dev/shm is wiped by a container restart
N=${SCROLL}_${SEG:0:14}; W=/work/bl_$N; O=logs/fl7/baseline_hecate/$N; mkdir -p $W $O /work/own /dev/shm/shards /work/ckpt/hecate
log(){ echo "[$(date -u +%FT%TZ)] hecate $N $*" >> $O/pipeline.log; }
fail(){ log "FAILED: $1"; echo "$1" > $O/FAILED; exit 1; }
[ -f $O/DONE ] && exit 0
if [ ! -f $CKPT ] || ! echo "$CKSHA  $CKPT" | sha256sum -c --quiet; then log "fetch ckpt"
  curl -fsSL -o $CKPT "https://huggingface.co/scrollprize/hecate/resolve/9cb86e500e944b11a06a7020403cde5dffb5bcb2/hecate_9.6um.pth" || fail "ckpt fetch"
  echo "$CKSHA  $CKPT" | sha256sum -c --quiet || fail "ckpt sha"; fi
if [ ! -x $PYH ]; then log "venv"; uv venv /work/hecate-venv --python 3.11 -q && VIRTUAL_ENV=/work/hecate-venv uv pip install -q torch --index-url https://download.pytorch.org/whl/cpu && \
  VIRTUAL_ENV=/work/hecate-venv uv pip install -q 'numpy<3' 'zarr<3' numcodecs s3fs fsspec scipy tifffile opencv-python-headless pillow || fail "venv"; fi
SH=/dev/shm/shards/$N.npz
[ -f $SH ] || cp /work/shards/$N.npz $SH 2>/dev/null || timeout 2400 $PYB tools/master/build_data.py $SCROLL $SEG $SV $SH --stride 48 --max 600 > $W/build.log 2>&1 || fail "shard build"
mkdir -p /work/shards; cp -n $SH /work/shards/ 2>/dev/null
R=$W/sv.zarr
if [ ! -f $W/sv.ok ]; then rm -rf $R; log "fetch sv"
  $PYB - <<PY || fail "sv fetch"
import s3fs,os; fs=s3fs.S3FileSystem(anon=True); sv='$B/$SCROLL/segments/$SEG/surface-volumes/$SV'
os.makedirs('$R',exist_ok=True)
for f in ['.zattrs','.zgroup']: fs.get(sv+'/'+f,'$R/'+f)
fs.get(sv+'/0','$R/0',recursive=True); print('fetched')
PY
  touch $W/sv.ok; fi
read D H WW < <($PYB -c "import zarr;print(*zarr.open('$R',mode='r')['0'].shape)")
[ -f $W/sv_9.6um.npy ] || { log "resample 8.64->9.6 um"; $PYH -I tools/master/hecate_resample.py $R $W/sv_9.6um.npy $O/resample.json > $W/resample.log 2>&1 || fail "resample"; }
export OMP_NUM_THREADS=4
for dir in fwd rev; do flag=""; [ $dir = rev ] && flag="--reverse"
  if [ ! -f $W/hecate_9.6um_$dir.png ]; then log "hecate $dir"; t0=$SECONDS
    $PYH -I tools/master/hecate_tiled.py --checkpoint $CKPT --input $W/sv_9.6um.npy --spacing-um 9.6 --output $W/hecate_9.6um_$dir.png --state $W/st_$dir --batch-size 16 --flush 25 $flag > $W/hecate_$dir.log 2>&1 || { tail -5 $W/hecate_$dir.log > $O/hecate_${dir}_fail.log.tail; fail "hecate $dir"; }
    log "hecate $dir done $((SECONDS-t0)) s"; fi
  cp $W/hecate_9.6um_$dir.json $O/hecate_9.6um_$dir.settings.json
  $PYH -I tools/master/hecate_to_canvas.py $W/hecate_9.6um_$dir.png $H $WW $W/hecate_$dir.tif $O/hecate_${dir}_q4.png >> $O/pipeline.log 2>&1 || fail "canvas $dir"
done
$PYH -I tools/master/hecate_to_canvas.py mean $W/hecate_fwd.tif $W/hecate_rev.tif $W/hecate_mean.tif $O/hecate_mean_q4.png >> $O/pipeline.log 2>&1 || fail "mean map"
for v in fwd rev mean; do $PYB tools/master/baseline_eval.py $SH $W/hecate_$v.tif $O/hecate96_resampled_$v.json --name hecate96_resampled_$v >> $O/pipeline.log 2>&1 || fail "eval $v"; done
# mismatch experiment: native 8.64 um crops fed as 9.6 um (hecate.py's CLI refuses this spacing; done per patch in hecate_crops.py)
for dir in fwd rev; do flag=""; [ $dir = rev ] && flag="--reverse"
  [ -f $O/hecate96_native_crops_$dir.json ] || $PYH -I tools/master/hecate_crops.py $SH $CKPT $O/hecate96_native_crops_$dir.json $flag --name hecate96_native_crops_$dir >> $O/pipeline.log 2>&1 || fail "native crops $dir"; done
touch $O/DONE; log "DONE"
