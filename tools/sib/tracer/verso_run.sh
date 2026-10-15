#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Verso-mode S1 maps (tracer) per tools/p4/BRIEF_VERSO.md (sha256 377fa355...), RULES.md DECL-P4-26-A2.
# Code unchanged: tools/p4/infer_verso.py (verso) and tools/sib/own-lead/infer.py (forward). Never opens or views an
# image: files are only copied and hashed.
#   setsid nohup bash tools/sib/tracer/verso_run.sh > /work/logs/verso.log 2>&1 &
# Two lanes take tiles in list order from a shared queue; for each tile: verso map, then (if listed) its forward map.
set -uo pipefail
REPO=/home/user/dominion; cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-tracer
OV=logs/sib/tracer/verso/tiles; OF=logs/sib/tracer/fwd_x/tiles
ST=logs/sib/tracer/STATUS.md
MODEL_SHA=bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5
Q=/work/own/queueV_${VA_KEY:-helpers}; mkdir -p "$OV" "$OF" $Q
ts() { date -u +%FT%TZ; }
echo "$MODEL_SHA  /work/own/arm_S1/model_final.pth" | sha256sum -c --quiet || { echo "$(ts) MODEL SHA MISMATCH"; exit 3; }
# list source (DECL-P4-26-A2-E2 extra lists): VA_FILE / VA_KEY select the assignment file and its top-level key
VA_FILE=${VA_FILE:-logs/p4/verso_assign.json}; VA_KEY=${VA_KEY:-helpers}
readarray -t VERSO < <(/opt/hv/bin/python -c "import json;print('\n'.join(json.load(open('$VA_FILE'))['$VA_KEY']['tracer']['verso']))")
FWD=" $(/opt/hv/bin/python -c "import json;print(' '.join(json.load(open('$VA_FILE'))['$VA_KEY']['tracer'].get('forward', [])))") "
tile_name() { local seg=${1%%:*} rc=${1#*:}; echo "${seg}_r${rc%%,*}_c${rc##*,}"; }
M=(--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json --threads 2)
publish() {  # src_dir dst_dir name kind lane
  ( flock 9
    cp "$1/tiles/$3.png" "$1/tiles/$3.png.json" "$2/" || exit 1
    echo "$(ts) $4 map $3 pushed (lane $5, png sha256 $(sha256sum "$2/$3.png" | cut -c1-16)...)" >> "$ST"
    git add "$2/$3.png" "$2/$3.png.json" "$ST"
    git commit -q -m "tracer: $4 map $3 (DECL-P4-26-A2)

Provenance: Project HERCULES | [id removed]" || exit 0
    for t in 2 4 8 16; do git push -q origin $BR && exit 0; sleep $t; done; exit 1 ) 9>/work/own/git.lock
}
done_tile() {  # tile -> 0 if every map it needs is pushed
  local n; n=$(tile_name "$1")
  [ -f "$OV/$n.png.json" ] || return 1
  case "$FWD" in *" $1 "*) [ -f "$OF/$n.png.json" ] || return 1;; esac
  return 0
}
claim() {
  ( flock 8
    for t in "${VERSO[@]}"; do
      done_tile "$t" && continue
      n=$(tile_name "$t"); [ -f "$Q/$n.claimed" ] && continue
      touch "$Q/$n.claimed"; echo "$t"; break
    done ) 8>$Q/claim.lock
}
lane() {
  local L=$1 t n
  while true; do
    t=$(claim); [ -z "$t" ] && return 0
    n=$(tile_name "$t")
    if [ ! -f "$OV/$n.png.json" ]; then
      echo "$(ts) lane $L verso $t"
      OWN_WORK=/work/own /opt/ckb/bin/python tools/p4/infer_verso.py "${M[@]}" --tiles "$t" --out /work/own/verso_$L \
        >> /work/logs/verso_lane$L.log 2>&1 || { echo "$(ts) lane $L verso FAILED $t"; rm -f "$Q/$n.claimed"; return 1; }
      publish /work/own/verso_$L "$OV" "$n" verso "$L" || { echo "$(ts) lane $L publish FAILED $t"; return 1; }
    fi
    case "$FWD" in *" $t "*)
      if [ ! -f "$OF/$n.png.json" ]; then
        echo "$(ts) lane $L forward $t"
        OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py "${M[@]}" --tiles "$t" --out /work/own/fwdx_$L \
          >> /work/logs/verso_lane$L.log 2>&1 || { echo "$(ts) lane $L forward FAILED $t"; rm -f "$Q/$n.claimed"; return 1; }
        publish /work/own/fwdx_$L "$OF" "$n" forward "$L" || { echo "$(ts) lane $L publish FAILED $t"; return 1; }
      fi;;
    esac
    echo "$(ts) lane $L done $t"
  done
}
lane A & PA=$!
lane B & PB=$!
wait $PA; RA=$?; wait $PB; RB=$?
if [ $RA -eq 0 ] && [ $RB -eq 0 ]; then
  ( flock 9; echo "$(ts) verso maps: all ${#VERSO[@]} verso tiles and their forward maps pushed (tracer)" >> "$ST"
    git add "$ST"; git commit -q -m "tracer: verso maps complete (DECL-P4-26-A2)

Provenance: Project HERCULES | [id removed]"; for t in 2 4 8 16; do git push -q origin $BR && break; sleep $t; done ) 9>/work/own/git.lock
  echo "VERSO DONE"; exit 0
fi
echo "VERSO FAILED A=$RA B=$RB"; exit 1
