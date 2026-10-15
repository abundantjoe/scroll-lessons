#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# First Letters extra pass: PHerc0813, PASS 2 (RULES.md DECL-FL-1; tools/fl/BRIEF_PASS.md at commit dcb6a6ba).
# The bucket has no organizer segments for PHerc0813 (PHerc0813/segments/ empty, listed 2026-09-30), so ranks 4-9
# are empty and the PASS 2 auto-grow rule applies: up to 4 segments, vc_grow_seg_from_seed on the organizer
# surface-m7 L0 prediction, one per seed from seeds.json (outer third of the scroll radius; seeds.py).
# Gate: 0 transverse self-intersections (vc_tifxyz_selfcross) and area >= 16 cm^2.
# Render C2-NT (vc_render_tifxyz -n 31 --flip-normals), official ink_9um step-075000 (sha-checked), both
# directions, no TTA, CPU; 2 x 2 cm tiles, u8, INTER_AREA to 1068 px, valid >= 50 %.
# Idempotent: each unit leaves a marker under logs/sib/fl2-pherc0813/units/ and finished units are skipped.
# Commits and pushes this worker's paths after every unit. No image is ever opened for viewing.
set -euo pipefail
REPO=/home/user/dominion
BR=claude/gifted-bell-gavnl5-sib-handed
T=tools/sib/fl2-pherc0813; LREL=logs/sib/fl2-pherc0813
L=$REPO/$LREL; U=$L/units; W=/work/fl2
S3=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0813
VOL=$S3/volumes/20250821151723-9.362um-1.2m-113keV-masked.zarr
SURF=$S3/representations/predictions/surfaces/20250821151723-surface-20260413222639-surface-m7-L0-th0.2.zarr
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
PY=/opt/hv/bin/python; LR="bash $REPO/$T/ledger_run.sh"; VC=/work/bin/vc
NGROW=4; MIN_CM2=16
mkdir -p "$U" "$W"/segs "$W"/render "$W"/infer "$W"/logs "$W"/cache
export VC_CPUS=3 OMP_NUM_THREADS=3 FL_PASS=2
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { echo "[$(utc)] $*"; }
status() { printf '%s | %s\n' "$(utc)" "$1" > "$L/STATUS.md"; }
push() {  # commit + push this worker's paths only
  cd "$REPO"
  find "$L" -type f -size +95M -print | while read -r f; do say "not committed (>95 MB): $f"; echo "${f#$REPO/}" >> "$REPO/.git/info/exclude"; done
  git add -A "$LREL" "$T" 2>/dev/null || true
  git diff --cached --quiet || git commit -q -F - <<MSG
fl2-pherc0813: $1

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01AzryPCp51bY9mCGLY8nFwg
MSG
  for i in 1 2 3 4 5; do git push -q -u origin "$BR" && return 0; sleep $((2**i)); done; say "push failed"; return 0; }
diskok() { local a; a=$(df -BG --output=avail /work 2>/dev/null | tail -1 | tr -dc 0-9); [ "${a:-0}" -ge 5 ]; }

# 1. Environment (setup_env.sh: VC3D apps via vc_build.sh at villa 41701aa; CPU vesuvius; sha-checked checkpoint)
if [ -d /work/villa/.git ]; then  # an earlier sparse clone may lack the build paths
  git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection 2>/dev/null || true; fi
