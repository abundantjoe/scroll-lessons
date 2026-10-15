#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 First Letters push, PHerc0343, primary worker p4v-04 (seed lane 0). Brief tools/fl2/BRIEF_FL2.md (0e07b757).
# Derived from the fl-pherc0257 template at 54b29c96 (tools/sib/fl-pherc0257/pipeline.sh); grow, gate, render, infer and
# tiling commands are the template's. Changes (parameters and bookkeeping only; every one disclosed in fl2/STATUS.md):
#   SCROLL/CT/SURF/UMB/branch/paths/names; voxel size 8.640 um (this volume; template had 9.362); 48 candidate seeds,
#   this lane takes index % 2 == 0, NSEEDS=40; each segment goes grow -> render -> infer -> tile -> push before the next
#   seed (brief item 6); tiles under <SEG>/tiles_<model>/ with direction labels forward|reverse; manifest rows annotated
#   with the item-5 fields (annotate.py). OFFICIAL model only (DENSE withdrawn, DECL-FL-2-E1).
# Numbers only: no image, tile or CT slice is ever opened.
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ME=p4v-04; BR=claude/gifted-bell-gavnl5-sib-$ME
SCROLL=PHerc0343; VOLUME=20250521140437; LANE=0
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/$ME/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$ME/fl2/fl.py; ANN=$REPO/tools/sib/$ME/fl2/annotate.py
export FL_SCROLL=$SCROLL FL_VOX_UM=8.640
VOX=8.640
CT=s3://vesuvius-challenge-open-data/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0343/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0343 bucket (listed 2026-10-01): photos/ representations/predictions/{lasagna,surfaces}/ volumes/; no umbilicus, no segments
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NCAND=48; NSEEDS=40; MIN_AREA=16
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }
status() { echo "$(date -u +%FT%TZ) $*" >> $L/STATUS.md; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add logs/sib/$ME tools/sib/$ME >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "$ME: FL2 $SCROLL $1 (DECL-FL-2)

Numbers and file lists only; no image viewed.

Provenance: Project HERCULES | [id removed]"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>$W/push.err && return 0
    git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 1. environment ----
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then
  log "env: docker down after restart; re-running setup_env.sh (idempotent)"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env re-setup FAILED"; exit 1; }
fi
if [ ! -f $ST/env.ok ]; then
  log "env: setup_env.sh"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env FAILED (tail: $(tail -2 $W/setup_env.log | tr '\n' ' '))"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_grow_seg_from_seed --help >/dev/null 2>&1; /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "env: vesuvius infer not importable"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests, imagecodecs" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs imagecodecs
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > $L/env.txt
  touch $ST/env.ok; log "env: OK"; status "env OK"
fi

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; status "s3 list: $($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))") organizer tifxyz segments"; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
[ "$NORG" -eq 0 ] || { log "organizer segments appeared ($NORG): this script implements the auto path only; stop for re-planning"; status "STOP: $NORG organizer segments listed"; push "stop: organizer segments"; touch $L/PIPELINE_DONE; exit 0; }
SOURCE=auto
if [ ! -f $L/seeds.json ]; then
  $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; exit 1; }
  status "seeds: $($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))") of $NCAND candidate rays gave a seed"; push "seeds"
fi
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")

