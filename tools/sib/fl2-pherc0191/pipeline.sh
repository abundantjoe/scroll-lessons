#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-1 First Letters extra pass (tools/fl/BRIEF_PASS.md @ dcb6a6b): SCROLL PHerc0191, PASS 2.
# Detached, idempotent, pushes after every unit (OWNER-STANDING-ORDER-5). Numbers and file lists only; no image viewed.
# Units: env -> list -> segments (organizer ranks 4-9, else auto-grow <= 4 seeds in the OUTER third of the radius)
#        -> per segment: render (C2-NT) -> infer (ink_9um step-075000, both directions, no TTA, CPU) -> tiles (+push).
# Resume: each unit leaves a marker (committed under logs/sib/fl2-pherc0191 or in /work/fl2-pherc0191/state).
# Launch: setsid nohup bash tools/sib/fl2-pherc0191/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-tribunal
SCROLL=PHerc0191; PASS=2; TAG=fl2-pherc0191; RANK_LO=4; RANK_HI=9; BAND_LO=0.667; BAND_HI=1.0
W=/work/$TAG; ST=$W/state; L=$REPO/logs/sib/$TAG
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$TAG/fl.py
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
CT=s3://vesuvius-challenge-open-data/PHerc0191/volumes/20250821151635-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0191/representations/predictions/surfaces/20250821151635-surface-20260413222639-surface-m7-L0-th0.2.zarr/
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=4; MIN_AREA=16
mkdir -p "$W" "$ST" "$L"
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$L/pipeline.log"; }
h() { echo "${1/s3:\/\/vesuvius-challenge-open-data/$HTTPB}"; }

