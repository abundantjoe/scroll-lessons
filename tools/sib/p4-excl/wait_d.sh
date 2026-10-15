#!/bin/bash
# P4-D waiter: fetch tiles-a/-b every 10 min; exit when any tile_points*.npz under logs/sib/p4-tiles-<s>/
# has a blob not yet in the processed list (includes P4-B files already processed). Prints "<s> <commit> <path> <blob>".
cd /home/user/dominion
ST=/tmp/claude-0/p4excl/processed_d.txt; touch $ST
while true; do
  for s in a b; do
    br=claude/gifted-bell-gavnl5-sib-p4-tiles-$s
    git fetch -q origin $br 2>/dev/null || continue
    while read -r mode type blob path; do
      grep -q "$blob" $ST /tmp/claude-0/p4excl/processed.txt && continue
      echo "$s $(git rev-parse origin/$br) $path $blob"; exit 0
    done < <(git ls-tree -r origin/$br -- logs/sib/p4-tiles-$s | grep -E 'tile_points[^/]*\.npz$')
  done
  sleep 600
done
