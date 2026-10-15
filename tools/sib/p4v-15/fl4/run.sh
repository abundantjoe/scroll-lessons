#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4-A1 worker pipeline: inner-winding seeds of PHerc0268 / PHerc0490A -> vc_grow_seg_from_seed -> FL-2 geometry gates
# -> C2-NT render (31 slices, --flip-normals) -> Grand Prize TimeSformer variant B (x voxel/7.91), forward then reverse -> FL-2
# tiler (2 x 2 cm) + vertex-grid block means (seam checks) -> push -> drop the render. Numbers only; no image is ever viewed.
# Config: /work/fl4/conf.sh (ME SCROLL LANE NLANES), written by go.sh. Idempotent via marker files; the watchdog re-runs it.
set -uo pipefail
source /work/fl4/conf.sh
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
K=$REPO/tools/sib/$ME/fl4; BR=claude/gifted-bell-gavnl5-sib-$ME; MAIN=origin/claude/gifted-bell-gavnl5
W=/work/fl4; ST=$W/state; L=$REPO/logs/sib/$ME/fl4/$SCROLL; mkdir -p $W $ST $L /work/own
PY=/opt/hv/bin/python; GPY=/opt/gp/bin/python; FL=$K/fl4.py; HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
case $SCROLL in
  PHerc0268)  VOLUME=20251110183117-8.640um-1.2m-116keV-masked; SURFN=20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr;;
  PHerc0490A) VOLUME=20250521151210-8.640um-1.2m-116keV-masked; SURFN=20250521151210-surface-20260413222639-surface-m7-L0-th0.2.zarr;;
  *) echo "unknown scroll $SCROLL"; exit 2;;
esac
VOX=8.640; CT=s3://vesuvius-challenge-open-data/$SCROLL/volumes/$VOLUME.zarr/
SURF=s3://vesuvius-challenge-open-data/$SCROLL/representations/predictions/surfaces/$SURFN/
GPSHA=490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488; MIN_AREA=4; GENS=100
export FL_SCROLL=$SCROLL FL_VOX_UM=$VOX FL_VOLUME=$VOLUME FL_DECL=DECL-FL-4-A1 FL_MODEL=GP_timesformer FL_MODEL_SHA=$GPSHA
export FL_CHAIN="C2-NT: vc_render_tifxyz -n 31 --flip-normals at 8.640 um; GP TimeSformer (organizer HF scrollprize/timesformer_GP_scroll1 @61b81d31, Youssef Nader / 2023 Grand Prize team, MIT) via villa 41701aa; layers 2..27; variant B x$(python3 -c "print(round($VOX/7.91,4))"); window 64 stride 32 fp32; Hann blend; sigmoid->0-255"
log() { echo "[$(date -u +%FT%TZ)] $*" >> $L/pipeline.log; }
push() {
  echo "$(date -u +%FT%TZ) $ME $SCROLL: $1" >> $L/STATUS.md
  flock /work/own/git.lock -c "git add logs/sib/$ME/fl4 tools/sib/$ME/fl4 >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m '$ME FL4 $SCROLL: $1

DECL-FL-4-A1 fleet unit (numbers and file lists only; no image viewed).

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'"
  for d in 2 4 8 16 32; do
    flock /work/own/git.lock git push -q -u origin HEAD:$BR 2>>$W/push.err && return 0
    flock /work/own/git.lock git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed: $1"
}
# --- environment: FL-2 env (vc, /opt/hv) then the GP env ---
if [ ! -x /work/bin/vc ] || ! docker info >/dev/null 2>&1; then
  log "env: setup_env.sh"; bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env FAILED: $(tail -2 $W/setup_env.log | tr '\n' ' ')"; push "env failed"; exit 1; }
fi
$PY -c "import numcodecs, cv2, tifffile, requests" 2>/dev/null || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs opencv-python-headless tifffile requests
if [ ! -f $ST/gp.ok ]; then
  bash $K/setup_gp.sh > $W/setup_gp.log 2>&1 || { log "GP env FAILED: $(tail -3 $W/setup_gp.log | tr '\n' ' ')"; push "GP env failed"; exit 1; }
  { echo "villa_gp $(git -C /work/villa_gp rev-parse HEAD)"; echo "gp_model_sha256 $GPSHA"; $GPY -c "import torch;print('torch',torch.__version__)"; tail -2 $W/setup_gp.log; } > $L/env.txt
  touch $ST/gp.ok; push "GP env ok"
fi
# --- seeds: the orchestrator's fixed inner-first list (DECL-FL-4-A1 item 3) ---
if [ ! -s $L/seeds_inner.json ]; then
  git fetch -q origin claude/gifted-bell-gavnl5; git show $MAIN:logs/fl4/seeds_inner_$SCROLL.json > $L/seeds_inner.json || { log "no seed list"; exit 1; }
  push "seed list ($(sha256sum $L/seeds_inner.json | cut -c1-12))"
