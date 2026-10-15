#!/bin/bash
# B-2UM: render and read one level-2 traced rescan patch at 2.403 um in a 1 cm^2 window, both depth orders.
# Steps (each idempotent): window_2um.py -> vc_render_tifxyz (64 slices, --scale-segmentation 4, explicit crop, no
# auto-crop) -> render crest check (R-CREST on the render's on-sheet slice profile, read_chart rules) -> run_2um.py
# (layers 1..63, forward and reverse) -> read_chart.py (rule 5.5 at 2.403 um, both maps, ledger line).
# Usage: run_2um_patch.sh <scroll> <rescan-vol> <pitch e.g. 2.403um-0.2m-77keV> <um> <patch_dir>
set -u
sc=$1; vol=$2; pitch=$3; um=$4; P=$5; D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
source $R/.venv/bin/activate
w=$P/window_2um.json; [ -f $w ] || python $R/scripts/window_2um.py $P >/dev/null
read cx cy cw < <(python -c "import json; d=json.load(open('$w')); print(d['crop_x'], d['crop_y'], d['crop_px'])")
out=$P/render_2um_${cw}px.zarr
echo "[run_2um_patch $(date -u +%FT%TZ)] window crop x=$cx y=$cy size=$cw -> $out"
RENDER_SLICES=64 RENDER_AUTOCROP=0 RENDER_CACHE_GB=${RENDER_CACHE_GB:-4} \
  RENDER_ARGS="--scale-segmentation 4 --crop-x $cx --crop-y $cy --crop-width $cw --crop-height $cw" VC_THREADS=${VC_THREADS:-2} \
  bash $R/scripts/vc_tools.sh render $sc $vol $pitch $um $P $out || { echo "render failed"; exit 1; }
# crest check on the render (same rule as the 9 um route: read_chart.crest_check on the on-sheet slice-mean profile)
python - "$out" "$P/render_crest_2um.json" <<'PY' || { echo "render crest check: VOID (see $P/render_crest_2um.json)"; exit 2; }
import os, sys, json, zarr, numpy as np
sys.path.insert(0, os.environ.get("HERCULES_ROOT", "/home/user/hercules") + '/scripts'); import read_chart as RC
a = zarr.open_group(sys.argv[1], mode='r')['0']; z = a.shape[0]
mid = np.asarray(a[z // 2]); onsheet = mid > 0
prof = [float(np.asarray(a[i])[onsheet].mean()) for i in range(z)]
c = RC.crest_check(prof); c['profile'] = [round(v, 2) for v in prof]; c['onsheet_frac_mid'] = float(onsheet.mean())
json.dump(c, open(sys.argv[2], 'w'), indent=1); print('render crest:', {k: c[k] for k in ('ratio', 'crest_slice', 'central_bounds', 'passed')})
sys.exit(0 if c['passed'] else 1)
PY
# R-COVER on the 2.4 um render: >= 80 % of the window must see papyrus within the 64 layers, else no inference
python $R/scripts/render_cover.py $out $P/render_cover_2um.json --thr 60 --bar 0.80 || { echo "R-COVER: VOID-COVER (see $P/render_cover_2um.json)"; exit 4; }
tag=ink2um_$(basename $P)
source $R/.venv2um/bin/activate
python $R/scripts/run_2um.py $out $P/read_2um --tag $tag --start 1 --end 63 --um $um || { echo "2um inference failed"; exit 3; }
source $R/.venv/bin/activate
python $R/scripts/read_chart.py $out $P/read_2um/${tag}_forward.tif $P/read_2um/${tag}_reverse.tif --um $um --out $P/read_2um \
  --key "$sc|$(basename $P)|0|ink_canonical_2um|both" --ledger $R/LEDGER.md
echo "[run_2um_patch $(date -u +%FT%TZ)] done"
