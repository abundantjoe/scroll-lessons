#!/bin/bash
# RULES R-BEST-2: the candidate-grade reader (--tta-mirror) over every sound-geometry surface that lacks one.
# Population fixed in RULES before any of these reads. Own ledger key (ink9um_seed42+tta), both depth orders, seed42,
# rule 5.5 unchanged. Renders are deleted after each read: 42.6 cm2 of renders will not fit on this box at once.
set -u
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
echo $$ > $D/logs/rbest2.pid
source $R/.venv/bin/activate
pop=$D/gates/ggp/rbest2_population.json
mapfile -t POP < <(python3 -c "
import json
for r in json.load(open('$pop')): print(r['scroll'], r['patch'])")
for pass_n in $(seq 1 ${MAX_PASSES:-40}); do
  left=0
  for line in "${POP[@]}"; do
    read -r sc patch <<< "$line"
    # $sc is a patches DIRECTORY name. PHerc0826_small, PHerc0826_src, PHerc0826_cons_part4 and PHerc0826_dense are
    # all the same scroll and the same volume; only the directory differs. --scroll must be the real scroll or
    # volume_info raises KeyError on the catalogue, which is exactly what it did for every PHerc0826_small member.
    base=${sc%%_*}
    case $base in
      PHerc0826) vol=20250821151701 ;;
      PHerc0358) vol=20250821151737 ;;
      PHerc1447) vol=20250521151220 ;;
      PHerc1203) vol=20250820131727 ;;
      *) echo "[rbest2] unknown scroll $base (from directory $sc)"; continue ;;
    esac
    # Honour the same per-scroll pause marker the other read loops use. This is a RESOURCE decision, not a change to
    # the declared population: the member stays in its population file and resumes when the marker is removed.
    [ -f $D/patches/$sc/read_paused ] && continue
    # A read DIRECTORY appears when the read starts; the completion test is its read_stats.json.
    [ -f $D/patches/$sc/$patch/read_ink9um_seed42_tta/read_stats.json ] && continue
    if ps -eo args | grep -q "[i]nk_detection.inference.infer $D/patches/$sc/$patch/render.zarr"; then
      echo "[rbest $(date -u +%FT%TZ)] $sc $patch already being read; not starting a second inference"
      left=$((left+1)); continue
    fi
    left=$((left+1))
    echo "[rbest2 $(date -u +%FT%TZ)] pass $pass_n: $sc $patch"
    HERCULES_INFER_LOCK=$D/logs/infer_rbest2.lock nice -n 6 python $R/scripts/run_patch_dir.py $D/patches/$sc \
      --scroll $base --vol $vol --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth \
      --tag ink9um_seed42+tta --only "$patch" --reread --delete-renders \
      --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null
  done
  [ "$left" -eq 0 ] && { echo "[rbest2 $(date -u +%FT%TZ)] every population member has its +tta read"; break; }
  sleep 300
done
echo "[rbest2 $(date -u +%FT%TZ)] done"
