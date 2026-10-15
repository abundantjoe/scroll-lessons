#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# First Letters screen for PHerc0125 (RULES.md DECL-FL-1; OWNER-STANDING-ORDER-5). Idempotent: every unit leaves a
# marker in $W/done/ and is skipped when present; each unit commits and pushes its numbers/tiles. No image is viewed.
# Launch: nohup bash tools/sib/fl-pherc0125/run.sh > /work/logs/fl0125_run.log 2>&1 &
set -euo pipefail
REPO=/home/user/dominion
BR=claude/gifted-bell-gavnl5-sib-p4-purple
OUT=logs/sib/fl-pherc0125
W=/work/fl0125
T=$REPO/tools/sib/fl-pherc0125
B=https://vesuvius-challenge-open-data.s3.amazonaws.com
VOL=$B/PHerc0125/volumes/20250821151825-9.362um-1.2m-113keV-masked.zarr
SURF=$B/PHerc0125/representations/predictions/surfaces/20250821151825-surface-20260413222639-surface-m7-L0-th0.2.zarr
VOX=9.362
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
PY=/opt/hv/bin/python
VC=/work/bin/vc
MAX_KEEP=4; MAX_TRIES=12; MIN_CM2=16
mkdir -p $W/done $W/grow $W/render $W/infer /work/logs "$REPO/$OUT"
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$REPO/$OUT/pipeline.log"; }
push() {  # commit and push $OUT with retries; never touches other paths
  cd "$REPO"; git add "$OUT" "tools/sib/fl-pherc0125" logs/sib/p4-purple/STATUS.md 2>/dev/null || true
  git diff --cached --quiet || git commit -qm "fl-pherc0125: $1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01TBwv1MDQJdjiR9dgoSQhVt"
  for i in 1 2 3 4 5; do git pull -q --rebase --autostash origin $BR 2>/dev/null || git rebase --abort 2>/dev/null; git push -q origin HEAD:$BR && return 0; sleep $((2**i)); done
  log "PUSH FAILED ($1)"; return 1; }
free_gb() { df -BG --output=avail / | tail -1 | tr -dc 0-9; }
need_disk() { [ "$(free_gb)" -ge "$1" ] || { log "PROBLEM: disk $(free_gb) GB < $1 GB, stopping"; exit 3; }; }

# 1. Environment
if [ ! -f $W/done/env ]; then
  log "env: setup_env.sh"; bash $REPO/docker/env/setup_env.sh >> /work/logs/fl0125_setup.log 2>&1
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet
  touch $W/done/env; log "env: OK"
fi
[ -f $W/done/env ] && { docker info >/dev/null 2>&1 || bash $REPO/docker/env/setup_env.sh >> /work/logs/fl0125_setup.log 2>&1; }

# 2. Segments: organizer tifxyz if any, else grow on the organizer surface-m7 prediction
if [ ! -f $W/done/segments ]; then
  ORG=$($PY $REPO/tools/c3/s3ls.py PHerc0125/segments/ 2>/dev/null | awk '$1=="P"' | wc -l || true)
  if [ "$ORG" -gt 0 ]; then log "PROBLEM: organizer segments now exist ($ORG); pipeline expects none (checked 2026-09-30). Stop for a declared update."; exit 4; fi
  log "segments: none from the organizers; growing (<= $MAX_TRIES tries, keep <= $MAX_KEEP, 0 self-crossings, >= $MIN_CM2 cm2)"
  cat > $W/grow/params.json <<J
{"mode": "seed", "voxelsize": $VOX, "use_cuda": false, "thread_limit": 3, "generations": 300, "step_size": 20,
 "min_area_cm": $MIN_CM2, "cache_size": 2000000000, "cache_root": "$W/grow/cache"}
