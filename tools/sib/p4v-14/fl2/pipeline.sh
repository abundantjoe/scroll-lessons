#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 First Letters push, PHerc0257, second worker p4v-14 (seed lane 1). Copy of the fl-pherc0257 template at
# 54b29c96 (tools/sib/fl-pherc0257/pipeline.sh); parameters, paths, names and the DECL-FL-2 output layout only (BRIEF_FL2 item 2, 5).
# Units: env -> list -> seeds -> grow sK (auto path) -> per segment: render -> infer -> tiles (+push).
# Resume: every unit leaves a marker under logs/sib/p4v-14/fl2 (committed) or /work/fl2/state; finished units are skipped.
# Launch: setsid nohup bash tools/sib/p4v-14/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-p4v-14
ME=p4v-14; LANE=1; SKIP_BELOW=4   # seed lane 1 (second); seeds 0-3 already grown by the primary as fl0257_s0..s3
SCROLL=PHerc0257
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/p4v-14/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/p4v-14/fl2/fl.py; export FL_SCROLL=PHerc0257
CT=s3://vesuvius-challenge-open-data/PHerc0257/volumes/20250821151750-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0257/representations/predictions/surfaces/20250821151750-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0257 has no organizer umbilicus or segments (bucket listing 2026-09-30: photos/ representations/predictions/{lasagna,surfaces}/ volumes/); fl.py seeds uses the CT-mask centroid axis
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=40; MIN_AREA=16; NCAND=48
VOLUME=20250821151750-9.362um-1.2m-113keV-masked; MODEL=official
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; echo "- $(date -u +%FT%TZ) $*" >> $L/STATUS.md; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add logs/sib/p4v-14/fl2 tools/sib/p4v-14/fl2 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "p4v-14: fl2 $1

DECL-FL-2 PHerc0257 second worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012858vqPtFDfZ7WB3ZXJxye
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

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
SEGS=()
if [ "$NORG" -gt 0 ]; then
  SOURCE=organizer; log "source: organizer ($NORG tifxyz segments); using all, ranks with rank % 2 == $LANE"
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
    $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; exit 1; }
    push "seeds"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  i=0; ntry=0
  while [ $i -lt $NS ] && [ $ntry -lt $NSEEDS ]; do
    if [ $((i % 2)) -ne $LANE ] || [ $i -lt $SKIP_BELOW ]; then i=$((i+1)); continue; fi
    name=pherc0257_${ME}_s$i; i=$((i+1)); ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
    if [ ! -f $R ]; then
      mkdir -p $W/seg $L/grow; rm -rf $d
      read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$((i-1))]['seed_xyz'];print(*s)")"
      cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":9.362,"thread_limit":3,
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
      SEGS+=("$name")
    fi
  done
fi
log "segments to render ($SOURCE): ${SEGS[*]:-none}"

# ---- 3-4. render, infer, tiles per segment ----
for name in "${SEGS[@]}"; do
  d=$W/seg/$name; O=$L/$name; TD=$O/tiles_$MODEL; mkdir -p $TD
  [ -f $O/DONE ] && continue
  R=$W/render/$name.zarr; P=$W/infer/$name/$name.tif
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; push "render $name failed"; continue; }
    touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_$name.ok ]; then
    mkdir -p $W/infer/$name; log "infer $name (both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_$name.log 2>&1 || { log "infer $name FAILED"; tail -20 $W/infer_$name.log > $O/infer.log.tail; push "infer $name failed"; continue; }
    touch $ST/infer_$name.ok
  fi
  # every prediction tif the official infer wrote (both directions); direction label = file stem
  nt=0; tf=0
  for PF in $W/infer/$name/*.tif; do
    [ -f "$PF" ] || continue; nt=$((nt+1)); st=$(basename "$PF" .tif)
    case "$st" in "$name") dl=forward;; "${name}_reverse") dl=reverse;; *) log "tiles $name: unexpected prediction $st"; tf=1; continue;; esac
    $PY $FL tiles $name $d $PF $dl $SOURCE $TD $TD/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $dl FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name: $nt prediction tifs, failure=$tf"; push "tiles $name failed"; continue; }
  ( cd $W/infer/$name && sha256sum *.tif > $O/prediction_sha256_$MODEL.txt )
  # DECL-FL-2 item 5 row fields (added to the unchanged cmd_tiles rows)
  $PY -c "
import json,hashlib
m=json.load(open('$TD/manifest.json')); me=json.load(open('$L/grow/${name}_measure.json')) if '$SOURCE'=='auto' else {}
h=lambda f:hashlib.sha256(open(f,'rb').read()).hexdigest()
xs=h('$d/x.tif'); m.update(decl='DECL-FL-2', model='$MODEL', model_sha256='$CKPT_SHA', worker='$ME')
for t in m['tiles']: t.update(scroll='$SCROLL', volume='$VOLUME', model='$MODEL', model_sha256='$CKPT_SHA', segment_area_cm2=me.get('area_cm2'), tifxyz_x_sha256=xs)
json.dump(m,open('$TD/manifest.json','w'),indent=1)" || { log "manifest $name FAILED"; tf=1; }
  touch $O/DONE; log "segment $name: $MODEL tiles done ($($PY -c "import json;print(len(json.load(open('$TD/manifest.json'))['tiles']))") tiles)"; push "tiles $name"
  rm -rf $R   # render zarr is regenerable; keep disk
done
NDONE=0; for name in "${SEGS[@]}"; do [ -f $L/$name/DONE ] && NDONE=$((NDONE+1)); done
if [ ${#SEGS[@]} -gt 0 ] && [ $NDONE -eq ${#SEGS[@]} ]; then
  log "PIPELINE COMPLETE: source=$SOURCE segments=${SEGS[*]}"; touch $L/PIPELINE_DONE; push "pipeline complete"
else
  log "PIPELINE INCOMPLETE: $NDONE of ${#SEGS[@]} segments done; watchdog retries"; push "pipeline incomplete"; exit 1
fi
