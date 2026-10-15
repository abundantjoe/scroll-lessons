#!/bin/bash
# p4v-11 runner (BRIEF_VERSO items 3, 6, 7). Code/model/options unchanged.
cd /home/user/dominion
ME=p4v-11; SEG=20260701183124-w010-027
MODEL="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json"
PY=/opt/ckb/bin/python; export OWN_WORK=/work/own
TRAILER='

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H8MQGEgr6XzAsoo86WgiWu
Provenance: Project HERCULES | [id removed]'
push() { for n in 1 2 3 4 5; do git push -q -u origin claude/gifted-bell-gavnl5-sib-$ME && return 0; sleep $((2**n)); done; return 1; }
commit_files() { # msg files...
  local msg=$1; shift
  flock /work/own/git.lock -c "git add $* && { git diff --cached --quiet || git commit -qm \"$msg$TRAILER\"; }; $(declare -f push); ME=$ME push"
}
st() { flock /work/own/git.lock -c "echo '- $(date -u +%FT%TZ) $1' >> logs/sib/$ME/STATUS.md"; }

# --- repro gate (item 6)
RN=${SEG}_r0_c11; RD=logs/sib/$ME/fwd_x/repro
if [ ! -f $RD/tiles/$RN.png.json ]; then
  $PY tools/sib/own-lead/infer.py $MODEL --tiles "$SEG:0,11" --out /work/own/repro --threads 2 >> /work/own/repro.log 2>&1 || { st "SETUP ERROR (infer.py error; not a repro result)"; commit_files "$ME: repro setup error" logs/sib/$ME/STATUS.md; exit 2; }
  mkdir -p $RD/tiles && cp /work/own/repro/tiles/$RN.png /work/own/repro/tiles/$RN.png.json $RD/tiles/
fi
MINE=$($PY -c "import json;print(json.load(open('$RD/tiles/$RN.png.json'))['png_sha256'])")
FILE=$(sha256sum $RD/tiles/$RN.png | cut -d' ' -f1)
REF=$(git show origin/claude/gifted-bell-gavnl5-sib-own-lead:logs/sib/own-s1/maps/tiles/$RN.png.json | $PY -c "import json,sys;print(json.load(sys.stdin)['png_sha256'])")
if ! grep -q "REPRO PASS\|REPRO FAIL:" logs/sib/$ME/STATUS.md; then
  if [ "$MINE" = "$REF" ] && [ "$FILE" = "$REF" ]; then R=PASS; else R=FAIL; fi
  st "REPRO $R: forward $RN png_sha256 $MINE (file $FILE) vs own-lead $REF"
  commit_files "$ME: forward repro r0c11 REPRO $R (BRIEF_VERSO item 6)" $RD logs/sib/$ME/STATUS.md
fi
grep -q "REPRO PASS" logs/sib/$ME/STATUS.md || { echo "REPRO FAIL; stopping"; exit 3; }

# --- lanes (items 3, 7)
LIST="1,1 7,2 4,4 1,6 7,7"
lane() {
  k=$1; L=$([ $k = 0 ] && echo A || echo B); i=0
  for rc in $LIST; do
    if [ $((i % 2)) -eq $k ]; then
      r=${rc%,*}; c=${rc#*,}; n=${SEG}_r${r}_c${c}
      for mode in verso fwd_x; do
        D=logs/sib/$ME/$mode/tiles
        [ -f $D/$n.png.json ] && continue
        if [ $mode = verso ]; then S=/work/own/verso_$L; P=tools/p4/infer_verso.py; else S=/work/own/fwdx_$L; P=tools/sib/own-lead/infer.py; fi
        mkdir -p $S
        $PY $P $MODEL --tiles "$SEG:$r,$c" --out $S --threads 2 >> /work/own/lane$L.log 2>&1 || { st "$mode $n FAILED (lane $L)"; continue; }
        mkdir -p $D && cp $S/tiles/$n.png $S/tiles/$n.png.json $D/
        h=$($PY -c "import json;d=json.load(open('$D/$n.png.json'));print(d['png_sha256'],d.get('order','forward'))")
        st "$mode $n lane $L png_sha256/order $h"
        commit_files "$ME: $mode map ${n} (DECL-P4-26-A2, lane $L)" $D/$n.png $D/$n.png.json logs/sib/$ME/STATUS.md
      done
    fi
    i=$((i+1))
  done
}
lane 0 & lane 1 & wait
st "lanes finished"
commit_files "$ME: lanes finished" logs/sib/$ME/STATUS.md
echo ALL_DONE
