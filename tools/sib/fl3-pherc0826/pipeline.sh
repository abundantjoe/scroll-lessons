#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters extra pass, SCROLL PHerc0826, PASS 3 (tools/fl/BRIEF_PASS.md @ dcb6a6b).
# The bucket has NO organizer segments for PHerc0826 (PHerc0826/ holds photos/, representations/, volumes/ only;
# listed 2026-09-30), so organizer ranks 10-15 are empty and the PASS 3 auto-grow rule applies: up to 4
# vc_grow_seg_from_seed runs on the organizer surface-m7 L0 prediction, each from an explicit seed in the INNER third
# of the scroll radius (fl3_tools.py seeds; rule in seeds.json), kept iff vc_tifxyz_selfcross finds 0 transverse
# self-intersections and area >= 16 cm^2. Then C2-NT render (-n 31 --flip-normals), official ink_9um step-075000
# (sha-checked), both directions, no TTA, CPU; 2 cm tiles, u8, INTER_AREA 1068 px, valid >= 50 %.
# Structure adapted from tools/sib/fl-pherc0813/pipeline.sh (sib-fl-pherc0813 @ 325973f).
# Idempotent: every unit leaves a pushed marker under logs/sib/fl3-pherc0826/units/, and finished units are skipped.
# Launch: nohup bash tools/sib/fl3-pherc0826/run.sh >> /work/fl3/run.log 2>&1 &
set -euo pipefail
REPO=/home/user/dominion
BR=claude/gifted-bell-gavnl5-sib-p4-pig-cu
L=$REPO/logs/sib/fl3-pherc0826; U=$L/units; W=/work/fl3
S3=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0826
VOL=$S3/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr
SURF=$S3/representations/predictions/surfaces/20250821151701-surface-20260413222639-surface-m7-L0-th0.2.zarr
UMB=$S3/representations/umbilicus/20250821151701-umbilicus-20260808113303.json
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
PY=/opt/hv/bin/python; LR="bash $REPO/tools/c3/ledger_run.sh"; VC=/work/bin/vc
T3="$REPO/tools/sib/fl3-pherc0826/fl3_tools.py"
NGROW=4; MIN_CM2=16
mkdir -p "$U" "$W"/segs "$W"/render "$W"/infer "$W"/logs "$W"/cache
export VC_CPUS=3 OMP_NUM_THREADS=3
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { echo "[$(utc)] $*"; }
status() { printf '%s | fl3-pherc0826 | %s\n' "$(utc)" "$1" >> "$L/STATUS.md"; }
push() {  # commit+push this worker's files only
  cd "$REPO"; git add -A logs/sib/fl3-pherc0826 tools/sib/fl3-pherc0826 logs/gpu_ledger.tsv 2>/dev/null || true
  git diff --cached --quiet || git commit -q -m "fl3-pherc0826: $1

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BGvjN5PqxUioDsG1cJPaYj"
  for i in 1 2 3 4 5; do git pull -q --no-rebase --no-edit origin "$BR" 2>/dev/null || true
    git push -q -u origin "$BR" && return 0; sleep $((2**i)); done; say "push failed"; return 0; }
diskok() { local a; a=$(df -BG --output=avail /work 2>/dev/null | tail -1 | tr -dc 0-9); [ "${a:-0}" -ge 5 ]; }

# 1. Environment (setup_env builds VC3D via vc_build.sh at villa 41701aa, CPU vesuvius, sha-checked checkpoint)
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_grow_seg_from_seed ] || [ ! -x "$PY" ] \
   || [ ! -x /opt/hv-ink/bin/python ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet 2>/dev/null; then
  say "setup_env"; bash "$REPO/docker/env/setup_env.sh" > "$W/logs/setup_env.log" 2>&1
fi
docker info >/dev/null 2>&1 || bash "$REPO/docker/env/setup_env.sh" >> "$W/logs/setup_env.log" 2>&1
echo "$CKPT_SHA  $CK" | sha256sum -c --quiet
VIRTUAL_ENV=/opt/hv uv pip install -q aiohttp fsspec >/dev/null 2>&1 || true
for b in vc_grow_seg_from_seed vc_tifxyz_selfcross vc_render_tifxyz; do
  test -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/$b; done
if [ ! -f "$U/env.json" ]; then
  B=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
  printf '{"utc":"%s","villa":"%s","ckpt_sha256":"%s","bins":{"vc_grow_seg_from_seed":"%s","vc_tifxyz_selfcross":"%s","vc_render_tifxyz":"%s"},"segments_source":"auto (bucket PHerc0826 has no segments/ prefix; organizer ranks 10-15 empty)","pass":3,"surface":"%s","volume":"%s","umbilicus":"%s"}\n' \
    "$(utc)" "$(git -C /work/villa rev-parse HEAD)" "$CKPT_SHA" "$(sha256sum $B/vc_grow_seg_from_seed|cut -c1-64)" \
    "$(sha256sum $B/vc_tifxyz_selfcross|cut -c1-64)" "$(sha256sum $B/vc_render_tifxyz|cut -c1-64)" "$SURF" "$VOL" "$UMB" > "$U/env.json"
  status "env ready; computing inner-third seeds"; push "environment ready"
fi

# 2a. Inner-third seeds (deterministic; pushed before any growth)
if [ ! -s "$L/seeds.json" ]; then
  $PY "$T3" seeds "$SURF" "$UMB" "$L/seeds.json" $NGROW > "$W/logs/seeds.log" 2>&1
  status "seeds: $($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))") inner-third seeds"; push "inner-third seeds"
