#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# fl-pilot: First Letters screen pilot on the eligible 9 um volumes. Idempotent; pushes after each unit.
# Resume rule: a unit is skipped when its pushed output exists in the repo (survives a container restart).
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-fl-pilot
OUT=logs/sib/fl-pilot; W=/work/flp; mkdir -p "$OUT" "$W" /work/logs
L=$W/pipeline.log
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
export AWS_CA_BUNDLE=/root/.ccr/ca-bundle.crt REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt OMP_NUM_THREADS=3
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
status() { echo "$(date -u +%FT%TZ) fl-pilot: $*" > "$OUT/STATUS.md"; }
push() { # push <msg> <paths...>
  local msg=$1; shift
  git add -- "$@" "$OUT/STATUS.md" 2>/dev/null
  git -c user.name="fl-pilot" -c user.email="noreply@anthropic.com" commit -q -m "fl-pilot: $msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0183h6ws29tbLyHa1AgUQpAb" || true
  for i in 1 2 3 4 5; do
    git pull -q --rebase origin "$BR" 2>>"$L"; git push -q -u origin "$BR" 2>>"$L" && return 0; sleep $((2**i)); done
  log "push failed: $msg"; }

# 0. minimal python for listing
[ -x /opt/hv/bin/python ] || { uv venv /opt/hv --python 3.11 -q && VIRTUAL_ENV=/opt/hv uv pip install -q numpy scipy opencv-python-headless tifffile "zarr<3" numcodecs pillow requests boto3; } >>"$L" 2>&1
PY=/opt/hv/bin/python

# 2. inventory (before the long build, so it lands early)
if [ ! -s "$OUT/inventory.json" ]; then
  status "step 2 inventory running"
  $PY tools/sib/fl-pilot/flp.py inventory "$W/inventory.json" >>"$L" 2>&1 && cp "$W/inventory.json" "$OUT/inventory.json" || { log "inventory FAILED"; exit 1; }
  status "step 2 inventory done: tifxyz volumes = $($PY -c "import json;print(json.load(open('$OUT/inventory.json'))['volumes_with_tifxyz'])")"
  push "inventory of eligible 9 um volumes" "$OUT/inventory.json"
fi
if [ "$($PY -c "import json;print(len(json.load(open('$OUT/inventory.json'))['volumes_with_tifxyz']))")" = 0 ]; then
  status "STOP after step 2: no eligible volume has a tifxyz segment"; push "stop: no tifxyz" "$OUT/STATUS.md"; touch $W/DONE; exit 0; fi

# selection
if [ ! -s "$OUT/selection.json" ]; then
  $PY tools/sib/fl-pilot/flp.py select "$OUT/inventory.json" "$OUT/selection.json" >>"$L" 2>&1 || { log "select FAILED"; exit 1; }
  push "segment selection (2 largest per volume, up to 3 volumes)" "$OUT/selection.json"
fi

# 1. environment (setup_env builds VC3D apps from villa 41701aa, CPU vesuvius, sha-verified checkpoint)
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || [ ! -x /opt/hv-ink/bin/python ] || [ ! -f "$CK" ]; then
  status "step 1 environment build running"
  bash docker/env/setup_env.sh >>/work/logs/setup_env.log 2>&1 || { log "setup_env FAILED (see /work/logs/setup_env.log)"; exit 1; }
fi
echo "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab  $CK" | sha256sum -c --quiet || { log "ckpt sha mismatch"; exit 1; }

# 3-4. per segment: prep -> render -> infer -> tiles -> push
$PY -c "
import json
for s in json.load(open('$OUT/selection.json'))['selection']:
  for r in s['segments']: print(s['scroll'], r['segment'], r['mesh_key'], s['voxel_um'], s['volume_zarr'])" > $W/units.txt
NU=$(wc -l < $W/units.txt); k=0
while read -r SC SEG MK VOX VZ <&3; do
  k=$((k+1)); D="$OUT/$SC/$SEG"; U=$W/$SC/$SEG; mkdir -p "$U" "$D"
  if [ -f "$D/manifest.json" ] && $PY -c "import json,sys;sys.exit(0 if len(json.load(open('$D/manifest.json'))['runs'])>=2 else 1)"; then continue; fi
  status "unit $k/$NU $SC $SEG: prep/render/infer running"
  [ -s "$U/crop.json" ] || $PY tools/sib/fl-pilot/flp.py prep "$SC" "$SEG" "$MK" "$U" >>"$L" 2>&1 || { log "prep FAILED $SEG"; continue; }
  read -r X Y CW CH < <($PY -c "import json;print(*json.load(open('$U/crop.json'))['crop_xywh'])")
  MD=$($PY -c "import json;print(json.load(open('$U/crop.json'))['mesh_dir'])")
  VZ=${VZ%/}; URL="https://vesuvius-challenge-open-data.s3.amazonaws.com/$SC/volumes/$VZ/"
  R=$U/render.zarr
  if [ ! -f "$U/render.done" ]; then
    rm -rf "$R"; log "render $SC $SEG crop $X $Y $CW $CH"
    ( cd "$U" && /work/bin/vc vc_render_tifxyz -v "$URL" --remote-url "$URL" --segmentation "$MD" --scale 1 --group-idx 0 \
        --num-slices 31 --slice-step 1 --voxel-size "$VOX" --voxel-unit micrometer \
        --crop-x "$X" --crop-y "$Y" --crop-width "$CW" --crop-height "$CH" --flip-normals --cache-gb 4 --zarr-output "$R" ) \
        > "$U/render.log" 2>&1 && touch "$U/render.done" || { log "render FAILED $SEG"; continue; }
  fi
  mkdir -p "$U/infer"
  if [ ! -f "$U/infer.done" ]; then
    log "infer $SC $SEG"
    /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CK" "$U/infer/$SEG.tif" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$U/infer.log" 2>&1 && touch "$U/infer.done" || { log "infer FAILED $SEG"; continue; }
  fi
  for P in "$U"/infer/*.tif; do
    case "$P" in *_reverse.tif) TAG=reverse;; *) TAG=forward;; esac
    $PY tools/sib/fl-pilot/flp.py tiles "$U" "$P" "$D" "$TAG" "$VOX" >>"$L" 2>&1 || log "tiles FAILED $SEG $TAG"
  done
  cp "$U/render.log" "$D/render.log" 2>/dev/null; tail -50 "$U/infer.log" > "$D/infer_tail.log" 2>/dev/null
  status "unit $k/$NU $SC $SEG done"
  push "tiles $SC $SEG" "$D"
  rm -rf "$R"   # keep disk low; prediction tifs stay in $U/infer
done 3< $W/units.txt
status "ALL DONE: $(ls -d $OUT/*/*/ 2>/dev/null | wc -l) segments tiled; see logs/sib/fl-pilot/*/*/manifest.json"
push "all units done" "$OUT"
touch $W/DONE
