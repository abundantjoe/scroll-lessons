#!/bin/bash
# RULES R-CREST-POWER, the informative half: the three PHerc1203 members, on their OWN inference lock.
# The PHerc1447 member in flight selected 9614 patches and will hold the global lock for hours, and the published
# normal field says PHerc1447's surfaces genuinely cross-cut (27 of 31 below |cos| 0.90) while PHerc1203's agree with
# it at 0.9967 and still render flat - so PHerc1203 is where this experiment's information is. Running them in
# parallel wastes no inference and reaches the informative half now. Same population, same decision rule, same tag.
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
echo $$ > $D/logs/rcrest_power_1203.pid
export HERCULES_INFER_LOCK=$D/logs/infer_1203.lock
source $R/.venv/bin/activate
while read sc patch; do
  [ -z "$sc" ] && continue
  # A pause marker must stop a RUNNING queue, not merely prevent the supervisor restarting it: killing the inference
  # alone just makes the queue retry the same surface, which is what happened on 2026-09-18.
  [ -f $D/logs/rcrest_power_1203_paused ] && { echo "[rcrest_power $(date -u +%FT%TZ)] paused"; break; }
  [ -f $D/patches/$sc/$patch/read_ink9um_seed42_plain_nocrest/.read_complete ] && { echo "[rcrest_1203] $sc/$patch already done"; continue; }
  echo "[rcrest_1203 $(date -u +%FT%TZ)] $sc/$patch"
  # the render floor is a WAIT, not a reason to drop a declared population member: one PHerc1203 surface was
  # skipped outright on 2026-09-18 because free disk happened to sit at 4.9 GB for a minute
  for i in $(seq 1 120); do
    f=$(df --output=avail -k / | tail -1)
    [ "$f" -ge 5200000 ] && break
    sleep 60
  done
  nice -n 10 python $R/scripts/run_patch_dir.py $D/patches/$sc --scroll $sc --vol 20250820131727 \
    --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth --tag ink9um_seed42+plain+nocrest \
    --no-tta --reread --ignore-crest --only $patch \
    --ledger $R/LEDGER.md --records $R/records/throughput.jsonl --delete-renders
done < $R/records/rcrest_power_1203.txt
echo "[rcrest_1203 $(date -u +%FT%TZ)] PHerc1203 members complete"
