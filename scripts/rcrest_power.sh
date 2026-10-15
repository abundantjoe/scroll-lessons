#!/bin/bash
# RULES R-CREST-POWER phase 1: read the 12 largest-area VOID surfaces of the team's two published volumes with the
# crest veto off, under their own tag and ledger key. The population is fixed in RULES and listed in
# records/rcrest_power_phase1.txt (map-blind: largest on-sheet area, ties by patch name); nothing else is relaxed.
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
echo $$ > $D/logs/rcrest_power.pid
source $R/.venv/bin/activate
declare -A VOL=( [PHerc1203]=20250820131727 [PHerc1447]=20250521151220 [PHerc0800]=20250521135224 )
while read sc patch; do
  [ -z "$sc" ] && continue
  # A pause marker must stop a RUNNING queue, not merely prevent the supervisor restarting it: killing the inference
  # alone just makes the queue retry the same surface, which is what happened on 2026-09-18.
  [ -f $D/logs/rcrest_power_paused ] && { echo "[rcrest_power $(date -u +%FT%TZ)] paused"; break; }
  out=$D/patches/$sc/$patch/read_ink9um_seed42_plain_nocrest/.read_complete
  [ -f "$out" ] && { echo "[rcrest_power] $sc/$patch already done"; continue; }
  echo "[rcrest_power $(date -u +%FT%TZ)] $sc/$patch"
  nice -n 10 python $R/scripts/run_patch_dir.py $D/patches/$sc --scroll $sc --vol ${VOL[$sc]} \
    --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth --tag ink9um_seed42+plain+nocrest \
    --no-tta --reread --ignore-crest --only $patch \
    --ledger $R/LEDGER.md --records $R/records/throughput.jsonl --delete-renders
done < $R/records/rcrest_power_phase1.txt
echo "[rcrest_power $(date -u +%FT%TZ)] phase 1 complete"
