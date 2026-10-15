#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# fl3-pherc0343: DECL-FL-1 First Letters extra PASS 3 on PHerc0343 (8.64 um), per tools/fl/BRIEF_PASS.md (dcb6a6ba).
# Adapted from tools/sib/fl-pherc0175b/pipeline.sh (commit 0d02bb5). Idempotent; commits and pushes after
# every unit. Resume rule: a unit is skipped when its pushed record exists in the repo (grown meshes are pushed too,
# so a container restart re-renders but never re-grows). Run: setsid nohup bash watchdog.sh &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-p4-tiles-b
T=tools/sib/fl3-pherc0343; OUT=logs/sib/fl3-pherc0343; W=/work/fl3-0343; mkdir -p "$OUT/grow" "$W" /work/logs
L=$W/pipeline.log
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKSHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
VOX=8.64
S3H=https://vesuvius-challenge-open-data.s3.amazonaws.com
VOLURL=$S3H/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr/
SURFB=$S3H/PHerc0343/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2
MAXSEG=4
export AWS_CA_BUNDLE=/root/.ccr/ca-bundle.crt REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt OMP_NUM_THREADS=3
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
status() { echo "$(date -u +%FT%TZ) fl3-pherc0343: $*" > "$OUT/STATUS.md"; log "STATUS $*"; }
push() { # push <msg> <paths...>
  local msg=$1; shift
  git add -- "$@" "$OUT/STATUS.md" 2>>"$L"
  # session attribution lines are kept outside the repo, in $W/attr.txt (written at launch)
  local attr=""; [ -s "$W/attr.txt" ] && attr=$(printf '\n\n%s' "$(cat "$W/attr.txt")")
  git commit -q -m "fl3-pherc0343: $msg

Provenance: Project HERCULES | owner the owner | [id removed]$attr" >>"$L" 2>&1 || true
  for i in 1 2 3 4 5; do
    git pull -q --rebase origin "$BR" 2>>"$L"; git push -q -u origin "$BR" 2>>"$L" && return 0; sleep $((2**i)); done
  log "push failed: $msg"; }

# 0. minimal python (listing, seeds, geometry, tiles)
[ -x /opt/hv/bin/python ] || { uv venv /opt/hv --python 3.11 -q && VIRTUAL_ENV=/opt/hv uv pip install -q numpy scipy opencv-python-headless tifffile imagecodecs "zarr<3" numcodecs pillow requests boto3; } >>"$L" 2>&1
PY=/opt/hv/bin/python

# 2a. segment listing (anonymous)
if [ ! -s "$OUT/listing.json" ]; then
  status "step 2 listing s3://vesuvius-challenge-open-data/PHerc0343/"
  $PY $T/fl3.py listing "$OUT/listing.json" >>"$L" 2>&1 || { log "listing FAILED"; exit 1; }
  push "S3 listing of PHerc0343" "$OUT/listing.json"
fi
ROUTE=$($PY -c "import json;print(json.load(open('$OUT/listing.json'))['route'])")

# 1. environment (VC3D apps from villa 41701aa via official deps image; vesuvius CPU; sha-verified checkpoint)
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || [ ! -x /opt/hv-ink/bin/python ] \
   || [ ! -f "$CK" ] || ! docker info >/dev/null 2>&1; then
  status "step 1 environment (setup_env.sh + vc_build.sh) running"
  bash docker/env/setup_env.sh >>/work/logs/setup_env.log 2>&1 || { log "setup_env FAILED (see /work/logs/setup_env.log)"; exit 1; }
fi
echo "$CKSHA  $CK" | sha256sum -c --quiet || { log "ckpt sha mismatch"; exit 1; }
for a in vc_render_tifxyz vc_grow_seg_from_seed vc_tifxyz_selfcross; do
  [ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/$a ] || { log "missing $a"; exit 1; }; done

