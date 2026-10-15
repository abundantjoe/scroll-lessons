#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# fl-pherc0483a: First Letters screen of PHerc0483A (RULES.md DECL-FL-1, OWNER-STANDING-ORDER-5). Numbers only.
# Idempotent; commits and pushes after every unit. A unit is skipped when its pushed output exists in the repo,
# so a relaunch after a container restart resumes where the last push left off (relaunch: bash tools/sib/fl-pherc0483a/autostart.sh).
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-fl-pherc0483a
T=tools/sib/fl-pherc0483a; OUT=logs/sib/fl-pherc0483a; W=/work/fl0483a; mkdir -p "$OUT" "$W" /work/logs
L=$W/pipeline.log
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKSHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
SC=PHerc0483A; VOX=8.64
S3H=https://vesuvius-challenge-open-data.s3.amazonaws.com
VURL=$S3H/$SC/volumes/20250521140913-8.640um-1.2m-116keV-masked.zarr/
PRED=$SC/representations/predictions/surfaces/20250521140913-surface-20260413222639-surface-m7-L0-th0.2
SURL=$S3H/$PRED.zarr/
export AWS_CA_BUNDLE=/root/.ccr/ca-bundle.crt REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
export OMP_NUM_THREADS=3 VC_CPUS=3
export FL_NG_DIR=$W/normal-grids FL_CACHE=$W/cache
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
status() { echo "$(date -u +%FT%TZ) fl-pherc0483a: $*" > "$OUT/STATUS.md"; }
push() { # push <msg> <paths...>
  local msg=$1; shift
  git add -- "$@" "$OUT/STATUS.md" 2>>"$L"
  git -c user.name="fl-pherc0483a" -c user.email="noreply@anthropic.com" commit -q -m "fl-pherc0483a: $msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QZiioTLyqFo1hNisTUtcCu" >>"$L" 2>&1 || true
  for i in 1 2 3 4 5; do
    git pull -q --rebase origin "$BR" >>"$L" 2>&1; git push -q -u origin "$BR" >>"$L" 2>&1 && return 0; sleep $((2**i)); done
  log "push failed: $msg"; }
fail() { log "FAILED: $*"; status "FAILED: $* (see $W/pipeline.log)"; push "failure: $*" "$OUT/STATUS.md"; exit 1; }

# 1. environment: VC3D apps from villa 41701aa, CPU vesuvius, sha-verified ink_9um step-075000
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || \
   [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_grow_seg_from_seed ] || \
   [ ! -x /opt/hv-ink/bin/python ] || [ ! -x /opt/hv/bin/python ] || [ ! -f "$CK" ] || [ ! -x /work/bin/vc ]; then
  status "step 1 environment build running"
  bash docker/env/setup_env.sh >>/work/logs/setup_env.log 2>&1 || fail "setup_env (see /work/logs/setup_env.log)"
fi
docker info >/dev/null 2>&1 || fail "docker daemon not running"
echo "$CKSHA  $CK" | sha256sum -c --quiet || fail "ckpt sha mismatch"
PY=/opt/hv/bin/python
$PY -c "import zarr, s3fs, cv2, tifffile, PIL, imagecodecs" 2>/dev/null || VIRTUAL_ENV=/opt/hv uv pip install -q "zarr<3" numcodecs s3fs fsspec opencv-python-headless tifffile pillow imagecodecs >>"$L" 2>&1

# 2. segments: inventory, then organizer tifxyz (3 largest) or auto-grow (up to 4 seeds)
if [ ! -s "$OUT/inventory.json" ]; then
  status "step 2 inventory running"
  $PY $T/fl.py inventory "$W/inventory.json" >>"$L" 2>&1 && cp "$W/inventory.json" "$OUT/inventory.json" || fail "inventory"
  push "inventory of s3://vesuvius-challenge-open-data/$SC/" "$OUT/inventory.json"
fi
NORG=$($PY -c "import json;print(json.load(open('$OUT/inventory.json'))['n_organizer_tifxyz'])")
: > $W/units.txt
if [ "$NORG" -gt 0 ]; then
  if [ ! -s "$OUT/selection.json" ]; then
    $PY $T/fl.py select "$OUT/inventory.json" "$OUT/selection.json" >>"$L" 2>&1 || fail "select"
    push "organizer segment selection (3 largest)" "$OUT/selection.json"
  fi
  $PY -c "
import json
for r in json.load(open('$OUT/selection.json'))['segments']: print(r['segment'], r['mesh_key'])" | while read -r SEG MK; do
    D=$OUT/$SEG; [ -f "$D/mesh/x.tif" ] || { $PY $T/fl.py download "$MK" "$D/mesh" >>"$L" 2>&1 || { log "download FAILED $SEG"; continue; }; }
    echo "$SEG organizer" >> $W/units.txt
  done
