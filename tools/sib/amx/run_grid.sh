#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Item 3 grid: {infer, train} x {fp32, bf16} x threads {1,2,4} x channels_last {0,1}; 5 warm-up + 20 timed.
# Resumable: a configuration already present in the output jsonl is skipped. Runs strictly one at a time.
cd "$(dirname "$0")"
OUT=${GRID_OUT:-/home/user/dominion/logs/sib/amx/bench_grid.jsonl}
export PYTHONPATH=/work/amx/pylib
for mode in infer train; do for th in 4 2 1; do for cl in 0 1; do for dt in fp32 bf16; do
  key="\"mode\": \"$mode\", \"dtype\": \"$dt\", \"threads\": $th, \"channels_last\": $([ $cl = 1 ] && echo true || echo false)"
  if [ -f $OUT ] && grep -qF "$key" $OUT; then echo "skip $key"; continue; fi
  CPUS=$(seq -s, 0 $((th-1)))
  taskset -c $CPUS /opt/hv-ink/bin/python bench.py --mode $mode --dtype $dt --threads $th --cl $cl --out $OUT 2>&1 | tail -n 1
done; done; done; done
echo GRID_DONE
