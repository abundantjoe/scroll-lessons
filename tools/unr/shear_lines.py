#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 item 3, shear-line detector at the scan's native 8.64 um (OME level 0), xz sections tracked along y.

A shear line is a line in the xz section across which the lamina stack on one side is displaced along the stacking
direction (z) relative to the other side, by a fractional or an integer number of spacings. What the native-resolution
data of PHerc0268 actually offers was measured on the real section y = 5828 (logs/dev/shear/control.json carries the
numbers) and dictates the design:
  * the fibre-scale texture decorrelates laterally within ~20 voxels and the sheet-scale pattern within ~30 voxels (a
    band 12 voxels to one side of a line matches the band on the other side with NCC 0.3-0.5 at best, and the matching
    shift agrees between candidate lines 12 voxels apart at only 24 % / 56 % of nodes at fibre / sheet scale), so a
    two-sided texture match cannot read the lamina phase across a line on its own: it is the SECONDARY measurement here;
  * what every slip produces, fractional or integer, is a line along which the fibre continuity is cut: a drop of the
    structure-tensor coherence on the line relative to both sides (DECL-UNR-1 item 3: "together with a local coherence
    drop"). This is the PRIMARY detection, chained along the line over >= n_min windows and tracked along y;
  * an integer slip of a locally periodic stack is invisible to any phase test by construction (the lattice maps onto
    itself); it is detectable only through the cut itself and wherever the stack is aperiodic within the match window.
Detection (pass 1, per section, per angle alpha of a 5-degree grid): shear the stripe-removed section so lines of angle
alpha become vertical; 2-D structure tensor (derivative sigma 2, integration sigma 8 vox); for every candidate line x0
(stride 4) and window of Lz rows (stride 16): coherence drop = 1 - coh(on the line, 2 g + 1 columns) / mean(coh of the
two side bands of w columns); domain: both sides in mask and coherent (>= coh_min). Nodes with drop > T_d chain along z
into segments of >= n_min windows; non-maximum suppression across x0 and alpha. T_d is the declared quantile of the
null (un-injected) window drops and n_min the smallest run length giving <= the declared false-positive rate of
segments per section on the null; both are fixed before any injected section is read.
Slip (pass 2, per detected segment): one-sided sheet-scale textures (slope from a tensor at derivative sigma 4,
integration 12; oriented average over w_tex voxels leftward for the left band and rightward for the right band, so no
average crosses the line), band NCC(s) over the segment's rows for z-shifts s of the right band; own peak (s1, v1);
continuity reference s_ref = median own peak of the strong (v1 >= c_min) parallel lines 12..24 voxels to either side;
slip = s1 - s_ref (voxels, signed: +x side displaced toward +z); E = v1 - max_{|s - s_ref| < s_min} NCC(s). Status
MEASURED when the own peak is strong and the reference agreed, else UNKNOWN (the segment stands on its coherence drop).
Along y: segments linked section to section (angle within one grid step, perpendicular distance <= link_dist, z-overlap
>= 50 %, slip agreement <= 0.25 pitch when both measured); persistence = number of consecutive sections of the line.
Output per section: segments with endpoints (z, x), angle, coherence drop (mean, max), slip + status + NCC values,
line id, persistence, first/last section.

Positive control (--control): the real 16-section slab (y 5820..5835, z 7936..8704, x 1280..2304 via core_native.L0.slab)
with a z-shift of the region on the +x side of a declared line injected into sections 4..11, for slips of half a spacing
(22 vox), one declared spacing (44 vox = census median pitch 380 um), two spacings (88) and one LOCAL integer pitch
(median peak spacing measured along the line on the un-injected section); 20 lines x 3 slip classes + 5 two-spacing
placements = 65. Detection rate per class, false positives per un-injected section (calibration slab, held-out slab
at another y, and the sections of each placement outside the injection +-2), slip error of MEASURED segments, PNG overlay.

usage: shear_lines.py <out_dir> --control [--slab slab.npy --null slab2.npy] [--threads 3]
       shear_lines.py <out_dir> --src s3://.../0 --y 5820 --n_sec 16 --z 7936 8704 --x 1280 2304 --T_d T --n_min N
"""
import argparse, json, os, sys, time, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb'))
from st_axis import stripe_removal, st_accumulate, st_eigen
VOX = 8.64

DEFAULTS = dict(pitch=44, sd=2.0, si=8.0, g=2, w=12, Lz=352, z_stride=16, x_stride=4, coh_min=0.3, mask_min=0.95,
                T_q=95.0, T_d=None, n_min=None, fp_rate=0.5, nms_dist=12, link_dist=8,
                sd2=4.0, si2=12.0, w_tex=32, sig_z=2.0, slope_box=16, slope_max=2.5, s_max=110, s_step=1, s_min=9, c_min=0.45, nb_min=12, nb_max=24, nb_need=3, nb_spread=6,
                angles=[float(a) for a in range(-40, 41, 5)])


# ------------------------------------------------------------------------------------------------------- primitives
def shear_image(img, tan_a, zc, order=1):
    """out(z, x') = img(z, x' + (z - zc) * tan_a): lines x = x' + (z - zc) tan_a of the original become vertical."""
    Z, X = img.shape; zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); xs = xx + (zz - zc) * tan_a
    return ndi.map_coordinates(img, [zz, xs], order=order, mode='constant', cval=0.0)


