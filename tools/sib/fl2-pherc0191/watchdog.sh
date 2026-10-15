#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Watchdog: (re)starts pipeline.sh until logs/sib/fl2-pherc0191/PIPELINE_DONE exists; at most 8 attempts.
# After a container restart: setsid nohup bash tools/sib/fl2-pherc0191/watchdog.sh >/dev/null 2>&1 &
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); L=$REPO/logs/sib/fl2-pherc0191; W=/work/fl2-pherc0191
mkdir -p "$W" "$L"; echo $$ > "$W/watchdog.pid"; n=0
while [ ! -f "$L/PIPELINE_DONE" ] && [ $n -lt 8 ]; do
  n=$((n+1)); echo "[$(date -u +%FT%TZ)] watchdog: attempt $n" >> "$L/pipeline.log"
  bash "$REPO/tools/sib/fl2-pherc0191/pipeline.sh" >> "$W/pipeline.out" 2>&1
  [ -f "$L/PIPELINE_DONE" ] || sleep 300
done
echo "[$(date -u +%FT%TZ)] watchdog: exit (done=$([ -f "$L/PIPELINE_DONE" ] && echo yes || echo no), attempts=$n)" >> "$L/pipeline.log"