J
  for n in $(seq 1 $MAX_TRIES); do
    kept=$(find $W/done -name "seg_*" | wc -l); [ "$kept" -ge $MAX_KEEP ] && break
    [ -f $W/done/try_$n ] && continue
    need_disk 8; s=grow_a$n; mkdir -p $W/grow/surf
    # shared target dir: the tool's seed search avoids existing surfaces there (check_existing_segments)
    before=$(ls $W/grow/surf | sort)
    log "grow try $n"
    timeout 5h $VC vc_grow_seg_from_seed -v $SURF -t $W/grow/surf -p $W/grow/params.json \
      > /work/logs/fl0125_$s.log 2>&1 || log "grow try $n rc=$?"
    rm -rf $W/grow/cache
    new=$(comm -13 <(echo "$before") <(ls $W/grow/surf | sort) | head -1)
    [ -n "$new" ] && [ -f $W/grow/surf/$new/x.tif ] && mv $W/grow/surf/$new $W/grow/$s && ln -s ../$s $W/grow/surf/$new
    if [ -f $W/grow/$s/x.tif ]; then
      a=$($PY $T/fl_tools.py area $W/grow/$s $VOX)
      $VC vc_tifxyz_selfcross --surface $W/grow/$s -o $W/grow/$s.selfcross.json > /dev/null 2>&1 || true
      clean=$($PY -c "import json;print(json.load(open('$W/grow/$s.selfcross.json')).get('clean_of_transverse_self_intersection'))" 2>/dev/null || echo None)
      ok=$($PY -c "print(int($a >= $MIN_CM2 and '$clean' == 'True'))")
      echo "{\"try\": $n, \"segment\": \"$s\", \"area_cm2\": $a, \"clean_of_transverse_self_intersection\": \"$clean\", \"kept\": $ok}" >> $REPO/$OUT/grow_tries.jsonl
      mkdir -p $REPO/$OUT/$s; cp $W/grow/$s/meta.json $REPO/$OUT/$s/meta.json 2>/dev/null || true
      cp $W/grow/$s.selfcross.json $REPO/$OUT/$s/selfcross.json 2>/dev/null || true
      [ "$ok" = 1 ] && touch $W/done/seg_$s
      [ "$ok" = 1 ] || { rm -rf $W/grow/$s; rm -f $W/grow/surf/$new; }
    else
      echo "{\"try\": $n, \"segment\": \"$s\", \"produced\": false}" >> $REPO/$OUT/grow_tries.jsonl
    fi
    touch $W/done/try_$n; push "grow try $n"
  done
  touch $W/done/segments
  log "segments: kept $(find $W/done -name "seg_*" | wc -l)"; push "segments done"
fi

# 3-4. Render (C2-NT), ink inference (ink_9um step-075000, both, no TTA, CPU), tiles
for m in $(ls $W/done/seg_* 2>/dev/null); do
  s=${m##*/seg_}; R=$W/render/$s.zarr; P=$W/infer/$s/pred.tif
  if [ ! -f $W/done/render_$s ]; then
    need_disk 10; rm -rf $R; log "render $s"
    VC_CPUS=3 OMP_NUM_THREADS=3 $VC vc_render_tifxyz -v $VOL --remote-url $VOL --segmentation $W/grow/$s --scale 1 \
      --group-idx 0 --num-slices 31 --slice-step 1 --voxel-size $VOX --voxel-unit micrometer --flip-normals \
      --cache-gb 2 --zarr-output $R > /work/logs/fl0125_render_$s.log 2>&1
    touch $W/done/render_$s
  fi
  if [ ! -f $W/done/infer_$s ]; then
    mkdir -p $W/infer/$s; log "infer $s"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > /work/logs/fl0125_infer_$s.log 2>&1
    touch $W/done/infer_$s
  fi
  if [ ! -f $W/done/tiles_$s ]; then
    log "tiles $s"; rm -rf $REPO/$OUT/$s/tiles
    SRC="{\"scroll\": \"PHerc0125\", \"volume\": \"$VOL\", \"surface\": \"$SURF\", \"segment_origin\": \"vc_grow_seg_from_seed (no organizer segments)\", \"render\": \"C2-NT vc_render_tifxyz -n 31 --flip-normals --scale 1\", \"model\": \"ink_9um hybrid_3d2d-seed42 step-075000 sha256 $CKPT_SHA, --direction both, no TTA, CPU\", \"pred_sha256\": \"$(sha256sum $P | cut -c1-64)\"}"
    $PY $T/fl_tools.py tiles $s $P $R $REPO/$OUT/$s $VOX "$SRC" >> $REPO/$OUT/pipeline.log 2>&1
    touch $W/done/tiles_$s; push "tiles $s"
    rm -rf $R   # render is regenerable; free disk
  fi
done
nseg=$(find $W/done -name "tiles_*" | wc -l)
[ "$nseg" -gt 0 ] || { log "PROBLEM: 0 segments kept after $MAX_TRIES grow tries; see grow_tries.jsonl"; echo "- $(date -u +%FT%TZ) fl-pherc0125: PROBLEM 0 segments kept (grow_tries.jsonl)." >> $REPO/logs/sib/p4-purple/STATUS.md; push "0 segments"; exit 4; }
log "ALL DONE"; echo "- $(date -u +%FT%TZ) fl-pherc0125 pipeline: ALL DONE ($(find $W/done -name "tiles_*" | wc -l) segments with tiles)." >> $REPO/logs/sib/p4-purple/STATUS.md
push "pipeline all done"
