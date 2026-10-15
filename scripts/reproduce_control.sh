#!/usr/bin/env bash
# reproduce_control.sh -- re-create the w040 known-text control from public data and check it against the record.
#
# Steps (each skipped if its output already exists, so the script resumes after an interruption):
#   1. fetch the w040 native stack + mesh (S3, anonymous), the w040 labels and the ink_9um checkpoint (Hugging Face)
#   2. ink_9um seed42 step-075000, plain, BOTH depth orders, on the full 28 x 6400 x 7980 stack (CPU: ~2 h per order)
#   3. Gate A: pixel ROC AUC of both maps against the human labels  (record: forward 0.99659, reverse 0.49633)
#   4. R-CTRL55: the frozen rule 5.5 on the full canvas              (record: 71 valid, 7 flagged, clusters [4, 2, 1])
#   5. the same maps through the ordinary reader, read_chart.py --maps-only (an independent code path)
#   6. bit-identity: the window [1500:3636, 2000:4136] of both maps against the pixel sha256 recorded in September
#   7. sha256 of every output
# Environment: INFER_PY = a Python 3.14 interpreter with torch 2.14.0+cpu and villa's vesuvius package at
# 5ab585ffee54331a3362b9ce6b2929b20dcde2c6 (requirements-infer.txt); PY = the analysis interpreter (requirements.txt).
#   usage: INFER_PY=/path/to/py3.14 PY=python bash scripts/reproduce_control.sh <work_dir>
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W=${1:?usage: reproduce_control.sh <work_dir>}
PY=${PY:-python}; INFER_PY=${INFER_PY:?set INFER_PY to the Python 3.14 inference interpreter}
HF=${HF:-$(dirname "$INFER_PY")/hf}
mkdir -p "$W"/{inputs,labels,models,out}
STACK="$W/inputs/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr"
CKPT="$W/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
LAB="$W/labels/w040"
FWD="$W/out/w040_full_plain.tif"; REV="$W/out/w040_full_plain_reverse.tif"
stamp() { date -u +%FT%TZ; }
retry() { local n=0; until "$@"; do n=$((n+1)); [ $n -ge 4 ] && return 1; sleep $((2**n)); done; }

echo "[$(stamp)] 1. inputs"
[ -f "$W/inputs/MANIFEST.sha256" ] || retry "$INFER_PY" "$R/scripts/fetch_control_w040.py" "$W/inputs"   # needs boto3 (requirements-infer.txt)
[ -f "$CKPT" ] || retry "$HF" download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth --local-dir "$W/models/ink_9um"
[ -d "$LAB/w040_inklabels.zarr" ] || retry "$HF" buckets sync hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w040 "$LAB"
echo "checkpoint sha256 $(sha256sum "$CKPT" | cut -d' ' -f1)  (Hugging Face LFS record: e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab)"

echo "[$(stamp)] 2. inference, both depth orders"
if [ ! -f "$W/out/.infer_complete" ]; then
  t0=$(date +%s)
  "$INFER_PY" -m vesuvius.ink_detection.inference.infer "$STACK" "$CKPT" "$FWD" \
      --direction both --batch-size 4 --no-compile --num-workers 3 > "$W/out/infer.log" 2> "$W/out/infer.err"
  echo "$(( $(date +%s) - t0 ))" > "$W/out/infer_seconds.txt"; touch "$W/out/.infer_complete"
fi
echo "inference wall time: $(cat "$W/out/infer_seconds.txt") s"
"$PY" "$R/scripts/map_integrity.py" --pair "$FWD" "$REV"

echo "[$(stamp)] 3. Gate A"
for m in "$FWD" "$REV"; do
  "$PY" "$R/scripts/score_auc.py" "$m" "$LAB/w040_inklabels.zarr" "$LAB/w040_supervision_mask.zarr" --slice 14 --ink-thr 128 \
      --json "${m%.tif}_gateA.json" > /dev/null
done
"$PY" - "$FWD" "$REV" <<'PY'
import json, sys
for m, ref in zip(sys.argv[1:], (0.99659, 0.49633)):
    j = json.load(open(m[:-4] + "_gateA.json"))
    print("%-28s AUC %.5f (record %.5f)  n_supervised %d (record 1629734)  mean on ink %.3f  on blank %.3f"
          % (m.split("/")[-1], j["auc"], ref, j["n_supervised"], j["mean_on_ink"], j["mean_on_blank"]))
PY

echo "[$(stamp)] 4. R-CTRL55 (frozen rule 5.5, full canvas)"
"$PY" "$R/scripts/rctrl55.py" --forward "$FWD" --reverse "$REV" --labels "$LAB/w040_inklabels.zarr" \
    --out "$W/out/rctrl55.json" | sed -n 1,6p

echo "[$(stamp)] 5. the ordinary reader on the same maps (independent path)"
"$PY" - "$FWD" "$REV" "$W/out/onsheet_footprint.tif" <<'PY'
import sys, numpy as np, tifffile
f, r = tifffile.imread(sys.argv[1]), tifffile.imread(sys.argv[2])
tifffile.imwrite(sys.argv[3], (((f > 0) | (r > 0)) * 255).astype(np.uint8))   # rctrl55's on-sheet definition
PY
rm -rf "$W/out/read_chart"
"$PY" "$R/scripts/read_chart.py" "$W/out/onsheet_footprint.tif" "$FWD" "$REV" --maps-only --um 9.362 \
    --out "$W/out/read_chart" --key "PHerc0139|w040_full|0|ink9um_seed42+plain|both" --ledger "$W/out/LEDGER.md" | cut -c1-160

echo "[$(stamp)] 6. bit-identity against the September record (window [1500:3636, 2000:4136])"
"$PY" - "$FWD" "$REV" <<'PY'
import hashlib, sys, tifffile, numpy as np
rec = {"forward": "4eced8f47248bc97917fde970faf912c2f2f0f2fc4e7ca77cdbe60b752c443a2",
       "reverse": "2522e6827513f358270a5b2fc72d70565a6239cf940357ceb47a747d276630f5"}
for name, m in zip(("forward", "reverse"), sys.argv[1:]):
    a = tifffile.imread(m)
    w = np.ascontiguousarray(a[1500:3636, 2000:4136])
    h = hashlib.sha256(w.tobytes()).hexdigest()
    print("%-8s window sha256 %s  %s" % (name, h, "IDENTICAL to the 2026-09-17 record" if h == rec[name] else "DIFFERS from the record " + rec[name]))
PY

echo "[$(stamp)] 7. output checksums"
( cd "$W/out" && sha256sum w040_full_plain.tif w040_full_plain_reverse.tif )
echo "[$(stamp)] done"
