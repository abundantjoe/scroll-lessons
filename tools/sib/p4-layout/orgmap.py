"""DECL-P4-13 P4-M item 3 (organizer-segment mapping) and the item-2 cross-check from organizer meshes.

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only: mesh vertex coordinates (tifxyz, volume voxels). No image or CT voxel.

For a segment mesh (tifxyz) given in the 20260411134726 frame, or in the 7.91 um 20230205180739 frame mapped
through the inverse of the bucket's 20260411134726 transform.json (moving 2.4 um -> fixed 7.91 um affine):
- per strip-a tile (r, c): the minimum 3-D distance from the segment to the tile's mesh vertices, and the number of
  segment vertices within 0.05 / 0.10 mm of the tile (overlap);
- continuation above strip a's top edge: for each segment grid column that overlaps strip a (d <= 0.05 mm), walk
  the segment grid column upward in z from its highest overlapping vertex; the contiguous valid run beyond it,
  with every vertex > 0.05 mm from strip a, is segment sheet beyond strip a's edge. Its along-sheet length and z
  are reported per strip-a column c (assigned by the nearest strip-a vertex of the overlapping start vertex).
Distances use a KD-tree on strip-a vertices at grid stride STRIDE (spacing ~ STRIDE x 48 um); a candidate within
0.2 mm is refined against the full-resolution vertices of its neighbourhood.
Usage:
  python orgmap.py <strip-a meshdir> <seg prefix> <frame: 2.4|7.91> <transform.json> <out.json>
  python orgmap.py xfcheck <seg 7.91 prefix> <seg 2.4 prefix> <transform.json> <out.json>
"""
import json, sys, time
import numpy as np, tifffile
from scipy.spatial import cKDTree

VOX_MM = 0.0024
T = 8343
STRIDE = 2


def load_tifxyz(prefix):
    P = np.stack([tifffile.imread(f"{prefix}_{a}.tif").astype(np.float64) for a in "xyz"], -1)
    valid = (P != -1).all(-1) & np.isfinite(P).all(-1) & (P != 0).any(-1)
    return P, valid


def affine(tj):
    M = np.array(json.load(open(tj))["transformation_matrix"], np.float64)
    A = np.eye(4)
    A[:3] = M
    return A


def apply(A, X):
    return X @ A[:3, :3].T + A[:3, 3]


