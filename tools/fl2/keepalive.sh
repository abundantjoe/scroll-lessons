#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# FL2 zero-turn keep-alive (owner order 2026-10-01: "compute with zero turns, maximize brute compute").
# Run as ONE harness-tracked background Bash (run_in_background, timeout 7200000); it keeps the session alive
# without model turns. Every 120 s it restarts the worker's detached watchdog if it is not running (also after a
# container restart). It prints nothing and exits after ~7150 s (one wake per 2 h), or at once (one line) if the
# done marker exists, meaning the seed list is exhausted and must be extended.
# usage: bash tools/fl2/keepalive.sh <you>      (override paths with env WD=<watchdog.sh> DONE=<done marker>)
Y=${1:?worker name}; REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
WD=${WD:-$REPO/tools/sib/$Y/fl2/watchdog.sh}; DONE=${DONE:-$REPO/logs/sib/$Y/fl2/PIPELINE_DONE}
[ -f "$WD" ] || { echo "keepalive: no watchdog at $WD (set WD=)"; exit 2; }
mkdir -p /work; end=$((SECONDS+7150))
while [ $SECONDS -lt $end ]; do
  [ -f "$DONE" ] && { echo "keepalive: DONE marker present ($DONE): extend the seed list, then re-arm"; exit 0; }
  if ! pgrep -f "$WD" >/dev/null; then
    (cd "$REPO" && setsid nohup bash "$WD" >/dev/null 2>&1 </dev/null &)
    echo "[$(date -u +%FT%TZ)] keepalive: (re)launched $WD" >> /work/fl2_keepalive.log
  fi
  sleep 120
done
