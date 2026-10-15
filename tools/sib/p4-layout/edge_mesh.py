"""DECL-P4-13 P4-M item 2, part a: mesh-only top-edge numbers for strip a (20260701183124-w010-027).

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only: reads the official tifxyz x/y/z grids (volume voxels, 2.4 um). No image or CT voxel.
Grid/tile rules are p4-tiles-a's (grid.json): canvas = 20 x grid, T = 8343 canvas px, tile (r,c) spans
grid rows [ceil(r*T/20), ceil((r+1)*T/20)) and cols likewise.
Usage: python edge_mesh.py <dir with mesh_x.tif mesh_y.tif mesh_z.tif> <out.json>
"""
import json, sys
import numpy as np, tifffile

VOX_MM = 0.0024
T = 8343
S = 20  # canvas px per grid step


def load(d):
    P = np.stack([tifffile.imread(f"{d}/mesh_{a}.tif").astype(np.float32) for a in "xyz"], -1)
    valid = (P != -1).all(-1) & np.isfinite(P).all(-1)
    return P, valid


def main(d, out):
    P, valid = load(d)
    gh, gw = valid.shape
    zmm = P[..., 2] * VOX_MM
    nr, nc = -(-gh * S // T), -(-gw * S // T)
    rb = lambda r: (-(-r * T // S), min(-(-(r + 1) * T // S), gh))
    cb = lambda c: (-(-c * T // S), min(-(-(c + 1) * T // S), gw))
    tiles = []
    for r in range(nr):
        for c in range(nc):
            (a, b), (e, f) = rb(r), cb(c)
            v = valid[a:b, e:f]
            z = zmm[a:b, e:f][v]
            tiles.append({"r": r, "c": c, "n_grid": int(v.size), "valid_fraction": float(v.mean()) if v.size else 0.0,
                          "n_valid": int(v.sum()),
                          "n_valid_z_gt_160mm": int((z > 160).sum()),
                          "frac_of_cells_valid_and_z_gt_160mm": float((z > 160).sum() / v.size) if v.size else 0.0,
                          "z_mm_min_med_max": [float(z.min()), float(np.median(z)), float(z.max())] if z.size else None})
    # per grid column: first valid grid row from the canvas top (row 0 = high z), its z, and z max of the column
    cols = []
    first = np.where(valid.any(0), valid.argmax(0), -1)
    zmax_col = np.where(valid, zmm, -np.inf).max(0)
    for c in range(nc):
        e, f = cb(c)
        fr = first[e:f]
        ok = fr >= 0
        zt = np.array([zmm[fr[k], e + k] for k in range(f - e) if ok[k]])
        zm = zmax_col[e:f][ok]
        # is the top-edge vertex the column's highest-z vertex? (row 0 = high z check)
        cols.append({"c": c, "grid_cols": [e, f], "n_cols_with_valid": int(ok.sum()),
                     "first_valid_row_min_med_max": [int(fr[ok].min()), float(np.median(fr[ok])), int(fr[ok].max())] if ok.any() else None,
                     "edge_z_mm_p5_med_p95": [float(np.percentile(zt, 5)), float(np.median(zt)), float(np.percentile(zt, 95))] if ok.any() else None,
                     "col_zmax_mm_p5_med_p95": [float(np.percentile(zm, 5)), float(np.median(zm)), float(np.percentile(zm, 95))] if ok.any() else None,
                     "frac_cols_edge_z_ge_172p5mm": float((zt >= 172.5).mean()) if ok.any() else None,
                     "frac_cols_zmax_ge_172p5mm": float((zm >= 172.5).mean()) if ok.any() else None})
    allz = zmm[valid]
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "segment": "20260701183124-w010-027", "grid_shape": [gh, gw], "tile_grid": [nr, nc],
           "mesh_z_mm_min_max": [float(allz.min()), float(allz.max())],
           "mesh_z_vox_max": float(P[..., 2][valid].max()),
           "note_fit_zrange": "20260701 spiral-fit source tag fitted_m7_ds2_z3000_18000 -> z 28.8-172.8 mm (recon.md critic additions)",
           "volume_L0_z_extent_mm": 75784 * VOX_MM,
           "tiles": tiles, "columns": cols}
    json.dump(res, open(out, "w"), indent=1)
    for t in tiles:
        if t["r"] <= 1 and 5 <= t["c"] <= 19:
            print(t["r"], t["c"], "vf %.3f" % t["valid_fraction"], "z>160: %d" % t["n_valid_z_gt_160mm"], t["z_mm_min_med_max"] and ["%.1f" % x for x in t["z_mm_min_med_max"]])
    for c in cols:
        print("c%d" % c["c"], c["first_valid_row_min_med_max"], c["edge_z_mm_p5_med_p95"] and ["%.2f" % x for x in c["edge_z_mm_p5_med_p95"]],
              c["col_zmax_mm_p5_med_p95"] and ["%.2f" % x for x in c["col_zmax_mm_p5_med_p95"]], c["frac_cols_edge_z_ge_172p5mm"])
    print("mesh z", res["mesh_z_mm_min_max"])


if __name__ == "__main__":
    main(*sys.argv[1:])
