#!/bin/bash
# Provenance: Project HERCULES | [id removed]
# p4v-10 (RULES.md DECL-P4-26-A2, tools/p4/BRIEF_VERSO.md items 1-7). Numbers only: no map, tile or CT image is opened.
# 1) Repro gate (item 6): forward map of w010-027:0,11 with infer.py -> logs/sib/p4v-10/fwd_x/repro/, compare png_sha256
#    with own-lead's record; REPRO PASS/FAIL into STATUS.md. On FAIL, stop (maps from a failing session are not used).
# 2) new.p4v-10 of logs/p4/verso_assign.json in list order, 2 lanes (lane k: positions k, k+2, ...), each tile verso
#    (tools/p4/infer_verso.py -> /work/own/verso_<L>) then forward (infer.py -> /work/own/fwdx_<L>), each map copied into
#    logs/sib/p4v-10/{verso,fwd_x}/tiles/ and pushed under /work/own/git.lock. Resumable (done tiles skipped).
cd /home/user/dominion
ME=p4v-10; BR=claude/gifted-bell-gavnl5-sib-p4v-10; D=logs/sib/$ME
PY=/opt/ckb/bin/python
MODEL="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json"
export OWN_WORK=/work/own
utc() { date -u +%FT%TZ; }
commit_push() {  # $1 = subject; files already staged
  git diff --cached --quiet && return 0
  git commit -qm "$1

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DQZLncR8BSMT9h8j7o88xH"
  for n in 1 2 3 4 5; do git push -q -u origin HEAD:$BR && return 0; sleep $((2**n)); done
  echo "PUSH FAILED: $1"; return 1
}
export -f commit_push utc; export BR

# ---- 1. repro gate
REF=6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102
if ! grep -q '^REPRO ' $D/STATUS.md 2>/dev/null; then
  $PY tools/sib/own-lead/infer.py $MODEL --tiles "20260701183124-w010-027:0,11" --out /work/own/fwdx_repro --threads 2 >> /work/own/repro.log 2>&1
  J=/work/own/fwdx_repro/tiles/20260701183124-w010-027_r0_c11.png.json
  [ -f $J ] || { echo "REPRO RUN FAILED $(utc)"; exit 2; }
  mkdir -p $D/fwd_x/repro/tiles
  cp /work/own/fwdx_repro/tiles/20260701183124-w010-027_r0_c11.png $J $D/fwd_x/repro/tiles/
  GOT=$($PY -c "import json;print(json.load(open('$J'))['png_sha256'])")
  FILE=$(sha256sum $D/fwd_x/repro/tiles/20260701183124-w010-027_r0_c11.png | cut -d' ' -f1)
  if [ "$GOT" = "$REF" ] && [ "$FILE" = "$REF" ]; then V=PASS; else V=FAIL; fi
  echo "- $(utc) REPRO $V: w010-027 r0c11 forward png_sha256 $GOT (file $FILE) vs own-lead $REF" >> $D/STATUS.md
  flock /work/own/git.lock bash -c "git add $D/fwd_x/repro $D/STATUS.md && commit_push '$ME: repro gate r0c11 forward map, REPRO $V (DECL-P4-26-A2 item 6)'"
  [ $V = PASS ] || { echo "REPRO FAIL - stopping"; exit 3; }
fi
grep -q '^- .* REPRO PASS' $D/STATUS.md || { echo "no REPRO PASS - stopping"; exit 3; }

# ---- 2. tiles
LIST=/work/own/p4v10_list.txt
$PY -c "
import json; a=json.load(open('logs/p4/verso_assign.json'))['new']['$ME']
assert a['verso']==a['forward'], 'lists differ'
print('\n'.join(a['verso']))" > $LIST || exit 4

push_tile() {  # $1 kind(verso|fwd_x) $2 stage $3 name $4 lane
  flock /work/own/git.lock bash -c "
    set -e; mkdir -p $D/$1/tiles
    cp $2/tiles/$3.png $2/tiles/$3.png.json $D/$1/tiles/
    echo \"- \$(utc) $1 $3 lane $4 png_sha256 \$(sha256sum $D/$1/tiles/$3.png | cut -d' ' -f1)\" >> $D/STATUS.md
    git add $D/$1/tiles/$3.png $D/$1/tiles/$3.png.json $D/STATUS.md
    commit_push '$ME: $1 map $3 (DECL-P4-26-A2, lane $4)'"
}
lane() {
  k=$1; L=$([ $k = 0 ] && echo A || echo B); i=0
  while read t; do
    if [ $((i % 2)) -eq $k ]; then
      seg=${t%%:*}; rc=${t#*:}; name=${seg}_r${rc%,*}_c${rc#*,}
      if [ ! -f $D/verso/tiles/$name.png.json ]; then
        $PY tools/p4/infer_verso.py $MODEL --tiles "$t" --out /work/own/verso_$L --threads 2 >> /work/own/lane$L.log 2>&1 \
          && push_tile verso /work/own/verso_$L $name $L || echo "FAILED verso $t"
      fi
      if [ ! -f $D/fwd_x/tiles/$name.png.json ]; then
        $PY tools/sib/own-lead/infer.py $MODEL --tiles "$t" --out /work/own/fwdx_$L --threads 2 >> /work/own/lane$L.log 2>&1 \
          && push_tile fwd_x /work/own/fwdx_$L $name $L || echo "FAILED fwd $t"
      fi
      echo "lane $L done $name $(utc)"
    fi
    i=$((i+1))
  done < $LIST
}
export D ME PY MODEL; export -f push_tile
lane 0 & P0=$!
lane 1 & P1=$!
wait $P0 $P1
N1=$(ls $D/verso/tiles/*.png.json 2>/dev/null | wc -l); N2=$(ls $D/fwd_x/tiles/*.png.json 2>/dev/null | wc -l)
echo "- $(utc) END: verso $N1/5, forward $N2/5 pushed" >> $D/STATUS.md
flock /work/own/git.lock bash -c "git add $D/STATUS.md && commit_push '$ME: end of list (verso $N1/5, forward $N2/5)'"
echo "ALL_DONE $(utc)"
