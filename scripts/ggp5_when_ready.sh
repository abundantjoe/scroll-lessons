#!/bin/bash
# RULES G-GP part 5: build the consensus the moment the dense queue finishes, without waiting for a human.
# Fires ONCE, and only when every declared part-5 seed has a .done marker and no dense loop is still running.
# It does not choose anything: the source set, the parameters and the bars are all already declared.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
sc=PHerc0826; vol=20250821151701; um=9.362
tgt=$D/patches/${sc}_cons_part5
[ -d "$tgt" ] && { echo "[ggp5] part 5 consensus already built"; exit 0; }
[ -f $D/patches/${sc}_dense/dense_paused ] && { echo "[ggp5] dense queue paused; not building"; exit 0; }
need=$($R/.venv/bin/python -c "
import json; print(len(json.load(open('$D/gates/ggp/part5_seeds.json'))['seeds']))")
have=$($R/.venv/bin/python -c "
import json, os
D='$D'; sc='$sc'
seeds=json.load(open(D+'/gates/ggp/part5_seeds.json'))['seeds']
print(sum(os.path.exists('%s/patches/%s_dense/logs/seed_%s_%s_%s.done' % (D, sc, s['x'], s['y'], s['z'])) for s in seeds))")
# Check the loops' OWN pid files, not a pattern match. `pgrep -f "dense_loop.sh PHerc0826"` matches any shell whose
# command line merely CONTAINS that string - including the very shell that launched this script - and on
# 2026-09-19 07:43 UTC that self-match made the build refuse to start with both queues already finished.
running=0
for pf in $D/patches/${sc}_dense/dense_loop_*.pid; do
  [ -f "$pf" ] || continue
  kill -0 "$(cat "$pf")" 2>/dev/null && running=$((running+1))
done
echo "[ggp5 $(date -u +%FT%TZ)] part-5 seeds done $have/$need; dense loops running $running"
[ "$have" -ge "$need" ] || exit 0
[ "${running:-0}" -eq 0 ] || { echo "[ggp5] a dense loop is still running; waiting"; exit 0; }
# the seed of the consensus growth is the same point part 4 used, so the two generations are comparable
read -r X Y Z <<< "$($R/.venv/bin/python -c "
import json; s=json.load(open('$D/gates/ggp/part4_consensus_seed.json')) if __import__('os').path.exists('$D/gates/ggp/part4_consensus_seed.json') else None
print('3590 2095 4179' if s is None else '%s %s %s' % (s['x'], s['y'], s['z']))")"
echo "[ggp5 $(date -u +%FT%TZ)] building the part-5 consensus at seed $X $Y $Z from every dense source"
PART=5 bash $R/scripts/ggp4_consensus.sh "$sc" "$vol" "$um" "$X" "$Y" "$Z" 6
# RULES G-GP part 5b: the same sources at consensus threshold 4, built and MEASURED but read only if it meets the
# same geometry bars as part 5 (<= 1.42 crossings/cm2 and p90 sag <= 9.93 um, the w040 control's own). The read
# decision is made from the measurements below, never from the area.
echo "[ggp5 $(date -u +%FT%TZ)] building the part-5b consensus at threshold 4 from the same sources"
PART=5b bash $R/scripts/ggp4_consensus.sh "$sc" "$vol" "$um" "$X" "$Y" "$Z" 4
echo "[ggp5 $(date -u +%FT%TZ)] part 5b geometry gate (RULES G-GP part 5b): the bars decide, never the area"
if $R/.venv/bin/python $R/scripts/ggp5b_decide.py --part 5b --pop cons_part5b; then
  echo "[ggp5 $(date -u +%FT%TZ)] part 5b ADMITTED; it is read alongside part 5"
  READ_DIRS="$tgt $D/patches/${sc}_cons_part5b"
else
  echo "[ggp5 $(date -u +%FT%TZ)] part 5b NOT ADMITTED: area bought at the cost of geometry, recorded and not read"
  READ_DIRS="$tgt"
fi
echo "[ggp5 $(date -u +%FT%TZ)] consensus built; reading at the centre window, plain, seed42"
for rd in $READ_DIRS; do
  [ -d "$rd" ] || { echo "[ggp5] $rd does not exist; skipping"; continue; }
  HERCULES_INFER_LOCK=$D/logs/infer_prod.lock nice -n 10 $R/.venv/bin/python $R/scripts/run_patch_dir.py \
    "$rd" --scroll "$sc" --vol "$vol" --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth \
    --tag ink9um_seed42+plain --no-tta --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null
done
echo "[ggp5 $(date -u +%FT%TZ)] done"
