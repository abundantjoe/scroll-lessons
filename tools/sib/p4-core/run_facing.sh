#!/bin/sh
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-P4-26 facing meshes: P_MIN pass, then title windows (3 shards), then controls (3 shards). Resumable per tile.
S=/home/user/scratch; cd /home/user/dominion/tools/sib/p4-core
python3 facing.py $S/mesh $S/facing pmin > $S/facing/pmin.log 2>&1
for W in title control; do
  for k in 0 1 2; do python3 facing.py $S/mesh $S/facing $W $k/3 > $S/facing/$W.$k.log 2>&1 & done
  wait
done
echo FACING_DONE > $S/facing/done
