#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 First Letters push, PHerc0175A, worker p4v-02 = PRIMARY (seed lane 0). Template: fl-pherc0257 pipeline.sh
# @54b29c96, unit logic unchanged; parameters only (tools/fl2/BRIEF_FL2.md item 2):
#   SCROLL/CT/SURF/UMB/branch/paths/names; voxel size 8.640 um (this volume; template 9.362); seeds `fl.py seeds ... 48`,
#   lane 0 takes seed indices k % 2 == 0, segment names pherc0175a_p4v-02_s<k>; NSEEDS (max grow attempts) 40;
#   MIN_AREA 16 cm2; 0 self-intersections; organizer tifxyz (if any): ALL, even ranks; tiles: every 2x2 cm cell with
#   valid >= 0.5, both directions (fl.py tiles unchanged). Each segment goes grow -> render -> infer -> tiles -> push
#   before the next seed is grown. Outputs: L/<SEG>/tiles_<model>/<SEG>_<forward|reverse>_rRR_cCC.png + manifest.json
#   (rows completed with scroll, volume, model, model_sha256, segment_area_cm2, tifxyz sha256s).
# Models: official always; dense only once $W/dense/dense.env exists (written from the pilot's DENSE_OK.json).
# Resume: markers under L (committed) or $W/state; finished units are skipped.
# Launch: setsid nohup bash tools/sib/p4v-02/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ME=p4v-02; LANE=0
BR=claude/gifted-bell-gavnl5-sib-$ME
SCROLL=PHerc0175A; VOLUME=20250521115057; SL=pherc0175a
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/$ME/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$ME/fl2/fl.py; export FL_SCROLL=$SCROLL
CT=s3://vesuvius-challenge-open-data/PHerc0175A/volumes/20250521115057-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0175A/representations/predictions/surfaces/20250521115057-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0175A has no organizer umbilicus or segments (bucket listing 2026-10-01: photos/ representations/predictions/surfaces/ volumes/); fl.py seeds uses the CT-mask centroid axis
VOX=8.640
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=40; MIN_AREA=16; NCAND=48
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }
status() { echo "$(date -u +%FT%TZ) $ME $*" >> $L/STATUS.md; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add logs/sib/$ME/fl2 tools/sib/$ME/fl2 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "$ME: FL2 $SCROLL $1

DECL-FL-2 compute worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S7WzvF2vxmV1oKK5c6U9p2

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
  touch $ST/env.ok; log "env: OK"; status "env OK ($(head -1 $L/env.txt))"
fi

# ---- per-segment units: render -> infer -> tiles, per model ----
models() { echo official; [ -f $W/dense/dense.env ] && echo dense; }
process_seg() {  # $1 name, $2 source
  local name=$1 source=$2 d=$W/seg/$1 O=$L/$1 R=$W/render/$1.zarr m
  local area; area=$($PY -c "import json;print(json.load(open('$O/measure.json'))['area_cm2'])" 2>/dev/null || echo null)
  for m in $(models); do
    local T=$O/tiles_$m; [ -f $T/DONE ] && continue
    local MCK=$CKPT MSHA=$CKPT_SHA INFER_CMD=""
    if [ $m = dense ]; then . $W/dense/dense.env; MCK=$DENSE_CKPT; MSHA=$DENSE_SHA; fi
    echo "$MSHA  $MCK" | sha256sum -c --quiet || { log "$m checkpoint sha mismatch"; status "$name $m: checkpoint sha mismatch, skipped"; continue; }
    if [ ! -f $ST/render_$name.ok ] || [ ! -d $R ]; then
      rm -rf $R; mkdir -p $W/render; log "render $name"
      /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
        --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
        --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; mkdir -p $O; tail -20 $W/render_$name.log > $O/render.log.tail; status "$name render FAILED"; push "render $name failed"; return 1; }
      touch $ST/render_$name.ok; status "$name render OK"
    fi
    local I=$W/infer/$m/$name P=$W/infer/$m/$name/$name.tif
    if [ ! -f $ST/infer_${m}_$name.ok ]; then
      rm -rf $I; mkdir -p $I; log "infer $name $m (both directions, no TTA)"
      if [ $m = official ]; then
        OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $MCK $P \
          --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_${m}_$name.log 2>&1
      else
        OMP_NUM_THREADS=3 bash -c "$DENSE_INFER" _ $R $MCK $P > $W/infer_${m}_$name.log 2>&1
      fi || { log "infer $name $m FAILED"; mkdir -p $O; tail -20 $W/infer_${m}_$name.log > $O/infer_$m.log.tail; status "$name infer $m FAILED"; push "infer $name $m failed"; return 1; }
      touch $ST/infer_${m}_$name.ok; status "$name infer $m OK"
    fi
    # every prediction tif the infer wrote: <name>.tif = forward, <name>_reverse.tif = reverse
    local nt=0 tf=0 PF stem dl
    mkdir -p $T; rm -f $T/manifest.json
    for PF in $I/*.tif; do
      [ -f "$PF" ] || continue; stem=$(basename "$PF" .tif)
      case $stem in $name) dl=forward;; ${name}_reverse) dl=reverse;; *) log "tiles $name $m: unexpected prediction $stem"; tf=1; continue;; esac
      nt=$((nt+1))
      $PY $FL tiles $name $d $PF $dl $source $T $T/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $m $dl FAILED"; tf=1; }
    done
    [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name $m: $nt prediction tifs, failure=$tf"; status "$name tiles $m FAILED"; push "tiles $name $m failed"; return 1; }
    $PY - "$T/manifest.json" "$SCROLL" "$VOLUME" "$m" "$MCK" "$MSHA" "$area" "$O/tifxyz" <<'PYEOF' || { log "manifest $name $m FAILED"; return 1; }
import hashlib, json, os, sys
f, scroll, volume, model, ckpt, msha, area, tx = sys.argv[1:9]
sh = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
txs = {k: sh(os.path.join(tx, k)) for k in ('x.tif', 'y.tif', 'z.tif', 'meta.json') if os.path.exists(os.path.join(tx, k))}
m = json.load(open(f)); m.update(volume=volume, model=model, model_checkpoint=os.path.basename(ckpt), model_sha256=msha)
for t in m['tiles']:
    t.update(scroll=scroll, volume=volume, model=model, model_sha256=msha,
             segment_area_cm2=None if area == 'null' else round(float(area), 4), tifxyz_sha256=txs)
json.dump(m, open(f, 'w'), indent=1)
print('manifest', model, len(m['tiles']), 'tiles')
PYEOF
    ( cd $I && sha256sum *.tif > $T/prediction_sha256.txt )
    local nk; nk=$($PY -c "import json;print(len(json.load(open('$T/manifest.json'))['tiles']))")
    touch $T/DONE; log "segment $name $m: $nk tiles"; status "$name tiles $m: $nk tiles (area $area cm2)"; push "tiles $name $m ($nk)"
  done
  # render zarr is regenerable; keep disk (a later dense arm re-renders)
  rm -rf $R; rm -f $ST/render_$name.ok
  return 0
}

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; status "s3 list: $($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))") organizer tifxyz segments"; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
SEGS=()
if [ "$NORG" -gt 0 ]; then
  SOURCE=organizer; log "source: organizer ($NORG tifxyz segments); ALL, largest first, lane $LANE ranks"
  rk=0
  for pre in $($PY -c "import json;[print(s['prefix']) for s in json.load(open('$L/s3_list.json'))['tifxyz_segments']]"); do
    rk=$((rk+1)); [ $(( (rk-1) % 2 )) -eq $LANE ] || continue
    name=$(basename "$pre"); d=$W/seg/$name; mkdir -p $d
    for f in x.tif y.tif z.tif meta.json mask.tif; do
      [ -s $d/$f ] || curl -fsS -o $d/$f "$HTTPB/$pre/$f" || rm -f $d/$f
    done
    if [ -s $d/x.tif ]; then
      mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/
      [ -f $L/$name/measure.json ] || $PY $FL measure $d $L/$name/measure.json >> $L/pipeline.log 2>&1
      SEGS+=("$name"); process_seg $name $SOURCE
    fi
  done
else
  SOURCE=auto; log "source: auto (no organizer tifxyz segments in the bucket)"
  if [ ! -f $L/seeds.json ]; then
    $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; status "seeds FAILED"; exit 1; }
    status "seeds: $($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))") candidate seeds; lane $LANE takes k % 2 == $LANE"; push "seeds"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  k=-1; ntry=0
  while [ $((k+1)) -lt $NS ] && [ $ntry -lt $NSEEDS ]; do
    k=$((k+1)); [ $((k % 2)) -eq $LANE ] || continue
    name=${SL}_${ME}_s$k; ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
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
      echo "{\"segment\":\"$name\",\"seed_index\":$k,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
      if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; cp $L/grow/${name}_measure.json $L/$name/measure.json; fi
      log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; status "$name grow: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; push "grow $name"
    fi
    if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
      [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
      SEGS+=("$name"); process_seg $name $SOURCE
    fi
  done
fi
log "segments ($SOURCE): ${SEGS[*]:-none}"

# ---- completion (per model present) ----
NDONE=0; NEED=0
for name in "${SEGS[@]}"; do for m in $(models); do NEED=$((NEED+1)); [ -f $L/$name/tiles_$m/DONE ] && NDONE=$((NDONE+1)); done; done
if [ $NEED -gt 0 ] && [ $NDONE -eq $NEED ]; then
  log "PIPELINE COMPLETE: source=$SOURCE segments=${SEGS[*]} models=$(models | tr '\n' ' ')"; status "PIPELINE COMPLETE: ${#SEGS[@]} segments, models $(models | tr '\n' ' ')"
  touch $L/PIPELINE_DONE; push "pipeline complete"
else
  log "PIPELINE INCOMPLETE: $NDONE of $NEED segment-model units done; watchdog retries"; push "pipeline incomplete"; exit 1
fi
