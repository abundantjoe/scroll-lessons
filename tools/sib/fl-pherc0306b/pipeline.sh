#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# First Letters screen (RULES.md DECL-FL-1), worker fl-pherc0306b, detached (OWNER-STANDING-ORDER-5).
# Idempotent: every unit leaves a committed record under logs/sib/fl-pherc0306b/ and is skipped when present,
# so a rerun (watchdog restart or a fresh container) continues where the pushed branch stopped.
# Numbers, hashes and file lists only; no image, tile or CT pixel is viewed.
# Units: env -> listing -> (organizer pick | declared seeds -> grow s0..s7 until 4 accepted)
#        -> per segment: render (C2-NT, -n 31 --flip-normals) -> infer (both, no TTA, CPU) -> tiles + manifest.
set -euo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cd "$REPO"
TASK=fl-pherc0306b
T=tools/sib/$TASK
OUT=logs/sib/$TASK
W=${FL_WORK:-/work/fl0306b}
BRANCH=claude/gifted-bell-gavnl5-sib-$TASK
PY=/opt/hv/bin/python
PYI=/opt/hv-ink/bin/python
VC=/work/bin/vc
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
BUCKET_HTTP=https://vesuvius-challenge-open-data.s3.amazonaws.com
VOL_URL=s3://vesuvius-challenge-open-data/PHerc0306B/volumes/20250521133212-8.640um-1.2m-116keV-masked.zarr/
PRED_URL=s3://vesuvius-challenge-open-data/PHerc0306B/representations/predictions/surfaces/20250521133212-surface-20260413222639-surface-m7-L0-th0.2.zarr/
NGRID_URL=$BUCKET_HTTP/PHerc0306B/representations/predictions/surfaces/20250521133212-surface-20260413222639-surface-m7-L0-th0.2.normal-grids
MAX_ACCEPT=4
export OMP_NUM_THREADS=3 VC_CPUS=3
mkdir -p "$W" "$OUT" /work/logs
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$W/pipeline.log"; }

status() {  # one STATUS.md line per unit (appended; the file is shared with the S1 helper record)
  echo "$(date -u +%FT%TZ) $TASK PHerc0306B: $*" >> "$OUT/STATUS.md"
}

push() {  # commit given paths and push to the worker branch (retries with backoff)
  local msg=$1; shift
  git add -- "$@" "$OUT/STATUS.md" 2>/dev/null || git add -- "$@"
  if git diff --cached --quiet; then return 0; fi
  git commit -q -m "$msg

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_015H61w4qRrx3aANRD5hPdTN"
  local d=2
  for _ in 1 2 3 4 5 6; do
    if git push -q -u origin "HEAD:$BRANCH"; then return 0; fi
    git pull -q --no-rebase --no-edit origin "$BRANCH" || true
    sleep $d; d=$((d * 2))
  done
  log "push failed (will retry on next unit)"; return 0
}

