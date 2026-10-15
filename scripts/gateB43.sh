#!/bin/bash
# RULES G-B-43: the seed43 checkpoint on the Gate B render (our own render of the w040 mesh crop), plain, both depth
# orders, scored exactly as seed42 was (same labels, same supervision mask, same slice and crop, same default ink
# threshold), so the two readers are compared like for like.
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
echo $$ > $D/logs/gateB43.pid
source $R/.venv/bin/activate
out=$D/gates/gateB43; mkdir -p $out; cd $out
CK=$D/models/ink_9um/hybrid_3d2d-seed43/step-075000.pth
[ -f .infer_complete_plain_both ] || { nice -n 15 python -m vesuvius.ink_detection.inference.infer \
    $D/gates/gateB/render.zarr $CK $out/render_plain.tif --direction both --batch-size 4 --no-compile --num-workers 2 \
    && touch .infer_complete_plain_both; }
for f in render_plain render_plain_reverse; do
  [ -f auc_$f.json ] || nice -n 15 python $R/scripts/score_auc.py $f.tif \
    $D/labels/w040/w040_inklabels.zarr $D/labels/w040/w040_supervision_mask.zarr \
    --slice 14 --crop 1152 2048 2048 2048 --json auc_$f.json
done
python - <<'PY'
import json, os
f=json.load(open(os.environ.get("HERCULES_DATA", "/home/user/hercules_data") + '/gates/gateB43/auc_render_plain.json'))
r=json.load(open(os.environ.get("HERCULES_DATA", "/home/user/hercules_data") + '/gates/gateB43/auc_render_plain_reverse.json'))
res=dict(checkpoint="hybrid_3d2d-seed43/step-075000.pth", render="gates/gateB/render.zarr",
         auc_forward=f["auc"], auc_reverse=r["auc"],
         fwd_on_ink=f["mean_on_ink"], rev_on_ink=r["mean_on_ink"],
         fwd_on_blank=f["mean_on_blank"], rev_on_blank=r["mean_on_blank"],
         margin_on_ink=f["mean_on_ink"]-r["mean_on_ink"], margin_on_blank=f["mean_on_blank"]-r["mean_on_blank"],
         n_ink=f["n_ink"], n_blank=f["n_blank"],
         bars=dict(auc_forward_min=0.95, margin_on_ink_min=0.30, margin_on_blank_max=0.05),
         seed42_reference=dict(auc_forward=0.9968034031673892, margin_on_ink=0.4681, margin_on_blank=-0.0039))
res["passed"]=bool(res["auc_forward"]>=0.95 and res["margin_on_ink"]>=0.30 and res["margin_on_blank"]<=0.05)
json.dump(res, open(os.environ.get("HERCULES_DATA", "/home/user/hercules_data") + '/gates/gateB43/gateB43.json','w'), indent=1)
print(json.dumps(res, indent=1))
PY
echo "[gateB43 $(date -u +%FT%TZ)] done"
