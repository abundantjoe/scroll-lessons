#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until /work/fl3/DONE exists (max 8 attempts). Start detached:
#   nohup setsid bash tools/sib/fl3-pherc0483b/watchdog.sh >/dev/null 2>&1 &
H=$(dirname "$(readlink -f "$0")"); mkdir -p /work/fl3
for a in 1 2 3 4 5 6 7 8; do
  [ -f /work/fl3/DONE ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> /work/fl3/watchdog.log
  bash "$H/pipeline.sh" >> /work/fl3/pipeline.out 2>&1
  [ -f /work/fl3/DONE ] && exit 0; sleep 120
done