if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_grow_seg_from_seed ] || [ ! -x "$PY" ] \
   || [ ! -x /opt/hv-ink/bin/python ] || [ ! -x "$VC" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet 2>/dev/null \
   || ! docker info >/dev/null 2>&1; then
  say "setup_env"; status "environment build running"; bash "$REPO/docker/env/setup_env.sh" > "$W/logs/setup_env.log" 2>&1
fi
echo "$CKPT_SHA  $CK" | sha256sum -c --quiet
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
for b in vc_grow_seg_from_seed vc_tifxyz_selfcross vc_render_tifxyz; do test -x $BIN/$b; done
[ -f "$L/seeds.json" ] || $LR "$L/seeds.json" "$W/logs/seeds.log" $PY "$REPO/$T/seeds.py" "$L/seeds.json"
export FL_VOX_UM=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['voxel_um_metadata_json'])" "$L/seeds.json")
if [ ! -f "$U/env.json" ]; then
  printf '{"utc":"%s","villa":"%s","ckpt_sha256":"%s","voxel_um_metadata_json":%s,"bins":{"vc_grow_seg_from_seed":"%s","vc_tifxyz_selfcross":"%s","vc_render_tifxyz":"%s"},"segments_source":"auto (bucket PHerc0813/segments/ empty; ranks 4-9 empty)","surface":"%s","volume":"%s"}\n' \
    "$(utc)" "$(git -C /work/villa rev-parse HEAD)" "$CKPT_SHA" "$FL_VOX_UM" "$(sha256sum $BIN/vc_grow_seg_from_seed|cut -c1-64)" \
    "$(sha256sum $BIN/vc_tifxyz_selfcross|cut -c1-64)" "$(sha256sum $BIN/vc_render_tifxyz|cut -c1-64)" "$SURF" "$VOL" > "$U/env.json"
  status "env ready; growing up to $NGROW outer-third auto segments"; push "environment ready"
fi

# 2. Grow, one unit per seed. Params are fixed before any growth (same as pass 1 except the explicit seed).
[ -f "$L/grow_params.json" ] || cat > "$L/grow_params.json" <<J
{"mode":"seed","voxelsize":$FL_VOX_UM,"min_area_cm":$MIN_CM2,"step_size":20,"generations":150,"thread_limit":3,
 "cache_size":4000000000,"cache_root":"$W/cache/grow","tgt_overlap_count":20,"search_effort":10}
