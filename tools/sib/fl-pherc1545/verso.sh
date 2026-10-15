#!/bin/bash
# Provenance: Project HERCULES | [id removed]
# Verso-mode S1 maps (RULES.md DECL-P4-26-A2 / -E1; brief tools/p4/BRIEF_VERSO.md). Code UNCHANGED: infer_verso.py wrapper
# for verso, own-lead infer.py for forward; S1 model; --threads 2 per lane. Units in verso-list order; a tile also on the
# forward list gets its forward map right after its verso map (CT chunks downloaded once). Two lanes share one queue
# (atomic mkdir claims); staging /work/own/verso_{A,B} and /work/own/fwdx_{A,B}. Resumable: pushed maps are skipped.
cd /home/user/dominion
ME=fl-pherc1545; BR=claude/gifted-bell-gavnl5-sib-fl-pherc1545; ST=logs/sib/$ME/STATUS.md; Q=/work/own/claims_V
MODEL="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json"
echo "bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5  /work/own/arm_S1/model_final.pth" | sha256sum -c --quiet || exit 3
echo "ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9  tools/sib/own-lead/own_common.py" | sha256sum -c --quiet || exit 3
echo "36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e  tools/sib/own-lead/infer.py" | sha256sum -c --quiet || exit 3
echo "a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90  tools/p4/infer_verso.py" | sha256sum -c --quiet || exit 3
VL=$(/opt/ckb/bin/python -c "import json;print(' '.join(json.load(open('logs/p4/verso_assign.json'))['helpers']['$ME']['verso']))")
FL=$(/opt/ckb/bin/python -c "import json;print(' '.join(json.load(open('logs/p4/verso_assign.json'))['helpers']['$ME'].get('forward',[])))")
commit() {
  git commit -q -m "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01HjwFB1nLT48AX8E28FR4CX

Provenance: Project HERCULES | [id removed]"
  for n in 1 2 3 4 5; do git push -q origin HEAD:$BR 2>>/work/own/push.err && return; git pull -q --rebase origin $BR 2>>/work/own/push.err; sleep $((2**n)); done
}
export -f commit; export BR
nm() { seg=${1%%:*}; rc=${1#*:}; echo ${seg}_r${rc%,*}_c${rc#*,}; }
one() {  # $1 mode verso|fwd  $2 tile  $3 lane
  mode=$1; t=$2; k=$3; name=$(nm $t)
  if [ $mode = verso ]; then OUT=logs/sib/$ME/verso/tiles; S=/work/own/verso_$k; PROG=tools/p4/infer_verso.py
  else OUT=logs/sib/$ME/fwd_x/tiles; S=/work/own/fwdx_$k; PROG=tools/sib/own-lead/infer.py; fi
  [ -f $OUT/$name.png.json ] && return
  mkdir -p $S; t0=$(date +%s)
  OWN_WORK=/work/own /opt/ckb/bin/python $PROG $MODEL --tiles "$t" --out $S --threads 2 >> /work/own/infer_V$k.log 2>&1
  if [ ! -f $S/tiles/$name.png.json ]; then
    flock /work/own/git.lock bash -c "echo \"\$(date -u +%FT%TZ) $ME: $mode map $name FAILED (lane $k)\" >> $ST"; return
  fi
  flock /work/own/git.lock bash -c "
    mkdir -p $OUT && cp $S/tiles/$name.png $S/tiles/$name.png.json $OUT/
    echo \"\$(date -u +%FT%TZ) $ME: $mode map $name done (lane $k, $(( $(date +%s)-t0 )) s, png_sha256 \$(sha256sum $OUT/$name.png | cut -c1-16)...)\" >> $ST
    git add $OUT/$name.png $OUT/$name.png.json $ST
    commit '$ME: $mode map $name (DECL-P4-26-A2)'"
  echo "lane $k $mode done $name $(date -u +%H:%M:%S)"
}
rm -rf $Q; mkdir -p $Q
lane() {
  k=$1
  for t in $VL; do
    name=$(nm $t); mkdir $Q/$name 2>/dev/null || continue
    one verso $t $k
    case " $FL " in *" $t "*) one fwd $t $k;; esac
  done
}
lane A & PA=$!
lane B & PB=$!
wait $PA $PB
NV=$(ls logs/sib/$ME/verso/tiles/*.png.json 2>/dev/null | wc -l); NF=$(ls logs/sib/$ME/fwd_x/tiles/*.png.json 2>/dev/null | wc -l)
flock /work/own/git.lock bash -c "echo \"\$(date -u +%FT%TZ) $ME: verso list finished: verso $NV of $(echo $VL | wc -w), forward $NF of $(echo $FL | wc -w) pushed\" >> $ST; git add $ST; commit '$ME: verso maps finished (verso $NV, forward $NF)'"
echo "VERSO_END v$NV f$NF"
