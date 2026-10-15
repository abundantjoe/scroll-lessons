#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-2 First Letters push, PHerc0483B (volume 20251124083638, 8.64 um), primary worker fl-pherc0483b (seed lane 0).
# Copy of fl-pherc0257's DECL-FL-1 pipeline (@54b29c96) with parameters changed per tools/fl2/BRIEF_FL2.md items 2-5:
#   SCROLL/CT/SURF/UMB/voxel size 8.64 (grow voxelsize, render --voxel-size, fl.py FL_VOX_UM), branch, paths, names;
#   48 candidate seeds; lane 0 = even seed indices; assign.json gives this scroll no second worker, so the odd indices
#   follow after the even ones (disclosed in STATUS.md); at most NSEEDS=40 grow attempts; MIN_AREA 16 cm^2, 0 transverse
#   self-intersections (gate unchanged); tiles: every 2 x 2 cm cell with valid >= 50 %, both directions, unchanged tiler;
#   outputs per brief item 5 (tiles_<model>/, manifest fields, tifxyz/, STATUS.md lines).
# Order: grow -> gate -> render -> infer -> tiles -> push for each seed in turn (brief item 6), so tiles arrive all day.
# DENSE arm: runs on every kept segment once /work/fl2/dense.env exists (written by the worker only after the pilot's
#   DENSE_OK.json is verified); it sets DENSE_CKPT, DENSE_SHA and optional DENSE_ARGS for the same villa infer.
# Resume: grow/<seg>.json, <seg>/tiles_<model>/DONE (committed) and /work/fl2/state markers; finished units are skipped.
# Launch: setsid nohup bash tools/sib/fl-pherc0483b/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ME=fl-pherc0483b; BR=claude/gifted-bell-gavnl5-sib-$ME
SCROLL=PHerc0483B; VOLUME=20251124083638; VOX=8.64; LANE=0
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/$ME/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$ME/fl2/fl.py; export FL_SCROLL=$SCROLL FL_VOX_UM=$VOX
CT=s3://vesuvius-challenge-open-data/PHerc0483B/volumes/20251124083638-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0483B/representations/predictions/surfaces/20251124083638-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0483B: no organizer umbilicus or segments (bucket: photos/ representations/predictions/surfaces/ volumes/; listing pushed 2026-09-30)
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NCAND=48; NSEEDS=40; MIN_AREA=16
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }
status() { echo "$(date -u +%FT%TZ) $ME fl2: $*" >> $L/STATUS.md; }

push() {  # commit + push this worker's FL-2 outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add logs/sib/$ME/fl2 tools/sib/$ME/fl2 >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -q -m "$ME: fl2 $1

DECL-FL-2 compute worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KFttsr5wzUre7QqHYjh2Zz
Provenance: Project HERCULES | [id removed]"
  for d in 2 4 8 16 32; do
    git push -q -u origin HEAD:$BR 2>>$W/push.err && return 0
    git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 1. environment (brief item 3) ----
envfix() {
  if [ -d /work/villa/vesuvius ] && [ -x /opt/hv-ink/bin/python ] && ! /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null; then
    /opt/hv-ink/bin/python -m ensurepip -q >/dev/null 2>&1
    /opt/hv-ink/bin/python -m pip install -q --ignore-requires-python --no-deps -e /work/villa/vesuvius >> $W/setup_env.log 2>&1
    VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r $REPO/docker/env/hv-ink-freeze.txt --no-deps >> $W/setup_env.log 2>&1 || true
  fi
  VIRTUAL_ENV=/opt/hv uv pip install -q imagecodecs numcodecs >> $W/setup_env.log 2>&1 || true
}
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then
  log "env: docker down after restart; re-running setup_env.sh"; bash $REPO/docker/env/setup_env.sh >> $W/setup_env.log 2>&1
fi
if [ ! -f $ST/env.ok ]; then
  log "env: setup_env.sh"
  bash $REPO/docker/env/setup_env.sh >> $W/setup_env.log 2>&1 || { envfix; bash $REPO/docker/env/setup_env.sh >> $W/setup_env.log 2>&1; }
  envfix
  docker info >/dev/null 2>&1 || { log "env: docker not running"; status "env FAILED: docker not running"; push "env failed"; exit 1; }
  /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; status "env FAILED: vc_render_tifxyz unusable (tail: $(tail -2 $W/setup_env.log | tr '\n' ' '))"; push "env failed"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; status "env FAILED: checkpoint sha"; push "env failed"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "env: vesuvius infer not importable"; status "env FAILED: vesuvius infer not importable"; push "env failed"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests, imagecodecs" || { log "env: /opt/hv imports"; exit 1; }
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch,sys;print('torch',torch.__version__,'python',sys.version.split()[0])"; } > $L/env.txt
  touch $ST/env.ok; log "env: OK"; status "env OK ($(tr '\n' ' ' < $L/env.txt))"; push "env"
fi

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
if [ "$NORG" -gt 0 ]; then
  log "STOP: $NORG organizer tifxyz segments now exist; this copy implements the auto branch only (0 at build time)"
  status "STOP: $NORG organizer tifxyz segments appeared in the bucket; the worker must switch to the organizer branch"; push "organizer segments appeared"; exit 0
fi
if [ ! -f $L/seeds.json ]; then
  $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; status "seeds FAILED"; push "seeds failed"; exit 1; }
  status "seeds: $($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))") of $NCAND candidate positions gave a seed"; push "seeds"
