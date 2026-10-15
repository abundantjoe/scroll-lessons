#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1 stage A/B: per-slab layering-normal concurrency fit of the scroll axis (umbilicus) with explicit confidence and
multi-centre diagnostics. Input: a masked CT volume (z,y,x uint8) at level 3 (69 um) either as a local .npy or streamed
from an OME-zarr level on S3. For every z-slab of `--slab` slices:
  1. per-slice polar high-pass about the reconstruction centre (removes azimuthally constant ring artefacts), mask erosion
     (the mask edge never votes), debris exclusion (per-slab p99.5 dilated), 2-D structure tensor (derivative sigma_d,
     integration sigma_i) accumulated over the slab, separately over odd and even slices (split-half);
  2. admissible voters: coherence and contrast above thresholds calibrated on a phase-randomised null of the same slab
     (data-derived, nothing copied from another scroll);
  3. robust concurrency fit: the point minimising the Tukey-biweight sum of perpendicular distances to the voters' normal
     lines (IRLS), multi-start basin agreement, conditioning ratio, inlier fraction, median residual;
  4. 36 azimuth x 3 radial-band sector fits: coverage, MAD spread, mean-shift clusters (multi-centre flag, mini-umbilicus
     seeds), inner/outer band concentricity; split-half distance; decoy diagnostics (distance to the image centre and to
     the mask centroid); ray-crossing winding-count balance on the slab mean image;
  5. confidence = coverage * (1 - clip(residual_mm / 0.5)) * [conditioning >= 0.1] * [basin spread <= 0.2 mm].
Writes <out>/slabs.json (one record per slab) and <out>/fields.npz (decimated normal angle, coherence, admissible mask).
usage: st_axis.py <src.npy | s3://bucket/key/of/level> <out_dir> [--vox_um 69.12] [--slab 16] [--z0 A --z1 B]
"""
import argparse, json, os, time, numpy as np, cv2
from scipy import ndimage as ndi
from scipy.optimize import minimize
cv2.setNumThreads(1)

class S3Blocks:
    """Chunk-row cached reader of one zarr-v2 level on S3 (threaded, decoded with numcodecs): V[z0:z1] fetches the enclosing
    chunk rows once and serves consecutive slabs from RAM (one chunk row of level 3 = 128 x 1519 x 1519 = 295 MB)."""
    def __init__(self, key, threads=32, axis=0):
        import s3fs; from numcodecs import get_codec; from concurrent.futures import ThreadPoolExecutor
        self.fs = s3fs.S3FileSystem(anon=True); self.key = key[5:].rstrip('/') if key.startswith('s3://') else key.rstrip('/'); za = json.loads(self.fs.cat_file(self.key + '/.zarray'))
        self.vshape, self.chunks, self.dtype = tuple(za['shape']), tuple(za['chunks']), np.dtype(za['dtype']); self.comp = get_codec(za['compressor']) if za.get('compressor') else None
        self.sep = za.get('dimension_separator', '.'); self.order = za.get('order', 'C'); self.fill = za.get('fill_value', 0) or 0; self.ex = ThreadPoolExecutor(threads); self.cache = {}; self.axis = axis
        Z, Y, X = self.vshape; self.shape = (Z, Y, X) if axis == 0 else (Y, Z, X)              # iteration axis first; a y-slab comes back as (n, Z, X): an xz section stack
    def _row(self, i):
        """Chunk row i (axis 0) or chunk column i (axis 1), as an array with the iteration axis first."""
        if i in self.cache: return self.cache[i]
        cz, cy, cx = self.chunks; Z, Y, X = self.vshape
        if self.axis == 0: out = np.full((min(cz, Z - i * cz), Y, X), self.fill, self.dtype); keys = [(i, j, k) for j in range((Y - 1) // cy + 1) for k in range((X - 1) // cx + 1)]
        else: out = np.full((min(cy, Y - i * cy), Z, X), self.fill, self.dtype); keys = [(ii, i, k) for ii in range((Z - 1) // cz + 1) for k in range((X - 1) // cx + 1)]
        def get(ijk):
            a, b, c = ijk
            try: raw = self.fs.cat_file(f'{self.key}/{a}{self.sep}{b}{self.sep}{c}')
            except FileNotFoundError: return ijk, None
            return ijk, np.frombuffer(self.comp.decode(raw) if self.comp else raw, self.dtype).reshape(self.chunks, order=self.order)
        for (a, b, c), arr in self.ex.map(get, keys):
            if arr is None: continue
            zs, ze = a * cz, min((a + 1) * cz, Z); ys, ye = b * cy, min((b + 1) * cy, Y); xs, xe = c * cx, min((c + 1) * cx, X); blk = arr[:ze - zs, :ye - ys, :xe - xs]
            if self.axis == 0: out[:, ys:ye, xs:xe] = blk
            else: out[:, zs:ze, xs:xe] = blk.transpose(1, 0, 2)
        self.cache = {i: out}; return out                                       # keep one row/column only
    def __getitem__(self, sl):
        n0, n1 = sl.start or 0, min(sl.stop, self.shape[0]); c = self.chunks[self.axis]; parts = []
        for i in range(n0 // c, (n1 - 1) // c + 1): row = self._row(i); a, b = max(n0, i * c) - i * c, min(n1, (i + 1) * c) - i * c; parts.append(row[a:b])
        return np.concatenate(parts) if len(parts) > 1 else parts[0]

class NpyAxis:
    """Local .npy (z,y,x) viewed along z (axis 0) or along y (axis 1, slabs come back as (n, Z, X))."""
    def __init__(self, path, axis=0): self.v = np.load(path, mmap_mode='r'); self.axis = axis; Z, Y, X = self.v.shape; self.shape = (Z, Y, X) if axis == 0 else (Y, Z, X)
    def __getitem__(self, sl): return np.asarray(self.v[sl]) if self.axis == 0 else np.asarray(self.v[:, sl, :]).transpose(1, 0, 2)

def open_source(src, axis=0):
    if src.startswith('s3://'): return S3Blocks(src, axis=axis)
    return NpyAxis(src, axis=axis)

def polar_highpass(img, cxy):
    """Subtract the azimuthal mean about cxy (the reconstruction centre): ring artefacts vanish, layering survives."""
    Y, X = img.shape; R = int(np.hypot(X, Y) / 2) + 2
    pol = cv2.warpPolar(img, (R, 720), cxy, R, cv2.WARP_POLAR_LINEAR | cv2.INTER_LINEAR)          # (720 angles, R radii)
    valid = cv2.warpPolar(np.ones_like(img), (R, 720), cxy, R, cv2.WARP_POLAR_LINEAR | cv2.INTER_NEAREST) > 0.5
    m = (pol * valid).sum(0) / np.maximum(valid.sum(0), 1); ring = np.broadcast_to(m[None], pol.shape).astype(np.float32)
    back = cv2.warpPolar(ring, (X, Y), cxy, R, cv2.WARP_POLAR_LINEAR | cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR)
    out = img - back
    if not np.isfinite(out).all():                                           # seen once, not reproducible: retry, then fall back to the raw image and say so
        out = img - cv2.warpPolar(np.ascontiguousarray(ring), (X, Y), cxy, R, cv2.WARP_POLAR_LINEAR | cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR)
        if not np.isfinite(out).all(): polar_highpass.fallbacks += 1; return img.copy()
    return out
polar_highpass.fallbacks = 0

def stripe_removal(img, mask):
    """xz sections of a volume reconstructed about z: ring artefacts are z-invariant vertical stripes; subtract each
    column's in-mask z-median (the layering, which varies along z, survives)."""
    m = mask > 0; col = np.zeros(img.shape[1], np.float32)
    for x in range(img.shape[1]):
        v = img[m[:, x], x]
        if v.size >= 8: col[x] = np.median(v)
    return (img - col[None, :]) * m

