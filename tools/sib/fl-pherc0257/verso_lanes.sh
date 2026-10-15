#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Verso-mode S1 maps (tools/p4/BRIEF_VERSO.md, DECL-P4-26-A2/-E1). Two lanes x --threads 2; code, model, options unchanged.
# Unit = one listed tile: its verso map (tools/p4/infer_verso.py, --out /work/own/verso_<lane>) then, if it is on the
# forward list, its forward map (own-lead infer.py, --out /work/own/fwdx_<lane>) back to back. Units keep list order,
# claimed under the shared lock. Idempotent: pushed maps are never redone. No image is opened.
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
ME=fl-pherc0257; BR=claude/gifted-bell-gavnl5-sib-$ME; VO=logs/sib/$ME/verso/tiles; FO=logs/sib/$ME/fwd_x/tiles
ST=logs/sib/$ME/STATUS.md; LK=/work/own/git.lock; CL=/work/own/claimV; mkdir -p $VO $FO $CL
readarray -t VL < <(python3 -c "import json;print(*json.load(open('logs/p4/verso_assign.json'))['helpers']['$ME']['verso'],sep='\n')")
FL=" $(python3 -c "import json;print(*json.load(open('logs/p4/verso_assign.json'))['helpers']['$ME'].get('forward',[]))") "
M=(--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json --threads 2)
push() { for d in 2 4 8 16; do git push -q -u origin $BR 2>>/work/own/push.err && return 0; git pull -q --rebase origin $BR 2>>/work/own/push.err; sleep $d; done; echo "push failed" >> /work/own/push.err; }
cmt() { git commit -q -m "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EcTkrkkwgJUPqRDZ4FKKoB
Provenance: Project HERCULES | [id removed]"; push; }
one() {  # $1 lane, $2 mode verso|fwd, $3 tile
  seg=${3%%:*}; rc=${3#*:}; r=${rc%,*}; c=${rc#*,}; name=${seg}_r${r}_c${c}
  if [ $2 = verso ]; then S=/work/own/verso_$1; O=$VO; P=tools/p4/infer_verso.py; else S=/work/own/fwdx_$1; O=$FO; P=tools/sib/own-lead/infer.py; fi
  [ -s $O/$name.png.json ] && return 0
  mkdir -p $S; t0=$(date +%s)
  OWN_WORK=/work/own /opt/ckb/bin/python $P "${M[@]}" --tiles "$3" --out $S >> /work/own/laneV_$1.log 2>&1; rc_=$?
  src=$(ls $S/tiles/*_r${r}_c${c}.png 2>/dev/null | grep -F "$seg" | head -1)
  ( flock 9
    if [ $rc_ -eq 0 ] && [ -n "$src" ] && [ -s "$src.json" ]; then
      cp "$src" $O/$name.png; cp "$src.json" $O/$name.png.json
      echo "$(date -u +%FT%TZ) $ME $2 map $name lane $1: done in $(( $(date +%s)-t0 )) s, png_sha256 $(sha256sum $O/$name.png | cut -c1-16)..." >> $ST
      git add $O/$name.png $O/$name.png.json $ST; cmt "$ME: $2 map $name (DECL-P4-26-A2)"
    else
      echo "$(date -u +%FT%TZ) $ME $2 map $name lane $1: FAILED rc=$rc_ (log /work/own/laneV_$1.log)" >> $ST
      git add $ST; cmt "$ME: $2 map $name failed (DECL-P4-26-A2)"
    fi ) 9>$LK
}
lane() {
  for t in "${VL[@]}"; do
    seg=${t%%:*}; rc=${t#*:}; name=${seg}_r${rc%,*}_c${rc#*,}
    ( flock 9; mkdir $CL/$name 2>/dev/null ) 9>$LK || continue
    one $1 verso "$t"
    case "$FL" in *" $t "*) one $1 fwd "$t";; esac
  done
}
lane A & lane B & wait
nv=$(ls $VO/*.png 2>/dev/null | wc -l); nf=$(ls $FO/*.png 2>/dev/null | wc -l)
( flock 9; echo "$(date -u +%FT%TZ) $ME verso maps end: verso $nv of ${#VL[@]}, forward $nf of $(echo $FL | wc -w) pushed" >> $ST; git add $ST; cmt "$ME: verso maps end (DECL-P4-26-A2)" ) 9>$LK
