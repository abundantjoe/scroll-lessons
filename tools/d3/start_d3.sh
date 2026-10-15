#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# D3 launcher; safe to re-run after any container restart. Starts run_arms.sh in the background under nohup,
# holding an exclusive flock so a second copy can never run concurrently (a re-run while one is alive just exits).
# Finished arms are skipped; the unfinished arm resumes from its latest 250-step checkpoint.
# Usage: /work/d3/scripts/start_d3.sh      (PID -> /work/d3/work/run_arms.pid, logs -> /work/d3/logs/)
cd /work/d3/work || exit 1
if ! flock -n /work/d3/work/run_arms.lock true; then
  echo "D3 run already active (lock held; pid file: $(cat /work/d3/work/run_arms.pid 2>/dev/null))"; exit 0
fi
nohup flock -n /work/d3/work/run_arms.lock /work/d3/scripts/run_arms.sh >> /work/d3/logs/run_arms.nohup 2>&1 &
echo $! > /work/d3/work/run_arms.pid
echo "started D3 run: pid $(cat /work/d3/work/run_arms.pid); logs /work/d3/logs/run_arms.log, /work/d3/logs/train_<ARM>.log"
