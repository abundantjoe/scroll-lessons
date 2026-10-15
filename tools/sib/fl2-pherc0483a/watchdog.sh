#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Restarts pipeline.sh until the DONE marker exists (max 8 attempts, 2 min apart). Single instance via flock.
H=$(dirname "$(readlink -f "$0")"); REPO=$(git -C "$H" rev-parse --show-toplevel); W=/work/fl2_0483a; mkdir -p $W
exec 9>$W/watchdog.lock; flock -n 9 || exit 0
for a in 1 2 3 4 5 6 7 8; do
  [ -f $W/DONE ] || [ -f "$REPO/logs/sib/fl2-pherc0483a/DONE" ] && exit 0
  echo "$(date -u +%FT%TZ) watchdog attempt $a" >> $W/watchdog.log
  bash "$H/pipeline.sh" >> $W/pipeline.out 2>&1
  [ -f $W/DONE ] && exit 0; sleep 120
done
