#!/bin/bash
# Poll origin sibling branch every 10 min for HANDOVER.md; exit when present or after 6h.
cd /home/user/dominion
B=claude/gifted-bell-gavnl5-sib-pairs0139
end=$(( $(date +%s) + 6*3600 ))
while [ $(date +%s) -lt $end ]; do
  git fetch -q origin $B 2>/dev/null
  if git cat-file -e origin/$B:logs/sib/pairs0139/HANDOVER.md 2>/dev/null; then
    echo "HANDOVER_FOUND $(date -u +%FT%TZ) $(git rev-parse origin/$B)"; exit 0; fi
  sleep 600
done
echo "HANDOVER_TIMEOUT $(date -u +%FT%TZ)"; exit 3