def st_accumulate(slices, sd):
    """Per-slice gradients -> summed tensor components (Jxx, Jxy, Jyy) over the given slices (float32)."""
    acc = None
    for s in slices:
        gx = ndi.gaussian_filter(s, sd, order=(0, 1)); gy = ndi.gaussian_filter(s, sd, order=(1, 0))
        t = np.stack([gx * gx, gx * gy, gy * gy]); acc = t if acc is None else acc + t
    return acc

def st_eigen(J, si):
    Jxx, Jxy, Jyy = [ndi.gaussian_filter(c, si) for c in J]
    tr = Jxx + Jyy; det = Jxx * Jyy - Jxy * Jxy; disc = np.sqrt(np.maximum(tr * tr / 4 - det, 0)); l1 = tr / 2 + disc; l2 = tr / 2 - disc
    theta = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)                           # orientation of the dominant gradient = layer normal
    coh = (l1 - l2) / (l1 + l2 + 1e-12); return theta.astype(np.float32), coh.astype(np.float32), tr.astype(np.float32)

def phase_null(img, rng):
    F = np.fft.rfft2(img); ph = np.exp(2j * np.pi * rng.random(F.shape)); return np.fft.irfft2(np.abs(F) * ph, s=img.shape).astype(np.float32)

def irls_centre(px, py, nx, ny, w, c0, tukey, iters=6):
    """Point minimising sum w * rho_Tukey(perp distance to line p + t n). u = n_perp; d = u.c - u.p."""
    ux, uy = -ny, nx; up = ux * px + uy * py; cx, cy = c0; W = w.copy()
    sched = [tukey * f for f in (16, 8, 4, 2, 1)] + [tukey] * iters          # coarse-to-fine: every start first sees the convex LS basin
    for tk in sched:
        d = ux * cx + uy * cy - up; r = d / tk; tw = np.where(np.abs(r) < 1, (1 - r * r) ** 2, 0.0); W = w * tw
        A = np.array([[np.sum(W * ux * ux), np.sum(W * ux * uy)], [np.sum(W * ux * uy), np.sum(W * uy * uy)]]); b = np.array([np.sum(W * ux * up), np.sum(W * uy * up)])
        if np.linalg.cond(A) > 1e8 or W.sum() <= 0: break
        cx, cy = np.linalg.solve(A, b)
    d = ux * cx + uy * cy - up; ev = np.linalg.eigvalsh(A / max(W.sum(), 1e-9)); return float(cx), float(cy), d, float(ev[0] / max(ev[1], 1e-12)), W

