#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 First Letters push, PHerc0125, p4v-01 = primary (seed lane 0). Template: fl-pherc0257 pipeline.sh @54b29c96,
# same units and commands; parameters per tools/fl2/BRIEF_FL2.md item 2. Operational differences, disclosed in STATUS.md:
#   - per seed, grow -> render -> infer -> tiles -> push (brief item 6), instead of growing every seed first;
#   - model: OFFICIAL ink_9um step-075000 only (the DENSE arm is withdrawn, RULES.md DECL-FL-2-E1);
#   - tiles go to <SEG>/tiles_official/ with direction labels forward|reverse; manifest rows gain the brief item 5 fields.
# Resume: committed markers under logs/sib/p4v-01/fl2 and /work/fl2/state; finished units are skipped.
# Launch: setsid nohup bash tools/sib/p4v-01/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ME=p4v-01; LANE=0; BR=claude/gifted-bell-gavnl5-sib-$ME
SCROLL=PHerc0125; VOLUME=20250821151825; SL=pherc0125
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/$ME/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$ME/fl2/fl.py; export FL_SCROLL=$SCROLL
CT=s3://vesuvius-challenge-open-data/PHerc0125/volumes/20250821151825-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0125/representations/predictions/surfaces/20250821151825-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=$HTTPB/PHerc0125/representations/umbilicus/20250821151825-umbilicus-20260808111524.json   # organizer umbilicus (83 control points)
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NCAND=48; NSEEDS=40; MIN_AREA=16
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }
status() { echo "$(date -u +%FT%TZ) $*" >> $L/STATUS.md; }

push() {  # commit + push this worker's outputs under one lock; retry with backoff
  ( flock 9
    cd "$REPO"; git add logs/sib/$ME/fl2 tools/sib/$ME/fl2 >/dev/null 2>&1
    git diff --cached --quiet || git -c user.name=$ME -c user.email=noreply@anthropic.com commit -q -m "$ME: fl2 $1 (DECL-FL-2)

DECL-FL-2 PHerc0125 primary worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01X29Q1eLXbpjS1HAsMSS83A

Provenance: Project HERCULES | [id removed]"
    for d in 2 4 8 16 32; do
      git push -q -u origin $BR 2>>$W/push.err && exit 0
      git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
    done; exit 1
  ) 9>$W/git.lock || log "WARN push failed for unit $1"
}

# ---- 1. environment (template step, unchanged) ----
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then
  log "env: docker down after restart; re-running setup_env.sh (idempotent)"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env2.log 2>&1 || { log "env re-setup FAILED"; exit 1; }
fi
if [ ! -f $ST/env.ok ]; then
  log "env: setup_env.sh"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env2.log 2>&1 || { log "env FAILED (tail: $(tail -2 $W/setup_env2.log | tr '\n' ' '))"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_grow_seg_from_seed --help >/dev/null 2>&1; /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "env: vesuvius infer not importable"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests, imagecodecs" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs imagecodecs
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > $L/env.txt
  touch $ST/env.ok; log "env: OK"; status "env OK ($(head -1 $L/env.txt))"
fi

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; status "s3 list: $($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))") organizer tifxyz segments"; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
[ "$NORG" -gt 0 ] && { log "organizer tifxyz segments now exist ($NORG): not handled by this auto-grow pipeline; stopping for review"; status "STOP: $NORG organizer segments appeared"; push "organizer segments appeared"; exit 1; }
SOURCE=auto
if [ ! -f $L/seeds.json ]; then
  $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; status "seeds FAILED"; push "seeds failed"; exit 1; }
  status "seeds: $($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))") of $NCAND candidates (sha256 $(sha256sum $L/seeds.json | cut -c1-16)); lane $LANE takes index % 2 == $LANE"
  push "seeds"
fi
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")

arms() { echo official; }   # DECL-FL-2-E1: official model only

