# Provenance: Project HERCULES | owner the owner | [id removed]
"""Affine between the 9.362 um render canvas and the 2.399 um ink-map canvas of one PHerc0139 segment, fitted from
the organizer meshes in both frames (DECL-D2 "affine fitted from meshes in both frames").

1. Q = T(P2): the 2.399 um organizer tifxyz mapped into the 9.362 um volume frame with the organizer landmark affine
   (PHerc0139/volumes/20260102150214-.../transform.json, moving 2.399 um -> fixed 9.362 um frame; x, y rows negative:
   the 180 degree remount).
2. For every valid 9.362 um grid vertex P9 (v9, u9), the fractional 2.399 um grid point (v2, u2) with Q(v2, u2) closest to
   P9 (KD-tree seed, then Gauss-Newton on the bilinear surface, as the renderer interpolates). |P9 - Q(v2, u2)| is the
   off-surface residual (voxels).
3. Robust least squares (v2, u2) = A (v9, u9, 1); converted to canvas pixels with the renderer convention
   (hercules.pipeline.canvas.RenderCanvas): M maps a 9.362 um canvas pixel (row, col) to a 2.399 um canvas pixel.
Numbers only."""
import json, sys, math
import numpy as np
from scipy.spatial import cKDTree
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
from hercules.pipeline.canvas import canvas_for

TJSON = "/work/p139/s3/PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/transform.json"


def load_T():
    return np.array(json.load(open(TJSON))["transformation_matrix"], dtype=np.float64)


def _bilinear(Q, v, u):
    H, W = Q.shape[:2]
    v = np.clip(v, 0, H - 1.000001); u = np.clip(u, 0, W - 1.000001)
    r = np.floor(v).astype(int); c = np.floor(u).astype(int)
    t = (v - r)[:, None]; s = (u - c)[:, None]
    q00, q01, q10, q11 = Q[r, c], Q[r, c + 1], Q[r + 1, c], Q[r + 1, c + 1]
    val = (1 - t) * ((1 - s) * q00 + s * q01) + t * ((1 - s) * q10 + s * q11)
    du = (1 - t) * (q01 - q00) + t * (q11 - q10)
    dv = (1 - s) * (q10 - q00) + s * (q11 - q01)
    ok = np.isfinite(q00).all(1) & np.isfinite(q01).all(1) & np.isfinite(q10).all(1) & np.isfinite(q11).all(1)
    return val, dv, du, ok


def correspond(P9, Q, iters=8):
    """P9 (N,3) points; Q (H,W,3) grid with NaN invalid -> (v2, u2, residual, ok)."""
    qv = np.isfinite(Q).all(-1)
    rr, cc = np.nonzero(qv)
    tree = cKDTree(Q[rr, cc])
    _, i = tree.query(P9)
    v = rr[i].astype(np.float64); u = cc[i].astype(np.float64)
    for _ in range(iters):
        val, dv, du, ok = _bilinear(Q, v, u)
        J = np.stack([dv, du], -1)                           # (N,3,2)
        r = P9 - val
        JtJ = np.einsum("nki,nkj->nij", J, J); Jtr = np.einsum("nki,nk->ni", J, r)
        det = JtJ[:, 0, 0] * JtJ[:, 1, 1] - JtJ[:, 0, 1] ** 2
        good = ok & (det > 1e-9)
        d0 = np.where(good, (JtJ[:, 1, 1] * Jtr[:, 0] - JtJ[:, 0, 1] * Jtr[:, 1]) / np.where(good, det, 1), 0)
        d1 = np.where(good, (JtJ[:, 0, 0] * Jtr[:, 1] - JtJ[:, 0, 1] * Jtr[:, 0]) / np.where(good, det, 1), 0)
        v = v + np.clip(d0, -1, 1); u = u + np.clip(d1, -1, 1)
    val, _, _, ok = _bilinear(Q, v, u)
    H, W = Q.shape[:2]
    inside = (v >= 0) & (v <= H - 1) & (u >= 0) & (u <= W - 1)
    return v, u, np.linalg.norm(P9 - val, axis=1), ok & inside