# ---------------------------------------------------------------- 1. environment (idempotent, ~15 min fresh)
env_ok() {
  [ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] &&
  [ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_grow_seg_from_seed ] &&
  [ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_tifxyz_selfcross ] &&
  [ -x $PY ] && [ -x $PYI ] && [ -x $VC ] && docker info >/dev/null 2>&1 &&
  $PYI -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null &&
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet 2>/dev/null
}
ink_fix() {
  [ -x $PYI ] || return 0
  $PYI -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null && return 0
  $PYI -c "import torch" 2>/dev/null || VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
  $PYI -m pip --version >/dev/null 2>&1 || VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python $PYI pip
  $PYI -m pip install -q --ignore-requires-python --no-deps -e /work/villa/vesuvius
  $PYI -m pip install -q --ignore-requires-python --no-deps -r docker/env/hv-ink-freeze.txt || true
}
if ! env_ok; then
  log "env: setup"
  bash docker/env/setup_env.sh >> /work/logs/setup_env.log 2>&1 || log "setup_env pass 1 rc=$? (expected when the build needs the live proxy port)"
  if [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_tifxyz_selfcross ]; then
    # docker/env/vc_build.sh pins proxy port 46883; the port changes per container, so use the live one.
    mkdir -p /work/scripts
    sed "s#http://127.0.0.1:46883#${HTTPS_PROXY:-http://127.0.0.1:46883}#g" docker/env/vc_build.sh > /work/scripts/vc_build_px.sh
    bash /work/scripts/vc_build_px.sh > /work/logs/vc_build.log 2>&1
  fi
  # setup_env installs vesuvius without --ignore-requires-python (pyproject pins 3.14; TOOLING.md used the flag),
  # which aborts it before the checkpoint step: repair the ink venv, then let setup_env finish (idempotent).
  bash docker/env/setup_env.sh >> /work/logs/setup_env.log 2>&1 || true
  ink_fix
  bash docker/env/setup_env.sh >> /work/logs/setup_env.log 2>&1 || true
  env_ok || { log "env: FAILED"; exit 2; }
fi
[ "$(git config core.hooksPath || true)" = tools/hooks ] || bash tools/hooks/install.sh >/dev/null
$PY -c "import numcodecs, imagecodecs, boto3, cv2, tifffile, zarr, PIL" 2>/dev/null || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs imagecodecs
log "env: OK"

# ---------------------------------------------------------------- 2. segment source
if [ ! -f "$OUT/s3_listing.json" ]; then
  log "listing"
  $PY $T/fl_lib.py listing "$OUT/s3_listing.json"
  status "listing done, source=$($PY -c "import json;print(json.load(open('$OUT/s3_listing.json'))['source'])")"
  push "fl-pherc0306b: anonymous S3 listing of PHerc0306B/" "$OUT/s3_listing.json"
fi
SOURCE=$($PY -c "import json;print(json.load(open('$OUT/s3_listing.json'))['source'])")
log "source=$SOURCE"

SEGS=()
if [ "$SOURCE" = organizer ]; then
  [ -f "$OUT/organizer_pick.json" ] || { $PY $T/fl_lib.py organizer "$OUT/s3_listing.json" "$OUT/organizer_pick.json";
    push "fl-pherc0306b: organizer segment pick (3 largest)" "$OUT/organizer_pick.json"; }
  while read -r d; do
    s=$(basename "$(dirname "$(dirname "$d")")" 2>/dev/null); [ -n "$s" ] && [ "$s" != segments ] || s=$(basename "$d")
    mkdir -p "$W/seg/$s"
    for f in meta.json x.tif y.tif z.tif mask.tif; do
      [ -s "$W/seg/$s/$f" ] || curl -fsS -o "$W/seg/$s/$f" "$BUCKET_HTTP/$d/$f" || rm -f "$W/seg/$s/$f"
    done
    SEGS+=("$s:$W/seg/$s")
  done < <($PY -c "import json;[print(c['dir']) for c in json.load(open('$OUT/organizer_pick.json'))['chosen']]")
else
  # ---- 2b. declared seeds, committed before any growth
  if [ ! -f "$OUT/seeds.json" ]; then
    log "seeds"
    $PY $T/fl_lib.py seeds "$OUT/seeds.json"
    status "seeds declared ($(grep -c '"status": "ok"' "$OUT/seeds.json") ok), growth next"
    push "fl-pherc0306b: declared GrowPatch seeds (mid radius, surface-m7) before any growth" "$OUT/seeds.json"
  fi
  mkdir -p "$W/ngrid" "$W/grow_cache"
  echo "{\"url\": \"$NGRID_URL\"}" > "$W/ngrid/normal-grids-remote.json"
  cat > "$W/grow_params.json" <<EOF
{"step_size": 20, "generations": 200, "min_area_cm": 16, "thread_limit": 3, "voxelsize": 8.64,
 "cache_size": 4000000000, "use_cuda": false, "normal_grid_path": "$W/ngrid", "cache_root": "$W/grow_cache"}
