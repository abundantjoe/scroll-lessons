#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 item 3 (re-read under DECL-UNR-1-A1, the rolled model): HAIRPIN TRACE OPERATOR at the scan's native 8.64 um.

Input: a y-slab of n consecutive xz sections (n, Z, X) uint8 of OME level 0 (fetched with tools/umb/core_native.L0.slab
or a local .npy). Per section: stripe removal (column z-median), anisotropic structure tensor (derivative sigma sd; the
tensor integrated along the preliminary lamina tangent with sigma_along and across it with sigma_across, through a bank
of oriented Gaussian kernels), a ridge image g (Gaussian sigma_r of the stripe-removed section), the director-index maps
at R = R0 and R1 (topo_axis.index_map on a stride grid; +1/2 plateaus = hairpin apexes, -1/2 plateaus = lobe boundaries).

Operator, for one apex (a +1/2 plateau at R0) in the trace section:
  1. opening direction d of the +1/2 from the director on a circle of radius R0 about the apex (psi = phi/2 + c fit; the
     arms lie at phi = 2c, the turn at 2c + pi);
  2. chord = the line perpendicular to d at distance L from the apex; lamina crossings on it = peaks of g with prominence
     >= det_mad (3) x the noise MAD of the ridge image (adjacent-section difference MAD / sqrt 2; the in-mask MAD of the
     section is signal-dominated and is reported only); arm A = s < 0, arm B = s > 0 (s along the chord; ordinal 1 = innermost on each arm);
  3. for every arm-A crossing (= the lamina's last observed point): 2-D ridge following along the lamina tangent (step
     <= 1 voxel; a tangent turn above max_turn per step is a junction and the follower coasts; re-anchored on the nearest
     ridge maximum along the local normal within +-ra voxels, by at most ra_step per step; lost after `lost` steps without a
     ridge of prominence >= ridge_mad * MAD; detection on the chord stays at 3 MAD, the fraction of the trace at 3 MAD
     is reported as ridge_frac_3mad) through the turn until it crosses the chord again on arm B (= the first observed point of the paired
     lamina), and the reverse trace from that lamina back; they must agree;
  4. acceptance: the region enclosed by the trace and the chord contains exactly one +1/2 (within enc_tol voxels of the
     region: the innermost loop carries its defect on itself) and no -1/2 (strict; R0 map of the same section) and no
     seam (a dark gap at least 2*seam_hw wide inside the region other than the nest's core void, the wide-dark component
     nearest the apex); the ridge is >= 3 MAD on >= ridge_min
     of the trace; the trace passes no closer than nb_mm to any -1/2; and the same ridge (re-traced from the same chord
     crossing) is continuous over >= N consecutive sections of the slab (end within match_tol, mean polyline offset <= dmax).
  Output per accepted trace: status HAIRPIN-TRACED, the trace polyline (window and absolute level-0 coordinates), the
  enclosed-defect counts, the ridge continuity measure (consecutive sections, per-section offsets, ridge fraction) and
  the arm pairing (ordinal and position of the lamina on each arm, above/below). Every attempt is recorded with its
  failure reason. HAIRPIN-VERIFIED is never issued here (W14 review is a separate step).
