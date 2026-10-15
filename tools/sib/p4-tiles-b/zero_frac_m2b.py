"""Supplement for M2b manifest: per-tile fraction of mesh-valid canvas px whose raw prediction is 0
(numbers only; no pixel printed). Also groups tiles with identical PNG sha256.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python zero_frac_m2b.py <download_dir> <m2b_out_dir>
"""
import collections
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import tile_m2b as tm  # noqa: E402


def zf(rec):
    G = tm.G
    T, s = G["T"], G["s"]
    y0, y1 = rec["in_canvas_rows"]
    x0, x1 = rec["in_canvas_cols"]
    a = tm.read_region(y0, y1, x0, x1)
    m = G["valid"][np.ix_((np.arange(y0, y1) // s).astype(np.int64), (np.arange(x0, x1) // s).astype(np.int64))]
    return rec["r"], rec["c"], float((a[m] == 0).mean()), int(m.sum())


def main():
    dl, out = sys.argv[1], sys.argv[2]
    man = json.load(open(os.path.join(out, "manifest.json")))
    g = json.load(open(os.path.join(out, "grid.json")))
    import tifffile
    x = tifffile.imread(tm.find(dl, "*1.129um.tifxyz_x.tif"))
    valid = x != -1
    del x
    pred = tm.find(dl, "*tile256-stride128.tif")
    with Pool(4, initializer=tm._init, initargs=(pred, valid, g["canvas_per_grid_scale_rows_cols"][0], g["T_px"])) as p:
        res = {(r, c): (f, n) for r, c, f, n in p.map(zf, man["tiles"])}
    groups = collections.defaultdict(list)
    for t in man["tiles"]:
        f, n = res[(t["r"], t["c"])]
        assert n == t["valid_px"], (t["r"], t["c"], n, t["valid_px"])
        t["stats"]["frac_zero_valid"] = f
        groups[t["png_sha256"]].append(f"r{t['r']}_c{t['c']}")
    dup = {k: v for k, v in groups.items() if len(v) > 1}
    zf_ = [t["stats"]["frac_zero_valid"] for t in man["tiles"]]
    man["zero_prediction_summary"] = {
        "note": "frac_zero_valid = fraction of mesh-valid px whose raw prediction value is 0 (valid mask from x.tif != -1, "
                "identical to all-three -1 since they agree)",
        "tiles_all_zero_valid": sum(f == 1.0 for f in zf_),
        "tiles_frac_zero_ge_0.5": sum(f >= 0.5 for f in zf_),
        "tiles_frac_zero_ge_0.05": sum(f >= 0.05 for f in zf_),
        "duplicate_png_groups": dup,
    }
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(json.dumps(man["zero_prediction_summary"]))
    print(sorted((round(f, 4), f"r{t['r']}_c{t['c']}") for f, t in zip(zf_, man["tiles"]) if f >= 0.05))


if __name__ == "__main__":
    main()
