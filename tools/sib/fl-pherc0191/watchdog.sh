#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Watchdog: relaunch pipeline.sh (detached) whenever it is not running, until ALL.done.
# Start (also after a container restart): setsid nohup bash tools/sib/fl-pherc0191/watchdog.sh >/dev/null 2>&1 &
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ST=$REPO/logs/sib/fl-pherc0191/state
mkdir -p /work/fl/pherc0191/logs
exec 9> /work/fl/pherc0191/watchdog.lock
flock -n 9 || exit 0
n=0
while [ ! -f "$ST/ALL.done" ]; do
  if ! pgrep -f "tools/sib/fl-pherc0191/pipeline.sh" >/dev/null; then
    n=$((n+1))
    [ $n -gt 6 ] && { echo "[$(date -u +%FT%TZ)] watchdog: 6 launches, giving up" >> /work/fl/pherc0191/logs/pipeline.log; exit 1; }
    setsid nohup bash "$REPO/tools/sib/fl-pherc0191/pipeline.sh" > /dev/null 2>&1 < /dev/null &
  fi
  sleep 600
done
