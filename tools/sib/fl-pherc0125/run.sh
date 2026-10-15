#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Watchdog: restarts pipeline.sh after a failure (max 20 attempts). Exit codes 3 (disk) and 4 (declared stop) end it.
D=$(dirname "$0")
for k in $(seq 1 20); do
  bash "$D/pipeline.sh" && exit 0
  rc=$?; [ $rc -eq 3 ] || [ $rc -eq 4 ] && exit $rc
  echo "[$(date -u +%FT%TZ)] pipeline rc=$rc, restart $k in 300 s" >> /home/user/dominion/logs/sib/fl-pherc0125/pipeline.log
  sleep 300
done
echo "[$(date -u +%FT%TZ)] PROBLEM: 20 failed attempts; watchdog gave up" >> /home/user/dominion/logs/sib/fl-pherc0125/pipeline.log
