#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-2 First Letters push, PHerc0175B, worker fl-pherc0175b = primary (seed lane 0). Template fl-pherc0257@54b29c96,
# parameters only (tools/fl2/BRIEF_FL2.md items 1-6). Reused DECL-FL-1 segments (same gate) are rendered first.
# Units: env -> list -> seeds -> grow sK (auto path) -> per segment: render -> infer -> tiles (+push).
# Resume: every unit leaves a marker under logs/sib/fl-pherc0175b/fl2 (committed) or /work/fl2/state; finished units are skipped.
# Launch: setsid nohup bash tools/sib/fl-pherc0175b/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-fl-pherc0175b
SCROLL=PHerc0175B; VOLUME=20250521125822; VOX=8.64; LANE=0; ME=fl-pherc0175b
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/fl-pherc0175b/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/fl-pherc0175b/fl2/fl.py; export FL_SCROLL=PHerc0175B FL_VOX=8.64 FL_VOLUME=20250521125822
CT=s3://vesuvius-challenge-open-data/PHerc0175B/volumes/20250521125822-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0175B/representations/predictions/surfaces/20250521125822-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0175B has no organizer umbilicus or segments (logs/sib/fl-pherc0175b/listing.json: photos/ representations/predictions/surfaces/ volumes/); fl.py seeds uses the CT-mask centroid axis
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=40; MIN_AREA=16; NSEEDCAND=48
REUSE="auto_pherc0175b_c00 auto_pherc0175b_c03"   # DECL-FL-1 segments that passed the same gate (logs/sib/fl-pherc0175b/grow/cand_{0,3}.json)
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  echo "$(date -u +%FT%TZ) fl-pherc0175b fl2: $1" >> $L/STATUS.md
  cd "$REPO"; git add logs/sib/fl-pherc0175b/fl2 tools/sib/fl-pherc0175b/fl2 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "fl-pherc0175b fl2: $1

DECL-FL-2 compute worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Xja7sXTwwPXHrR7n2qJdo4

Provenance: Project HERCULES | [id removed]"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>$W/push.err && return 0
    git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 1. environment ----
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then   # container restart: dockerd is gone, the env marker is not
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
  touch $ST/env.ok; log "env: OK"
fi