usage: hairpin_trace.py <out_dir> (--npy slab.npy | --src s3://.../0 --y Y --z0 Z0 --z1 Z1 --x0 X0 --x1 X1) [--n 16] [--N 8] ...
"""
import argparse, json, os, sys, time, numpy as np, cv2
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb'))
from st_axis import stripe_removal                      # noqa: E402
from topo_axis import index_map, plateaus               # noqa: E402
VOX = 8.64; MM = 1000.0 / VOX
cv2.setNumThreads(3)

# ----------------------------------------------------------------------------------------------------------------- fields
def eig2(Jxx, Jxz, Jzz):
    tr = Jxx + Jzz; det = Jxx * Jzz - Jxz * Jxz; disc = np.sqrt(np.maximum(tr * tr / 4 - det, 0)); l1 = tr / 2 + disc; l2 = tr / 2 - disc
    theta = 0.5 * np.arctan2(2 * Jxz, Jxx - Jzz); coh = (l1 - l2) / (l1 + l2 + 1e-12); return theta.astype(np.float32), coh.astype(np.float32)

def aniso_kernel(ang, s_along, s_across):
    h = int(np.ceil(3 * s_along)); yy, xx = np.mgrid[-h:h + 1, -h:h + 1].astype(np.float32)
    u = xx * np.cos(ang) + yy * np.sin(ang); v = -xx * np.sin(ang) + yy * np.cos(ang)
    k = np.exp(-u * u / (2 * s_along ** 2) - v * v / (2 * s_across ** 2)); return (k / k.sum()).astype(np.float32)

def st_aniso(s, sd, s_across, s_along, nori):
    """Anisotropic structure tensor: gradients at sigma sd; the tensor components integrated with an oriented Gaussian
    (sigma_along along the preliminary lamina tangent, sigma_across across it). Returns normal angle theta, coherence."""
    gx = ndi.gaussian_filter(s, sd, order=(0, 1)); gz = ndi.gaussian_filter(s, sd, order=(1, 0)); J = [gx * gx, gx * gz, gz * gz]; del gx, gz
    si0 = 2 * s_across; th0, _ = eig2(*[ndi.gaussian_filter(c, si0) for c in J])                 # preliminary (isotropic, small) orientation
    psi0 = np.mod(th0 + np.pi / 2, np.pi); u = psi0 / (np.pi / nori); k1 = np.floor(u).astype(int); fr = (u - k1).astype(np.float32); k1 = np.mod(k1, nori); k2 = np.mod(k1 + 1, nori)
    out = [np.zeros_like(c) for c in J]
    for k in range(nori):                                                                            # each pixel blends the two nearest orientation bins (a hard bin choice makes the angle jump at bin borders)
        W = np.where(k1 == k, 1 - fr, 0) + np.where(k2 == k, fr, 0)
        if not (W > 0).any(): continue
        ker = aniso_kernel(k * np.pi / nori, s_along, s_across)
        for c in range(3): out[c] += W * cv2.filter2D(J[c], -1, ker, borderType=cv2.BORDER_REFLECT)
    th, coh = eig2(*out); return th, coh, (out[0] + out[2]).astype(np.float32)

def merge_plateaus(P, r):
    """Plateaus of one sign closer than r (the loop radius) are one defect (a disc split by an invalid band): cell-weighted centroid."""
    P = sorted(P, key=lambda t: -t[2]); out = []
    for cx, cy, nc, v in P:
        for o in out:
            if np.hypot(o[0] - cx, o[1] - cy) <= r: w = o[2] + nc; o[0] = (o[0] * o[2] + cx * nc) / w; o[1] = (o[1] * o[2] + cy * nc) / w; o[2] = w; o[3] = (o[3] * o[2] + v * nc) / (o[2] + nc); break
        else: out.append([cx, cy, nc, v])
    return [tuple(o) for o in out]

def dark_mask(g, mask, win=65):
    """Gap pixels: below the local midpoint between the min and max of g over a (win x win) window (~2 pitches): the same
    rule in compact lamination, open lobes and the phantom's empty background."""
    lo = ndi.minimum_filter(g, win); hi = ndi.maximum_filter(g, win); thr = 0.5 * (lo + hi); return (g < thr) & mask, float(np.median(thr[mask]))

def prep_section(raw, p):
    """raw (Z, X) uint8 -> dict of per-section fields (float32) and the defect lists at R0/R1 (window voxel coordinates)."""
    mask = raw > 0
    if mask.sum() < 100: mask = np.ones_like(mask)                                                   # a (near-)empty section inside a slab: keep the fields defined (the trace section is gated in run_slab)
    s = stripe_removal(raw.astype(np.float32) / 255.0, mask)
    th, coh, tr = st_aniso(s, p['sd'], p['s_across'], p['s_along'], p['nori']); valid = mask & (tr >= p['tr_frac'] * float(np.median(tr[mask]))); coh = coh * valid   # the anisotropic integration inflates the coherence of noise: validity = gradient energy, not coherence
    g = ndi.gaussian_filter(s, p['sigma_r']).astype(np.float32); mad = float(np.median(np.abs(g[mask] - np.median(g[mask])))) + 1e-6
    qr = (coh * np.cos(2 * th)).astype(np.float32); qi = (coh * np.sin(2 * th)).astype(np.float32)
    st = p['stride']; ths, cos_ = th[::st, ::st].copy(), coh[::st, ::st].copy(); defs = {}
    for R in (p['R0'], p['R1']):
        idx = index_map(ths, cos_, cos_ > 1e-6, st, R * MM)
        defs[R] = {'plus': merge_plateaus([(cx * st, cy * st, nc, v) for cx, cy, nc, v in plateaus(idx, 0.3, 0.75, 2)], R * MM), 'minus': merge_plateaus([(cx * st, cy * st, nc, v) for cx, cy, nc, v in plateaus(idx, -0.75, -0.3, 2)], R * MM)}
    dk, thr = dark_mask(g, mask); r = int(p['seam_hw']); se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    seam = cv2.morphologyEx(dk.astype(np.uint8), cv2.MORPH_OPEN, se).astype(bool)                   # dark gaps at least 2*seam_hw wide
    return {'mask': mask, 'g': g, 'qr': qr, 'qi': qi, 'mad': mad, 'defs': defs, 'seam': seam, 'dark_thr': thr, 'coh_med': float(np.median(coh[mask])), 'valid_frac': float(valid[mask].mean())}

# ---------------------------------------------------------------------------------------------------------------- sampling
def bilin(a, x, z):
    """Bilinear sample of a[z, x] at float coordinates (arrays); 0 outside."""
    Z, X = a.shape; x = np.asarray(x, np.float64); z = np.asarray(z, np.float64); ok = (x >= 0) & (x <= X - 1) & (z >= 0) & (z <= Z - 1)
    xc = np.clip(x, 0, X - 1.000001); zc = np.clip(z, 0, Z - 1.000001); x0 = np.floor(xc).astype(int); z0 = np.floor(zc).astype(int); fx = xc - x0; fz = zc - z0
    v = (a[z0, x0] * (1 - fx) * (1 - fz) + a[z0, x0 + 1] * fx * (1 - fz) + a[z0 + 1, x0] * (1 - fx) * fz + a[z0 + 1, x0 + 1] * fx * fz); return np.where(ok, v, 0.0)

def orient_at(F, x, z):
    qr = bilin(F['qr'], x, z); qi = bilin(F['qi'], x, z); return 0.5 * np.arctan2(qi, qr), np.hypot(qr, qi)

# ------------------------------------------------------------------------------------------------------------ apex geometry
def opening_direction(F, ax, az, r):
    """Fit the +1/2 director model psi = phi/2 + c (psi = normal + pi/2) with a FREE centre on an annulus of radii
    0.4 r .. 1.0 r about the plateau centroid (Nelder-Mead on xc, zc, c; coherence-weighted). Returns the unit opening
    direction d = (cos 2c, sin 2c) in (x, z) (the arms lie along +d, the turn at -d), the refined centre, the circular
    residual of the doubled-angle fit (0 = perfect +1/2) and the number of weighted samples."""
    from scipy.optimize import minimize
    phi = np.linspace(0, 2 * np.pi, 48, endpoint=False); rr_ = np.array([0.4, 0.6, 0.8, 1.0]) * r; PH = np.repeat(phi[None], len(rr_), 0).ravel(); RR = np.repeat(rr_[:, None], len(phi), 1).ravel()
    mk = F['mask'].astype(np.float32)
    def cost(q):
        xc, zc = q[0], q[1]; x = xc + RR * np.cos(PH); z = zc + RR * np.sin(PH); th, c = orient_at(F, x, z); w = c * (bilin(mk, x, z) > 0.5)
        if w.sum() <= 1e-6: return 2.0, None, 0
        e = np.sum(w * np.exp(1j * (2 * (th + np.pi / 2) - PH))); return 1.0 - np.abs(e) / w.sum(), np.angle(e), int((w > 0).sum())
    res = minimize(lambda q: cost(q)[0], np.array([ax, az], float), method='Nelder-Mead', options={'xatol': 0.5, 'fatol': 1e-4, 'maxiter': 200, 'initial_simplex': np.array([[ax, az], [ax + 0.3 * r, az], [ax, az + 0.3 * r]])})
    cval, m, nsamp = cost(res.x)
    if m is None or np.hypot(res.x[0] - ax, res.x[1] - az) > r: cval, m, nsamp = cost(np.array([ax, az], float)); res.x = np.array([ax, az], float)
    if m is None: return None, (ax, az), None, 0
    return np.array([np.cos(m), np.sin(m)]), (float(res.x[0]), float(res.x[1])), float(np.sqrt(-2 * np.log(max(1e-9, 1 - cval)))), nsamp

def chord_peaks(F, o, nc, S, p):
    """Lamina crossings on the chord: s in [-S, S] along nc from the origin o; peaks of g with prominence >= det_mad x the
    noise MAD of the ridge image (the in-mask MAD of the whole section or of the profile is signal-dominated: a regular
    lamination has peak prominence of only ~2 such MADs, so '3 MAD' is read as 3 noise MADs), width >= min_w, separation
    >= min_sep. Returns s, prominences, in-mask flags and the MAD used."""
    s = np.arange(-S, S + 1, 1.0); x = o[0] + s * nc[0]; z = o[1] + s * nc[1]; v = bilin(F['g'], x, z); inm = bilin(F['mask'].astype(np.float32), x, z) > 0.5
    if inm.sum() < 20: return s[:0], v[:0], inm, F['nmad']
    mad = F['nmad']                                                                                   # noise MAD of the ridge image (slab-wide, from adjacent-section differences)
    pk, pr = find_peaks(np.where(inm, v, v.min() - 1), prominence=p['det_mad'] * mad, width=p['min_w'], distance=p['min_sep']); return s[pk], pr['prominences'], inm, mad

# ------------------------------------------------------------------------------------------------------------- ridge follow
def follow(F, p0, h0, o, d, nc, p, mad):
    """2-D ridge following from p0 with initial heading h0 (unit) along the lamina tangent; re-anchoring on the ridge along
    the local normal; stops when the trace re-crosses the chord (u = (p - o).d >= 0 after having gone deeper than
    min_depth), leaves the mask/window, loses the ridge or exceeds max_steps. Returns the polyline and diagnostics."""
    step, ra, w, lost_max, cmin = p['step'], p['ra'], p['prom_w'], p['lost'], p['coh_min']; thr = p['ridge_mad'] * mad; thr3 = p['det_mad'] * mad; Z, X = F['g'].shape; ra_step = p['ra_step']; cos_turn = np.cos(np.radians(p['max_turn'])); inertia = p['inertia']
    offs = np.arange(-ra, ra + 0.01, 0.5); woffs = np.arange(-w, w + 1, 1.0); pts = [p0.copy()]; prom = []; pr = p0.copy(); h = h0.copy(); lost = 0; deep = False; status = 'max steps'; u_prev = 0.0; low = 0
    for it in range(p['max_steps']):
        th, c = orient_at(F, pr[0], pr[1]); th = float(th); c = float(c); t = np.array([-np.sin(th), np.cos(th)])
        if t @ h < 0: t = -t
        if c < cmin or (t @ h) < cos_turn: t = h; low += 1                                          # no orientation, or a turn sharper than max_turn per step (a junction, not a lamina): coast along the heading
        t = (1 - inertia) * t + inertia * h; t = t / np.linalg.norm(t)                               # heading inertia damps voxel-scale orientation noise
        pn = pr + step * t; n = np.array([-t[1], t[0]])
        vals = bilin(F['g'], pn[0] + offs * n[0], pn[1] + offs * n[1]); k0 = len(offs) // 2
        lm = np.nonzero((vals[1:-1] >= vals[:-2]) & (vals[1:-1] >= vals[2:]))[0] + 1                   # interior local maxima of the normal profile (a window-edge maximum is not a ridge)
        if len(lm):
            j = int(lm[np.argmin(np.abs(lm - k0))]); dlt = offs[j]; a, b, cc = vals[j - 1], vals[j], vals[j + 1]; den = a - 2 * b + cc
            if den < 0: dlt += 0.5 * (a - cc) / den * 0.5
            dlt = float(np.clip(dlt, -ra_step, ra_step))                                           # re-anchor to the NEAREST ridge, at most ra_step per step (never a hop to the brightest neighbour)
        else: dlt = 0.0
        pn = pn + dlt * n
        if not (0 <= pn[0] < X - 1 and 0 <= pn[1] < Z - 1) or bilin(F['mask'].astype(np.float32), pn[0], pn[1]) < 0.5: status = 'left mask'; break
        prof = bilin(F['g'], pn[0] + woffs * n[0], pn[1] + woffs * n[1]); k0 = len(woffs) // 2; pv = float(prof[k0] - max(prof[:k0].min(), prof[k0 + 1:].min())); prom.append(pv)
        lost = lost + 1 if pv < thr else 0
        if lost > lost_max: status = 'ridge lost'; break
        h = t / np.linalg.norm(t); pr = pn; pts.append(pr.copy()); u = float((pr - o) @ d)                       # heading = the tangent stepped along (the re-anchor shift is across the lamina, not a heading)
        if u < -p['min_depth']: deep = True
        if deep and u >= 0:
            f = u_prev / (u_prev - u) if u_prev != u else 1.0; pc = pts[-2] + f * (pts[-1] - pts[-2]); pts[-1] = pc; status = 'crossed'; break
        u_prev = u
    P = np.array(pts); prom = np.array(prom) if prom else np.zeros(0)
    return {'pts': P, 'status': status, 'ridge_frac': float((prom >= thr).mean()) if len(prom) else 0.0, 'ridge_frac3': float((prom >= thr3).mean()) if len(prom) else 0.0, 'n_low_coh': low, 's_end': float((P[-1] - o) @ nc), 'u_end': float((P[-1] - o) @ d), 'len': float(len(P) * step)}

def poly_dist(A, B):
    """Mean distance from the points of A to the polyline points of B (voxels)."""
    if len(A) < 2 or len(B) < 2: return None
    d, _ = cKDTree(B).query(A); return float(d.mean())

def polygon_mask(P, chord_pts, shape):
    """Raster of the region enclosed by the trace polyline P (A -> B) and the chord segment back (B -> A)."""
    from PIL import Image, ImageDraw
    img = Image.new('L', (shape[1], shape[0]), 0); poly = [(float(x), float(z)) for x, z in P] + [(float(x), float(z)) for x, z in chord_pts]
    ImageDraw.Draw(img).polygon(poly, fill=1, outline=1); return np.array(img, bool)

# ------------------------------------------------------------------------------------------------------------------ operator
def trace_apex(secs, k, apex, p, off):
    """All trace attempts for one apex in trace section k; returns the attempt records (accepted ones carry HAIRPIN-TRACED)."""
    F = secs[k]; Z, X = F['g'].shape; ax, az = apex[0], apex[1]; R0v = p['R0'] * MM; L = p['L_mm'] * MM; S = p['S_mm'] * MM
    d, ctr, res, nsamp = opening_direction(F, ax, az, R0v); base = {'apex_xz': [round(float(ax), 1), round(float(az), 1)], 'apex_cells': int(apex[2]), 'apex_index': round(float(apex[3]), 3), 'apex_refined_xz': [round(ctr[0], 1), round(ctr[1], 1)]}
    if d is None or res > p['fit_res_max']: return [dict(base, status='REJECTED', reason='no +1/2 direction fit', fit_res=None if res is None else round(res, 3))]
    ax, az = ctr                                                                                      # the fitted centre is the apex used for the chord and the enclosure test
    o = np.array([ax, az]) + L * d; nc = np.array([-d[1], d[0]]); base.update({'open_dir': [round(float(d[0]), 3), round(float(d[1]), 3)], 'fit_res': round(res, 3), 'chord_origin': [round(float(o[0]), 1), round(float(o[1]), 1)]})
    if not (0 <= o[0] < X and 0 <= o[1] < Z) or not F['mask'][int(o[1]), int(o[0])]: return [dict(base, status='REJECTED', reason='chord origin outside mask/window')]
    s_pk, s_pr, inm, cmad = chord_peaks(F, o, nc, S, p); base['chord_mad'] = round(cmad, 4)
    A = sorted([s for s in s_pk if s < 0], key=lambda v: -v); B = sorted([s for s in s_pk if s > 0])           # ordinal 1 = innermost on each arm
    if not A or not B: return [dict(base, status='REJECTED', reason='no lamina crossing on an arm', n_A=len(A), n_B=len(B))]
    sp = np.diff(np.sort(s_pk)); spacing = float(np.median(sp)) if len(sp) else p['match_tol'] / 0.4; tol = max(4.0, min(p['match_tol'], 0.4 * spacing))
    # the core void of this nest: the wide-dark component nearest the (refined) apex within R0 (the innermost loop's interior, not a seam)
    lab, nl = ndi.label(F['seam']); core_void = np.zeros_like(F['seam'])
    if nl:
        yy, xx = np.nonzero(F['seam']); dd = np.hypot(xx - ax, yy - az); jx = int(np.argmin(dd))
        if dd[jx] <= R0v: core_void = lab == lab[yy[jx], xx[jx]]
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(p['enc_tol']) + 1, 2 * int(p['enc_tol']) + 1))
    mins = F['defs'][p['R0']]['minus']; plus = F['defs'][p['R0']]['plus']; out = []
    arm_lab = ('above', 'below') if nc[1] > 0.7 else ('below', 'above') if nc[1] < -0.7 else ('A', 'B')
    for i, sA in enumerate(A):
        rec = dict(base, status='REJECTED', arm_A={'ordinal': i + 1, 's': round(float(sA), 1), 'xz': [round(float(o[0] + sA * nc[0]), 1), round(float(o[1] + sA * nc[1]), 1)], 'label': arm_lab[0]}, n_A=len(A), n_B=len(B), chord_spacing=round(spacing, 1))
        p0 = o + sA * nc; fw = follow(F, p0, -d, o, d, nc, p, cmad); rec['trace_status'] = fw['status']; rec['ridge_frac'] = round(fw['ridge_frac'], 3); rec['ridge_frac_3mad'] = round(fw['ridge_frac3'], 3); rec['trace_len_vox'] = round(fw['len'], 1); rec['n_coast_steps'] = fw['n_low_coh']
        Pw = fw['pts'][::max(1, len(fw['pts']) // 400)]; rec['polyline_xz'] = [[round(float(x), 1), round(float(z), 1)] for x, z in Pw]
        if fw['status'] != 'crossed': rec['reason'] = 'trace ' + fw['status']; out.append(rec); continue
        rec['s_end'] = round(fw['s_end'], 1)
        if fw['s_end'] < 0: rec['reason'] = 'returned to the same arm'; out.append(rec); continue
        j = int(np.argmin(np.abs(np.array(B) - fw['s_end']))); sB = B[j]
        if abs(sB - fw['s_end']) > tol: rec['reason'] = 'unpaired endpoint'; out.append(rec); continue
        rec['arm_B'] = {'ordinal': j + 1, 's': round(float(sB), 1), 'xz': [round(float(o[0] + sB * nc[0]), 1), round(float(o[1] + sB * nc[1]), 1)], 'label': arm_lab[1]}; rec['nesting_equal'] = bool(i == j)
        bw = follow(F, o + sB * nc, -d, o, d, nc, p, cmad); rec['reverse_status'] = bw['status']
        if bw['status'] != 'crossed' or abs(bw['s_end'] - sA) > tol: rec['reason'] = 'reverse trace disagrees'; rec['reverse_s_end'] = round(bw['s_end'], 1); out.append(rec); continue
        P = fw['pts']; dd = poly_dist(P, bw['pts']); rec['fwd_rev_offset_vox'] = round(dd, 2)
        if dd > p['dmax']: rec['reason'] = 'reverse trace offset'; out.append(rec); continue
        if fw['ridge_frac'] < p['ridge_min']: rec['reason'] = 'ridge fraction below ridge_min'; out.append(rec); continue
        chord_pts = [P[-1], P[0]]; M = polygon_mask(P, chord_pts, (Z, X)); rec['enclosed_area_vox'] = int(M.sum()); Md = cv2.dilate(M.astype(np.uint8), disk).astype(bool)
        def pin(Mask, pts): return [q for q in pts if 0 <= int(round(q[1])) < Z and 0 <= int(round(q[0])) < X and Mask[int(round(q[1])), int(round(q[0]))]]
        ep_s = pin(M, plus); ep = pin(Md, plus); em = pin(M, mins); rec['enclosed_plus_half'] = len(ep); rec['enclosed_plus_half_strict'] = len(ep_s); rec['enclosed_minus_half'] = len(em)
        rec['apex_enclosed'] = bool(M[min(Z - 1, max(0, int(round(az)))), min(X - 1, max(0, int(round(ax))))])
        if mins: dm, _ = cKDTree(np.array([[q[0], q[1]] for q in mins])).query(P); rec['min_dist_minus_half_mm'] = round(float(dm.min() / MM), 3)
        else: rec['min_dist_minus_half_mm'] = None
        # seam test: a wide dark gap inside the polygon that is not the nest's core void (the component nearest the apex) is a delamination between laminae
        innermost = (i == 0 and j == 0); seam_px = int((F['seam'] & M & ~core_void).sum()); rec['seam_px_inner_region'] = seam_px; rec['innermost'] = innermost; rec['core_void_px_enclosed'] = int((core_void & M).sum())
        # continuity across sections: re-trace from the same chord crossing in neighbouring sections
        cont = {'sections': [k], 'offset_vox': [0.0], 'end_s': [round(fw['s_end'], 1)]}
        for direction in (1, -1):
            prev = P; prev_sA = sA; prev_end = fw['s_end']
            for jj in range(k + direction, len(secs) if direction > 0 else -1, direction):
                Fj = secs[jj]; sj, _, _, mj = chord_peaks(Fj, o, nc, S, p)
                if len(sj) == 0: break
                cand = sj[np.argmin(np.abs(sj - prev_sA))]
                if abs(cand - prev_sA) > tol: break
                tj = follow(Fj, o + cand * nc, -d, o, d, nc, p, mj)
                if tj['status'] != 'crossed' or abs(tj['s_end'] - prev_end) > tol: break
                od = poly_dist(tj['pts'], prev)
                if od is None or od > p['dmax']: break
                cont['sections'].append(jj); cont['offset_vox'].append(round(od, 2)); cont['end_s'].append(round(tj['s_end'], 1)); prev, prev_sA, prev_end = tj['pts'], cand, tj['s_end']
        n_cont = len(cont['sections']); rec['continuity'] = {'n_consecutive_sections': n_cont, 'sections': sorted(cont['sections']), 'mean_offset_vox': round(float(np.mean(cont['offset_vox'][1:])), 2) if n_cont > 1 else None, 'max_offset_vox': round(float(np.max(cont['offset_vox'][1:])), 2) if n_cont > 1 else None}
        fails = []
        if len(ep) != 1: fails.append('enclosed +1/2 != 1')
        if len(em) > 0: fails.append('enclosed -1/2 > 0')
        if seam_px >= p['seam_min_px']: fails.append('seam in enclosed region')
        if rec['min_dist_minus_half_mm'] is not None and rec['min_dist_minus_half_mm'] < p['nb_mm']: fails.append('closer than nb_mm to a -1/2')
        if n_cont < p['N']: fails.append('continuity < N')
        Pw = P[::max(1, len(P) // 400)]; rec['polyline_xz'] = [[round(float(x), 1), round(float(z), 1)] for x, z in Pw]
        rec['polyline_abs_zyx'] = [[round(float(z + off[1]), 1), float(off[0] + k), round(float(x + off[2]), 1)] for x, z in Pw[:: max(1, len(Pw) // 60)]]
        if fails: rec['reason'] = '; '.join(fails)
        else: rec['status'] = 'HAIRPIN-TRACED'; rec.pop('reason', None)
        out.append(rec)
    return out

# ------------------------------------------------------------------------------------------------------------------ overlay
def overlay_png(F, recs, path, p, scale=1.0):
    from PIL import Image, ImageDraw
    g = F['g']; m = F['mask']; lo, hi = np.percentile(g[m], [1, 99.5]); im = np.clip((g - lo) / (hi - lo + 1e-9), 0, 1); im = (im * 255 * m).astype(np.uint8)
    img = Image.fromarray(im).convert('RGB'); dr = ImageDraw.Draw(img); cols = [(255, 60, 60), (60, 220, 60), (80, 140, 255), (255, 200, 0), (255, 80, 255), (0, 220, 220), (255, 140, 0), (160, 255, 120)]
    for q in F['defs'][p['R0']]['minus']: x, z = q[0], q[1]; dr.line([(x - 6, z - 6), (x + 6, z + 6)], fill=(255, 0, 255), width=2); dr.line([(x - 6, z + 6), (x + 6, z - 6)], fill=(255, 0, 255), width=2)
    for q in F['defs'][p['R0']]['plus']: x, z = q[0], q[1]; dr.line([(x - 7, z), (x + 7, z)], fill=(255, 255, 0), width=2); dr.line([(x, z - 7), (x, z + 7)], fill=(255, 255, 0), width=2)
    n = 0
    if p.get('draw_rejected'):
        for r in recs:
            if r['status'] != 'HAIRPIN-TRACED' and 'polyline_xz' in r and len(r['polyline_xz']) > 1: dr.line([(x, z) for x, z in r['polyline_xz']], fill=(200, 60, 60), width=1)
    for r in recs:
        if r['status'] != 'HAIRPIN-TRACED': continue
        c = cols[n % len(cols)]; n += 1; pts = [(x, z) for x, z in r['polyline_xz']]; dr.line(pts, fill=c, width=2); dr.line([pts[-1], pts[0]], fill=c, width=1)
        for q in (r['arm_A']['xz'], r['arm_B']['xz']): dr.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=c, width=2)
    if scale != 1.0: img = img.resize((int(img.width * scale), int(img.height * scale)))
    img.save(path); return n

# ------------------------------------------------------------------------------------------------------------------- phantom
def phantom_slab(n=16, Z=1024, X=1024, K=6, pitch=28.0, sheet=14.0, rho0=20.0, seed=0, tilt=0.5, noise=0.25, seam_after=3, seam_gap=30.0):
    """Synthetic xz sections of nested hairpin columns (a flattened roll's edge). Nest 1 (upper band): K laminae nested
    around a short vertical core slit at (xc, zc), arms to +x up to the window edge; a seam (gap widened by seam_gap)
    between upper-arm laminae seam_after and seam_after+1 for x > xc + 10 (inside the chord); lamina K-1 (outermost) terminates on the
    lower arm at x = xc + 300. Nest 2 (lower band) opens to -x. Sections drift by `tilt` voxels per section; Gaussian
    noise, column stripes, a mask margin. Truth: upper-arm ordinal i pairs with lower-arm ordinal i (i = 1..K);
    laminae > seam_after on nest 1 enclose the seam and must be rejected; the outermost lamina of nest 1 is lost."""
    rng = np.random.default_rng(seed); zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); out = np.zeros((n, Z, X), np.uint8)
    def nest(xc, zc, h, sign, zshift, seam, term):
        dz = np.clip(np.abs(zz - zc - zshift) - h, 0, None); dx = (xc - xx) * sign; dxp = np.clip(dx, 0, None); dist = np.sqrt(dxp * dxp + dz * dz); img = np.zeros((Z, X), np.float32)
        for i in range(K):
            rho = rho0 + i * pitch; d_i = dist - rho; amp = np.ones((Z, X), np.float32); upper = zz < zc + zshift
            if seam and i > seam_after: d_i = d_i - seam_gap * np.clip((sign * (xx - xc) - 10) / 40.0, 0, 1) * upper * (dx < 0)
            if term and i == K - 1: amp = np.where(upper, 1.0, np.clip(((xc + sign * 300) - xx) * sign / 20.0, 0, 1)).astype(np.float32)
            img += amp * np.exp(-d_i * d_i / (2 * (sheet / 2.355) ** 2))
        return img
    for k in range(n):
        zs = tilt * (k - n // 2); img = nest(300.0, 250.0, 10.0, +1, zs, True, True) + nest(X - 300.0, 740.0, 10.0, -1, -zs, False, False)
        img = 0.15 + 0.55 * img + noise * 0.55 * rng.standard_normal((Z, X)).astype(np.float32); img += 0.05 * rng.standard_normal(X)[None, :]
        img = ndi.gaussian_filter(img, 1.0); m = (xx > 12) & (xx < X - 12) & (zz > 8); out[k] = (np.clip(img, 0, 1) * 255 * m).astype(np.uint8)
    truth = {'K': K, 'pitch': pitch, 'sheet': sheet, 'rho0': rho0, 'seam_after_ordinal': seam_after + 1, 'nest1': {'xc': 300, 'zc': 250, 'h': 10, 'opens': '+x', 'seam': True, 'terminating_ordinal': K}, 'nest2': {'xc': X - 300, 'zc': 740, 'h': 10, 'opens': '-x'}, 'tilt_vox_per_section': tilt, 'noise': noise}
    return out, truth

# ---------------------------------------------------------------------------------------------------------------------- main
def run_slab(stack, p, off, out_dir, tag):
    """stack (n, Z, X) uint8; off = (y0, z0, x0) absolute level-0 origin. Writes <out>/<tag>.json and <tag>_overlay.png."""
    t0 = time.time(); n = len(stack); k = p['sec'] if p['sec'] is not None else n // 2; secs = []; os.makedirs(out_dir, exist_ok=True)
    if (stack[k] > 0).mean() < 0.01:                                                                 # outside the scroll: nothing to trace
        summ = {'tag': tag, 'status': 'no mask', 'origin_zyx_l0': [off[1], off[0], off[2]], 'shape_nZX': list(stack.shape), 'trace_section': k, 'trace_y': off[0] + k, 'mask_frac': float((stack[k] > 0).mean()), 'defects_trace_section': {}, 'n_apexes_attempted': 0, 'n_trace_attempts': 0, 'n_accepted': 0, 'rejection_reasons': {}, 'per_section_defects': [], 'noise_mad': None, 'signal_mad_trace_section': None, 'secs_prep': 0, 'secs_trace': 0, 'overlay_png': None, 'records': []}
        json.dump(summ, open(os.path.join(out_dir, f'{tag}.json'), 'w'), indent=1); return summ
    for i in range(n): secs.append(prep_section(stack[i], p))
    # noise scale of the ridge image: MAD of the difference of adjacent sections / sqrt 2 (laminae are continuous across 8.64 um; the difference is noise plus a small tilt term, so this is conservative)
    nm = []
    for i in range(n - 1):
        m = secs[i]['mask'] & secs[i + 1]['mask']; dd = (secs[i]['g'] - secs[i + 1]['g'])[m]; nm.append(float(np.median(np.abs(dd - np.median(dd))) / np.sqrt(2)))
    nmad = float(np.median(nm)) if nm else secs[0]['mad']
    for F in secs: F['nmad'] = nmad
    t1 = time.time(); F = secs[k]; dR0, dR1 = F['defs'][p['R0']], F['defs'][p['R1']]
    per_sec = [{'sec': i, 'y': off[0] + i, 'plus_R0': len(s['defs'][p['R0']]['plus']), 'minus_R0': len(s['defs'][p['R0']]['minus']), 'plus_R1': len(s['defs'][p['R1']]['plus']), 'minus_R1': len(s['defs'][p['R1']]['minus']), 'coh_med': round(s['coh_med'], 3), 'valid_frac': round(s['valid_frac'], 3), 'mad': round(s['mad'], 4)} for i, s in enumerate(secs)]
    recs = []
    for apex in dR0['plus']:
        stable = any(np.hypot(q[0] - apex[0], q[1] - apex[1]) <= p['R1'] * MM for q in dR1['plus'])
        for r in trace_apex(secs, k, apex, p, off): r['apex_stable_R1'] = bool(stable); recs.append(r)
    acc = [r for r in recs if r['status'] == 'HAIRPIN-TRACED']; attempts = [r for r in recs if 'arm_A' in r]
    reasons = {}
    for r in recs:
        if r['status'] != 'HAIRPIN-TRACED': reasons[r.get('reason', '?')] = reasons.get(r.get('reason', '?'), 0) + 1
    os.makedirs(out_dir, exist_ok=True); png = os.path.join(out_dir, f'{tag}_overlay.png'); n_drawn = overlay_png(F, recs, png, p)
    summ = {'tag': tag, 'vox_um': VOX, 'origin_zyx_l0': [off[1], off[0], off[2]], 'shape_nZX': list(stack.shape), 'trace_section': k, 'trace_y': off[0] + k, 'params': p,
            'defects_trace_section': {f'plus_half_R{p["R0"]}': len(dR0['plus']), f'minus_half_R{p["R0"]}': len(dR0['minus']), f'plus_half_R{p["R1"]}': len(dR1['plus']), f'minus_half_R{p["R1"]}': len(dR1['minus'])},
            'apexes_R0_xz': [[round(float(q[0]), 1), round(float(q[1]), 1)] for q in dR0['plus']], 'minus_R0_xz': [[round(float(q[0]), 1), round(float(q[1]), 1)] for q in dR0['minus']],
            'n_apexes_attempted': len(dR0['plus']), 'n_trace_attempts': len(attempts), 'n_accepted': len(acc), 'rejection_reasons': reasons, 'per_section_defects': per_sec,
            'noise_mad': round(nmad, 5), 'signal_mad_trace_section': round(F['mad'], 5), 'secs_prep': round(t1 - t0, 1), 'secs_trace': round(time.time() - t1, 1), 'overlay_png': os.path.basename(png), 'traces_drawn': n_drawn, 'records': recs}
    json.dump(summ, open(os.path.join(out_dir, f'{tag}.json'), 'w'), indent=1); return summ

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--npy', default=None, help='local (n, Z, X) uint8 y-slab'); ap.add_argument('--src', default='s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/0')
    ap.add_argument('--y', type=int, default=5820); ap.add_argument('--n', type=int, default=16); ap.add_argument('--z0', type=int, default=7936); ap.add_argument('--z1', type=int, default=8704); ap.add_argument('--x0', type=int, default=1280); ap.add_argument('--x1', type=int, default=2304)
    ap.add_argument('--tag', default='slab'); ap.add_argument('--sec', type=int, default=None, help='trace section index in the slab (default n//2)'); ap.add_argument('--tile_z', type=int, default=0, help='process in z-tiles of this height (0 = whole)'); ap.add_argument('--tile_ov', type=int, default=256)
    ap.add_argument('--N', type=int, default=8, help='required consecutive sections of ridge continuity (prov.)'); ap.add_argument('--R0', type=float, default=0.5); ap.add_argument('--R1', type=float, default=1.0); ap.add_argument('--stride', type=int, default=4)
    ap.add_argument('--sd', type=float, default=1.5); ap.add_argument('--s_across', type=float, default=3.0); ap.add_argument('--s_along', type=float, default=12.0); ap.add_argument('--nori', type=int, default=12); ap.add_argument('--tr_frac', type=float, default=0.25, help='orientation valid where the tensor energy >= tr_frac x its in-mask median (voids and empty regions carry no director)'); ap.add_argument('--sigma_r', type=float, default=3.5, help='ridge image smoothing (sheet-level ridge; the fibre plies are ~6-8 vox)')
    ap.add_argument('--L_mm', type=float, default=0.8, help='chord distance from the apex along the opening direction'); ap.add_argument('--S_mm', type=float, default=1.5, help='chord half-length'); ap.add_argument('--min_w', type=float, default=3.0); ap.add_argument('--min_sep', type=int, default=8, help='minimum separation of lamina crossings on the chord (vox)')
    ap.add_argument('--step', type=float, default=1.0); ap.add_argument('--ra', type=float, default=5.0, help='re-anchor search half-window along the normal (vox); the nearest interior local maximum is taken'); ap.add_argument('--ra_step', type=float, default=2.0, help='maximum re-anchor shift per step (vox)'); ap.add_argument('--inertia', type=float, default=0.5, help='heading inertia of the follower (0 = pure tangent)'); ap.add_argument('--max_turn', type=float, default=45.0, help='maximum tangent turn per step (deg); sharper = junction, the follower coasts'); ap.add_argument('--prom_w', type=int, default=22); ap.add_argument('--lost', type=int, default=15, help='steps the follower may coast without a ridge (about one sheet thickness)'); ap.add_argument('--coh_min', type=float, default=0.05); ap.add_argument('--min_depth', type=float, default=10.0); ap.add_argument('--max_steps', type=int, default=4000)
    ap.add_argument('--det_mad', type=float, default=3.0, help='lamina crossing on the chord: peak prominence >= det_mad x noise MAD'); ap.add_argument('--ridge_mad', type=float, default=3.0, help='follow gate: ridge present if prominence >= ridge_mad x noise MAD'); ap.add_argument('--match_tol', type=float, default=8.0); ap.add_argument('--dmax', type=float, default=3.0); ap.add_argument('--ridge_min', type=float, default=0.9); ap.add_argument('--seam_hw', type=int, default=12, help='seam = dark gap at least 2*seam_hw wide (vox)'); ap.add_argument('--seam_min_px', type=int, default=100, help='seam pixels inside the region needed to reject (raster noise floor)'); ap.add_argument('--enc_tol', type=int, default=12, help='a +1/2 counts as enclosed within this many voxels of the polygon (the innermost loop carries the defect on itself)'); ap.add_argument('--nb_mm', type=float, default=1.0); ap.add_argument('--fit_res_max', type=float, default=1.0); ap.add_argument('--draw_rejected', type=int, default=1, help='draw rejected attempts (thin red) on the overlay')
    ap.add_argument('--phantom', type=int, default=0, help='1 = run on the synthetic nested-hairpin slab (code-path check only; never evidence about 0268)')
    a = ap.parse_args(); p = {k: v for k, v in vars(a).items() if k not in ('out', 'npy', 'src', 'y', 'n', 'z0', 'z1', 'x0', 'x1', 'tag', 'tile_z', 'tile_ov', 'phantom')}
    if a.phantom:
        stack, truth = phantom_slab(n=a.n); off = (0, 0, 0); os.makedirs(a.out, exist_ok=True); json.dump(truth, open(os.path.join(a.out, f'{a.tag}_truth.json'), 'w'), indent=1)
    elif a.npy: stack = np.load(a.npy, mmap_mode='r'); meta = json.load(open(a.npy[:-4] + '.json')) if os.path.exists(a.npy[:-4] + '.json') else {}; off = tuple(meta.get('origin_yzx', (a.y, a.z0, a.x0)))
    else:
        from core_native import L0; src = L0(a.src, threads=3); stack, ft = src.slab(a.y, a.n, a.z0, a.z1, a.x0, a.x1); off = (a.y, a.z0, a.x0); print('fetch', json.dumps(ft), flush=True)
    if a.tile_z <= 0 or stack.shape[1] <= a.tile_z:
        s = run_slab(np.asarray(stack), p, off, a.out, a.tag); print(json.dumps({k: s[k] for k in ('tag', 'defects_trace_section', 'n_apexes_attempted', 'n_trace_attempts', 'n_accepted', 'rejection_reasons', 'secs_prep', 'secs_trace')}), flush=True)
    else:
        Z = stack.shape[1]; z = 0; tiles = []
        while z < Z:
            z1 = min(Z, z + a.tile_z); sub = np.asarray(stack[:, z:z1]); tg = f'{a.tag}_z{off[1] + z}'
            s = run_slab(sub, p, (off[0], off[1] + z, off[2]), a.out, tg); tiles.append({k: s[k] for k in ('tag', 'origin_zyx_l0', 'shape_nZX', 'defects_trace_section', 'n_apexes_attempted', 'n_trace_attempts', 'n_accepted', 'rejection_reasons', 'secs_prep', 'secs_trace')})
            print(json.dumps(tiles[-1]), flush=True)
            if z1 >= Z: break
            z = z1 - a.tile_ov
        json.dump({'tag': a.tag, 'tiles': tiles, 'note': 'tiles overlap by tile_ov; apexes in the overlap are counted in both tiles'}, open(os.path.join(a.out, f'{a.tag}_tiles.json'), 'w'), indent=1)

if __name__ == '__main__': main()
