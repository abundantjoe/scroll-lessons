#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# First Letters screen, PHerc0191 (DECL-FL-1 item 1). Detached, idempotent, resumable.
# Units (done markers committed under logs/sib/fl-pherc0191/state/, so a fresh container resumes):
#   env -> seeds -> per seed k: grow_k (GrowPatch, gate: 0 self-intersections, area >= 16 cm^2)
#   -> per accepted segment: render (C2-NT: vc_render_tifxyz -n 31 --flip-normals)
#   -> infer (official ink_9um step-075000, both orders, no TTA, CPU) -> tiles (push).
# Bucket listing 2026-09-30: PHerc0191 has no organizer tifxyz segments (only photos/,
# representations/predictions/{surfaces,lasagna}, volumes/), so segments are auto-grown.
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
N=fl-pherc0191
BR=claude/gifted-bell-gavnl5-sib-$N
L=$REPO/logs/sib/$N
ST=$L/state
W=/work/fl/pherc0191
mkdir -p "$ST" "$W"/{segs,render,infer,logs}
LOG=$W/logs/pipeline.log
exec >> "$LOG" 2>&1
S3VOL=s3://vesuvius-challenge-open-data/PHerc0191/volumes/20250821151635-9.362um-1.2m-113keV-masked.zarr/
S3SURF=s3://vesuvius-challenge-open-data/PHerc0191/representations/predictions/surfaces/20250821151635-surface-20260413222639-surface-m7-L0-th0.2.zarr/
S3NG=s3://vesuvius-challenge-open-data/PHerc0191/representations/predictions/surfaces/20250821151635-surface-20260413222639-surface-m7-L0-th0.2.normal-grids/
VOX=9.362
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
MAX_SEGS=4
MIN_CM2=16
export REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt SSL_CERT_FILE=/root/.ccr/ca-bundle.crt OMP_NUM_THREADS=3
say() { echo "[$(date -u +%FT%TZ)] $*"; }
done_() { [ -f "$ST/$1.done" ]; }
mark() { printf '%s\n' "${2:-ok}" > "$ST/$1.done"; }

push() {  # commit logs + tools for this sibling, push with retries
  cd "$REPO" || return 1
  git add "logs/sib/$N" "tools/sib/$N" docker/env/vc_build.sh 2>/dev/null
  git diff --cached --quiet || git commit -q -m "fl-pherc0191: $1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01RoyxAF1DLyh3AvErLKPzwr"
  for i in 1 2 3 4 5; do
    git push -q -u origin "$BR" && return 0
    git pull -q --rebase origin "$BR" || true
    sleep $((2**i))
  done
  say "push failed: $1"; return 1
}

disk_ok() { local a; a=$(df --output=avail -BG /work | tail -1 | tr -dc 0-9); [ "${a:-0}" -ge "${1:-8}" ]; }

status() { printf '%s\n' "$(date -u +%FT%TZ) fl-pherc0191: $*" > "$L/STATUS.md"; }

# ---- env (always re-verified: cheap if present; rebuilds after a container restart)
say "env"
bash "$REPO/docker/env/setup_env.sh" > "$W/logs/setup_env.log" 2>&1 || { say "setup_env FAILED"; status "BLOCKED setup_env failed (see /work/fl/pherc0191/logs/setup_env.log)"; push "env failed"; exit 2; }
[ -x /opt/hv/bin/python ] || { say "no /opt/hv"; exit 2; }
PY=/opt/hv/bin/python
VC=/work/bin/vc

# ---- seeds
if ! done_ seeds; then
  say "seeds"
  $PY "$REPO/tools/sib/$N/seeds.py" --out "$L/seeds.json" --zfrac 0.5 || { status "BLOCKED seeds.py found no seed"; push "seeds failed"; exit 3; }
  mark seeds; push "seeds"
fi

# ---- grow + gate
GP=$W/grow_params.json
cat > "$GP" <<EOF
{"step_size": 20, "generations": 200, "min_area_cm": $MIN_CM2, "voxelsize": $VOX,
 "thread_limit": 3, "cache_size": 4000000000, "use_cuda": false, "cache_root": "$W/cache",
 "normal_grid_path": "$S3NG"}
