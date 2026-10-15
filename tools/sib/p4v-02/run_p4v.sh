#!/bin/bash
# Provenance: Project HERCULES | [id removed]
# p4v-02 (DECL-P4-26-A2, BRIEF_VERSO items 3-7): new.p4v-02 tiles, each VERSO (tools/p4/infer_verso.py) then FORWARD
# (own-lead infer.py), back to back, 2 lanes x 2 threads, staging /work/own/verso_L and /work/own/fwdx_L. Resumable.
cd /home/user/dominion
ME=p4v-02
echo "f3364896476b5ab8f1ef2218236877067852f93ef44718b95e3a866955941d6a  logs/p4/verso_assign.json" | sha256sum -c - || exit 3
echo "a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90  tools/p4/infer_verso.py" | sha256sum -c - || exit 3
echo "bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5  /work/own/arm_S1/model_final.pth" | sha256sum -c - || exit 3
LIST=/work/own/p4v_list.txt
/opt/ckb/bin/python -c "import json;a=json.load(open('logs/p4/verso_assign.json'))['new']['$ME'];assert a['verso']==a['forward'];[print(t) for t in a['verso']]" > $LIST || exit 4
MODEL="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json"
push_tile() {  # $1 stage dir, $2 dest dir, $3 name, $4 kind, $5 lane
  flock /work/own/git.lock -c "
    set -e
    mkdir -p $2; cp $1/tiles/$3.png $1/tiles/$3.png.json $2/
    echo '- '\$(date -u +%FT%TZ)' $4 $3 lane $5 png_sha256 '\$(sha256sum $2/$3.png | cut -c1-64) >> logs/sib/$ME/STATUS.md
    git add $2/$3.png $2/$3.png.json logs/sib/$ME/STATUS.md
    git diff --cached --quiet || { git commit -qm '$ME: S1 $4 map $3 (DECL-P4-26-A2, lane $5)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S7WzvF2vxmV1oKK5c6U9p2

Provenance: Project HERCULES | [id removed]'; for n in 1 2 3 4; do git push -q -u origin claude/gifted-bell-gavnl5-sib-$ME && break; sleep \$((2**n)); done; }
  "
}
lane() {
  k=$1; L=$2; i=0
  while read t; do
    if [ $((i % 2)) -eq $k ]; then
      seg=${t%%:*}; rc=${t#*:}; r=${rc%,*}; c=${rc#*,}; name=${seg}_r${r}_c${c}
      V=logs/sib/$ME/verso/tiles; F=logs/sib/$ME/fwd_x/tiles
      if [ ! -f $V/$name.png.json ]; then
        [ -f /work/own/verso_$L/tiles/$name.png.json ] || OWN_WORK=/work/own /opt/ckb/bin/python tools/p4/infer_verso.py $MODEL --tiles "$t" --out /work/own/verso_$L --threads 2 >> /work/own/verso_$L.log 2>&1 || { echo "FAILED verso $t"; i=$((i+1)); continue; }
        push_tile /work/own/verso_$L $V $name VERSO $L && echo "lane $L verso $name $(date -u +%H:%M)"
      fi
      if [ ! -f $F/$name.png.json ]; then
        [ -f /work/own/fwdx_$L/tiles/$name.png.json ] || OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py $MODEL --tiles "$t" --out /work/own/fwdx_$L --threads 2 >> /work/own/fwdx_$L.log 2>&1 || { echo "FAILED fwd $t"; i=$((i+1)); continue; }
        push_tile /work/own/fwdx_$L $F $name FORWARD $L && echo "lane $L fwd $name $(date -u +%H:%M)"
      fi
      [ -f $V/$name.png.json ] && [ -f $F/$name.png.json ] && rm -rf /work/own/infer_verso/S1/$name /work/own/infer/S1/$name
    fi
    i=$((i+1))
  done < $LIST
}
lane 0 A & L0=$!
lane 1 B & L1=$!
wait $L0 $L1
echo "ALL_DONE $(date -u +%FT%TZ)"