def oriented_box(img, slope, w, side=0):
    """Mean of img(z + u * slope(z, x), x + u) over u in [-w/2, w/2) (side 0), (-w, 0] (side -1: leftward only) or [0, w)
    (side +1: rightward only): a box average along the local layer direction; one-sided, it never crosses a line on the
    other side."""
    Z, X = img.shape; zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); acc = np.zeros_like(img); cnt = np.zeros_like(img)
    us = np.arange(-w / 2 + 0.5, w / 2, 1.0) if side == 0 else (np.arange(-w + 1, 1, 1.0) if side < 0 else np.arange(0, w, 1.0))
    for u in us.astype(np.float32):
        zq = zz + u * slope; xq = xx + u
        acc += ndi.map_coordinates(img, [zq, xq], order=1, mode='constant', cval=0.0)
        cnt += ndi.map_coordinates(np.ones_like(img), [zq, xq], order=1, mode='constant', cval=0.0)
    return acc / np.maximum(cnt, 1e-6)


def box_z(a, L):
    """Running sum over a centred window of L samples along axis 0 (zero outside)."""
    c = np.cumsum(np.concatenate([np.zeros((1,) + a.shape[1:], a.dtype), a], 0), 0); h0, h1 = L // 2, L - L // 2
    Z = a.shape[0]; lo = np.clip(np.arange(Z) - h0, 0, Z); hi = np.clip(np.arange(Z) + h1, 0, Z)
    return c[hi] - c[lo]


def runs_of(b):
    """Runs of True along axis 0 of a boolean (nz, nx): list of (j, i0, i1), inclusive."""
    out = []
    for j in range(b.shape[1]):
        col = b[:, j]; i = 0; n = len(col)
        while i < n:
            if not col[i]: i += 1; continue
            k = i
            while k + 1 < n and col[k + 1]: k += 1
            out.append((j, i, k)); i = k + 1
    return out


# ------------------------------------------------------------------------------------------- pass 1: coherence drop
def section_prep(sec_u8):
    mask = sec_u8 > 0; return stripe_removal(sec_u8.astype(np.float32) / 255.0, mask), mask


