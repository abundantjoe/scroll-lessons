#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 item 3, shear-line detector at the scan's native 8.64 um (OME level 0), xz sections tracked along y.

A shear line is a line in the xz section across which the lamina stack on one side is displaced along the stacking
direction (z, the local layer normal) relative to the other side. A FRACTIONAL slip (e.g. half a spacing) breaks every
ridge and is visible to section-to-section ridge tracking; an INTEGER slip (one or more spacings) reconnects ridge k to
ridge k+1 and is invisible to forward/backward tracking because the lattice is locally periodic. What survives an integer
slip is the aperiodic signature of the stack (the sequence of pitches, widths, gaps and texture over several spacings):
the vertical profile on one side of the line matches the other side only after the slip, not at the tilt-predicted
continuation. The detector measures exactly that.

Per section:
  1. stripe removal (column z-median, tools/umb/st_axis.stripe_removal); the in-mask field only;
  2. for each declared line angle alpha (from the stacking direction z): shear the image so candidate lines of that angle
     become vertical, 2-D structure tensor on the sheared image (derivative sigma 2 vox, integration sigma 8 vox as in
     DECL-UMB-2) -> local layer slope m and coherence; oriented box average of width w along the local layer direction
     -> strip profile S(z, x) (one sheet-sharp vertical profile per column);
  3. for every candidate line x0 (stride 4): left strip profile P_L(z) = S(z, x0 - g - w/2), right strip profile
     continued along the layers over the gap D = w + 2 g: P_R'(z) = S(z + D * m_bar(z), x0 + g + w/2); windowed (L_z vox)
     normalised cross-correlation NCC(s) of P_L against P_R'(z + s) for integer s in [-s_max, s_max], parabolic sub-voxel
     refinement;
  4. slip = the best local maximum of NCC with |s| >= s_min; evidence E = NCC(slip) - max_{|s| < s_min} NCC(s): the
     excess of the slipped match over the continuous (no-slip) match. On a continuous stack E <= 0; on an integer slip
     E > 0 by the aperiodicity of the stack; on a fractional slip E is large.
     Coherence drop = 1 - coh(on the line) / mean(coh of the two strips) (reported, not gated: an exact integer slip need
     not disturb the texture at all);
  5. domain gate: both strips >= 90 % in mask over the window, strip coherence >= coh_min, |layer slope| <= 1 in the
     sheared frame (the line must cross the layers), NCC(slip) >= c_min;
  6. nodes with E >= T_E chain along z (same alpha, same x0, consistent slip) into segments of >= n_min windows;
     non-maximum suppression across x0 and alpha (perpendicular distance <= nms_dist, z-overlap >= 50 %);
Along y: segments are linked section to section (angle within one step, perpendicular distance <= link_dist, z-overlap
>= 50 %, slip agreement <= 0.25 pitch); persistence = number of consecutive sections of the line.

Output per section: segments with endpoints (z, x) in the section frame, angle, slip in voxels (signed: the +x side of
the line displaced toward +z relative to the -x side), NCC at the slip and at zero, evidence E, coherence drop, line id
and persistence along y.

Positive control (--control): take the real 16-section slab (y 5820..5835, z 7936..8704, x 1280..2304, L0.slab), inject
a z-shift of the region on the +x side of a declared line (angle, position) into sections 4..11 (8 sections) for
slips of half a spacing (22 vox), one declared spacing (44 vox = the census median pitch 380 um), two spacings (88) and
one LOCAL integer pitch (the median peak spacing measured along the line on the un-injected section): >= 20 placements.
T_E is calibrated on the un-injected slab (declared false-positive rate) and the detection rate is measured per slip
class with the +-2-section rule; false positives are counted on every un-injected section (the calibration slab, the
held-out slab at another y, and the sections of each placement outside the injection +-2).

usage: shear_lines.py <out_dir> --control [--slab slab.npy --null slab2.npy] [--threads 3]
       shear_lines.py <out_dir> --src s3://.../0 --y 5820 --n_sec 16 --z 7936 8704 --x 1280 2304
