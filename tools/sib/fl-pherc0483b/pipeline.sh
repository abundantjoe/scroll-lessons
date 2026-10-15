#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# fl-pherc0483b: DECL-FL-1 First Letters screen on PHerc0483B (8.64 um, 20251124083638). Idempotent; pushes after each unit.
# Resume rule: every unit's result is pushed under logs/sib/fl-pherc0483b/ (grown tifxyz included), and a unit is skipped
# when its pushed result exists, so a fresh container resumes with one command:
#   nohup setsid bash tools/sib/fl-pherc0483b/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-fl-pherc0483b
T=tools/sib/fl-pherc0483b; OUT=logs/sib/fl-pherc0483b; W=/work/flx; mkdir -p "$OUT" "$W" /work/logs
L=$W/pipeline.log
SC=PHerc0483B; VOX=8.64; NSEEDS=4
VZ=20251124083638-8.640um-1.2m-116keV-masked.zarr
VURL="https://vesuvius-challenge-open-data.s3.amazonaws.com/$SC/volumes/$VZ/"
SURL="https://vesuvius-challenge-open-data.s3.amazonaws.com/$SC/representations/predictions/surfaces/20251124083638-surface-20260413222639-surface-m7-L0-th0.2.zarr/"
GROW_GENS=${FLX_GROW_GENS:-200}; GROW_TIMEOUT=${FLX_GROW_TIMEOUT:-6h}
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
export AWS_CA_BUNDLE=/root/.ccr/ca-bundle.crt REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt OMP_NUM_THREADS=3
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
status() { echo "$(date -u +%FT%TZ) fl-pherc0483b: $*" > "$OUT/STATUS.md"; log "STATUS $*"; }
push() { # push <msg> <paths...>
  local msg=$1; shift
  git add -- "$@" "$OUT/STATUS.md" 2>/dev/null
  git -c user.name="fl-pherc0483b" -c user.email="noreply@anthropic.com" commit -q -m "fl-pherc0483b: $msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KFttsr5wzUre7QqHYjh2Zz" || true
  for i in 1 2 3 4 5; do
    git pull -q --rebase origin "$BR" 2>>"$L"; git push -q -u origin "$BR" 2>>"$L" && return 0; sleep $((2**i)); done
  log "push failed: $msg"; }
killvc() { docker ps -q --filter "ancestor=$IMG" | xargs -r docker kill >/dev/null 2>&1; }

# 0. minimal python (listing, seeds, gate, tiles)
[ -x /opt/hv/bin/python ] || { uv venv /opt/hv --python 3.11 -q && VIRTUAL_ENV=/opt/hv uv pip install -q numpy scipy opencv-python-headless tifffile "zarr<3" numcodecs pillow requests boto3; } >>"$L" 2>&1
PY=/opt/hv/bin/python

# 2a. anonymous listing of the scroll folder
if [ ! -s "$OUT/listing.json" ]; then
  status "step 2 listing running"
  $PY $T/flx.py listing "$W/listing.json" >>"$L" 2>&1 && cp "$W/listing.json" "$OUT/listing.json" || { log "listing FAILED"; exit 1; }
  push "anonymous S3 listing of $SC" "$OUT/listing.json"
fi
NT=$($PY -c "import json;print(json.load(open('$OUT/listing.json'))['n_tifxyz'])")
if [ "$NT" != 0 ]; then
  status "STOP: $NT organizer tifxyz segments now exist for $SC; this pipeline was built for the auto-grow branch (0 at build time). Orchestrator: switch to the organizer branch (3 largest)."
  push "stop: organizer segments appeared" "$OUT/STATUS.md"; touch $W/DONE; exit 0; fi

# 2b. seeds at mid radius on the organizer surface prediction
if [ ! -s "$OUT/seeds.json" ]; then
  status "step 2 seed placement running"
  $PY $T/flx.py seeds "$W/seeds.json" $NSEEDS >>"$L" 2>&1 && cp "$W/seeds.json" "$OUT/seeds.json" || { log "seeds FAILED"; exit 1; }
  push "GrowPatch seeds (mid radius, surface-m7)" "$OUT/seeds.json"
