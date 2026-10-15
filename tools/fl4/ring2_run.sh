#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-5 ring2 lane: grow one normal-grid patch from seeds_b070_PHerc0268[IDX] (band 0.70, z_frac 0.5), render C2-NT
# (31 layers, flip-normals, 8.64 um), ink_9um step-075000 forward+reverse (no TTA), sheet-piece map, informational radial
# gate; push PNG maps + tifxyz + JSON to logs/fl4t/ring2/i<IDX>/ on this branch. Idempotent; markers DONE / FAILED.
# usage: setsid nohup bash tools/fl4/ring2_run.sh <IDX> [GENS=60] > /work/ring2.out 2>&1 < /dev/null &
set -uo pipefail
RING=${RING:-ring2}; SEEDS=${SEEDS:-logs/fl4/seeds_b070_PHerc0268.json}; I=$1; GENS=${2:-60}; REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=$(git rev-parse --abbrev-ref HEAD); K=$REPO/tools/fl4; W=/work/fl4t/${RING}_i$I; ST=$W/state; mkdir -p $W $ST /work/own
O=$REPO/logs/fl4t/$RING/i$I; mkdir -p $O
CT=s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0268/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr
NGURL=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0268/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.normal-grids
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $O/pipeline.log; }
proxy_refresh(){ local p; p=$(grep -o 'http://127\.0\.0\.1:[0-9]\+' /root/.ccr/README.md 2>/dev/null | head -1)
  [ -n "$p" ] && [ "$p" != "${HTTPS_PROXY:-}" ] && export HTTPS_PROXY=$p https_proxy=$p DOCKER_HTTPS_PROXY=$p; return 0; }
push(){ flock /work/own/git.lock -c "git add logs/fl4t/$RING/i$I >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl4t $RING i$I: $1

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>'"
  for d in 2 4 8 16 32 64; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>>$W/push.err && return 0
    flock /work/own/git.lock git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d; done; log "WARN push failed: $1"; }
fail(){ log "FAILED: $1"; echo "$1" > $O/FAILED; push "FAILED $1"; exit 1; }
[ -f $O/DONE ] && exit 0; rm -f $O/FAILED; proxy_refresh
if [ ! -x /work/bin/vc ] || [ ! -x /opt/hv/bin/python ] || [ ! -x /opt/hv-ink/bin/python ] || [ ! -f $CKPT ] || ! docker info >/dev/null 2>&1; then
  log "env: setup_env.sh"; bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { tail -40 $W/setup_env.log > $O/env_fail.log.tail; fail "setup_env"; }; fi
[ -f $CKPT ] || fail "no ink_9um checkpoint after setup"
grep -q '/dev/shm:/dev/shm' /work/bin/vc || sed -i 's#-v /work:/work #-v /work:/work -v /dev/shm:/dev/shm #' /work/bin/vc
mkdir -p /dev/shm/ngrids/p0268; [ -f /dev/shm/ngrids/p0268/normal-grids-remote.json ] || printf '{"url":"%s"}' $NGURL > /dev/shm/ngrids/p0268/normal-grids-remote.json
D=$W/seg
if [ ! -f $ST/grow.ok ]; then
  read -r sx sy sz <<<"$(python3 -c "import json;print(*json.load(open('$REPO/$SEEDS'))['seeds'][$I]['seed_xyz'])")"
  printf '{"mode":"seed","step_size":20,"generations":%s,"min_area_cm":0.01,"voxelsize":8.640,"thread_limit":4,"cache_size":2000000000,"cache_root":"%s/cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10,"normal_grid_path":"/dev/shm/ngrids/p0268"}' $GENS $W > $O/grow_params.json
  rm -rf $W/grow; mkdir -p $W/grow; log "grow i$I seed ($sx $sy $sz) gens $GENS"; t0=$SECONDS
  /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $W/grow -p $O/grow_params.json -s $sx $sy $sz --segment-name ${RING}_i$I --skip-overlap-check > $W/grow.log 2>&1 || { tail -30 $W/grow.log > $O/grow.log.tail; fail "grow rc"; }
  tail -3 $W/grow.log > $O/grow.log.tail; x=$(find $W/grow -name x.tif | head -1); [ -n "$x" ] || fail "grow produced no surface"
  rm -rf $D; mkdir -p $D $O/tifxyz; cp $(dirname $x)/*.tif $(dirname $x)/meta.json $D/; cp $D/x.tif $D/y.tif $D/z.tif $D/meta.json $O/tifxyz/
  log "grow done $((SECONDS-t0)) s: $(grep 'generated surface' $W/grow.log)"; touch $ST/grow.ok; push "grow done"; fi
SEED_IDX=98 SHEET_JSON=$O/radial_gate_info.json /opt/hv/bin/python $K/sheetcheck.py $D >> $O/pipeline.log 2>&1 || log "radial gate (informational) errored"
R=$W/render.zarr
if [ ! -f $ST/render.ok ]; then proxy_refresh; rm -rf $R; log "render"
  ( cd $W && /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $D --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 \
    --voxel-size 8.64 --voxel-unit micrometer --flip-normals --cache-gb 3 --zarr-output $R > $W/render.log 2>&1 ) || { tail -5 $W/render.log > $O/render.log.tail; fail "render"; }
  touch $ST/render.ok; log "render ok"; fi
[ -f $O/${RING}_i${I}_pieces.json ] || { /opt/hv/bin/python $K/pieces.py $R $O/${RING}_i$I >> $O/pipeline.log 2>&1 || log "pieces errored"; push "pieces"; }
if [ ! -f $O/ink9um_forward.png ] || [ ! -f $O/ink9um_reverse.png ]; then log "ink_9um both"; t0=$SECONDS
  ( cd $W && OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $W/ink.tif --direction both --batch-size 4 --num-workers 1 --no-compile > $W/ink.log 2>&1 ) || { tail -5 $W/ink.log > $O/ink_fail.log.tail; fail "ink_9um"; }
  /opt/hv/bin/python - <<PY || fail "ink png"
import tifffile,numpy as np,cv2,json
for src,dst in [('$W/ink.tif','$O/ink9um_forward.png'),('$W/ink_reverse.tif','$O/ink9um_reverse.png')]:
    t=tifffile.imread(src).astype(np.float32); p=t/(255.0 if t.max()>1.5 else 1.0)
    cv2.imwrite(dst,np.clip(p*255,0,255).astype(np.uint8),[cv2.IMWRITE_PNG_COMPRESSION,6])
    json.dump({'src':src,'shape':list(t.shape),'min':float(t.min()),'max':float(t.max()),'frac_ge05':float((p>=0.5).mean()),'frac_ge08':float((p>=0.8).mean())},open(dst[:-4]+'.json','w'))
PY
  log "ink_9um done $((SECONDS-t0)) s"; fi
touch $O/DONE; push "DONE"; rm -rf $R
