#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters extra pass, PHerc0800 PASS 3 (tools/fl/BRIEF_PASS.md @ dcb6a6b); adapted from
# tools/sib/fl-pherc0813/pipeline.sh. Volume 20250521135224, 8.640 um. Idempotent: every unit leaves a marker under
# logs/sib/fl3-pherc0800/units/ (pushed); finished units are skipped. Commits + pushes per unit.
# Rank range 10-15 is EMPTY: the bucket holds 6 organizer segments (s3 PHerc0800/segments/, listed 2026-09-30).
# So the PASS 3 rule applies: auto-grow up to 4 segments (vc_grow_seg_from_seed, explicit --seed) on the organizer
# surface-m7 L0 prediction, seeded in the INNER third of the scroll radius (fl_tools.py seeds; seeds fixed and pushed
# before any growth). Kept iff vc_tifxyz_selfcross finds 0 transverse contacts and area >= 16 cm^2.
# Launch: nohup bash tools/sib/fl3-pherc0800/run.sh > /work/fl/run.log 2>&1 &
set -euo pipefail
REPO=/home/user/dominion
BR=claude/gifted-bell-gavnl5-sib-dev-distft
L=$REPO/logs/sib/fl3-pherc0800; U=$L/units; W=/work/fl
S3=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0800
VOL=$S3/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr
SURF=$S3/representations/predictions/surfaces/20250521135224-surface-20260413222639-surface-m7-L0-th0.2.zarr
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
PY=/opt/hv/bin/python; LR="bash $REPO/tools/c3/ledger_run.sh"; VC=/work/bin/vc
NGROW=4; MIN_CM2=16
mkdir -p "$U" "$W"/segs "$W"/render "$W"/infer "$W"/logs "$W"/cache
export VC_CPUS=3 OMP_NUM_THREADS=3
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { echo "[$(utc)] $*"; }
push() {  # commit+push this worker's files only
  cd "$REPO"; git add -A logs/sib/fl3-pherc0800 tools/sib/fl3-pherc0800 2>/dev/null || true
  git diff --cached --quiet || git commit -q -m "fl3-pherc0800: $1

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018MPzKxBJy8gwCSqvMeSeW7"
  for i in 1 2 3 4 5; do git push -q -u origin "$BR" && return 0; sleep $((2**i)); done; say "push failed"; return 0; }
diskok() { local a; a=$(df -BG --output=avail /work 2>/dev/null | tail -1 | tr -dc 0-9); [ "${a:-0}" -ge 5 ]; }
status() { printf '%s | %s\n' "$(utc)" "$1" >> "$L/STATUS.md"; }

# 0. An existing sparse /work/villa (vesuvius + ink-detection only) must also hold the VC3D sources for vc_build.sh.
if [ -d /work/villa/.git ] && [ ! -d /work/villa/volume-cartographer ]; then
  git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection
  git -C /work/villa checkout -q 41701aa0eaa1aa765523db3f9f972b5830abf549
