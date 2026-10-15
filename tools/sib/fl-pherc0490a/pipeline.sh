#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# fl-pherc0490a: DECL-FL-1 First Letters screen for PHerc0490A (OWNER-STANDING-ORDER-5, detached, zero-turn).
# Idempotent. A unit is skipped when its PUSHED output exists in the repo, so after a container restart
# `bash tools/sib/fl-pherc0490a/watchdog.sh` resumes from the last pushed unit (grown tifxyz are pushed too).
# Numbers, hashes and file lists only: nothing here opens or describes an image.
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-fl-pherc0490a
SC=PHerc0490A
OUT=logs/sib/fl-pherc0490a; W=/work/fl0490a; mkdir -p "$OUT" "$W" /work/logs
L=$W/pipeline.log
T=tools/sib/fl-pherc0490a
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
VOX=8.64
MAX_ATTEMPTS=8; MAX_KEEP=4; GROW_TIMEOUT=${GROW_TIMEOUT:-5h}
export AWS_CA_BUNDLE=/root/.ccr/ca-bundle.crt REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt OMP_NUM_THREADS=3
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
status() { echo "$(date -u +%FT%TZ) fl-pherc0490a: $*" > "$OUT/STATUS.md"; }
push() { # push <msg> <paths...>
  local msg=$1; shift
  git add -- "$@" "$OUT/STATUS.md" 2>/dev/null
  git -c user.name="fl-pherc0490a" -c user.email="noreply@anthropic.com" commit -q -m "fl-pherc0490a: $msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019WYQ2MCNFU2H2e2b6zB989" || true
  for i in 1 2 3 4 5; do
    git pull -q --rebase origin "$BR" 2>>"$L"; git push -q -u origin "$BR" 2>>"$L" && return 0; sleep $((2**i)); done
  log "push failed: $msg"; }
jget() { /opt/hv/bin/python -c "import json,sys;d=json.load(open(sys.argv[1]));print(eval(sys.argv[2]))" "$@"; }

# 1. environment (VC3D apps from villa 41701aa, CPU vesuvius, sha-verified ink_9um step-075000)
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
while pgrep -f "docker/env/setup_env.sh" >/dev/null; do sleep 30; done   # an instance already running
if [ ! -x $BIN/vc_render_tifxyz ] || [ ! -x $BIN/vc_grow_seg_from_seed ] || [ ! -x $BIN/vc_tifxyz_selfcross ] \
   || [ ! -x /opt/hv-ink/bin/python ] || [ ! -x /opt/hv/bin/python ] || [ ! -f "$CK" ] || ! docker info >/dev/null 2>&1; then
  status "step 1 environment build running"
  bash docker/env/setup_env.sh >>/work/logs/setup_env.log 2>&1 || { log "setup_env FAILED (see /work/logs/setup_env.log)"; status "step 1 FAILED setup_env"; exit 1; }
fi
[ -x $BIN/vc_grow_seg_from_seed ] && [ -x $BIN/vc_tifxyz_selfcross ] || { log "VC3D apps missing"; status "step 1 FAILED: VC3D apps missing"; exit 1; }
echo "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab  $CK" | sha256sum -c --quiet || { log "ckpt sha mismatch"; exit 1; }
PY=/opt/hv/bin/python

# 2. segments: anonymous listing -> organizer (3 largest tifxyz) or auto (GrowPatch on surface-m7)
if [ ! -s "$OUT/listing.json" ]; then
  status "step 2 listing"
  $PY $T/fl.py listing "$W/listing.json" >>"$L" 2>&1 && cp "$W/listing.json" "$OUT/listing.json" || { log "listing FAILED"; exit 1; }
  push "S3 listing of $SC (mode $(jget "$OUT/listing.json" "d['mode']"))" "$OUT/listing.json"
fi
MODE=$(jget "$OUT/listing.json" "d['mode']")
: > $W/units.txt   # SEG MESHDIR SOURCE
if [ "$MODE" = organizer ]; then
  $PY -c "import json;[print(r['segment'],r['mesh_key']) for r in json.load(open('$OUT/listing.json'))['selected_organizer']]" |
  while read -r SEG MK; do
    MD=$W/mesh/$SEG; [ -s "$MD/x.tif" ] || $PY $T/fl.py fetch "$MK" "$MD" >>"$L" 2>&1 || { log "fetch FAILED $SEG"; continue; }
    echo "$SEG $MD organizer" >> $W/units.txt
  done