# ---- 3-4. render, infer, tiles per segment ----
do_seg() {  # render -> infer (official) -> tiles for one segment; returns 0 when DONE
  local name=$1 d O R P nt tf PF dl area
  d=$W/seg/$name; O=$L/$name; mkdir -p $O/tiles_official
  [ -f $O/DONE ] && return 0
  R=$W/render/$name.zarr; P=$W/infer/$name/$name.tif
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    cd $W   # the render app writes a copy of the segmentation into its working directory; keep it out of the repo
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 8.64 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; cd "$REPO"; rm -rf $R; push "render $name failed"; return 1; }
    cd "$REPO"; touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_$name.ok ]; then
    mkdir -p $W/infer/$name; log "infer $name (both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_$name.log 2>&1 || { log "infer $name FAILED"; tail -20 $W/infer_$name.log > $O/infer.log.tail; push "infer $name failed"; return 1; }
    touch $ST/infer_$name.ok
  fi
  # every prediction tif the official infer wrote (both directions); direction label = file stem
  nt=0; tf=0
  for PF in $W/infer/$name/*.tif; do
    [ -f "$PF" ] || continue; nt=$((nt+1)); dl=$(basename "$PF" .tif)
    case "$dl" in *_reverse) dl=reverse;; *) dl=forward;; esac
    area=$($PY -c "import json;print(json.load(open('$O/measure.json'))['area_cm2'])" 2>/dev/null || echo nan)
    FL_MODEL=official FL_MODEL_SHA=$CKPT_SHA FL_AREA=$area $PY $FL tiles $name $d $PF $dl $SOURCE $O/tiles_official $O/tiles_official/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $dl FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name: $nt prediction tifs, failure=$tf"; push "tiles $name failed"; return 1; }
  ( cd $W/infer/$name && sha256sum *.tif > $O/prediction_sha256.txt )
  touch $O/DONE; log "segment $name: tiles done"
  push "tiles $name official: $($PY -c "import json;t=json.load(open('$O/tiles_official/manifest.json'))['tiles'];print(len(t),'tiles')")"
  rm -rf $R   # render zarr is regenerable; keep disk
  return 0
}

# ---- 1b. reused DECL-FL-1 segments (same gate: 0 transverse self-crossings, >= 16 cm^2), rendered first ----
for name in $REUSE; do
  src=$REPO/logs/sib/fl-pherc0175b/$name/mesh; d=$W/seg/$name; O=$L/$name
  [ -f $src/x.tif ] || { log "reuse $name: no mesh in repo"; continue; }
  if [ ! -f $O/tifxyz/x.tif ]; then
    mkdir -p $d $O/tifxyz; cp $src/x.tif $src/y.tif $src/z.tif $src/meta.json $d/; cp $d/* $O/tifxyz/
    cp $REPO/logs/sib/fl-pherc0175b/$name/geometry.json $O/declfl1_geometry.json 2>/dev/null
    $PY $FL measure $d $O/measure.json >> $L/pipeline.log 2>&1
    push "reuse $name (DECL-FL-1 auto segment, gate passed; area $($PY -c "import json;print(round(json.load(open('$O/measure.json'))['area_cm2'],2))") cm2)"
  fi
  [ -f $d/x.tif ] || { mkdir -p $d; cp $O/tifxyz/* $d/; }
  SOURCE=auto; do_seg $name
done

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
SEGS=()
if [ "$NORG" -gt 0 ]; then
  SOURCE=organizer; log "source: organizer ($NORG tifxyz segments); all, largest first, ranks with rank % 2 == $LANE"
  for pre in $($PY -c "import json;[print(s['prefix']) for i,s in enumerate(json.load(open('$L/s3_list.json'))['tifxyz_segments']) if i%2==$LANE]"); do
    name=$(basename "$pre"); d=$W/seg/$name; mkdir -p $d
    for f in x.tif y.tif z.tif meta.json mask.tif; do
      [ -s $d/$f ] || curl -fsS -o $d/$f "$HTTPB/$pre/$f" || rm -f $d/$f
    done
    [ -s $d/x.tif ] && SEGS+=("$name")
  done
else
  SOURCE=auto; log "source: auto (no organizer tifxyz segments in the bucket)"
  if [ ! -f $L/seeds.json ]; then
    $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NSEEDCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; exit 1; }
    push "seeds"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  i=0; ntry=0
  while [ $i -lt $NS ] && [ $ntry -lt $NSEEDS ]; do
    if [ $((i % 2)) -ne $LANE ]; then i=$((i+1)); continue; fi   # seed lane: index % 2 == LANE
    name=pherc0175b_${ME}_s$i; i=$((i+1)); ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
    if [ ! -f $R ]; then
      mkdir -p $W/seg $L/grow; rm -rf $d
      read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$((i-1))]['seed_xyz'];print(*s)")"
      cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":8.64,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
      cp $W/grow_params.json $L/grow_params.json
      log "grow $name seed ($sx $sy $sz)"
      t0=$(date +%s)
      cd $W   # the grow app also writes a copy into its working directory; keep it out of the repo
      OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $d -p $W/grow_params.json \
        -s $sx $sy $sz --segment-name $name --skip-overlap-check > $W/grow_$name.log 2>&1; rc=$?; cd "$REPO"
      tail -40 $W/grow_$name.log > $L/grow/$name.log.tail
      # tolerate grow writing into a named subdirectory of -t
      if [ ! -f $d/x.tif ]; then xs=$(find $d -name x.tif 2>/dev/null | head -1); [ -n "$xs" ] && cp $(dirname $xs)/*.tif $(dirname $xs)/meta.json $d/ 2>/dev/null; fi
      ok=false; area=0; sc=null
      if [ -f $d/x.tif ]; then
        $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
        area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
        /work/bin/vc vc_tifxyz_selfcross $d -o $W/selfcross_$name.json > /dev/null 2>&1; cp $W/selfcross_$name.json $L/grow/${name}_selfcross.json 2>/dev/null
        # vc_tifxyz_selfcross report: 'census' = one entry per quad triangulation; count transverse contacts over both,
        # and require the tool's own clean_of_transverse_self_intersection verdict to agree (else null = not kept)
        sc=$($PY -c "import json;r=json.load(open('$W/selfcross_$name.json'));n=sum(c['transverse'] for c in r['census']);print(n if (n==0)==bool(r['clean_of_transverse_self_intersection']) else 'null')" 2>/dev/null || echo null)
        [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
      fi
      echo "{\"segment\":\"$name\",\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
      if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; cp $L/grow/${name}_measure.json $L/$name/measure.json; fi
      log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; push "grow $name"
    fi
    if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
      [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
      SEGS+=("$name"); do_seg $name   # segment after segment: render -> infer -> tiles right after its grow
    fi
  done
fi
log "segments ($SOURCE): ${SEGS[*]:-none}; retrying any not DONE"
for name in $REUSE "${SEGS[@]}"; do [ -f $W/seg/$name/x.tif ] && do_seg $name; done
SEGS=($REUSE "${SEGS[@]}")

NDONE=0; for name in "${SEGS[@]}"; do [ -f $L/$name/DONE ] && NDONE=$((NDONE+1)); done
if [ ${#SEGS[@]} -gt 0 ] && [ $NDONE -eq ${#SEGS[@]} ]; then
  log "PIPELINE COMPLETE: source=$SOURCE segments=${SEGS[*]}"; touch $L/PIPELINE_DONE; push "pipeline complete"
else
  log "PIPELINE INCOMPLETE: $NDONE of ${#SEGS[@]} segments done; watchdog retries"; push "pipeline incomplete"; exit 1
fi
