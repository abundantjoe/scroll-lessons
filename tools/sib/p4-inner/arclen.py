"""DECL-P4-25 item 3 locator geometry, numbers only: per tile, traced surface position (cm) along the spiral
[line withheld: prize-candidate detail under review]
- Outward is DECREASING column on every strip (same-angle crossing check, direction.json); column 0 = outer end.
- Within a strip, s(row, col) = cumulative 3-D length along the grid row from the row's first valid column (gaps
  bridged by the straight 3-D chord). A tile's position = median of s over its grid rows at the tile's centre
  column, plus the summed median full-row lengths of all strips outward of it.
- Seam check: 3-D distance from each strip's inner-end column (last valid col per row) to the nearest vertex of
  the next strip's outer-end column (first valid col); median and p90 in mm. Continuity assumption holds only if
  the seam gap is small relative to the ~0.25 mm winding pitch.
Provenance: Project HERCULES | owner the owner | [id removed]
usage: arclen.py <out.json> <tag=dl_dir=manifest_dir> ...   (outermost first)
"""
import glob, json, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree
VOX_MM = 0.0024
out = sys.argv[1]; specs = [a.split("=") for a in sys.argv[2:]]
res = {"provenance": "Project HERCULES | owner the owner | [id removed]", "method": __doc__.split("Provenance")[0].strip(), "strips": {}, "seams": []}
offset_mm = 0.0; prev_inner = None; prev_tag = None
for tag, dl, mdir in specs:
    G = np.stack([tifffile.imread(glob.glob(f"{dl}/*{tag}*tifxyz_{c}.tif")[0]).astype(np.float64) for c in "xyz"], -1)
    valid = ~(G == -1).any(-1) & np.isfinite(G).all(-1)
    gh, gw, _ = G.shape
    S = np.full((gh, gw), np.nan); rowlen = []
    outer_pts, inner_pts = [], []
    for i in range(gh):
        idx = np.where(valid[i])[0]
        if len(idx) < 2: continue
        seg = np.linalg.norm(np.diff(G[i, idx], axis=0), axis=1) * VOX_MM
        s = np.r_[0, np.cumsum(seg)]
        S[i, idx] = s; rowlen.append(s[-1])
        outer_pts.append(G[i, idx[0]]); inner_pts.append(G[i, idx[-1]])
    Lmm = float(np.median(rowlen))
    if prev_inner is not None:
        d, _ = cKDTree(np.array(outer_pts)).query(prev_inner)
        res["seams"].append({"from_inner_end_of": prev_tag, "to_outer_end_of": tag, "gap_mm_median": round(float(np.median(d)) * VOX_MM, 3),
                             "gap_mm_p90": round(float(np.percentile(d, 90)) * VOX_MM, 3)})
    m = json.load(open(f"{mdir}/manifest.json")); tiles = {}
    for t in m["tiles"]:
        g0, g1 = t["grid_rows"]; c0, c1 = t["grid_cols"]; cc = (c0 + c1) // 2
        col = S[g0:g1, cc]
        if np.isfinite(col).sum() == 0:
            col = np.nanmedian(S[g0:g1, c0:c1], axis=1)
        s_mm = float(np.nanmedian(col))
[line withheld: prize-candidate detail under review]
                                         "s_cm_tile_outer_edge": round((offset_mm + float(np.nanmedian(np.nanmin(S[g0:g1, c0:c1], axis=1)))) / 10, 2)}
    res["strips"][tag] = {"segment": m["segment"], "grid_shape": [gh, gw], "median_row_length_cm": round(Lmm / 10, 2), "row_length_cm_p10_p90": [round(float(np.percentile(rowlen, q)) / 10, 2) for q in (10, 90)],
                          "offset_from_outer_end_cm": round(offset_mm / 10, 2), "tiles": tiles}
    offset_mm += Lmm; prev_inner = np.array(inner_pts); prev_tag = tag
    print(tag, "L_cm", round(Lmm / 10, 1), "offset_cm", round((offset_mm - Lmm) / 10, 1), res["seams"][-1] if res["seams"] else "")
json.dump(res, open(out, "w"), indent=1)
