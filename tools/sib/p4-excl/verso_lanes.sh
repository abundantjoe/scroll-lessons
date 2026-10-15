#!/bin/bash
# P4-OFF verso-mode S1 maps (RULES.md DECL-P4-26-A2 + -E1; tools/p4/BRIEF_VERSO.md). Code, wrapper, model, options, lists unchanged.
cd /home/user/dominion
ME=p4-excl; W=/work/own; BR=claude/gifted-bell-gavnl5-sib-$ME; Q=$W/queue_V.txt; F=$W/fwdlist_V.txt
VO=logs/sib/$ME/verso/tiles; FO=logs/sib/$ME/fwd_x/tiles; mkdir -p $VO $FO
[ "$(sha256sum $W/arm_S1/model_final.pth | cut -d' ' -f1)" = bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5 ] || { echo MODEL_SHA_MISMATCH >> $W/lanes_V.log; exit 2; }
ASSIGN=${ASSIGN:-logs/p4/verso_assign.json}; KEY=${KEY:-helpers}   # extra list (DECL-P4-26-A2-E2): ASSIGN=logs/p4/verso_assign_x.json KEY=extra
[ -f $Q ] || python3 -c "import json;print('\n'.join(json.load(open('$ASSIGN'))['$KEY']['$ME']['verso']))" > $Q
python3 -c "import json;print('\n'.join(json.load(open('$ASSIGN'))['$KEY']['$ME'].get('forward',[])))" > $F
pop() { ( flock 8; t=$(head -n1 $Q); [ -n "$t" ] && sed -i '1d' $Q; echo "$t" ) 8>$W/queueV.lock; }
run1() { # lane kind(verso|fwd) tile
  L=$1; k=$2; t=$3; seg=${t%%:*}; rc=${t#*:}; r=${rc%,*}; c=${rc#*,}; f=${seg}_r${r}_c${c}
  if [ $k = verso ]; then OUT=$VO; S=$W/verso_$L; PY=tools/p4/infer_verso.py; else OUT=$FO; S=$W/fwdx_$L; PY=tools/sib/own-lead/infer.py; fi
  git cat-file -e origin/$BR:$OUT/$f.png 2>/dev/null && return 0
  echo "$(date -u +%FT%TZ) lane $L $k start $t" >> $W/lanes_V.log
  OWN_WORK=$W /opt/ckb/bin/python $PY --model $W/arm_S1/model_final.pth --summary $W/arm_S1/summary.json \
    --tiles "$t" --out $S --threads 2 >> $W/laneV_$L.log 2>&1 || { echo "$(date -u +%FT%TZ) lane $L $k FAIL $t" >> $W/lanes_V.log; echo "$k $t" >> $W/failed_V.txt; return 1; }
  ( flock 9; cp $S/tiles/$f.png $S/tiles/$f.png.json $OUT/
    echo "$(date -u +%FT%TZ) $k S1 map $f (lane $L)" >> logs/sib/$ME/STATUS.md
    git add $OUT/$f.png $OUT/$f.png.json logs/sib/$ME/STATUS.md
    git commit -q -m "$ME: $k S1 map $f (DECL-P4-26-A2)

Provenance: Project HERCULES | [id removed]" -- $OUT/$f.png $OUT/$f.png.json logs/sib/$ME/STATUS.md
    for i in 1 2 3 4 5; do git push -q origin $BR && break; sleep $((2**i)); done ) 9>$W/git.lock
  echo "$(date -u +%FT%TZ) lane $L $k done $t" >> $W/lanes_V.log
}
lane() { L=$1; while t=$(pop); [ -n "$t" ]; do run1 $L verso "$t"; grep -qx "$t" $F && run1 $L fwd "$t"; done; }
lane A & sleep 90; lane B & wait
# sequential retry of failures (e.g. two lanes racing on a first download); infer resumes
if [ -s $W/failed_V.txt ]; then mv $W/failed_V.txt $W/failed_V.retry; while read -r k t; do run1 R $k "$t"; done < $W/failed_V.retry; fi
( flock 9; echo "$(date -u +%FT%TZ) verso list processed (see lanes); failures after retry: $(cat $W/failed_V.txt 2>/dev/null | wc -l)" >> logs/sib/$ME/STATUS.md
  git commit -q -m "$ME: verso list processed

Provenance: Project HERCULES | [id removed]" -- logs/sib/$ME/STATUS.md; git push -q origin $BR ) 9>$W/git.lock
