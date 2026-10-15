#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters screen, PHerc1203 (worker fl-pherc1203). Idempotent: every unit has a
# done marker (repo markers survive container loss; /work markers do not). Commits and pushes
# after each unit. Run: nohup bash tools/sib/fl-pherc1203/pipeline.sh > /work/fl/pherc1203.log 2>&1 &
# Without --once it is its own restart loop (max 12 attempts, 120 s apart).
set -uo pipefail
NAME=fl-pherc1203
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-$NAME
L=$REPO/logs/sib/$NAME
T=$REPO/tools/sib/$NAME
W=/work/fl/pherc1203
VOL=s3://vesuvius-challenge-open-data/PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/
VOX=9.362   # eligible_products.json samplePixelSize_mm 0.009362
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
NSEG=3
mkdir -p "$W" "$L"

if [ "${1:-}" != "--once" ]; then
  for a in $(seq 1 12); do
    bash "$0" --once; rc=$?; [ $rc -eq 0 ] && exit 0
    echo "[$(date -u +%FT%TZ)] attempt $a failed rc=$rc; retry in 120 s" | tee -a "$L/progress.log"
    sleep 120
  done
  echo "$(date -u +%FT%TZ) FAILED after 12 attempts; see progress.log" > "$L/STATUS.md"
  git -C "$REPO" add "$L" && git -C "$REPO" commit -qm "fl-pherc1203: FAILED after 12 attempts" && git -C "$REPO" push -q -u origin "$BR"
  exit 1
fi
set -e

log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$L/progress.log"; }
status() { echo "$(date -u +%FT%TZ) $*" > "$L/STATUS.md"; }
push() {  # push <msg>
  git -C "$REPO" add "$L" "$T" 2>/dev/null || true
  git -C "$REPO" diff --cached --quiet || git -C "$REPO" commit -qm "fl-pherc1203: $1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JKfHMQWukE7h5d5W3CgnvY"
  for i in 1 2 3 4 5; do git -C "$REPO" push -q -u origin "$BR" && return 0; sleep $((2 ** i)); done
  log "push failed (will retry next unit)"; return 0
}
disk() { local a; a=$(df -BG --output=avail /work | tail -1 | tr -dc 0-9); [ "$a" -ge 5 ] || { log "disk < 5 GB free ($a)"; exit 4; }; }

# ---- unit 0: environment (per container) ----
if [ ! -f "$W/env.done" ]; then
  log "env: setup_env.sh"
  bash "$REPO/docker/env/setup_env.sh" >> "$W/setup_env.log" 2>&1
  [ "$(git -C /work/villa rev-parse HEAD)" = "$VILLA_SHA" ]
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet
  /work/bin/vc vc_render_tifxyz --help > /dev/null
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null
  date -u +%FT%TZ > "$W/env.done"; log "env: OK (villa $VILLA_SHA, ckpt sha ok, CPU)"
  status "env OK; next: segment selection"; push "env ready"
fi

# ---- unit 1: segment selection ----
if [ ! -f "$L/segments.json" ]; then
  log "select: organizer tifxyz segments"
  /opt/hv/bin/python "$T/select_segments.py" "$L/segments.json.tmp" "$W/seg" "$NSEG" | tee -a "$L/progress.log"
  mv "$L/segments.json.tmp" "$L/segments.json"
  status "segments selected; next: render"; push "segment selection"
fi
SEGS=$(/opt/hv/bin/python -c "import json;print(' '.join(r['segment'] for r in json.load(open('$L/segments.json'))['picked']))")

for S in $SEGS; do
  [ -f "$L/$S/tiles/manifest.json" ] && continue
  mkdir -p "$L/$S" "$W/render" "$W/infer/$S"
  # tifxyz files (re-fetch after container loss; sha256 checked against segments.json)
  if [ ! -f "$W/seg/$S/z.tif" ]; then
    /opt/hv/bin/python "$T/select_segments.py" "$W/reselect.json" "$W/seg" "$NSEG" > /dev/null
  fi
  /opt/hv/bin/python - "$L/segments.json" "$W/seg/$S" "$S" <<'E'