# 2b. material
nkept() { ls "$OUT"/*/geometry.json 2>/dev/null | xargs -r grep -l '"keep": true' | wc -l; }
if [ "$ROUTE" = organizer ]; then
  [ -s "$OUT/selection.json" ] || { $PY $T/fl3.py select "$OUT/listing.json" "$OUT/selection.json" >>"$L" 2>&1 && push "organizer selection (ranks 10-15)" "$OUT/selection.json"; }
  NSEL=$($PY -c "import json;print(len(json.load(open('$OUT/selection.json'))['segments']))")
  if [ "$NSEL" = 0 ]; then status "DONE: no segments in range"; push "DONE: no segments in range" "$OUT"; touch $W/DONE; exit 0; fi
  $PY -c "
import json
for r in json.load(open('$OUT/selection.json'))['segments']: print(r['segment'], r['mesh_key'])" > $W/org.txt
  while read -r SEG MK <&3; do
    D="$OUT/$SEG"; [ -s "$D/geometry.json" ] && continue
    mkdir -p "$D"; $PY $T/fl3.py fetch_mesh "$MK" "$W/seg/$SEG/mesh" >>"$L" 2>&1 || { log "fetch FAILED $SEG"; continue; }
    /work/bin/vc vc_tifxyz_selfcross "$W/seg/$SEG/mesh" -o "$W/seg/$SEG/selfcross.json" >>"$L" 2>&1
    $PY $T/fl3.py geom "$W/seg/$SEG/mesh" "$W/seg/$SEG/selfcross.json" $VOX "$D/geometry.json" >>"$L" 2>&1
    # organizer segments are the published material: the gate is recorded, not applied
    $PY -c "import json;g=json.load(open('$D/geometry.json'));g['keep']=True;g['source']='organizer';json.dump(g,open('$D/geometry.json','w'),indent=1)"
    cp "$W/seg/$SEG/selfcross.json" "$D/selfcross.json" 2>/dev/null
    push "organizer segment $SEG geometry" "$D"
  done 3< $W/org.txt
else
  [ -s "$OUT/seeds.json" ] || { status "step 2 seed plan (surface-m7 level 5 -> level 0 snap)";
    $PY $T/fl3.py seeds "$OUT/seeds.json" >>"$L" 2>&1 && push "GrowPatch seed plan, inner third of radius" "$OUT/seeds.json" || { log "seeds FAILED"; exit 1; }; }
  NC=$($PY -c "import json;print(len(json.load(open('$OUT/seeds.json'))['candidates']))")
  for k in $(seq 0 $((NC-1))); do
    [ "$(nkept)" -ge $MAXSEG ] && break
    R="$OUT/grow/cand_$k.json"; [ -s "$R" ] && continue
    SEG=auto_pherc0343_p3_c$(printf %02d $k); G=$W/grow/$SEG
    if ! $PY $T/fl3.py exclude "$OUT/seeds.json" $k "$OUT" >>"$L" 2>&1; then
      echo "{\"k\": $k, \"segment\": \"$SEG\", \"outcome\": \"skipped (no seed, or seed within 2 mm of a kept segment)\", \"utc\": \"$(date -u +%FT%TZ)\"}" > "$R"
      push "grow cand $k skipped" "$R"; continue; fi
    read -r SX SY SZ < <($PY -c "import json;print(*json.load(open('$OUT/seeds.json'))['candidates'][$k]['seed_xyz'])")
    NG=""
    for variant in normalgrid plain; do
      rm -rf "$G"; mkdir -p "$G"
      $PY - "$G/params.json" "$variant" <<EOF
import json, sys
p = {"step_size": 20, "generations": 200, "min_area_cm": 0, "thread_limit": 3, "voxelsize": $VOX,
     "cache_size": 3e9, "cache_root": "/work/fl3-0343/cache"}
if sys.argv[2] == "normalgrid":
    p["normal_grid_path"] = "$SURFB.normal-grids"
json.dump(p, open(sys.argv[1], "w"), indent=1)
EOF
      status "grow cand $k ($variant) seed $SX $SY $SZ; kept so far $(nkept)/$MAXSEG"
      timeout 4h /work/bin/vc vc_grow_seg_from_seed -v "$SURFB.zarr/" -t "$G" -p "$G/params.json" -s $SX $SY $SZ \
        --segment-name "$SEG" > "$G/grow.log" 2>&1; RC=$?
      [ $RC = 0 ] && [ -f "$G/x.tif" ] && { NG=$variant; break; }
      log "grow cand $k $variant rc=$RC"; cp "$G/grow.log" "$W/grow_${k}_${variant}.log" 2>/dev/null
    done
    if [ -z "$NG" ]; then
      echo "{\"k\": $k, \"segment\": \"$SEG\", \"outcome\": \"grow failed (both variants)\", \"utc\": \"$(date -u +%FT%TZ)\"}" > "$R"
      tail -30 "$G/grow.log" > "$OUT/grow/cand_${k}_grow_tail.log" 2>/dev/null
      push "grow cand $k failed" "$R" "$OUT/grow/cand_${k}_grow_tail.log"; continue; fi
    /work/bin/vc vc_tifxyz_selfcross "$G" -o "$G/selfcross.json" > "$G/selfcross.log" 2>&1
    $PY $T/fl3.py geom "$G" "$G/selfcross.json" $VOX "$G/geometry.json" >>"$L" 2>&1 || { log "geom FAILED $k"; }
    KEEP=$($PY -c "import json;g=json.load(open('$G/geometry.json'));print(int(g['keep']))" 2>/dev/null || echo 0)
    $PY -c "
import json;g=json.load(open('$G/geometry.json')) if __import__('os').path.exists('$G/geometry.json') else {}
json.dump({'k':$k,'segment':'$SEG','variant':'$NG','seed_xyz':[$SX,$SY,$SZ],'outcome':'kept' if $KEEP else 'rejected by gate',
 'gate':g.get('gate'),'meta_area_cm2':g.get('meta_area_cm2'),'grid_area_cm2':g.get('grid_area_cm2'),
 'selfcross_transverse':g.get('selfcross_transverse'),'utc':'$(date -u +%FT%TZ)'},open('$R','w'),indent=1)"
    cp "$G/grow.log" "$W/grow_${k}.log"; tail -40 "$G/grow.log" > "$OUT/grow/cand_${k}_grow_tail.log"
    if [ "$KEEP" = 1 ]; then
      D="$OUT/$SEG"; mkdir -p "$D/mesh"
      cp "$G"/{x,y,z}.tif "$G/meta.json" "$D/mesh/"; [ -f "$G/mask.tif" ] && cp "$G/mask.tif" "$D/mesh/"
      cp "$G/params.json" "$G/selfcross.json" "$D/"
      $PY -c "import json;g=json.load(open('$G/geometry.json'));g['source']='auto';g['grow_variant']='$NG';json.dump(g,open('$D/geometry.json','w'),indent=1)"
      push "auto segment $SEG kept (geometry gate passed)" "$R" "$OUT/grow/cand_${k}_grow_tail.log" "$D"
    else
      cp "$G/geometry.json" "$OUT/grow/cand_${k}_geometry.json" 2>/dev/null
      push "grow cand $k rejected by gate" "$R" "$OUT/grow/cand_${k}_grow_tail.log" "$OUT/grow/cand_${k}_geometry.json"
    fi
  done
fi

# 3-4. per kept segment: prep -> render (C2-NT) -> infer (both, no TTA) -> tiles -> push
ls "$OUT"/*/geometry.json 2>/dev/null | xargs -r grep -l '"keep": true' | xargs -r -n1 dirname | xargs -r -n1 basename > $W/units.txt
NU=$(wc -l < $W/units.txt); k=0
[ "$NU" = 0 ] && { status "STOP: no segment passed the gate (see $OUT/grow/*.json)"; echo "DONE 0 tiles" >> "$OUT/STATUS.md"; push "stop: no segment; DONE 0 tiles" "$OUT"; touch $W/DONE; exit 0; }
while read -r SEG <&3; do
  k=$((k+1)); D="$OUT/$SEG"; TD="$D/tiles"; U=$W/unit/$SEG; mkdir -p "$U"
  if [ -f "$TD/manifest.json" ] && $PY -c "import json,sys;sys.exit(0 if len(json.load(open('$TD/manifest.json'))['runs'])>=2 else 1)"; then continue; fi
  SRC=$($PY -c "import json;print(json.load(open('$D/geometry.json')).get('source','auto'))")
  MD=$([ -d "$D/mesh" ] && echo "$REPO/$D/mesh" || echo "$W/seg/$SEG/mesh")
  status "unit $k/$NU $SEG ($SRC): prep/render/infer running"
  [ -s "$U/crop.json" ] || $PY $T/fl3.py prep "$MD" "$U" >>"$L" 2>&1 || { log "prep FAILED $SEG"; continue; }
  read -r X Y CW CH < <($PY -c "import json;print(*json.load(open('$U/crop.json'))['crop_xywh'])")
  R=$U/render.zarr
  if [ ! -f "$U/render.done" ]; then
    rm -rf "$R"; log "render $SEG crop $X $Y $CW $CH"
    ( cd "$U" && /work/bin/vc vc_render_tifxyz -v "$VOLURL" --remote-url "$VOLURL" --segmentation "$MD" --scale 1 --group-idx 0 \
        --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --timeout 480 \
        --crop-x "$X" --crop-y "$Y" --crop-width "$CW" --crop-height "$CH" --flip-normals --cache-gb 4 --zarr-output "$R" ) \
        > "$U/render.log" 2>&1 && touch "$U/render.done" || { log "render FAILED $SEG"; cp "$U/render.log" "$D/render_failed.log"; push "render failed $SEG" "$D/render_failed.log"; continue; }
  fi
  mkdir -p "$U/infer"
  if [ ! -f "$U/infer.done" ]; then
    log "infer $SEG"
    timeout 10h /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CK" "$U/infer/$SEG.tif" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$U/infer.log" 2>&1 && touch "$U/infer.done" \
      || { log "infer FAILED $SEG"; tail -50 "$U/infer.log" > "$D/infer_failed_tail.log"; push "infer failed $SEG" "$D/infer_failed_tail.log"; continue; }
  fi
  rm -f "$TD/manifest.json"
  for P in "$U"/infer/*.tif; do
    case "$P" in *_reverse.tif) TAG=reverse;; *) TAG=forward;; esac
    $PY $T/fl3.py tiles "$U" "$P" "$TD" "$TAG" $VOX "$SRC" >>"$L" 2>&1 || log "tiles FAILED $SEG $TAG"
  done
  cp "$U/render.log" "$D/render.log" 2>/dev/null; tail -50 "$U/infer.log" > "$D/infer_tail.log" 2>/dev/null; cp "$U/crop.json" "$D/crop.json"
  status "unit $k/$NU $SEG done: $($PY -c "import json;M=json.load(open('$TD/manifest.json'));print(', '.join('%s kept %d/%d'%(t,r['tiles_kept'],r['tiles_total']) for t,r in M['runs'].items()))" 2>/dev/null)"
  push "tiles $SEG" "$D"
  rm -rf "$R"
done 3< $W/units.txt
NT=$($PY -c "
import json,glob
n=0
for f in glob.glob('$OUT/*/tiles/manifest.json'):
    for r in json.load(open(f))['runs'].values(): n+=r['tiles_kept']
print(n)")
status "ALL DONE: $NU segments; tiles under $OUT/<segment>/tiles/ (manifest.json each)"
echo "DONE $NT tiles" >> "$OUT/STATUS.md"
push "all units done: DONE $NT tiles" "$OUT"
touch $W/DONE