fi
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
ORDER=$($PY -c "print(*([i for i in range($NS) if i%2==$LANE]+[i for i in range($NS) if i%2!=$LANE])[:$NSEEDS])")

tile_model() {  # tile_model <name> <model> <ckpt> <sha> [extra infer args]
  local name=$1 model=$2 ck=$3 sha=$4; shift 4
  local d=$W/seg/$name O=$L/$name/tiles_$model R=$W/render/$name.zarr I=$W/infer/$model/$name
  [ -f $O/DONE ] && return 0
  mkdir -p $O $I
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $L/$name/render.log.tail; status "$name render FAILED"; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_${model}_$name.ok ]; then
    log "infer $name $model (both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $ck $I/$name.tif \
      --direction both --batch-size 4 --num-workers 1 --no-compile "$@" > $W/infer_${model}_$name.log 2>&1 || { log "infer $name $model FAILED"; tail -20 $W/infer_${model}_$name.log > $O/infer.log.tail; status "$name $model infer FAILED"; push "infer $name $model failed"; return 1; }
    touch $ST/infer_${model}_$name.ok
  fi
  local area; area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
  local nt=0 tf=0 PF
  rm -f $O/manifest.json
  for PF in $I/*.tif; do
    [ -f "$PF" ] || continue; nt=$((nt+1))
    $PY $FL tiles $name $d $PF $(basename "$PF" .tif) auto $O $O/manifest.json $model $sha $VOLUME $area >> $L/pipeline.log 2>&1 || { log "tiles $name $model FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { status "$name $model tiles FAILED ($nt prediction tifs)"; push "tiles $name $model failed"; return 1; }
  ( cd $I && sha256sum *.tif > $O/prediction_sha256.txt )
  touch $O/DONE
  status "$name $model: $($PY -c "import json;t=json.load(open('$O/manifest.json'))['tiles'];print(len(t),'tiles kept (forward',sum(x['direction']=='forward' for x in t),', reverse',sum(x['direction']=='reverse' for x in t),')')"), area $area cm2"
  push "tiles $name $model"
}

# ---- 3. grow -> gate -> render -> infer -> tiles, seed after seed ----
for i in $ORDER; do
  name=$(echo $SCROLL | tr 'A-Z' 'a-z')_${ME}_s$i; R=$L/grow/$name.json; d=$W/seg/$name
  if [ ! -f $R ]; then
    mkdir -p $W/seg $L/grow; rm -rf $d
    read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$i]['seed_xyz'];print(*s)")"
    cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":$VOX,"thread_limit":3,
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
    echo "{\"segment\":\"$name\",\"seed_index\":$i,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
    if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; ( cd $L/$name/tifxyz && sha256sum x.tif y.tif z.tif meta.json > ../tifxyz_sha256.txt ); fi
    log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; status "grow $name (seed $i): rc $rc, area $area cm2, self-intersections $sc, kept $ok"; push "grow $name"
  fi
  [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ] || continue
  [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
  tile_model $name official $CKPT $CKPT_SHA
  if [ -f $W/dense.env ]; then . $W/dense.env; tile_model $name dense $DENSE_CKPT $DENSE_SHA ${DENSE_ARGS:-}; fi
  if [ -f $L/$name/tiles_official/DONE ] && { [ ! -f $W/dense.env ] || [ -f $L/$name/tiles_dense/DONE ]; }; then rm -rf $W/render/$name.zarr; rm -f $ST/render_$name.ok; fi
done
log "pass complete over seeds: $ORDER"; touch $ST/pass.done
