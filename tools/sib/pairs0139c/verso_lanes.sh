#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-P4-26-A2 (+E1) verso-mode S1 maps, helper pairs0139c: tools/p4/BRIEF_VERSO.md sha256 377fa355...,
# logs/p4/verso_assign.json sha256 f3364896... Code unchanged (infer_verso.py a1bd1f24, infer.py 36a64e1a,
# own_common.py ddf90770, ckpt-screen-b 98cd075), model S1 bfa9f7a6, --threads 2, two lanes.
# Tiles are claimed in list order (mkdir); each tile's verso map, then (if listed) its forward map, back to back.
[line withheld: prize-candidate detail under review]
# Idempotent: maps whose .png.json is already in the repo out dir are skipped.
set -uo pipefail
REPO=/home/user/dominion; ME=pairs0139c; BR=claude/gifted-bell-gavnl5-sib-$ME
VO=logs/sib/$ME/verso/tiles; FO=logs/sib/$ME/fwd_x/tiles
ST=$REPO/logs/sib/$ME/STATUS.md; RUNS=$REPO/logs/sib/$ME/runs.jsonl; LOCK=/work/own/git.lock; CL=/work/own/claimV
VERSO="20260701183124-w010-027:4,15 20260701183124-w010-027:0,17 20260701183124-w010-027:5,18 20260701183124-w010-027:1,20 20260701183124-w010-027:6,9 20260701183124-w010-027:2,11 20260701183124-w010-027:7,12"
FWD=" 20260701183124-w010-027:1,20 20260701183124-w010-027:6,9 "
M=/work/own/arm_S1/model_final.pth; SU=/work/own/arm_S1/summary.json
cd "$REPO"; mkdir -p "$CL"
utc() { date -u +%FT%TZ; }
push() { for i in 1 2 3 4; do git push -q -u origin "$BR" && return 0; sleep $((2 ** i)); done; echo "$(utc) push failed" >> /work/own/lanesV.err; return 1; }
nm() { local seg=${1%%:*} rc=${1#*:}; echo "${seg}_r${rc%,*}_c${rc#*,}"; }
run_map() {  # run_map LANE TILE MODE(verso|fwd)
  local L=$1 t=$2 mode=$3 name seg s ec osha prog stage dest
  name=$(nm "$t"); seg=${t%%:*}; s=$(utc)
  if [ "$mode" = verso ]; then prog=tools/p4/infer_verso.py; stage=/work/own/verso_$L; dest=$VO
  else prog=tools/sib/own-lead/infer.py; stage=/work/own/fwdx_$L; dest=$FO; fi
  [ -f "$dest/$name.png.json" ] && return 0
  local cmd="OWN_WORK=/work/own /opt/ckb/bin/python $prog --model $M --summary $SU --tiles $t --out $stage --threads 2"
  (
    if [ ! -f "/work/own/$seg/mesh_valid.npy" ]; then flock 8; fi
    OWN_WORK=/work/own /opt/ckb/bin/python $prog --model $M --summary $SU --tiles "$t" --out $stage --threads 2 \
      > /work/own/laneV_${mode}_${L}_$name.log 2>&1
  ) 8>"/work/own/seg_$seg.lock"
  ec=$?; osha=$(sha256sum /work/own/laneV_${mode}_${L}_$name.log | cut -c1-64)
  (
    flock 9
    echo "{\"tag\":\"${mode}_$name\",\"lane\":\"$L\",\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"command\":\"$cmd\",\"exit\":$ec,\"output_sha256\":\"$osha\"}" >> "$RUNS"
    if [ $ec -eq 0 ] && [ -f $stage/tiles/$name.png.json ]; then
      mkdir -p "$dest"; cp $stage/tiles/$name.png $stage/tiles/$name.png.json "$dest/"
      psha=$(sha256sum "$dest/$name.png" | cut -c1-64)
      echo "$(utc) $mode $name done (lane $L) png_sha256 $psha" >> "$ST"
      git add "$dest/$name.png" "$dest/$name.png.json" "$ST" "$RUNS"
      git commit -q -m "$ME: S1 $mode map $name (DECL-P4-26-A2)

Provenance: Project HERCULES | [id removed]" -- "$dest/$name.png" "$dest/$name.png.json" "$ST" "$RUNS"
      push
    else
      echo "$(utc) $mode $name FAILED exit $ec (lane $L)" >> "$ST"
      git add "$ST" "$RUNS"; git commit -q -m "$ME: S1 $mode map $name failed (exit $ec)

Provenance: Project HERCULES | [id removed]" -- "$ST" "$RUNS"; push
    fi
  ) 9>"$LOCK"
  return $ec
}
lane() {
  local L=$1 t name ok
  for t in $VERSO; do
    name=$(nm "$t")
    if [ -f "$VO/$name.png.json" ]; then case "$FWD" in *" $t "*) [ -f "$FO/$name.png.json" ] && continue;; *) continue;; esac; fi
    mkdir "$CL/$name" 2>/dev/null || continue
    ok=1
    run_map "$L" "$t" verso || ok=0
    case "$FWD" in *" $t "*) run_map "$L" "$t" fwd || ok=0;; esac
    [ $ok -eq 1 ] || rmdir "$CL/$name"
  done
}
lane A & pa=$!
lane B & pb=$!
wait $pa $pb
nv=0; for t in $VERSO; do [ -f "$VO/$(nm $t).png.json" ] && nv=$((nv+1)); done
nf=0; for t in $FWD; do [ -f "$FO/$(nm $t).png.json" ] && nf=$((nf+1)); done
( flock 9; echo "$(utc) END verso pass: verso $nv of 7, forward $nf of 2 pushed" >> "$ST"
  git add "$ST"; git commit -q -m "$ME: verso pass end (verso $nv/7, forward $nf/2)

Provenance: Project HERCULES | [id removed]" -- "$ST"; push ) 9>"$LOCK"
echo VLANES_END
