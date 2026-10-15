"""DECL-P4-4-A1 item 1 scan-coverage numbers for P4-D M2a (20260623141924-w010-027).

Provenance: Project HERCULES | owner the owner | [id removed]

Geometry only: uses mesh points and the 1.129 um volume's L0 shape; never reads prediction values.
A point (x, y, z) in 20260608103018 voxels is outside the volume unless
0 <= x < X, 0 <= y < Y and 0 <= z < Z, where (Z, Y, X) is the level-0 .zarray shape.

Per read-eligible tile (>= 50 % mesh-valid) it records:
- frac_mesh_points_outside_1129_volume: over the tile's saved points (tile_points.npz key r<r>_c<c>);
  this is the A1 rule input;
- frac_all_valid_vertices_outside_1129_volume: over every valid native vertex in the tile (check);
- read_eligible_A1: valid_fraction >= 0.5 and frac_mesh_points_outside_1129_volume < 0.5.
It also compares with p4-tiles-b E1 (same grid) where that manifest is given.

Usage: python m2a_coverage.py <x.tif> <y.tif> <z.tif> <.zarray> <m2a_dir> [tiles_b_e1_manifest.json]
"""
import json
import sys

import numpy as np
import tifffile

PROV = "Project HERCULES | owner the owner | [id removed]"


def outside(p, shape_zyx):
    Z, Y, X = shape_zyx
    ins = (p[:, 0] >= 0) & (p[:, 0] < X) & (p[:, 1] >= 0) & (p[:, 1] < Y) & (p[:, 2] >= 0) & (p[:, 2] < Z)
    return ~ins


def main():
    xf, yf, zf, zarray, d = sys.argv[1:6]
    tb = sys.argv[6] if len(sys.argv) > 6 else None
    shape = json.load(open(zarray))["shape"]
    P = np.stack([tifffile.imread(f).astype(np.float32) for f in (xf, yf, zf)], -1)
    V = ~(P == -1).any(-1) & np.isfinite(P).all(-1)
    pts = np.load(d + "/tile_points.npz")
    recs = [json.loads(l) for l in open(d + "/tile_census.jsonl")]
    tbm = {}
    if tb:
        m = json.load(open(tb))
        for t in m["tiles"]:
            tbm[(t["r"], t["c"])] = {"frac_outside": t.get("frac_outside"), "eligible": True}
        for t in m.get("ineligible_ge50_valid_but_outside", []):
            if isinstance(t, str):
                rr, cc = (int(s[1:]) for s in t.split("_"))
                tbm[(rr, cc)] = {"frac_outside": None, "eligible": False}
            elif isinstance(t, dict):
                tbm[(t["r"], t["c"])] = {"frac_outside": t.get("frac_outside", t.get("frac_mesh_points_outside_1129_volume")), "eligible": False}
    out = []
    for r in recs:
        if not r["eligible"]:
            continue
        key = "r%d_c%d" % (r["r"], r["c"])
        fs = float(outside(pts[key], shape).mean())
        gy0, gy1 = r["grid_rows"]
        gx0, gx1 = r["grid_cols"]
        allp = P[gy0:gy1, gx0:gx1][V[gy0:gy1, gx0:gx1]]
        fa = float(outside(allp, shape).mean())
        e = {"r": r["r"], "c": r["c"], "valid_fraction": r["valid_fraction"],
             "frac_mesh_points_outside_1129_volume": fs,
             "frac_all_valid_vertices_outside_1129_volume": fa,
             "n_all_valid_vertices": int(allp.shape[0]),
             "read_eligible_A1": bool(r["valid_fraction"] >= 0.5 and fs < 0.5),
             "decision_same_on_all_vertices": bool((fs < 0.5) == (fa < 0.5))}
        if (r["r"], r["c"]) in tbm:
            e["tiles_b_e1"] = tbm[(r["r"], r["c"])]
        out.append(e)
    with open(d + "/coverage_A1.jsonl", "w") as f:
        for e in out:
            f.write(json.dumps(e) + "\n")
    summ = {"provenance": PROV, "rule": "DECL-P4-4-A1 item 1", "volume_L0_shape_zyx": shape,
            "n_ge50_valid": len(out), "n_read_eligible_A1": sum(e["read_eligible_A1"] for e in out),
            "n_excluded_by_coverage": sum(not e["read_eligible_A1"] for e in out),
            "n_decision_differs_all_vertices": sum(not e["decision_same_on_all_vertices"] for e in out),
            "max_abs_diff_saved_vs_all": max(abs(e["frac_mesh_points_outside_1129_volume"] - e["frac_all_valid_vertices_outside_1129_volume"]) for e in out)}
    if tbm:
        both = [e for e in out if "tiles_b_e1" in e]
        summ["tiles_b_compared"] = len(both)
        summ["tiles_b_eligibility_disagreements"] = [[e["r"], e["c"]] for e in both if e["tiles_b_e1"]["eligible"] != e["read_eligible_A1"]]
        summ["tiles_b_tiles_eligible_here_missing_there"] = [[e["r"], e["c"]] for e in out if e["read_eligible_A1"] and "tiles_b_e1" not in e]
        diffs = [abs(e["tiles_b_e1"]["frac_outside"] - e["frac_mesh_points_outside_1129_volume"]) for e in both if e["tiles_b_e1"]["frac_outside"] is not None]
        summ["tiles_b_max_abs_frac_diff"] = max(diffs) if diffs else None
    print(json.dumps(summ))
    json.dump(summ, open(d + "/coverage_A1_summary.json", "w"), indent=1)


if __name__ == "__main__":
    main()