def metric_resid(theta_p, px, py, nx, ny):
    """Residual of the affine-squeeze model: the normal at v should align with M (v - c); returns a signed miss in voxels
    (|v - c| times the sine of the angle between n and M(v - c)); equals the point-model residual when s = 1."""
    cx, cy, s, phi = theta_p; dx, dy = px - cx, py - cy; cp, sp = np.cos(phi), np.sin(phi)
    X1, Y1 = cp * dx + sp * dy, -sp * dx + cp * dy; X1, Y1 = X1, Y1 * s * s                 # M (v - c) in the rotated frame
    mx, my = cp * X1 - sp * Y1, sp * X1 + cp * Y1; nm = np.hypot(mx, my) + 1e-9; r = np.hypot(dx, dy)
    return (mx / nm * ny - my / nm * nx) * r

def slit_resid(t, px, py, nx, ny):
    """Confocal slit model: foci F = (cx, cy) +- c (cos phi, sin phi); the layer normal at v aligns with the bisector of the
    directions from the two foci; residual = sine of the misalignment x distance from v to the slit segment (voxels).
    c = 0 is the point model."""
    cx, cy, c, phi = t; ux, uy = np.cos(phi), np.sin(phi); fx, fy = c * ux, c * uy
    d1x, d1y = px - (cx - fx), py - (cy - fy); d2x, d2y = px - (cx + fx), py - (cy + fy); r1 = np.hypot(d1x, d1y) + 1e-9; r2 = np.hypot(d2x, d2y) + 1e-9
    bx, by = d1x / r1 + d2x / r2, d1y / r1 + d2y / r2; bn = np.hypot(bx, by) + 1e-9
    tt = np.clip((px - cx) * ux + (py - cy) * uy, -c, c); dist = np.hypot(px - (cx + tt * ux), py - (cy + tt * uy))
    return (bx / bn * ny - by / bn * nx) * dist

def tukey_obj(d, w, tukey):
    r = np.abs(d) / tukey; rho = np.where(r < 1, (tukey ** 2 / 6) * (1 - (1 - r * r) ** 3), tukey ** 2 / 6); return float(np.sum(w * rho))

def fit_slit(px, py, nx, ny, w, c0, tukey, phi0, c_max):
    """Nelder-Mead over (cx, cy, c, phi) from several starts (c = 0, 0.3 c_max, 0.6 c_max at phi0 and phi0 + 90 deg)."""
    def obj(t):
        if not (0.0 <= t[2] <= c_max): return 1e18
        return tukey_obj(slit_resid(t, px, py, nx, ny), w, tukey)
    best = None
    for cs in (0.0, 0.3 * c_max, 0.6 * c_max):
        for ph in ((phi0,) if cs == 0 else (phi0, phi0 + np.pi / 2)):
            r = minimize(obj, [c0[0], c0[1], cs, ph], method='Nelder-Mead', options={'xatol': 0.05, 'fatol': 1e-3, 'maxiter': 800})
            if best is None or r.fun < best.fun: best = r
    t = best.x.copy(); t[3] = float(np.mod(t[3], np.pi)); return t, slit_resid(t, px, py, nx, ny), float(best.fun)

def fit_metric(px, py, nx, ny, w, c0, tukey, mask_inertia_phi):
    """Nelder-Mead over (cx, cy, s, phi) of the Tukey-weighted squared residual; starts at the point fit with s=1 and at the mask inertia orientation with s=0.6."""
    def obj(t):
        if not (0.25 <= t[2] <= 1.0): return 1e18
        d = metric_resid(t, px, py, nx, ny); r = np.abs(d) / tukey; rho = np.where(r < 1, (tukey ** 2 / 6) * (1 - (1 - r * r) ** 3), tukey ** 2 / 6); return float(np.sum(w * rho))
    best = None
    for s0, ph0 in [(1.0, 0.0), (0.6, mask_inertia_phi), (0.6, mask_inertia_phi + np.pi / 2)]:
        r = minimize(obj, [c0[0], c0[1], s0, ph0], method='Nelder-Mead', options={'xatol': 0.05, 'fatol': 1e-3, 'maxiter': 600})
        if best is None or r.fun < best.fun: best = r
    t = best.x; t[3] = float(np.mod(t[3], np.pi)); d = metric_resid(t, px, py, nx, ny); return t, d, float(best.fun)

def mean_shift(pts, bw, iters=30):
    """Mean-shift modes of 2-D points; returns cluster centres and member counts."""
    if len(pts) == 0: return [], []
    m = pts.astype(np.float64).copy()
    for _ in range(iters):
        d2 = ((m[:, None, :] - pts[None, :, :]) ** 2).sum(-1); k = np.exp(-0.5 * d2 / bw ** 2); m = (k @ pts) / k.sum(1, keepdims=True)
    cents, counts = [], []
    for q in m:
        for i, c in enumerate(cents):
            if np.hypot(*(q - c)) < bw / 2: counts[i] += 1; break
        else: cents.append(q); counts.append(1)
    return [c.tolist() for c in cents], counts

