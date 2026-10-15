#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters extra PASS 3, PHerc0211 (tools/fl/BRIEF_PASS.md @ dcb6a6b; OWNER-STANDING-ORDER-5:
# detached, idempotent, pushes after every unit). Adapted from tools/sib/fl-pherc0211/pipeline.sh (pass 1, f5876b5).
# Pass 3 rule: organizer segments ranked 10-15 by area; if the scroll has none, auto-grow up to 4 segments seeded in
# the INNER third of the scroll radius. Keep only 0 self-intersections and >= 16 cm^2.
# Launch: setsid nohup bash tools/sib/fl3-pherc0211/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-devloop2
SCROLL=PHerc0211; PASS=3; TAG=fl3-pherc0211
W=/work/$TAG; ST=$W/state; L=$REPO/logs/sib/$TAG
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$TAG/fl.py
CT=s3://vesuvius-challenge-open-data/PHerc0211/volumes/20250821151803-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0211/representations/predictions/surfaces/20250821151803-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=$HTTPB/PHerc0211/representations/umbilicus/20250821151803-umbilicus-20260808112626.json
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=4; MIN_AREA=16; RANK_LO=10; RANK_HI=15
BAND="0.05 0.3333 0.19"   # inner third of R (lo, hi, target); lo keeps seeds off the umbilicus core
mkdir -p "$W" "$ST" "$L"
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$L/pipeline.log"; }
disk_ok() {  # keep >= 5 GB free plus the unit's estimate (GB)
  local av; av=$(df -BG --output=avail / | tail -1 | tr -dc 0-9)
  [ "$av" -ge $((5 + ${1:-0})) ] || { log "DISK: ${av} GB free < 5+${1:-0} GB; stopping this attempt"; return 1; }
}
push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  cd "$REPO"; git add "logs/sib/$TAG" "tools/sib/$TAG" docker/env/vc_build.sh >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "$TAG: $1