"""
import argparse, json, os, sys, time, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb'))
from st_axis import stripe_removal, st_accumulate, st_eigen
VOX = 8.64

DEFAULTS = dict(pitch=44, sd=2.0, si=8.0, w=8, g=4, w_tex=8, sig_z=1.0, slope_box=16, slope_max=2.0, Lz=176, s_max=110, s_step=2, s_min=9,
                nb_min=12, nb_max=24, ref_min=0.2, agree_min=0.5, x_stride=4, z_stride=16, coh_min=0.3, mask_min=0.9,
                c_min=0.3, T_E=None, n_min=3, nms_dist=12, link_dist=8, angles=[-40, -30, -20, -10, 0, 10, 20, 30, 40])


# ----------------------------------------------------------------------------------------------- per-section detector
def shear_image(img, tan_a, zc, order=1):
    """out(z, x') = img(z, x' + (z - zc) * tan_a): lines x = x' + (z - zc) tan_a of the original become vertical."""
    Z, X = img.shape; zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); xs = xx + (zz - zc) * tan_a
    return ndi.map_coordinates(img, [zz, xs], order=order, mode='constant', cval=0.0)


def oriented_box(img, slope, w):
    """Mean over u in [-w/2, w/2) of img(z + u * slope(z, x), x + u): a box average along the local layer direction."""
    Z, X = img.shape; zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); acc = np.zeros_like(img); cnt = np.zeros_like(img)
    for u in np.arange(-w / 2 + 0.5, w / 2, 1.0, dtype=np.float32):
        zq = zz + u * slope; xq = xx + u
        acc += ndi.map_coordinates(img, [zq, xq], order=1, mode='constant', cval=0.0)
        cnt += ndi.map_coordinates(np.ones_like(img), [zq, xq], order=1, mode='constant', cval=0.0)
    return acc / np.maximum(cnt, 1e-6)


def box_z(a, L):
    """Running sum over a centred window of L samples along axis 0 (zero outside)."""
    c = np.cumsum(np.concatenate([np.zeros((1,) + a.shape[1:], a.dtype), a], 0), 0); h0, h1 = L // 2, L - L // 2
    Z = a.shape[0]; lo = np.clip(np.arange(Z) - h0, 0, Z); hi = np.clip(np.arange(Z) + h1, 0, Z)
    return c[hi] - c[lo]


