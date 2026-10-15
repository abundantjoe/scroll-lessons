#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4 GP-model gate (pairs0139c): 2 x 2 cell blocks (rows 0-1, cols 0-1) of w054, w055, w052, w053 as the two
# DECL-FL-2-E3 column pieces each; variants A and B; both directions. Order: A(w054, w055), B(w054, w055), then
# w052 A, B and w053 A, B. Push per segment and variant. Idempotent by marker files.
set -uo pipefail
REPO=/home/user/dominion; cd "$REPO"; BR=claude/gifted-bell-gavnl5-sib-pairs0139c
L=logs/sib/pairs0139c/fl4_gate; W=/work/gp; ST=$W/state; mkdir -p $ST $W/render $W/pred $L
FW=/work/fl2gate; PV=$FW/pv; VOLID=20250728140407-9.362um-1.2m-113keV-masked.zarr; VOL=s3://vesuvius-challenge-open-data/PHerc0139/volumes/$VOLID/
GPY=/opt/gp/bin/python; PY=/opt/hv/bin/python; FLL=logs/sib/pairs0139c/fl2_gate
utc() { date -u +%FT%TZ; }
log() { echo "$(utc) $*" >> $L/STATUS.md; }
push() { ( flock 9; git add $L; git commit -q -m "pairs0139c: fl4 GP gate $1 (DECL-FL-4)

Provenance: Project HERCULES | [id removed]" -- $L; for i in 1 2 3 4; do git push -q origin $BR && break; sleep $((2**i)); done ) 9>/work/own/git.lock; }
VS=$($PY -c "import json;d=json.load(open('$FW/vol_meta.json'));print(float(d['scan']['tomo']['acquisition']['detector']['samplePixelSize'])*1000)")
pids() { $PY -c "import json;p=json.load(open('$PV/plan_$1.json'))['pieces'];print(' '.join(str(x['id']) for x in p if sorted(map(tuple,x['cells'])) in ([(0,0),(1,0)],[(0,1),(1,1)])))"; }
render() {  # render SEG ID
  local SEG=$1 ID=$2 R=$W/render/$1_p$2.zarr
  [ -f $R.ok ] && return 0
  read cx cy cw ch < <($PY -c "import json;p=json.load(open('$PV/plan_$SEG.json'))['pieces'][$ID];print(p['crop_x'],p['crop_y'],p['crop_w'],p['crop_h'])")
  rm -rf $R; local s=$(utc)
  /work/bin/vc vc_render_tifxyz -v $VOL --remote-url $VOL --segmentation $FW/seg/$SEG --scale 1 --group-idx 0 \
    --num-slices 31 --slice-step 1 --voxel-size $VS --voxel-unit micrometer --flip-normals \
    --crop-x $cx --crop-y $cy --crop-width $cw --crop-height $ch --cache-gb 4 --zarr-output $R > $W/render.log 2>&1; local rc=$?
  echo "{\"step\":\"render_piece\",\"segment\":\"$SEG\",\"piece\":$ID,\"crop\":[$cx,$cy,$cw,$ch],\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/render.log|cut -c1-64)\"}" >> $L/runs.jsonl
  [ $rc -eq 0 ] && touch $R.ok; return $rc
}
segvar() {  # segvar SEG VARIANT
  local SEG=$1 V=$2 OUT=$L/tiles_gp_$2/$1 id dir P n
  [ -f $ST/$SEG.$V.done ] && return 0
  for id in $(pids $SEG); do
    render $SEG $id || { log "$SEG piece $id render FAILED"; push "$SEG render failed"; return 1; }
    for dir in forward reverse; do
      P=$W/pred/${SEG}_p${id}_${V}_$dir.tif
      if [ ! -f $P.ok ]; then
        s=$(utc); $GPY tools/sib/pairs0139c/gp_infer.py run $W/render/${SEG}_p$id.zarr $P $V $dir > $W/infer.log 2>&1; rc=$?
        echo "{\"step\":\"gp_infer\",\"segment\":\"$SEG\",\"piece\":$id,\"variant\":\"$V\",\"direction\":\"$dir\",\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"exit\":$rc,\"result\":$(tail -1 $W/infer.log | grep '^{' || echo null)}" >> $L/runs.jsonl
        [ $rc -eq 0 ] || { log "$SEG p$id $V $dir infer FAILED rc=$rc"; tail -20 $W/infer.log > $L/infer_fail.log.tail; push "$SEG infer failed"; return 1; }
        touch $P.ok
      fi
      $PY tools/sib/pairs0139c/gp_tile.py $SEG $FW/seg/$SEG $PV/plan_$SEG.json $id $P $dir $OUT $OUT/manifest.json $VOLID $FLL/$SEG/measure.json $V >> $W/tile.log 2>&1 || { log "$SEG p$id $V $dir tile FAILED"; return 1; }
    done
  done
  ( cd $W/pred && sha256sum ${SEG}_p*_${V}_*.tif ) > $OUT/prediction_sha256.txt
  n=$($PY -c "import json;print(len(json.load(open('$OUT/manifest.json'))['tiles']))")
  touch $ST/$SEG.$V.done; log "$SEG variant $V: $n tiles (rows 0-1, cols 0-1; both directions)"; push "$SEG $V"
}
cleanup() { [ -f $ST/$1.A.done ] && [ -f $ST/$1.B.done ] && rm -rf $W/render/$1_p*.zarr $W/render/$1_p*.zarr.ok; return 0; }
S054=20260206000002-w054_2026020617; S055=20251226000000-w055_2025122611; S052=20260227000000-w052_2026022705; S053=20260220000000-w053_2026022021
# fp32 vs bf16 check on real data (first piece of w054), once
if [ ! -f $ST/check.done ]; then
  id=$(pids $S054 | cut -d' ' -f1); render $S054 $id && $GPY tools/sib/pairs0139c/gp_infer.py check $W/render/${S054}_p$id.zarr $L/precision_check.json > $W/check.log 2>&1
  log "precision check (fp32 vs villa bf16 autocast, w054 640 px crop, variant A forward): $(tr -d '\n ' < $L/precision_check.json 2>/dev/null || echo FAILED)"; touch $ST/check.done; push "precision check"
fi
segvar $S054 A; segvar $S055 A; segvar $S054 B; segvar $S055 B; cleanup $S054; cleanup $S055
for S in $S052 $S053; do segvar $S A; segvar $S B; cleanup $S; done
log "GP GATE END"; push "end"; echo GPGATE_END