else
  mkdir -p "$FL_NG_DIR" "$FL_CACHE"
  echo "{\"url\": \"$S3H/$PRED.normal-grids/\"}" > "$FL_NG_DIR/normal-grids-remote.json"
  if [ ! -s "$OUT/seeds.json" ]; then
    status "step 2 auto-grow: seed placement running"
    $PY $T/fl.py seeds "$W/seeds.json" >>"$L" 2>&1 && cp "$W/seeds.json" "$OUT/seeds.json" || fail "seeds"
    push "GrowPatch seeds (4, mid radius, surface-m7)" "$OUT/seeds.json"
  fi
  for K in 0 1 2 3; do
    SEG=auto_pherc0483a_s$K; D=$OUT/$SEG; G=$W/grow/$SEG
    if [ ! -s "$D/gate.json" ]; then
      mkdir -p "$D" "$G"
      read -r SX SY SZ < <($PY $T/fl.py params "$OUT/seeds.json" $K "$D/grow_params.json")
      if [ "$SX" = NONE ]; then
        echo "{\"segment\": \"$SEG\", \"keep\": false, \"reason\": \"no surface voxel near the seed target\"}" > "$D/gate.json"
        push "grow $SEG: no seed" "$D"; continue; fi
      status "step 2 GrowPatch $SEG (seed $SX $SY $SZ) running"
      log "grow $SEG seed $SX $SY $SZ"
      rm -rf "$G/seg"; mkdir -p "$G/seg"
      ( cd "$G" && timeout --signal=TERM 10h /work/bin/vc vc_grow_seg_from_seed -v "$SURL" -t "$G/seg" -p "$REPO/$D/grow_params.json" \
          -s "$SX" "$SY" "$SZ" --segment-name "$SEG" ) > "$G/grow.log" 2>&1
      GRC=$?
      tail -80 "$G/grow.log" > "$D/grow_tail.log"
      if [ -f "$G/seg/x.tif" ] && [ -f "$G/seg/meta.json" ]; then
        /work/bin/vc vc_tifxyz_selfcross "$G/seg" -o "$G/selfcross.json" --threads 3 --fail-on-crossing > "$G/selfcross.log" 2>&1
        XRC=$?
        cp "$G/selfcross.json" "$D/selfcross.json" 2>/dev/null
        $PY $T/fl.py gate "$G/seg" "$G/selfcross.json" $XRC "$D/gate.json" >>"$L" 2>&1 || fail "gate $SEG"
        mkdir -p "$D/mesh"; cp "$G/seg"/*.tif "$G/seg/meta.json" "$D/mesh/"
      else
        $PY -c "import json;json.dump({'segment':'$SEG','keep':False,'grow_rc':$GRC,'reason':'no surface saved (discarded below min_area_cm 16, timeout 10h, or error; see grow_tail.log)'},open('$D/gate.json','w'),indent=1)"
      fi
      log "grow $SEG rc=$GRC gate $(cat "$D/gate.json" | tr -d '\n ' | head -c 200)"
      push "GrowPatch $SEG (rc $GRC) + self-intersection/area gate" "$D"
    fi
    $PY -c "import json,sys;sys.exit(0 if json.load(open('$D/gate.json')).get('keep') else 1)" && echo "$SEG auto" >> $W/units.txt
  done
fi
NU=$(wc -l < $W/units.txt)
[ "$NU" -gt 0 ] || { status "ALL DONE: 0 segments passed the gate; no tiles"; push "done: no segment" "$OUT"; touch "$OUT/DONE" $W/DONE; push "DONE" "$OUT/DONE"; exit 0; }

# 3-4. per segment: prep -> render C2-NT -> infer both directions -> tiles -> push
k=0
while read -r SEG SRC <&3; do
  k=$((k+1)); D=$OUT/$SEG; U=$W/seg/$SEG; mkdir -p "$U"
  if [ -f "$D/manifest.json" ] && $PY -c "import json,sys;sys.exit(0 if len(json.load(open('$D/manifest.json'))['runs'])>=2 else 1)"; then continue; fi
  status "unit $k/$NU $SEG ($SRC): render/infer running"
  [ -s "$U/crop.json" ] || $PY $T/fl.py prep "$REPO/$D/mesh" "$U" "$SRC" >>"$L" 2>&1 || { log "prep FAILED $SEG"; continue; }
  read -r X Y CW CH < <($PY -c "import json;print(*json.load(open('$U/crop.json'))['crop_xywh'])")
  R=$U/render.zarr
  if [ ! -f "$U/render.done" ]; then
    rm -rf "$R"; log "render $SEG crop $X $Y $CW $CH"
    ( cd "$U" && /work/bin/vc vc_render_tifxyz -v "$VURL" --remote-url "$VURL" --segmentation "$REPO/$D/mesh" --scale 1 --group-idx 0 \
        --num-slices 31 --slice-step 1 --voxel-size "$VOX" --voxel-unit micrometer \
        --crop-x "$X" --crop-y "$Y" --crop-width "$CW" --crop-height "$CH" --flip-normals --cache-gb 4 --zarr-output "$R" ) \
        > "$U/render.log" 2>&1 && touch "$U/render.done" || { log "render FAILED $SEG"; tail -40 "$U/render.log" > "$D/render_fail_tail.log"; push "render failed $SEG" "$D"; continue; }
  fi
  mkdir -p "$U/infer"
  if [ ! -f "$U/infer.done" ]; then
    log "infer $SEG"
    /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CK" "$U/infer/$SEG.tif" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$U/infer.log" 2>&1 && touch "$U/infer.done" || \
      { log "infer FAILED $SEG"; tail -40 "$U/infer.log" > "$D/infer_fail_tail.log"; push "infer failed $SEG" "$D"; continue; }
  fi
  rm -f "$D/manifest.json"
  for P in "$U"/infer/*.tif; do
    case "$P" in *_reverse.tif) TAG=reverse;; *) TAG=forward;; esac
    $PY $T/fl.py tiles "$U" "$P" "$D" "$TAG" "$VOX" >>"$L" 2>&1 || log "tiles FAILED $SEG $TAG"
  done
  cp "$U/crop.json" "$D/crop.json"; tail -40 "$U/render.log" > "$D/render_tail.log" 2>/dev/null; tail -40 "$U/infer.log" > "$D/infer_tail.log" 2>/dev/null
  status "unit $k/$NU $SEG done"
  push "tiles $SEG ($SRC)" "$D"
  rm -rf "$R"   # keep disk low; prediction tifs stay in $U/infer
done 3< $W/units.txt
status "ALL DONE: $NU segment(s) tiled; see $OUT/*/manifest.json"
touch "$OUT/DONE"; push "all units done" "$OUT"
touch $W/DONE
