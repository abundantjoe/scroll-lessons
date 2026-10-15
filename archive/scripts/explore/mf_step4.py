"""Step 4: the OPTIMAL linear spatial integrator (Wiener / patch-LDA) on the depth
projection, and its anisotropic (stroke-frame) counterpart.

h_full     : unconstrained KxK kernel, h = (R+lam I)^-1 c        <- linear ceiling
h_radial   : the same kernel forced to be radially symmetric      <- 'plain smoothing' ceiling
h_aniso    : kernel fitted in the LOCAL STROKE FRAME, applied as max over 12 rotations
             <- the per-stroke matched-filter hypothesis in its strongest linear form
All three use the SAME noise model R, so the only difference is the assumed signal shape.
Leave-one-crop-out over the 8 TRAINING crops."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *
from scipy.signal import fftconvolve
from scipy.ndimage import gaussian_filter, map_coordinates

W = np.load("/home/user/megara/stats/explore/proj_w.npy").astype(np.float32)
K = 41                      # kernel half-size 20 px = 0.38 mm ; kernel 0.79 mm across
R_ = K // 2
RA = K - 1          # autocorrelation radius needed for the block-Toeplitz R
NTH = 12

def prep(s, c):
    x, mp = load_x(s, c)
    t, b = ds8_labels(s, c)
    pj = np.tensordot(W, x, axes=(0, 0)).astype(np.float32)
    m = (mp > 0.5).astype(np.float32)
    q, den = fill(pj, m, 2.0)
    v = (den > 0.3).astype(np.float32)
    q = q * v
    sel = (t | b) & (mp > 0.5)
    return q.astype(np.float32), v, t, b, sel

def corr(a, bimg, rad):
    """Sum_x a(x) b(x+D) for |D|<=rad, via FFT."""
    out = fftconvolve(bimg, a[::-1, ::-1], mode="same")
    cy, cx = out.shape[0] // 2, out.shape[1] // 2
    return out[cy - rad:cy + rad + 1, cx - rad:cx + rad + 1].astype(np.float64)

def stroke_orientation(t):
    """Local stroke direction from the label mask: eigenvector of the structure tensor
    of a lightly smoothed label; returns angle of the along-stroke direction and coherence."""
    L = gaussian_filter(t.astype(np.float32), 3.0)
    gy, gx = np.gradient(L)
    J11 = gaussian_filter(gx * gx, 8.0); J22 = gaussian_filter(gy * gy, 8.0)
    J12 = gaussian_filter(gx * gy, 8.0)
    tr = J11 + J22
    d = np.sqrt(np.maximum((J11 - J22) ** 2 + 4 * J12 ** 2, 0))
    coh = d / (tr + 1e-9)
    # gradient direction = across the stroke; along = +90deg
    ang_grad = 0.5 * np.arctan2(2 * J12, J11 - J22)
    return (ang_grad + np.pi / 2) % np.pi, coh

def contrib(s, c, cache):
    A = np.zeros((2 * RA + 1, 2 * RA + 1)); NA = np.zeros_like(A)
    C = np.zeros((2 * R_ + 1, 2 * R_ + 1)); NC = 0.0
    CR = np.zeros_like(C); NCR = 0.0
    if True:
        q, v, t, b, sel = cache[(s, c)]
        A += corr(q, q, RA); NA += corr(v, v, RA)
        nt, nb = max(int(t.sum()), 1), max(int(b.sum()), 1)
        yc = (t.astype(np.float32) / nt) - (b.astype(np.float32) / nb)
        C += corr(yc, q, R_); NC += 1.0
        # stroke-frame accumulation: bin text pixels by local orientation, rotate back
        ang, coh = stroke_orientation(t)
        good = t & (coh > 0.3)
        for k in range(NTH):
            lo, hi = np.pi * k / NTH, np.pi * (k + 1) / NTH
            sel_k = good & (ang >= lo) & (ang < hi)
            n_k = int(sel_k.sum())
            if n_k < 200: continue
            yk = sel_k.astype(np.float32) / n_k - (b.astype(np.float32) / nb)
            Ck = corr(yk, q, R_)
            th = -np.pi * (k + 0.5) / NTH   # rotate so that the stroke runs along +x
            yy, xx = np.mgrid[-R_:R_ + 1, -R_:R_ + 1].astype(np.float64)
            src_y = (-np.sin(th) * xx + np.cos(th) * yy) + R_
            src_x = (np.cos(th) * xx + np.sin(th) * yy) + R_
            CR += map_coordinates(Ck, [src_y, src_x], order=1, mode="constant")
            NCR += 1.0
    return A, NA, C, NC, CR, NCR


def accumulate(crops, parts):
    A = sum(parts[c][0] for c in crops); NA = sum(parts[c][1] for c in crops)
    C = sum(parts[c][2] for c in crops); NC = sum(parts[c][3] for c in crops)
    CR = sum(parts[c][4] for c in crops); NCR = sum(parts[c][5] for c in crops)
    return A / np.maximum(NA, 1.0), C / max(NC, 1.0), CR / max(NCR, 1.0)

def toeplitz_from_acorr(A):
    idx = np.arange(K)
    dy = idx[:, None] - idx[None, :]
    yy1, xx1 = np.meshgrid(idx, idx, indexing="ij")
    p = np.stack([yy1.ravel(), xx1.ravel()], 1)
    DY = p[:, 0][:, None] - p[:, 0][None, :] + RA
    DX = p[:, 1][:, None] - p[:, 1][None, :] + RA
    return A[DY, DX]

def solve(A, C, lam=1e-2):
    R = toeplitz_from_acorr(A)
    R = R + lam * np.trace(R) / R.shape[0] * np.eye(R.shape[0])
    h = np.linalg.solve(R, C.ravel())
    return h.reshape(K, K)

def radialise(h):
    yy, xx = np.mgrid[-R_:R_ + 1, -R_:R_ + 1]
    r = np.sqrt(yy * yy + xx * xx)
    rb = np.round(r).astype(int)
    prof = np.bincount(rb.ravel(), h.ravel()) / np.maximum(np.bincount(rb.ravel()), 1)
    return prof[rb].astype(np.float32)

def apply_max_rot(q, h, nth=NTH):
    yy, xx = np.mgrid[-R_:R_ + 1, -R_:R_ + 1].astype(np.float64)
    best = None
    for k in range(nth):
        th = np.pi * k / nth
        sy = (np.cos(th) * yy + np.sin(th) * xx) + R_    # inverse rotation sampling
        sx = (-np.sin(th) * yy + np.cos(th) * xx) + R_
        hk = map_coordinates(h, [sy, sx], order=1, mode="constant")
        r = fftconvolve(q, hk[::-1, ::-1], mode="same").astype(np.float32)
        best = r if best is None else np.maximum(best, r)
    return best

if __name__ == "__main__":
    cache = {}
    parts = {}
    for s, c in TRAIN:
        cache[(s, c)] = prep(s, c)
        parts[(s, c)] = contrib(s, c, cache)
        print("prepped", s, c, flush=True)
    res = {"h_full": [], "h_radial": [], "h_aniso_max": [], "h_aniso_sum": [], "best_gauss": []}
    kernels = {}
    for held in TRAIN:
        tr = [x for x in TRAIN if x != held]
        A, C, CR = accumulate(tr, parts)
        hf = solve(A, C); hr = radialise(hf); ha = solve(A, CR)
        q, v, t, b, sel = cache[held]
        sc_f = fftconvolve(q, hf[::-1, ::-1], mode="same")
        sc_r = fftconvolve(q, hr[::-1, ::-1], mode="same")
        sc_a = apply_max_rot(q, ha)
        sc_as = fftconvolve(q, ha[::-1, ::-1], mode="same")
        g = gaussian_filter(q, 16.0, mode="nearest")
        for k, sc in (("h_full", sc_f), ("h_radial", sc_r), ("h_aniso_max", sc_a),
                      ("h_aniso_sum", sc_as), ("best_gauss", g)):
            a = auc(sc[sel], t[sel], b[sel]); res[k].append(round(a, 4))
        print("HOLD %s/%s " % held, {k: res[k][-1] for k in res}, flush=True)
        kernels[f"{held[0]}_{held[1]}"] = {"h_full": hf.tolist(), "h_aniso": ha.tolist()}
    summary = {k: round(float(np.mean(v)), 4) for k, v in res.items()}
    print("LOCO MEANS", summary)
    json.dump({"per_crop": res, "mean": summary}, open("/home/user/megara/stats/explore/step4_wiener.json", "w"), indent=1)
    np.savez_compressed("/home/user/megara/stats/explore/step4_kernels.npz",
                        **{k: np.array(v["h_full"]) for k, v in kernels.items()},
                        **{k + "_ani": np.array(v["h_aniso"]) for k, v in kernels.items()})