J
for k in $(seq 0 $((NGROW-1))); do
  [ -f "$U/grow_$k.json" ] && continue
  diskok || { status "BLOCKED: <5 GB free on /work"; push "disk low"; exit 1; }
  read -r ok sx sy sz < <($PY -c "import json,sys;s=json.load(open(sys.argv[1]))['seeds'][int(sys.argv[2])];print(s.get('ok'),s.get('x'),s.get('y'),s.get('z'))" "$L/seeds.json" $k)
  if [ "$ok" != "True" ]; then printf '{"k":%d,"segment":null,"kept":false,"reason":"seed not usable (seeds.json)"}\n' $k > "$U/grow_$k.json"; push "grow $k: no seed"; continue; fi
  TD="$W/segs/k$k"; rm -rf "$TD"; mkdir -p "$TD"; say "grow $k seed $sx $sy $sz"; status "growing segment $k"
  set +e; timeout 8h $LR "$TD" "$W/logs/grow_$k.log" $VC vc_grow_seg_from_seed -v "$SURF" -t "$TD" -p "$L/grow_params.json" -s $sx $sy $sz; rc=$?; set -e
  tail -n 300 "$W/logs/grow_$k.log" > "$L/grow_$k.log.tail" 2>/dev/null || true
  new=$(ls "$TD" 2>/dev/null | grep -v '^\.' | head -1 || true)
  if [ -z "$new" ] || [ ! -f "$TD/$new/x.tif" ]; then
    printf '{"k":%d,"rc":%d,"seed":[%s,%s,%s],"segment":null,"kept":false,"reason":"no segment written (area < %s cm2, timeout or error)"}\n' $k $rc $sx $sy $sz $MIN_CM2 > "$U/grow_$k.json"
    push "grow $k: no segment"; continue; fi
  S="$TD/$new"; seg="p2k${k}_$new"
  $PY "$REPO/$T/fl_tools.py" geom "$S" "$L/$seg.geom.json" > /dev/null
  set +e; $LR "$L/$seg.selfcross.json" "$W/logs/selfcross_$k.log" $VC vc_tifxyz_selfcross "$S" -o "$L/$seg.selfcross.json" --fail-on-crossing; src=$?; set -e
  gate=$($PY - "$L/$seg.selfcross.json" "$L/$seg.geom.json" $src $MIN_CM2 <<'P'
import json,sys
try: sc=json.load(open(sys.argv[1]))
except Exception: sc={}
g=json.load(open(sys.argv[2])); src=int(sys.argv[3]); m=float(sys.argv[4])
clean=bool(sc.get('clean_of_transverse_self_intersection')) and src==0
print(json.dumps(dict(clean_of_transverse=clean, selfcross_rc=src, area_cm2=g['area_cm2'], kept=clean and g['area_cm2']>=m)))
P
)
  printf '{"k":%d,"rc":%d,"seed":[%s,%s,%s],"segment":"%s","gate":%s}\n' $k $rc $sx $sy $sz "$seg" "$gate" > "$U/grow_$k.json"
  if echo "$gate" | grep -q '"kept": true'; then
    mkdir -p "$L/$seg/tifxyz"; cp "$S"/*.tif "$S"/meta.json "$L/$seg/tifxyz/" 2>/dev/null || true
    rm -rf "$W/segs/$seg"; cp -r "$S" "$W/segs/$seg"; fi
  status "grow $k -> $seg $gate"; push "grow $k: $seg"
done

# 3-4. Render (C2-NT), infer (official, both directions, no TTA, CPU), tiles.
for g in "$U"/grow_*.json; do
  grep -q '"kept": true' "$g" || continue
  seg=$($PY -c "import json,sys;print(json.load(open(sys.argv[1]))['segment'])" "$g")
  [ -f "$L/$seg/tiles/manifest.json" ] && continue
  S="$W/segs/$seg"; [ -f "$S/x.tif" ] || { rm -rf "$S"; mkdir -p "$S"; cp "$L/$seg/tifxyz/"* "$S/"; }
  R="$W/render/$seg.zarr"; P="$W/infer/$seg/pred.tif"
  diskok || { status "BLOCKED: <5 GB free on /work"; push "disk low"; exit 1; }
  if [ ! -f "$R.done" ]; then rm -rf "$R"; say "render $seg"; status "rendering $seg"
    $LR "$R" "$W/logs/render_$seg.log" $VC vc_render_tifxyz -v "$VOL" --remote-url "$VOL" --segmentation "$S" \
      --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size "$FL_VOX_UM" --voxel-unit micrometer \
      --flip-normals --cache-gb 2 --zarr-output "$R"
    touch "$R.done"; fi
  if [ ! -f "$W/infer/$seg/infer.done" ]; then rm -rf "$W/infer/$seg"; mkdir -p "$W/infer/$seg"; say "infer $seg"; status "inferring $seg"
    $LR "$P" "$W/logs/infer_$seg.log" /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer \
      "$R" "$CK" "$P" --direction both --batch-size 4 --num-workers 1 --no-compile
    touch "$W/infer/$seg/infer.done"; fi
  [ -f "$P" ] || P=$(ls "$W/infer/$seg"/*.tif | head -1)
  $PY "$REPO/$T/fl_tools.py" tiles "$S" "$R" "$P" "$L/$seg/tiles" "$seg" auto
  status "tiles done for $seg"; push "tiles $seg"
  rm -rf "$W/cache/render" 2>/dev/null || true
done
n=$(cat "$L"/*/tiles/manifest.json 2>/dev/null | grep -c '"png_sha256"' || true)
kept=$(grep -l '"kept": true' "$U"/grow_*.json 2>/dev/null | wc -l)
status "PASS 2 finished: $kept/$NGROW outer-third auto segments kept, $n tiles (valid >= 50 %)"
echo "DONE $n" >> "$L/STATUS.md"
push "done ($n tiles)"; touch "$W/ALLDONE"; say ALLDONE
