#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2-E2: (2) supplementary title strip tiles; (1) gate material = organizer PHerc0139 segments NOT in the
# official ink_9um training list, largest first, skipping known re-traces of a chosen one (w052, w053 re-trace w054):
# w054, w055, w051, w057. Same chain as fl2_gate.sh (C2-NT render, official ink_9um both directions no TTA,
# template cmd_tiles UNCHANGED, per-segment manifest + BRIEF_FL2 item 5 fields). Idempotent per unit.
set -uo pipefail
REPO=/home/user/dominion; cd "$REPO"; BR=claude/gifted-bell-gavnl5-sib-pairs0139c
L=logs/sib/pairs0139c/fl2_gate; W=/work/fl2gate; ST=$W/state; mkdir -p $ST
VOLID=20250728140407-9.362um-1.2m-113keV-masked.zarr
VOL=s3://vesuvius-challenge-open-data/PHerc0139/volumes/$VOLID/
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
SEGS="${GATE_SEGS:-20260206000002-w054_2026020617 20251226000000-w055_2025122611 20260306000001-w051_2026030600 20260127000000-w057_2026012713}"
utc() { date -u +%FT%TZ; }
log() { echo "$(utc) $*" >> $L/STATUS.md; }
push() { ( flock 9; git add $L; git commit -q -m "pairs0139c: fl2 gate $1 (DECL-FL-2-E2)

Provenance: Project HERCULES | [id removed]" -- $L; for i in 1 2 3 4; do git push -q origin $BR && break; sleep $((2**i)); done ) 9>/work/own/git.lock; }
until grep -q GATE_END $W/gate_run.log 2>/dev/null; do sleep 30; done
# (2) supplementary title strips
TS=20260422000000-title_2026042222_zmid_flatboi
if [ ! -f $ST/supp.ok ] && [ -f $ST/infer.ok ]; then
  for PF in $W/infer/$TS*.tif; do
    dl=$(basename $PF .tif); case $dl in *reverse*) dl=reverse;; *) dl=forward;; esac
    /opt/hv/bin/python tools/sib/pairs0139c/fl2_supp_tiles.py $TS $W/seg/$TS $PF $dl $L/tiles_title_supp $L/tiles_title_supp/manifest.json >> $W/gate2.log 2>&1
  done
  /opt/hv/bin/python tools/sib/pairs0139c/fl2_manifest_fields.py $L/tiles_title_supp/manifest.json $L/measure.json $VOLID >> $W/gate2.log 2>&1
  n=$(/opt/hv/bin/python -c "import json;print(len(json.load(open('$L/tiles_title_supp/manifest.json'))['tiles']))")
  touch $ST/supp.ok; log "tiles_title_supp: $n strip cells (both directions), supplementary per DECL-FL-2-E2 item 2"; push "title supplementary tiles"
fi
VS=$(/opt/hv/bin/python -c "import json;d=json.load(open('$W/vol_meta.json'));print(float(d['scan']['tomo']['acquisition']['detector']['samplePixelSize'])*1000)")
for SEG in $SEGS; do
  TSG=${SEG%%-*}; d=$W/seg/$SEG; O=$L/tiles_official/$SEG; K=$L/$SEG
  [ -f $ST/$SEG.done ] && continue
  if [ ! -f $ST/$SEG.seg ]; then
    mkdir -p $d $K/tifxyz
    ok=1; for f in meta.json x.tif y.tif z.tif; do
      curl -fsSL --retry 4 -o $d/$f "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/$SEG/mesh/$TSG-on-20250728140407-9.362um.tifxyz/$f" || ok=0; done
    [ $ok -eq 1 ] || { log "$SEG fetch FAILED"; push "$SEG fetch failed"; continue; }
    cp $d/meta.json $d/x.tif $d/y.tif $d/z.tif $K/tifxyz/; ( cd $d && sha256sum meta.json x.tif y.tif z.tif ) > $K/tifxyz/sha256.txt
    /opt/hv/bin/python tools/sib/fl-pherc0257/fl.py measure $d $K/measure.json >> $W/gate2.log 2>&1
    touch $ST/$SEG.seg; log "$SEG tifxyz fetched (sha256 in $SEG/tifxyz/sha256.txt), area $(/opt/hv/bin/python -c "import json;print(round(json.load(open('$K/measure.json'))['area_cm2'],2))") cm2"; push "$SEG tifxyz"
  fi
  R=$W/render/$SEG.zarr
  if [ ! -f $ST/$SEG.render ]; then
    rm -rf $R; mkdir -p $W/render; s=$(utc)
    /work/bin/vc vc_render_tifxyz -v $VOL --remote-url $VOL --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size $VS --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$SEG.log 2>&1; rc=$?
    echo "{\"step\":\"render\",\"segment\":\"$SEG\",\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"voxel_size_um\":$VS,\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/render_$SEG.log|cut -c1-64)\"}" >> $L/runs.jsonl
    [ $rc -eq 0 ] || { log "$SEG render FAILED rc=$rc"; tail -20 $W/render_$SEG.log > $K/render.log.tail; push "$SEG render failed"; continue; }
    touch $ST/$SEG.render; log "$SEG render done"; push "$SEG render"
  fi
  P=$W/infer/$SEG/$SEG.tif
  if [ ! -f $ST/$SEG.infer ]; then
    mkdir -p $W/infer/$SEG; s=$(utc)
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_$SEG.log 2>&1; rc=$?
    echo "{\"step\":\"infer_official\",\"segment\":\"$SEG\",\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/infer_$SEG.log|cut -c1-64)\"}" >> $L/runs.jsonl
    [ $rc -eq 0 ] || { log "$SEG infer FAILED rc=$rc"; tail -20 $W/infer_$SEG.log > $K/infer.log.tail; push "$SEG infer failed"; continue; }
    ( cd $W/infer/$SEG && sha256sum *.tif ) > $K/prediction_sha256_official.txt
    touch $ST/$SEG.infer; log "$SEG official infer done (both directions)"; push "$SEG infer"
  fi
  mkdir -p $O; tf=0
  for PF in $W/infer/$SEG/*.tif; do
    dl=$(basename $PF .tif); case $dl in *reverse*) dl=reverse;; *) dl=forward;; esac
    FL_SCROLL=PHerc0139 /opt/hv/bin/python tools/sib/fl-pherc0257/fl.py tiles $SEG $d $PF $dl organizer $O $O/manifest.json >> $W/gate2.log 2>&1 || tf=1
  done
  [ $tf -eq 0 ] || { log "$SEG tiles FAILED"; push "$SEG tiles failed"; continue; }
  /opt/hv/bin/python tools/sib/pairs0139c/fl2_manifest_fields.py $O/manifest.json $K/measure.json $VOLID >> $W/gate2.log 2>&1
  n=$(/opt/hv/bin/python -c "import json;print(len(json.load(open('$O/manifest.json'))['tiles']))")
  touch $ST/$SEG.done; rm -rf $R; log "$SEG tiles_official: $n tiles (both directions; template cmd_tiles unchanged)"; push "$SEG tiles"
done
log "GATE2 END: segments done: $(ls $ST/*.done 2>/dev/null | wc -l) ($SEGS)"; push "gate2 end"
echo GATE2_END