def fit(seg_dir, ts, max_pts=200000, seed=0):
    m9 = read_tifxyz(f"{seg_dir}/mesh/{ts}-on-20250728140407-9.362um.tifxyz")
    m2 = read_tifxyz(f"{seg_dir}/mesh/{ts}-on-20260102150214-2.399um.tifxyz")
    T = load_T()
    P2 = m2.points.astype(np.float64)
    Q = P2 @ T[:, :3].T + T[:, 3]
    Q[~valid_mask(m2.points)] = np.nan
    v9m = valid_mask(m9.points)
    rr, cc = np.nonzero(v9m)
    if rr.size > max_pts:
        k = np.random.default_rng(seed).choice(rr.size, max_pts, replace=False); rr, cc = rr[k], cc[k]
    P9 = m9.points[rr, cc].astype(np.float64)
    v2, u2, res, ok = correspond(P9, Q)
    use = ok & (res < 3.0)
    X = np.c_[rr, cc, np.ones(rr.size)].astype(np.float64)
    Y = np.c_[v2, u2]
    A = None
    for _ in range(3):
        A, *_ = np.linalg.lstsq(X[use], Y[use], rcond=None)
        e = np.linalg.norm(X @ A - Y, axis=1)
        med = np.median(e[use]); mad = np.median(np.abs(e[use] - med)) + 1e-9
        use = ok & (res < 3.0) & (e < med + 6 * 1.4826 * mad)
    e = np.linalg.norm(X @ A - Y, axis=1)
    c9 = canvas_for(m9.points, m9.scale); c2 = canvas_for(m2.points, m2.scale)
    # canvas matrix: pix9 -> grid9 -> grid2 -> pix2 (all affine); solve from 3 points
    P = np.array([[0.0, 0.0], [1000.0, 0.0], [0.0, 1000.0]])
    gv, gu = c9.pixel_to_grid(P[:, 0], P[:, 1])
    G2 = np.c_[gv, gu, np.ones(3)] @ A
    y2, x2 = c2.grid_to_pixel(G2[:, 0], G2[:, 1])
    Mm = np.linalg.solve(np.c_[P, np.ones(3)], np.c_[y2, x2]).T      # 2x3: [y2,x2] = Mm @ [y9,x9,1]
    # plain-scaling comparison (factor from metadata voxel sizes, same pixel origin)
    Hc9, Wc9 = c9.shape
    F = 9.362 / 2.399
    corners = np.array([[0, 0], [Hc9 - 1, 0], [0, Wc9 - 1], [Hc9 - 1, Wc9 - 1], [(Hc9 - 1) / 2, (Wc9 - 1) / 2]], float)
    fitted = corners @ Mm[:, :2].T + Mm[:, 2]
    plain = corners * F
    dev_um = np.linalg.norm(fitted - plain, axis=1) * 2.399
    g2px = 1.0 / m2.scale[0] * (2.399 / 9.362)     # one 2.399 grid unit in 9.362 canvas px
    return dict(
        grid9=list(m9.points.shape[:2]), grid2=list(m2.points.shape[:2]), canvas9=list(c9.shape), canvas2=list(c2.shape),
        n_pts=int(rr.size), n_used=int(use.sum()), frac_used=float(use.mean()),
        offsurface_res_vox=dict(p50=float(np.median(res[ok])), p95=float(np.percentile(res[ok], 95)),
                                p99=float(np.percentile(res[ok], 99)), max=float(res[ok].max())),
        fit_res_px9=dict(p50=float(np.median(e[use]) * g2px), p95=float(np.percentile(e[use], 95) * g2px),
                         p99=float(np.percentile(e[use], 99) * g2px), max=float(e[use].max() * g2px)),
        A_grid=A.T.tolist(), M_pix9_to_pix2=Mm.tolist(),
        scale_rows=float(Mm[0, 0]), scale_cols=float(Mm[1, 1]), shear=[float(Mm[0, 1]), float(Mm[1, 0])],
        plain_scaling_dev_um=dict(corner_max=float(dev_um[:4].max()), centre=float(dev_um[4])),
    )


if __name__ == "__main__":
    seg = sys.argv[1]
    ts = seg.split("-")[0]
    r = fit(f"/work/p139/s3/PHerc0139/segments/{seg}", ts)
    print(json.dumps(r, indent=1))
