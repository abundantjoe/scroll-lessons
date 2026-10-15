"""Supplement for M2b manifest: per-tile fraction of saved mesh points outside the 20260608103018 L0
extent (zyx 59969 x 36006 x 32354, recon.json), and its correlation with frac_zero_valid.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python coverage_m2b.py <m2b_out_dir>
"""
import json
import os
import sys

import numpy as np

SHAPE_ZYX = (59969, 36006, 32354)
out = sys.argv[1]
man = json.load(open(os.path.join(out, "manifest.json")))
z = np.load(os.path.join(out, "tile_points.npz"))
xs, ys = [], []
for t in man["tiles"]:
    P = z[f"r{t['r']}_c{t['c']}"]
    o = float(((P[:, 0] < 0) | (P[:, 0] >= SHAPE_ZYX[2]) | (P[:, 1] < 0) | (P[:, 1] >= SHAPE_ZYX[1])
               | (P[:, 2] < 0) | (P[:, 2] >= SHAPE_ZYX[0])).mean())
    t["stats"]["frac_mesh_points_outside_1129_volume"] = o
    xs.append(o)
    ys.append(t["stats"]["frac_zero_valid"])
xs, ys = np.array(xs), np.array(ys)
man["zero_prediction_summary"]["coverage_check"] = {
    "volume_L0_shape_zyx": SHAPE_ZYX,
    "pearson_r_outside_vs_zero": float(np.corrcoef(xs, ys)[0, 1]),
    "mean_abs_diff": float(np.abs(xs - ys).mean()), "max_abs_diff": float(np.abs(xs - ys).max()),
    "reading": "zero-valued mesh-valid prediction px track mesh vertices outside the 1.129 um volume "
               "extent: the prediction there has no CT input, it is not a no-ink measurement",
}
json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
print(json.dumps(man["zero_prediction_summary"]["coverage_check"]))
