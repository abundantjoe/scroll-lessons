#!/bin/bash
# RULES R-DEPTH: sweep the reader's 17-slice window across the 28-slice Gate B render (our own render of the w040
# mesh crop) and score each window against the published ink labels, exactly as Gate B and G-B-43 were scored.
# No tracing and no rendering: --layer-start/--layer-end move the window inside a render already on disk.
# CENTRE is NOT re-run -- it is gates/gateB/auc_render_plain{,_reverse}.json, recorded before the bar was written.
set -u
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
echo $$ > $D/logs/rdepth.pid
source $R/.venv/bin/activate
out=$D/gates/rdepth; mkdir -p $out; cd $out
CK=$D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth
REN=$D/gates/gateB/render.zarr
run_window() {  # run_window <name> <layer-start> <layer-end>
  local w=$1 s=$2 e=$3
  if [ ! -f .infer_complete_$w ]; then
    echo "[rdepth $(date -u +%FT%TZ)] window $w layers $s..$e"
    # take a GLOBAL inference slot: rdepth.sh calls infer directly and so bypassed run_patch_dir.py's cap entirely,
    # and this is the job whose reverse pass truncated first
    bash $R/scripts/infer_slot.sh nice -n 19 python -m vesuvius.ink_detection.inference.infer "$REN" "$CK" "$out/$w.tif" \
      --direction both --layer-start "$s" --layer-end "$e" --batch-size 4 --no-compile --num-workers 2
    # An exit code of 0 is NOT proof the maps were written. On 2026-09-19 this call returned 0 having written
    # exactly one quadrant of high_reverse.tif; the unwritten zeros were then scored as if the model had answered
    # zero there and produced an ADMITTED verdict out of nothing. The pair is verified before anything is scored.
    if python $R/scripts/map_integrity.py --json $out/integrity_$w.json 2>&1 | grep -q "SUSPECT $out/$w.tif"; then
      echo "[rdepth $(date -u +%FT%TZ)] TRUNCATED MAPS for window $w -- deleting them and refusing to score"
      rm -f "$out/$w.tif" "$out/${w}_reverse.tif"
      return 1
    fi
    touch .infer_complete_$w
  fi
  for f in $w ${w}_reverse; do
    [ -f auc_$f.json ] || nice -n 19 python $R/scripts/score_auc.py $f.tif \
      $D/labels/w040/w040_inklabels.zarr $D/labels/w040/w040_supervision_mask.zarr \
      --slice 14 --crop 1152 2048 2048 2048 --json auc_$f.json
  done
}
run_window low 0 17
run_window high 11 28
python $R/scripts/rdepth_result.py
echo "[rdepth $(date -u +%FT%TZ)] done"
