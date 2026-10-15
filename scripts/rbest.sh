#!/bin/bash
# RULES R-BEST: the candidate-grade reader (--tta-mirror) on the geometrically pristine surfaces, a population fixed
# in RULES before any of these reads. Own ledger key (ink9um_seed42+tta), both depth orders, seed42, rule 5.5 unchanged.
# Renders are NOT deleted here: two of the three are also R-BEST/G-GP inputs and a re-render costs more than the disk.
set -u
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
echo $$ > $D/logs/rbest.pid
source $R/.venv/bin/activate
pop=$D/gates/ggp/rbest_population.json
# --reread is required: run_patch_dir.py skips a patch that already has ANY read directory, whatever its tag, and two
# of these three were screened plain. The ledger key carries the tag, so a +tta line is a new key, not a duplicate.
# The loop retries because a TTA read needs a render and rendering is held off below the 5 GB free-disk floor; it
# stops as soon as every member of the population carries a read_ink9um_seed42_tta directory, or after MAX_PASSES.
mapfile -t POP < <(python3 -c "
import json
for r in json.load(open('$pop')): print(r['scroll'], r['patch'])")
for pass_n in $(seq 1 ${MAX_PASSES:-24}); do
  left=0
  for line in "${POP[@]}"; do
    read -r sc patch <<< "$line"
    case $sc in PHerc0826) vol=20250821151701;; PHerc0358) vol=20250821151737;; *) echo "[rbest] unknown scroll $sc"; continue;; esac
    # Honour the same per-scroll pause marker the other read loops use. This is a RESOURCE decision, not a change to
    # the declared population: the member stays in its population file and resumes when the marker is removed.
    [ -f $D/patches/$sc/read_paused ] && continue
    # A read DIRECTORY appears as soon as the read starts, so an interrupted read would be mistaken for a finished one.
    # The completed-read test is its read_stats.json.
    [ -f $D/patches/$sc/$patch/read_ink9um_seed42_tta/read_stats.json ] && continue
    if ps -eo args | grep -q "[i]nk_detection.inference.infer $D/patches/$sc/$patch/render.zarr"; then
      echo "[rbest $(date -u +%FT%TZ)] $sc $patch already being read; not starting a second inference"
      left=$((left+1)); continue
    fi
    left=$((left+1))
    echo "[rbest $(date -u +%FT%TZ)] pass $pass_n: $sc $patch"
    HERCULES_INFER_LOCK=$D/logs/infer_rbest.lock nice -n 4 python $R/scripts/run_patch_dir.py $D/patches/$sc \
      --scroll $sc --vol $vol --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth \
      --tag ink9um_seed42+tta --only "$patch" --reread \
      --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null
  done
  [ "$left" -eq 0 ] && { echo "[rbest $(date -u +%FT%TZ)] every population member has its +tta read"; break; }
  sleep 600
done
echo "[rbest $(date -u +%FT%TZ)] done"
