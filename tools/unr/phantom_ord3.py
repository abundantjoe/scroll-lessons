#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
ORD-3 phantom: stacked papyrus laminae at the scan's native 8.64 um voxel, written as a y-stack of xz sections for
testing a sheet-tracking operator that follows ONE target lamina T and its neighbours A = T+1 (+z) and B = T-1 (-z)
across y. Frame: block[y] is a (Z, X) section; lamina L is the height field z = z_L(y, x) (centreline), stacked along
+z, L = 0 lowest. Geometry only; nothing here is an ink or letter claim.
Intensities (uint8, like masked means): 0 outside the mask (top/bottom margins of 60 vox), air ~70 +- 10 (smooth),
papyrus 215 * base_L (base 0.8-1.0), ply gap ~120, voids ~40, crack interior ~30 with a bright 3-vox rim ~200; blur 1.0
on the material image, then column stripes, then noise 0.15 * 215 per voxel, clip [1, 255] in the mask.
Spec items (parameters and realised values in params.json):
 1 spacings: two-piece log-normal through p10/p50/p90 = 11/17.5/40 vox, clip [8, 60], stratified draw (a single
   log-normal fitted to p10/p90 alone has median 21, so the split law is used to honour all three declared quantiles)
 2 widths: 52 % thin plies 5-7 vox; 48 % full sheets 14 vox = two plies + a 1-2 vox dimmer gap (~120)
 3 tilt s_L(y, x) = dz/dy = s_common(y, x) + 0.2 beta_L s_own_L(y, x): smooth fields (sigma 231 vox in y and x, low-res
   noise + cubic upsample); |s_common| and each |s_own_L| are rank-mapped onto p10/p50/p90 = 0.075/0.34/1.0 (adjacent
   laminae of a roll move together, so the individual deviation is ~20 % of the common tilt); |s_L| capped at 1.0;
   z integrates s from the seed row y_seed = Y // 2. No crossing: if an adjacent pair gets closer than 8 vox at any (y, x)
   the own part of the lamina farther from T is scaled down (x0.7, then 0) until the minimum spacing is >= 8 everywhere.
   The stored s is the realised dz/dy of the truth (after the shear, before hops).
 4 in-section buckling b_L(x) = 70 % common + 30 % own slope-budgeted sinusoid sums (|b'| <= 0.6 by construction),
   curvature radius median 72 (f <= 1 calibration), own part scaled down until adjacent spacing >= 8 at the seed row
 5 open gaps along x (30-300 vox, 30 % > 132) about every 579 vox per section, persisting 40-200 sections (truth NaN)
 6 voids: dark soft-edged ellipsoids, 10 % of the mask area, sizes 20-120 vox (truth NaN inside)
 7 crack rims: 30 dark ellipses, semi-axes 25-100, random orientation, bright 3-vox rim (truth NaN inside)
 8 dark seams: every 116-463 vox of stack height one pair spacing widened to 30-60 vox
 9 one integer-spacing shear: a line at 30 deg to the z axis, same in every section; laminae on one side move up by one
   local spacing (lamina L lands on the slot of L+1); truth records (z_point, x_point, angle_deg, shift_side)
10 the target terminates for x in a 300-vox window and all y > y_t (truth NaN, air)
11 fibre texture 1 + 0.1 sin(2 pi x / P_L + phi_L(y)), P_L in [6, 12], phi a slow random walk along y
12 column stripes (1 + 0.05 g(x)), noise 0.15 * 215 after blur
13 injected hops: n_hops windows of 232 vox; for y beyond y_c the whole window content (all z) rolls by +d = one local
   T-A spacing (vacated rows = air); truth z += d there. Windows avoid the shear band and the termination window; windows
   of the same sweep direction are kept disjoint while x allows, then may overlap if their y_c differ by >= 40 (X = 2048
   cannot hold 20 disjoint 232-vox windows per direction); truth is cumulative where they overlap.
14 target T = lamina nearest z = Z/2 at the seed row.
usage: phantom_ord3.py <out_dir> [--Y 384 --Z 1024 --X 2048 --seed 0 --n_hops 40] [--no_preview]
outputs: block.npy uint8 (Y, Z, X) memmap written section by section; truth.npz (z, width, s, target, hops, shear, term,
mask_z, y_seed, ...); params.json; preview.png (seed section at 1/2 scale + x-mean along y)."""
import argparse, json, os, time
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import RectBivariateSpline
from scipy.special import ndtri

VOX_UM = 8.64
MARGIN, PAD, MINSP = 60, 20, 8.0
AIR, MAT, GAPV, VOIDV, CRACKV, RIMV = 70.0, 215.0, 120.0, 40.0, 30.0, 200.0
Q90 = 1.2815515655446004
SPEC = dict(spacing_q=(11.0, 17.5, 40.0), spacing_clip=(8.0, 60.0), thin_frac=0.52, thin_w=(5.0, 7.0), full_w=14.0,
            ply_gap=(1, 2), base=(0.8, 1.0), tilt_q=(0.075, 0.34, 1.0), tilt_sigma=231.0, tilt_cap=1.0, tilt_own=0.2,
            tilt_cell=58, rho_median=72.0, rho_thresh=48.0, rho_frac=0.37, slope_max=0.6,
            buckle_common=0.7, gap_len=(30, 132, 300), gap_long_frac=0.3, gap_every=579.0, gap_persist=(40, 200),
            void_frac=0.10, void_size=(20, 120), void_edge=3.0, n_cracks=30, crack_axes=(25, 100), crack_rim=3,
            seam_every=(116, 463), seam_width=(30, 60), shear_angle=30.0, term_width=300, hop_width=232, hop_ysep=40,
            fibre_P=(6.0, 12.0), fibre_amp=0.1, fibre_phase_sigma=0.02, stripe_amp=0.05, noise=0.15, blur=1.0,
            air_var=10.0, air_cell=64)


def tp_ppf(q, q3):
    """Two-piece log-normal (split normal in log space) through the quantiles p10/p50/p90 = q3."""
    p10, p50, p90 = q3; u = ndtri(np.asarray(q, np.float64))
    lo = (np.log(p50) - np.log(p10)) / Q90; hi = (np.log(p90) - np.log(p50)) / Q90
    return np.exp(np.log(p50) + np.where(u < 0, lo, hi) * u)


def smooth_fields(rng, n, Y, X, sigma, cell, sigma_n=0.0):
    """n smooth Gaussian fields (n, Y, X) float32 with pooled unit variance, correlation sigma (vox) in y and x and an
    optional Gaussian correlation across the field index; low-res noise, cubic upsample."""
    pad = 4; Yl = int(np.ceil(Y / cell)) + 2 * pad; Xl = int(np.ceil(X / cell)) + 2 * pad
    lo = ndi.gaussian_filter(rng.standard_normal((n, Yl, Xl)), (sigma_n, sigma / cell, sigma / cell), mode='reflect')
    lo /= lo.std(); yl = (np.arange(Yl) - pad) * cell; xl = (np.arange(Xl) - pad) * cell
    out = np.empty((n, Y, X), np.float32)
    for i in range(n): out[i] = RectBivariateSpline(yl, xl, lo[i])(np.arange(Y), np.arange(X))
    return out


def unit_profile(rng, X, lam_long=(150.0, 300.0), lam_short=(30.0, 60.0), n_long=2, n_short=2, frac_long=0.45):
    """Slope-budgeted sum of sinusoids (two long + two short log-uniform wavelengths; the short ones carry the sharp
    bends), normalised to max |p'| = 1 so that any convex mix of such profiles keeps the same slope bound."""
    x = np.arange(X, dtype=np.float64)
    k = 2 * np.pi / np.exp(np.r_[rng.uniform(np.log(lam_long[0]), np.log(lam_long[1]), n_long), rng.uniform(np.log(lam_short[0]), np.log(lam_short[1]), n_short)])
    w = rng.uniform(0.5, 1.5, n_long + n_short); w[:n_long] *= frac_long / w[:n_long].sum(); w[n_long:] *= (1 - frac_long) / w[n_long:].sum()
    p = ((w / k)[:, None] * np.sin(k[:, None] * x[None, :] + rng.uniform(0, 2 * np.pi, len(k))[:, None])).sum(0); p -= p.mean()
    return p / np.abs(np.gradient(p)).max()


def build_stack(rng, Z, sp):
    """Seed-row flat positions: spacings from the declared law (item 1; a shuffled stratified draw, so the few dozen
    realised spacings carry the law's quantiles) with dark seams every 116-463 vox (item 8)."""
    z_lo, z_hi = MARGIN, Z - MARGIN; z = [z_lo + PAD + rng.uniform(0, 10)]; spac, seams = [], []
    mean_law = float(np.clip(tp_ppf(np.linspace(0.0005, 0.9995, 2000), sp['spacing_q']), *sp['spacing_clip']).mean())
    m = int(np.ceil((z_hi - PAD - z[0]) / mean_law)) + 8
    pool = np.clip(tp_ppf((np.arange(m) + rng.random(m)) / m, sp['spacing_q']), *sp['spacing_clip']); rng.shuffle(pool); k = 0
    next_seam = z[0] + rng.uniform(*sp['seam_every'])
    while True:
        seam = z[-1] >= next_seam
        d = rng.uniform(*sp['seam_width']) if seam else float(pool[k] if k < m else np.clip(tp_ppf(rng.random(), sp['spacing_q']), *sp['spacing_clip']))
        if z[-1] + d > z_hi - PAD: break
        if seam: seams.append(len(z) - 1); next_seam = z[-1] + d + rng.uniform(*sp['seam_every'])
        else: k += 1
        z.append(z[-1] + d); spac.append(d)
    return np.array(z), np.array(spac), seams


def build_buckling(rng, z0, X, sp):
    """Item 4: b_L = slope_max f (wc c + wo beta_L o_L) with unit-slope profiles, so |b'| <= slope_max f <= slope_max;
    f <= 1 is set so the median curvature radius is rho_median when reachable; beta_L (own part) is reduced for the
    8-vox minimum spacing (the upper lamina of a too-close pair first, then the lower one)."""
    n = len(z0); wc = sp['buckle_common']; wo = 1 - wc; S = sp['slope_max']
    c = unit_profile(rng, X); o = np.stack([unit_profile(rng, X) for _ in range(n)]); beta = np.ones(n); f = 1.0
    prof = lambda: S * f * (wc * c[None, :] + wo * beta[:, None] * o)
    rho = lambda b: 1.0 / np.maximum(np.abs(np.gradient(np.gradient(b, axis=1), axis=1)), 1e-9)
    f = min(1.0, float(np.median(rho(prof())) / sp['rho_median']))
    n_iter = 0
    for n_iter in range(1, 2000):
        mins = np.diff(z0[:, None] + prof(), axis=0).min(axis=1); bad = np.where(mins < MINSP - 1e-3)[0]
        if len(bad) == 0: break
        for i in bad:
            L = i + 1 if beta[i + 1] > 0 else i
            beta[L] = 0.0 if beta[L] < 0.02 else beta[L] * 0.8
    b = prof(); r = rho(b)
    stats = dict(rho_q10_50_90=[float(v) for v in np.quantile(r, [0.1, 0.5, 0.9])], rho_lt48_frac=float((r < sp['rho_thresh']).mean()),
                 slope_max=float(np.abs(np.gradient(b, axis=1)).max()), beta_mean=float(beta.mean()), beta_min=float(beta.min()),
                 n_beta_reduced=int((beta < 1).sum()), f=float(f), noncross_iters=n_iter, amp_rms=float(b.std(axis=1).mean()),
                 min_spacing_seed_row=float(np.diff(z0[:, None] + b, axis=0).min()))
    return b.astype(np.float32), stats


def map_abs(field, q3, cap, rng, nsamp=200000):
    """Rank-map |field| onto the two-piece law (sign kept, in place) and cap."""
    flat = field.reshape(-1); samp = np.sort(np.abs(flat[rng.integers(0, flat.size, min(nsamp, flat.size))]))
    tgt = tp_ppf((np.arange(len(samp)) + 0.5) / len(samp), q3)
    m = np.interp(np.abs(field), samp, tgt); np.minimum(m, cap, out=m); field[...] = np.sign(field) * m


def build_tilt(rng, n, Y, X, zseed, T, sp):
    """Item 3: s_L = clip(s_common + 0.2 beta_L s_own_L); z_L integrates s_L from the seed row; beta_L is reduced
    (x0.7, then 0; the lamina farther from T first) until every adjacent pair stays >= 8 vox apart at every (y, x).
    Returns s (n, Y, X) float32, z (n, Y, X) float32 and the repair statistics."""
    q, cap, cell, sig, own = sp['tilt_q'], sp['tilt_cap'], sp['tilt_cell'], sp['tilt_sigma'], np.float32(sp['tilt_own'])
    sc = smooth_fields(rng, 1, Y, X, sig, cell)[0]; map_abs(sc, q, cap, rng)
    so = smooth_fields(rng, n, Y, X, sig, cell)
    for L in range(n): map_abs(so[L], q, cap, rng)
    beta = np.ones(n, np.float32); z = np.empty_like(so); ys = Y // 2
    def s_of(L): return np.clip(sc + own * beta[L] * so[L], -cap, cap)
    def integrate(L):
        sL = s_of(L); np.cumsum(sL, axis=0, out=z[L]); z[L] -= sL; z[L] -= z[L, ys:ys + 1, :].copy(); z[L] += zseed[L][None, :]
    for L in range(n): integrate(L)
    n_iter = 0
    for n_iter in range(1, 1000):
        mins = np.array([(z[L + 1] - z[L]).min() for L in range(n - 1)]); bad = np.where(mins < MINSP - 1e-3)[0]
        if len(bad) == 0: break
        changed = False
        for i in bad:
            far, near = (i + 1, i) if abs(i + 1 - T) > abs(i - T) else (i, i + 1)
            for L in (far, near):
                if beta[L] > 0: beta[L] = np.float32(0.0) if beta[L] < 0.1 else beta[L] * np.float32(0.7); integrate(L); changed = True; break
        if not changed: break
    for L in range(n): so[L] = s_of(L)
    mins = np.array([(z[L + 1] - z[L]).min() for L in range(n - 1)])
    stats = dict(own_weight=float(own), beta=[float(v) for v in beta], n_own_reduced=int((beta < 1).sum()), n_own_zero=int((beta == 0).sum()),
                 repair_iters=n_iter, min_spacing_realised=float(mins.min()), min_spacing_per_pair=[float(v) for v in mins])
    return so, z, stats


def bilinear_up(lo, Zq, Xq, cell):
    """(Zl, Xl) low-res grid (cell spacing, origin at -cell/2) -> (Zq, Xq) at 4-vox steps."""
    def idx(nq, nl):
        t = (np.arange(nq) * 4 + 2) / cell - 0.5; i0 = np.clip(np.floor(t).astype(int), 0, nl - 2); return i0, (t - i0).clip(0, 1)
    iz, wz = idx(Zq, lo.shape[0]); ix, wx = idx(Xq, lo.shape[1]); wz = wz[:, None].astype(np.float32); wx = wx[None, :].astype(np.float32)
    a = lo[iz][:, ix]; b = lo[iz + 1][:, ix]; c = lo[iz][:, ix + 1]; d = lo[iz + 1][:, ix + 1]
    return (a * (1 - wz) + b * wz) * (1 - wx) + (c * (1 - wz) + d * wz) * wx


def raster(img, zrow, width, pgap, mats, Z):
    """Composite each lamina over the image on its band of rows only (coverage model, per-column centreline)."""
    X = img.shape[1]; xx = np.arange(X)
    for L in range(zrow.shape[0]):
        zc = zrow[L]; ok = np.isfinite(zc)
        if not ok.any(): continue
        xs = xx[ok]; zc = zc[ok]; hw = width[L] / 2; K = int(np.ceil(hw + 1))
        rows = np.rint(zc).astype(np.int64)[None, :] + np.arange(-K, K + 1)[:, None]; dz = np.abs(rows - zc[None, :])
        cov = np.clip(hw - dz + 0.5, 0, 1); val = np.broadcast_to(mats[L][ok][None, :], rows.shape)
        if pgap[L] > 0: gc = np.clip(pgap[L] / 2 - dz + 0.5, 0, 1); val = val * (1 - gc) + GAPV * gc
        sel = (rows >= 0) & (rows < Z) & (cov > 0)
        r = rows[sel]; c = np.broadcast_to(xs[None, :], rows.shape)[sel]; cv = cov[sel]
        img[r, c] = img[r, c] * (1 - cv) + val[sel] * cv


def render_voids(img, voids, y, z_lo, z_hi, X, edge):
    """Dark soft-edged ellipsoid cross-sections; returns the number of covered in-mask voxels."""
    cover = 0
    for (yc, zc, xc, ry, rz, rx) in voids:
        t = 1 - ((y - yc) / ry) ** 2
        if t <= 0: continue
        f = np.sqrt(t); az, ax = rz * f, rx * f
        z0, z1 = max(z_lo, int(zc - az - 2)), min(z_hi, int(zc + az + 3)); x0, x1 = max(0, int(xc - ax - 2)), min(X, int(xc + ax + 3))
        if z1 <= z0 or x1 <= x0: continue
        rho = np.sqrt(((np.arange(z0, z1) - zc) / az)[:, None] ** 2 + ((np.arange(x0, x1) - xc) / ax)[None, :] ** 2)
        cov = np.clip((1 - rho) * min(az, ax) / edge + 0.5, 0, 1).astype(np.float32)
        sub = img[z0:z1, x0:x1]; sub *= (1 - cov); sub += VOIDV * cov; cover += int((cov > 0.5).sum())
    return cover


def render_cracks(img, cracks, y, z_lo, z_hi, X, rim):
    for (yc, zc, xc, ry, a, b, th) in cracks:
        t = 1 - ((y - yc) / ry) ** 2
        if t <= 0: continue
        f = np.sqrt(t); af, bf = a * f, b * f; R = max(af, bf) + rim + 2
        z0, z1 = max(z_lo, int(zc - R)), min(z_hi, int(zc + R + 1)); x0, x1 = max(0, int(xc - R)), min(X, int(xc + R + 1))
        if z1 <= z0 or x1 <= x0: continue
        dz = (np.arange(z0, z1) - zc)[:, None]; dx = (np.arange(x0, x1) - xc)[None, :]
        u = dz * np.cos(th) + dx * np.sin(th); v = -dz * np.sin(th) + dx * np.cos(th)
        inner = (u / af) ** 2 + (v / bf) ** 2 < 1; outer = (u / (af + rim)) ** 2 + (v / (bf + rim)) ** 2 < 1
        sub = img[z0:z1, x0:x1]; sub[outer & ~inner] = RIMV; sub[inner] = CRACKV


def nan_voids(z, voids, Y, X):
    for (yc, zc, xc, ry, rz, rx) in voids:
        y0, y1 = max(0, int(yc - ry)), min(Y, int(yc + ry) + 1); x0, x1 = max(0, int(xc - rx)), min(X, int(xc + rx) + 1)
        if y1 <= y0 or x1 <= x0: continue
        sub = z[:, y0:y1, x0:x1]
        r2 = ((np.arange(y0, y1) - yc) / ry)[None, :, None] ** 2 + ((np.arange(x0, x1) - xc) / rx)[None, None, :] ** 2 + ((sub - zc) / rz) ** 2
        sub[r2 < 1] = np.nan


def nan_cracks(z, cracks, Y, X, rim):
    for (yc, zc, xc, ry, a, b, th) in cracks:
        R = max(a, b) + rim; y0, y1 = max(0, int(yc - ry)), min(Y, int(yc + ry) + 1); x0, x1 = max(0, int(xc - R)), min(X, int(xc + R + 1))
        if y1 <= y0 or x1 <= x0: continue
        sub = z[:, y0:y1, x0:x1]; t = 1 - ((np.arange(y0, y1) - yc) / ry)[None, :, None] ** 2
        f = np.sqrt(np.maximum(t, 1e-6)); dz = sub - zc; dx = (np.arange(x0, x1) - xc)[None, None, :]
        u = dz * np.cos(th) + dx * np.sin(th); v = -dz * np.sin(th) + dx * np.cos(th)
        sub[((u / (a * f + rim)) ** 2 + (v / (b * f + rim)) ** 2 < 1) & (t > 0)] = np.nan


def place_hops(rng, n_hops, Y, X, forbid, sp):
    """Item 13 placement: the free x-range (outside the shear band and the termination window) is tiled with slots of
    hop_width (random offset per layer); layer 0 holds disjoint windows, further layers reuse the slots with y_c moved
    by >= hop_ysep per layer (jittered), so overlapping windows of one sweep direction stay separable in y."""
    W, ysep = sp['hop_width'], sp['hop_ysep']; hops = []; n_overlap = 0; free = []; cur = 0
    for a, b in sorted((max(0, int(a)), min(X, int(np.ceil(b)))) for a, b in forbid):
        if a > cur: free.append((cur, a))
        cur = max(cur, b)
    if cur < X: free.append((cur, X))
    slots = [(a, b) for a, b in free if b - a >= W]; n_slot = sum((b - a) // W for a, b in slots)
    ranges = {+1: (Y // 2 + 10, Y - 20), -1: (20, Y // 2 - 10)}
    for dirn in (+1, -1):
        lo, hi = ranges[dirn]; want = n_hops // 2 + (n_hops % 2 if dirn > 0 else 0)
        if hi < lo or n_slot == 0 or want == 0: continue
        n_layer = int(np.ceil(want / n_slot)); step = (hi - lo) / max(n_layer - 1, 1); jit = max(0.0, (step - ysep) / 2); placed = 0
        for k in range(n_layer):
            xs = []
            for a, b in slots:
                m = (b - a) // W; off = int(rng.integers(0, (b - a) - m * W + 1)); xs += [a + off + j * W for j in range(m)]
            rng.shuffle(xs)
            for x0 in xs:
                if placed >= want: break
                yc = int(rng.integers(lo, hi + 1)) if n_layer == 1 else int(np.clip(round(lo + k * step + rng.uniform(-jit, jit)), lo, hi))
                hops.append((x0, x0 + W, yc, 0, dirn)); n_overlap += int(k > 0); placed += 1
    return hops, n_overlap


def main():
    ap = argparse.ArgumentParser(description='ORD-3 lamina-stack phantom (see module docstring)')
    ap.add_argument('out_dir'); ap.add_argument('--Y', type=int, default=384); ap.add_argument('--Z', type=int, default=1024)
    ap.add_argument('--X', type=int, default=2048); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--n_hops', type=int, default=40)
    ap.add_argument('--no_preview', action='store_true')
    args = ap.parse_args(); sp = SPEC; Y, Z, X = args.Y, args.Z, args.X; rng = np.random.default_rng(args.seed)
    os.makedirs(args.out_dir, exist_ok=True); t_start = time.time()
    z_lo, z_hi = MARGIN, Z - MARGIN; y_seed = Y // 2; xx = np.arange(X)
    # --- items 1, 8: flat stack; item 2: widths; item 14: target
    z0, spac, seams = build_stack(rng, Z, sp); n = len(z0)
    if n < 3: raise SystemExit('stack too thin for a target with two neighbours (Z too small)')
    thin = rng.random(n) < sp['thin_frac']; width = np.where(thin, rng.uniform(*sp['thin_w'], n), sp['full_w']).astype(np.float32)
    pgap = np.where(thin, 0, rng.integers(sp['ply_gap'][0], sp['ply_gap'][1] + 1, n)); base = rng.uniform(*sp['base'], n)
    T = int(np.clip(np.argmin(np.abs(z0 - Z / 2)), 1, n - 2)); A, B = T + 1, T - 1
    # --- item 4: buckling at the seed row
    b, bstats = build_buckling(rng, z0, X, sp); zseed = z0[:, None].astype(np.float32) + b
    # --- item 3: tilt, integration along y from the seed row, no-crossing by scaling the own tilt part
    s, z, tstats = build_tilt(rng, n, Y, X, zseed, T, sp)
    # --- item 9: integer-spacing shear (lamina L takes the slot of L+1 where that slot lies on the shifted side)
    ang = np.radians(sp['shear_angle']); z_p = Z / 2; half = np.tan(ang) * (z_hi - z_lo) / 2 + 10
    x_p = float(rng.uniform(half + 100, X - half - 100)) if X > 2 * half + 200 else X / 2; side = int(rng.choice([-1, 1]))
    sp_top = z[-1] - z[-2]
    for L in range(n):
        dest = z[L + 1] if L + 1 < n else z[L] + sp_top
        sel = side * (np.cos(ang) * (xx - x_p)[None, :] - np.sin(ang) * (dest - z_p)) > 0
        np.copyto(z[L], dest, where=sel)
    shear_x = (x_p - half, x_p + half)
    # realised tilt = dz/dy of the truth (before NaNs and hops)
    for L in range(n): s[L, :-1] = z[L, 1:] - z[L, :-1]; s[L, -1] = s[L, -2]
    # --- item 10: termination window of the target
    term = (-1, -1, -1)
    if Y // 2 + 20 <= Y - 60:
        y_t = int(rng.integers(Y // 2 + 20, Y - 60 + 1)); forbid = [shear_x]
        for _ in range(2000):
            xt0 = int(rng.integers(0, X - sp['term_width'] + 1)); xt1 = xt0 + sp['term_width']
            if not any(xt0 < bb and aa < xt1 for aa, bb in forbid): term = (xt0, xt1, y_t); break
    forbid = [shear_x] + ([term[:2]] if term[0] >= 0 else [])
    # --- item 5: gaps along x
    gaps = []; n_gap_total = 0
    lam_g = X / sp['gap_every'] * Y / np.mean(sp['gap_persist'])
    for L in range(n):
        for _ in range(int(rng.poisson(lam_g))):
            long = rng.random() < sp['gap_long_frac']; ln = int(rng.uniform(*(sp['gap_len'][1:] if long else sp['gap_len'][:2])))
            x0 = int(rng.integers(0, max(1, X - ln))); h = rng.uniform(*sp['gap_persist']) / 2; yc = rng.uniform(0, Y)
            y0, y1 = max(0, int(yc - h)), min(Y, int(yc + h) + 1)
            if y1 > y0: z[L, y0:y1, x0:x0 + ln] = np.nan; gaps.append((L, x0, ln, y0, y1)); n_gap_total += 1
    # --- item 6: voids (3D ellipsoids, total volume for 10 % coverage incl. overlap correction)
    A_mask = (z_hi - z_lo) * X; V_target = -np.log(1 - sp['void_frac']) * Y * A_mask; voids = []; V = 0.0
    while V < V_target:
        r = rng.uniform(sp['void_size'][0] / 2, sp['void_size'][1] / 2); ry, rz, rx = r * rng.uniform(0.7, 1.3, 3)
        voids.append((rng.uniform(0, Y), rng.uniform(z_lo, z_hi), rng.uniform(0, X), ry, rz, rx)); V += 4 / 3 * np.pi * ry * rz * rx
    nan_voids(z, voids, Y, X)
    # --- item 7: crack rims
    cracks = [(rng.uniform(0, Y), rng.uniform(z_lo, z_hi), rng.uniform(0, X), rng.uniform(*sp['crack_axes']), rng.uniform(*sp['crack_axes']),
               rng.uniform(*sp['crack_axes']), rng.uniform(0, np.pi)) for _ in range(sp['n_cracks'])]
    nan_cracks(z, cracks, Y, X, sp['crack_rim'])
    if term[0] >= 0: z[T, term[2] + 1:, term[0]:term[1]] = np.nan
    for L in range(n): z[L][(z[L] < z_lo + 1) | (z[L] > z_hi - 2)] = np.nan
    # --- item 13: hop placement and shift sizes (from the truth, pre-hop)
    hops, n_overlap = place_hops(rng, args.n_hops, Y, X, forbid, sp)
    med_sp = float(np.median(spac))
    for i, (x0, x1, yc, _, dirn) in enumerate(hops):
        d = z[A, yc, x0 + sp['hop_width'] // 2] - z[T, yc, x0 + sp['hop_width'] // 2]
        if not np.isfinite(d):
            win = (z[A, yc, x0:x1] - z[T, yc, x0:x1]); win = win[np.isfinite(win)]; d = np.median(win) if win.size else np.nan
        if not np.isfinite(d): d = med_sp
        hops[i] = (x0, x1, yc, max(1, int(round(float(d)))), dirn)
    hops_arr = np.array(hops, np.int32).reshape(-1, 5)
    # --- items 11, 12: textures
    P = rng.uniform(*sp['fibre_P'], n); phi = rng.uniform(0, 2 * np.pi, n)[:, None] + np.cumsum(rng.normal(0, sp['fibre_phase_sigma'], (n, Y)), axis=1)
    stripe = (1 + sp['stripe_amp'] * rng.standard_normal(X)).astype(np.float32)[None, :]
    cell = sp['air_cell']; air_lo = rng.standard_normal((int(np.ceil(Y / cell)) + 2, int(np.ceil(Z / cell)) + 2, int(np.ceil(X / cell)) + 2))
    air_lo = ndi.gaussian_filter(air_lo, 1.0, mode='reflect'); air_lo /= air_lo.std(); air_lo = air_lo.astype(np.float32)
    Zq, Xq = -(-Z // 4), -(-X // 4); t_truth = time.time() - t_start
    # --- render section by section
    block = np.lib.format.open_memmap(os.path.join(args.out_dir, 'block.npy'), mode='w+', dtype=np.uint8, shape=(Y, Z, X))
    xmean = np.zeros((Y, Z), np.float32); times = []; void_cover = 0; mat_amp = np.float32(MAT) * base[:, None].astype(np.float32)
    sig_n = np.float32(sp['noise'] * MAT)
    for y in range(Y):
        t0 = time.time(); ty = y / cell; i0 = min(int(ty), air_lo.shape[0] - 2); w = ty - i0
        lo2 = air_lo[i0] * (1 - w) + air_lo[i0 + 1] * w
        img = np.repeat(np.repeat(bilinear_up(lo2, Zq, Xq, cell), 4, axis=0), 4, axis=1)[:Z, :X]
        img *= np.float32(sp['air_var']); img += np.float32(AIR)
        mats = mat_amp * (1 + np.float32(sp['fibre_amp']) * np.sin(2 * np.pi * xx[None, :] / P[:, None] + phi[:, y][:, None]).astype(np.float32))
        raster(img, z[:, y, :], width, pgap, mats, Z)
        void_cover += render_voids(img, voids, y, z_lo, z_hi, X, sp['void_edge']); render_cracks(img, cracks, y, z_lo, z_hi, X, sp['crack_rim'])
        img = ndi.gaussian_filter(img, sp['blur'])
        for (x0, x1, yc, d, dirn) in hops:
            if (dirn > 0 and y > yc) or (dirn < 0 and y < yc):
                win = img[z_lo:z_hi, x0:x1]; win[d:] = win[:-d].copy(); win[:d] = AIR
        img *= stripe; img += sig_n * rng.standard_normal((Z, X), dtype=np.float32)
        out = np.clip(np.rint(img), 1, 255).astype(np.uint8); out[:z_lo] = 0; out[z_hi:] = 0
        block[y] = out; xmean[y] = out.mean(axis=1); times.append(time.time() - t0)
    block.flush(); del block
    # --- truth follows the moved content (item 13)
    for (x0, x1, yc, d, dirn) in hops:
        ys = slice(yc + 1, Y) if dirn > 0 else slice(0, yc); z[:, ys, x0:x1] += d
    for L in range(n): z[L][z[L] > z_hi - 2] = np.nan
    np.savez(os.path.join(args.out_dir, 'truth.npz'), z=z, width=width, s=s.astype(np.float16), target=np.int64(T), hops=hops_arr,
             shear=np.array([z_p, x_p, sp['shear_angle'], side], np.float64), term=np.array(term, np.int64),
             mask_z=np.array([z_lo, z_hi], np.int64), y_seed=np.int64(y_seed), thin=thin, ply_gap=pgap.astype(np.int64),
             base=base.astype(np.float32), seams=np.array(seams, np.int64), tilt_beta=np.array(tstats['beta'], np.float32), z_seed_flat=z0.astype(np.float32))
    # --- realised statistics
    idx = rng.integers(0, z[:-1].size, 1000000); dsp = (z[1:] - z[:-1]).ravel()[idx]; dsp = dsp[np.isfinite(dsp)]
    sidx = rng.integers(0, s.size, 1000000); sabs = np.abs(s.ravel()[sidx])
    gaps_per_section = sum((g[4] - g[3]) for g in gaps) / Y / n if gaps else 0.0
    params = dict(provenance='Project HERCULES | [id removed]', tool='phantom_ord3', vox_um=VOX_UM, Y=Y, Z=Z, X=X, seed=args.seed,
                  margin=MARGIN, pad=PAD, min_spacing=MINSP, mask_z=[z_lo, z_hi], y_seed=y_seed, n_lam=n, target=T, A=A, B=B,
                  intensities=dict(air=AIR, material=MAT, ply_gap=GAPV, void=VOIDV, crack=CRACKV, rim=RIMV), spec=sp,
                  spacing=dict(law='two-piece log-normal through p10/p50/p90', declared_q=sp['spacing_q'], n_pairs=len(spac), n_seams=len(seams),
                               seam_pairs=seams, realised_q_flat_noseam=[float(v) for v in np.quantile(np.delete(spac, seams), [0.1, 0.5, 0.9])] if len(spac) > len(seams) else [],
                               realised_q_truth_sampled=[float(v) for v in np.quantile(dsp, [0.1, 0.5, 0.9])] if dsp.size else []),
                  width=dict(n_thin=int(thin.sum()), thin_frac_realised=float(thin.mean()), per_lamina=[float(v) for v in width], ply_gap=[int(v) for v in pgap]),
                  tilt=dict(declared_q=sp['tilt_q'], realised_abs_q_sampled=[float(v) for v in np.quantile(sabs, [0.1, 0.5, 0.9])],
                            capped_frac=float((sabs >= sp['tilt_cap'] - 1e-3).mean()), **tstats),
                  buckling=bstats, gaps=dict(n_total=n_gap_total, per_lamina_mean=n_gap_total / n, present_per_lamina_per_section=gaps_per_section,
                                             expected_per_section_from_rate=X / sp['gap_every']),
                  voids=dict(n_blobs=len(voids), target_frac=sp['void_frac'], realised_frac=void_cover / (Y * A_mask)),
                  cracks=dict(n=len(cracks), list=[[float(v) for v in c] for c in cracks]),
                  shear=dict(z_point=z_p, x_point=x_p, angle_deg=sp['shear_angle'], shift_side=side, x_band=[float(v) for v in shear_x]),
                  term=dict(x0=term[0], x1=term[1], y_t=term[2]),
                  hops=dict(requested=args.n_hops, placed=len(hops), n_overlapping_same_direction=n_overlap, width=sp['hop_width'],
                            list=[[int(v) for v in h] for h in hops], columns=['x0', 'x1', 'y_c', 'd', 'direction']),
                  fibre=dict(P=[float(v) for v in P]),
                  timing=dict(truth_build_s=t_truth, sec_per_section_mean=float(np.mean(times)), sec_per_section_median=float(np.median(times)),
                              sec_per_section_max=float(np.max(times)), total_s=time.time() - t_start))
    with open(os.path.join(args.out_dir, 'params.json'), 'w') as f: json.dump(params, f, indent=1)
    if not args.no_preview:
        from PIL import Image
        blk = np.load(os.path.join(args.out_dir, 'block.npy'), mmap_mode='r'); sec = np.asarray(blk[y_seed], np.float32)
        Zh, Xh = Z // 2, X // 2; left = sec[:2 * Zh, :2 * Xh].reshape(Zh, 2, Xh, 2).mean((1, 3))
        xm = xmean.T[:2 * Zh, :2 * (Y // 2)].reshape(Zh, 2, Y // 2, 2).mean((1, 3)) if Y >= 2 else xmean.T[:2 * Zh:2]
        lo_, hi_ = np.percentile(xm[xm > 0], [1, 99]) if (xm > 0).any() else (0, 1); xm = np.clip((xm - lo_) / max(hi_ - lo_, 1e-6), 0, 1) * 255
        canvas = np.zeros((Zh, Xh + 8 + xm.shape[1]), np.uint8); canvas[:, :Xh] = left.astype(np.uint8); canvas[:, Xh + 8:] = xm.astype(np.uint8)
        Image.fromarray(canvas, 'L').save(os.path.join(args.out_dir, 'preview.png'))
    print(json.dumps(dict(shape=[Y, Z, X], MB=round(Y * Z * X / 1e6, 1), n_lam=n, target=T, sec_per_section=round(float(np.mean(times)), 4),
                          n_hops=len(hops), total_s=round(time.time() - t_start, 1))))


if __name__ == '__main__':
    main()