def coherence_nodes(img, mask, p):
    """Per angle: window coherence drop and domain over the (zc, x0) grid."""
    Z, X = img.shape; zc_img = Z / 2.0; g, w, Lz = p['g'], p['w'], p['Lz']
    x0s = np.arange(g + w + 2, X - g - w - 2, p['x_stride']); zcs = np.arange(Lz // 2, Z - Lz // 2 + 1, p['z_stride']); out = {}
    for alpha in p['angles']:
        ta = np.tan(np.radians(alpha)); I = shear_image(img, ta, zc_img); M = shear_image(mask.astype(np.float32), ta, zc_img) > 0.5
        J = st_accumulate([I], p['sd']); th, coh, _ = st_eigen(J, p['si']); coh = coh * M; del J, th
        on = ndi.uniform_filter1d(coh, 2 * g + 1, axis=1); side = ndi.uniform_filter1d(coh, w, axis=1); Mb = ndi.uniform_filter1d(M.astype(np.float32), 2 * (g + w) + 1, axis=1)
        CL, CR, CO, MB = [box_z(a, Lz)[zcs] / Lz for a in (side[:, x0s - g - w // 2], side[:, x0s + g + w // 2], on[:, x0s], Mb[:, x0s])]
        Io = ndi.uniform_filter1d(I * M, 2 * g + 1, axis=1); Is = ndi.uniform_filter1d(I * M, w, axis=1)                   # intensity on the line vs the sides (stripe-removed units): a seam is dark on the line
        IO, IL, IR = [box_z(a, Lz)[zcs] / Lz for a in (Io[:, x0s], Is[:, x0s - g - w // 2], Is[:, x0s + g + w // 2])]; dip = IO - 0.5 * (IL + IR)
        drop = 1 - CO / np.maximum(0.5 * (CL + CR), 1e-6); ok = (MB >= p['mask_min']) & (CL >= p['coh_min']) & (CR >= p['coh_min'])
        out[alpha] = dict(x0=x0s, zc=zcs, drop=drop.astype(np.float32), ok=ok, coh_side=(0.5 * (CL + CR)).astype(np.float32), dip=dip.astype(np.float32))
    return out, dict(Z=Z, X=X, zc_img=zc_img)


def segments_from_drop(nodes, geom, p, T_d, n_min):
    """Runs of >= n_min consecutive windows with ok & drop > T_d per (alpha, x0); NMS across x0 and alpha."""
    segs = []; Lz = p['Lz']; zci = geom['zc_img']
    for alpha, nd in nodes.items():
        acc = nd['ok'] & (nd['drop'] > T_d); ta = np.tan(np.radians(alpha))
        for j, i0, i1 in runs_of(acc):
            if i1 - i0 + 1 < n_min: continue
            x0 = float(nd['x0'][j]); z0, z1 = float(nd['zc'][i0] - Lz // 2), float(nd['zc'][i1] + Lz // 2); d = nd['drop'][i0:i1 + 1, j]
            segs.append(dict(alpha=float(alpha), x0=x0, z0=z0, z1=z1, x_at_z0=float(x0 + (z0 - zci) * ta), x_at_z1=float(x0 + (z1 - zci) * ta), drop_mean=float(d.mean()), drop_max=float(d.max()),
                             drop_sum=float(d.sum()), coh_side=float(nd['coh_side'][i0:i1 + 1, j].mean()), dip=float(nd['dip'][i0:i1 + 1, j].mean()), n_windows=int(i1 - i0 + 1)))
    segs.sort(key=lambda s: -s['drop_sum']); keep = []
    for s in segs:
        ok = True
        for t in keep:
            zo0, zo1 = max(s['z0'], t['z0']), min(s['z1'], t['z1'])
            if zo1 - zo0 < 0.5 * min(s['z1'] - s['z0'], t['z1'] - t['z0']): continue
            zm = 0.5 * (zo0 + zo1); xs = s['x0'] + (zm - zci) * np.tan(np.radians(s['alpha'])); xt = t['x0'] + (zm - zci) * np.tan(np.radians(t['alpha']))
            if abs(xs - xt) * np.cos(np.radians(0.5 * (s['alpha'] + t['alpha']))) <= p['nms_dist']: ok = False; break
        if ok: keep.append(s)
    return keep


# ---------------------------------------------------------------------------------------------- pass 2: slip measure
def sheet_textures(img, mask, alpha, p):
    """One-sided sheet-scale textures (TL for left bands, TR for right bands) in the sheared frame of angle alpha."""
    Z, X = img.shape; ta = np.tan(np.radians(alpha)); I = shear_image(img, ta, Z / 2.0); M = shear_image(mask.astype(np.float32), ta, Z / 2.0) > 0.5
    J = st_accumulate([I], p['sd2']); th, coh, _ = st_eigen(J, p['si2']); coh = coh * M
    slope = np.clip(-np.cos(th) / np.where(np.abs(np.sin(th)) < 1e-3, 1e-3, np.sin(th)), -4, 4).astype(np.float32)
    cs = ndi.uniform_filter(coh, p['slope_box']); sw = np.clip(ndi.uniform_filter(slope * coh, p['slope_box']) / np.maximum(cs, 1e-6), -p['slope_max'], p['slope_max'])
    def tex(side):
        T = ndi.gaussian_filter1d(oriented_box(I, sw, p['w_tex'], side), p['sig_z'], axis=0); T = T - ndi.uniform_filter1d(T, 2 * p['pitch'], axis=0); return (T * M).astype(np.float32)
    return tex(-1), tex(+1), M


def band_curve(TL, TR, M, x0, z0, z1, p):
    """NCC(s) of the left band (w columns, gap g) against the right band shifted by s, over rows z0..z1, for one line x0."""
    Z, X = TL.shape; g, w, smax = p['g'], p['w'], p['s_max']; xl = np.arange(x0 - g - w, x0 - g); xr = np.arange(x0 + g, x0 + g + w)
    if xl[0] < 0 or xr[-1] >= X: return None
    z0, z1 = int(max(0, z0)), int(min(Z, z1)); L = TL[z0:z1, xl] * M[z0:z1, xl]; shifts = np.arange(-smax, smax + 1, p['s_step']); out = np.full(len(shifts), -1.0, np.float32)
    LL = (L * L).sum()
    if LL <= 0: return None
    for i, s in enumerate(shifts):
        a, b = z0 + s, z1 + s
        if a < 0 or b > Z: continue
        R = TR[a:b, xr] * M[a:b, xr]; RR = (R * R).sum()
        if RR <= 0: continue
        out[i] = (L * R).sum() / np.sqrt(LL * RR)
    return shifts, out


def peak_of(curve, shifts, step):
    i = int(curve.argmax()); v = float(curve[i])
    if 0 < i < len(curve) - 1:
        ym, y0, yp = curve[i - 1], curve[i], curve[i + 1]; den = ym - 2 * y0 + yp; frac = 0.5 * (ym - yp) / den if abs(den) > 1e-6 else 0.0
        return float(shifts[i] + np.clip(frac, -0.5, 0.5) * step), v
    return float(shifts[i]), v


def measure_slip(seg, textures, p):
    """Own band peak on the segment's rows vs the median peak of strong parallel lines 12..24 vox to either side."""
    TL, TR, M = textures; x0 = int(round(seg['x0'])); z0, z1 = seg['z0'], seg['z1']; res = dict(slip=None, slip_status='UNKNOWN', ncc_own=None, ncc_cont=None, E=None, s_ref=None, n_ref=0)
    bc = band_curve(TL, TR, M, x0, z0, z1, p)
    if bc is None: return res
    shifts, c = bc; s1, v1 = peak_of(c, shifts, p['s_step']); res['ncc_own'] = round(v1, 3); res['s_own'] = round(s1, 1)
    refs = []
    for dx in range(p['nb_min'], p['nb_max'] + 1, p['x_stride']):
        for sgn in (-1, 1):
            b = band_curve(TL, TR, M, x0 + sgn * dx, z0, z1, p)
            if b is None: continue
            s, v = peak_of(b[1], b[0], p['s_step'])
            if v >= p['c_min']: refs.append(s)
    res['n_ref'] = len(refs)
    if v1 < p['c_min'] or len(refs) < p['nb_need']: return res
    s_ref = float(np.median(refs)); spread = float(np.median(np.abs(np.array(refs) - s_ref)))
    res['s_ref'] = round(s_ref, 1); res['ref_spread'] = round(spread, 1)
    if spread > p['nb_spread']: return res
    cont = float(c[np.abs(shifts - s_ref) < p['s_min']].max()); slip = s1 - s_ref
    res.update(slip=round(slip, 1), ncc_cont=round(cont, 3), E=round(v1 - cont, 3), slip_status='MEASURED' if abs(slip) >= p['s_min'] else 'CONTINUOUS')
    return res


# ------------------------------------------------------------------------------------------------------- per stack
def detect_section(sec_u8, p, T_d, n_min, want_nodes=False):
    img, mask = section_prep(sec_u8); nodes, geom = coherence_nodes(img, mask, p); segs = segments_from_drop(nodes, geom, p, T_d, n_min)
    cache = {}
    for s in segs:
        if p.get('no_slip'): s.update(dict(slip=None, slip_status='UNKNOWN', ncc_own=None, ncc_cont=None, E=None, s_ref=None, n_ref=0, slip_stage='skipped')); continue
        if s['alpha'] not in cache: cache[s['alpha']] = sheet_textures(img, mask, s['alpha'], p)
        s.update(measure_slip(s, cache[s['alpha']], p))
    return segs, (nodes if want_nodes else None), geom


def link_along_y(per_section, p, geom):
    zci = geom['zc_img']; next_id = 0; lines = {}
    for i, segs in enumerate(per_section):
        prev = per_section[i - 1] if i > 0 else []; taken = set()
        for s in segs:
            best, bd = None, None
            for t in prev:
                if abs(s['alpha'] - t['alpha']) > 5.5 or t['line_id'] in taken: continue
                zo0, zo1 = max(s['z0'], t['z0']), min(s['z1'], t['z1'])
                if zo1 - zo0 < 0.5 * min(s['z1'] - s['z0'], t['z1'] - t['z0']): continue
                zm = 0.5 * (zo0 + zo1); d = abs((s['x0'] + (zm - zci) * np.tan(np.radians(s['alpha']))) - (t['x0'] + (zm - zci) * np.tan(np.radians(t['alpha'])))) * np.cos(np.radians(s['alpha']))
                if d > p['link_dist']: continue
                if s.get('slip') is not None and t.get('slip') is not None and s['slip_status'] == t['slip_status'] == 'MEASURED' and abs(s['slip'] - t['slip']) > 0.25 * p['pitch']: continue
                if bd is None or d < bd: best, bd = t, d
            if best is not None: s['line_id'] = best['line_id']; taken.add(best['line_id'])
            else: s['line_id'] = next_id; next_id += 1
            lines.setdefault(s['line_id'], []).append(i)
    for segs in per_section:
        for s in segs: ys = lines[s['line_id']]; s['persistence'] = int(len(ys)); s['y_first'] = int(min(ys)); s['y_last'] = int(max(ys))
    return per_section


def detect_stack(stack, p, T_d, n_min, threads=1, want_nodes=False):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max(1, threads)) as ex: res = list(ex.map(lambda s: detect_section(s, p, T_d, n_min, want_nodes), [stack[i] for i in range(stack.shape[0])]))
    geom = res[0][2]; per = link_along_y([r[0] for r in res], p, geom)
    return per, [r[1] for r in res] if want_nodes else None, geom


def calibrate(nodes_list, geom, p, fp_rate, T_q):
    """T_d = the T_q-th percentile of the null window drops (domain nodes); n_min = the smallest run length at which the
    null stack yields <= fp_rate segments per section after NMS."""
    d = np.concatenate([nd[a]['drop'][nd[a]['ok']].ravel() for nd in nodes_list for a in nd]); T_d = float(np.percentile(d, T_q)); rate = None
    for n_min in range(3, 60):
        rate = sum(len(segments_from_drop(nd, geom, p, T_d, n_min)) for nd in nodes_list) / len(nodes_list)
        if rate <= fp_rate: break
    return T_d, n_min, dict(n_domain_nodes=int(len(d)), drop_quantiles={q: round(float(np.percentile(d, q)), 4) for q in (50, 90, 95, 99, 99.9)}, null_segments_per_section_at_n_min=rate)


# ------------------------------------------------------------------------------------------------ control harness
def inject(stack, alpha, x0, slip, secs, zc_img):
    """Shift the region on the +x side of the line x = x0 + (z - zc) tan(alpha) by `slip` voxels along z (+ = larger row
    index) in the listed sections; voxels rolled in from outside the volume are 0 (= outside the mask)."""
    out = stack.copy(); n, Z, X = stack.shape; ta = np.tan(np.radians(alpha)); zz, xx = np.mgrid[0:Z, 0:X]
    side = (xx - (x0 + (zz - zc_img) * ta)) * np.cos(np.radians(alpha)) > 0; s = int(round(slip)); sh = np.zeros((Z, X), np.uint8)
    for i in secs:
        sh[:] = 0
        if s > 0: sh[s:] = stack[i][:Z - s]
        elif s < 0: sh[:Z + s] = stack[i][-s:]
        else: sh[:] = stack[i]
        out[i] = np.where(side, sh, stack[i])
    return out


def local_pitch_along_line(sec_u8, alpha, x0, zc_img, p):
    """Median peak spacing (prominence >= 3 MAD, width >= 3) of vertical profiles within +-40 vox of the line."""
    Z, X = sec_u8.shape; mask = sec_u8 > 0; img = ndi.gaussian_filter(stripe_removal(sec_u8.astype(np.float32) / 255.0, mask), 1.0); ta = np.tan(np.radians(alpha)); gaps = []
    for dz in range(0, Z, 48):
        xc = int(round(x0 + (dz - zc_img) * ta))
        for dx in (-40, -20, 20, 40):
            x = xc + dx
            if not (0 <= x < X): continue
            col = img[:, x]; m = mask[:, x]
            if m.sum() < 200: continue
            mad = np.median(np.abs(col[m] - np.median(col[m]))) + 1e-6; pk, _ = find_peaks(np.where(m, col, 0), prominence=3 * mad, width=3); gaps += list(np.diff(pk))
    gaps = np.array(gaps); gaps = gaps[(gaps > 0.5 * p['pitch']) & (gaps < 1.6 * p['pitch'])]
    return int(round(np.median(gaps))) if len(gaps) >= 10 else p['pitch']


def seg_hits_line(seg, alpha, x0, zc_img, tol_x, tol_a=7.5):
    if abs(seg['alpha'] - alpha) > tol_a: return False
    zm = 0.5 * (seg['z0'] + seg['z1']); xs = seg['x0'] + (zm - zc_img) * np.tan(np.radians(seg['alpha'])); xt = x0 + (zm - zc_img) * np.tan(np.radians(alpha))
    return abs(xs - xt) * np.cos(np.radians(alpha)) <= tol_x


def overlay_png(path, panels, geom):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    n = len(panels); fig, axes = plt.subplots(1, n, figsize=(6.2 * n, 5.6)); axes = np.atleast_1d(axes)
    for ax, (sec, segs, inj, title) in zip(axes, panels):
        ax.imshow(sec, cmap='gray', vmin=0, vmax=255, interpolation='nearest'); ax.set_title(title, fontsize=8)
        if inj is not None:
            ta = np.tan(np.radians(inj['alpha'])); z = np.array([0, geom['Z'] - 1]); ax.plot(inj['x0'] + (z - geom['zc_img']) * ta, z, '--', color='cyan', lw=1.0, label='injected line')
        for s in segs:
            col = {'MEASURED': 'red', 'CONTINUOUS': 'orange', 'UNKNOWN': 'yellow'}[s['slip_status']]
            ax.plot([s['x_at_z0'], s['x_at_z1']], [s['z0'], s['z1']], '-', color=col, lw=1.6, alpha=0.9)
            ax.text(s['x_at_z1'] + 3, s['z1'], (f"{s['slip']:+.0f}" if s['slip'] is not None else '?') + f" p{s['persistence']}", color=col, fontsize=7)
        ax.set_xlim(0, geom['X']); ax.set_ylim(geom['Z'], 0); ax.set_xlabel('x (vox)'); ax.set_ylabel('z (vox)')
    axes[0].plot([], [], '-', color='red', label='segment, slip MEASURED'); axes[0].plot([], [], '-', color='yellow', label='segment, slip UNKNOWN'); axes[0].legend(loc='lower right', fontsize=7)
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close(fig)


def _one_placement(args):
    pl, slab_path, inj_secs, p, T_d, n_min, tol_x = args
    stack = np.load(slab_path); n, Z, X = stack.shape; zci = Z / 2.0
    st = inject(stack, pl['alpha'], pl['x0'], pl['slip'], inj_secs, zci); per, _, _ = detect_stack(st, p, T_d, n_min, threads=1)
    hits, fps, slips, meas = [], [], [], 0
    for i in range(n):
        h = [s for s in per[i] if seg_hits_line(s, pl['alpha'], pl['x0'], zci, tol_x)]; o = [s for s in per[i] if s not in h]
        hits.append(len(h) > 0); fps.append(len(o) if (inj_secs[0] - 2 <= i <= inj_secs[-1] + 2) else len(per[i]))
        if i in inj_secs:
            for s in h:
                if s['slip_status'] == 'MEASURED': slips.append(s['slip']); meas += 1
    in_inj = [hits[i] for i in inj_secs]; far = [i for i in range(n) if i < inj_secs[0] - 2 or i > inj_secs[-1] + 2]
    ids = set(s['line_id'] for i in inj_secs for s in per[i] if seg_hits_line(s, pl['alpha'], pl['x0'], zci, tol_x))
    pers = max([s['persistence'] for i in inj_secs for s in per[i] if s['line_id'] in ids], default=0)
    rec = dict(**pl, hit_sections=[i for i in range(n) if hits[i]], hit_frac_injected=float(np.mean(in_inj)), detected_all_injected=bool(all(in_inj)),
               detected_any_injected=bool(any(in_inj)), detected_pm2=bool(all(in_inj)) and not any(hits[i] for i in far), spill_sections=[i for i in range(n) if hits[i] and i not in inj_secs],
               n_measured=meas, slip_est_median=float(np.median(slips)) if slips else None, slip_err_median=float(np.median(np.abs(np.array(slips) - pl['slip']))) if slips else None,
               slip_sign_ok_frac=float(np.mean(np.sign(slips) == np.sign(pl['slip']))) if slips else None, fp_per_section=fps, fp_total=int(sum(fps)), persistence_max=int(pers), n_lines_on_injection=len(ids))
    return rec, per[8], st[8]


def run_control(a, p):
    out = a.out; os.makedirs(out, exist_ok=True); t_all = time.time(); log = lambda *s: print(*s, flush=True)
    stack = np.load(a.slab); n, Z, X = stack.shape; zci = Z / 2.0; null2 = np.load(a.null) if a.null and os.path.exists(a.null) else None
    # 1. null run + calibration (declared before any injected section is read)
    t = time.time(); per_null, nodes_null, geom = detect_stack(stack, p, T_d=9.0, n_min=10**6, threads=a.threads, want_nodes=True); log(f'null nodes {time.time() - t:.0f} s')
    T_d, n_min, stats = calibrate(nodes_null, geom, p, a.fp_rate, p['T_q']); p['T_d'], p['n_min'] = T_d, n_min; log(f'calibrated: T_d = {T_d:.4f} (p{p["T_q"]} of null window drops), n_min = {n_min} windows', stats)
    per_null = link_along_y([segments_from_drop(nd, geom, p, T_d, n_min) for nd in nodes_null], p, geom)
    img_cache = {}
    for i, segs in enumerate(per_null):
        img, mask = section_prep(stack[i])
        for s in segs:
            if p.get('no_slip'): s.update(dict(slip=None, slip_status='UNKNOWN', ncc_own=None, ncc_cont=None, E=None, s_ref=None, n_ref=0, slip_stage='skipped')); continue
            key = (i, s['alpha'])
            if key not in img_cache: img_cache[key] = sheet_textures(img, mask, s['alpha'], p)
            s.update(measure_slip(s, img_cache[key], p))
    del img_cache, nodes_null; fp_null = [len(s) for s in per_null]; log('null (calibration slab) segments per section:', fp_null)
    fp_held = None; per_h = None
    if null2 is not None: per_h, _, _ = detect_stack(null2, p, T_d, n_min, threads=a.threads); fp_held = [len(s) for s in per_h]; log('held-out null segments per section:', fp_held)
    # 2. placements (declared)
    angles = [0, 20, -20, 35]; xs = [380, 520, 660, 800, 940]; inj_secs = list(range(4, 12)); lines = [(al, x0) for x0 in xs for al in angles]; placements = []
    for li, (al, x0) in enumerate(lines):
        sgn = 1 if li % 2 == 0 else -1; p_loc = local_pitch_along_line(stack[8], al, x0, zci, p)
        placements += [dict(alpha=al, x0=x0, slip=sgn * (p['pitch'] // 2), cls='half'), dict(alpha=al, x0=x0, slip=sgn * p['pitch'], cls='one_declared'), dict(alpha=al, x0=x0, slip=p_loc, cls='one_local')]
        if li % 4 == 0: placements.append(dict(alpha=al, x0=x0, slip=2 * p['pitch'], cls='two'))
    log(f'{len(placements)} placements over {len(lines)} lines; injected sections {inj_secs[0]}..{inj_secs[-1]} of {n}')
    json.dump(dict(placements=placements, injected_sections=inj_secs, T_d=T_d, n_min=n_min, params=p), open(os.path.join(out, 'placements.json'), 'w'), indent=1)
    # 3. run
    from concurrent.futures import ProcessPoolExecutor
    tol_x = 12.0; results = []; panels = [(stack[8], per_null[8], None, f'un-injected y=5828: {len(per_null[8])} segment(s)')]; shown = set()
    with ProcessPoolExecutor(max(1, a.threads)) as ex:
        for k, (rec, segs8, sec8) in enumerate(ex.map(_one_placement, [(pl, a.slab, inj_secs, p, T_d, n_min, tol_x) for pl in placements])):
            results.append(rec); log(json.dumps({kk: rec[kk] for kk in ('alpha', 'x0', 'slip', 'cls', 'hit_frac_injected', 'detected_pm2', 'n_measured', 'slip_est_median', 'fp_total', 'persistence_max', 'spill_sections')}))
            if rec['cls'] not in shown and len(panels) < 5: shown.add(rec['cls']); panels.append((sec8, segs8, placements[k], f"{rec['cls']}: slip {placements[k]['slip']:+d}, angle {placements[k]['alpha']}, x0 {placements[k]['x0']}: hit {rec['hit_frac_injected']:.2f}"))
            json.dump(dict(partial=True, n_done=len(results), placements=results), open(os.path.join(out, 'control_partial.json'), 'w'))
    # 4. summary
    by = {}
    for r in results: by.setdefault(r['cls'], []).append(r)
    def summ(v):
        se = [r['slip_err_median'] for r in v if r['slip_err_median'] is not None]; sg = [r['slip_sign_ok_frac'] for r in v if r['slip_sign_ok_frac'] is not None]
        return dict(n=len(v), detected_pm2=int(sum(r['detected_pm2'] for r in v)), detection_rate_pm2=round(float(np.mean([r['detected_pm2'] for r in v])), 3),
                    detected_any_injected_section=int(sum(r['detected_any_injected'] for r in v)), all_injected_sections_hit=int(sum(r['detected_all_injected'] for r in v)),
                    mean_hit_frac=round(float(np.mean([r['hit_frac_injected'] for r in v])), 3), placements_with_measured_slip=int(sum(r['n_measured'] > 0 for r in v)),
                    slip_err_median_vox=round(float(np.median(se)), 1) if se else None, slip_sign_ok_frac=round(float(np.mean(sg)), 2) if sg else None,
                    fp_per_section=round(float(np.mean([np.mean(r['fp_per_section']) for r in v])), 3))
    summary = {c: summ(v) for c, v in by.items()}
    fp_far = [x for r in results for i, x in enumerate(r['fp_per_section']) if i < inj_secs[0] - 2 or i > inj_secs[-1] + 2]
    fp_band = [x for r in results for i, x in enumerate(r['fp_per_section']) if inj_secs[0] - 2 <= i <= inj_secs[-1] + 2]
    report = dict(vox_um=VOX, slab=a.slab, held_out_null=a.null, params=p, declared=dict(fp_rate_segments_per_section=a.fp_rate, T_quantile=p['T_q'], tol_x_vox=tol_x, tol_angle_deg=7.5, injected_sections=inj_secs),
                  T_d=T_d, n_min=n_min, calibration=stats,
                  null_fp_per_section=dict(calibration_slab=fp_null, mean=float(np.mean(fp_null)), held_out=fp_held, held_out_mean=float(np.mean(fp_held)) if fp_held else None),
                  fp_on_placements=dict(uninjected_sections_mean=float(np.mean(fp_far)), injected_band_off_line_mean=float(np.mean(fp_band))),
                  summary_per_class=summary, overall_detection_rate_pm2=float(np.mean([r['detected_pm2'] for r in results])), overall_any_section_rate=float(np.mean([r['detected_any_injected'] for r in results])),
                  n_placements=len(results), placements=results, null_segments=per_null, held_out_segments=per_h, runtime_s=round(time.time() - t_all, 1))
    json.dump(report, open(os.path.join(out, 'control.json'), 'w'), indent=1)
    overlay_png(os.path.join(out, 'overlay.png'), panels, geom)
    if os.path.exists(os.path.join(out, 'control_partial.json')): os.remove(os.path.join(out, 'control_partial.json'))
    log('summary', json.dumps(summary, indent=1)); log('null FP/section', np.mean(fp_null), 'held-out', fp_held and np.mean(fp_held), 'runtime s', round(time.time() - t_all))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--control', action='store_true'); ap.add_argument('--slab', default=None); ap.add_argument('--null', default=None)
    ap.add_argument('--src', default='s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/0'); ap.add_argument('--y', type=int, default=5820); ap.add_argument('--n_sec', type=int, default=16)
    ap.add_argument('--z', type=int, nargs=2, default=[7936, 8704]); ap.add_argument('--x', type=int, nargs=2, default=[1280, 2304]); ap.add_argument('--threads', type=int, default=3); ap.add_argument('--fp_rate', type=float, default=0.5)
    ap.add_argument('--T_d', type=float, default=None); ap.add_argument('--n_min', type=int, default=None); ap.add_argument('--Lz', type=int, default=DEFAULTS['Lz']); ap.add_argument('--T_q', type=float, default=DEFAULTS['T_q']); ap.add_argument('--s_step', type=int, default=DEFAULTS['s_step']); ap.add_argument('--no_slip', action='store_true', help='skip the slip stage (pass 2); segments carry status UNKNOWN')
    a = ap.parse_args(); p = dict(DEFAULTS); p['Lz'] = a.Lz; p['fp_rate'] = a.fp_rate; p['T_q'] = a.T_q; p['s_step'] = a.s_step; p['no_slip'] = bool(a.no_slip)
    if a.control:
        if a.slab is None or not os.path.exists(a.slab):
            from core_native import L0
            src = L0(a.src, threads=a.threads); st, ft = src.slab(a.y, a.n_sec, a.z[0], a.z[1], a.x[0], a.x[1]); os.makedirs(a.out, exist_ok=True); a.slab = a.slab or os.path.join(a.out, f'slab_y{a.y}.npy'); np.save(a.slab, st); print('fetched', ft)
        run_control(a, p); return
    if a.T_d is None or a.n_min is None: sys.exit('--T_d and --n_min required outside --control (calibrated on an un-injected slab by --control)')
    from core_native import L0
    src = L0(a.src, threads=a.threads); st, ft = src.slab(a.y, a.n_sec, a.z[0], a.z[1], a.x[0], a.x[1]); print('fetched', ft)
    per, _, geom = detect_stack(st, p, a.T_d, a.n_min, threads=a.threads); os.makedirs(a.out, exist_ok=True)
    json.dump(dict(vox_um=VOX, y0=a.y, n_sec=a.n_sec, z=a.z, x=a.x, params=p, T_d=a.T_d, n_min=a.n_min, fetch=ft, sections=per), open(os.path.join(a.out, 'shear_lines.json'), 'w'), indent=1)
    print(json.dumps([len(s) for s in per]))


if __name__ == '__main__': main()
