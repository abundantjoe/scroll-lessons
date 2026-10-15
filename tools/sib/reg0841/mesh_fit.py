# Provenance: Project HERCULES | owner the owner | [id removed]
"""Step 1-2: flip/remount test and coarse affine from the organizer meshes that exist in
both frames (<id>-on-20250821151531-9.366um and <id>-on-20260319124803-2.403um).

Correspondence: the two tifxyz grids of one segment share the UV parametrisation up to
the resolution ratio (B0841-BANK: N2/N9 within 0.07 % of F). For every valid 9 um grid node
(v9, u9) the 2.4 um grid position is g2 = (g9*20 + o) * N2/N9 / 20 - o/20 per axis, with the
canvas-pixel offset o scanned (B0841-BANK used o = 10); the 2.4 um mesh is bilinearly
interpolated there. A 3-D affine x2 = A x9 + c is fitted by least squares, then robustly
(3 x MAD trimming). Numbers only.
"""
import json, sys, hashlib
import numpy as np, tifffile

ROOT = "/work/reg/mesh"
SEGS = ["20260220213127-w00", "20260220214732-auto_grown_20260220144552896",
        "20260221022814-auto_grown_20260220174252405"]
F = 9.366 / 2.403  # samplePixelSize from each metadata.json (0.009366 mm, 0.002403 mm)


def load(seg, frame):
    ts = seg.split("-")[0]
    d = f"{ROOT}/{seg}/mesh/{ts}-on-{frame}.tifxyz"
    P = np.stack([tifffile.imread(f"{d}/{a}.tif").astype(np.float64) for a in "xyz"], -1)
    valid = ~np.all(P == -1, -1) & (P[..., 2] > 0)
    return P, valid


def bilinear(P, V, r, c):
    H, W = V.shape
    r0 = np.floor(r).astype(int); c0 = np.floor(c).astype(int)
    ok = (r0 >= 0) & (c0 >= 0) & (r0 + 1 < H) & (c0 + 1 < W)
    r0 = np.where(ok, r0, 0); c0 = np.where(ok, c0, 0)
    fr = (r - r0)[:, None]; fc = (c - c0)[:, None]
    v4 = V[r0, c0] & V[r0 + 1, c0] & V[r0, c0 + 1] & V[r0 + 1, c0 + 1]
    out = (P[r0, c0] * (1 - fr) * (1 - fc) + P[r0 + 1, c0] * fr * (1 - fc)
           + P[r0, c0 + 1] * (1 - fr) * fc + P[r0 + 1, c0 + 1] * fr * fc)
    return out, ok & v4


def fit_affine(X, Y, w=None):
    Xh = np.c_[X, np.ones(len(X))]
    sol, *_ = np.linalg.lstsq(Xh, Y, rcond=None)
    return sol[:3].T, sol[3]


def robust_fit(X, Y, it=5):
    keep = np.ones(len(X), bool)
    for _ in range(it):
        A, c = fit_affine(X[keep], Y[keep])
        r = np.linalg.norm(X @ A.T + c - Y, axis=1)
        med = np.median(r[keep]); mad = np.median(np.abs(r[keep] - med)) * 1.4826
        keep = r <= med + 3 * mad
    return A, c, r, keep


def pairs(seg, o):
    P9, V9 = load(seg, "20250821151531-9.366um")
    P2, V2 = load(seg, "20260319124803-2.403um")
    N9 = np.array(P9.shape[:2]) * 20; N2 = np.array(P2.shape[:2]) * 20
    rr, cc = np.nonzero(V9)
    r2 = ((rr * 20 + o) * N2[0] / N9[0] - o) / 20
    c2 = ((cc * 20 + o) * N2[1] / N9[1] - o) / 20
    X2, ok = bilinear(P2, V2, r2, c2)
    return P9[rr, cc][ok], X2[ok], dict(grid9=list(P9.shape[:2]), grid2=list(P2.shape[:2]),
                                        n9_valid=int(V9.sum()), n2_valid=int(V2.sum()), n_pairs=int(ok.sum()))


def main():
    res = {"F": F, "segments": {}}
    allX, allY = [], []
    for seg in SEGS:
        best = None
        for o in [0, 5, 10, 10.5, 15, 20]:
            X, Y, info = pairs(seg, o)
            A, c, r, keep = robust_fit(X, Y)
            e = dict(offset=o, rms=float(np.sqrt(np.mean(r[keep] ** 2))), med=float(np.median(r)),
                     p95=float(np.percentile(r, 95)), kept=float(keep.mean()))
            res["segments"].setdefault(seg, {"offset_scan": []})["offset_scan"].append(e)
            if best is None or e["rms"] < best[0]["rms"]:
                best = (e, X, Y, A, c, info)
        e, X, Y, A, c, info = best
        U, S, Vt = np.linalg.svd(A / F)
        R = U @ Vt
        res["segments"][seg].update(info=info, best_offset=e["offset"], A=A.tolist(), c=c.tolist(),
                                    det=float(np.linalg.det(A)), singular_over_F=S.tolist(),
                                    rotation_part=R.tolist(),
                                    rot_angle_deg=float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))),
                                    z9_range=[float(X[:, 2].min()), float(X[:, 2].max())],
                                    z2_range=[float(Y[:, 2].min()), float(Y[:, 2].max())])
        allX.append(X); allY.append(Y)
    X = np.concatenate(allX); Y = np.concatenate(allY)
    A, c, r, keep = robust_fit(X, Y)
    U, S, Vt = np.linalg.svd(A / F); R = U @ Vt
    res["joint"] = dict(n=int(len(X)), A=A.tolist(), c=c.tolist(), det=float(np.linalg.det(A)),
                        singular_over_F=S.tolist(), rotation_part=R.tolist(),
                        rot_angle_deg=float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))),
                        rms2=float(np.sqrt(np.mean(r[keep] ** 2))), med2=float(np.median(r)),
                        p95_2=float(np.percentile(r, 95)), kept=float(keep.mean()))
    # per-segment residual under the joint fit (2.4 um voxels)
    for seg, Xs, Ys in zip(SEGS, allX, allY):
        rs = np.linalg.norm(Xs @ A.T + c - Ys, axis=1)
        res["segments"][seg]["joint_resid_med2"] = float(np.median(rs))
        res["segments"][seg]["joint_resid_p95_2"] = float(np.percentile(rs, 95))
    # 9 um z-band covered by the rescan (0..15120 in rescan z) under the joint affine, at mesh xy
    Ainv = np.linalg.inv(A)
    zb = []
    for z2 in [0, 15120]:
        p = (np.c_[Y[:, 0], Y[:, 1], np.full(len(Y), z2)] - c) @ Ainv.T
        zb.append([float(np.percentile(p[:, 2], 1)), float(np.percentile(p[:, 2], 99))])
    res["joint"]["z9_of_rescan_z0_and_z15120_at_mesh_xy_p1_p99"] = zb
    json.dump(res, open(sys.argv[1], "w"), indent=1)
    print(json.dumps(res["joint"], indent=1))
    for s in SEGS:
        d = res["segments"][s]; print(s, d["info"], d["best_offset"], d["det"], d["rot_angle_deg"], d["joint_resid_med2"])


if __name__ == "__main__":
    main()