segment() {  # render -> infer -> tiles for every enabled arm; idempotent by markers
  local name=$1 d=$W/seg/$1 O=$L/$1 R=$W/render/$1.zarr arm need=0
  for arm in $(arms); do [ -f $O/DONE_$arm ] || need=1; done
  [ $need -eq 1 ] || return 0
  [ -f $d/x.tif ] || { mkdir -p $d; cp $O/tifxyz/* $d/; }
  if [ ! -f $ST/render_$name.ok ] || [ ! -d $R ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"; local t0=$(date +%s)
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; status "render $name FAILED"; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok; status "render $name ok ($(( $(date +%s)-t0 )) s)"
  fi
  for arm in $(arms); do
    [ -f $O/DONE_$arm ] && continue
    local I=$W/infer_$arm/$name MSHA ck t0=$(date +%s)
    if [ ! -f $ST/infer_${arm}_$name.ok ]; then
      rm -rf $I; mkdir -p $I; log "infer $name $arm (both directions, no TTA)"
      OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $I/$name.tif \
        --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_${arm}_$name.log 2>&1 || { log "infer $name $arm FAILED"; tail -20 $W/infer_${arm}_$name.log > $O/infer_$arm.log.tail; status "infer $name $arm FAILED"; push "infer $name $arm failed"; continue; }
      touch $ST/infer_${arm}_$name.ok
    fi
    MSHA=$CKPT_SHA
    local T=$O/tiles_$arm nt=0 tf=0 PF dl; mkdir -p $T
    for PF in $I/*.tif; do
      [ -f "$PF" ] || continue; nt=$((nt+1))
      case $(basename "$PF" .tif) in $name) dl=forward;; ${name}_reverse) dl=reverse;; *) dl=$(basename "$PF" .tif);; esac
      $PY $FL tiles $name $d $PF $dl $SOURCE $T $T/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $arm $dl FAILED"; tf=1; }
    done
    [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name $arm: $nt prediction tifs, failure=$tf"; status "tiles $name $arm FAILED"; push "tiles $name $arm failed"; continue; }
    $PY - "$T/manifest.json" "$SCROLL" "$VOLUME" "$name" "$arm" "$MSHA" "$L/grow/${name}_measure.json" "$O/tifxyz/x.tif" <<'P'
import json, sys, hashlib
mp, scroll, vol, seg, arm, msha, meas, xt = sys.argv[1:]
m = json.load(open(mp)); area = json.load(open(meas))['area_cm2']
xs = hashlib.sha256(open(xt, 'rb').read()).hexdigest()
m.update(rule='DECL-FL-2', model=arm, model_sha256=msha, volume=vol, segment_area_cm2=area, tifxyz_x_sha256=xs)
for t in m['tiles']:
    t.update(scroll=scroll, volume=vol, model=arm, model_sha256=msha, segment_area_cm2=area, tifxyz_x_sha256=xs)
json.dump(m, open(mp, 'w'), indent=1)
P
    ( cd $I && sha256sum *.tif > $T/prediction_sha256.txt )
    local nk; nk=$($PY -c "import json;print(len(json.load(open('$T/manifest.json'))['tiles']))")
    touch $O/DONE_$arm; log "segment $name $arm: $nk tiles"; status "tiles $name $arm: $nk tiles ($(( $(date +%s)-t0 )) s infer+tile)"
    push "tiles $name $arm"
    rm -rf $I
  done
  [ -f $O/DONE_official ] && rm -rf $R   # render zarr is regenerable; keep disk (template behaviour)
}

kept() { [ -f $L/grow/$1.json ] && [ "$($PY -c "import json;print(json.load(open('$L/grow/$1.json'))['kept'])")" = "True" ]; }

# ---- 3. per seed: grow -> segment (render, infer, tiles, push) ----
i=0; ntry=0
while [ $i -lt $NS ] && [ $ntry -lt $NSEEDS ]; do
  k=$i; i=$((i+1)); [ $((k % 2)) -eq $LANE ] || continue
  ntry=$((ntry+1)); name=${SL}_${ME}_s$k; Rg=$L/grow/$name.json; d=$W/seg/$name
  if [ ! -f $Rg ]; then
    mkdir -p $W/seg $L/grow; rm -rf $d
    read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$k]['seed_xyz'];print(*s)")"
    cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":9.362,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
    cp $W/grow_params.json $L/grow_params.json
    log "grow $name seed ($sx $sy $sz)"; t0=$(date +%s)
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
    echo "{\"segment\":\"$name\",\"seed_index\":$k,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $Rg
    if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; fi
    log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; status "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok ($(( $(date +%s)-t0 )) s)"
    push "grow $name"
  fi
  kept $name && segment $name
  # catch-up: any earlier kept segment whose render/infer/tiles failed is retried
  for g in $L/grow/${SL}_${ME}_s*.json; do case $g in *_measure.json|*_selfcross.json) continue;; esac
    n=$(basename $g .json); kept $n && segment $n; done
done
[ -f $L/PIPELINE_DONE ] || { log "seed list exhausted: $ntry grow attempts of lane $LANE"; status "seed list exhausted ($ntry attempts)"; }
[ -f $L/PIPELINE_DONE ] || { touch $L/PIPELINE_DONE; push "pipeline seed list exhausted"; }
