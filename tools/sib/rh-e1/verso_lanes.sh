#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# rh-e1 verso/forward map lane (RULES.md DECL-P4-26-A2, -A2-E1; tools/p4/BRIEF_VERSO.md 377fa355). Code, model, options unchanged:
# verso = tools/p4/infer_verso.py (a1bd1f24), forward = tools/sib/own-lead/infer.py (36a64e1a); S1 model bfa9f7a6; --threads 2.
# Args: <lane> <tile>[+fwd] ...   A tile with "+fwd" gets its forward map right after its verso map. Never opens an image.
set -uo pipefail
cd /home/user/dominion
BR=claude/gifted-bell-gavnl5-sib-rh-e1
M=/work/own/arm_S1/model_final.pth; S=/work/own/arm_S1/summary.json
L=$1; shift
log(){ echo "$(date -u +%FT%TZ) lane $L $*"; }
push(){ # <kind:verso|fwd_x> <stage> <name>
  local K=$1 ST=$2 N=$3 OUT=logs/sib/rh-e1/$1/tiles
  ( flock 9
    mkdir -p "$OUT"; cp "$ST/tiles/$N.png" "$ST/tiles/$N.png.json" "$OUT/"
    echo "- $(date -u +%FT%TZ) $K map $N lane $L png_sha256 $(sha256sum "$OUT/$N.png" | cut -c1-64)" >> logs/sib/rh-e1/STATUS.md
    git add "$OUT/$N.png" "$OUT/$N.png.json" logs/sib/rh-e1/STATUS.md
    git commit -q -m "rh-e1: $K map $N (DECL-P4-26-A2)

Provenance: Project HERCULES | [id removed]" -- "$OUT/$N.png" "$OUT/$N.png.json" logs/sib/rh-e1/STATUS.md
    for d in 2 4 8 16 0; do git push -q origin HEAD:$BR 2>/dev/null && break; [ $d = 0 ] && log "PUSH FAIL $N"; sleep $d; git pull -q --no-rebase --no-edit origin $BR 2>/dev/null; done
    git fetch -q origin $BR
  ) 9>/work/own/git.lock
}
run(){ # <cmd> <stage> <tile>
  for k in 1 2 3; do OWN_WORK=/work/own /opt/ckb/bin/python $1 --model $M --summary $S --tiles "$3" --out "$2" --threads 2 && return 0
    log "attempt $k failed for $3"; sleep 30; done; return 1; }
for A in "$@"; do
  T=${A%+fwd}; SEG=${T%%:*}; RC=${T#*:}; N="${SEG}_r${RC%%,*}_c${RC#*,}"
  log "verso start $N"
  run tools/p4/infer_verso.py /work/own/verso_$L "$T" && push verso /work/own/verso_$L "$N" && log "verso done $N" || { log "VERSO FAIL $N"; exit 1; }
  if [ "$A" != "$T" ]; then
    log "fwd start $N"
    run tools/sib/own-lead/infer.py /work/own/fwdx_$L "$T" && push fwd_x /work/own/fwdx_$L "$N" && log "fwd done $N" || { log "FWD FAIL $N"; exit 1; }
  fi
done
log "END"
