#!/usr/bin/env python
"""Gate A / Gate C scorer: pixel ROC AUC of a stored prediction TIFF (uint8 = p*255) against a label zarr
slice on the supervised pixels. Never resamples the map. Reports AUC, mean prediction on ink / blank, n px.
usage: score_auc.py <pred.tif> <inklabels.zarr> <supervision_mask.zarr> --slice 14 --ink-thr 128 [--crop X Y W H] [--json out.json]
The crop (X Y W H, level-0 canvas pixels) says where the prediction sits on the label canvas.
"""
import argparse, json, sys
import numpy as np, tifffile, zarr
from sklearn.metrics import roc_auc_score

def read_label_slice(path, z):
    g = zarr.open_group(path, mode="r")
    arr = g["0"] if "0" in g else g[list(g.keys())[0]]
    return arr[z]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pred"); ap.add_argument("labels"); ap.add_argument("mask")
    ap.add_argument("--slice", type=int, required=True)
    ap.add_argument("--ink-thr", type=float, default=128, help="label value > thr = ink (128 for 0/255 labels, 0 for 0/1)")
    ap.add_argument("--crop", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    ap.add_argument("--json")
    a = ap.parse_args()
    pred = tifffile.imread(a.pred)
    if pred.ndim == 3: pred = pred[0]
    lab = read_label_slice(a.labels, a.slice); sup = read_label_slice(a.mask, a.slice)
    if a.crop:
        x, y, w, h = a.crop
        lab = lab[y:y + h, x:x + w]; sup = sup[y:y + h, x:x + w]
    if pred.shape != lab.shape:
        sys.exit(f"shape mismatch pred {pred.shape} vs labels {lab.shape}; pass --crop")
    m = sup > 0
    yt = (lab[m] > a.ink_thr).astype(np.uint8); ys = pred[m].astype(np.float64) / 255.0
    n_ink, n_blank = int(yt.sum()), int((1 - yt).sum())
    out = {"pred": a.pred, "labels": a.labels, "slice": a.slice, "ink_thr": a.ink_thr, "n_supervised": int(m.sum()),
           "n_ink": n_ink, "n_blank": n_blank,
           "mean_on_ink": float(ys[yt == 1].mean()) if n_ink else None,
           "mean_on_blank": float(ys[yt == 0].mean()) if n_blank else None,
           "auc": float(roc_auc_score(yt, ys)) if n_ink and n_blank else None,
           "pred_dtype": str(pred.dtype), "pred_shape": list(pred.shape), "crop": a.crop}
    print(json.dumps(out, indent=1))
    if a.json: json.dump(out, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    main()