fi
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds_inner.json'))['seeds']))")
AX=$REPO/logs/sib/$ME/fl4/$SCROLL/seeds_inner.json   # carries axis_points
sl=$(echo $SCROLL | tr A-Z a-z)
for ((i=LANE; i<NS; i+=NLANES)); do
  name=${sl}_${ME}_i$i; d=$W/seg/$name; O=$L/$name; G=$L/grow/$name.json; mkdir -p $L/grow
  [ -f $O/DONE ] && continue
  if [ ! -f $G ]; then
    rm -rf $d; mkdir -p $W/seg
    read -r sx sy sz <<<"$($PY -c "import json;print(*json.load(open('$L/seeds_inner.json'))['seeds'][$i]['seed_xyz'])")"
    cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":$GENS,"min_area_cm":1.0,"voxelsize":$VOX,"thread_limit":4,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
    cp $W/grow_params.json $L/grow_params.json; log "grow $name seed ($sx $sy $sz)"; t0=$(date +%s)
    ( cd $W && OMP_NUM_THREADS=4 timeout 3h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $d -p $W/grow_params.json \
        -s $sx $sy $sz --segment-name $name --skip-overlap-check > $W/grow_$name.log 2>&1 ); rc=$?
    tail -40 $W/grow_$name.log > $L/grow/$name.log.tail
    if [ ! -f $d/x.tif ]; then xs=$(find $d -name x.tif 2>/dev/null | head -1); [ -n "$xs" ] && cp $(dirname $xs)/*.tif $(dirname $xs)/meta.json $d/ 2>/dev/null; fi
    ok=false; area=0; sc=null
    if [ -f $d/x.tif ]; then
      $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
      area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])" 2>/dev/null || echo 0)
      /work/bin/vc vc_tifxyz_selfcross $d -o $W/selfcross_$name.json > /dev/null 2>&1; cp $W/selfcross_$name.json $L/grow/${name}_selfcross.json 2>/dev/null
      sc=$($PY -c "import json;r=json.load(open('$W/selfcross_$name.json'));n=sum(c['transverse'] for c in r['census']);print(n if (n==0)==bool(r['clean_of_transverse_self_intersection']) else 'null')" 2>/dev/null || echo null)
      [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
    fi
    echo "{\"segment\":\"$name\",\"seed_index\":$i,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $G
    if $ok; then mkdir -p $O/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $O/tifxyz/; fi
    log "grow $name: rc=$rc area=$area selfx=$sc kept=$ok"; push "grow $name area=$area selfx=$sc kept=$ok"
  fi
  [ "$($PY -c "import json;print(json.load(open('$G'))['kept'])")" = "True" ] || continue
  [ -f $d/x.tif ] || { mkdir -p $d; cp $O/tifxyz/* $d/; }
  R=$W/render/$name.zarr
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $W/render; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $L/grow/${name}_render.log.tail; push "render $name failed"; continue; }
    touch $ST/render_$name.ok
  fi
  mkdir -p $W/pred $O/tiles_gp_B $O/vgrid; fail=0
  for dir in forward reverse; do
    P=$W/pred/${name}_B_$dir.tif
    if [ ! -f $ST/gp_${name}_$dir.ok ]; then
      log "GP B $dir $name"; s=$(date -u +%FT%TZ)
      FL_VOX_UM=$VOX OMP_NUM_THREADS=4 $GPY $K/gp_infer.py run $R $P B $dir > $W/gp_${name}_$dir.log 2>&1; rc=$?
      echo "{\"step\":\"gp_infer\",\"segment\":\"$name\",\"variant\":\"B\",\"direction\":\"$dir\",\"utc_start\":\"$s\",\"utc_end\":\"$(date -u +%FT%TZ)\",\"exit\":$rc,\"result\":$(tail -1 $W/gp_${name}_$dir.log | grep '^{' || echo null)}" >> $L/runs.jsonl
      [ $rc -eq 0 ] || { log "GP $name $dir FAILED rc=$rc"; tail -20 $W/gp_${name}_$dir.log > $O/gp_fail_$dir.log.tail; push "GP $name $dir failed"; fail=1; break; }
      touch $ST/gp_${name}_$dir.ok
    fi
    AREA=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
    FL_AREA_CM2=$AREA $PY $FL tiles $name $d $P $dir auto-inner $O/tiles_gp_B $O/tiles_gp_B/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $dir FAILED"; fail=1; break; }
    $PY $FL vgrid $d $P $O/vgrid/B_$dir.tif $AX > $O/vgrid/B_$dir.json 2>>$L/pipeline.log || log "vgrid $name $dir failed (non-fatal)"
    push "GP B $dir $name: $($PY -c "import json;print(len([t for t in json.load(open('$O/tiles_gp_B/manifest.json'))['tiles'] if t['direction']=='$dir']))") tiles"
  done
  [ $fail -eq 0 ] || continue
  ( cd $W/pred && sha256sum ${name}_B_*.tif > $O/prediction_sha256.txt ); touch $O/DONE; push "segment $name done"
  rm -rf $R $W/pred/${name}_B_*.tif   # regenerable; disk
done
log "lane pass complete"; touch $L/ALL_DONE; push "lane complete"
