#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Verso-mode S1 maps (tools/p4/BRIEF_VERSO.md, DECL-P4-26-A2). Two lanes take helpers.fl-pherc0191 `verso` tiles in
# list order from a shared queue (flock); for each tile the verso map (tools/p4/infer_verso.py) is made and pushed,
# then, if the tile is in the `forward` list, its forward map (own-lead infer.py) back to back (CT chunks once).
[line withheld: prize-candidate detail under review]
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
ME=fl-pherc0191; BR=claude/gifted-bell-gavnl5-sib-$ME; M=/work/own/arm_S1
VD=logs/sib/$ME/verso/tiles; FD=logs/sib/$ME/fwd_x/tiles; AF=${AF:-logs/p4/verso_assign.json}; AK1=${AK1:-helpers}; TAG=${TAG:-}   # extra list: AF=logs/p4/verso_assign_x.json AK1=extra TAG=x
Q=/work/own/V${TAG}_queue; mkdir -p "$VD" "$FD" "$Q"
exec >> /work/own/verso${TAG}_$ME.log 2>&1
say() { echo "[$(date -u +%FT%TZ)] $*"; }
st() { echo "$(date -u +%FT%TZ) $ME verso: $*" >> "logs/sib/$ME/STATUS.md"; }
push() { git commit -q -m "$1

Provenance: Project HERCULES | [id removed]" || return 0
  for i in 1 2 3 4; do git push -q -u origin "$BR" && return 0; git pull -q --rebase origin "$BR"; sleep $((2**i)); done; say "push failed: $1"; }
mapfile -t TV < <(/opt/ckb/bin/python -c "
import json;h=json.load(open('$AF'))['$AK1']['$ME'];print('\n'.join(h['verso']))")
FWD=" $(/opt/ckb/bin/python -c "
import json;h=json.load(open('$AF'))['$AK1']['$ME'];print(' '.join(h.get('forward',[])))") "
one() {  # lane kind(verso|fwd) seg r c
  local L=$1 K=$2 s=$3 r=$4 c=$5 n=${3}_r${4}_c${5} stg dst
  if [ "$K" = verso ]; then stg=/work/own/verso_$L; dst=$VD; else stg=/work/own/fwdx_$L; dst=$FD; fi
  git cat-file -e "HEAD:$dst/$n.png" 2>/dev/null && { say "$L skip $K $n"; return 0; }
  say "$L start $K $n"
  if [ "$K" = verso ]; then
    OWN_WORK=/work/own /opt/ckb/bin/python tools/p4/infer_verso.py --model "$M/model_final.pth" --summary "$M/summary.json" \
      --tiles "$s:$r,$c" --out "$stg" --threads 2 >> "$stg.log" 2>&1
  else
    OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py --model "$M/model_final.pth" --summary "$M/summary.json" \
      --tiles "$s:$r,$c" --out "$stg" --threads 2 >> "$stg.log" 2>&1
  fi
  [ -f "$stg/tiles/$n.png" ] || { say "$L FAILED $K $n"; return 1; }
  ( flock 9; cp "$stg/tiles/$n.png" "$stg/tiles/$n.png.json" "$dst/"
    st "$K $n done png_sha256 $(sha256sum "$dst/$n.png" | cut -d' ' -f1) (lane $L)"
    git add "$dst/$n.png" "$dst/$n.png.json" "logs/sib/$ME/STATUS.md"; push "$ME: $K map $n (DECL-P4-26-A2)" ) 9>/work/own/git.lock
  say "$L pushed $K $n"; }
claim() {
  ( flock 8; for t in "${TV[@]}"; do s=${t%%:*}; rc=${t#*:}; n=${s}_r${rc%,*}_c${rc#*,}
      [ -e "$Q/$n" ] && continue
      if git cat-file -e "HEAD:$VD/$n.png" 2>/dev/null; then case "$FWD" in *" $t "*) git cat-file -e "HEAD:$FD/$n.png" 2>/dev/null && continue;; *) continue;; esac; fi
      touch "$Q/$n"; echo "$t"; break; done ) 8>/work/own/V${TAG}_queue.lock; }
lane() {
  local L=$1
  while t=$(claim); [ -n "$t" ]; do
    s=${t%%:*}; rc=${t#*:}; r=${rc%,*}; c=${rc#*,}; n=${s}_r${r}_c${c}; ok=1
    one "$L" verso "$s" "$r" "$c" || ok=0
    case "$FWD" in *" $t "*) one "$L" fwd "$s" "$r" "$c" || ok=0;; esac
    if [ $ok = 0 ]; then k=$(( $(cat "$Q/$n.fail" 2>/dev/null || echo 0) + 1 )); echo $k > "$Q/$n.fail"; [ $k -lt 2 ] && rm -f "$Q/$n"; fi
  done; }
( flock 9; st "START${TAG:+ (extra list $AF $AK1)}: infer_verso.py sha256 $(sha256sum tools/p4/infer_verso.py | cut -d' ' -f1), infer.py $(sha256sum tools/sib/own-lead/infer.py | cut -d' ' -f1), own_common.py $(sha256sum tools/sib/own-lead/own_common.py | cut -d' ' -f1), model $(sha256sum $M/model_final.pth | cut -d' ' -f1); verso ${#TV[@]}, forward$(echo $FWD | wc -w)"
  git add "logs/sib/$ME/STATUS.md" tools/sib/own-lead tools/sib/ckpt-screen-b tools/p4/infer_verso.py tools/p4/BRIEF_VERSO.md $AF tools/sib/$ME/verso_lanes.sh
  push "$ME: verso maps${TAG:+ extra} start (DECL-P4-26-A2)" ) 9>/work/own/git.lock
lane A & PA=$!
for _ in $(seq 1 40); do [ -f /work/own/20260701183124-w010-027/mesh_valid.npy ] && break; sleep 30; done
lane B & PB=$!
wait $PA $PB
nv=$(ls "$VD"/*.png 2>/dev/null | wc -l); nf=$(ls "$FD"/*.png 2>/dev/null | wc -l)
( flock 9; st "END${TAG:+ extra}: verso $nv of ${#TV[@]}, forward $nf of $(echo $FWD | wc -w) pushed"; git add "logs/sib/$ME/STATUS.md"; push "$ME: verso${TAG:+ extra} list end (verso $nv, fwd $nf)" ) 9>/work/own/git.lock
touch /work/own/verso${TAG}_$ME.END
