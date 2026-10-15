#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# D3 (DECL-D3-A1/-A2) full run: the 4 arms sequentially (CTRL, FA, NULLA, REVA), 2000 steps each, 3 threads.
# Restart-safe: an arm with model_final.pth + summary.json is skipped; an unfinished arm is re-run and d3_train.py
# resumes it from <out>/resume_latest.pth (saved every 250 steps). Start it via start_d3.sh (nohup + flock).
# Each invocation is ledgered in /work/d3/work/ledger.tsv: host, cpu, command, start, end, exit, output sha256
# (sha256 of <out>/model_final.pth). Stops at the first failing arm.
set -u
cd /work/d3/work
export PYTHONPATH=/work/d3_timing/pylib OMP_NUM_THREADS=3 MKL_NUM_THREADS=3
HOST=$(hostname)
CPU="cpus=3/$(nproc) $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
LOG=/work/d3/logs/run_arms.log
echo "run_arms start $(date -u +%FT%TZ) pid $$" >> "$LOG"
for ARM in CTRL FA NULLA REVA; do
  OUT=/work/d3/runs/$ARM
  if [ -f "$OUT/model_final.pth" ] && [ -f "$OUT/summary.json" ]; then
    echo "arm $ARM already complete, skipped $(date -u +%FT%TZ)" >> "$LOG"; continue
  fi
  if [ -f "$OUT/resume_latest.pth" ]; then
    echo "arm $ARM RESUMING from $OUT/resume_latest.pth $(date -u +%FT%TZ)" >> "$LOG"
  fi
  CMD="/opt/hv-ink/bin/python /work/d3/scripts/d3_train.py --arm $ARM --steps 2000 --ckpt-every 250 --out $OUT"
  START=$(date -u +%FT%TZ)
  echo "arm $ARM start $START" >> "$LOG"
  $CMD >> /work/d3/logs/train_$ARM.log 2>&1
  RC=$?
  END=$(date -u +%FT%TZ)
  if [ "$RC" -eq 0 ] && [ -f "$OUT/model_final.pth" ]; then SHA=$(sha256sum "$OUT/model_final.pth" | cut -d' ' -f1); else SHA=missing; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$HOST" "$CPU" "PYTHONPATH=$PYTHONPATH OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 $CMD" "$START" "$END" "$RC" "$SHA" >> /work/d3/work/ledger.tsv
  echo "arm $ARM end $END rc $RC sha256 $SHA" >> "$LOG"
  if [ "$RC" -ne 0 ]; then echo "run_arms ABORT at $ARM rc=$RC" >> "$LOG"; exit "$RC"; fi
done
echo "run_arms all done $(date -u +%FT%TZ)" >> "$LOG"
