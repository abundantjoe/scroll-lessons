#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-2 ORD-3: ordered-stack ridge tracking of one target lamina T and its two nearest competitor laminae A (+n side) and
B (-n side) across y. Per row: tube ROI around the previous row's three curves; (RAW mode) tilt-corrected 8-section mean with
the slope from the 3-D structure tensor, (MEANS mode) the cached 16-section mean as is; the gated ridge field of
e2e_sheet.sheet_fields with ONE tau per block; per lamina an exact Viterbi along u on integer offsets along the lamina's own
previous normal, inside a competitor-distance label range Delta = min(dmax, floor(0.5 d_comp) - 1 - |dy s|); identity
invariants I1 (order/separation of T, A, B), I2 (bridging only under anchored twins), I3 (motion bound by construction),
I4 (tangent texture ZNCC against a twin-swap null); status grammar ANCHORED / AMBIGUOUS / BRIDGED / UNRESOLVED / TERMINATED
with the declared limits; export of ANCHORED cells only in the e2e formats. Geometry only: nothing here is a claim about ink
or letters. Every number is written to grow_checks.json; every identity event to ledger.json.
usage: ord3.py means <params.json> <out_dir> --store <dir of sec_<y>.npy> --seed_npz <surface.npz> --seed_y 5820 --origin 1312 544 [--ys 5532 5564 ...]
       ord3.py raw   <params.json> <out_dir> --block <block.npy> --seed_npy <seed (U,2) z,x> --seed_y 192 --rows 47 48
