#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Wait for logs/sib/pairs0139/HANDOVER.md on the pairs0139 branch: git fetch every INTERVAL s (default 600); exit 0 when it appears,
# exit 3 after MAX_S seconds (default 6 h from the start time recorded in the first argument, epoch seconds).
B=claude/gifted-bell-gavnl5-sib-pairs0139
START=${1:-$(date +%s)}; MAX_S=${MAX_S:-21600}
cd /home/user/dominion
while true; do
  git fetch -q origin "$B" 2>/dev/null
  if git cat-file -e "origin/$B:logs/sib/pairs0139/HANDOVER.md" 2>/dev/null; then
    echo "HANDOVER present $(date -u +%FT%TZ) tip $(git rev-parse origin/$B)"; exit 0; fi
  [ $(( $(date +%s) - START )) -ge "$MAX_S" ] && { echo "timeout $(date -u +%FT%TZ)"; exit 3; }
  sleep "${INTERVAL:-600}"
done
