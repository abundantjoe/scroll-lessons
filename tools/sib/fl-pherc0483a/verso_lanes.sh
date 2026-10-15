#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Verso-mode S1 maps (RULES.md DECL-P4-26-A2, -E1; tools/p4/BRIEF_VERSO.md) for fl-pherc0483a. Two lanes, --threads 2,
# code UNCHANGED (tools/p4/infer_verso.py wrapper, own-lead infer.py). One shared queue in list order; each tile's verso
# map then (if listed) its forward map run back to back in the same lane. Pushed maps are skipped on a rerun.
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
ME=fl-pherc0483a; BR=claude/gifted-bell-gavnl5-sib-$ME
VO=logs/sib/$ME/verso/tiles; FO=logs/sib/$ME/fwd_x/tiles; ST=logs/sib/$ME/STATUS.md; LOG=/work/own/verso.log; Q=/work/own/queueV
mkdir -p "$VO" "$FO" /work/own
python3 -c "
import json;h=json.load(open('logs/p4/verso_assign.json'))['helpers']['$ME'];print('\n'.join(h['verso']))" > $Q.list
FWD=$(python3 -c "
import json;h=json.load(open('logs/p4/verso_assign.json'))['helpers']['$ME'];print(' '.join(h.get('forward',[])))")
echo 0 > $Q.next
M="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json --threads 2"
st() { echo "$(date -u +%FT%TZ) $ME: $*" >> "$ST"; }
push() { # push <msg> <paths...>   (caller holds /work/own/git.lock)
  local msg=$1; shift
  git add -- "$@" "$ST"
  git -c user.name="$ME" -c user.email="noreply@anthropic.com" commit -q -m "$msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QZiioTLyqFo1hNisTUtcCu
Provenance: Project HERCULES | [id removed]" >>"$LOG" 2>&1
  for i in 1 2 3 4; do git pull -q --rebase origin "$BR" >>"$LOG" 2>&1; git push -q -u origin "$BR" >>"$LOG" 2>&1 && return 0; sleep $((2**i)); done
  echo "$(date -u +%FT%TZ) push failed: $msg" >>"$LOG"; }
next_tile() { ( flock 8; i=$(cat $Q.next); echo $((i+1)) > $Q.next; sed -n "$((i+1))p" $Q.list ) 8>$Q.lock; }
one() { # one <lane> <mode verso|fwd> <seg> <r> <c>
  local L=$1 mode=$2 seg=$3 r=$4 c=$5; local n=${seg}_r${r}_c${c} od stage
  if [ $mode = verso ]; then od=$VO; stage=/work/own/verso_$L; else od=$FO; stage=/work/own/fwdx_$L; fi
  [ -f "$od/$n.png" ] && [ -f "$od/$n.png.json" ] && return 0
  echo "$(date -u +%FT%TZ) lane $L $mode start $n" >>"$LOG"
  if [ $mode = verso ]; then OWN_WORK=/work/own /opt/ckb/bin/python tools/p4/infer_verso.py $M --tiles "$seg:$r,$c" --out $stage >>/work/own/verso_$L.log 2>&1
  else OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py $M --tiles "$seg:$r,$c" --out $stage >>/work/own/fwdx_$L.log 2>&1; fi
  local rc_=$?
  if [ $rc_ -ne 0 ] || [ ! -f $stage/tiles/$n.png ]; then
    echo "$(date -u +%FT%TZ) lane $L $mode FAILED $n rc=$rc_" >>"$LOG"
    ( flock 9; st "$mode map $n FAILED rc=$rc_ (lane $L)"; push "$ME: $mode map $n failed (DECL-P4-26-A2)" ) 9>/work/own/git.lock
    return 1
  fi
  ( flock 9
    cp $stage/tiles/$n.png $stage/tiles/$n.png.json "$od/"
    st "$mode map $n pushed (lane $L, png_sha256 $(sha256sum "$od/$n.png" | cut -c1-16)...)"
    push "$ME: $mode map $n (DECL-P4-26-A2)" "$od/$n.png" "$od/$n.png.json"
  ) 9>/work/own/git.lock
}
lane() {
  local L=$1 t
  while t=$(next_tile) && [ -n "$t" ]; do
    local seg=${t%%:*} rc=${t#*:}; local r=${rc%,*} c=${rc#*,}
    one $L verso "$seg" "$r" "$c"
    case " $FWD " in *" $t "*) one $L fwd "$seg" "$r" "$c";; esac
  done
}
lane A & PA=$!
lane B & PB=$!
wait $PA $PB
NV=0; NF=0; TV=0; TF=0
while read -r t; do TV=$((TV+1)); s=${t%%:*}; rc=${t#*:}; [ -f "$VO/${s}_r${rc%,*}_c${rc#*,}.png" ] && NV=$((NV+1)); done < $Q.list
for t in $FWD; do TF=$((TF+1)); s=${t%%:*}; rc=${t#*:}; [ -f "$FO/${s}_r${rc%,*}_c${rc#*,}.png" ] && NF=$((NF+1)); done
( flock 9; st "verso list end: verso $NV/$TV, forward $NF/$TF pushed"; push "$ME: verso list end verso $NV/$TV fwd $NF/$TF (DECL-P4-26-A2)" ) 9>/work/own/git.lock
echo "$(date -u +%FT%TZ) verso end $NV/$TV $NF/$TF" >>"$LOG"
