#!/bin/sh
# Provenance: Project HERCULES | owner the owner | [id removed]
# Order (DECL-P4-24-A1 ruling): holes -> (e2) validate v1 and v2 -> (e2) beyond with a VALID variant (v1 first) -> DECL-P4-26 facing.
set -u
S=/home/user/scratch; T=/home/user/dominion/tools/sib/p4-core
while ps aux | grep -q "[h]oles.py /home"; do sleep 60; done
python3 $T/holes_agg.py $S/holes/rows.jsonl $S/holes/holes_agg.json > $S/holes/agg.log 2>&1
PMIN=$(python3 -c "import json;print(json.load(open('$S/holes/holes_agg.json'))['p_min_prominence'])")
cd $T
[ -f $S/e2_validate_v1.json ] || python3 edge_follow.py $S/mesh $PMIN $S/e2_validate_v1.json validate v1 > $S/e2_validate_v1.log 2>&1
[ -f $S/e2_validate_v2.json ] || python3 edge_follow.py $S/mesh $PMIN $S/e2_validate_v2.json validate v2 > $S/e2_validate_v2.log 2>&1
for V in v1 v2; do
  if python3 -c "import json,sys;sys.exit(0 if json.load(open('$S/e2_validate_$V.json')).get('VALID') else 1)"; then
    PM=$(python3 -c "import json;print(json.load(open('$S/e2_validate_$V.json'))['p_min'])")
    python3 edge_follow.py $S/mesh $PM $S/e2_beyond_$V.json beyond $V > $S/e2_beyond_$V.log 2>&1
    break
  fi
done
python3 facing.py $S/mesh $S/facing control > $S/facing/log.txt 2>&1
python3 facing.py $S/mesh $S/facing title >> $S/facing/log.txt 2>&1
echo CHAIN_DONE > $S/chain.done
