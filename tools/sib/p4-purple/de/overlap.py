"""p4-purple-de A2: per-tile overlap of the 137 keV 2.4 um extent with the w010-027 (geometry only) and w028-037 (control)
meshes, plus sampled non-zero fractions on the control only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python overlap.py <scratch>
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

scr = sys.argv[1]
os.makedirs(scr, exist_ok=True)
M = D.ref_to_137()
fence = D.fence(scr)
out = {"provenance": D.PROV, "serves": "brief_de.md item 2; PROTOCOL.md A2",
       "composed_affine_ref_to_137_xyz": M.tolist(), "fence": {"rule": "PROTOCOL amendment A-1", "D_f_vox": D.D_F, "n_F": fence["n_F"], "sha256_F_float64": fence["sha256_F_float64"]}}


def per_tile(seg, T, nr, nc):
    xyz, inputs = D.load_mesh(seg, scr)
    H, W = xyz.shape[:2]
    tot = np.zeros((nr, nc), np.int64)
    ext = np.zeros((nr, nc), np.int64)
    cyl = np.zeros((nr, nc), np.int64)
    inside_idx = {}
    for i0 in range(0, H, 128):
        blk = np.asarray(xyz[i0:i0 + 128])
        gi, gj = np.nonzero(np.isfinite(blk[..., 0]))
        P = blk[gi, gj]
        Q = D.map_pts(M, P)
        e = D.inside_extent(Q)
        cy = e & D.inside_cyl(Q)
        gi = gi + i0
        r, c = gi * 20 // T, gj * 20 // T
        np.add.at(tot, (r, c), 1)
        np.add.at(ext, (r, c), e)
        np.add.at(cyl, (r, c), cy)
        for k in np.nonzero(e)[0]:
            inside_idx.setdefault((int(r[k]), int(c[k])), []).append((int(gi[k]), int(gj[k])))
    tiles = {}
    for i in range(nr):
        for j in range(nc):
            if tot[i, j]:
                tiles[f"r{i}_c{j}"] = {"valid_vertices": int(tot[i, j]), "frac_inside_extent": ext[i, j] / tot[i, j],
                                       "frac_inside_cylinder": cyl[i, j] / tot[i, j]}
    return xyz, inputs, tiles, inside_idx, int(tot.sum()), int(ext.sum()), int(cyl.sum())


# ---- w010-027: geometry only, no 137 keV byte
g = D.git_json("logs/sib/pairs0814b/e2/grid.json", "origin/claude/gifted-bell-gavnl5-sib-pairs0814b")
T = g["T_canvas_px"]
xyz, inputs, tiles, _, n, ne, ncy = per_tile(D.SEG_E2, T, g["tile_grid"]["n_rows"], g["tile_grid"]["n_cols"])
del xyz
hz = D.git_json("logs/sib/p4-highz/kedge_coverage_e2.json", D.SCANS_REF)["tiles_with_any_coverage"]
cmp = {k: {"this": tiles[k]["frac_inside_extent"], "p4_highz": hz.get(k),
           "abs_diff": abs(tiles[k]["frac_inside_extent"] - hz.get(k, 0.0))}
       for k in tiles if tiles[k]["frac_inside_extent"] > 0 or k in hz}
out["w010_027_geometry_only"] = {
    "segment": D.SEG_E2, "grid": "logs/sib/pairs0814b/e2/grid.json (T %d), tile = (gi*20//T, gj*20//T)" % T,
    "mesh_inputs": inputs, "valid_vertices": n, "frac_inside_extent": ne / n, "frac_inside_cylinder": ncy / n,
    "tiles_with_coverage": {k: v for k, v in tiles.items() if v["frac_inside_extent"] > 0},
    "comparison_with_p4_highz": cmp,
    "max_abs_diff_vs_p4_highz": max(v["abs_diff"] for v in cmp.values()) if cmp else None,
    "note": "no 137 keV chunk or byte was fetched for this strip (HARD FENCE)"}
json.dump(out, open(os.path.join(D.REPO, "logs/sib/p4-purple/de/overlap.json"), "w"), indent=1)
print("E2", ne / n, ncy / n, out["w010_027_geometry_only"]["max_abs_diff_vs_p4_highz"], flush=True)

# ---- w028-037 control
g = D.git_json("logs/sib/p4-tiles-b/grid.json", "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b")
T = g["T_px"]
nr, nc = g["tile_grid_rows_cols"]
xyz, inputs, tiles, inside_idx, n, ne, ncy = per_tile(D.SEG_C2, T, nr, nc)
refused = 0
allin = np.array([ij for lst in inside_idx.values() for ij in lst])
Qall = D.map_pts(M, np.asarray(xyz[allin[:, 0], allin[:, 1]], np.float64))
dist, _ = fence["tree"].query(Qall, distance_upper_bound=5000)
dist_stats = {"n": len(dist), "p1": float(np.percentile(dist, 1)), "p5": float(np.percentile(dist, 5)),
              "p50": float(np.percentile(dist, 50)), "frac_ge_Df": float((dist >= D.D_F).mean()),
              "frac_ge_Df_plus_block_halfdiag_111": float((dist >= D.D_F + 111).mean()),
              "frac_ge_Df_plus_block_halfdiag_222": float((dist >= D.D_F + 222).mean()),
              "note": "distance in 137 keV voxels from control vertices inside the extent to the nearest fenced w010-027 vertex; "
                      "blocks of 128^3 have half-diagonal 111 voxels (centre to corner = 64*sqrt(3))"}
print(dist_stats, flush=True)


def sample_one(ij):
    global refused
    P = np.asarray(xyz[ij[0], ij[1]], np.float64)
    Q = D.map_pts(M, P[None])[0]
    qi = np.rint(Q).astype(int)
    pi = np.rint(P).astype(int)
    try:
        b137 = D.read_byte_137(int(qi[0]), int(qi[1]), int(qi[2]), scr)
    except D.FenceError:
        refused += 1
        return None
    b78 = D.read_byte_78(int(pi[0]), int(pi[1]), int(pi[2]))
    return (b137, b78)


t0 = time.time()
with ThreadPoolExecutor(32) as ex:
    for key, lst in sorted(inside_idx.items()):
        r, c = key
        rng = np.random.default_rng(20260926 + 1000 * r + c)
        sel = rng.choice(len(lst), min(1000, len(lst)), replace=False)
        res = [x for x in ex.map(sample_one, [lst[k] for k in sel]) if x is not None and x[0] is not None and x[1] is not None]
        a = np.array(res, float).reshape(-1, 2)
        t = tiles[f"r{r}_c{c}"]
        t.update({"n_sampled": len(a), "frac_nonzero_137": float((a[:, 0] > 0).mean()) if len(a) else None,
                  "frac_nonzero_78": float((a[:, 1] > 0).mean()) if len(a) else None,
                  "frac_nonzero_both": float(((a[:, 0] > 0) & (a[:, 1] > 0)).mean()) if len(a) else None,
                  "n_inside_extent": len(lst)})
        print(key, t, round(time.time() - t0), flush=True)
out["w028_037_control"] = {
    "segment": D.SEG_C2, "grid": "logs/sib/p4-tiles-b/grid.json (T %d, %dx%d), tile = (gi*20//T, gj*20//T)" % (T, nr, nc),
    "mesh_inputs": inputs, "valid_vertices": n, "frac_inside_extent": ne / n, "frac_inside_cylinder": ncy / n,
    "n_vertices_inside_extent": ne, "fence_refused_samples": refused, "distance_to_fence": dist_stats,
    "tiles_with_coverage": {k: v for k, v in tiles.items() if v["frac_inside_extent"] > 0},
    "sampling": "min(1000, n_inside) inside vertices per tile, rng 20260926+1000r+c; single-byte level-0 reads at round(Q) (137) "
                "and round(P) (78)"}
out["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(out, open(os.path.join(D.REPO, "logs/sib/p4-purple/de/overlap.json"), "w"), indent=1)
print("C2", ne / n, ncy / n, refused)
