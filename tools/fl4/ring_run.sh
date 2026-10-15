#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# OWNER-ORDER-FL4-B ring lane: grow one sheet-following patch (normal grids, DECL-FL-4-A6) from seeds_inner_PHerc0268[IDX],
# apply the DECL-FL-4-A5 sheet gate, render (31 layers, flip-normals, 8.64 um), GP variant B forward + reverse, push PNG ink
# maps + tifxyz + gate JSON to logs/fl4t/<RING>/i<IDX>/ on this branch. Idempotent. Markers: DONE or FAILED in that dir.
# usage: setsid nohup bash tools/fl4/ring_run.sh <RING> <IDX> [GENS=60] > /work/ring.out 2>&1 &
set -uo pipefail
RING=$1; I=$2; GENS=${3:-60}; REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=$(git rev-parse --abbrev-ref HEAD); K=$REPO/tools/fl4; W=/work/fl4t/i$I; ST=$W/state; mkdir -p $W $ST /work/own
O=$REPO/logs/fl4t/$RING/i$I; mkdir -p $O
CT=s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0268/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr
NGURL=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0268/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.normal-grids
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $O/pipeline.log; }
proxy_refresh(){ local p; p=$(grep -o 'http://127\.0\.0\.1:[0-9]\+' /root/.ccr/README.md 2>/dev/null | head -1)
  [ -n "$p" ] && [ "$p" != "${HTTPS_PROXY:-}" ] && export HTTPS_PROXY=$p https_proxy=$p DOCKER_HTTPS_PROXY=$p; return 0; }
push(){ local d; flock /work/own/git.lock -c "git add logs/fl4t/$RING/i$I >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl4t $RING i$I: $1

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'"
  for d in 2 4 8 16 32 64; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>>$W/push.err && return 0
    flock /work/own/git.lock git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d; done; log "WARN push failed: $1"; }