fi
# 2b. Grow (one unit per seed). Params are fixed before any growth and pushed with the seeds.
[ -s "$L/grow_params.json" ] || { cat > "$L/grow_params.json" <<J
{"mode":"seed","voxelsize":9.362,"min_area_cm":$MIN_CM2,"step_size":20,"generations":150,"thread_limit":3,
 "cache_size":4000000000,"cache_root":"$W/cache/grow","tgt_overlap_count":20,"search_effort":10}
J
push "grow params"; }
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
for k in $(seq 0 $((NS-1))); do
  [ -f "$U/grow_$k.json" ] && continue
  diskok || { status "BLOCKED: <5 GB free on /work"; push "disk low"; exit 1; }
  read -r SX SY SZ < <($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$k];print(s['x'],s['y'],s['z'])")
  say "grow $k seed $SX $SY $SZ"; before=$(ls "$W/segs" | sort)
  set +e; timeout 8h $LR "$W/segs" "$W/logs/grow_$k.log" $VC vc_grow_seg_from_seed -v "$SURF" -t "$W/segs" -p "$L/grow_params.json" --seed "$SX" "$SY" "$SZ"; rc=$?; set -e
  new=$(comm -13 <(echo "$before") <(ls "$W/segs" | sort) | grep '^auto_grown_' | head -1 || true)
  if [ -z "$new" ]; then
    printf '{"k":%d,"rc":%d,"seed_xyz":[%s,%s,%s],"segment":null,"kept":false,"reason":"no segment written (area < %s cm2 or overlap)"}\n' $k $rc $SX $SY $SZ $MIN_CM2 > "$U/grow_$k.json"
    status "grow $k: no segment"; push "grow $k: no segment"; continue; fi
  S="$W/segs/$new"
  $PY "$T3" geom "$S" "$L/$new.geom.json" > /dev/null
  set +e; $LR "$L/$new.selfcross.json" "$W/logs/selfcross_$k.log" $VC vc_tifxyz_selfcross "$S" -o "$L/$new.selfcross.json" --fail-on-crossing; src=$?; set -e
  kept=$($PY - "$L/$new.selfcross.json" "$L/$new.geom.json" $src $MIN_CM2 <<'P'
import json,sys
sc=json.load(open(sys.argv[1])); g=json.load(open(sys.argv[2])); src=int(sys.argv[3]); m=float(sys.argv[4])
clean=bool(sc.get('clean_of_transverse_self_intersection')) and src==0
print(json.dumps(dict(clean_of_transverse=clean, selfcross_rc=src, area_cm2=g['area_cm2'], kept=clean and g['area_cm2']>=m)))
P
)
  printf '{"k":%d,"rc":%d,"seed_xyz":[%s,%s,%s],"segment":"%s","gate":%s}\n' $k $rc $SX $SY $SZ "$new" "$kept" > "$U/grow_$k.json"
  if echo "$kept" | grep -q '"kept": true'; then
    mkdir -p "$L/$new/tifxyz"; cp "$S"/*.tif "$S"/meta.json "$L/$new/tifxyz/" 2>/dev/null || true; fi
  status "grow $k -> $new $kept"; push "grow $k: $new"
done

# 3-4. Render (C2-NT: -n 31 --flip-normals), infer (official, both directions, no TTA, CPU), tiles.
for g in "$U"/grow_*.json; do
  [ -f "$g" ] || continue
  grep -q '"kept": true' "$g" || continue
  seg=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['segment'])" "$g")
  [ -f "$L/$seg/tiles/manifest.json" ] && continue
  S="$W/segs/$seg"; [ -d "$S" ] || { mkdir -p "$S"; cp "$L/$seg/tifxyz/"* "$S/"; }
  R="$W/render/$seg.zarr"; P="$W/infer/$seg/pred.tif"
  diskok || { status "BLOCKED: <5 GB free on /work"; push "disk low"; exit 1; }
  if [ ! -f "$R.done" ]; then rm -rf "$R"; say "render $seg"; status "render $seg"
    $LR "$R" "$W/logs/render_$seg.log" $VC vc_render_tifxyz -v "$VOL" --remote-url "$VOL" --segmentation "$S" \
      --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer \
      --flip-normals --cache-gb 2 --zarr-output "$R"
    touch "$R.done"; fi
  if [ ! -f "$P.done" ]; then mkdir -p "$W/infer/$seg"; say "infer $seg"; status "infer $seg"
    $LR "$P" "$W/logs/infer_$seg.log" /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer \
      "$R" "$CK" "$P" --direction both --batch-size 4 --num-workers 1 --no-compile
    touch "$P.done"; fi
  $PY "$T3" tiles "$S" "$R" "$W/infer/$seg" "$L/$seg/tiles" "$seg" auto
  status "tiles done for $seg"; push "tiles $seg"
  rm -rf "$W/cache/render" 2>/dev/null || true
done
n=$(cat "$L"/*/tiles/manifest.json 2>/dev/null | grep -c '"png_sha256"' || true)  # both directions counted
status "DONE $n tiles ($(grep -l '"kept": true' "$U"/grow_*.json 2>/dev/null | wc -l)/$NS inner-third auto segments kept; valid>=50 %)"
push "done"; touch "$W/ALLDONE"; say ALLDONE
