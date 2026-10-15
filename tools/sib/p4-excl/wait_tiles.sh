#!/bin/bash
# Poll origin every 3 min; exit when a tile_points.npz appears on p4-tiles-a/-b whose blob id
# differs from the one already processed (state file). Prints "<strip> <commit> <blob>".
cd /home/user/dominion
ST=/tmp/claude-0/p4excl/processed.txt; touch $ST
while true; do
  for s in a b; do
    br=claude/gifted-bell-gavnl5-sib-p4-tiles-$s
    git fetch -q origin $br 2>/dev/null || continue
    blob=$(git rev-parse -q --verify origin/$br:logs/sib/p4-tiles-$s/tile_points.npz 2>/dev/null) || continue
    grep -q "^$s $blob$" $ST && continue
    echo "$s $(git rev-parse origin/$br) $blob"; exit 0
  done
  sleep 180
done
