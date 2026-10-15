#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-P4-26-A2 (+E1): own-lead's 80 VERSO-mode S1 maps of w010-027 c9-c19 x r0-r7 (logs/p4/verso_assign.json "own-lead"
# .verso, sha256 f3364896..., list order), wrapper tools/p4/infer_verso.py (sha256 a1bd1f24...; infer.py unchanged),
# 2 lanes x 2 threads with per-lane staging /work/own/verso_A|verso_B; under /work/own/git.lock each tile's .png and
# .png.json move to logs/sib/own-s1/verso/tiles/ and are committed + pushed. Resumable. At the end relaunches
[line withheld: prize-candidate detail under review]
cd /home/user/dominion
touch /work/own/PAUSE
git show origin/claude/gifted-bell-gavnl5:logs/p4/verso_assign.json > /work/own/verso_assign.json
echo "f3364896476b5ab8f1ef2218236877067852f93ef44718b95e3a866955941d6a  /work/own/verso_assign.json" | sha256sum -c - || exit 3
echo "a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90  tools/p4/infer_verso.py" | sha256sum -c - || exit 3
LIST=/work/own/verso_list.txt
/opt/ckb/bin/python -c "import json;d=json.load(open('/work/own/verso_assign.json'));assert d['model_final_sha256']=='bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5';[print(t) for t in d['own-lead']['verso']]" > $LIST || exit 4
OUT=logs/sib/own-s1/verso
MODEL="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json"
lane() {
  k=$1; L=$2; i=0; STAGE=/work/own/verso_$L
  while read t; do
    if [ $((i % 2)) -eq $k ]; then
      seg=${t%%:*}; rc=${t#*:}; r=${rc%,*}; c=${rc#*,}; name=${seg}_r${r}_c${c}
      if [ ! -f $OUT/tiles/$name.png.json ]; then
        if [ ! -f $STAGE/tiles/$name.png.json ]; then
          OWN_WORK=/work/own /opt/ckb/bin/python tools/p4/infer_verso.py $MODEL --tiles "$t" --out $STAGE --threads 2 >> /work/own/infer_verso$L.log 2>&1 || { echo "FAILED $t"; i=$((i+1)); continue; }
        fi
        flock /work/own/git.lock -c "
          set -e
          mkdir -p $OUT/tiles; mv $STAGE/tiles/$name.png $STAGE/tiles/$name.png.json $OUT/tiles/
          git add $OUT/tiles/$name.png $OUT/tiles/$name.png.json
          git diff --cached --quiet || { git commit -qm 'own-lead: S1 VERSO map $name (DECL-P4-26-A2, lane $L)

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013RMBx9vJymzu55FFHNHGfd'; for n in 1 2 3 4; do git push -q origin HEAD && break; sleep \$((2**n)); done; }
        "
        rm -rf /work/own/infer_verso/S1/$name
        echo "lane $L done $name $(date -u +%H:%M)"
      fi
    fi
    i=$((i+1))
  done < $LIST
}
lane 0 A & L0=$!
lane 1 B & L1=$!
wait $L0 $L1
echo "ALL_VERSO_DONE $(date -u +%FT%TZ)"
pgrep -f "^/bin/bash tools/sib/own-lead/run_Qlanes.sh" > /dev/null || setsid nohup tools/sib/own-lead/run_Qlanes.sh >> /work/own/run_Qlanes.log 2>&1 < /dev/null &
