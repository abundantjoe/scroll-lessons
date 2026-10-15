#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2-E3 gate in pieces (pairs0139c). Unit 0: w050 piece re-make; its tile png_sha256 are compared with the
# full-canvas w050 tiles (equivalence check of the piece method). Then held-out segments in heldout_rank.json order:
# round 1 = first 2 pieces of each of the first 3 segments, then all remaining pieces, segment after segment.
# Per piece: vc_render_tifxyz C2-NT + --crop-x/y/width/height (container --rm, so ~/.VC3D/remote_cache is deleted with it),
# official ink_9um both directions no TTA, margin cropped, full-grid cells valid >= 0.5, push. ENOSPC -> single-cell replan.
set -uo pipefail
REPO=/home/user/dominion; cd "$REPO"; BR=claude/gifted-bell-gavnl5-sib-pairs0139c
L=logs/sib/pairs0139c/fl2_gate; W=/work/fl2gate; ST=$W/state3; PV=$W/pv; mkdir -p $ST $PV
VOLID=20250728140407-9.362um-1.2m-113keV-masked.zarr; VOL=s3://vesuvius-challenge-open-data/PHerc0139/volumes/$VOLID/
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth; PY=/opt/hv/bin/python; PCS=tools/sib/pairs0139c/fl2_pieces.py
utc() { date -u +%FT%TZ; }
log() { echo "$(utc) $*" >> $L/STATUS.md; }
push() { ( flock 9; git add $L; git commit -q -m "pairs0139c: fl2 gate pieces $1 (DECL-FL-2-E3)

Provenance: Project HERCULES | [id removed]" -- $L; for i in 1 2 3 4; do git push -q origin $BR && break; sleep $((2**i)); done ) 9>/work/own/git.lock; }
VS=$($PY -c "import json;d=json.load(open('$W/vol_meta.json'));print(float(d['scan']['tomo']['acquisition']['detector']['samplePixelSize'])*1000)")
fetch() {  # fetch SEG -> $W/seg/SEG + $L/SEG/{tifxyz,measure.json}
  local SEG=$1 TSG=${1%%-*} d=$W/seg/$1 K=$L/$1
  [ -f $K/measure.json ] && [ -f $d/z.tif ] && return 0
  mkdir -p $d $K/tifxyz
  for f in meta.json x.tif y.tif z.tif; do
    curl -fsSL --retry 4 -o $d/$f "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/$SEG/mesh/$TSG-on-20250728140407-9.362um.tifxyz/$f" || return 1; done
  cp $d/meta.json $d/x.tif $d/y.tif $d/z.tif $K/tifxyz/; ( cd $d && sha256sum meta.json x.tif y.tif z.tif ) > $K/tifxyz/sha256.txt
  $PY tools/sib/fl-pherc0257/fl.py measure $d $K/measure.json > /dev/null 2>&1
  [ -f $K/measure.json ] && sha256sum -c --quiet <(cd $d && cat $K/tifxyz/sha256.txt | sed "s#  #  $d/#") 2>/dev/null; return 0
}
piece() {  # piece SEG PLAN ID OUTDIR -> 0 ok, 2 ENOSPC, 1 other failure
  local SEG=$1 PL=$2 ID=$3 OUT=$4 d=$W/seg/$1 R=$W/render/p.zarr I=$W/pinfer
  read cx cy cw ch area < <($PY -c "import json;p=json.load(open('$PL'))['pieces'][$ID];print(p['crop_x'],p['crop_y'],p['crop_w'],p['crop_h'],p['area_cm2'])")
  rm -rf $R $I; mkdir -p $W/render $I; local s=$(utc)
  /work/bin/vc vc_render_tifxyz -v $VOL --remote-url $VOL --segmentation $d --scale 1 --group-idx 0 \
    --num-slices 31 --slice-step 1 --voxel-size $VS --voxel-unit micrometer --flip-normals \
    --crop-x $cx --crop-y $cy --crop-width $cw --crop-height $ch --cache-gb 4 --zarr-output $R > $W/render_piece.log 2>&1; local rc=$?
  echo "{\"step\":\"render_piece\",\"segment\":\"$SEG\",\"piece\":$ID,\"crop\":[$cx,$cy,$cw,$ch],\"area_cm2\":$area,\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/render_piece.log|cut -c1-64)\"}" >> $L/runs.jsonl
  if [ $rc -ne 0 ]; then rm -rf $R; grep -q "No space left" $W/render_piece.log && return 2; return 1; fi
  s=$(utc)
  OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $I/p.tif \
    --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_piece.log 2>&1; rc=$?
  echo "{\"step\":\"infer_piece\",\"segment\":\"$SEG\",\"piece\":$ID,\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/infer_piece.log|cut -c1-64)\"}" >> $L/runs.jsonl
  rm -rf $R; [ $rc -eq 0 ] || return 1
  mkdir -p $OUT; echo "piece $ID $(cd $I && sha256sum *.tif | tr '\n' ' ')" >> $OUT/prediction_sha256.txt
  $PY $PCS tile $SEG $d $PL $ID $I/p.tif forward $OUT $OUT/manifest.json $VOLID $L/$SEG/measure.json >> $W/gate3.log 2>&1 || return 1
  $PY $PCS tile $SEG $d $PL $ID $I/p_reverse.tif reverse $OUT $OUT/manifest.json $VOLID $L/$SEG/measure.json >> $W/gate3.log 2>&1 || return 1
  return 0
}
# ---- unit 0: equivalence check on w050 (output kept under fl2_gate/piece_check_w050, not gate tiles) ----
V=20260302000001-w050_2026030220
if [ ! -f $ST/check.done ]; then
  $PY $PCS plan $W/seg/$V $PV/plan_w050.json >> $W/gate3.log 2>&1
  piece $V $PV/plan_w050.json 0 $L/piece_check_w050; rc=$?
  if [ $rc -eq 0 ]; then
    res=$($PY - $L/tiles_official/$V/manifest.json $L/piece_check_w050/manifest.json <<'PY'
import json, sys
a = {(t["r"], t["c"], t["direction"]): t["png_sha256"] for t in json.load(open(sys.argv[1]))["tiles"]}
b = {(t["r"], t["c"], t["direction"]): t["png_sha256"] for t in json.load(open(sys.argv[2]))["tiles"]}
same = sum(a.get(k) == v for k, v in b.items())
print(f"{same} of {len(b)} piece tiles byte-identical to the full-canvas tiles (full-canvas has {len(a)})")
PY
)
    log "PIECE CHECK w050: $res"
  else log "PIECE CHECK w050: piece run failed rc=$rc"; fi
  touch $ST/check.done; push "w050 piece check"
fi
# ---- held-out segments ----
SEGS=$($PY -c "import json;print(' '.join(r['segment'] for r in json.load(open('$L/heldout_rank.json')) if r['frac_lt4']==0 and 'w050' not in r['segment'] and 'title' not in r['segment']))")
for SEG in $SEGS; do fetch $SEG || { log "$SEG fetch FAILED"; continue; }; [ -f $PV/plan_$SEG.json ] || $PY $PCS plan $W/seg/$SEG $PV/plan_$SEG.json >> $W/gate3.log 2>&1; cp $PV/plan_$SEG.json $L/$SEG/pieces_plan.json; done
run_seg() {  # run_seg SEG MAXPIECES
  local SEG=$1 MAX=$2 n=0 PL=$PV/plan_$1.json np id rc
  np=$($PY -c "import json;print(len(json.load(open('$PL'))['pieces']))")
  for id in $(seq 0 $((np - 1))); do
    [ $n -ge $MAX ] && return 0
    key=${SEG}_$($PY -c "import json;print('_'.join(f'r{r}c{c}' for r,c in json.load(open('$PL'))['pieces'][$id]['cells']))")
    [ -f $ST/$key.done ] && continue
    piece $SEG $PL $id $L/tiles_official/$SEG; rc=$?
    if [ $rc -eq 2 ] && ! grep -q single $PL; then
      log "$SEG piece $id: ENOSPC; replanning $SEG as single-cell pieces"
      $PY $PCS plan $W/seg/$SEG $PV/plan_${SEG}_single.json --single >> $W/gate3.log 2>&1
      cp $PV/plan_${SEG}_single.json $PL; echo single > /dev/null; sed -i '1s/^{/{"single": true, /' $PL
      cp $PL $L/$SEG/pieces_plan.json; push "$SEG replan single"; run_seg $SEG $MAX; return
    fi
    if [ $rc -ne 0 ]; then log "$SEG piece $id FAILED rc=$rc"; push "$SEG piece $id failed"; touch $ST/$key.done; n=$((n+1)); continue; fi
    nt=$($PY -c "import json;m=json.load(open('$L/tiles_official/$SEG/manifest.json'));print(len([t for t in m['tiles'] if t['piece']['id']==$id]))")
    tot=$(cat $L/tiles_official/*/manifest.json | $PY -c "import sys,json;import re;print(sys.stdin.read().count('\"png_sha256\"'))")
    log "$SEG piece $id ($($PY -c "import json;p=json.load(open('$PL'))['pieces'][$id];print(p['cells'],p['area_cm2'],'cm2')")): $nt tiles; gate tiles_official total $tot"
    touch $ST/$key.done; push "$SEG piece $id"; n=$((n+1))
  done
}
set -- $SEGS
for SEG in ${1:-} ${2:-} ${3:-}; do run_seg $SEG 2; done
for SEG in $SEGS; do run_seg $SEG 1000; done
log "GATE3 END"; push "gate3 end"; echo GATE3_END