# ---- 3-4. render, infer, tiles for one segment and one model ----
process() {  # $1 name  $2 model label  $3 checkpoint  $4 checkpoint sha256  [$5 python for infer]
  local name=$1 mod=$2 ck=$3 cks=$4 ipy=${5:-/opt/hv-ink/bin/python}
  local d=$W/seg/$name O=$L/$name R=$W/render/$name.zarr P=$W/infer_$2/$name/$name.tif
  [ -f $O/DONE_$mod ] && return 0
  mkdir -p $O/tiles_$mod
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; status "render $name FAILED"; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_${mod}_$name.ok ]; then
    [ -d $R ] || { log "render zarr of $name missing"; rm -f $ST/render_$name.ok; status "infer $mod $name: render missing, retry"; return 1; }
    mkdir -p $W/infer_$mod/$name; log "infer $mod $name (both directions, no TTA)"
    OMP_NUM_THREADS=3 $ipy -m vesuvius.ink_detection.inference.infer $R $ck $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_${mod}_$name.log 2>&1 || { log "infer $mod $name FAILED"; tail -20 $W/infer_${mod}_$name.log > $O/infer_$mod.log.tail; status "infer $mod $name FAILED"; push "infer $mod $name failed"; return 1; }
    touch $ST/infer_${mod}_$name.ok
  fi
  # every prediction tif the official infer wrote: <name>.tif = forward, <name>_reverse.tif = reverse
  local nt=0 tf=0 PF dl
  for PF in $W/infer_$mod/$name/*.tif; do
    [ -f "$PF" ] || continue; nt=$((nt+1))
    case $(basename "$PF" .tif) in $name) dl=forward;; ${name}_reverse) dl=reverse;; *) dl=$(basename "$PF" .tif);; esac
    $PY $FL tiles $name $d $PF $dl $SOURCE $O/tiles_$mod $O/tiles_$mod/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $mod $dl FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name $mod: $nt prediction tifs, failure=$tf"; status "tiles $name $mod FAILED ($nt tifs)"; push "tiles $name $mod failed"; return 1; }
  $PY $ANN $O/tiles_$mod/manifest.json $SCROLL $VOLUME $name $mod $cks $L/grow/${name}_measure.json || { status "annotate $name $mod FAILED"; return 1; }
  ( cd $W/infer_$mod/$name && sha256sum *.tif > $O/prediction_sha256_$mod.txt )
  touch $O/DONE_$mod
  status "tiles $name $mod: $($PY -c "import json;t=json.load(open('$O/tiles_$mod/manifest.json'))['tiles'];print(len(t),'tiles (',sum(x['direction']=='forward' for x in t),'fwd /',sum(x['direction']=='reverse' for x in t),'rev )')")"
  log "segment $name $mod: tiles done"; push "tiles $name $mod"
}

DENSE=false   # DECL-FL-2-E1: the DENSE arm is withdrawn; OFFICIAL model only
run_models() {
  process $1 official $CKPT $CKPT_SHA || return 1
  if $DENSE; then process $1 dense $DCKPT $DCKPT_SHA $DPY || return 1; fi
  rm -rf $W/render/$1.zarr; rm -f $ST/render_$1.ok   # render zarr is regenerable; keep disk
}

# ---- grow -> render -> infer -> tile -> push, seed after seed ----
SEGS=(); FAIL=0; ntry=0
for ((i=LANE; i<NS; i+=2)); do
  [ $ntry -lt $NSEEDS ] || break
  name=pherc0343_${ME}_s$i; ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
  if [ ! -f $R ]; then
    mkdir -p $W/seg $L/grow; rm -rf $d
    read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$i]['seed_xyz'];print(*s)")"
    cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":$VOX,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
    cp $W/grow_params.json $L/grow_params.json
    log "grow $name seed ($sx $sy $sz)"
    t0=$(date +%s)
    cd $W
    OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $d -p $W/grow_params.json \
      -s $sx $sy $sz --segment-name $name --skip-overlap-check > $W/grow_$name.log 2>&1; rc=$?; cd "$REPO"
    tail -40 $W/grow_$name.log > $L/grow/$name.log.tail
    if [ ! -f $d/x.tif ]; then xs=$(find $d -name x.tif 2>/dev/null | head -1); [ -n "$xs" ] && cp $(dirname $xs)/*.tif $(dirname $xs)/meta.json $d/ 2>/dev/null; fi
    ok=false; area=0; sc=null
    if [ -f $d/x.tif ]; then
      $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
      area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
      /work/bin/vc vc_tifxyz_selfcross $d -o $W/selfcross_$name.json > /dev/null 2>&1; cp $W/selfcross_$name.json $L/grow/${name}_selfcross.json 2>/dev/null
      sc=$($PY -c "import json;r=json.load(open('$W/selfcross_$name.json'));n=sum(c['transverse'] for c in r['census']);print(n if (n==0)==bool(r['clean_of_transverse_self_intersection']) else 'null')" 2>/dev/null || echo null)
      [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
    fi
    echo "{\"segment\":\"$name\",\"seed_index\":$i,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
    if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/
      ( cd $L/$name/tifxyz && sha256sum x.tif y.tif z.tif meta.json > ../tifxyz_sha256.txt ); fi
    log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; status "grow $name: rc=$rc area_cm2=$area selfx=$sc kept=$ok"; push "grow $name"
  fi
  if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
    [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/{x,y,z}.tif $L/$name/tifxyz/meta.json $d/; }
    SEGS+=("$name"); run_models $name || FAIL=$((FAIL+1))
  fi
done
log "lane $LANE pass: ${#SEGS[@]} kept segments, $FAIL with failed units, $ntry seeds attempted"
if [ $FAIL -eq 0 ]; then
  status "PASS COMPLETE (official only, DECL-FL-2-E1): ${#SEGS[@]} segments"; touch $L/PIPELINE_DONE
  push "pass complete"
else
  status "PASS INCOMPLETE: $FAIL segments with failed units; watchdog retries"; push "pass incomplete"; exit 1
fi
