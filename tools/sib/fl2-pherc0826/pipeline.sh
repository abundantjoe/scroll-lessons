#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters extra pass: PHerc0826, PASS 2 (tools/fl/BRIEF_PASS.md; OWNER-STANDING-ORDER-5: detached,
# idempotent, pushes after every unit). Adapted from the pass-1 worker fl-pherc0211. PASS 2 = organizer segments ranked
# 4-9; PHerc0826 has none, so up to 4 auto-grown segments seeded in the OUTER third of the radius (fl.py seeds).
# Units: env -> list -> seeds -> grow sK (auto path) -> per segment: render -> infer -> tiles (+push).
# Resume: every unit leaves a marker under logs/sib/fl2-pherc0826 (committed) or /work/fl2/state; finished units are skipped.
# Launch: setsid nohup bash tools/sib/fl2-pherc0826/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-readcal2
SCROLL=PHerc0826
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/fl2-pherc0826
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/fl2-pherc0826/fl.py
CT=s3://vesuvius-challenge-open-data/PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0826/representations/predictions/surfaces/20250821151701-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=$HTTPB/PHerc0826/representations/umbilicus/20250821151701-umbilicus-20260808113303.json
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=4; MAXTRY=8; MIN_AREA=16
export FL_SCROLL=$SCROLL FL_PASS=2
export FL_VOX_UM=$(curl -fsS https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr/metadata.json | $PY -c "import json,sys;print(round(float(json.load(sys.stdin)['scan']['tomo']['acquisition']['detector']['samplePixelSize'])*1000,6))")
[ -n "$FL_VOX_UM" ] || { echo "voxel size unavailable"; exit 1; }
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add logs/sib/fl2-pherc0826 tools/sib/fl2-pherc0826 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "fl2-pherc0826: $1

DECL-FL-1 PASS 2 worker unit (numbers and file lists only; no image viewed).

Provenance: Project HERCULES | owner the owner | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016xXtTKGSN5FYrQWH7tzHeH"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>$W/push.err && return 0
    git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 1. environment ----
if [ ! -f $ST/env.ok ]; then
  log "env: setup_env.sh (villa sparse set widened; VC build with the HTTPS_PROXY-aware vc_build copy)"
  [ -d /work/villa/.git ] && git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection >> $W/setup_env.log 2>&1
  mkdir -p /work/scripts /work/bin /work/logs
  if ! docker info >/dev/null 2>&1; then HTTPS_PROXY=$HTTPS_PROXY HTTP_PROXY=$HTTPS_PROXY nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 & for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done; fi
  IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
  docker image inspect $IMG >/dev/null 2>&1 || docker pull $IMG >> $W/setup_env.log 2>&1
  git -C /work/villa checkout -q 41701aa0eaa1aa765523db3f9f972b5830abf549 >> $W/setup_env.log 2>&1
  [ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || bash $REPO/tools/sib/fl2-pherc0826/vc_build.sh > $W/vc_build.log 2>&1 || { log "env: VC build FAILED (tail: $(tail -2 $W/vc_build.log | tr '\n' ' '))"; exit 1; }
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env FAILED (tail: $(tail -2 $W/setup_env.log | tr '\n' ' '))"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_grow_seg_from_seed --help >/dev/null 2>&1; /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
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
  SOURCE=organizer; log "source: organizer ($NORG tifxyz segments); using the 3 largest"
  for pre in $($PY -c "import json;[print(s['prefix']) for s in json.load(open('$L/s3_list.json'))['tifxyz_segments'][:3]]"); do
    name=$(basename "$pre"); d=$W/seg/$name; mkdir -p $d
    for f in x.tif y.tif z.tif meta.json mask.tif; do
      [ -s $d/$f ] || curl -fsS -o $d/$f "$HTTPB/$pre/$f" || rm -f $d/$f
    done
    [ -s $d/x.tif ] && SEGS+=("$name")
  done
else
  SOURCE=auto; log "source: auto (no organizer tifxyz segments in the bucket)"
  if [ ! -f $L/seeds.json ]; then
    $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB 8 $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; exit 1; }
    push "seeds"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  i=0; ntry=0
  while [ $i -lt $NS ] && [ $ntry -lt $MAXTRY ] && [ ${#SEGS[@]} -lt $NSEEDS ]; do
    name=fl2_0826_s$i; i=$((i+1)); ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
    if [ ! -f $R ]; then
      mkdir -p $W/seg $L/grow; rm -rf $d
      read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$((i-1))]['seed_xyz'];print(*s)")"
      cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":$FL_VOX_UM,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
      cp $W/grow_params.json $L/grow_params.json
      log "grow $name seed ($sx $sy $sz)"
      t0=$(date +%s)
      OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $d -p $W/grow_params.json \
        -s $sx $sy $sz --segment-name $name --skip-overlap-check > $W/grow_$name.log 2>&1; rc=$?
      tail -40 $W/grow_$name.log > $L/grow/$name.log.tail
      ok=false; area=0; sc=null
      if [ -f $d/x.tif ]; then
        $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
        area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
        /work/bin/vc vc_tifxyz_selfcross $d -o $W/selfcross_$name.json > /dev/null 2>&1; cp $W/selfcross_$name.json $L/grow/${name}_selfcross.json 2>/dev/null
        sc=$($PY -c "import json;r=json.load(open('$W/selfcross_$name.json'));print(sum(d['transverse'] for d in r['diagonals']) if 'diagonals' in r else 'null')" 2>/dev/null || echo null)
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
  d=$W/seg/$name; O=$L/$name; mkdir -p $O/tiles
  [ -f $O/DONE ] && continue
  R=$W/render/$name.zarr; P=$W/infer/$name/$name.tif
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $FL_VOX_UM --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; push "render $name failed"; continue; }
    touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_$name.ok ]; then
    mkdir -p $W/infer/$name; log "infer $name (both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_$name.log 2>&1 || { log "infer $name FAILED"; tail -20 $W/infer_$name.log > $O/infer.log.tail; push "infer $name failed"; continue; }
    touch $ST/infer_$name.ok
  fi
  $PY $FL tiles $name $d $P forward $SOURCE $O/tiles $O/tiles/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name forward FAILED"; continue; }
  $PY $FL tiles $name $d ${P%.tif}_reverse.tif reverse $SOURCE $O/tiles $O/tiles/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name reverse FAILED"; continue; }
  ( cd $W/infer/$name && sha256sum *.tif > $O/prediction_sha256.txt )
  touch $O/DONE; log "segment $name: tiles done"; push "tiles $name"
  rm -rf $R   # render zarr is regenerable; keep disk
done
NT=$($PY -c "import json,glob;print(sum(len(json.load(open(f))['tiles']) for f in glob.glob('$L/*/tiles/manifest.json')))")
log "PIPELINE COMPLETE: source=$SOURCE segments=${SEGS[*]:-none} tiles=$NT"
echo "DONE $NT tiles ($(date -u +%FT%TZ); source=$SOURCE; segments=${SEGS[*]:-none})" >> $L/STATUS.md
touch $L/PIPELINE_DONE; push "pipeline complete: DONE $NT tiles"