push() {  # commit + push this worker's outputs only; retry with backoff, rebase on rejection
  cd "$REPO" || return 1; git add "logs/sib/$TAG" "tools/sib/$TAG" >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "$TAG: $1

DECL-FL-1 extra-pass compute worker unit (numbers and file lists only; no image viewed).

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01YUHdkQ6ZFAJMnFeavch5Xc"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>"$W/push.err" && return 0
    git pull -q --rebase origin $BR 2>>"$W/push.err"; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 0. voxel size from the volume's metadata.json (never assumed) ----
VOX=$($PY "$FL" voxel "$(h $CT)metadata.json") || { log "voxel size lookup FAILED"; exit 1; }
[ -n "$VOX" ] || { log "voxel size empty"; exit 1; }
export FL_VOX_UM=$VOX

# ---- 1. environment (reuses an existing build) ----
if [ ! -f "$ST/env.ok" ]; then
  log "env: setup_env.sh (voxel $VOX um from metadata.json)"
  bash "$REPO/docker/env/setup_env.sh" > "$W/setup_env.log" 2>&1 || { log "env FAILED (tail: $(tail -2 "$W/setup_env.log" | tr '\n' ' '))"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_render_tifxyz --help > "$W/render_help.txt" 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; echo "voxel_um $VOX (metadata.json samplePixelSize)";
    /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > "$L/env.txt"
  touch "$ST/env.ok"; log "env: OK"; push "env"
fi
# dockerd does not survive a container restart; bring it back without redoing the env unit
docker info >/dev/null 2>&1 || bash "$REPO/docker/env/setup_env.sh" > "$W/setup_env_restart.log" 2>&1

# ---- 2. segment source ----
if [ ! -f "$L/s3_list.json" ]; then
  $PY "$FL" list $SCROLL "$L/s3_list.json" >> "$L/pipeline.log" 2>&1 || { log "list FAILED"; exit 1; }
  push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")
SEGS=()

check_keep() {  # $1 name, $2 dir, $3 source -> writes $L/segments/<name>.json; returns 0 if kept
  local name=$1 d=$2 src=$3 area sc ok=false
  mkdir -p "$L/segments"
  $PY "$FL" measure "$d" "$L/segments/${name}_measure.json" >> "$L/pipeline.log" 2>&1
  area=$($PY -c "import json;print(json.load(open('$L/segments/${name}_measure.json'))['area_cm2'])" 2>/dev/null || echo 0)
  /work/bin/vc vc_tifxyz_selfcross "$d" -o "$W/selfcross_$name.json" > "$W/selfcross_$name.log" 2>&1
  cp "$W/selfcross_$name.json" "$L/segments/${name}_selfcross.json" 2>/dev/null
  sc=$($PY "$FL" selfx "$W/selfcross_$name.json" "$W/selfx_$name.txt" 2>/dev/null || echo -1)
  [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
  echo "{\"segment\":\"$name\",\"source\":\"$src\",\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > "$L/segments/$name.json"
  log "segment $name ($src): area=$area cm2 selfx=$sc kept=$ok"
  $ok
}
kept() { [ "$($PY -c "import json;print(json.load(open('$L/segments/$1.json'))['kept'])" 2>/dev/null)" = "True" ]; }

if [ "$NORG" -ge "$RANK_LO" ]; then
  SOURCE=organizer; log "source: organizer ($NORG tifxyz segments); ranks $RANK_LO-$RANK_HI"
  for pre in $($PY "$FL" rank "$L/s3_list.json" $RANK_LO $RANK_HI); do
    name=$(basename "$pre"); d=$W/seg/$name
    if [ ! -f "$L/segments/$name.json" ]; then
      mkdir -p "$d" "$L/segments"
      for f in x.tif y.tif z.tif meta.json mask.tif; do
        [ -s "$d/$f" ] || curl -fsS -o "$d/$f" "$HTTPB/$pre/$f" || rm -f "${d:?}/${f:?}"
      done
      ( cd "$d" && sha256sum ./*.tif meta.json ) > "$L/segments/${name}_files_sha256.txt"
      check_keep "$name" "$d" organizer; push "segment $name checked"
    fi
    kept "$name" && SEGS+=("$name")
  done
elif [ "$NORG" -gt 0 ]; then
  SOURCE=none; log "organizer segments exist ($NORG) but none in ranks $RANK_LO-$RANK_HI; auto-grow rule does not apply"
  echo "DONE: no segments in range" >> "$L/STATUS.md"; touch "$L/PIPELINE_DONE"; push "no segments in range"; exit 0
else
  SOURCE=auto; log "source: auto (no organizer tifxyz segments); up to $NSEEDS GrowPatch seeds in radius band [$BAND_LO, $BAND_HI) R"
  if [ ! -f "$L/seeds.json" ]; then
    $PY "$FL" seeds_band "$(h $CT)" "$(h $SURF)" 8 $BAND_LO $BAND_HI "$L/seeds.json" >> "$L/pipeline.log" 2>&1 || { log "seeds FAILED"; exit 1; }
    push "seeds (outer third)"
  fi
  NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
  i=0
  while [ $i -lt "$NS" ] && [ $i -lt $NSEEDS ]; do
    name=fl2_0191_s$i; d=$W/seg/$name
    if [ ! -f "$L/segments/$name.json" ]; then
      mkdir -p "$W/seg" "$L/grow"; rm -rf "${W:?}/seg/${name:?}"
      read -r sx sy sz <<<"$($PY -c "import json;print(*json.load(open('$L/seeds.json'))['seeds'][$i]['seed_xyz'])")"
      cat > "$W/grow_params.json" <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":$VOX,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
      cp "$W/grow_params.json" "$L/grow_params.json"
      log "grow $name seed ($sx $sy $sz)"; t0=$(date +%s)
      OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t "$d" -p "$W/grow_params.json" \
        -s $sx $sy $sz --segment-name $name --skip-overlap-check > "$W/grow_$name.log" 2>&1; rc=$?
      tail -40 "$W/grow_$name.log" > "$L/grow/$name.log.tail"
      echo "{\"segment\":\"$name\",\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 ))}" > "$L/grow/$name.json"
      if [ -f "$d/x.tif" ]; then
        if check_keep "$name" "$d" auto; then
          mkdir -p "$L/$name/tifxyz"; cp "$d/x.tif" "$d/y.tif" "$d/z.tif" "$d/meta.json" "$L/$name/tifxyz/"
        fi
      else
        mkdir -p "$L/segments"; echo "{\"segment\":\"$name\",\"source\":\"auto\",\"rc\":$rc,\"kept\":false,\"note\":\"no tifxyz produced\"}" > "$L/segments/$name.json"
        log "grow $name: rc=$rc, no tifxyz"
      fi
      push "grow $name"
    fi
    if kept "$name"; then
      [ -f "$d/x.tif" ] || { mkdir -p "$d"; cp "$L/$name/tifxyz/"* "$d/"; }
      SEGS+=("$name")
    fi
    i=$((i+1))
  done
fi
log "segments to render ($SOURCE): ${SEGS[*]:-none}"

# ---- 3-4. render, infer, tiles per segment ----
for name in "${SEGS[@]}"; do
  d=$W/seg/$name; O=$L/$name; mkdir -p "$O/tiles"
  [ -f "$O/DONE" ] && continue
  R=$W/render/$name.zarr; I=$W/infer/$name; P=$I/$name.tif
  if [ ! -f "$ST/render_$name.ok" ]; then
    rm -rf "${W:?}/render/${name:?}.zarr"; mkdir -p "$W/render"; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation "$d" --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output "$R" > "$W/render_$name.log" 2>&1 || { log "render $name FAILED"; tail -20 "$W/render_$name.log" > "$O/render.log.tail"; push "render $name failed"; continue; }
    touch "$ST/render_$name.ok"
  fi
  if [ ! -f "$ST/infer_$name.ok" ]; then
    rm -rf "${W:?}/infer/${name:?}"; mkdir -p "$I"; log "infer $name (both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CKPT" "$P" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$W/infer_$name.log" 2>&1 || { log "infer $name FAILED"; tail -20 "$W/infer_$name.log" > "$O/infer.log.tail"; push "infer $name failed"; continue; }
    touch "$ST/infer_$name.ok"
  fi
  ( cd "$I" && ls -1 ./*.tif > "$O/prediction_files.txt" && sha256sum ./*.tif > "$O/prediction_sha256.txt" )
  find "$O/tiles" -maxdepth 1 -name '*.png' -delete; find "$O/tiles" -maxdepth 1 -name manifest.json -delete
  nd=0; fail=0
  for pt in "$I"/*.tif; do
    case "$(basename "$pt")" in *rev*) dir=reverse ;; *) dir=forward ;; esac
    $PY "$FL" tiles "$name" "$d" "$pt" $dir $SOURCE "$O/tiles" "$O/tiles/manifest.json" $SCROLL $PASS >> "$L/pipeline.log" 2>&1 || { log "tiles $name $dir FAILED"; fail=1; }
    nd=$((nd+1))
  done
  if [ $fail != 0 ] || [ $nd -lt 1 ]; then push "tiles $name failed"; continue; fi
  [ $nd -eq 2 ] || log "WARN $name: $nd prediction files (expected 2: forward + reverse)"
  touch "$O/DONE"; log "segment $name: tiles done ($nd prediction files)"; push "tiles $name"
  rm -rf "${W:?}/render/${name:?}.zarr"   # render zarr is regenerable; keep disk
done
NT=$($PY -c "import json,glob;print(sum(len(json.load(open(f))['tiles']) for f in glob.glob('$L/*/tiles/manifest.json')))")
log "PIPELINE COMPLETE: source=$SOURCE segments=${SEGS[*]:-none} tiles=$NT"
echo "DONE $NT tiles" >> "$L/STATUS.md"; touch "$L/PIPELINE_DONE"; push "pipeline complete ($NT tiles)"