EOF
jq 'del(.normal_grid_path)' "$GP" > "$W/grow_params_nong.json" 2>/dev/null || \
  $PY -c "import json,sys;d=json.load(open('$GP'));d.pop('normal_grid_path');json.dump(d,open('$W/grow_params_nong.json','w'))"
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
accepted() { ls "$ST"/grow_*.done 2>/dev/null | xargs -r grep -l '^accepted' | wc -l; }
for k in $(seq 0 $((NS-1))); do
  [ "$(accepted)" -ge $MAX_SEGS ] && break
  done_ grow_$k && continue
  read -r X Y Z < <($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$k];print(s['x'],s['y'],s['z'])")
  SEG=pherc0191_auto_$k; SD=$W/segs/$SEG; rm -rf "$SD"; mkdir -p "$SD"
  say "grow $k seed $X $Y $Z"
  rc=1
  for P in "$GP" "$W/grow_params_nong.json"; do
    timeout 5h $VC vc_grow_seg_from_seed -v "$S3SURF" -t "$SD" -p "$P" --seed $X $Y $Z --segment-name "$SEG" \
      > "$W/logs/grow_$k.log" 2>&1; rc=$?
    say "grow $k params $(basename $P) rc=$rc"
    [ -f "$SD/meta.json" ] && break
    grep -q "discarding generated surface" "$W/logs/grow_$k.log" && break
  done
  if [ ! -f "$SD/meta.json" ]; then
    why=$(grep -m1 -o "discarding generated surface.*\|ERROR.*" "$W/logs/grow_$k.log" | head -c 200)
    mark grow_$k "rejected no_surface rc=$rc ${why}"; push "grow $k rejected"; continue
  fi
  AREA=$($PY -c "import json;print(json.load(open('$SD/meta.json')).get('area_cm2',0))")
  $VC vc_tifxyz_selfcross --surface "$SD" -o "$W/segs/${SEG}_selfcross.json" > "$W/logs/selfcross_$k.log" 2>&1
  NX=$($PY - "$W/segs/${SEG}_selfcross.json" <<'EOF'
import json,sys
def cnt(o):
    if isinstance(o,dict): return sum((len(v) if k=="transverse_contacts" and isinstance(v,list) else cnt(v)) for k,v in o.items())
    if isinstance(o,list): return sum(cnt(v) for v in o)
    return 0
try: print(cnt(json.load(open(sys.argv[1]))))
except Exception: print(-1)
EOF
)
  if grep -q "No non-adjacent transverse self-intersection found" "$W/logs/selfcross_$k.log"; then NX=0
  elif [ "$NX" = 0 ]; then NX=-1; fi   # no clean verdict line -> unknown, rejected
  mkdir -p "$L/$SEG"
  cp "$W/segs/${SEG}_selfcross.json" "$L/$SEG/selfcross.json" 2>/dev/null
  tail -c 4000 "$W/logs/grow_$k.log" > "$L/$SEG/grow_log_tail.txt"
  OK=$($PY -c "print(int(float('$AREA')>=$MIN_CM2 and '$NX'=='0'))")
  if [ "$OK" = 1 ]; then
    SZ=$(du -sm "$SD" | cut -f1)
    if [ "$SZ" -le 40 ]; then mkdir -p "$L/$SEG/tifxyz"; cp -r "$SD"/. "$L/$SEG/tifxyz/"; fi
    mark grow_$k "accepted area_cm2=$AREA selfcross=$NX seed=$X,$Y,$Z tifxyz_mb=$SZ"
  else
    mark grow_$k "rejected area_cm2=$AREA selfcross=$NX seed=$X,$Y,$Z"
  fi
  push "grow $k $(head -c 60 $ST/grow_$k.done)"
done

# ---- render / infer / tiles for accepted segments
for f in $(ls "$ST"/grow_*.done 2>/dev/null | sort -V); do
  grep -q '^accepted' "$f" || continue
  k=$(basename "$f" .done); k=${k#grow_}; SEG=pherc0191_auto_$k; SD=$W/segs/$SEG
  done_ tiles_$k && continue
  [ -f "$SD/meta.json" ] || { rm -rf "$SD"; cp -r "$L/$SEG/tifxyz" "$SD"; }   # restored after restart
  R=$W/render/$SEG.zarr; P=$W/infer/$SEG/pred.tif
  if [ ! -f "$W/render/$SEG.ok" ]; then
    disk_ok 10 || { say "disk low"; status "BLOCKED disk < 10 GB before render $SEG"; push "disk low"; exit 4; }
    rm -rf "$R"; say "render $SEG"
    $VC vc_render_tifxyz -v "$S3VOL" --remote-url "$S3VOL" --segmentation "$SD" --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output "$R" > "$W/logs/render_$k.log" 2>&1 && touch "$W/render/$SEG.ok" \
      || { say "render $SEG failed"; mark tiles_$k "failed render"; push "render $k failed"; continue; }
  fi
  if [ ! -f "$W/infer/$SEG.ok" ]; then
    mkdir -p "$W/infer/$SEG"; say "infer $SEG"
    /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$R" "$CKPT" "$P" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$W/logs/infer_$k.log" 2>&1 && touch "$W/infer/$SEG.ok" \
      || { say "infer $SEG failed"; mark tiles_$k "failed infer"; push "infer $k failed"; continue; }
  fi
  say "tiles $SEG"
  rm -rf "$L/$SEG/tiles"
  $PY "$REPO/tools/sib/$N/tiles.py" --render "$R" --segment "$SEG" --source auto --outdir "$L/$SEG/tiles" \
    --pred "forward=$P" "reverse=${P%.tif}_reverse.tif" > "$W/logs/tiles_$k.log" 2>&1 \
    || { say "tiles $SEG failed"; mark tiles_$k "failed tiles"; push "tiles $k failed"; continue; }
  mark tiles_$k "$(tail -1 $W/logs/tiles_$k.log)"
  push "tiles $SEG"
  rm -rf "$R"   # free disk; prediction maps kept in /work
done

NA=$(accepted); NT=$(cat "$L"/pherc0191_auto_*/tiles/manifest.json 2>/dev/null | grep -c '"png_sha256"')
status "DONE auto-grown segments accepted=$NA (>=${MIN_CM2} cm2, 0 selfcross); tiles=$NT (both orders) under logs/sib/$N/<segment>/tiles/; no organizer segments in bucket"
touch "$ST/ALL.done"; push "DONE"
say "ALL DONE"