EOF
  [ -f "$OUT/grow_params.json" ] || cp "$W/grow_params.json" "$OUT/grow_params.json"
  NS=$($PY -c "import json;print(len(json.load(open('$OUT/seeds.json'))['seeds']))")
  for k in $(seq 0 $((NS - 1))); do
    s=auto_s$k; R="$OUT/$s/grow.json"
    nacc=$( (grep -l '"accepted": true' $OUT/auto_s*/grow.json 2>/dev/null || true) | wc -l)
    [ "$nacc" -ge $MAX_ACCEPT ] && break
    [ -f "$R" ] && continue
    xyz=$($PY -c "import json;s=json.load(open('$OUT/seeds.json'))['seeds'][$k];print(' '.join(map(str,s['seed0_xyz'])) if s['status']=='ok' else '')")
    mkdir -p "$OUT/$s"
    if [ -z "$xyz" ]; then
      echo '{"accepted": false, "reason": "seed status not ok"}' > "$R"
      push "fl-pherc0306b: $s skipped (no seed)" "$R"; continue
    fi
    log "grow $s seed xyz=$xyz"; status "growing $s ($nacc accepted so far)"
    rm -rf "$W/grow/$s"; mkdir -p "$W/grow/$s"
    set +e
    timeout 8h $VC vc_grow_seg_from_seed -v "$PRED_URL" -t "$W/grow/$s" -p "$W/grow_params.json" \
      -s $xyz --segment-name "pherc0306b_$s" > "$W/grow_$s.log" 2>&1
    rc=$?; set -e
    tail -40 "$W/grow_$s.log" > "$OUT/$s/grow_tail.log"
    if [ $rc -ne 0 ] || [ ! -f "$W/grow/$s/meta.json" ]; then
      printf '{"accepted": false, "reason": "no surface written (rc=%s; tool discards < min_area_cm 16)", "seed_xyz": "%s"}\n' "$rc" "$xyz" > "$R"
      push "fl-pherc0306b: $s grown, not kept (rc=$rc)" "$R" "$OUT/$s/grow_tail.log"; continue
    fi
    $VC vc_tifxyz_selfcross --surface "$W/grow/$s" -o "$W/grow/${s}_selfcross.json" > "$W/selfcross_$s.log" 2>&1 || true
    cp "$W/grow/${s}_selfcross.json" "$OUT/$s/selfcross.json" 2>/dev/null || echo '{"census": [{"transverse": 999999}]}' > "$OUT/$s/selfcross.json"
    $PY $T/fl_lib.py accept "$W/grow/$s" "$OUT/$s/selfcross.json" "$R" | tee -a "$W/pipeline.log"
    if grep -q '"accepted": true' "$R"; then
      mkdir -p "$OUT/$s/tifxyz"; cp "$W/grow/$s"/*.tif "$W/grow/$s"/meta.json "$OUT/$s/tifxyz/"
      push "fl-pherc0306b: $s accepted (0 self-intersections, >= 16 cm2)" "$R" "$OUT/$s"
    else
      push "fl-pherc0306b: $s rejected" "$R" "$OUT/$s"
    fi
  done
  for k in $(seq 0 $((NS - 1))); do
    s=auto_s$k
    grep -q '"accepted": true' "$OUT/$s/grow.json" 2>/dev/null && SEGS+=("$s:$OUT/$s/tifxyz")
  done
fi
log "segments: ${SEGS[*]:-none}"
[ ${#SEGS[@]} -gt 0 ] || { status "no segment passed (see grow.json records); screen ends with 0 tiles"; touch "$OUT/DONE"; push "fl-pherc0306b: no usable segment" "$OUT"; exit 0; }

# ---------------------------------------------------------------- 3-4. render, infer, tiles per segment
for e in "${SEGS[@]}"; do
  s=${e%%:*}; SEG=${e#*:}
  [ -f "$OUT/$s/manifest.json" ] && continue
  mkdir -p "$W/render" "$W/infer/$s" "$OUT/$s"
  Z="$W/render/$s.zarr"
  if [ ! -f "$W/render/$s.ok" ]; then
    log "render $s"; status "rendering $s"
    rm -rf "$Z"
    CMD=(vc_render_tifxyz -v "$VOL_URL" --remote-url "$VOL_URL" --segmentation "$(readlink -f "$SEG")" --scale 1 --group-idx 0
         --num-slices 31 --slice-step 1 --voxel-size 8.64 --voxel-unit micrometer --flip-normals --cache-gb 4 --zarr-output "$Z")
    timeout 6h $VC "${CMD[@]}" > "$W/render_$s.log" 2>&1
    printf '%s\n' "${CMD[@]}" > "$W/render/$s.cmd"; touch "$W/render/$s.ok"
  fi
  P="$W/infer/$s/pred.tif"
  if [ ! -f "$W/infer/$s.ok" ]; then
    log "infer $s"; status "inferring $s (ink_9um step-075000, both, no TTA)"
    timeout 12h $PYI -m vesuvius.ink_detection.inference.infer "$Z" "$CKPT" "$P" \
      --direction both --batch-size 4 --num-workers 1 --no-compile > "$W/infer_$s.log" 2>&1
    touch "$W/infer/$s.ok"
  fi
  log "tiles $s"
  $PY $T/fl_lib.py tiles "$s" "$Z" "$P" "$W/infer/$s/pred_reverse.tif" "$OUT/$s" "$SOURCE" | tee -a "$W/pipeline.log"
  BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
  $PY - "$OUT/$s/run.json" "$s" "$W/render/$s.cmd" <<EOF
import json, sys, hashlib, subprocess
out, s, cmdf = sys.argv[1:4]
h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
json.dump({'segment': s, 'render_cmd': open(cmdf).read().split('\n')[:-1],
  'infer_cmd': ['$PYI', '-m', 'vesuvius.ink_detection.inference.infer', '$Z', '$CKPT', '$P', '--direction', 'both',
                '--batch-size', '4', '--num-workers', '1', '--no-compile'],
  'direction_names': {'fwd': 'pred.tif (forward = render slices ascending)', 'rev': 'pred_reverse.tif'},
  'villa_sha': subprocess.check_output(['git', '-C', '/work/villa', 'rev-parse', 'HEAD'], text=True).strip(),
  'vc_render_tifxyz_sha256': h('$BIN/vc_render_tifxyz'), 'vc_grow_seg_from_seed_sha256': h('$BIN/vc_grow_seg_from_seed'),
  'ckpt_sha256': '$CKPT_SHA', 'fl_lib_sha256': h('$T/fl_lib.py'), 'pipeline_sha256': h('$T/pipeline.sh')},
  open(out, 'w'), indent=1)
EOF
  tail -30 "$W/render_$s.log" > "$OUT/$s/render_tail.log"
  tail -30 "$W/infer_$s.log" > "$OUT/$s/infer_tail.log"
  status "$s tiles pushed ($($PY -c "import json;print(json.load(open('$OUT/$s/manifest.json'))['n_tiles'])") PNGs)"
  push "fl-pherc0306b: $s tiles + manifest (DECL-FL-1)" "$OUT/$s"
  rm -rf "$Z"   # free disk; the tiles and hashes are pushed
done

n=$(cat $OUT/*/manifest.json | grep -c '"png_sha256"' || true)
status "DONE: ${#SEGS[@]} segment(s), $n tile PNGs (fwd+rev) under $OUT/<segment>/tiles; census next (DECL-FL-1 items 2-5)"
touch "$OUT/DONE"
push "fl-pherc0306b: pipeline done" "$OUT"
log "ALL DONE"