fi
# 1. Environment (setup_env builds VC3D via vc_build.sh at villa 41701aa, CPU vesuvius, sha-checked checkpoint)
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_grow_seg_from_seed ] || [ ! -x "$PY" ] \
   || [ ! -x /opt/hv-ink/bin/python ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet 2>/dev/null; then
  say "setup_env"; bash "$REPO/docker/env/setup_env.sh" > "$W/logs/setup_env.log" 2>&1
fi
docker info >/dev/null 2>&1 || bash "$REPO/docker/env/setup_env.sh" >> "$W/logs/setup_env.log" 2>&1
echo "$CKPT_SHA  $CK" | sha256sum -c --quiet
for b in vc_grow_seg_from_seed vc_tifxyz_selfcross vc_render_tifxyz; do
  test -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/$b; done
if [ ! -f "$U/env.json" ]; then
  B=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
  printf '{"utc":"%s","villa":"%s","ckpt_sha256":"%s","bins":{"vc_grow_seg_from_seed":"%s","vc_tifxyz_selfcross":"%s","vc_render_tifxyz":"%s"},"segments_source":"auto, PASS 3 inner third (bucket PHerc0800/segments/ has 6 organizer segments; ranks 10-15 empty)","surface":"%s","volume":"%s"}\n' \
    "$(utc)" "$(git -C /work/villa rev-parse HEAD)" "$CKPT_SHA" "$(sha256sum $B/vc_grow_seg_from_seed|cut -c1-64)" \
    "$(sha256sum $B/vc_tifxyz_selfcross|cut -c1-64)" "$(sha256sum $B/vc_render_tifxyz|cut -c1-64)" "$SURF" "$VOL" > "$U/env.json"
  status "env ready; picking inner-third seeds"; push "environment ready"
fi

# 2a. Seeds (PASS 3: inner third of the radius), fixed and pushed before any growth.
if [ ! -f "$U/seeds.json" ]; then
  $PY "$REPO/tools/sib/fl3-pherc0800/fl_tools.py" seeds "$SURF" $NGROW "$L/seeds.json" > "$W/logs/seeds.log" 2>&1
  cp "$L/seeds.json" "$U/seeds.json"; status "seeds fixed (inner third); growing"; push "inner-third seeds"
fi
# 2b. Grow (one unit per seed). Params are fixed before any growth and pushed with the seeds.
cat > "$L/grow_params.json" <<J
{"mode":"seed","voxelsize":8.640,"min_area_cm":$MIN_CM2,"step_size":20,"generations":150,"thread_limit":3,
 "cache_size":4000000000,"cache_root":"$W/cache/grow","tgt_overlap_count":20,"search_effort":10}
J
for k in $(seq 0 $((NGROW-1))); do
  [ -f "$U/grow_$k.json" ] && continue
  diskok || { status "BLOCKED: <5 GB free on /work"; push "disk low"; exit 1; }
  SEED=$($PY -c "import json,sys;b=json.load(open(sys.argv[1]))['bands'][int(sys.argv[2])];print(' '.join(map(str,b['seed_xyz'])) if b.get('seed_xyz') else '')" "$U/seeds.json" $k)
  if [ -z "$SEED" ]; then printf '{"k":%d,"segment":null,"kept":false,"reason":"no inner-third seed in band"}\n' $k > "$U/grow_$k.json"; push "grow $k: no seed"; continue; fi
  say "grow $k seed $SEED"; before=$(ls "$W/segs" | sort)
  set +e; timeout 8h $LR "$W/segs" "$W/logs/grow_$k.log" $VC vc_grow_seg_from_seed -v "$SURF" -t "$W/segs" -p "$L/grow_params.json" --seed $SEED; rc=$?; set -e
  new=$(comm -13 <(echo "$before") <(ls "$W/segs" | sort) | grep '^auto_grown_' | head -1 || true)
  seed="$SEED (explicit, inner third)"
  if [ -z "$new" ]; then
    printf '{"k":%d,"rc":%d,"segment":null,"kept":false,"reason":"no segment written (area < %s cm2 or no seed)","seed":"%s"}\n' $k $rc $MIN_CM2 "$seed" > "$U/grow_$k.json"
    push "grow $k: no segment"; continue; fi
  S="$W/segs/$new"
  $PY "$REPO/tools/sib/fl3-pherc0800/fl_tools.py" geom "$S" "$L/$new.geom.json" > /dev/null
  set +e; $LR "$L/$new.selfcross.json" "$W/logs/selfcross_$k.log" $VC vc_tifxyz_selfcross "$S" -o "$L/$new.selfcross.json" --fail-on-crossing; src=$?; set -e
  kept=$($PY - "$L/$new.selfcross.json" "$L/$new.geom.json" $src $MIN_CM2 <<'P'
import json,sys
sc=json.load(open(sys.argv[1])); g=json.load(open(sys.argv[2])); src=int(sys.argv[3]); m=float(sys.argv[4])
clean=bool(sc.get('clean_of_transverse_self_intersection')) and src==0
print(json.dumps(dict(clean_of_transverse=clean, selfcross_rc=src, area_cm2=g['area_cm2'], kept=clean and g['area_cm2']>=m)))
P
)
  printf '{"k":%d,"rc":%d,"segment":"%s","seed":"%s","gate":%s}\n' $k $rc "$new" "$seed" "$kept" > "$U/grow_$k.json"
  if echo "$kept" | grep -q '"kept": true'; then
    mkdir -p "$L/$new/tifxyz"; cp "$S"/*.tif "$S"/meta.json "$L/$new/tifxyz/" 2>/dev/null || true; fi
  status "grow $k -> $new $kept"; push "grow $k: $new"
done

# 3-4. Render (C2-NT: -n 31 --flip-normals), infer (official, both directions, no TTA, CPU), tiles.
for g in "$U"/grow_*.json; do
  grep -q '"kept": true' "$g" || continue
  seg=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['segment'])" "$g")
  [ -f "$L/$seg/tiles/manifest.json" ] && continue
  S="$W/segs/$seg"; [ -d "$S" ] || { mkdir -p "$S"; cp "$L/$seg/tifxyz/"* "$S/"; }
  R="$W/render/$seg.zarr"; P="$W/infer/$seg/pred.tif"
  diskok || { status "BLOCKED: <5 GB free on /work"; push "disk low"; exit 1; }
  if [ ! -f "$R.done" ]; then rm -rf "$R"; say "render $seg"
    $LR "$R" "$W/logs/render_$seg.log" $VC vc_render_tifxyz -v "$VOL" --remote-url "$VOL" --segmentation "$S" \
      --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size 8.640 --voxel-unit micrometer \
      --flip-normals --cache-gb 2 --zarr-output "$R"
    touch "$R.done"; fi
  if [ ! -f "$P.done" ]; then mkdir -p "$W/infer/$seg"; say "infer $seg"
    $LR "$P" "$W/logs/infer_$seg.log" /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer \
      "$R" "$CK" "$P" --direction both --batch-size 4 --num-workers 1 --no-compile
    [ -f "$P" ] || P=$(ls "$W/infer/$seg"/*.tif | head -1); touch "$W/infer/$seg/pred.tif.done"; fi
  [ -f "$P" ] || P=$(ls "$W/infer/$seg"/*.tif | head -1)
  $PY "$REPO/tools/sib/fl3-pherc0800/fl_tools.py" tiles "$S" "$R" "$P" "$L/$seg/tiles" "$seg" auto
  status "tiles done for $seg"; push "tiles $seg"
  rm -rf "$W/cache/render" 2>/dev/null || true
done
n=$(cat "$L"/*/tiles/manifest.json 2>/dev/null | grep -c '"png_sha256"' || true)
printf '%s | DONE %s tiles (%s/%s inner-third auto segments kept; PASS 3)\n' "$(utc)" "$n" "$(grep -l '"kept": true' "$U"/grow_*.json 2>/dev/null | wc -l)" "$NGROW" >> "$L/STATUS.md"
push "done"; touch "$W/ALLDONE"; say ALLDONE
