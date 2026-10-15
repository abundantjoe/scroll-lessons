#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# D3 stage 2 restart helper; safe to re-run after any container restart. Re-launches infer_arms.sh under nohup unless
# one is already running (pgrep guard). infer_arms.sh is idempotent: arms whose inference is complete are skipped and
# d3_infer.py skips completed windows.
# Usage: /work/d3/scripts/start_d3_stage2.sh   (PID -> /work/d3/work/infer_arms.pid, log -> /work/d3/logs/infer_arms.log)
cd /work/d3/work || exit 1
if pgrep -f "bash /work/d3/scripts/infer_arms.sh" > /dev/null; then
  echo "D3 stage 2 watcher already running: pid(s) $(pgrep -f 'bash /work/d3/scripts/infer_arms.sh' | tr '\n' ' ')"; exit 0
fi
nohup bash /work/d3/scripts/infer_arms.sh >> /work/d3/logs/infer_arms.nohup 2>&1 &
echo $! > /work/d3/work/infer_arms.pid
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start_d3_stage2: launched infer_arms.sh pid $(cat /work/d3/work/infer_arms.pid)" >> /work/d3/logs/infer_arms.log
echo "started D3 stage 2 watcher: pid $(cat /work/d3/work/infer_arms.pid); log /work/d3/logs/infer_arms.log"