import hashlib, json, sys
from pathlib import Path
r = next(p for p in json.load(open(sys.argv[1]))["picked"] if p["segment"] == sys.argv[3])
for f, h in r["files_sha256"].items():
    assert hashlib.sha256((Path(sys.argv[2]) / f).read_bytes()).hexdigest() == h, f
E
  # self-intersection count (record only; organizer segments are not filtered on it)
  [ -f "$L/$S/selfcross.json" ] || /work/bin/vc vc_tifxyz_selfcross --surface "$W/seg/$S" -o "$L/$S/selfcross.json" > "$W/selfcross_$S.log" 2>&1 || true

  # ---- unit: render (C2-NT: -n 31 --flip-normals) ----
  if [ ! -f "$W/render/$S.done" ]; then
    disk; rm -rf "$W/render/$S.zarr"; log "render $S start"; t0=$(date +%s)
    ( cd "$W" && /work/bin/vc vc_render_tifxyz -v "$VOL" --remote-url "$VOL" --segmentation "$W/seg/$S" \
        --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size "$VOX" --voxel-unit micrometer \
        --flip-normals --cache-gb 4 --zarr-output "$W/render/$S.zarr" ) > "$W/render/$S.log" 2>&1
    touch "$W/render/$S.done"; log "render $S done $(( $(date +%s) - t0 )) s"
    status "render $S done; next: infer $S"; push "render $S"
  fi

  # ---- unit: official infer, both directions, no TTA, CPU ----
  if [ ! -f "$W/infer/$S/done" ]; then
    disk; log "infer $S start"; t0=$(date +%s)
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer \
      "$W/render/$S.zarr" "$CKPT" "$W/infer/$S/ink.tif" --direction both --batch-size 4 --num-workers 1 --no-compile \
      > "$W/infer/$S/infer.log" 2>&1
    [ -f "$W/infer/$S/ink.tif" ] && [ -f "$W/infer/$S/ink_reverse.tif" ]
    touch "$W/infer/$S/done"; log "infer $S done $(( $(date +%s) - t0 )) s"
    status "infer $S done; next: tiles $S"; push "infer $S"
  fi

  # ---- unit: tiles ----
  cat > "$W/extra_$S.json" <<J
{"source": "organizer", "scroll": "PHerc1203", "volume": "$VOL",
 "render": "vc_render_tifxyz -n 31 --flip-normals --scale 1 --slice-step 1 --voxel-size $VOX (villa $VILLA_SHA)",
 "ink_model": "HF scrollprize/ink_9um hybrid_3d2d-seed42 step-075000 sha256 $CKPT_SHA",
 "infer": "vesuvius.ink_detection.inference.infer --direction both --batch-size 4 --num-workers 1 --no-compile (no TTA, CPU)",
 "forward_file": "ink.tif", "reverse_file": "ink_reverse.tif",
 "ink_tif_sha256": {"forward": "$(sha256sum "$W/infer/$S/ink.tif" | cut -c1-64)", "reverse": "$(sha256sum "$W/infer/$S/ink_reverse.tif" | cut -c1-64)"}}
J
  rm -rf "$L/$S/tiles.tmp"
  /opt/hv/bin/python "$T/make_tiles.py" "$W/render/$S.zarr" "$W/infer/$S/ink.tif" "$W/infer/$S/ink_reverse.tif" \
    "$S" "$L/$S/tiles.tmp" "$VOX" "$W/extra_$S.json" | tee -a "$L/progress.log"
  rm -rf "$L/$S/tiles"; mv "$L/$S/tiles.tmp" "$L/$S/tiles"
  log "tiles $S pushed"; status "tiles $S done"; push "tiles $S"
done

N=$(ls "$L"/*/tiles/manifest.json 2>/dev/null | wc -l)
status "DONE: $N/$(echo $SEGS | wc -w) segments tiled ($SEGS); tiles under logs/sib/$NAME/<segment>/tiles/"
log "ALL DONE"; push "all segments done"
