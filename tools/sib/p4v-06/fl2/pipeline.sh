#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 worker p4v-06, PHerc0800 primary (seed lane 0). Base: fl-pherc0257 fl2 adaptation at 9c8af0a5 of the 54b29c96 template;
# changes are parameters plus brief item 2 (ALL organizer segments, even ranks, before auto-grow) and item 5 (tifxyz kept).
# First Letters screen, PHerc0800 (OWNER-STANDING-ORDER-5: detached, idempotent, pushes after every unit).
# Units: env -> list -> seeds -> grow sK (auto path) -> per segment: render -> infer -> tiles (+push).
# Resume: every unit leaves a marker under logs/sib/p4v-06/fl2 (committed) or /work/fl2/state; finished units are skipped.
# Launch: setsid nohup bash tools/sib/p4v-06/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-p4v-06
SCROLL=PHerc0800
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/p4v-06/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/p4v-06/fl2/fl.py; export FL_SCROLL=PHerc0800 FL_VOLUME=20250521135224
CT=s3://vesuvius-challenge-open-data/PHerc0800/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0800/representations/predictions/surfaces/20250521135224-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0800 has no organizer umbilicus (bucket listing 2026-10-01: photos/ representations/predictions/{lasagna,surfaces}/ segments/ volumes/); fl.py seeds uses the CT-mask centroid axis
VOX=8.640  # PHerc0800 volume voxel size (volume name 20250521135224-8.640um-...)
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=40; MIN_AREA=16; LANE=0   # DECL-FL-2: primary = seed lane 0 (even seed indices); 40 attempts max
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add logs/sib/p4v-06/fl2 tools/sib/p4v-06/fl2 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "p4v-06 fl2 PHerc0800: $1

DECL-FL-2 compute worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FmUFzddXeuc7X8o9nFUkyU
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
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > $L/env.txt
  touch $ST/env.ok; log "env: OK"
fi

# ---- 3-4. render, infer, tiles for one segment (called as soon as the segment exists; DECL-FL-2 item 6) ----
process_seg() {
  local name=$1 d O R P nt tf PF dl
  d=$W/seg/$name; O=$L/$name; mkdir -p $O/tiles_official
  [ -f $O/DONE ] && return 0
  R=$W/render/$name.zarr; P=$W/infer/$name/$name.tif
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok
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
    $PY $FL tiles $name $d $PF $dl ${SRC[$name]} $O/tiles_official $O/tiles_official/manifest.json official $CKPT_SHA >> $L/pipeline.log 2>&1 || { log "tiles $name $dl FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name: $nt prediction tifs, failure=$tf"; push "tiles $name failed"; return 1; }
  ( cd $W/infer/$name && sha256sum *.tif > $O/prediction_sha256.txt )
  touch $O/DONE; log "segment $name: tiles done"; push "tiles $name"
  rm -rf $R   # render zarr is regenerable; keep disk
}

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
SEGS=(); ORGNEW=(); declare -A SRC
if [ "$NORG" -gt 0 ]; then
  # DECL-FL-2 item 2: ALL organizer tifxyz segments, largest first, this lane takes ranks with rank % 2 == LANE.
  # Each organizer segment dir also holds copies under mesh/intermediate/; only the main mesh/<id>.tifxyz is a segment.
  log "source: organizer ($NORG tifxyz dirs listed); main tifxyz only, ranks % 2 == $LANE"
  for rp in $($PY -c "import json;s=[x for x in json.load(open('$L/s3_list.json'))['tifxyz_segments'] if '/intermediate/' not in x['prefix']];s.sort(key=lambda x:(-x['x_tif_bytes'],x['prefix']));[print(str(k)+'|'+x['prefix']) for k,x in enumerate(s) if k%2==$LANE]"); do
    k=${rp%%|*}; pre=${rp#*|}; name=pherc0800_p4v-06_org$k; d=$W/seg/$name; mkdir -p $d
    for f in x.tif y.tif z.tif meta.json mask.tif; do
      [ -s $d/$f ] || curl -fsS -o $d/$f "$HTTPB/$pre/$f" || rm -f $d/$f
    done
    if [ -s $d/x.tif ] && [ -s $d/meta.json ]; then
      SEGS+=("$name"); SRC[$name]=organizer
      ORGNEW+=("$name")
      if [ ! -f $L/$name/tifxyz/x.tif ]; then
        mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/
        echo "{\"segment\":\"$name\",\"rank\":$k,\"organizer_prefix\":\"$pre\"}" > $L/$name/source.json
        $PY $FL measure $d $L/$name/measure.json >> $L/pipeline.log 2>&1
        log "organizer $name = $pre"; push "organizer segment $name"
      fi
    else log "organizer $name download FAILED ($pre)"; fi
  done
fi
for name in "${ORGNEW[@]}"; do process_seg $name || true; done   # organizer segments before any auto-grow
if true; then
  SOURCE=auto; log "auto-grow (lane $LANE, up to $NSEEDS attempts) after organizer segments"
  if [ ! -f $L/seeds.json ]; then
    $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB 48 $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; exit 1; }
    push "seeds"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  i=0; ntry=0
  while [ $i -lt $NS ] && [ $ntry -lt $NSEEDS ]; do
    k=$i; i=$((i+1)); [ $((k % 2)) -eq $LANE ] || continue
    name=pherc0800_p4v-06_s$k; ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
    if [ ! -f $R ]; then
      mkdir -p $W/seg $L/grow; rm -rf $d
      read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$k]['seed_xyz'];print(*s)")"
      cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":$VOX,"thread_limit":3,
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
      if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; fi
      log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; push "grow $name"
    fi
    if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
      [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
      SEGS+=("$name"); SRC[$name]=auto
      process_seg $name || true
    fi
  done
fi
log "segments to render: ${SEGS[*]:-none}"

# ---- 3-4 (retry pass): every segment not yet DONE ----
for name in "${SEGS[@]}"; do process_seg $name || true; done
NDONE=0; for name in "${SEGS[@]}"; do [ -f $L/$name/DONE ] && NDONE=$((NDONE+1)); done
if [ ${#SEGS[@]} -gt 0 ] && [ $NDONE -eq ${#SEGS[@]} ]; then
  log "PIPELINE COMPLETE: segments=${SEGS[*]}"; touch $L/PIPELINE_DONE; push "pipeline complete"
else
  log "PIPELINE INCOMPLETE: $NDONE of ${#SEGS[@]} segments done; watchdog retries"; push "pipeline incomplete"; exit 1
fi