DECL-FL-1 extra pass 3 compute worker unit (numbers and file lists only; no image viewed).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XmfKMsfRzMGj4TuJyZv67G"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>"$W/push.err" && return 0
    git pull -q --rebase origin $BR 2>>"$W/push.err"; sleep $d
  done; log "WARN push failed for unit $1"
}
finish() {  # $1 = status line
  echo "$(date -u +%FT%TZ) $1" >> "$L/STATUS.md"; touch "$L/PIPELINE_DONE"; log "PIPELINE COMPLETE: $1"; push "pipeline complete: $1"; exit 0
}
check_seg() {  # $1 segdir, $2 out prefix -> prints "area selfx ok"
  local d=$1 o=$2 area=0 sc=null ok=false
  if [ -s "$d/x.tif" ]; then
    $PY $FL measure "$d" "${o}_measure.json" >> "$L/pipeline.log" 2>&1
    area=$($PY -c "import json;print(json.load(open('${o}_measure.json'))['area_cm2'])" 2>/dev/null || echo 0)
    /work/bin/vc vc_tifxyz_selfcross "$d" -o "${o}_selfcross.json" > /dev/null 2>&1
    sc=$($PY -c "import json;r=json.load(open('${o}_selfcross.json'));print(sum(d['transverse'] for d in r['diagonals']) if 'diagonals' in r else 'null')" 2>/dev/null || echo null)
    [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
  fi
  echo "$area $sc $ok"
}

# ---- 1. environment (reuses an existing build if present) ----
if [ ! -f "$ST/env.ok" ]; then
  disk_ok 15 || exit 1
  log "env: setup_env.sh"
  bash "$REPO/docker/env/setup_env.sh" > "$W/setup_env.log" 2>&1 || { log "env FAILED (tail: $(tail -2 "$W/setup_env.log" | tr '\n' ' '))"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_render_tifxyz --help > "$W/render_help.txt" 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > "$L/env.txt"
  touch "$ST/env.ok"; log "env: OK"; push "env ok"
fi
docker info >/dev/null 2>&1 || { log "docker down; rerunning setup_env"; bash "$REPO/docker/env/setup_env.sh" > "$W/setup_env.log" 2>&1 || exit 1; }

# ---- 2. segment source ----
if [ ! -f "$ST/list.ok" ]; then
  $PY $FL list $SCROLL "$L/s3_list.json" >> "$L/pipeline.log" 2>&1 || { log "list FAILED"; exit 1; }
  $PY $FL rank "$L/s3_list.json" "$L/s3_rank.json" >> "$L/pipeline.log" 2>&1 || { log "rank FAILED"; exit 1; }
  touch "$ST/list.ok"; push "s3 listing + area ranking"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_rank.json'))['segments']))")
SEGS=()
if [ "$NORG" -gt 0 ]; then
  SOURCE=organizer
  [ "$NORG" -ge $RANK_LO ] || finish "DONE: no segments in range (organizer segments: $NORG < rank $RANK_LO)"
  log "source: organizer ($NORG tifxyz segments); ranks $RANK_LO-$RANK_HI"
  for pre in $($PY -c "import json;[print(s['prefix']) for s in json.load(open('$L/s3_rank.json'))['segments'] if $RANK_LO<=s['rank']<=$RANK_HI]"); do
    name=$(basename "$pre"); d=$W/seg/$name; R=$L/check/$name.json; mkdir -p "$d" "$L/check"
    if [ ! -f "$R" ]; then
      for f in x.tif y.tif z.tif meta.json mask.tif; do
        [ -s "$d/$f" ] || curl -fsS -o "$d/$f" "$HTTPB/$pre/$f" || rm -f -- "${d:?}/${f:?}"
      done
      read -r area sc ok <<<"$(check_seg "$d" "$L/check/$name")"
      echo "{\"segment\":\"$name\",\"prefix\":\"$pre\",\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > "$R"
      log "check $name: area=$area cm2 selfx=$sc kept=$ok"; push "check $name"
    fi
    [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ] && SEGS+=("$name")
  done
else
  SOURCE=auto; log "source: auto (no organizer tifxyz segments in the bucket); inner third, band $BAND"
  if [ ! -f "$L/seeds.json" ]; then
    $PY $FL seeds $CT "${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB}" $UMB 8 "$L/seeds.json" $BAND >> "$L/pipeline.log" 2>&1 || { log "seeds FAILED"; exit 1; }
    push "seeds (inner third)"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  i=0
  while [ $i -lt "$NS" ] && [ $i -lt $NSEEDS ]; do
    name=fl3_0211_s$i; i=$((i+1)); R=$L/grow/$name.json; d=$W/seg/$name
    if [ ! -f "$R" ]; then
      disk_ok 5 || exit 1
      mkdir -p "$W/seg" "$L/grow"; rm -rf -- "${d:?}"
      read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$((i-1))]['seed_xyz'];print(*s)")"
      cat > "$W/grow_params.json" <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":9.362,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
      cp "$W/grow_params.json" "$L/grow_params.json"
      log "grow $name seed ($sx $sy $sz)"
      t0=$(date +%s)
      OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t "$d" -p "$W/grow_params.json" \
        -s $sx $sy $sz --segment-name $name --skip-overlap-check > "$W/grow_$name.log" 2>&1; rc=$?
      tail -40 "$W/grow_$name.log" > "$L/grow/$name.log.tail"
      read -r area sc ok <<<"$(check_seg "$d" "$L/grow/$name")"
      echo "{\"segment\":\"$name\",\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > "$R"
      if $ok; then mkdir -p "$L/$name/tifxyz"; cp "$d/x.tif" "$d/y.tif" "$d/z.tif" "$d/meta.json" "$L/$name/tifxyz/"; fi
      log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; push "grow $name"
    fi
    if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
      [ -f "$d/x.tif" ] || { mkdir -p "$d"; cp "$L/$name/tifxyz/"* "$d/"; }
      SEGS+=("$name")
    fi
  done
fi
log "segments to render ($SOURCE): ${SEGS[*]:-none}"

# ---- 3-4. render, infer, tiles per segment ----
for name in "${SEGS[@]}"; do
  d=$W/seg/$name; O=$L/$name; mkdir -p "$O/tiles"
  [ -f "$O/DONE" ] && continue
  R=$W/render/$name.zarr; P=$W/infer/$name/$name.tif
  if [ ! -f "$ST/render_$name.ok" ]; then
    disk_ok 8 || exit 1
    rm -rf -- "${R:?}"; mkdir -p "$W/render"; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation "$d" --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output "$R" > "$W/render_$name.log" 2>&1 || { log "render $name FAILED"; tail -20 "$W/render_$name.log" > "$O/render.log.tail"; push "render $name failed"; continue; }
    touch "$ST/render_$name.ok"
  fi
  if [ ! -f "$ST/infer_$name.ok" ]; then
    disk_ok 2 || exit 1
    mkdir -p "$W/infer/$name"; log "infer $name (both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" $CKPT "$P" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$W/infer_$name.log" 2>&1 || { log "infer $name FAILED"; tail -20 "$W/infer_$name.log" > "$O/infer.log.tail"; push "infer $name failed"; continue; }
    touch "$ST/infer_$name.ok"
  fi
  $PY $FL tiles $name "$d" "$P" forward $SOURCE "$O/tiles" "$O/tiles/manifest.json" $SCROLL $PASS >> "$L/pipeline.log" 2>&1 || { log "tiles $name forward FAILED"; continue; }
  $PY $FL tiles $name "$d" "${P%.tif}_reverse.tif" reverse $SOURCE "$O/tiles" "$O/tiles/manifest.json" $SCROLL $PASS >> "$L/pipeline.log" 2>&1 || { log "tiles $name reverse FAILED"; continue; }
  ( cd "$W/infer/$name" && sha256sum ./*.tif > "$O/prediction_sha256.txt" )
  touch "$O/DONE"; log "segment $name: tiles done"; push "tiles $name"
  rm -rf -- "${R:?}"   # render zarr is regenerable; keep disk
done
# every kept segment must have finished; otherwise the watchdog retries
for name in "${SEGS[@]}"; do [ -f "$L/$name/DONE" ] || { log "segment $name not finished; attempt ends"; exit 1; }; done
NT=$($PY -c "import json,glob;print(sum(len(json.load(open(m))['tiles']) for m in glob.glob('$L/*/tiles/manifest.json')))")
finish "DONE $NT tiles (pass $PASS, source=$SOURCE, segments=${SEGS[*]:-none})"