def ray_crossings(img, mask, c, n_rays=36, step=0.5):
    """Count layer crossings (smoothed-profile local maxima) along rays from c to the mask edge; returns counts per ray."""
    Y, X = img.shape; counts = []; sm = ndi.gaussian_filter(img, 1.0)
    for k in range(n_rays):
        th = 2 * np.pi * k / n_rays; dx, dy = np.cos(th), np.sin(th); rs = np.arange(0, max(X, Y), step); xs, ys = c[0] + rs * dx, c[1] + rs * dy
        ok = (xs >= 0) & (xs < X - 1) & (ys >= 0) & (ys < Y - 1); xs, ys = xs[ok], ys[ok]
        inm = ndi.map_coordinates(mask.astype(np.float32), [ys, xs], order=0) > 0.5
        if inm.sum() < 10: counts.append(0); continue
        last = np.nonzero(inm)[0].max(); prof = ndi.map_coordinates(sm, [ys[:last], xs[:last]], order=1)
        if len(prof) < 5: counts.append(0); continue
        thr = 0.25 * prof.std(); pk = (prof[1:-1] > prof[:-2]) & (prof[1:-1] >= prof[2:]) & (prof[1:-1] - np.minimum(prof[:-2], prof[2:]) > thr); counts.append(int(pk.sum()))
    return counts