fi

# 1. environment (villa 41701aa VC3D apps incl. vc_grow_seg_from_seed + vc_tifxyz_selfcross, CPU vesuvius, sha-verified ckpt)
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || \
   [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_grow_seg_from_seed ] || \
   [ ! -x /opt/hv-ink/bin/python ] || [ ! -f "$CK" ]; then
  status "step 1 environment build running (setup_env.sh + vc_build.sh)"
  bash docker/env/setup_env.sh >>/work/logs/setup_env.log 2>&1 || { log "setup_env FAILED (see /work/logs/setup_env.log)"; exit 1; }
fi
docker info >/dev/null 2>&1 || bash docker/env/setup_env.sh >>/work/logs/setup_env.log 2>&1
echo "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab  $CK" | sha256sum -c --quiet || { log "ckpt sha mismatch"; exit 1; }

# per seed: grow -> selfcross + area gate -> [render -> infer -> tiles] -> push
$PY -c "
import json
for s in json.load(open('$OUT/seeds.json'))['seeds']:
  if s['seed_xyz_L0']: print(s['name'], *s['seed_xyz_L0'])" > $W/units.txt
NU=$(wc -l < $W/units.txt); k=0
while read -r SEG SX SY SZ <&3; do
  k=$((k+1)); D="$OUT/$SEG"; U=$W/$SEG; G=$U/grow; mkdir -p "$U" "$D"
  # --- grow unit
  if [ ! -s "$D/gate.json" ]; then
    status "unit $k/$NU $SEG: GrowPatch running (seed $SX $SY $SZ, gens $GROW_GENS, timeout $GROW_TIMEOUT)"
    rm -rf "$G"; mkdir -p "$G" "$W/cache"
    cat > "$U/grow_params.json" <<EOF
{"mode": "seed", "use_cuda": false, "voxelsize": $VOX, "step_size": 20, "generations": $GROW_GENS,
 "min_area_cm": 0, "snapshot-interval": 10, "thread_limit": 3, "cache_size": 4000000000, "cache_root": "$W/cache"}
EOF
    t0=$(date +%s)
    ( cd "$U" && timeout -s TERM "$GROW_TIMEOUT" /work/bin/vc vc_grow_seg_from_seed -v "$SURL" -t "$G" -p "$U/grow_params.json" \
        -s "$SX" "$SY" "$SZ" --segment-name "$SEG" ) > "$U/grow.log" 2>&1; rc=$?
    killvc; t1=$(date +%s)
    tail -80 "$U/grow.log" > "$D/grow_tail.log"; cp "$U/grow_params.json" "$D/"
    if [ -f "$G/x.tif" ] && [ -f "$G/meta.json" ]; then
      /work/bin/vc vc_tifxyz_selfcross --surface "$G" --output "$U/selfcross.json" > "$U/selfcross.log" 2>&1
      $PY $T/flx.py gate "$G" "$U/selfcross.json" "$D/gate.json" $VOX >>"$L" 2>&1
      cp "$U/selfcross.json" "$D/selfcross.json" 2>/dev/null
      $PY - "$D/gate.json" "$rc" "$((t1-t0))" <<'E'