def section_nodes(sec_u8, p):
    """One section (Z, X) uint8 -> node table per angle: dict alpha -> arrays over (zc grid, x0 grid).
    Band matching: the band of w columns on each side of the candidate line (gap g from the line; column pairs D = w + 2 g
    apart) is compared as a 2-D normalised cross-correlation NCC(s) over a window of Lz rows along the line for every
    z-shift s of the right band. On a continuous stack NCC peaks at the continuity offset delta = D x (local layer
    slope), which varies smoothly along x. The continuity reference at a candidate line is measured from the data, not
    from a tensor model: the mean NCC curve of the neighbouring candidates whose bands lie outside the straddle zone of
    the line (|dx| = nb_min .. nb_max), whose argmax is s_ref. A shear line is a local maximum of the line's own NCC at
    |s - s_ref| >= s_min with evidence E = NCC(slip) - max_{|s - s_ref| < s_min} NCC(s) > 0; slip = s - s_ref."""
    Z, X = sec_u8.shape; mask = sec_u8 > 0; img = stripe_removal(sec_u8.astype(np.float32) / 255.0, mask)
    zc_img = Z / 2.0; w, g, Lz, smax, smin = p['w'], p['g'], p['Lz'], p['s_max'], p['s_min']; D = w + 2 * g; xs_ = p['x_stride']
    x0s = np.arange(g + w + 2, X - g - w - 2, xs_); zcs = np.arange(Lz // 2, Z - Lz // 2 + 1, p['z_stride']); nx = len(x0s)
    nb = [k for k in range(-8, 9) if p['nb_min'] <= abs(k) * xs_ <= p['nb_max']]                                   # neighbour offsets (x0-grid units)
    out = {}
    for alpha in p['angles']:
        ta = np.tan(np.radians(alpha)); I = shear_image(img, ta, zc_img); M = shear_image(mask.astype(np.float32), ta, zc_img) > 0.5
        J = st_accumulate([I], p['sd']); th, coh, _ = st_eigen(J, p['si'])
        slope = -np.cos(th) / np.where(np.abs(np.sin(th)) < 1e-3, 1e-3, np.sin(th))        # layer slope dz/dx in the sheared frame
        slope = np.clip(slope, -4.0, 4.0).astype(np.float32); coh = (coh * M).astype(np.float32)
        cs = ndi.uniform_filter(coh, p['slope_box']); sw = np.clip(ndi.uniform_filter(slope * coh, p['slope_box']) / np.maximum(cs, 1e-6), -p['slope_max'], p['slope_max'])
        T = ndi.gaussian_filter1d(oriented_box(I, sw, p['w_tex']), p['sig_z'], axis=0) if p['w_tex'] > 1 else ndi.gaussian_filter1d(I, p['sig_z'], axis=0)
        T = T - ndi.uniform_filter1d(T, 2 * p['pitch'], axis=0); T = (T * M).astype(np.float32); Mf = M.astype(np.float32)
        cols = np.arange(w)[None, :]; xl = x0s[:, None] - g - w + cols; xr = x0s[:, None] + g + cols                  # (nx, w)
        xlc, xrc = x0s - g - w // 2, x0s + g + w // 2
        L = T[:, xl]; R = T[:, xr]; ML = Mf[:, xl]; MR = Mf[:, xr]                                                   # (Z, nx, w)
        LL = box_z((L * L).sum(2), Lz)[zcs]; shifts = np.arange(-smax, smax + 1, p['s_step']); ncc = np.zeros((len(shifts), len(zcs), nx), np.float32)
        Rpad = np.concatenate([np.zeros((smax, nx, w), np.float32), R, np.zeros((smax, nx, w), np.float32)], 0); RR_full = box_z((Rpad * Rpad).sum(2), Lz)
        for i, s in enumerate(shifts):
            num = box_z((L * Rpad[smax + s: smax + s + Z]).sum(2), Lz)[zcs]; ncc[i] = num / np.sqrt(np.maximum(LL * RR_full[smax + s + zcs], 1e-9))
        # continuity reference: mean NCC curve of the neighbours outside the straddle zone
        ref = np.zeros_like(ncc); n_nb = np.zeros((len(zcs), nx), np.float32); agree = np.zeros((len(zcs), nx), np.float32)
        for k in nb:
            if k > 0: ref[:, :, :nx - k] += ncc[:, :, k:]; n_nb[:, :nx - k] += 1
            else: ref[:, :, -k:] += ncc[:, :, :nx + k]; n_nb[:, -k:] += 1
        ref = ref / np.maximum(n_nb, 1)[None]; iref = ref.argmax(0); s_ref = shifts[iref].astype(np.float32); ncc_ref = np.take_along_axis(ref, iref[None], 0)[0]
        for k in nb:                                                                                                  # fraction of neighbours whose own peak agrees with s_ref
            own = shifts[ncc.argmax(0)]
            if k > 0: agree[:, :nx - k] += (np.abs(own[:, k:] - s_ref[:, :nx - k]) < smin)
            else: agree[:, -k:] += (np.abs(own[:, :nx + k] - s_ref[:, -k:]) < smin)
        agree = agree / np.maximum(n_nb, 1)
        # continuous match (|s - s_ref| < s_min) and the best slipped local maximum of the line's own curve
        dist = np.abs(shifts[:, None, None] - s_ref[None]); inner = dist < smin; ncc0 = np.where(inner, ncc, -2).max(0)
        nc = np.where(inner, -2, ncc)
        is_max = (nc >= np.roll(nc, 1, 0)) & (nc >= np.roll(nc, -1, 0)); nc_pk = np.where(is_max, nc, -2); nc_pk[0] = nc_pk[-1] = -2
        ib = nc_pk.argmax(0); best = np.take_along_axis(nc_pk, ib[None], 0)[0]
        ii, jj = np.meshgrid(np.arange(len(zcs)), np.arange(nx), indexing='ij'); ibc = np.clip(ib, 1, len(shifts) - 2)
        ym, y0, yp = ncc[ibc - 1, ii, jj], ncc[ibc, ii, jj], ncc[ibc + 1, ii, jj]; den = ym - 2 * y0 + yp
        frac = np.where(np.abs(den) > 1e-6, 0.5 * (ym - yp) / np.where(np.abs(den) > 1e-6, den, 1), 0.0); frac = np.clip(frac, -0.5, 0.5) * p['s_step']
        slip = shifts[ib] + frac - s_ref; E = best - ncc0
        # validity per node: both bands in mask, side bands coherent over the window, a real and agreed continuity reference
        mask_ok = (box_z(ML.mean(2), Lz)[zcs] / Lz >= p['mask_min']) & (box_z(MR.mean(2), Lz)[zcs] / Lz >= p['mask_min'])
        cL = box_z(cs[:, xlc], Lz)[zcs] / Lz; cR = box_z(cs[:, xrc], Lz)[zcs] / Lz; c_on = box_z(ndi.uniform_filter1d(coh, 2 * g + 1, axis=1)[:, x0s], Lz)[zcs] / Lz
        valid = mask_ok & (cL >= p['coh_min']) & (cR >= p['coh_min']) & (n_nb >= 4) & (ncc_ref >= p['ref_min']) & (agree >= p['agree_min']) & (np.abs(s_ref) <= D * p['slope_max'])
        cstrip = 0.5 * (cL + cR); coh_drop = 1 - c_on / np.maximum(cstrip, 1e-6)
        out[alpha] = dict(x0=x0s, zc=zcs, valid=valid, E=E.astype(np.float32), slip=slip.astype(np.float32), ncc_best=best.astype(np.float32),
                          ncc0=ncc0.astype(np.float32), coh_drop=coh_drop.astype(np.float32), coh_strip=cstrip.astype(np.float32), s_ref=s_ref, ncc_ref=ncc_ref.astype(np.float32), agree=agree.astype(np.float32), **({"ncc": ncc, "shifts": shifts, "ref": ref} if p.get("debug") else {}))
    return out, dict(Z=Z, X=X, zc_img=zc_img)


def segments_from_nodes(nodes, geom, p, T_E):
    """Chain accepted nodes along z per (alpha, x0) into segments, then NMS across x0 and alpha."""
    segs = []; Lz = p['Lz']; zci = geom['zc_img']
    for alpha, nd in nodes.items():
        acc = nd['valid'] & (nd['E'] >= T_E) & (nd['ncc_best'] >= p['c_min']); ta = np.tan(np.radians(alpha))
        for j, x0 in enumerate(nd['x0']):
            col = acc[:, j]
            if col.sum() < p['n_min']: continue
            i = 0; n = len(col)
            while i < n:
                if not col[i]: i += 1; continue
                k = i
                while k + 1 < n and col[k + 1] and abs(nd['slip'][k + 1, j] - nd['slip'][k, j]) <= 0.25 * p['pitch']: k += 1
                if k - i + 1 >= p['n_min']:
                    sl = slice(i, k + 1); z0, z1 = nd['zc'][i] - Lz // 2, nd['zc'][k] + Lz // 2
                    segs.append(dict(alpha=float(alpha), x0=float(x0), z0=float(z0), z1=float(z1), x_at_z0=float(x0 + (z0 - zci) * ta), x_at_z1=float(x0 + (z1 - zci) * ta),
                                     slip=float(np.median(nd['slip'][sl, j])), E_sum=float(nd['E'][sl, j].sum()), E_max=float(nd['E'][sl, j].max()),
                                     ncc_best=float(np.median(nd['ncc_best'][sl, j])), ncc0=float(np.median(nd['ncc0'][sl, j])),
                                     coh_drop=float(np.median(nd['coh_drop'][sl, j])), coh_strip=float(np.median(nd['coh_strip'][sl, j])), n_windows=int(k - i + 1)))
                i = k + 1
    # NMS: perpendicular distance between the two lines at the overlap midpoint <= nms_dist and z-overlap >= 50 %
    segs.sort(key=lambda s: -s['E_sum']); keep = []
    for s in segs:
        ok = True
        for t in keep:
            zo0, zo1 = max(s['z0'], t['z0']), min(s['z1'], t['z1'])
            if zo1 - zo0 < 0.5 * min(s['z1'] - s['z0'], t['z1'] - t['z0']): continue
            zm = 0.5 * (zo0 + zo1); xs = s['x0'] + (zm - zci) * np.tan(np.radians(s['alpha'])); xt = t['x0'] + (zm - zci) * np.tan(np.radians(t['alpha']))
            if abs(xs - xt) * np.cos(np.radians(0.5 * (s['alpha'] + t['alpha']))) <= p['nms_dist']: ok = False; break
        if ok: keep.append(s)
    return keep


def link_along_y(per_section, p, geom):
    """Greedy section-to-section linking; assigns line_id and persistence (number of consecutive sections)."""
    zci = geom['zc_img']; next_id = 0; lines = {}
    for i, segs in enumerate(per_section):
        prev = per_section[i - 1] if i > 0 else []
        for s in segs:
            best, bd = None, None
            for t in prev:
                if abs(s['alpha'] - t['alpha']) > 15.5: continue
                zo0, zo1 = max(s['z0'], t['z0']), min(s['z1'], t['z1'])
                if zo1 - zo0 < 0.5 * min(s['z1'] - s['z0'], t['z1'] - t['z0']): continue
                zm = 0.5 * (zo0 + zo1); d = abs((s['x0'] + (zm - zci) * np.tan(np.radians(s['alpha']))) - (t['x0'] + (zm - zci) * np.tan(np.radians(t['alpha'])))) * np.cos(np.radians(s['alpha']))
                if d <= p['link_dist'] and abs(s['slip'] - t['slip']) <= 0.25 * p['pitch'] and (bd is None or d < bd): best, bd = t, d
            if best is not None and best['line_id'] not in [u['line_id'] for u in segs if 'line_id' in u]: s['line_id'] = best['line_id']
            else: s['line_id'] = next_id; next_id += 1
            lines.setdefault(s['line_id'], []).append(i)
    for segs in per_section:
        for s in segs: ys = lines[s['line_id']]; s['persistence'] = int(len(ys)); s['y_first'] = int(min(ys)); s['y_last'] = int(max(ys))
    return per_section


def detect_stack(stack, p, T_E, threads=1, keep_nodes=False):
    """stack (n, Z, X) uint8 -> (per-section segment lists with y-links, node tables if asked)."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max(1, threads)) as ex: res = list(ex.map(lambda s: section_nodes(s, p), [stack[i] for i in range(stack.shape[0])]))
    geom = res[0][1]; per = [segments_from_nodes(nd, geom, p, T_E) for nd, _ in res]
    per = link_along_y(per, p, geom)
    return per, ([nd for nd, _ in res] if keep_nodes else None), geom


# -------------------------------------------------------------------------------------------- control: injection + eval
def inject(stack, alpha, x0, slip, secs, zc_img):
    """Shift the region on the +x side of the line x = x0 + (z - zc) tan(alpha) by `slip` voxels along z (positive = +z,
    i.e. toward larger row index) in the listed sections. Voxels rolled in from outside the volume are 0 (= outside mask)."""
    out = stack.copy(); n, Z, X = stack.shape; ta = np.tan(np.radians(alpha)); zz, xx = np.mgrid[0:Z, 0:X]
    side = (xx - (x0 + (zz - zc_img) * ta)) * np.cos(np.radians(alpha)) > 0
    s = int(round(slip)); sh = np.zeros((Z, X), np.uint8)
    for i in secs:
        sh[:] = 0
        if s > 0: sh[s:] = stack[i][:Z - s]
        elif s < 0: sh[:Z + s] = stack[i][-s:]
        else: sh[:] = stack[i]
        out[i] = np.where(side, sh, stack[i])
    return out


def local_pitch_along_line(sec_u8, alpha, x0, zc_img, p):
    """Median peak spacing (prominence >= 3 MAD) of vertical profiles within +-60 vox of the line, over the clean half."""
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


def seg_hits_line(seg, alpha, x0, zc_img, tol_x, tol_a=15.5):
    if abs(seg['alpha'] - alpha) > tol_a: return False
    zm = 0.5 * (seg['z0'] + seg['z1']); xs = seg['x0'] + (zm - zc_img) * np.tan(np.radians(seg['alpha'])); xt = x0 + (zm - zc_img) * np.tan(np.radians(alpha))
    return abs(xs - xt) * np.cos(np.radians(alpha)) <= tol_x


def calibrate_T_E(nodes_list, p, fp_per_section):
    """T_E = the smallest threshold at which the null stack yields <= fp_per_section segments per section (searched on
    the node-level null distribution of E among valid nodes)."""
    Es = np.concatenate([nd[a]['E'][nd[a]['valid'] & (nd[a]['ncc_best'] >= p['c_min'])].ravel() for nd in nodes_list for a in nd])
    cands = np.unique(np.round(np.quantile(Es[Es > 0], np.linspace(0.5, 1.0, 101)), 4)) if (Es > 0).any() else np.array([0.05])
    geom = dict(zc_img=None)
    best = None
    for T in cands:
        n_seg = sum(len(segments_from_nodes(nd, {'zc_img': p['_zc_img']}, p, float(T))) for nd in nodes_list)
        rate = n_seg / len(nodes_list)
        if rate <= fp_per_section: best = (float(T), rate); break
    if best is None: best = (float(cands[-1]) + 1e-3, 0.0)
    return best, dict(n_valid_nodes=int(len(Es)), E_quantiles={q: float(np.quantile(Es, q)) for q in (0.5, 0.9, 0.99, 0.999, 1.0)})


def overlay_png(path, stack, per_section, injected, geom, title_rows):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    n = len(title_rows); fig, axes = plt.subplots(1, n, figsize=(6.5 * n, 5.6)); axes = np.atleast_1d(axes)
    for ax, (k, sec_i, title) in zip(axes, title_rows):
        st = stack[k]; ax.imshow(st[sec_i], cmap='gray', vmin=0, vmax=255, interpolation='nearest'); ax.set_title(title, fontsize=9)
        inj = injected[k]
        if inj is not None:
            a, x0 = inj['alpha'], inj['x0']; ta = np.tan(np.radians(a)); z = np.array([0, geom['Z'] - 1]); ax.plot(x0 + (z - geom['zc_img']) * ta, z, '--', color='cyan', lw=1.0, label='injected line')
        for s in per_section[k][sec_i]:
            col = 'red' if abs(s['slip']) >= 0.75 * 44 else 'orange'
            ax.plot([s['x_at_z0'], s['x_at_z1']], [s['z0'], s['z1']], '-', color=col, lw=1.6, alpha=0.9)
            ax.text(s['x_at_z1'], s['z1'], f"{s['slip']:+.0f}", color=col, fontsize=7)
        ax.set_xlim(0, geom['X']); ax.set_ylim(geom['Z'], 0); ax.set_xlabel('x (vox)'); ax.set_ylabel('z (vox)')
    axes[0].legend(loc='lower right', fontsize=7); plt.tight_layout(); plt.savefig(path, dpi=110); plt.close(fig)


def run_control(a, p):
    out = a.out; os.makedirs(out, exist_ok=True); t_all = time.time()
    stack = np.load(a.slab); n, Z, X = stack.shape; zci = Z / 2.0; p['_zc_img'] = zci
    null2 = np.load(a.null) if a.null and os.path.exists(a.null) else None
    log = lambda *s: print(*s, flush=True)
    # 1. null run on the un-injected slab (nodes kept for calibration)
    t = time.time(); per_null, nodes_null, geom = detect_stack(stack, p, T_E=1e9, threads=a.threads, keep_nodes=True); log(f'null nodes: {time.time() - t:.1f} s')
    (T_E, null_rate), stats = calibrate_T_E(nodes_null, p, a.fp_rate); p['T_E'] = T_E; log(f'T_E calibrated: {T_E:.4f} (null segments/section {null_rate:.3f} at declared <= {a.fp_rate})', stats)
    per_null = link_along_y([segments_from_nodes(nd, geom, p, T_E) for nd in nodes_null], p, geom)
    fp_null = [len(s) for s in per_null]
    # held-out null at another y
    fp_held = None
    if null2 is not None:
        per_h, _, _ = detect_stack(null2, p, T_E, threads=a.threads); fp_held = [len(s) for s in per_h]; log('held-out null FP per section:', fp_held)
    # 2. placements (declared before any detection on injected data)
    angles = [0, 20, -20, 35]; xs = [380, 520, 660, 800, 940]; inj_secs = list(range(4, 12)); lines = [(al, x0) for x0 in xs for al in angles]
    placements = []
    for li, (al, x0) in enumerate(lines):
        sgn = 1 if li % 2 == 0 else -1; p_loc = local_pitch_along_line(stack[8], al, x0, zci, p)
        placements += [dict(alpha=al, x0=x0, slip=sgn * p['pitch'] // 2, cls='half'), dict(alpha=al, x0=x0, slip=sgn * p['pitch'], cls='one_declared'), dict(alpha=al, x0=x0, slip=p_loc, cls='one_local')]
        if li % 4 == 0: placements.append(dict(alpha=al, x0=x0, slip=2 * p['pitch'], cls='two'))
    log(f'{len(placements)} placements over {len(lines)} lines, injected sections {inj_secs[0]}..{inj_secs[-1]} of {n}')
    json.dump(dict(placements=placements, injected_sections=inj_secs, T_E=T_E, params={k: v for k, v in p.items() if not k.startswith('_')}), open(os.path.join(out, 'placements.json'), 'w'), indent=1)
    # 3. run each placement
    from concurrent.futures import ProcessPoolExecutor
    tol_x = 12.0; results = []; overlays = []
    def one(pl):
        st = inject(stack, pl['alpha'], pl['x0'], pl['slip'], inj_secs, zci); per, _, _ = detect_stack(st, p, T_E, threads=1)
        hits = []; fps = []; slips = []
        for i in range(n):
            h = [s for s in per[i] if seg_hits_line(s, pl['alpha'], pl['x0'], zci, tol_x)]; o = [s for s in per[i] if s not in h]
            hits.append(len(h) > 0); slips += [s['slip'] for s in h] if i in inj_secs else []
            fps.append(len(o) if (inj_secs[0] - 2 <= i <= inj_secs[-1] + 2) else len(per[i]))      # outside the +-2 band any detection on the injected line is a false positive too
        in_inj = [hits[i] for i in inj_secs]; far = [i for i in range(n) if i < inj_secs[0] - 2 or i > inj_secs[-1] + 2]
        line_ids = set(s['line_id'] for i in inj_secs for s in per[i] if seg_hits_line(s, pl['alpha'], pl['x0'], zci, tol_x))
        pers = max([s['persistence'] for i in inj_secs for s in per[i] if s['line_id'] in line_ids], default=0)
        rec = dict(**pl, hit_sections=[i for i in range(n) if hits[i]], hit_frac_injected=float(np.mean(in_inj)), detected_all_injected=bool(all(in_inj)),
                   detected_pm2=bool(all(in_inj)) and not any(hits[i] for i in far), spill_sections=[i for i in range(n) if hits[i] and i not in inj_secs],
                   slip_est_median=float(np.median(slips)) if slips else None, slip_err_median=float(np.median(np.abs(np.array(slips) - pl['slip']))) if slips else None,
                   fp_per_section=fps, fp_total=int(sum(fps)), persistence_max=int(pers), n_lines_on_injection=len(line_ids))
        return rec, per, st
    with ProcessPoolExecutor(max(1, a.threads)) as ex:
        for k, (rec, per, st) in enumerate(ex.map(one, placements)):
            results.append(rec); log(json.dumps({kk: rec[kk] for kk in ('alpha', 'x0', 'slip', 'cls', 'hit_frac_injected', 'detected_pm2', 'slip_est_median', 'fp_total', 'persistence_max', 'spill_sections')}))
            if len(overlays) < 4 and rec['cls'] in ('one_local', 'half', 'one_declared', 'two') and rec['cls'] not in [o[3] for o in overlays]: overlays.append((st, per, placements[k], rec['cls']))
    # 4. summary per class
    by = {}
    for r in results: by.setdefault(r['cls'], []).append(r)
    summary = {c: dict(n=len(v), detected_pm2=int(sum(r['detected_pm2'] for r in v)), detection_rate_pm2=float(np.mean([r['detected_pm2'] for r in v])),
                       all_injected_sections_hit=int(sum(r['detected_all_injected'] for r in v)), mean_hit_frac=float(np.mean([r['hit_frac_injected'] for r in v])),
                       slip_err_median=float(np.median([r['slip_err_median'] for r in v if r['slip_err_median'] is not None])) if any(r['slip_err_median'] is not None for r in v) else None,
                       fp_per_section=float(np.mean([np.mean(r['fp_per_section']) for r in v]))) for c, v in by.items()}
    fp_inj_far = [x for r in results for i, x in enumerate(r['fp_per_section']) if i < inj_secs[0] - 2 or i > inj_secs[-1] + 2]
    fp_inj_band = [x for r in results for i, x in enumerate(r['fp_per_section']) if inj_secs[0] - 2 <= i <= inj_secs[-1] + 2]
    report = dict(vox_um=VOX, slab=a.slab, held_out_null=a.null, params={k: v for k, v in p.items() if not k.startswith('_')}, declared_fp_rate_per_section=a.fp_rate, T_E=T_E, calibration=stats,
                  null_fp_per_section=dict(calibration_slab=fp_null, mean=float(np.mean(fp_null)), held_out=fp_held, held_out_mean=float(np.mean(fp_held)) if fp_held else None),
                  fp_on_placements=dict(uninjected_sections_mean=float(np.mean(fp_inj_far)), injected_band_off_line_mean=float(np.mean(fp_inj_band))),
                  summary_per_class=summary, overall_detection_rate_pm2=float(np.mean([r['detected_pm2'] for r in results])), n_placements=len(results), injected_sections=inj_secs, tol_x_vox=tol_x,
                  placements=results, null_segments=per_null, runtime_s=round(time.time() - t_all, 1))
    json.dump(report, open(os.path.join(out, 'control.json'), 'w'), indent=1)
    rows = [(0, 8, f'un-injected y=5828: {len(per_null[8])} segments')]; stacks = [stack]; pers = [per_null]; injs = [None]
    for st, per, pl, cls in overlays:
        stacks.append(st); pers.append(per); injs.append(pl); rows.append((len(stacks) - 1, 8, f"{cls}: slip {pl['slip']:+d} vox, angle {pl['alpha']} deg, x0 {pl['x0']}"))
    overlay_png(os.path.join(out, 'overlay.png'), stacks, pers, injs, geom, rows)
    log('summary', json.dumps(summary, indent=1)); log('null FP/section', np.mean(fp_null), 'held-out', fp_held and np.mean(fp_held), 'runtime', round(time.time() - t_all, 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--control', action='store_true'); ap.add_argument('--slab', default=None); ap.add_argument('--null', default=None)
    ap.add_argument('--src', default='s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/0'); ap.add_argument('--y', type=int, default=5820); ap.add_argument('--n_sec', type=int, default=16)
    ap.add_argument('--z', type=int, nargs=2, default=[7936, 8704]); ap.add_argument('--x', type=int, nargs=2, default=[1280, 2304]); ap.add_argument('--threads', type=int, default=3); ap.add_argument('--fp_rate', type=float, default=0.5)
    ap.add_argument('--T_E', type=float, default=None); ap.add_argument('--Lz', type=int, default=DEFAULTS['Lz']); ap.add_argument('--angles', type=float, nargs='*', default=DEFAULTS['angles'])
    a = ap.parse_args(); p = dict(DEFAULTS); p['Lz'] = a.Lz; p['angles'] = list(a.angles); p['threads'] = a.threads
    if a.control:
        if a.slab is None or not os.path.exists(a.slab):
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb')); from core_native import L0
            src = L0(a.src, threads=a.threads); st, ft = src.slab(a.y, a.n_sec, a.z[0], a.z[1], a.x[0], a.x[1]); a.slab = a.slab or os.path.join(a.out, f'slab_y{a.y}.npy'); os.makedirs(a.out, exist_ok=True); np.save(a.slab, st); print('fetched', ft)
        run_control(a, p); return
    from core_native import L0
    src = L0(a.src, threads=a.threads); st, ft = src.slab(a.y, a.n_sec, a.z[0], a.z[1], a.x[0], a.x[1]); print('fetched', ft)
    if a.T_E is None: sys.exit('--T_E required outside --control (calibrate it on an un-injected slab with --control first)')
    per, _, geom = detect_stack(st, p, a.T_E, threads=a.threads); os.makedirs(a.out, exist_ok=True)
    json.dump(dict(vox_um=VOX, y0=a.y, n_sec=a.n_sec, z=a.z, x=a.x, params=p, T_E=a.T_E, fetch=ft, sections=per), open(os.path.join(a.out, 'shear_lines.json'), 'w'), indent=1)
    print(json.dumps([len(s) for s in per]))


if __name__ == '__main__': main()