def analyse_slab(stack, vox_um, p, rng, img_centre):
    """stack: (n, Y, X) float32 in [0,1] (0 outside the mask). Returns the slab record and decimated fields."""
    n, Y, X = stack.shape; mm = 1000.0 / vox_um                                   # voxels per mm
    mask = (stack > 0).mean(0) > 0.5; area = int(mask.sum())
    rec = {'n_slices': n, 'mask_area_vox': area}
    if area < 2000: rec['status'] = 'no mask'; return rec, None
    ys, xs = np.nonzero(mask); mcx, mcy = float(xs.mean()), float(ys.mean()); rec['mask_centroid'] = [round(mcx, 2), round(mcy, 2)]
    er = ndi.binary_erosion(mask, iterations=p['erode'])
    if er.sum() < 500: rec['status'] = 'mask too thin after erosion'; rec['eroded_area_vox'] = int(er.sum()); return rec, None
    
    hi = np.percentile(stack[:, mask], 99.5); debris = ndi.binary_dilation((stack > hi).any(0), iterations=3); rec['debris_frac'] = round(float(debris[mask].mean()), 4)
    # polar high-pass per slice about the reconstruction centre (image centre), then structure tensor, odd/even separately
    if p.get('axis') == 'y': sl = [stripe_removal(np.ascontiguousarray(stack[i]), mask) for i in range(n)]            # y frame: rings are vertical stripes
    else: sl = [polar_highpass(np.ascontiguousarray(stack[i]), img_centre) * mask for i in range(n)]
    half = n // 2
    Jq = [st_accumulate([x for k, x in enumerate(sl) if k % 2 == i and k < half], p['sd']) for i in (0, 1)]      # odd/even within the FIRST half
    Jr = [st_accumulate([x for k, x in enumerate(sl) if k % 2 == i and k >= half], p['sd']) for i in (0, 1)]     # odd/even within the LAST half
    Jo, Je = Jq[0] + Jr[0], Jq[1] + Jr[1]; Jfirst, Jlast = Jq[0] + Jq[1], Jr[0] + Jr[1]
    J = Jo + Je
    theta, coh, con = st_eigen(J, p['si'])
    # null calibration on a phase-randomised slice (same power spectrum, no structure)
    tn, cn, conn = st_eigen(st_accumulate([phase_null(x, rng) * mask for x in sl], p['sd']), p['si'])   # same power spectrum, no structure
    c0 = float(np.percentile(cn[er], 99)); t0 = float(np.percentile(con[er], 30)); rec['null_thr'] = {'coh_p99_null': round(c0, 3), 'coh_p50_real': round(float(np.percentile(coh[er], 50)), 3), 'contrast_p30': float(t0)}
    adm = er & ~debris & (coh >= max(c0, p['coh_min'])) & (con >= t0); rec['admissible_frac_of_mask'] = round(float(adm.sum() / area), 4)
    if adm.sum() < 500: rec['status'] = 'too few admissible voters'; return rec, (theta, coh, adm)
    ay, ax = np.nonzero(adm)
    if len(ax) > p['max_voters']: sel = rng.choice(len(ax), p['max_voters'], replace=False); ay, ax = ay[sel], ax[sel]
    px, py = ax.astype(np.float64), ay.astype(np.float64); th = theta[ay, ax].astype(np.float64); nx, ny = np.cos(th), np.sin(th); w = (coh[ay, ax] * con[ay, ax] ** 0.5).astype(np.float64); w /= w.mean()
    tk = p['tukey_mm'] * mm
    # weighted LS start, then IRLS; multi-start basin test
    cx, cy, d, cond, W = irls_centre(px, py, nx, ny, w, (mcx, mcy), tk)
    starts = [(mcx, mcy)] + [(cx + 5 * mm * np.cos(a), cy + 5 * mm * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
    ends = np.array([irls_centre(px, py, nx, ny, w, s, tk)[:2] for s in starts]); spread = float(np.hypot(*(ends - ends.mean(0)).T).max())
    rec['point_model'] = {'centre': [round(cx, 2), round(cy, 2)], 'median_resid_mm': round(float(np.median(np.abs(d))) / mm, 4), 'conditioning': round(cond, 4), 'multistart_spread_mm': round(spread / mm, 4)}
    pt_obj = tukey_obj(d, w, tk); pt_res = float(np.median(np.abs(d)))
    # split-half (odd vs even slices) and first-half vs last-half (a kink INSIDE the slab shows here, not in odd/even)
    def half_centre(Jh):
        t_, c_, k_ = st_eigen(Jh, p['si']); a_ = adm & (c_ >= c0); yy, xx = np.nonzero(a_)
        if len(xx) < 300: return None
        if len(xx) > p['max_voters']: s_ = rng.choice(len(xx), p['max_voters'], replace=False); yy, xx = yy[s_], xx[s_]
        t2 = t_[yy, xx].astype(np.float64); return irls_centre(xx.astype(np.float64), yy.astype(np.float64), np.cos(t2), np.sin(t2), (c_[yy, xx] * k_[yy, xx] ** 0.5).astype(np.float64), (cx, cy), tk)[:2]
    hf, hl = half_centre(Jfirst), half_centre(Jlast)
    if hf is not None and hl is not None: rec['half_first_last_mm'] = round(float(np.hypot(hf[0] - hl[0], hf[1] - hl[1])) / mm, 4); rec['half_centres'] = [[round(hf[0], 2), round(hf[1], 2)], [round(hl[0], 2), round(hl[1], 2)]]
    if p.get('no_models'):                                                   # fields-only mode: the point fit is kept as a cross-check, the slit/affine fits are skipped (topo_axis.py is the estimator)
        rec['model'] = 'point'; rec.update({'centre': [round(cx, 2), round(cy, 2)], 'n_voters': int(len(px)), 'median_resid_mm': round(pt_res / mm, 4), 'inlier_frac_1mm': round(float((np.abs(d) < 1 * mm).mean()), 4), 'conditioning': round(cond, 4), 'multistart_spread_mm': round(spread / mm, 4),
                    'dist_to_image_centre_mm': round(float(np.hypot(cx - img_centre[0], cy - img_centre[1])) / mm, 3), 'dist_to_mask_centroid_mm': round(float(np.hypot(cx - mcx, cy - mcy)) / mm, 3), 'residual_frac_gt1mm': round(float((np.abs(d) > 1 * mm).mean()), 4), 'sector_coverage_0p5mm': None, 'n_clusters_ge25pct': None, 'confidence': 0.0, 'status': 'ok', 'polar_fallbacks': polar_highpass.fallbacks})
        return rec, (theta, coh, adm)
    # slit (confocal) model, always fitted on a subsample; the point model is its c = 0 member
    yy_, xx_ = np.nonzero(er); cxy_ = np.cov(np.stack([xx_ - xx_.mean(), yy_ - yy_.mean()])); evl, evv = np.linalg.eigh(cxy_); phi0 = float(np.arctan2(evv[1, 1], evv[0, 1])); c_max = 0.5 * float(np.ptp(xx_) + np.ptp(yy_)) / 2
    sub = rng.choice(len(px), min(len(px), 60000), replace=False)
    ts, _, _ = fit_slit(px[sub], py[sub], nx[sub], ny[sub], w[sub], (cx, cy), tk, phi0, c_max); d_s = slit_resid(ts, px, py, nx, ny); sl_res = float(np.median(np.abs(d_s)))
    h1, h2 = sub[0::2], sub[1::2]; t1 = fit_slit(px[h1], py[h1], nx[h1], ny[h1], w[h1], (cx, cy), tk, phi0, c_max)[0]; t2 = fit_slit(px[h2], py[h2], nx[h2], ny[h2], w[h2], (cx, cy), tk, phi0, c_max)[0]
    rec['slit_model'] = {'centre': [round(float(ts[0]), 2), round(float(ts[1]), 2)], 'c_mm': round(float(ts[2]) / mm, 3), 'phi_deg': round(float(np.degrees(ts[3])), 1), 'median_resid_mm': round(sl_res / mm, 4), 'inlier_frac_1mm': round(float((np.abs(d_s) < 1 * mm).mean()), 4),
                         'improvement_over_point': round(float(1 - sl_res / max(pt_res, 1e-9)), 3), 'split_half_centre_mm': round(float(np.hypot(t1[0] - t2[0], t1[1] - t2[1])) / mm, 4), 'split_half_c_mm': [round(float(t1[2]) / mm, 3), round(float(t2[2]) / mm, 3)]}
    model, dm, cxm, cym, res_m = 'point', d, cx, cy, pt_res
    if rec['slit_model']['improvement_over_point'] >= 0.10 and ts[2] >= 0.5 * mm and rec['slit_model']['split_half_centre_mm'] <= 0.5: model, dm, cxm, cym, res_m = 'slit', d_s, float(ts[0]), float(ts[1]), sl_res
    # affine squeeze, tried when neither point nor slit explains the section well
    pre_cov = float((np.abs(dm) < 0.5 * mm).mean())
    if pre_cov < 0.75 or (np.abs(dm) > 1 * mm).mean() > 0.2:
        ta, _, _ = fit_metric(px[sub], py[sub], nx[sub], ny[sub], w[sub], (cx, cy), tk, phi0); d_a = metric_resid(ta, px, py, nx, ny); af_res = float(np.median(np.abs(d_a)))
        ta1 = fit_metric(px[h1], py[h1], nx[h1], ny[h1], w[h1], (cx, cy), tk, phi0)[0]; ta2 = fit_metric(px[h2], py[h2], nx[h2], ny[h2], w[h2], (cx, cy), tk, phi0)[0]
        rec['metric_model'] = {'centre': [round(float(ta[0]), 2), round(float(ta[1]), 2)], 'aspect_s': round(float(ta[2]), 3), 'phi_deg': round(float(np.degrees(ta[3])), 1), 'median_resid_mm': round(af_res / mm, 4), 'inlier_frac_1mm': round(float((np.abs(d_a) < 1 * mm).mean()), 4),
                              'improvement': round(float(1 - af_res / max(res_m, 1e-9)), 3), 'split_half_centre_mm': round(float(np.hypot(ta1[0] - ta2[0], ta1[1] - ta2[1])) / mm, 4), 'split_half_s': [round(float(ta1[2]), 3), round(float(ta2[2]), 3)]}
        if rec['metric_model']['improvement'] > 0.3 and ta[2] < 0.9 and rec['metric_model']['split_half_centre_mm'] <= 0.5: model, dm, cxm, cym, res_m = 'affine_squeeze', d_a, float(ta[0]), float(ta[1]), af_res
    cx, cy, d = cxm, cym, dm; rec['model'] = model
    rec.update({'centre': [round(cx, 2), round(cy, 2)], 'n_voters': int(len(px)), 'median_resid_mm': round(res_m / mm, 4), 'inlier_frac_1mm': round(float((np.abs(d) < 1 * mm).mean()), 4),
                'conditioning': round(cond, 4), 'multistart_spread_mm': round(spread / mm, 4), 'dist_to_image_centre_mm': round(float(np.hypot(cx - img_centre[0], cy - img_centre[1])) / mm, 3), 'dist_to_mask_centroid_mm': round(float(np.hypot(cx - mcx, cy - mcy)) / mm, 3)})
    if Je is not None:
        so = []
        for Jh in (Jo, Je):
            t_, c_, k_ = st_eigen(Jh, p['si']); a_ = adm & (c_ >= c0); yy, xx = np.nonzero(a_)
            if len(xx) > p['max_voters']: s_ = rng.choice(len(xx), p['max_voters'], replace=False); yy, xx = yy[s_], xx[s_]
            t2 = t_[yy, xx].astype(np.float64); so.append(irls_centre(xx.astype(np.float64), yy.astype(np.float64), np.cos(t2), np.sin(t2), (c_[yy, xx] * k_[yy, xx] ** 0.5).astype(np.float64), (cx, cy), tk)[:2])
        rec['split_half_mm'] = round(float(np.hypot(so[0][0] - so[1][0], so[0][1] - so[1][1])) / mm, 4) if model == 'point' else (rec['slit_model']['split_half_centre_mm'] if model == 'slit' else rec['metric_model']['split_half_centre_mm'])
    # sector fits: 36 azimuths x 3 radial bands about the global centre
    r = np.hypot(px - cx, py - cy); az = np.arctan2(py - cy, px - cx); Rm = float(np.percentile(r, 99)); bands = [(0.10, 0.25), (0.25, 0.5), (0.5, 0.85)]; sect = []; NS = 12
    for bi, (b0, b1) in enumerate(bands):
        for k in range(NS):
            a0 = -np.pi + 2 * np.pi * k / NS; m = (r >= b0 * Rm) & (r < b1 * Rm) & (az >= a0) & (az < a0 + 2 * np.pi / NS)
            if m.sum() < 150: continue
            sres = float(np.median(d[m]))                                     # signed miss of the GLOBAL centre by this sector's lines (well posed)
            sx, sy, sd_, sc_, _ = irls_centre(px[m], py[m], nx[m], ny[m], w[m], (cx, cy), tk, iters=4); sect.append({'band': bi, 'az': k, 'c': [sx, sy], 'cond': sc_, 'n': int(m.sum()), 'miss_global': sres, 'resid_own': float(np.median(np.abs(sd_)))})
    if sect:
        miss = np.array([s['miss_global'] for s in sect]); cov = float((np.abs(miss) < 0.5 * mm).mean()); mad = float(np.median(np.abs(miss)))
        ok_s = [s for s in sect if s['cond'] >= 0.1]; S = np.array([s['c'] for s in ok_s]) if ok_s else np.zeros((0, 2))
        cents, counts = mean_shift(S, 1.0 * mm) if len(S) else ([], []); big = [(c, k) for c, k in zip(cents, counts) if k >= 0.25 * max(len(ok_s), 1)]
        bc = {}
        for bi in range(3):
            mb = np.array([s['miss_global'] for s in sect if s['band'] == bi])
            if len(mb) >= 4: bc[bi] = float(np.median(np.abs(mb)))
        rec.update({'sectors_fitted': len(sect), 'sector_coverage_0p5mm': round(cov, 4), 'sector_median_miss_mm': round(mad / mm, 4), 'sectors_conditioned': len(ok_s), 'n_clusters_ge25pct': len(big), 'cluster_centres': [[round(float(c[0]), 2), round(float(c[1]), 2), int(k)] for c, k in big],
                    'band_miss_mm': {str(b): round(v / mm, 4) for b, v in bc.items()}, 'R_adm_vox': round(Rm, 1)})
    else: cov = 0.0; rec.update({'sectors_fitted': 0, 'sector_coverage_0p5mm': 0.0, 'n_clusters_ge25pct': 0})
    # residual-driven secondary centres (U3 hardened): voters missing the primary centre by > 1 mm, grouped in 1 mm cells, components >= 10 % of voters
    resid = np.abs(d) > 1.0 * mm; sec = []
    if resid.sum() >= 0.1 * len(px):
        cell = max(1, int(round(1.0 * mm))); g = np.zeros((Y // cell + 1, X // cell + 1), bool); g[(py[resid] // cell).astype(int), (px[resid] // cell).astype(int)] = True
        lab, nl = ndi.label(g, structure=np.ones((3, 3))); vl = lab[(py // cell).astype(int), (px // cell).astype(int)] * resid
        for li in range(1, nl + 1):
            m = vl == li
            if m.sum() < 0.1 * len(px): continue
            sx, sy, sd_, sc_, _ = irls_centre(px[m], py[m], nx[m], ny[m], w[m], (float(px[m].mean()), float(py[m].mean())), tk)
            sec.append({'centre': [round(sx, 2), round(sy, 2)], 'frac_voters': round(float(m.mean()), 4), 'conditioning': round(sc_, 4), 'inlier_frac_1mm': round(float((np.abs(sd_) < 1 * mm).mean()), 4), 'accepted': bool(sc_ >= 0.1 and (np.abs(sd_) < 1 * mm).mean() >= 0.5)})
    rec['residual_frac_gt1mm'] = round(float(resid.mean()), 4); rec['secondary_centres'] = sec
    if model == 'slit':
        ux, uy = np.cos(ts[3]), np.sin(ts[3]); vx, vy = -uy, ux; img_m = ndi.gaussian_filter(stack.mean(0), 1.0); ud = []
        for f in np.linspace(-0.8, 0.8, 5):
            qx, qy = cx + f * ts[2] * ux, cy + f * ts[2] * uy; cc = []
            for sgn in (1, -1):
                rs = np.arange(0, max(X, Y), 0.5); xs_, ys_ = qx + sgn * rs * vx, qy + sgn * rs * vy; okk = (xs_ >= 0) & (xs_ < X - 1) & (ys_ >= 0) & (ys_ < Y - 1); xs_, ys_ = xs_[okk], ys_[okk]
                inm = ndi.map_coordinates(er.astype(np.float32), [ys_, xs_], order=0) > 0.5
                if inm.sum() < 10: cc.append(0); continue
                last = np.nonzero(inm)[0].max(); prof = ndi.map_coordinates(img_m, [ys_[:last], xs_[:last]], order=1); thr = 0.25 * prof.std()
                pk = (prof[1:-1] > prof[:-2]) & (prof[1:-1] >= prof[2:]) & (prof[1:-1] - np.minimum(prof[:-2], prof[2:]) > thr); cc.append(int(pk.sum()))
            ud.append(cc)
        tot = [u + v for u, v in ud]; rec['slit_crossings'] = {'up_down': ud, 'balanced_frac': round(float(np.mean([abs(u - v) <= 1 for u, v in ud])), 2), 'total_spread': int(max(tot) - min(tot)) if tot else None}
    cnt = ray_crossings(stack.mean(0), er, (cx, cy)); cnt_nz = [c for c in cnt if c > 0]
    rec['ray_crossings'] = {'counts': cnt, 'spread_rel': round((max(cnt_nz) - min(cnt_nz)) / max(np.mean(cnt_nz), 1), 3) if cnt_nz else None, 'adjacent_diff_le1_frac': round(float(np.mean([abs(cnt[i] - cnt[(i + 1) % len(cnt)]) <= 1 for i in range(len(cnt))])), 3)}
    if rec['model'] == 'affine_squeeze': gate = 1.0 if rec['metric_model']['split_half_centre_mm'] <= 0.5 else 0.0      # the fit's own stability (its acceptance already required it)
    elif rec['model'] == 'slit': gate = 1.0 if rec['slit_model']['split_half_centre_mm'] <= 0.5 else 0.0
    else: gate = (1.0 if cond >= 0.1 else 0.0) * (1.0 if spread / mm <= 0.2 else 0.0)
    conf = cov * max(0.0, 1 - rec['median_resid_mm'] / 0.5) * gate
    rec['polar_fallbacks'] = polar_highpass.fallbacks
    rec['confidence'] = round(float(conf), 4); rec['multi_centre'] = bool(rec['n_clusters_ge25pct'] >= 2 or any(q['accepted'] for q in sec)); rec['status'] = 'ok'
    return rec, (theta, coh, adm)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--slab', type=int, default=16); ap.add_argument('--z0', type=int, default=0); ap.add_argument('--z1', type=int, default=-1)
    ap.add_argument('--no_models', action='store_true', help='fields + point cross-check only (fast); use topo_axis.py as the estimator'); ap.add_argument('--axis', default='z', choices=['z', 'y'], help='roll axis of the volume: sections are xy slabs (z) or xz slabs (y)'); ap.add_argument('--sd', type=float, default=1.2); ap.add_argument('--si', type=float, default=5.0); ap.add_argument('--erode_mm', type=float, default=1.0); ap.add_argument('--tukey_mm', type=float, default=0.5); ap.add_argument('--coh_min', type=float, default=0.3); ap.add_argument('--max_voters', type=int, default=300000); ap.add_argument('--stride', type=int, default=4); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); V = open_source(a.src, axis=0 if a.axis == 'z' else 1); Z, Y, X = V.shape; z1 = Z if a.z1 < 0 else min(a.z1, Z); mm = 1000.0 / a.vox_um
    p = {'sd': a.sd, 'si': a.si, 'erode': max(1, int(round(a.erode_mm * mm))), 'tukey_mm': a.tukey_mm, 'coh_min': a.coh_min, 'max_voters': a.max_voters, 'no_models': bool(a.no_models), 'axis': a.axis}; rng = np.random.default_rng(a.seed); img_centre = ((X - 1) / 2.0, (Y - 1) / 2.0)
    recs = []; TH, CO, AD, IM = [], [], [], []; t0 = time.time(); zs = list(range(a.z0, z1, a.slab))
    for i, zz in enumerate(zs):
        ze = min(zz + a.slab, z1); stack = np.asarray(V[zz:ze]).astype(np.float32) / 255.0
        try: rec, fields = analyse_slab(stack, a.vox_um, p, rng, img_centre)
        except Exception as e: rec, fields = {'status': f'error: {type(e).__name__}: {str(e)[:120]}'}, None
        rec.update({'z0': zz, 'z1': ze, 'z_mid': (zz + ze - 1) / 2.0}); rec['slit_c_mm'] = (rec.get('slit_model') or {}).get('c_mm'); recs.append(rec)
        if fields is not None: TH.append(fields[0][::a.stride, ::a.stride]); CO.append(fields[1][::a.stride, ::a.stride]); AD.append(fields[2][::a.stride, ::a.stride])
        else: TH.append(np.zeros(((Y + a.stride - 1) // a.stride, (X + a.stride - 1) // a.stride), np.float32)); CO.append(TH[-1].copy()); AD.append(TH[-1] > 1)
        IM.append(ndi.uniform_filter(stack.mean(0), a.stride)[::a.stride, ::a.stride].astype(np.float32))      # decimated section image for the hole refinement in topo_axis.py
        print(json.dumps({k: rec.get(k) for k in ['z0', 'status', 'centre', 'model', 'confidence', 'slit_c_mm', 'median_resid_mm', 'sector_coverage_0p5mm', 'n_clusters_ge25pct', 'residual_frac_gt1mm', 'split_half_mm', 'half_first_last_mm', 'conditioning', 'multistart_spread_mm', 'admissible_frac_of_mask']}), f'{time.time()-t0:.0f}s', flush=True)
        if (i + 1) % 10 == 0 or i == len(zs) - 1: np.savez_compressed(os.path.join(a.out, 'fields.npz'), theta=np.stack(TH), coh=np.stack(CO), adm=np.stack(AD), img=np.stack(IM), z_mid=np.array([r['z_mid'] for r in recs]), stride=a.stride)
        json.dump({'src': a.src, 'axis': a.axis, 'vox_um': a.vox_um, 'params': p, 'slab': a.slab, 'image_centre': img_centre, 'shape': [Z, Y, X], 'section_axes': 'xy' if a.axis == 'z' else 'xz', 'centre_is': ['x', 'y'] if a.axis == 'z' else ['x', 'z'], 'slabs': recs}, open(os.path.join(a.out, 'slabs.json'), 'w'), indent=1)
    np.savez_compressed(os.path.join(a.out, 'fields.npz'), theta=np.stack(TH), coh=np.stack(CO), adm=np.stack(AD), img=np.stack(IM), z_mid=np.array([r['z_mid'] for r in recs]), stride=a.stride)
    print('done', len(recs), 'slabs', f'{time.time()-t0:.0f}s')

if __name__ == '__main__': main()
