#!/bin/bash
# Run a command under one of the GLOBAL 9 um inference slots, the same ones run_patch_dir.py takes.
# Scripts that call `infer` directly -- rdepth.sh and the gate queue -- bypassed the cap entirely, and R-DEPTH is the
# very job whose reverse pass truncated first. Usage: infer_slot.sh <command...>
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}
N=${HERCULES_INFER_SLOTS:-2}
dir=$D/logs/infer_slots; mkdir -p "$dir"
while true; do
  for i in $(seq 0 $((N-1))); do
    exec {fd}>"$dir/slot$i"
    if flock -n "$fd"; then
      "$@"; rc=$?
      exec {fd}>&-
      exit $rc
    fi
    exec {fd}>&-
  done
  sleep 5
done
