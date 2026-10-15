#!/bin/sh
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-P4-26(-A1): control peaks (3 shards) -> control rules + acceptance -> title peaks (3 shards) -> title rules. Resumable.
S=/home/user/scratch; cd /home/user/dominion/tools/sib/p4-core
for W in control title; do
  for k in 0 1 2; do python3 facing2.py peaks $S/mesh $S/facing $W $k/3 > $S/facing/peaks.$W.$k.log 2>&1 & done
  wait
  python3 facing2.py rules $S/mesh $S/facing $W $S/audit/rows.jsonl > $S/facing/rules.$W.log 2>&1
done
echo FACING2_DONE > $S/facing/done2