def xfcheck(p791, p24, tj, out):
    A = affine(tj)
    Ai = np.linalg.inv(A)
    P7, v7 = load_tifxyz(p791)
    P2, v2 = load_tifxyz(p24)
    X7 = P7[v7]
    X2 = P2[v2]
    tree = cKDTree(X2)
    res = {}
    for name, B in (("inverse(A): 7.91 -> 2.4", Ai), ("A: 7.91 -> 2.4 (wrong direction test)", A)):
        Y = apply(B, X7)
        d, _ = tree.query(Y[:: max(1, len(Y) // 200000)])
        res[name] = {"n": int(len(d)), "dist_um_p10_p50_p90_p99": (np.percentile(d, [10, 50, 90, 99]) * 2.4).round(1).tolist()}
    # reference: resampling spacing of X2 subsample (self nn distance)
    dd, _ = cKDTree(X2).query(X2[::50], k=2)
    res["reference_2.4mesh_subsample_nn_um_p50"] = float(np.median(dd[:, 1]) * 2.4)
    res["provenance"] = "Project HERCULES | owner the owner | [id removed]"
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


def main(md, prefix, frame, tj, out):
    t0 = time.time()
    SA, va = load_tifxyz(f"{md}/mesh")
    gh, gw = va.shape
    ii, jj = np.nonzero(va)
    tr = (ii * 20) // T
    tc = (jj * 20) // T
    sel = (ii % STRIDE == 0) & (jj % STRIDE == 0)
    tree = cKDTree(SA[ii[sel], jj[sel]])
    idx_sel = np.nonzero(sel)[0]
    first = np.where(va.any(0), va.argmax(0), -1)
    P, v = load_tifxyz(prefix)
    if frame == "7.91":
        Ai = np.linalg.inv(affine(tj))
        P = np.where(v[..., None], apply(Ai, P.reshape(-1, 3)).reshape(P.shape), -1)
    si, sj = np.nonzero(v)
    X = P[si, sj]
    d, k = tree.query(X, distance_upper_bound=5 / VOX_MM)
    near = np.isfinite(d)
    kk = np.where(near, k, 0)
    hit = idx_sel[kk]
    # refine candidates within 0.2 mm against full-res neighbours (+-STRIDE grid)
    cand = np.nonzero(d * VOX_MM <= 0.2)[0]
    dref = d.copy()
    for a in range(-STRIDE, STRIDE + 1):
        for b in range(-STRIDE, STRIDE + 1):
            gi = np.clip(ii[hit[cand]] + a, 0, gh - 1)
            gj = np.clip(jj[hit[cand]] + b, 0, gw - 1)
            ok = va[gi, gj]
            dd = np.linalg.norm(SA[gi, gj] - X[cand], axis=1)
            dref[cand] = np.where(ok & (dd < dref[cand]), dd, dref[cand])
    dmm = dref * VOX_MM
    R, Cc = (np.array(tr[hit]), np.array(tc[hit]))
    tiles = {}
    for r in range(-(-gh * 20 // T)):
        for c in range(-(-gw * 20 // T)):
            m = near & (R == r) & (Cc == c)
            if m.any():
                tiles[f"r{r}_c{c}"] = {"min_mm": round(float(dmm[m].min()), 4), "n_le_0p05mm": int((dmm[m] <= 0.05).sum()),
                                       "n_le_0p10mm": int((dmm[m] <= 0.10).sum())}
    # per tile (from the strip side): min distance of the tile's vertices to the segment (all tiles, incl. far)
    stree = cKDTree(X[:: max(1, len(X) // 1500000)])
    tile_min = {}
    for r in range(-(-gh * 20 // T)):
        for c in range(-(-gw * 20 // T)):
            m = sel & (tr == r) & (tc == c)
            if m.any():
                dq, _ = stree.query(SA[ii[m], jj[m]][::4])
                tile_min[f"r{r}_c{c}"] = round(float(dq.min() * VOX_MM), 3)
    # continuation above strip a's edge along the segment grid
    ov = np.zeros(v.shape, bool)
    ov[si, sj] = dmm <= 0.05
    D = np.full(v.shape, np.inf)
    D[si, sj] = dmm
    cont = []
    z = P[..., 2]
    for j in np.nonzero(ov.any(0))[0]:
        rows = np.nonzero(ov[:, j])[0]
        # the segment's z direction along its grid column: pick the overlapping vertex of highest z
        r0 = rows[np.argmax(z[rows, j])]
        # direction of increasing z along the column
        step = 1 if (r0 + 1 < v.shape[0] and v[r0 + 1, j] and z[r0 + 1, j] > z[r0, j]) else -1
        r = r0
        L = 0.0
        while 0 <= r + step < v.shape[0] and v[r + step, j] and D[r + step, j] > 0.05 and z[r + step, j] >= z[r, j] - 1:
            L += np.linalg.norm(P[r + step, j] - P[r, j]) * VOX_MM
            r += step
        # strip-a column of the start vertex
        q = np.nonzero((si == r0) & (sj == j))[0][0]
        cont.append((int(tc[hit[q]]), int(tr[hit[q]]), float(z[r0, j] * VOX_MM), float(z[r, j] * VOX_MM), L,
                     int(ii[hit[q]] - first[jj[hit[q]]])))
    cont = np.array(cont) if cont else np.zeros((0, 6))
    per_c = {}
    for c in sorted(set(cont[:, 0].astype(int).tolist())):
        m = cont[:, 0] == c
        top = m & (cont[:, 5] <= 10)  # start vertex within 10 grid rows (0.5 mm) of strip a's top edge
        per_c[f"c{c}"] = {"n_seg_cols_overlapping": int(m.sum()), "n_starting_at_strip_top_edge": int(top.sum()),
                          "beyond_len_mm_p50_p90_max_at_edge": np.percentile(cont[top, 4], [50, 90, 100]).round(2).tolist() if top.any() else None,
                          "z_top_mm_p50_max_at_edge": [round(float(np.median(cont[top, 3])), 2), round(float(cont[top, 3].max()), 2)] if top.any() else None,
                          "start_z_mm_p50": round(float(np.median(cont[m, 2])), 2)}
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]", "segment_mesh": prefix.split("/")[-1],
           "frame": frame, "n_vertices": int(len(X)), "stride": STRIDE,
           "overlap_tiles": tiles, "tile_min_mm_from_strip_side": tile_min, "continuation_above_strip_edge": per_c,
           "seg_z_mm_max": float(X[:, 2].max() * VOX_MM), "seconds": round(time.time() - t0, 1)}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("segment_mesh", "n_vertices", "seg_z_mm_max")}))
    print("overlap tiles (<=0.05 mm):", sorted([k for k, x in tiles.items() if x["n_le_0p05mm"] > 0]))
    print(json.dumps(per_c, indent=0))


if __name__ == "__main__":
    if sys.argv[1] == "xfcheck":
        xfcheck(*sys.argv[2:])
    else:
        main(*sys.argv[1:])