"""
import os, sys, json, time, resource, argparse, numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'master')); sys.path.insert(0, os.path.join(HERE, '..', 'umb'))
from e2e_sheet import sheet_fields
UNTRACKED, ANCHORED, AMBIGUOUS, BRIDGED, UNRESOLVED, TERMINATED, DORMANT = 0, 1, 2, 3, 4, 5, 6
SNAME = ['UNTRACKED', 'ANCHORED', 'AMBIGUOUS', 'BRIDGED', 'UNRESOLVED', 'TERMINATED', 'DORMANT']; LN = ['T', 'A', 'B']; OPEN = 44.0
J = lambda o: o.item() if hasattr(o, 'item') else (str(o) if not isinstance(o, (list, dict)) else o)

def rss_gb(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
def smooth(C, s): return np.stack([ndi.gaussian_filter1d(C[:, i].astype(np.float64), s, mode='nearest') for i in range(2)], 1)
def frame(C, s):
    """Unit tangent t = (tz, tx) and in-section normal n = (-tx, tz) of the sigma_u-smoothed curve C (U, 2) in (z, x)."""
    S = smooth(C, s); d = np.gradient(S, axis=0); t = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9); return t, np.stack([-t[:, 1], t[:, 0]], 1)
def rho_of(C, s):
    S = smooth(C, s); d1 = np.gradient(S, axis=0); d2 = np.gradient(d1, axis=0); k = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / (np.sum(d1 ** 2, 1) ** 1.5 + 1e-9); return 1.0 / (k + 1e-9)
def resample(Z, X, step=1.0):
    ok = np.isfinite(Z) & np.isfinite(X); z, x = Z[ok], X[ok]; s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(z), np.diff(x)))]); u = np.arange(0, s[-1], step); return np.stack([np.interp(u, s, z), np.interp(u, s, x)], 1)
def sample(F, pts, order=1):
    return ndi.map_coordinates(F, [pts[..., 0].ravel(), pts[..., 1].ravel()], order=order, mode='nearest').reshape(pts.shape[:-1])
def inside(shape, pts): return (pts[..., 0] >= 0) & (pts[..., 0] <= shape[0] - 1) & (pts[..., 1] >= 0) & (pts[..., 1] <= shape[1] - 1)
def runs_longer(b, L):
    """Mask of the elements of boolean b that lie in a run of True longer than L."""
    lab, n = ndi.label(b); 
    if n == 0: return np.zeros_like(b)
    sz = np.bincount(lab.ravel()); big = np.zeros(n + 1, bool); big[1:] = sz[1:] > L; return big[lab]
def runs_atleast(b, L):
    lab, n = ndi.label(b)
    if n == 0: return np.zeros_like(b)
    sz = np.bincount(lab.ravel()); ok = np.zeros(n + 1, bool); ok[1:] = sz[1:] >= L; return ok[lab]

def gated_fields(M, mask, P):
    """DECL-E2E-2-A1: Hessian bright ridge (sigma 4) gated by the gap-adaptive symmetric test (centre brighter by g_min than the minimum
    of the image over offsets 4..22 along +n and along -n), voids excluded; orientation field and coherence as in sheet_fields."""
    import uturns as UT; from st_axis import st_accumulate, st_eigen
    Z, X = M.shape; img = ndi.gaussian_filter(M.astype(np.float32) / 255.0, 1.0); sig = P.get('ridge_sigmas') or [P['ridge_sigma']]; R, nz, nx = UT.hessian_ridge(img, sig[0])
    for sg in sig[1:]:                                                                                                       # multi-scale: the sigma^2-normalised bright-ridge strength, max over scales, normal from the winning scale
        R2, nz2, nx2 = UT.hessian_ridge(img, sg); w = R2 > R; R = np.where(w, R2, R); nz = np.where(w, nz2, nz); nx = np.where(w, nx2, nx); del R2, nz2, nx2, w
    ds = np.arange(4, P['flank_d'] + 1, 2, dtype=np.float32)
    zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); mp = np.full((Z, X), np.inf, np.float32); mm = np.full((Z, X), np.inf, np.float32)
    for d in ds:
        mp = np.minimum(mp, ndi.map_coordinates(img, [zz + d * nz, xx + d * nx], order=1, mode='nearest')); mm = np.minimum(mm, ndi.map_coordinates(img, [zz - d * nz, xx - d * nx], order=1, mode='nearest'))
    sym = np.minimum(img - mp, img - mm); del mp, mm, zz, xx
    void = ndi.binary_dilation((M < np.percentile(M[mask], P['void_pct'])) & mask, iterations=P['void_dilate']) if mask.any() else np.zeros_like(mask)
    Rs = np.where((sym > P['g_min_adaptive']) & ~void & mask, R, 0).astype(np.float32); del sym, R, nz, nx
    th, coh, _ = st_eigen(st_accumulate([img], 2.0), 8.0); del img; nzv = Rs[mask & (Rs > 0)]; tau = float(np.median(nzv) + 3 * np.median(np.abs(nzv - np.median(nzv)))) if nzv.size else 1e9
    return Rs, np.sin(th).astype(np.float16), np.cos(th).astype(np.float16), coh.astype(np.float16), void, tau

def gated_fields3d(S, M, mask, P):
    """DECL-E2E-3 item 2: 3-D sheet-likeness operator on the raw tube stack S (n, Z, X) (stripe-removed float), evaluated at the middle
    section: Hessian at sigma (sy, sz, sx) via 1-D Gaussian derivatives along y and 2-D derivatives in (z, x); bright-sheet strength
    R3 = max(0, -l1) * sz^2 where l1 is the most negative eigenvalue, kept where |l1| >= 2 |l2| (sheet-likeness) and the in-section part of
    the normal |n_v| >= 0.7; the gap-adaptive symmetric gate along the in-section normal on the mean M; voids excluded. Scales: max over
    the declared list, the normal from the winning scale. Returns (Rs, FZ, FX, coh=|n_v|, void, tau) like gated_fields."""
    n, Z, X = S.shape; mid = n // 2; Rb = np.zeros((Z, X), np.float32); nz = np.zeros((Z, X), np.float32); nx = np.zeros((Z, X), np.float32); nyb = np.zeros((Z, X), np.float32); nvb = np.zeros((Z, X), np.float32)
    for (sy, sz, sx) in P.get('sigmas3d', [[2, 3, 3], [2, 2, 2]]):
        G0 = ndi.gaussian_filter1d(S, sy, axis=0, order=0, mode='nearest')[mid]; G1 = ndi.gaussian_filter1d(S, sy, axis=0, order=1, mode='nearest')[mid]; G2 = ndi.gaussian_filter1d(S, sy, axis=0, order=2, mode='nearest')[mid]
        Hyy = ndi.gaussian_filter(G2, (sz, sx)); Hyz = ndi.gaussian_filter(G1, (sz, sx), order=(1, 0)); Hyx = ndi.gaussian_filter(G1, (sz, sx), order=(0, 1)); Hzz = ndi.gaussian_filter(G0, (sz, sx), order=(2, 0)); Hxx = ndi.gaussian_filter(G0, (sz, sx), order=(0, 2)); Hzx = ndi.gaussian_filter(G0, (sz, sx), order=(1, 1)); del G0, G1, G2
        H = np.empty((Z * X, 3, 3), np.float32); H[:, 0, 0] = Hyy.ravel(); H[:, 1, 1] = Hzz.ravel(); H[:, 2, 2] = Hxx.ravel(); H[:, 0, 1] = H[:, 1, 0] = Hyz.ravel(); H[:, 0, 2] = H[:, 2, 0] = Hyx.ravel(); H[:, 1, 2] = H[:, 2, 1] = Hzx.ravel(); del Hyy, Hyz, Hyx, Hzz, Hxx, Hzx
        w, e = np.linalg.eigh(H); del H; l1 = w[:, 0]; l2 = w[:, 1]; v = e[:, :, 0]; del w, e                                           # ascending: l1 most negative (across the bright sheet)
        R = np.maximum(0, -l1) * (sz * sz); sheet = np.abs(l1) >= 2.0 * np.abs(l2); nv = np.sqrt(v[:, 1] ** 2 + v[:, 2] ** 2); R = np.where(sheet & (nv >= P.get('nv_min', 0.7)), R, 0).reshape(Z, X).astype(np.float32)
        better = R > Rb; Rb = np.where(better, R, Rb); nvr = nv.reshape(Z, X); vz = (v[:, 1] / (nv + 1e-9)).reshape(Z, X); vx = (v[:, 2] / (nv + 1e-9)).reshape(Z, X); vy = v[:, 0].reshape(Z, X)
        nz = np.where(better, vz, nz); nx = np.where(better, vx, nx); nyb = np.where(better, vy, nyb); nvb = np.where(better, nvr, nvb); del R, v, l1, l2, nv, vz, vx, vy, nvr
    img = ndi.gaussian_filter(M.astype(np.float32) / 255.0, 1.0); zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); mp = np.full((Z, X), np.inf, np.float32); mm = mp.copy()
    for d in np.arange(4, P['flank_d'] + 1, 2, dtype=np.float32):
        mp = np.minimum(mp, ndi.map_coordinates(img, [zz + d * nz, xx + d * nx], order=1, mode='nearest')); mm = np.minimum(mm, ndi.map_coordinates(img, [zz - d * nz, xx - d * nx], order=1, mode='nearest'))
    sym = np.minimum(img - mp, img - mm); del mp, mm, zz, xx, img
    void = ndi.binary_dilation((M < np.percentile(M[mask], P['void_pct'])) & mask, iterations=P['void_dilate']) if mask.any() else np.zeros_like(mask)
    Rs = np.where((sym > P['g_min_adaptive']) & ~void & mask, Rb, 0).astype(np.float32); del sym, Rb; nzv = Rs[mask & (Rs > 0)]; tau = float(np.median(nzv) + 3 * np.median(np.abs(nzv - np.median(nzv)))) if nzv.size else 1e9
    return Rs, nz.astype(np.float16), nx.astype(np.float16), nvb.astype(np.float16), void, tau

class MeansSource:
    """One cached 16-section mean per row (uint8, 1..255 inside the mask, 0 outside): the ORD-3-M variant, no tilt correction."""
    def __init__(self, store, ys): self.ys = list(ys); self.mm = {y: np.load(f'{store}/sec_{y}.npy', mmap_mode='r') for y in self.ys}; self.shape = self.mm[self.ys[0]].shape; self.has_tensor = False
    def mean(self, y, bb, s_dense=None, nhat=None):
        c = np.asarray(self.mm[y][bb[0]:bb[1], bb[2]:bb[3]]); return c, c > 0, c

class BlockSource:
    """Raw sections (Y, Z, X) uint8 memmap, 0 outside the mask. Per section: stripe removal (column z-median over the block's full
    z range inside the mask); one fixed intensity scale for the block (p0.5-p99.5 of the seed row's stack); the row's image is the
    plain or tilt-corrected n_avg-section mean; the texture section is the stripe-removed middle section at the same scale."""
    def __init__(self, path, n_avg=8, n_tensor=12): self.blk = np.load(path, mmap_mode='r'); self.Y, self.Z, self.X = self.blk.shape; self.shape = (self.Z, self.X); self.n_avg = n_avg; self.n_tensor = n_tensor; self.lo = None; self.has_tensor = True
    def section(self, j, bb):
        col = np.asarray(self.blk[j, :, bb[2]:bb[3]]).astype(np.float32); col[col == 0] = np.nan; med = np.nanmedian(col, 0); med[~np.isfinite(med)] = 0
        c = col[bb[0]:bb[1]]; mk = np.isfinite(c); return np.where(mk, c - med[None, :], 0).astype(np.float32), mk
    def stack(self, y, bb, n):
        js = [min(max(y - n // 2 + i, 0), self.Y - 1) for i in range(n)]; S, M = zip(*[self.section(j, bb) for j in js]); return np.stack(S), np.stack(M)
    def u8(self, v, mask):
        if self.lo is None: self.lo, self.hi = [float(q) for q in np.percentile(v[mask], [0.5, 99.5])]
        return (np.clip((v - self.lo) / (self.hi - self.lo + 1e-6), 0, 1) * 254 + 1).astype(np.uint8) * mask
    def mean(self, y, bb, s_dense=None, nhat=None):
        S12, Mk12 = self.stack(y, bb, self.n_tensor); o = (self.n_tensor - self.n_avg) // 2; S, Mk = S12[o:o + self.n_avg], Mk12[o:o + self.n_avg]; n = S.shape[0]; mask = Mk[n // 2]
        if s_dense is None: M = S.mean(0)
        else:
            zz, xx = np.mgrid[0:S.shape[1], 0:S.shape[2]].astype(np.float32); M = np.zeros(S.shape[1:], np.float32)
            for i in range(n):
                d = (i - n // 2 + 0.5) * s_dense; M += ndi.map_coordinates(S[i], [zz + d * nhat[0], xx + d * nhat[1]], order=1, mode='nearest')
            M /= n
        self._stack = S12; return self.u8(M, mask), mask, self.u8(S[n // 2], Mk[n // 2])                      # tensor on the 12-section stack (DECL-E2E-2-A2), mean on the middle 8

def tensor3(S, P):
    """3-D structure tensor of the raw stack (n, Z, X) at half resolution: N (Zh, Xh, 3) the (y, z, x) eigenvector of the largest
    eigenvalue at the middle section, coh3 = (l3 - l2) / l3."""
    n, Z, X = S.shape; Zh, Xh = Z // 2, X // 2; H = S[:, :2 * Zh, :2 * Xh].reshape(n, Zh, 2, Xh, 2).mean((2, 4))
    g = [ndi.gaussian_filter(H, P['grad_sigma_half'], order=o) for o in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]]; del H; Jt = np.zeros((Zh, Xh, 3, 3), np.float32)
    for a in range(3):
        for b in range(a, 3): Jt[..., a, b] = Jt[..., b, a] = ndi.gaussian_filter(g[a] * g[b], P['smooth_sigma_half'])[n // 2]
    del g; w, e = np.linalg.eigh(Jt); N = e[..., :, 2].astype(np.float32); coh3 = ((w[..., 2] - w[..., 1]) / (w[..., 2] + 1e-12)).astype(np.float32); return N, coh3

def slope_field(N, coh3, FZ, FX, P):
    """Dense slope s(z, x) = -N_y / (N . nhat) at full resolution; 0 where coh3 < coh3_min or |s| > s_max; Gaussian-smoothed."""
    Zh, Xh = coh3.shape; nz = FZ[:2 * Zh:2, :2 * Xh:2].astype(np.float32); nx = FX[:2 * Zh:2, :2 * Xh:2].astype(np.float32)
    den = N[..., 1] * nz + N[..., 2] * nx; den = np.where(np.abs(den) < 1e-3, 1e-3, den); s = -2.0 * N[..., 0] / den        # x2: the tensor grid is half-resolution in (z, x), full in y
    ok = (coh3 >= P['coh3_min']) & (np.abs(s) <= P['s_max']); s = np.where(ok, s, 0).astype(np.float32)
    full = np.zeros(FZ.shape, np.float32); up = np.repeat(np.repeat(s, 2, 0), 2, 1); full[:up.shape[0], :up.shape[1]] = up[:FZ.shape[0], :FZ.shape[1]]
    return ndi.gaussian_filter(full, P['dense_s_smooth']), float(ok.mean())

def slope_cells(N, coh3, pts, n, P):
    """Per-cell slope at full-resolution crop points pts (U, 2) for a lamina with normal n (U, 2): (s, ok)."""
    ph = pts / 2.0; Nc = np.stack([sample(N[..., i], ph) for i in range(3)], 1); c3 = sample(coh3, ph); den = Nc[:, 1] * n[:, 0] + Nc[:, 2] * n[:, 1]
    s = -2.0 * Nc[:, 0] / np.where(np.abs(den) < 1e-3, 1e-3, den); ok = (c3 >= P['coh3_min']) & (np.abs(s) <= P['s_max']); return np.where(ok, s, 0.0), ok

def viterbi(D, Pw):
    """Exact minimum-cost labelling along u: D (U, nV) unary, Pw (nV, nV) pairwise on label pairs."""
    U, nV = D.shape; back = np.zeros((U, nV), np.int16); cost = D[0].astype(np.float64); ar = np.arange(nV)
    for u in range(1, U):
        tot = cost[:, None] + Pw; back[u] = np.argmin(tot, 0); cost = tot[back[u], ar] + D[u]
    lab = np.zeros(U, np.int32); lab[-1] = int(np.argmin(cost))
    for u in range(U - 1, 0, -1): lab[u - 1] = back[u, lab[u]]
    return lab

def solve_lamina(Rs, void, mask, tau, C, n, p, Delta, active, P, dmax):
    """One lamina, one row. C, n (U, 2) crop coords and normals of the previous curve; p (U,) predicted offset along n; Delta (U,) label
    half-range (< 1: the cell is carried at p); active (U,). Returns h (sub-voxel offset), rs_h (Rs/tau), margin, hit (a candidate
    >= tau/2 in range), n_cand, in_void (at h), in_mask (at h)."""
    U = len(p); V = np.arange(-dmax, dmax + 1); nV = len(V); p0 = np.round(p); vv = p0[:, None] + V[None, :]
    pts = C[:, None, :] + vv[..., None] * n[:, None, :]; ins = inside(Rs.shape, pts); rs = sample(Rs, pts) / tau * ins; vd = sample(void.astype(np.float32), pts) > 0.5; mk = sample(mask.astype(np.float32), pts) > 0.5
    allowed = (np.abs(vv - p[:, None]) <= Delta[:, None]) & active[:, None]; j0 = np.argmin(np.abs(vv - p[:, None]), 1); none = ~allowed.any(1); allowed[none, j0[none]] = True
    D = -np.minimum(rs, P['unary_cap']) + P['void_cost'] * vd + P['lambda_y'] * np.minimum(((vv - p[:, None]) / P['sigma_y']) ** 2, P['T_y']); D = np.where(allowed, D, 1e6).astype(np.float32)
    dv = np.abs(V[:, None] - V[None, :]); Pw = np.where(dv <= 1, P['pair'][0], np.where(dv == 2, P['pair'][1], P['pair'][2])).astype(np.float64)
    lab = viterbi(D, Pw); ar = np.arange(U); h = vv[ar, lab].astype(np.float64); r0 = rs[ar, lab]
    lm_, lp_ = np.clip(lab - 1, 0, nV - 1), np.clip(lab + 1, 0, nV - 1); a_, b_, c_ = rs[ar, lm_], r0, rs[ar, lp_]; den = a_ - 2 * b_ + c_
    ok = (lab > 0) & (lab < nV - 1) & (den < 0) & (b_ >= a_) & (b_ >= c_); h = h + np.where(ok, np.clip(0.5 * (a_ - c_) / np.where(den == 0, -1e-9, den), -0.5, 0.5), 0.0)
    rsa = np.where(allowed, rs, -1.0); left = np.roll(rsa, 1, 1); right = np.roll(rsa, -1, 1); left[:, 0] = -1; right[:, -1] = -1
    lmax = (rsa >= left) & (rsa >= right) & (rsa >= P['anchored_rs_frac']); hit = lmax.any(1); other = lmax.copy(); other[ar, lab] = False; other[ar, lm_] = False; other[ar, lp_] = False
    best_other = np.where(other, rsa, -1.0).max(1); margin = np.where(best_other > 0, r0 - best_other, r0)
    return h, r0, margin, hit, lmax.sum(1), vd[ar, lab], mk[ar, lab]

def find_twins(Rs, tau, C, n, P):
    """Seed row: the nearest gated maxima (Rs >= tau/2, local maximum along the ray) at >= exclusion vox on the + side (A) and the - side
    (B) within +-search along n; NaN where none (OPEN-SIDE)."""
    srch, excl = P['search'], P['exclusion']; V = np.arange(-srch, srch + 1).astype(np.float64); pts = C[:, None, :] + V[None, :, None] * n[:, None, :]; rs = sample(Rs, pts) / tau * inside(Rs.shape, pts)
    lm = (rs >= np.roll(rs, 1, 1)) & (rs >= np.roll(rs, -1, 1)) & (rs >= P['min_rs_frac']); lm[:, 0] = False; lm[:, -1] = False
    pos = np.where(lm & (V[None, :] >= excl), V[None, :], np.inf).min(1); neg = np.where(lm & (V[None, :] <= -excl), V[None, :], -np.inf).max(1)
    return np.where(np.isfinite(pos), pos, np.nan), np.where(np.isfinite(neg), neg, np.nan)

def texture(tex, C, t, half):
    """Z-normalised CT profile along the tangent at every cell: (U, 2 half + 1)."""
    jj = np.arange(-half, half + 1).astype(np.float64); pts = C[:, None, :] + jj[None, :, None] * t[:, None, :]; v = sample(tex.astype(np.float32), pts); v = v - v.mean(1, keepdims=True); return v / (v.std(1, keepdims=True) + 1e-6)
def zncc(a, b): return (a * b).mean(1)

class Tracker:
    """State across rows: curves C[L] (U, 2) in section coordinates, normals, statuses, counters; one fixed tau per block."""
    def __init__(self, src, P, seed_curve, seed_y, dy, out, origin=(0, 0), nulls=True, overlay_every=8, verbose=True):
        self.src, self.P, self.dy, self.out, self.origin, self.nulls, self.ov_every, self.verbose = src, P, dy, out, np.array(origin, np.float64), nulls, overlay_every, verbose
        self.sig = P['sigma_u']; self.tube = P['tube']; self.dmax = P['delta']['delta_max_raw'] if src.has_tensor else P['delta']['delta_max_means']
        self.U = len(seed_curve); self.seed_y = seed_y; self.tau = None; self.ledger = []; self.records = []; self.rows = {}; self.ctx = {}; os.makedirs(out, exist_ok=True)
        self.seed_curve = seed_curve.astype(np.float64); self.ablation = {}; self.fcache = {}; self.keep_fields = True; self.seed_fields = None
    # ---------------------------------------------------------------- helpers
    def bbox(self, st):
        pts = np.concatenate([st['C'][L] for L in range(3)]); Z, X = self.src.shape; z0 = int(max(0, np.floor(pts[:, 0].min()) - self.tube)); z1 = int(min(Z, np.ceil(pts[:, 0].max()) + self.tube + 1)); x0 = int(max(0, np.floor(pts[:, 1].min()) - self.tube)); x1 = int(min(X, np.ceil(pts[:, 1].max()) + self.tube + 1)); return (z0, z1, x0, x1)
    def crop_field(self, F, bb_from, bb_to, fill=0.0):
        """Re-frame a crop field from bb_from to bb_to (zero outside)."""
        out = np.full((bb_to[1] - bb_to[0], bb_to[3] - bb_to[2]), fill, F.dtype); z0, z1 = max(bb_from[0], bb_to[0]), min(bb_from[1], bb_to[1]); x0, x1 = max(bb_from[2], bb_to[2]), min(bb_from[3], bb_to[3])
        if z1 > z0 and x1 > x0: out[z0 - bb_to[0]:z1 - bb_to[0], x0 - bb_to[2]:x1 - bb_to[2]] = F[z0 - bb_from[0]:z1 - bb_from[0], x0 - bb_from[2]:x1 - bb_from[2]]
        return out
    def fields(self, y, bb, corrected, k=None):
        if k is not None and k in self.fcache:                                                            # Jacobi pass: the sweep's fields of this row, re-framed to the new tube bbox
            F = self.fcache[k]; bbo = F['bb']
            if bb[0] >= bbo[0] - 8 and bb[1] <= bbo[1] + 8 and bb[2] >= bbo[2] - 8 and bb[3] <= bbo[3] + 8:
                rf = lambda A, fill=0: self.crop_field(A, bbo, bb, fill); return rf(F['M']), rf(F['mask']).astype(bool), rf(F['tex']), rf(F['Rs']), rf(F['FZ']), rf(F['FX']), rf(F['void']).astype(bool), F['tau_row'], F['corr']
        s_dense = nhat = None
        if corrected and self.src.has_tensor and 's_dense' in self.ctx:
            s_dense = self.crop_field(self.ctx['s_dense'], self.ctx['s_bb'], bb); nhat = (self.crop_field(self.ctx['FZ'].astype(np.float32), self.ctx['s_bb'], bb), self.crop_field(self.ctx['FX'].astype(np.float32), self.ctx['s_bb'], bb))
        M, mask, tex = self.src.mean(y, bb, s_dense, nhat)
        if self.P['fields'].get('operator') == '3d' and self.src.has_tensor: Rs, FZ, FX, coh, void, tau_row = gated_fields3d(self.src._stack, M, mask, self.P['fields'])          # DECL-E2E-3 item 2
        else: Rs, FZ, FX, coh, void, tau_row = (gated_fields(M, mask, self.P['fields']) if self.P['fields'].get('gate', 'adaptive') == 'adaptive' else sheet_fields(M, mask))
        if self.tau is None: self.tau = tau_row
        if k is None and self.keep_fields and getattr(self, '_cache_k', None) is not None: self.fcache[self._cache_k] = {'bb': bb, 'M': M, 'mask': mask, 'tex': tex, 'Rs': Rs, 'FZ': FZ, 'FX': FX, 'void': void, 'tau_row': tau_row, 'corr': s_dense is not None}
        return M, mask, tex, Rs, FZ, FX, void, tau_row, s_dense is not None
    # ---------------------------------------------------------------- one row
    def solve_row(self, prev, y, k, corrected=True, pred=None, jacobi=False, tag=''):
        t0 = time.time(); P = self.P; U = self.U; dy = self.dy; bb = self.bbox(prev); self._cache_k = None if jacobi else k; M, mask, tex, Rs, FZ, FX, void, tau_row, corr = self.fields(y, bb, corrected, k=k if jacobi else None); tau = self.tau; o = np.array([bb[0], bb[2]], np.float64)
        st = {'y': y, 'k': k, 'C': [None] * 3, 'n': [None] * 3, 't': [None] * 3, 'status': [None] * 3, 'rs': [None] * 3, 'margin': [None] * 3, 's': [None] * 3, 'inc': [None] * 3, 'run_b': [None] * 3, 'run_u': [None] * 3, 'fallback': [0.0] * 3, 'bb': bb}
        # slope prior (RAW) from the tensor of this row's raw stack; the dense field is kept for the NEXT row's warp (declared: previous row's s)
        N = coh3 = None
        if self.src.has_tensor and not jacobi: N, coh3 = tensor3(self.src._stack, P['tensor']); s_dense, s_ok_frac = slope_field(N, coh3, FZ, FX, P['tensor']); self.ctx.update({'s_dense': s_dense, 's_bb': bb, 'FZ': FZ, 'FX': FX, 's_ok_frac': s_ok_frac})
        d_comp = self.dcomp(prev); step = 0 if jacobi else int(y - prev['y']); pstep = prev.get('step', 0); st['step'] = step                 # signed y step of this row (0 on a re-solve); the previous row's step gives the sign of the fallback slope
        for L in range(3):
            Cp = prev['C'][L] - o; t_, n_ = frame(prev['C'][L], self.sig); act = (prev['status'][L] != TERMINATED) & (prev['status'][L] != UNTRACKED); was_dorm = prev['status'][L] == DORMANT
            s_fb = np.clip(prev['inc'][L] / pstep, -1.0, 1.0) if pstep else np.zeros(U)                                                     # previous accepted increment per section (signed by its own step)
            if self.src.has_tensor and not jacobi:
                s, ok = slope_cells(N, coh3, Cp, n_, P['tensor']); fb = ~ok & act; s = np.where(ok, s, np.clip(s_fb, -P['tensor']['s_max'], P['tensor']['s_max'])); st['fallback'][L] = float(fb.sum() / max(1, act.sum()))
            else: s = s_fb
            if jacobi or step == 0: s = np.zeros(U)
            p = np.clip(step * s, -self.dmax, self.dmax) if pred is None else np.clip(pred[L], -self.dmax, self.dmax)
            Delta = np.minimum(self.dmax, np.floor(0.5 * d_comp[L]) - 1 - np.abs(p)); unres = act & (Delta < 1)
            solvP = P['solver'] | {'anchored_rs_frac': P['status']['anchored_rs_frac']}
            if step == 0 and not jacobi and 'lambda_y_seed' in P['solver']: solvP = solvP | {'lambda_y': P['solver']['lambda_y_seed']}          # DECL-E2E-2-A4 item 4
            h, r0, mg, hit, nc, vd, mk = solve_lamina(Rs, void, mask, tau, Cp, n_, p, Delta, act & ~unres, solvP, self.dmax)
            # status grammar
            S = P['status']; status = np.full(U, TERMINATED, np.int8); status[~act] = prev['status'][L][~act]; status[(status == TERMINATED) & ~act] = TERMINATED
            cand = act & ~unres & hit & (r0 >= S['anchored_rs_frac']); anch = cand & ((mg >= S['margin_min']) | (S['margin_min'] <= 0)); amb = cand & ~anch; br = act & ~unres & ~cand; st.setdefault('ncand2', [0.0] * 3)[L] = float((nc[cand] >= 2).mean()) if cand.any() else 0.0
            was_br = (prev['status'][L] == BRIDGED) | was_dorm; re_ok = runs_atleast(anch & (np.abs(h - p) <= S['reanchor_tol']), S['reanchor_cells']); stay = was_br & anch & ~re_ok; anch &= ~stay
            dorm = (stay | br | amb | unres) & was_dorm                                                                                      # a dormant cell stays dormant until it re-anchors
            br = (br | stay) & ~was_dorm; amb &= ~was_dorm; unres &= ~was_dorm; revived = was_dorm & anch
            run_b = np.where(br, prev['run_b'][L] + abs(step), 0); run_u = np.where(unres, prev['run_u'][L] + abs(step), 0)
            term_b = br & (prev['run_b'][L] + abs(step) > S['G_y_sections']); term_u = unres & (prev['run_u'][L] >= S['unresolved_sections']); term_gu = runs_longer(br, S['G_u_vox']) & br
            term_m = act & ~mk; term_v = br & vd
            h = np.where(br | unres | dorm, p, h)
            if dorm.any() and anch.any(): ua = np.nonzero(anch)[0]; h[dorm] = np.interp(np.nonzero(dorm)[0], ua, h[ua])                           # DECL-E2E-2-A4 item 5: dormant cells ride the lamina's anchored increments
            status[anch] = ANCHORED; status[amb] = AMBIGUOUS; status[br] = BRIDGED; status[unres] = UNRESOLVED; status[dorm] = DORMANT
            for m_, why in ((term_b, 'bridge_Gy'), (term_u, 'unresolved_limit'), (term_gu, 'bridge_Gu'), (term_m, 'mask_edge'), (term_v, 'void')):      # DECL-E2E-2-A3 item 1: non-identity causes -> DORMANT
                if m_.any(): status[m_] = DORMANT; self.ledger.append({'type': 'DORMANT', 'reason': why, 'lamina': LN[L], 'y': int(y), 'k': int(k), 'n_cells': int(m_.sum()), 'u_first': int(np.argmax(m_))})
            nd = (status == DORMANT) & ~dorm
            if nd.any() and anch.any(): ua = np.nonzero(anch)[0]; h[nd] = np.interp(np.nonzero(nd)[0], ua, h[ua])
            if revived.any(): self.ledger.append({'type': 'REVIVED', 'lamina': LN[L], 'y': int(y), 'k': int(k), 'n_cells': int(revived.sum())})
            st.setdefault('revived', [None] * 3)[L] = revived
            C_new = prev['C'][L] + h[:, None] * n_; C_new[~act] = prev['C'][L][~act]; tn, nn = frame(C_new, self.sig)
            clean_prev = prev.get('clean', [np.ones(U, bool)] * 3)[L]; st.setdefault('clean', [None] * 3)[L] = clean_prev & (status != DORMANT) & (status != TERMINATED)     # DECL-E2E-2-A5 item 1
            st['C'][L] = C_new; st['t'][L] = tn; st['n'][L] = nn; st['status'][L] = status; st['rs'][L] = r0.astype(np.float32); st['margin'][L] = mg.astype(np.float32); st['s'][L] = s.astype(np.float32); st['inc'][L] = np.where(act, h, 0.0).astype(np.float32); st['run_b'][L] = run_b.astype(np.int32); st['run_u'][L] = run_u.astype(np.int32)
        # I1 order / separation on signed twin distances along n_T; I2 bridging support
        nT = st['n'][0]; dA = np.einsum('ij,ij->i', st['C'][1] - st['C'][0], nT); dB = np.einsum('ij,ij->i', st['C'][2] - st['C'][0], nT); rh = rho_of(st['C'][0], self.sig)
        actT = st['status'][0] < TERMINATED; actT &= st['status'][0] != UNTRACKED; presA = (st['status'][1] != UNTRACKED) & (st['status'][1] != TERMINATED); presB = (st['status'][2] != UNTRACKED) & (st['status'][2] != TERMINATED)
        rcA = presA & (rh < np.abs(dA)); rcB = presB & (rh < np.abs(dB)); testA = presA & actT & ~rcA; testB = presB & actT & ~rcB; sep = P['status']['separation']
        swapA = testA & (dA <= 0); mergeA = testA & (dA > 0) & (dA < sep); swapB = testB & (dB >= 0); mergeB = testB & (dB < 0) & (dB > -sep)
        for m_, typ, L in ((swapA, 'SWAP', 1), (mergeA, 'MERGE', 1), (swapB, 'SWAP', 2), (mergeB, 'MERGE', 2)):
            if m_.any():
                st['status'][0][m_] = TERMINATED; st['status'][L][m_] = TERMINATED; d_ = dA if L == 1 else dB
                for u in np.nonzero(m_)[0][:50]: self.ledger.append({'type': typ, 'lamina': LN[L], 'u': int(u), 'y': int(y), 'k': int(k), 'd_signed': round(float(d_[u]), 2), 'rs_T': round(float(st['rs'][0][u]), 3), 'rs_twin': round(float(st['rs'][L][u]), 3)})
                if m_.sum() > 50: self.ledger.append({'type': typ + '_MORE', 'lamina': LN[L], 'y': int(y), 'k': int(k), 'n_cells': int(m_.sum())})
        brT = st['status'][0] == BRIDGED; anyPres = presA | presB; anyAnch = (presA & (st['status'][1] == ANCHORED)) | (presB & (st['status'][2] == ANCHORED)); i2_fail = brT & anyPres & ~anyAnch        # DECL-E2E-2-A4 item 6
        if i2_fail.any(): st['status'][0][i2_fail] = DORMANT; self.ledger.append({'type': 'DORMANT', 'reason': 'I2_bridge_without_anchored_twins', 'lamina': 'T', 'y': int(y), 'k': int(k), 'n_cells': int(i2_fail.sum())})
        tJ = max(4.0, abs(float(step))) if step else None; jumps = {}                                                                         # DECL-E2E-2-A3 item 2: I5 twin-distance continuity
        if tJ is not None and 'dA' in prev:
            for L, d_, dp in ((1, dA, prev['dA']), (2, dB, prev['dB'])):
                bothA = (st['status'][0] == ANCHORED) & (st['status'][L] == ANCHORED) & (prev['status'][0] == ANCHORED) & (prev['status'][L] == ANCHORED) & np.isfinite(dp) & (presA if L == 1 else presB)
                dd = np.abs(d_ - dp); jumps[LN[L]] = {'n': int(bothA.sum()), 'p50_p90_p99': [round(float(v), 2) for v in np.percentile(dd[bothA], [50, 90, 99])] if bothA.sum() >= 10 else None}
                tj = bothA & (dd > tJ)
                if tj.any():
                    st['status'][0][tj] = TERMINATED; st['status'][L][tj] = TERMINATED; jumps[LN[L]]['events'] = int(tj.sum())
                    for u in np.nonzero(tj)[0][:30]: self.ledger.append({'type': 'TWIN-JUMP', 'lamina': LN[L], 'u': int(u), 'y': int(y), 'k': int(k), 'd_prev': round(float(dp[u]), 2), 'd_now': round(float(d_[u]), 2)})
                    if tj.sum() > 30: self.ledger.append({'type': 'TWIN-JUMP_MORE', 'lamina': LN[L], 'y': int(y), 'k': int(k), 'n_cells': int(tj.sum())})
        st['twin_jumps'] = jumps
        st['dA'] = np.where(presA, dA, np.nan).astype(np.float32); st['dB'] = np.where(presB, dB, np.nan).astype(np.float32); st['ray_cross'] = (rcA | rcB); st['rho'] = rh.astype(np.float32)
        # I4 tangent texture: Z_same vs the previous row at the same u; null = twin swap pooled over the row; cut only where the row's power >= 0.8
        tex = M; half = P['I4']['half']; vec = [texture(tex, st['C'][L] - o, st['t'][L], half) for L in range(3)]; zs = np.full(U, np.nan, np.float32); thr = np.nan; power = np.nan; verified = st['status'][0] == ANCHORED; i4_fail = np.zeros(U, bool); i4_tested = False    # DECL-E2E-2-A3 item 3: texture on the tilt-corrected mean
        memP = prev.get('vecT_mem', prev.get('vecT')); fails_prev = prev.get('i4_fails', np.zeros(U, np.int8))
        if memP is not None and not jacobi:
            zs = zncc(vec[0], memP).astype(np.float32); nullv = np.concatenate([zncc(vec[0], vec[1])[presA], zncc(vec[0], vec[2])[presB]])
            if nullv.size >= 50:
                thr = float(np.percentile(nullv, 95)); strong = (st['status'][0] == ANCHORED) & (st['margin'][0] >= P['I4']['margin_for_power'])
                if strong.sum() >= 20:
                    power = float((zs[strong] > thr).mean()); i4_tested = True
                    if power >= P['I4']['power_min']: i4_fail = (st['status'][0] == ANCHORED) & ~(zs > thr); verified &= ~i4_fail
                    if i4_fail.any(): self.ledger.append({'type': 'I4_FAIL', 'lamina': 'T', 'y': int(y), 'k': int(k), 'n_cells': int(i4_fail.sum()), 'power': round(power, 3), 'thr': round(thr, 3)})
        fails = np.where(i4_fail, fails_prev + 1, 0).astype(np.int8) if i4_tested else fails_prev.copy()                                           # DECL-E2E-2-A4 item 7: consecutive tested failures
        i4_term = fails >= P['I4'].get('terminate_after_fails', 99)
        if i4_term.any(): st['status'][0][i4_term] = TERMINATED; verified &= ~i4_term; self.ledger.append({'type': 'I4_TERMINATE', 'lamina': 'T', 'y': int(y), 'k': int(k), 'n_cells': int(i4_term.sum())})
        st['i4_fails'] = fails
        alpha = P['I4'].get('memory_alpha', 1.0); anchT = st['status'][0] == ANCHORED; revT_ = st.get('revived', [np.zeros(U, bool)] * 3)[0]
        if memP is None or alpha >= 1.0: mem = vec[0].copy()
        else:
            mem = memP.copy(); upd = anchT & ~(revT_ if revT_ is not None else False); mem[upd] = (1 - alpha) * memP[upd] + alpha * vec[0][upd]
            if revT_ is not None and revT_.any(): mem[revT_] = vec[0][revT_]
            mem = mem - mem.mean(1, keepdims=True); mem = mem / (mem.std(1, keepdims=True) + 1e-6)
        st['vecT_mem'] = mem
        revT = st.get('revived', [np.zeros(U, bool)] * 3)[0]
        if revT is not None and revT.any(): verified &= ~(revT & ~(i4_tested & (zs > thr) if i4_tested else np.zeros(U, bool)))
        for L in range(3): st['clean'][L] &= (st['status'][L] != DORMANT) & (st['status'][L] != TERMINATED)
        verified &= st['clean'][0]
        st['vecT'] = vec[0]; st['zsame'] = zs; st['i4_thr'] = thr; st['i4_power'] = power; st['verified'] = verified; st['i4_fail'] = i4_fail; st['i4_tested'] = i4_tested; st['revived_T'] = revT if revT is not None else np.zeros(U, bool)
        # nulls (V2): the acceptance statistic, G5-on-M and Z_same for T, C1 (between laminae), C2 (twin A), C3 (random in-tube)
        nul = self.null_stats(Rs, M, mask, tex, tau, st, prev, o, presA) if self.nulls else {}
        rec = {'tag': tag, 'y': int(y), 'k': int(k), 'jacobi': jacobi, 'corrected': corr, 'bbox': list(bb), 'px': int((bb[1] - bb[0]) * (bb[3] - bb[2])), 'tau_block': round(float(tau), 5), 'tau_row': round(float(tau_row), 5), 'secs': round(time.time() - t0, 2), 'rss_gb': round(rss_gb(), 2)}
        for L in range(3):
            s_ = st['status'][L]; rec[LN[L]] = {SNAME[i]: int((s_ == i).sum()) for i in range(7)}; rec[LN[L]]['anchored_frac'] = round(float((s_ == ANCHORED).mean()), 4); rec[LN[L]]['fallback_frac'] = round(st['fallback'][L], 4); rec[LN[L]]['mean_abs_inc'] = round(float(np.abs(st['inc'][L][s_ == ANCHORED]).mean()) if (s_ == ANCHORED).any() else float('nan'), 3)
        a = np.abs(st['s'][0]); bins = [(0, 0.25), (0.25, 0.5), (0.5, 1.01)]; rec['unresolved_frac_by_tilt'] = {f'{lo}-{hi}': (round(float((st['status'][0][(a >= lo) & (a < hi)] == UNRESOLVED).mean()), 4) if ((a >= lo) & (a < hi)).any() else None) for lo, hi in bins}
        rec.update({'identity_verified_frac': round(float(verified.mean()), 4), 'clean_anchored_frac_T': round(float((st['clean'][0] & (st['status'][0] == ANCHORED)).mean()), 4), 'open_side_frac': {'A': round(float(1 - presA.mean()), 4), 'B': round(float(1 - presB.mean()), 4)}, 'ray_cross_frac': round(float(st['ray_cross'].mean()), 4), 'swap_merge_cells': int((swapA | mergeA | swapB | mergeB).sum()), 'i2_dormant': int(i2_fail.sum()), 'twin_jumps': jumps, 'revived_T': int(st['revived_T'].sum()), 'revived_unverified_T': int((st['revived_T'] & ~verified & (st['status'][0] == ANCHORED)).sum()), 'I4': {'power': None if np.isnan(power) else round(power, 3), 'thr': None if np.isnan(thr) else round(thr, 3), 'tested': i4_tested, 'fail_cells': int(i4_fail.sum()), 'terminated_cells': int(i4_term.sum()), 'ply_frac_ncand2_T': round(st.get('ncand2', [0.0] * 3)[0], 4), 'median_zsame_T': None if np.all(np.isnan(zs)) else round(float(np.nanmedian(zs)), 3)}, 'nulls': nul, 's_ok_frac_dense': round(self.ctx.get('s_ok_frac', float('nan')), 3) if self.src.has_tensor else None, 'dcomp_T_p10_50': [round(float(np.percentile(d_comp[0], 10)), 1), round(float(np.percentile(d_comp[0], 50)), 1)]})
        self.records.append(rec)
        if self.ov_every and (k % self.ov_every == 0): self.overlay(M, st, o, os.path.join(self.out, f'overlay_k{k:+03d}{tag}.png'))
        if self.verbose: print(f"row k={k:+d} y={y} T anch {rec['T']['anchored_frac']:.3f} ver {rec['identity_verified_frac']:.3f} A {rec['A']['anchored_frac']:.3f} B {rec['B']['anchored_frac']:.3f} unres {rec['T']['UNRESOLVED']} br {rec['T']['BRIDGED']} term {rec['T']['TERMINATED']} I4 {rec['I4']['power']} {rec['secs']}s", flush=True)
        return st
    def dcomp(self, prev):
        dA = np.abs(np.where(np.isfinite(prev['dA']), prev['dA'], OPEN)); dB = np.abs(np.where(np.isfinite(prev['dB']), prev['dB'], OPEN)); return [np.minimum(dA, dB), dA, dB]
    def accept_stat(self, Rs, void, tau, pts, n, Delta):
        V = np.arange(-Delta, Delta + 1).astype(np.float64); q = pts[:, None, :] + V[None, :, None] * n[:, None, :]; rs = sample(Rs, q) / tau * inside(Rs.shape, q)
        lm = (rs >= np.roll(rs, 1, 1)) & (rs >= np.roll(rs, -1, 1)) & (rs >= 0.5); lm[:, 0] = rs[:, 0] >= 0.5; lm[:, -1] = rs[:, -1] >= 0.5; return float(lm.any(1).mean())
    def g5_stat(self, M, pts, n):
        Mf = M.astype(np.float32); c = sample(Mf, pts); a = sample(Mf, pts + 6 * n); b = sample(Mf, pts - 6 * n); return float(((c > a) & (c > b)).mean())
    def null_stats(self, Rs, M, mask, tex, tau, st, prev, o, presA):
        out = {}; rng = np.random.default_rng(int(st['y'])); void = np.zeros_like(mask)
        okT = (st['status'][0] != TERMINATED) & (st['status'][0] != UNTRACKED); nT = st['n'][0]; CT = st['C'][0] - o
        sets = {'T': (CT[okT], nT[okT])}
        m1 = okT & presA; sets['C1_between'] = ((CT + 0.5 * st['dA'][:, None] * nT)[m1], nT[m1]); sets['C2_twinA'] = ((st['C'][1] - o)[m1], st['n'][1][m1])
        zz, xx = np.nonzero(mask); 
        if len(zz) > 0:
            i = rng.integers(0, len(zz), 2000); pr = np.stack([zz[i], xx[i]], 1).astype(np.float64); th = rng.uniform(0, np.pi, 2000); sets['C3_random'] = (pr, np.stack([np.sin(th), np.cos(th)], 1))
        for key, (pts, n) in sets.items():
            if len(pts) < 20: continue
            out[key] = {'n': int(len(pts)), 'accept_d4': round(self.accept_stat(Rs, void, tau, pts, n, 4), 4), 'accept_d12': round(self.accept_stat(Rs, void, tau, pts, n, 12), 4), 'g5_on_M': round(self.g5_stat(M, pts, n), 4)}
        if 'tex_prev' in prev and 'vecT' in prev and not np.all(np.isnan(st['zsame'])):
            if 'T' in out and okT.any(): out['T']['median_zsame'] = round(float(np.nanmedian(st['zsame'][okT])), 3)
            tp, bbp = prev['tex_prev'], prev['bb']; op = np.array([bbp[0], bbp[2]], np.float64)
            if m1.sum() >= 20:
                c1_now = (st['C'][0] + 0.5 * st['dA'][:, None] * nT)[m1]; c1_prev = (prev['C'][0] + 0.5 * np.nan_to_num(prev['dA'], nan=OPEN)[:, None] * prev['n'][0])[m1]
                v_now = texture(tex, c1_now - o, st['t'][0][m1], self.P['I4']['half']); v_prev = texture(tp, c1_prev - op, prev['t'][0][m1], self.P['I4']['half']); out.setdefault('C1_between', {})['median_zsame'] = round(float(np.median(zncc(v_now, v_prev))), 3)
            if 'C3_random' in sets:
                pr, nr = sets['C3_random']; tr = np.stack([-nr[:, 1], nr[:, 0]], 1); v_now = texture(tex, pr, tr, self.P['I4']['half']); v_prev = texture(tp, pr + o - op, tr, self.P['I4']['half']); out.setdefault('C3_random', {})['median_zsame'] = round(float(np.median(zncc(v_now, v_prev))), 3)
        st['tex_prev'] = tex; return out
    def overlay(self, M, st, o, path, scale=4):
        try:
            from PIL import Image, ImageDraw
        except Exception: return
        img = Image.fromarray(M[::scale, ::scale]).convert('RGB'); dr = ImageDraw.Draw(img); cols = {0: (255, 200, 0), 1: (255, 60, 60), 2: (60, 120, 255)}
        for L in range(3):
            C = (st['C'][L] - o) / scale; s_ = st['status'][L]
            for i in range(0, len(C), 2):
                if s_[i] in (UNTRACKED,): continue
                c = cols[L] if s_[i] == ANCHORED else tuple(int(v * 0.45) for v in cols[L]); dr.point((float(C[i, 1]), float(C[i, 0])), fill=c)
        img.save(path)
    # ---------------------------------------------------------------- seed row
    def seed(self, nulls_first=False):
        """Seed row: fields with s = 0, tau fixed from the in-tube Rs, twins by the ray search, the three laminae solved about their
        curves (p = 0); in RAW mode a second pass with the tensor slope (V12 ablation recorded)."""
        C0 = self.seed_curve; t0, n0 = frame(C0, self.sig); U = self.U; P = self.P; st0 = {'k': 0, 'y': self.seed_y, 'C': [C0, C0.copy(), C0.copy()], 'n': [n0] * 3, 't': [t0] * 3, 'status': [np.full(U, ANCHORED, np.int8), np.full(U, UNTRACKED, np.int8), np.full(U, UNTRACKED, np.int8)], 'inc': [np.zeros(U, np.float32)] * 3, 'run_b': [np.zeros(U, np.int32)] * 3, 'run_u': [np.zeros(U, np.int32)] * 3, 'dA': np.full(U, np.nan, np.float32), 'dB': np.full(U, np.nan, np.float32)}
        bb = self.bbox(st0); M, mask, tex, Rs, FZ, FX, void, tau_row, _ = self.fields(self.seed_y, bb, corrected=False); o = np.array([bb[0], bb[2]], np.float64); self.seed_fields = {'bb': bb, 'M': M, 'mask': mask, 'tex': tex, 'Rs': Rs, 'FZ': FZ, 'FX': FX, 'void': void, 'tau_row': tau_row, 'C0': C0, 'n0': n0, 't0': t0}
        dA, dB = find_twins(Rs, self.tau, C0 - o, n0, P['twins']); fa, fb = np.isfinite(dA), np.isfinite(dB); u = np.arange(U)
        dAf = np.interp(u, u[fa], dA[fa]) if fa.sum() >= 2 else np.full(U, OPEN); dBf = np.interp(u, u[fb], dB[fb]) if fb.sum() >= 2 else np.full(U, -OPEN)
        st0['C'][1] = C0 + dAf[:, None] * n0; st0['C'][2] = C0 + dBf[:, None] * n0; st0['status'][1][fa] = ANCHORED; st0['status'][2][fb] = ANCHORED; st0['dA'] = np.where(fa, dA, np.nan).astype(np.float32); st0['dB'] = np.where(fb, dB, np.nan).astype(np.float32)
        for L in (1, 2): st0['t'][L], st0['n'][L] = frame(st0['C'][L], self.sig)
        self.seed_info = {'tau': float(self.tau), 'tau_row_seed': float(tau_row), 'bbox': list(bb), 'twin_found_frac': {'A': round(float(fa.mean()), 4), 'B': round(float(fb.mean()), 4)}, 'dA_p10_50_90': [round(float(v), 1) for v in np.nanpercentile(dA, [10, 50, 90])] if fa.any() else None, 'dB_p10_50_90': [round(float(v), 1) for v in np.nanpercentile(dB, [10, 50, 90])] if fb.any() else None, 'dcomp_p10_25_50': [round(float(v), 1) for v in np.percentile(np.minimum(np.abs(np.where(fa, dA, OPEN)), np.abs(np.where(fb, dB, OPEN))), [10, 25, 50])], 'rho_frac_below': {str(r): round(float((rho_of(C0, self.sig) < r).mean()), 3) for r in (20, 28, 48, 144)}, 'length_vox': int(U)}
        if self.P['fields'].get('gate', 'adaptive') == 'adaptive':                                                        # DECL-E2E-2-A1 item 3: the d = 22 gate beside the adaptive one
            Rs22, _, _, _, _, tau22 = sheet_fields(M, mask); dA22, dB22 = find_twins(Rs22, tau22, C0 - o, n0, P['twins']); acc22 = self.accept_stat(Rs22, void, tau22, C0 - o, n0, 4); acc_ad = self.accept_stat(Rs, void, self.tau, C0 - o, n0, 4)
            self.ablation['gate_d22_vs_adaptive_seed'] = {'accept_d4_T_d22': round(acc22, 4), 'accept_d4_T_adaptive': round(acc_ad, 4), 'tau_d22': float(tau22), 'tau_adaptive': float(self.tau), 'twin_found_frac_d22': {'A': round(float(np.isfinite(dA22).mean()), 4), 'B': round(float(np.isfinite(dB22).mean()), 4)}, 'dA_p10_50_90_d22': [round(float(v), 1) for v in np.nanpercentile(dA22, [10, 50, 90])] if np.isfinite(dA22).any() else None, 'dB_p10_50_90_d22': [round(float(v), 1) for v in np.nanpercentile(dB22, [10, 50, 90])] if np.isfinite(dB22).any() else None}; del Rs22
        self.tau_fixed = self.tau; st1 = self.solve_row(st0, self.seed_y, 0, corrected=False, tag='_seed_pass1'); self.ablation['seed_pass1_s0'] = {'anchored_T': self.records[-1]['T']['anchored_frac'], 'tau': float(self.tau)}
        if self.src.has_tensor:
            st1['k'] = 0; st2 = self.solve_row(st1, self.seed_y, 0, corrected=True, tag='_seed_pass2'); self.ablation['seed_pass2_tensor'] = {'anchored_T': self.records[-1]['T']['anchored_frac'], 'tau_row': self.records[-1]['tau_row'], 's_ok_frac_dense': self.records[-1]['s_ok_frac_dense']}; st1 = st2
        st1['k'] = 0; self.rows[0] = st1; return st1
    # ---------------------------------------------------------------- sweeps and refinement
    def sweep(self, rows_pos, rows_neg):
        seed = self.rows[0]
        for k in range(1, rows_pos + 1): self.rows[k] = self.solve_row(self.rows[k - 1], self.seed_y + k * self.dy, k)
        for k in range(-1, -rows_neg - 1, -1): self.rows[k] = self.solve_row(self.rows[k + 1], self.seed_y + k * self.dy, k)
    def jacobi(self):
        """One Jacobi refinement pass: every interior row re-solved about its own solution with the prediction = the mean of its two
        neighbours projected on its rays; the fraction of cells moving > 1 vox is recorded."""
        ks = sorted(self.rows); moved = []; new = {}
        for k in ks:
            if (k - 1) not in self.rows or (k + 1) not in self.rows: new[k] = self.rows[k]; continue
            cur = self.rows[k]; pred = []
            for L in range(3): mid = 0.5 * (self.rows[k - 1]['C'][L] + self.rows[k + 1]['C'][L]); pred.append(np.einsum('ij,ij->i', mid - cur['C'][L], cur['n'][L]))
            st = self.solve_row(cur, cur['y'], k, corrected=True, pred=pred, jacobi=True, tag='_jacobi'); st['vecT'] = cur.get('vecT'); st['zsame'] = cur['zsame']; st['i4_power'] = cur['i4_power']; st['i4_fail'] = cur['i4_fail']; st['verified'] = (st['status'][0] == ANCHORED) & ~cur['i4_fail']
            st['s'] = cur['s']; st['inc'] = cur['inc']; st['fallback'] = cur['fallback']; st['revived_T'] = cur.get('revived_T'); st['twin_jumps'] = cur.get('twin_jumps', {}); st['vecT_mem'] = cur.get('vecT_mem'); st['i4_fails'] = cur.get('i4_fails'); st['clean'] = cur.get('clean'); st['verified'] = (st['status'][0] == ANCHORED) & ~cur['i4_fail'] & cur['clean'][0]                                              # sweep diagnostics are kept; the pass refines positions only
            moved.append(float((np.abs(np.einsum('ij,ij->i', st['C'][0] - cur['C'][0], cur['n'][0])) > 1.0).mean())); new[k] = st
        self.rows = new; self.jacobi_moved = {'rows': len(moved), 'frac_moved_gt1_mean': round(float(np.mean(moved)), 4) if moved else None}
    # ---------------------------------------------------------------- outputs
    def export(self, cfg_decl='DECL-E2E-2'):
        ks = sorted(self.rows); U = self.U; ys = [self.rows[k]['y'] for k in ks]; Zs = np.full((len(ks), U), np.nan, np.float32); Xs = np.full((len(ks), U), np.nan, np.float32); status = np.zeros((len(ks), 3, U), np.int8); H = np.zeros((len(ks), 3, U, 2), np.float32)
        Zr = np.full((len(ks), U), np.nan, np.float32); Xr = Zr.copy(); clean = np.zeros((len(ks), U), bool)
        rs = np.zeros((len(ks), 3, U), np.float16); mg = np.zeros((len(ks), 3, U), np.float16); sl = np.zeros((len(ks), 3, U), np.float16); inc = np.zeros((len(ks), 3, U), np.float16); dA = np.full((len(ks), U), np.nan, np.float32); dB = dA.copy(); zs = dA.copy(); ver = np.zeros((len(ks), U), bool); rc = ver.copy(); rh = dA.copy(); rev = ver.copy()
        for i, k in enumerate(ks):
            st = self.rows[k]; cl = st.get('clean', [np.ones(U, bool)] * 3)[0]; a = (st['status'][0] == ANCHORED) & cl; arv = (st['status'][0] == ANCHORED) & ~cl; Cl0 = st['C'][0] + self.origin; Zs[i, a] = Cl0[a, 0]; Xs[i, a] = Cl0[a, 1]; Zr[i, arv] = Cl0[arv, 0]; Xr[i, arv] = Cl0[arv, 1]; clean[i] = cl
            for L in range(3): status[i, L] = st['status'][L]; H[i, L] = st['C'][L] + self.origin; rs[i, L] = st['rs'][L]; mg[i, L] = st['margin'][L]; sl[i, L] = st['s'][L]; inc[i, L] = st['inc'][L]
            dA[i], dB[i], zs[i], ver[i], rc[i], rh[i] = st['dA'], st['dB'], st['zsame'], st['verified'], st['ray_cross'], st['rho']; rev[i] = st.get('revived_T', np.zeros(U, bool))
        assert np.all(np.isfinite(Zs) == ((status[:, 0] == ANCHORED) & clean)), 'export must hold CLEAN ANCHORED cells only'
        cells = np.arange(0, U, 4); np.savez_compressed(os.path.join(self.out, 'surface.npz'), Z=Zs[:, cells], X=Xs[:, cells], U=cells.astype(np.float32), ys=np.array(ys)); np.savez_compressed(os.path.join(self.out, 'surface_revived.npz'), Z=Zr[:, cells], X=Xr[:, cells], U=cells.astype(np.float32), ys=np.array(ys)); 
        np.savez_compressed(os.path.join(self.out, 'grow_status.npz'), status=status, pos=H, rs_over_tau=rs, margin=mg, s=sl, inc=inc, dA=dA, dB=dB, zsame=zs, identity_verified=ver, revived=rev, clean=clean, ray_cross=rc, rho=rh, ys=np.array(ys), ks=np.array(ks), tau=self.tau)
        import tifffile; d = os.path.join(self.out, 'surface_tifxyz'); os.makedirs(d, exist_ok=True); c8 = np.arange(0, U, 8); fin = np.isfinite(Zs[:, c8]) & np.isfinite(Xs[:, c8])
        Xg = np.where(fin, Xs[:, c8], -1).astype(np.float32); Zg = np.where(fin, Zs[:, c8], -1).astype(np.float32); Yg = np.where(fin, np.array(ys, np.float32)[:, None], -1).astype(np.float32)
        for nm, G in (('x', Xg), ('y', Yg), ('z', Zg)): tifffile.imwrite(os.path.join(d, f'{nm}.tif'), G, metadata=None, software=False)
        json.dump({'scale': [1 / 8.0, 1 / float(self.dy)], 'frame': 'level-0 voxels (x, y, z)' if self.origin.any() else 'block voxels (x, y, z)', 'declaration': cfg_decl, 'cells': 'ANCHORED only'}, open(os.path.join(d, 'meta.json'), 'w'))
        json.dump(self.ledger, open(os.path.join(self.out, 'ledger.json'), 'w'), indent=0, default=J)
        # gap-length histogram along u (non-ANCHORED runs inside the tracked span) and bridged-run assertion
        gl = []
        for i in range(len(ks)):
            b = status[i, 0] == BRIDGED; lab, n = ndi.label(~(status[i, 0] == ANCHORED)); 
            if n: gl += list(np.bincount(lab.ravel())[1:])
            assert not runs_longer(b, self.P['status']['G_u_vox']).any(), 'bridged run along u longer than G_u'
        gl = np.array(gl) if gl else np.zeros(1)
        summ = {'rows': len(ks), 'ys': [int(v) for v in ys], 'U_cells': int(U), 'tau': float(self.tau), 'seed': getattr(self, 'seed_info', {}), 'ablation_seed': self.ablation, 'jacobi': getattr(self, 'jacobi_moved', None),
                'per_row': self.records, 'anchored_frac_T_per_row': {int(ys[i]): round(float((status[i, 0] == ANCHORED).mean()), 4) for i in range(len(ks))}, 'clean_anchored_frac_T_per_row': {int(ys[i]): round(float(((status[i, 0] == ANCHORED) & clean[i]).mean()), 4) for i in range(len(ks))}, 'identity_verified_frac_per_row': {int(ys[i]): round(float(ver[i].mean()), 4) for i in range(len(ks))},
                'bridged_frac_of_nonterminated': round(float((status[:, 0] == BRIDGED).sum() / max(1, ((status[:, 0] != TERMINATED) & (status[:, 0] != UNTRACKED)).sum())), 4), 'gap_len_hist': {'p50': float(np.median(gl)), 'p90': float(np.percentile(gl, 90)), 'max': int(gl.max()), 'n': int(len(gl))},
                'ledger_counts': {t: sum(1 for e in self.ledger if e['type'] == t) for t in sorted({e['type'] for e in self.ledger})}, 'swap_merge_cells_total': int(sum(r['swap_merge_cells'] for r in self.records if not r['jacobi'])), 'twin_jump_cells_total': int(sum(sum(v.get('events', 0) for v in r['twin_jumps'].values()) for r in self.records if not r['jacobi'])), 'revived_cells_total': int(rev.sum()), 'dormant_frac_mean': round(float((status[:, 0] == DORMANT).mean()), 4), 'rss_gb_peak': round(rss_gb(), 2)}
        json.dump(summ, open(os.path.join(self.out, 'grow_checks.json'), 'w'), indent=1, default=J); return summ

def seed_from_e2e(npz, y, origin, sigma_u):
    S = np.load(npz); i = int(np.nonzero(S['ys'] == y)[0][0]); C = resample(S['Z'][i], S['X'][i], 1.0) - np.array(origin, np.float64); return smooth(C, sigma_u)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['means', 'raw']); ap.add_argument('params'); ap.add_argument('out'); ap.add_argument('--store'); ap.add_argument('--ys', type=int, nargs='*'); ap.add_argument('--seed_npz'); ap.add_argument('--seed_npy'); ap.add_argument('--seed_y', type=int, required=True)
    ap.add_argument('--origin', type=int, nargs=2, default=[0, 0]); ap.add_argument('--block'); ap.add_argument('--rows', type=int, nargs=2, default=[47, 48]); ap.add_argument('--no_jacobi', action='store_true'); ap.add_argument('--no_nulls', action='store_true'); ap.add_argument('--cells', default=None, help='u0:u1 sub-range of seed cells')
    a = ap.parse_args(); P = json.load(open(a.params)); t0 = time.time()
    if a.mode == 'means':
        ys = sorted(a.ys) if a.ys else sorted(int(f[4:-4]) for f in os.listdir(a.store) if f.startswith('sec_')); src = MeansSource(a.store, ys); dy = ys[1] - ys[0]; seed = seed_from_e2e(a.seed_npz, a.seed_y, a.origin, P['sigma_u']); i0 = ys.index(a.seed_y); rows_pos, rows_neg = len(ys) - 1 - i0, i0
    else:
        src = BlockSource(a.block, P['n_avg']); dy = P['dy']; seed = smooth(np.load(a.seed_npy).astype(np.float64), P['sigma_u']); rows_neg, rows_pos = a.rows
    if a.cells: u0, u1 = [int(v) for v in a.cells.split(':')]; seed = seed[u0:u1]
    tr = Tracker(src, P, seed, a.seed_y, dy, a.out, origin=a.origin, nulls=not a.no_nulls); tr.seed(); tr.sweep(rows_pos, rows_neg)
    if not a.no_jacobi: tr.jacobi()
    summ = tr.export(); print(json.dumps({'rows': summ['rows'], 'tau': summ['tau'], 'anchored_T': summ['anchored_frac_T_per_row'], 'ledger': summ['ledger_counts'], 'secs': round(time.time() - t0), 'rss_gb': summ['rss_gb_peak']}))

if __name__ == '__main__': main()