else
  SURF=$(jget "$OUT/listing.json" "d['surface_m7_zarrs'][0]"); SURF=${SURF%/}
  SURL="https://vesuvius-challenge-open-data.s3.amazonaws.com/${SURF#s3://vesuvius-challenge-open-data/}"
  if [ ! -s "$OUT/seeds.json" ]; then
    status "step 2 seed selection on $SURF"
    $PY $T/fl.py seeds "$OUT/listing.json" "$W/seeds.json" >>"$L" 2>&1 && cp "$W/seeds.json" "$OUT/seeds.json" || { log "seeds FAILED"; status "step 2 FAILED seeds"; exit 1; }
    push "GrowPatch seeds (mid radius, surface-m7 >= 128)" "$OUT/seeds.json"
  fi
  cat > $W/grow_params.json <<J
{"mode": "seed", "cache_size": 4000000000, "generations": 160, "step_size": 20, "thread_limit": 3, "voxelsize": $VOX}
J
  mkdir -p "$OUT/grow"; cp $W/grow_params.json "$OUT/grow/params.json"
  for k in $(seq 0 $((MAX_ATTEMPTS-1))); do
    NK=$(ls "$OUT"/grow/s*.json 2>/dev/null | xargs -r grep -l '"keep": true' | wc -l)
    [ "$NK" -ge $MAX_KEEP ] && break
    SEG=fl0490a_auto_s$k; G="$OUT/grow/s$k.json"
    [ -s "$G" ] && continue
    read -r X Y Z < <(jget "$OUT/seeds.json" "' '.join(map(str,d['seeds'][$k]['seed_xyz']))")
    GD=$W/grow/$SEG; rm -rf "$GD"; mkdir -p "$W/grow"
    status "step 2 grow attempt $((k+1))/$MAX_ATTEMPTS ($NK kept) $SEG seed $X $Y $Z"
    log "grow $SEG seed $X $Y $Z"
    t0=$(date +%s)
    ( cd $W/grow && VC_CPUS=3 OMP_NUM_THREADS=3 timeout --kill-after=60 "$GROW_TIMEOUT" /work/bin/vc vc_grow_seg_from_seed -v "$SURL" -t "$GD" \
        -p $W/grow_params.json --seed "$X" "$Y" "$Z" --segment-name "$SEG" --skip-overlap-check ) > "$W/grow/$SEG.log" 2>&1
    rc=$?; dt=$(( $(date +%s) - t0 ))
    docker ps -q --filter ancestor=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f | xargs -r docker kill >/dev/null 2>&1
    mkdir -p "$OUT/grow/logs"; tail -60 "$W/grow/$SEG.log" > "$OUT/grow/logs/$SEG.tail.log"
    if [ -s "$GD/x.tif" ] && [ -s "$GD/meta.json" ]; then
      VC_CPUS=3 /work/bin/vc vc_tifxyz_selfcross "$GD" -o "$GD/selfcross.json" --threads 3 > "$W/grow/$SEG.selfcross.log" 2>&1
      $PY $T/fl.py gate "$GD" "$GD/selfcross.json" "$W/grow/$SEG.gate.json" >>"$L" 2>&1
    fi
    $PY - "$W/grow/$SEG.gate.json" "$G" "$SEG" "$rc" "$dt" "$X $Y $Z" <<'P'
import json, os, sys
g, out, seg, rc, dt, seed = sys.argv[1:]
d = json.load(open(g)) if os.path.exists(g) else {'segment': seg, 'keep': False, 'reason': 'no tifxyz produced'}
d.update(grow_rc=int(rc), grow_seconds=int(dt), seed_xyz=[int(v) for v in seed.split()], source='auto',
         grow_cmd='vc_grow_seg_from_seed -v <surface-m7 L0 https> -p grow/params.json --seed X Y Z --segment-name SEG --skip-overlap-check (villa 41701aa)')
json.dump(d, open(out, 'w'), indent=1)
P
    if grep -q '"keep": true' "$G"; then
      mkdir -p "$OUT/$SEG/tifxyz"
      cp "$GD"/x.tif "$GD"/y.tif "$GD"/z.tif "$GD"/meta.json "$OUT/$SEG/tifxyz/"
      [ -f "$GD/mask.tif" ] && cp "$GD/mask.tif" "$OUT/$SEG/tifxyz/"
      cp "$GD/selfcross.json" "$OUT/$SEG/selfcross.json"
    fi
    push "grow attempt $SEG: $(jget "$G" "('KEEP ' if d['keep'] else 'DROP ')+d['reason']")" "$OUT/grow" "$OUT/$SEG"
  done
  for G in "$OUT"/grow/s*.json; do
    [ -f "$G" ] && grep -q '"keep": true' "$G" || continue
    SEG=$(jget "$G" "d['segment']"); echo "$SEG $REPO/$OUT/$SEG/tifxyz auto" >> $W/units.txt
  done
