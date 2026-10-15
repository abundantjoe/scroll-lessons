"""Verify UV correspondence between the 1.129 um and 2.4 um tifxyz meshes of 20260623142658-w028-037.

Provenance: Project HERCULES | owner the owner | [id removed]

Reference: published affine transform.json (20260608103018 L0 xyz -> 20260411134726 xyz).
For candidate UV maps (i24, j24) = (a_i * i + b_i, a_j * j + b_j), bilinear-interpolate the 2.4 um
mesh and measure the 3-D distance (2.4 um voxels) to the affine-mapped 1.129 um vertex. Also fits
a_i, b_i, a_j, b_j by least squares on per-vertex refined matches. Numbers only.
Usage: python verify_uv_m2b.py <download_dir> <out_json>
"""
import glob
import json
import sys

import numpy as np
import tifffile

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
dl, out = sys.argv[1], sys.argv[2]
ld = lambda tag: np.stack([tifffile.imread(glob.glob(f"{dl}/*{tag}.tifxyz_{a}.tif")[0]) for a in "xyz"], -1)
A = ld("1.129um")
Bm = ld("2.4um")
tr = json.load(open(glob.glob(f"{dl}/*transform.json")[0]))
M = np.array(tr["transformation_matrix"], dtype=np.float64)
vA = (A != -1).all(-1)
vB = (Bm != -1).all(-1)
hA, wA = vA.shape
hB, wB = vB.shape
rng = np.random.default_rng(20260926)
ii, jj = np.nonzero(vA)
sel = rng.choice(ii.size, 2000, replace=False)
ii, jj = ii[sel], jj[sel]
P = A[ii, jj].astype(np.float64) @ M[:, :3].T + M[:, 3]


def bilin(fi, fj):
    i0 = np.floor(fi).astype(int)
    j0 = np.floor(fj).astype(int)
    ok = (i0 >= 0) & (j0 >= 0) & (i0 + 1 < hB) & (j0 + 1 < wB)
    i0c, j0c = np.clip(i0, 0, hB - 2), np.clip(j0, 0, wB - 2)
    ok &= vB[i0c, j0c] & vB[i0c + 1, j0c] & vB[i0c, j0c + 1] & vB[i0c + 1, j0c + 1]
    di, dj = (fi - i0c)[:, None], (fj - j0c)[:, None]
    Q = (Bm[i0c, j0c] * (1 - di) * (1 - dj) + Bm[i0c + 1, j0c] * di * (1 - dj)
         + Bm[i0c, j0c + 1] * (1 - di) * dj + Bm[i0c + 1, j0c + 1] * di * dj)
    return Q.astype(np.float64), ok


def stats(d):
    return {"n": int(d.size), "median": float(np.median(d)), "p95": float(np.percentile(d, 95)),
            "max": float(d.max())}


res = {"provenance": PROV, "grid_1129": [hA, wA], "grid_24": [hB, wB], "n_sample": int(ii.size),
       "affine_landmark_resid_vx24": None, "candidates": {}}
mv, fx = np.array(tr["moving_landmarks"]), np.array(tr["fixed_landmarks"])
lr = np.linalg.norm(mv @ M[:, :3].T + M[:, 3] - fx, axis=1)
res["affine_landmark_resid_vx24"] = stats(lr)
cands = {
    "shape_ratio": ((hB / hA, 0.0), (wB / wA, 0.0)),
    "shape_ratio_minus1": (((hB - 1) / (hA - 1), 0.0), ((wB - 1) / (wA - 1), 0.0)),
    "voxel_ratio": ((1.129 / 2.4, 0.0), (1.129 / 2.4, 0.0)),
    "shape_ratio_centre": ((hB / hA, 0.5 * hB / hA - 0.5), (wB / wA, 0.5 * wB / wA - 0.5)),
}
best = None
for name, ((ai, bi), (aj, bj)) in cands.items():
    Q, ok = bilin(ii * ai + bi, jj * aj + bj)
    d = np.linalg.norm(Q[ok] - P[ok], axis=1)
    res["candidates"][name] = {"a_i": ai, "b_i": bi, "a_j": aj, "b_j": bj, "valid": int(ok.sum()),
                               "dist_vx24": stats(d)}
    if best is None or np.median(d) < best[1]:
        best = (name, float(np.median(d)))
# refine: per-vertex local Gauss-Newton on (fi, fj) starting from the best candidate, then LSQ fit
(ai, bi), (aj, bj) = cands[best[0]]
fi, fj = ii * ai + bi, jj * aj + bj
for _ in range(8):
    Q, ok = bilin(fi, fj)
    Qi, _ = bilin(fi + 0.01, fj)
    Qj, _ = bilin(fi, fj + 0.01)
    Ji, Jj = (Qi - Q) / 0.01, (Qj - Q) / 0.01
    r = P - Q
    a11, a12, a22 = (Ji * Ji).sum(1), (Ji * Jj).sum(1), (Jj * Jj).sum(1)
    b1, b2 = (Ji * r).sum(1), (Jj * r).sum(1)
    det = a11 * a22 - a12 ** 2
    det[det == 0] = 1
    fi = fi + np.clip((a22 * b1 - a12 * b2) / det, -2, 2)
    fj = fj + np.clip((a11 * b2 - a12 * b1) / det, -2, 2)
Q, ok = bilin(fi, fj)
d = np.linalg.norm(Q - P, axis=1)
good = ok & (d < 5)
fit_i = np.polyfit(ii[good], fi[good], 1)
fit_j = np.polyfit(jj[good], fj[good], 1)
res["refined_per_vertex"] = {"valid": int(ok.sum()), "dist_vx24": stats(d[ok]),
                             "fit_i": {"a": float(fit_i[0]), "b": float(fit_i[1]),
                                       "resid_rms_grid": float(np.sqrt(np.mean((np.polyval(fit_i, ii[good]) - fi[good]) ** 2)))},
                             "fit_j": {"a": float(fit_j[0]), "b": float(fit_j[1]),
                                       "resid_rms_grid": float(np.sqrt(np.mean((np.polyval(fit_j, jj[good]) - fj[good]) ** 2)))}}
Q, ok = bilin(np.polyval(fit_i, ii), np.polyval(fit_j, jj))
res["fitted_linear_uv"] = {"valid": int(ok.sum()), "dist_vx24": stats(np.linalg.norm(Q[ok] - P[ok], axis=1))}
res["best_simple_candidate"] = best[0]
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