import json, sys
g = json.load(open(sys.argv[1])); g['grow_rc'] = int(sys.argv[2]); g['grow_wall_s'] = int(sys.argv[3])
g['grow_note'] = 'rc 124 = timeout; the surface is then the last snapshot (snapshot-interval 10)'
json.dump(g, open(sys.argv[1], 'w'), indent=1)
E
      if $PY -c "import json,sys;sys.exit(0 if json.load(open('$D/gate.json'))['keep'] else 1)"; then
        mkdir -p "$D/tifxyz"; cp "$G"/*.tif "$G"/meta.json "$D/tifxyz/" 2>/dev/null
      fi
    else
      echo "{\"keep\": false, \"reject_reasons\": [\"no surface written (rc $rc)\"], \"grow_rc\": $rc, \"grow_wall_s\": $((t1-t0))}" > "$D/gate.json"
    fi
    status "unit $k/$NU $SEG: grow done, gate $(python3 -c "import json;g=json.load(open('$D/gate.json'));print('KEEP' if g['keep'] else 'REJECT', g.get('area_cm2_meta'), g['reject_reasons'])")"
    push "grow $SEG (gate)" "$D"
  fi
  $PY -c "import json,sys;sys.exit(0 if json.load(open('$D/gate.json'))['keep'] else 1)" || continue
  # --- render/infer/tiles unit
  TD="$D/tiles"
  if [ -f "$TD/manifest.json" ] && $PY -c "import json,sys;sys.exit(0 if len(json.load(open('$TD/manifest.json'))['runs'])>=2 else 1)"; then continue; fi
  MD=$U/mesh/$SEG; mkdir -p "$MD"; cp "$D/tifxyz/"* "$MD/"
  status "unit $k/$NU $SEG: render/infer running"
  $PY $T/flx.py prep "$SEG" "$MD" "$U" >>"$L" 2>&1 || { log "prep FAILED $SEG"; continue; }
  read -r X Y CW CH < <($PY -c "import json;print(*json.load(open('$U/crop.json'))['crop_xywh'])")
  R=$U/render.zarr
  if [ ! -f "$U/render.done" ]; then
    rm -rf "$R"; log "render $SEG crop $X $Y $CW $CH"
    ( cd "$U" && /work/bin/vc vc_render_tifxyz -v "$VURL" --remote-url "$VURL" --segmentation "$MD" --scale 1 --group-idx 0 \
        --num-slices 31 --slice-step 1 --voxel-size "$VOX" --voxel-unit micrometer \
        --crop-x "$X" --crop-y "$Y" --crop-width "$CW" --crop-height "$CH" --flip-normals --cache-gb 4 --zarr-output "$R" ) \
        > "$U/render.log" 2>&1 && touch "$U/render.done" || { log "render FAILED $SEG"; tail -50 "$U/render.log" > "$D/render_fail.log"; push "render FAILED $SEG" "$D"; continue; }
  fi
  mkdir -p "$U/infer"
  if [ ! -f "$U/infer.done" ]; then
    log "infer $SEG"
    /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CK" "$U/infer/$SEG.tif" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$U/infer.log" 2>&1 && touch "$U/infer.done" || { log "infer FAILED $SEG"; tail -50 "$U/infer.log" > "$D/infer_fail.log"; push "infer FAILED $SEG" "$D"; continue; }
  fi
  rm -f "$TD/manifest.json"
  for P in "$U"/infer/*.tif; do
    case "$P" in *_reverse.tif) TAG=reverse;; *) TAG=forward;; esac
    $PY $T/flx.py tiles "$U" "$P" "$TD" "$TAG" "$VOX" auto >>"$L" 2>&1 || log "tiles FAILED $SEG $TAG"
  done
  cp "$U/crop.json" "$D/"; tail -40 "$U/render.log" > "$D/render_tail.log" 2>/dev/null; tail -50 "$U/infer.log" > "$D/infer_tail.log" 2>/dev/null
  status "unit $k/$NU $SEG: tiles done ($(ls "$TD"/*.png 2>/dev/null | wc -l) PNG)"
  push "tiles $SEG" "$D"
  rm -rf "$R"   # disk; predictions stay in $U/infer
done 3< $W/units.txt
NK=$(ls "$OUT"/*/tiles/manifest.json 2>/dev/null | wc -l); NP=$(ls "$OUT"/*/tiles/*.png 2>/dev/null | wc -l)
status "ALL DONE: $NU seeds grown, $NK segments kept and tiled, $NP PNG tiles; gates in logs/sib/fl-pherc0483b/*/gate.json"
push "all units done" "$OUT"
touch $W/DONE