fi
NU=$(wc -l < $W/units.txt)
if [ "$NU" = 0 ]; then
  status "STOP after step 2: mode $MODE, 0 segments passed (see $OUT/grow/*.json)"; push "stop: no segment passed the gate" "$OUT"; touch $W/DONE; exit 0; fi

# 3-4. per segment: prep -> render (C2-NT) -> infer (both, no TTA) -> tiles -> push
URL="https://vesuvius-challenge-open-data.s3.amazonaws.com/$SC/volumes/$(jget "$OUT/listing.json" "d['volume_zarr'].rstrip('/')")/"
k=0
while read -r SEG MD SRC <&3; do
  k=$((k+1)); D="$OUT/$SEG/tiles"; U=$W/units/$SEG; mkdir -p "$U" "$D"
  if [ -f "$D/manifest.json" ] && $PY -c "import json,sys;sys.exit(0 if len(json.load(open('$D/manifest.json'))['runs'])>=2 else 1)"; then continue; fi
  status "unit $k/$NU $SEG ($SRC): prep/render/infer running"
  [ -s "$U/crop.json" ] || $PY $T/fl.py prep "$SEG" "$MD" "$U" >>"$L" 2>&1 || { log "prep FAILED $SEG"; continue; }
  read -r X Y CW CH < <(jget "$U/crop.json" "' '.join(map(str,d['crop_xywh']))")
  R=$U/render.zarr
  if [ ! -f "$U/render.done" ]; then
    rm -rf "$R"; log "render $SEG crop $X $Y $CW $CH"
    ( cd "$U" && /work/bin/vc vc_render_tifxyz -v "$URL" --remote-url "$URL" --segmentation "$MD" --scale 1 --group-idx 0 \
        --num-slices 31 --slice-step 1 --voxel-size "$VOX" --voxel-unit micrometer \
        --crop-x "$X" --crop-y "$Y" --crop-width "$CW" --crop-height "$CH" --flip-normals --cache-gb 4 --zarr-output "$R" ) \
        > "$U/render.log" 2>&1 && touch "$U/render.done" || { log "render FAILED $SEG"; tail -40 "$U/render.log" > "$OUT/$SEG/render_fail.log"; push "render FAILED $SEG" "$OUT/$SEG"; continue; }
  fi
  mkdir -p "$U/infer"
  if [ ! -f "$U/infer.done" ]; then
    log "infer $SEG"
    /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CK" "$U/infer/$SEG.tif" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$U/infer.log" 2>&1 && touch "$U/infer.done" || { log "infer FAILED $SEG"; tail -40 "$U/infer.log" > "$OUT/$SEG/infer_fail.log"; push "infer FAILED $SEG" "$OUT/$SEG"; continue; }
  fi
  for P in "$U"/infer/*.tif; do
    case "$P" in *_reverse.tif) TAG=reverse;; *) TAG=forward;; esac
    $PY $T/fl.py tiles "$U" "$P" "$D" "$TAG" "$SRC" >>"$L" 2>&1 || log "tiles FAILED $SEG $TAG"
  done
  cp "$U/crop.json" "$OUT/$SEG/crop.json"; tail -30 "$U/render.log" > "$OUT/$SEG/render_tail.log" 2>/dev/null
  tail -30 "$U/infer.log" > "$OUT/$SEG/infer_tail.log" 2>/dev/null
  status "unit $k/$NU $SEG done: $(jget "$D/manifest.json" "', '.join(f\"{t} {r['tiles_kept']}/{r['tiles_total']}\" for t,r in d['runs'].items())") tiles kept"
  push "tiles $SEG" "$OUT/$SEG"
  rm -rf "$R"
done 3< $W/units.txt
NT=$(ls "$OUT"/*/tiles/*.png 2>/dev/null | wc -l)
status "ALL DONE: mode $MODE, $NU segments, $NT tiles (both directions); manifests at $OUT/<segment>/tiles/manifest.json"
push "all units done" "$OUT"
touch $W/DONE
