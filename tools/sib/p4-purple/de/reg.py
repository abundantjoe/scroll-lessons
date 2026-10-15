"""p4-purple-de B2: control-only 78 -> 137 keV registration refinement by 3-D block matching (PROTOCOL.md Part B).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python reg.py <scratch>
Outputs logs/sib/p4-purple/de/registration.json (blocks, fits, LOO, held-out residuals). Numbers only.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

scr = sys.argv[1]
os.makedirs(os.path.join(scr, "blk"), exist_ok=True)
M = D.ref_to_137()
N, HALF, SR, CEN = 128, 64, 16, 96
MARG = 24
g = D.git_json("logs/sib/p4-tiles-b/grid.json", "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b")
T = g["T_px"]
xyz, _ = D.load_mesh(D.SEG_C2, scr)
WIN = {D.V78: (-0.04, 0.22), D.V137: (0.01, 0.16)}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------- candidate block centres
rng = np.random.default_rng(8)
cand = []
for i0 in range(0, xyz.shape[0], 128):
    blk = np.asarray(xyz[i0:i0 + 128])
    gi, gj = np.nonzero(np.isfinite(blk[..., 0]))
    P = blk[gi, gj].astype(np.float64)
    Q = D.map_pts(M, P)
    ok = D.inside_extent(Q) & D.inside_cyl(Q)
    cand.append(np.c_[gi[ok] + i0, gj[ok], P[ok]])
cand = np.concatenate(cand)
cand = cand[rng.permutation(len(cand))]
log("candidates", len(cand))

side137 = int(np.ceil(N * 1.75)) + 2 * MARG


def box137(P):
    Q = D.map_pts(M, P[None])[0]
    lo = np.floor(Q - side137 / 2).astype(int)
    return lo, side137


blocks = {"fit": [], "held": []}
tried = refused = 0
for row in cand:
    if len(blocks["fit"]) >= 30 and len(blocks["held"]) >= 30:
        break
    gi, gj, P = int(row[0]), int(row[1]), row[2:5]
    part = "fit" if (gj * 20 // T) % 2 == 0 else "held"
    if len(blocks[part]) >= 30:
        continue
    allp = [b["P"] for b in blocks["fit"] + blocks["held"]]
    if allp and np.min(np.linalg.norm(np.array(allp) - P, axis=1)) < 250:
        continue
    tried += 1
    lo, s = box137(P)
    if not D.fence_ok_chunks(lo[0], lo[0] + s, lo[1], lo[1] + s, lo[2], lo[2] + s, scr):
        refused += 1
        continue
    Q = D.map_pts(M, P[None])[0]
    qi, pi = np.rint(Q).astype(int), np.rint(P).astype(int)
    if not D.read_byte_137(*map(int, qi), scr) or not D.read_byte_78(*map(int, pi)):
        continue
    blocks[part].append({"gi": gi, "gj": gj, "tile_c": gj * 20 // T, "P": P.tolist()})
log("blocks", len(blocks["fit"]), len(blocks["held"]), "tried", tried, "fence-refused", refused)


def load(b):
    P = np.array(b["P"])
    key = os.path.join(scr, "blk", f"{b['gi']}_{b['gj']}")
    if os.path.exists(key + "_78.npy"):
        return np.load(key + "_78.npy"), np.load(key + "_137.npy"), np.load(key + "_lo.npy")
    p0 = np.rint(P).astype(int) - HALF
    a = D.read_box(D.V78, int(p0[0]), int(p0[1]), int(p0[2]), N, scr)
    lo, s = box137(P)
    c = D.read_box(D.V137, int(lo[0]), int(lo[1]), int(lo[2]), s, scr)
    np.save(key + "_78.npy", a)
    np.save(key + "_137.npy", c)
    np.save(key + "_lo.npy", np.r_[p0, lo])
    return a, c, np.r_[p0, lo]


def tofloat(u, v):
    w0, w1 = WIN[v]
    return w0 + u.astype(np.float32) * (w1 - w0) / 255.0


def resample137(c, lo137, p0, corr):
    """137 keV grey on the 78 keV block grid (REF voxel p0 + idx) through M(P + corr(P))."""
    zz, yy, xx = np.meshgrid(np.arange(N), np.arange(N), np.arange(N), indexing="ij")
    P = np.stack([xx.ravel() + p0[0], yy.ravel() + p0[1], zz.ravel() + p0[2]], 1).astype(np.float64)
    P = P + corr(P)
    Q = D.map_pts(M, P) - lo137
    out = ndi.map_coordinates(c.astype(np.float32), [Q[:, 2], Q[:, 1], Q[:, 0]], order=1, mode="constant", cval=0)
    return out.reshape(N, N, N)


def ncc_shift(a, b):
    """Shift s (xyz) maximising NCC between a[centre] and b(x + s); returns s, peak, on_boundary."""
    o = (N - CEN) // 2
    t = a[o:o + CEN, o:o + CEN, o:o + CEN].astype(np.float64)
    t = (t - t.mean()) / (t.std() + 1e-12)
    F = np.fft.rfftn
    Fi = lambda X: np.fft.irfftn(X, s=(N, N, N), axes=(0, 1, 2))
    tp = np.zeros((N, N, N))
    tp[:CEN, :CEN, :CEN] = t
    bb = b.astype(np.float64)
    ones = np.zeros((N, N, N))
    ones[:CEN, :CEN, :CEN] = 1
    cor = Fi(F(bb) * np.conj(F(tp)))
    s1 = Fi(F(bb) * np.conj(F(ones)))
    s2 = Fi(F(bb * bb) * np.conj(F(ones)))
    n = CEN ** 3
    var = np.maximum(s2 - s1 * s1 / n, 1e-9)
    ncc = cor / np.sqrt(var * n)
    # window start offset u corresponds to shift u - o
    sh = np.arange(-SR, SR + 1)
    sub = ncc[np.ix_(sh + o, sh + o, sh + o)]
    k = np.unravel_index(np.argmax(sub), sub.shape)
    peak = float(sub[k])
    bound = any(x in (0, 2 * SR) for x in k)
    s = []
    for ax in range(3):
        i = list(k)
        v = []
        for d in (-1, 0, 1):
            j = list(k)
            j[ax] = min(max(k[ax] + d, 0), 2 * SR)
            v.append(sub[tuple(j)])
        den = v[0] - 2 * v[1] + v[2]
        frac = 0.5 * (v[0] - v[2]) / den if den < 0 and 0 < k[ax] < 2 * SR else 0.0
        s.append(sh[k[ax]] + frac)
    sz, sy, sx = s
    return np.array([sx, sy, sz]), peak, bound


def match(b, corr):
    a, c, lo = load(b)
    p0, lo137 = lo[:3], lo[3:]
    fa = ndi.gaussian_filter(tofloat(a, D.V78), 1.5)
    fb = resample137(c, lo137, p0, corr)
    valid = fb > 0.5
    fb = ndi.gaussian_filter(tofloat(fb, D.V137) * valid, 1.5)
    s, peak, bound = ncc_shift(fa, fb)
    return {"d": s.tolist(), "peak": peak, "on_boundary": bool(bound), "frac_137_valid": float(valid.mean()),
            "frac_78_nonzero": float((a > 0).mean())}


zero = lambda P: np.zeros_like(P)
t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    for part in ("fit", "held"):
        res = list(ex.map(lambda b: match(b, zero), blocks[part]))
        for b, r in zip(blocks[part], res):
            b["m0"] = r
        log(part, "matched", round(time.time() - t0))


def ok(b, k="m0"):
    return b[k]["peak"] >= 0.30 and not b[k]["on_boundary"]


def fit_affine(P, d):
    keep = np.ones(len(P), bool)
    for _ in range(3):
        X = np.c_[P[keep], np.ones(keep.sum())]
        W, *_ = np.linalg.lstsq(X, d[keep], rcond=None)
        r = np.linalg.norm(np.c_[P, np.ones(len(P))] @ W - d, axis=1)
        sd = np.sqrt((r[keep] ** 2).mean())
        nk = r <= 3 * sd
        if (nk == keep).all():
            break
        keep = nk
    return W, keep


def pred_A(W):
    return lambda P: np.c_[P, np.ones(len(P))] @ W


def pred_T(W, Pf, rf):
    def f(P):
        base = np.c_[P, np.ones(len(P))] @ W
        dd = np.linalg.norm(P[:, None, :] - Pf[None], axis=2)
        idx = np.argsort(dd, 1)[:, :6]
        w = 1.0 / np.maximum(np.take_along_axis(dd, idx, 1), 1.0) ** 2
        return base + (w[..., None] * rf[idx]).sum(1) / w.sum(1)[:, None]
    return f


F_ = [b for b in blocks["fit"] if ok(b)]
Pf = np.array([b["P"] for b in F_])
df = np.array([b["m0"]["d"] for b in F_])
um = 2.4
loo = {"A": [], "T": []}
for i in range(len(F_)):
    m = np.arange(len(F_)) != i
    W, keep = fit_affine(Pf[m], df[m])
    loo["A"].append(float(np.linalg.norm(pred_A(W)(Pf[i:i + 1])[0] - df[i])))
    rf = df[m] - pred_A(W)(Pf[m])
    loo["T"].append(float(np.linalg.norm(pred_T(W, Pf[m], rf)(Pf[i:i + 1])[0] - df[i])))
W, keep = fit_affine(Pf, df)
rf = df - pred_A(W)(Pf)
choice = "A" if np.median(loo["A"]) <= np.median(loo["T"]) else "T"
model = pred_A(W) if choice == "A" else pred_T(W, Pf, rf)
log("LOO median um", {k: np.median(v) * um for k, v in loo.items()}, "choice", choice)

H_ = [b for b in blocks["held"] if ok(b)]
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(lambda b: match(b, model), H_))
for b, r in zip(H_, res):
    b["m1"] = r
Hok = [b for b in H_ if ok(b, "m1")]
rn = np.array([np.linalg.norm(b["m1"]["d"]) for b in Hok]) * um
pred_err = np.array([np.linalg.norm(np.array(b["m0"]["d"]) - model(np.array([b["P"]]))[0]) for b in H_]) * um
out = {"provenance": D.PROV, "serves": "brief_de.md item 3; PROTOCOL.md B2",
       "n_blocks": {"fit": len(blocks["fit"]), "held": len(blocks["held"]), "fit_accepted": len(F_),
                    "held_accepted_m0": len(H_), "held_accepted_m1": len(Hok)},
       "selection": {"tried": tried, "fence_refused": refused, "candidates": int(len(cand))},
       "published_affine_offsets_um": {
           "fit_median_norm": float(np.median(np.linalg.norm(df, axis=1)) * um),
           "fit_p90_norm": float(np.percentile(np.linalg.norm(df, axis=1), 90) * um),
           "held_median_norm": float(np.median([np.linalg.norm(b["m0"]["d"]) for b in H_]) * um) if H_ else None},
       "loo_median_um": {k: float(np.median(v) * um) for k, v in loo.items()},
       "loo_p90_um": {k: float(np.percentile(v, 90) * um) for k, v in loo.items()},
       "primary_model": choice, "affine_correction_W_rows_xyz1_to_dxyz": W.tolist(),
       "affine_inliers": int(keep.sum()),
       "fit_residuals_after_affine_um": (np.linalg.norm(rf, axis=1) * um).tolist(),
       "held_out_block_residual_um": {"median": float(np.median(rn)) if len(rn) else None,
                                      "p90": float(np.percentile(rn, 90)) if len(rn) else None, "n": int(len(rn)),
                                      "prediction_error_median": float(np.median(pred_err)) if len(pred_err) else None,
                                      "prediction_error_p90": float(np.percentile(pred_err, 90)) if len(pred_err) else None},
       "blocks": blocks, "fit_block_P_used": Pf.tolist(), "fit_block_residuals_vox": rf.tolist(),
       "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump(out, open(os.path.join(D.REPO, "logs/sib/p4-purple/de/registration.json"), "w"), indent=1)
log(json.dumps({k: out[k] for k in ("n_blocks", "published_affine_offsets_um", "loo_median_um", "primary_model",
                                    "held_out_block_residual_um")}))