fail(){ log "FAILED: $1"; echo "$1" > $O/FAILED; push "FAILED $1"; exit 1; }
[ -f $O/DONE ] && exit 0; rm -f $O/FAILED; proxy_refresh
if [ ! -x /work/bin/vc ] || [ ! -x /opt/hv/bin/python ] || [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || ! docker info >/dev/null 2>&1; then
  log "env: setup_env.sh"; bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { tail -40 $W/setup_env.log > $O/env_fail.log.tail; fail "setup_env"; }; fi
grep -q '/dev/shm:/dev/shm' /work/bin/vc || sed -i 's#-v /work:/work #-v /work:/work -v /dev/shm:/dev/shm #' /work/bin/vc
GPY=/opt/gp/bin/python
if [ ! -f $ST/gp.ok ]; then
  if [ -x /opt/hv-ink/bin/python ] && [ -f /work/gp/model.safetensors ] && [ -d /work/villa_gp ]; then GPY=/opt/hv-ink/bin/python
  else bash $K/setup_gp.sh > $W/setup_gp.log 2>&1 || { tail -40 $W/setup_gp.log > $O/env_fail.log.tail; fail "setup_gp"; }; fi
  echo $GPY > $ST/gp.ok; log "GP env ok ($GPY)"; push "env ok"; fi
GPY=$(cat $ST/gp.ok)
mkdir -p /dev/shm/ngrids/p0268; [ -f /dev/shm/ngrids/p0268/normal-grids-remote.json ] || printf '{"url":"%s"}' $NGURL > /dev/shm/ngrids/p0268/normal-grids-remote.json
D=$W/seg
if [ ! -f $ST/grow.ok ]; then
  read -r sx sy sz <<<"$(python3 -c "import json;print(*json.load(open('$REPO/logs/fl4/seeds_inner_PHerc0268.json'))['seeds'][$I]['seed_xyz'])")"
  printf '{"mode":"seed","step_size":20,"generations":%s,"min_area_cm":0.01,"voxelsize":8.640,"thread_limit":4,"cache_size":2000000000,"cache_root":"%s/cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10,"normal_grid_path":"/dev/shm/ngrids/p0268"}' $GENS $W > $O/grow_params.json
  rm -rf $W/grow; mkdir -p $W/grow; log "grow i$I seed ($sx $sy $sz) gens $GENS"; t0=$SECONDS
  /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $W/grow -p $O/grow_params.json -s $sx $sy $sz --segment-name r_i$I --skip-overlap-check > $W/grow.log 2>&1 || { tail -30 $W/grow.log > $O/grow.log.tail; fail "grow rc"; }
  tail -3 $W/grow.log > $O/grow.log.tail; x=$(find $W/grow -name x.tif | head -1); [ -n "$x" ] || fail "grow produced no surface"
  rm -rf $D; mkdir -p $D; cp $(dirname $x)/*.tif $(dirname $x)/meta.json $D/; mkdir -p $O/tifxyz; cp $D/x.tif $D/y.tif $D/z.tif $D/meta.json $O/tifxyz/
  log "grow done $((SECONDS-t0)) s: $(grep 'generated surface' $W/grow.log)"; touch $ST/grow.ok; push "grow done"; fi
if [ ! -f $ST/gate.ok ]; then
  SEED_IDX=$I SHEET_JSON=$O/sheet_gate.json /opt/hv/bin/python $K/sheetcheck.py $D >> $O/pipeline.log 2>&1 || fail "sheetcheck error"
  if ! python3 -c "import json,sys;sys.exit(0 if json.load(open('$O/sheet_gate.json'))['pass'] else 1)"; then
    # DECL-FL-4-A7-E2: marginal tier (median|cos| >= 0.45 and spread < 4 mm/cm) is rendered and inked, flagged MARGINAL
    if [ "${RING_GATE:-strict}" = marginal ] && python3 -c "import json,sys;g=json.load(open('$O/sheet_gate.json'));sys.exit(0 if g['median_cos']>=0.45 and g['spread_mm_per_cm']<4.0 else 1)"; then
      echo "median|cos|>=0.45 and spread<4 mm/cm; strict A5 gate failed" > $O/MARGINAL; log "gate MARGINAL tier (A7-E2)"
    else push "sheet gate FAIL"; fail "sheet gate (DECL-FL-4-A5)"; fi
  fi
  touch $ST/gate.ok; push "sheet gate pass"; fi
R=$W/render.zarr
if [ ! -f $ST/render.ok ]; then proxy_refresh; rm -rf $R; log "render"
  ( cd $W && /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $D --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 \
    --voxel-size 8.64 --voxel-unit micrometer --flip-normals --cache-gb 3 --zarr-output $R > $W/render.log 2>&1 ) || { tail -5 $W/render.log > $O/render.log.tail; fail "render"; }
  touch $ST/render.ok; log "render ok"; fi
for dir in forward reverse; do [ -f $O/gp_B_$dir.png ] && continue; log "GP B $dir"
  FL_VOX_UM=8.64 OMP_NUM_THREADS=4 $GPY $K/gp_infer.py run $R $W/gp_$dir.tif B $dir > $W/gp_$dir.log 2>&1 || { tail -5 $W/gp_$dir.log > $O/gp_fail.log.tail; fail "GP $dir"; }
  /opt/hv/bin/python -c "
import tifffile,numpy as np,cv2
p=tifffile.imread('$W/gp_$dir.tif').astype(np.float32); p=p/(255.0 if p.max()>1.5 else 1.0)
cv2.imwrite('$O/gp_B_$dir.png',np.clip(p*255,0,255).astype(np.uint8),[cv2.IMWRITE_PNG_COMPRESSION,9])" || fail "png $dir"
  tail -1 $W/gp_$dir.log > $O/gp_$dir.json; push "GP B $dir"; done
touch $O/DONE; push "DONE"; rm -rf $R
