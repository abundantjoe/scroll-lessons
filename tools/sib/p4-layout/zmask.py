"""Item 2 context: in-mask (nonzero) fraction and mean CT value per z of the level-4 volume (38.4 um) over the
xy footprint of strip a's top edge (numbers only). Answers: where does the masked scroll end in z?
Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python zmask.py <meshdir> <out.json> <manifest.jsonl>
"""
import json, sys
import numpy as np, tifffile
sys.path.insert(0, __import__("os").path.dirname(__file__))
from zarrfetch import Vol

L = 4
F = 2 ** L
VOX_MM = 0.0024


def main(md, out, man):
    P = np.stack([tifffile.imread(f"{md}/mesh_{a}.tif").astype(np.float32) for a in "xyz"], -1)
    valid = (P != -1).all(-1)
    top = P[valid][P[valid][:, 2] > 170 / VOX_MM]  # vertices within 2.9 mm of the edge
    xy = top[:, :2] / F
    x0, y0 = np.floor(xy.min(0)).astype(int) - 8
    x1, y1 = np.ceil(xy.max(0)).astype(int) + 8
    v = Vol(L, man, threads=32)
    z0, z1 = int(150 / VOX_MM / F), v.shape[0]
    keys = [(z, y, x) for z in range(z0 // 128, (z1 - 1) // 128 + 1) for y in range(y0 // 128, y1 // 128 + 1)
            for x in range(x0 // 128, x1 // 128 + 1)]
    v.prefetch(keys)
    # xy mask of the edge footprint: L4 pixels within 3 px (115 um) of any top-edge vertex
    H, W = y1 - y0, x1 - x0
    fp = np.zeros((H, W), bool)
    pi = np.rint(xy).astype(int) - [x0, y0]
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            fp[np.clip(pi[:, 1] + dy, 0, H - 1), np.clip(pi[:, 0] + dx, 0, W - 1)] = True
    yy, xx = np.nonzero(fp)
    rows = []
    for z in range(z0, z1, 2):
        pts = np.c_[np.full(len(yy), z), yy + y0, xx + x0]
        s = v.sample(pts)
        # whole-box nonzero fraction (all xy in the box)
        rows.append({"z_L4": z, "z_mm": round((z + 0.5) * F * VOX_MM, 3), "footprint_nonzero_frac": float((s > 0).mean()),
                     "footprint_mean": float(s.mean()), "footprint_p90": float(np.percentile(s, 90))})
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]", "level": L,
           "voxel_mm": F * VOX_MM, "box_xy_L4": [int(x0), int(y0), int(x1), int(y1)],
           "footprint": "L4 xy px within 3 px of any strip-a mesh vertex with z > 170 mm (the top-edge band), sampled at every z",
           "n_footprint_px": int(fp.sum()), "chunks_fetched": v.n_get, "chunks_404": v.n_404, "rows": rows}
    json.dump(res, open(out, "w"), indent=1)
    for r in rows[::6]:
        print(r)


if __name__ == "__main__":
    main(*sys.argv[1:])
