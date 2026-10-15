#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until /work/fl3-0343/DONE exists (max 8 attempts, 5 min apart). Launch:
#   setsid nohup bash tools/sib/fl3-pherc0343/watchdog.sh >/dev/null 2>&1 < /dev/null &
H=$(dirname "$(readlink -f "$0")"); mkdir -p /work/fl3-0343
for a in 1 2 3 4 5 6 7 8; do
  [ -f /work/fl3-0343/DONE ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> /work/fl3-0343/watchdog.log
  bash "$H/pipeline.sh" >> /work/fl3-0343/pipeline.out 2>&1
  [ -f /work/fl3-0343/DONE ] && exit 0; sleep 300
done
echo "$(date -u +%FT%TZ) watchdog gave up after 8 attempts" >> /work/fl3-0343/watchdog.log
