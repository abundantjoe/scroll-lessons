#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-2 item 2, the U-TURN OPERATOR at native resolution (8.64 um): sheet centrelines are ridge polylines; a U-turn is a
ridge polyline whose tangent rotates through >= `turn_deg` (150) within an arc of <= `turn_arc` voxels; each U-turn gets
an apex (the point of the turn where the tangent is perpendicular to the mean arm direction), an opening direction (unit
vector from the apex to the midpoint of the two arm ends), the turn angle, the arm lengths, and an INTERIOR TEST (ridge
pixels between the arms within `interior_pitches` (3) sheet pitches of the apex: 0 = empty). The innermost U-turn of a
column (x increasing INTO the stack): among U-turns opening into the stack (+x within 45 deg) with an empty interior, the
one with the largest apex x among its nested neighbours (the U-turns whose arm span in z contains its apex). Nothing here
is an ink or letter claim.

Method (numpy/scipy only): ridge strength R = max(0, -lambda_min) of the Hessian at sigma_r (default 4 vox; sheet 14 vox)
with the across-ridge direction = the eigenvector of lambda_min; centreline = non-maximum suppression of R along that
direction above tau = `k_mad` x MAD(R | mask); seeds = centreline pixels on a stride grid; each seed is traced both ways
along the ridge tangent (step 1 vox, sign continuous, snapped each step to the ridge maximum along the normal within +-1
vox) for up to `max_len` vox or until R < tau for 3 steps / the mask ends; the unwrapped direction angle along each
trace gives the net rotation over sliding windows of `turn_arc` steps; apexes closer than one sheet width are merged.
usage: uturns.py --img window.npz|png [--side left] [--out json] [--png overlay.png]   |   uturns.py --selftest
"""
import argparse, json, os, sys, time, numpy as np
from scipy import ndimage as ndi

DEFAULTS = dict(sigma_r=4.0, k_mad=3.0, seed_stride=24, max_len=1800, turn_deg=150.0, turn_arc=1800, pitch=44.0, sheet=14.0, interior_pitches=3.0, open_tol_deg=45.0, min_arm=30, batch=1500)

def hessian_ridge(img, sigma, band=1024, halo=32):
    """R (bright-ridge strength) and the across-ridge unit direction (nz, nx) from the Hessian eigen-decomposition, in row bands (bounded memory)."""
    Z, X = img.shape; R = np.zeros((Z, X), np.float32); NZ = np.zeros((Z, X), np.float32); NX = np.zeros((Z, X), np.float32)
    for z0 in range(0, Z, band):
        z1 = min(Z, z0 + band); a0, a1 = max(0, z0 - halo), min(Z, z1 + halo); sub = img[a0:a1]
        Hzz = ndi.gaussian_filter(sub, sigma, order=(2, 0)); Hxx = ndi.gaussian_filter(sub, sigma, order=(0, 2)); Hzx = ndi.gaussian_filter(sub, sigma, order=(1, 1))
        tr = Hzz + Hxx; det = Hzz * Hxx - Hzx * Hzx; lmin = tr / 2 - np.sqrt(np.maximum(tr * tr / 4 - det, 0)); del tr, det
        v1 = np.stack([Hzx, lmin - Hzz]); v2 = np.stack([lmin - Hxx, Hzx]); use2 = np.abs(v1).sum(0) < np.abs(v2).sum(0); v = np.where(use2, v2, v1); del v1, v2, use2
        v /= np.sqrt((v * v).sum(0)) + 1e-12; s0, s1 = z0 - a0, z0 - a0 + (z1 - z0)
        R[z0:z1] = (np.maximum(0, -lmin) * sigma * sigma)[s0:s1]; NZ[z0:z1] = v[0, s0:s1]; NX[z0:z1] = v[1, s0:s1]; del Hzz, Hxx, Hzx, lmin, v
    return R, NZ, NX

def centreline(R, nz, nx, mask, k_mad, band=1024):
    """Non-maximum suppression of R along the across-ridge direction (in row bands to bound memory); returns the binary centreline and tau."""
    Z, X = R.shape; rm = R[mask]; tau = float(k_mad * (np.median(np.abs(rm - np.median(rm))) + 1e-9) + np.median(rm)); cl = np.zeros((Z, X), bool)
    for z0 in range(0, Z, band):
        z1 = min(Z, z0 + band); zz, xx = np.mgrid[z0:z1, 0:X].astype(np.float32); n0, n1 = nz[z0:z1], nx[z0:z1]
        a = ndi.map_coordinates(R, [zz + n0, xx + n1], order=1, mode='nearest'); b = ndi.map_coordinates(R, [zz - n0, xx - n1], order=1, mode='nearest')
        r = R[z0:z1]; cl[z0:z1] = (r >= a) & (r >= b) & (r > tau) & mask[z0:z1]
    return cl, tau

def trace(R, nz, nx, mask, seeds, tau, p):
    """Batched ridge-tangent streamlines from seeds (N,2) (z,x), both directions. Returns list of (path (L,2), seed index)."""
    Z, X = R.shape; out = []
    for sign in (1.0, -1.0):
        pos = seeds.astype(np.float32).copy(); N = len(pos); alive = np.ones(N, bool); weak = np.zeros(N, int); d = None
        paths = np.full((N, p['max_len'], 2), np.nan, np.float32); L = np.zeros(N, int)
        for step in range(p['max_len']):
            zi = np.clip(np.rint(pos[:, 0]).astype(int), 0, Z - 1); xi = np.clip(np.rint(pos[:, 1]).astype(int), 0, X - 1)
            inside = (pos[:, 0] >= 0) & (pos[:, 0] <= Z - 1) & (pos[:, 1] >= 0) & (pos[:, 1] <= X - 1) & mask[zi, xi]
            alive &= inside
            if not alive.any(): break
            n = np.stack([ndi.map_coordinates(nz, [pos[:, 0], pos[:, 1]], order=1, mode='nearest'), ndi.map_coordinates(nx, [pos[:, 0], pos[:, 1]], order=1, mode='nearest')], 1)
            n /= (np.sqrt((n * n).sum(1, keepdims=True)) + 1e-9); t = np.stack([-n[:, 1], n[:, 0]], 1)        # tangent = normal rotated 90 deg
            if d is None: d = t * sign
            else: t[(t * d).sum(1) < 0] *= -1; d = t
            # snap to the ridge maximum along the normal (parabolic, clamped to +-1 vox)
            r0 = ndi.map_coordinates(R, [pos[:, 0], pos[:, 1]], order=1, mode='nearest'); rp = ndi.map_coordinates(R, [pos[:, 0] + n[:, 0], pos[:, 1] + n[:, 1]], order=1, mode='nearest'); rm_ = ndi.map_coordinates(R, [pos[:, 0] - n[:, 0], pos[:, 1] - n[:, 1]], order=1, mode='nearest')
            den = rp + rm_ - 2 * r0; sh = np.where(np.abs(den) > 1e-9, 0.5 * (rm_ - rp) / np.where(np.abs(den) > 1e-9, den, 1), 0.0); sh = np.clip(np.where(den < 0, sh, np.sign(rp - rm_)), -1, 1)
            pos = pos + n * sh[:, None]
            weak = np.where(r0 < 0.5 * tau, weak + 1, 0); alive &= weak < 5                      # hysteresis: a trace coasts over short weak stretches (< 5 vox below tau/2)
            paths[alive, step] = pos[alive]; L[alive] += 1
            pos = pos + d
        for k in range(N):
            if L[k] >= 3: out.append((paths[k, :L[k]], k, sign))
    return out

def merge_traces(tr_list, N):
    """Join the two directions of each seed into one polyline (reverse the backward one)."""
    fw = {}; bw = {}
    for path, k, s in tr_list: (fw if s > 0 else bw)[k] = path
    polys = []
    for k in set(fw) | set(bw):
        a = bw.get(k); b = fw.get(k)
        if a is not None and b is not None: polys.append(np.concatenate([a[::-1], b[1:]]))
        else: polys.append(a if a is not None else b)
    return polys

def find_turns(poly, p, R_img=None, tau_=0.0):
    """U-turns along one polyline: list of dicts (apex, open dir, turn angle, arm ends, indices). Vectorized sliding-window rotation."""
    if len(poly) < 2 * p['min_arm'] + 10: return []
    d = np.diff(poly, axis=0); phi = np.unwrap(np.arctan2(d[:, 0], d[:, 1])); n = len(phi); W = min(p['turn_arc'], n); thr = np.deg2rad(p['turn_deg']); turns = []
    # for each i: the extreme of phi over [i, i+W) (sliding max/min, window anchored at i)
    mx = ndi.maximum_filter1d(phi, W, origin=-(W // 2), mode='nearest'); mn = ndi.minimum_filter1d(phi, W, origin=-(W // 2), mode='nearest')
    best = np.where(mx - phi >= phi - mn, mx - phi, mn - phi); cand = np.nonzero(np.abs(best) >= thr)[0]
    tol = np.deg2rad(10.0); m_arm = p['min_arm']
    while len(cand):
        i = int(cand[np.argmax(np.abs(best[cand]))]); seg = phi[i:i + W] - phi[i]; j = i + int(np.argmax(np.abs(seg))); rot = phi[j] - phi[i]
        dev = np.abs(phi[i:j + 1] - phi[i]); on_arm = np.nonzero(dev < tol)[0]; i2 = i + int(on_arm[-1]) if len(on_arm) else i          # last point still on the first arm
        done = np.nonzero(np.abs(phi[i:j + 1] - phi[j]) < tol)[0]; j2 = i + int(done[0]) if len(done) else j                             # first point on the second arm
        cand = cand[(cand < i - W) | (cand > j)]
        if i2 < m_arm or j2 > len(poly) - 1 - m_arm or j2 <= i2: continue                                                                  # both arms must be traced beyond the turn
        La = min(200, i2, len(poly) - 1 - j2); d1 = poly[i2] - poly[i2 - La]; d2 = poly[j2 + La] - poly[j2]                                # arm directions away from the turn
        o = -d1 / (np.hypot(*d1) + 1e-9) + d2 / (np.hypot(*d2) + 1e-9); o = o / (np.hypot(*o) + 1e-9)
        if R_img is not None:
            rr = ndi.map_coordinates(R_img, [poly[i2:j2 + 1, 0], poly[i2:j2 + 1, 1]], order=1, mode='nearest'); strong = float((rr >= tau_).mean())
            if strong < 0.8: continue                                                                                                  # the turn must be a continuous ridge (not a coasted path)
        else: strong = None
        pr = (poly[i2:j2 + 1] * o).sum(1); near = np.nonzero(pr <= pr.min() + 1.0)[0]; a = i2 + int(np.round(near.mean())); apex = poly[i2 + near].mean(0); e1, e2 = poly[i2 - m_arm], poly[j2 + m_arm]   # apex = centroid of the turn's extreme points (within 1 vox) along -opening
        perp = np.array([-o[1], o[0]]); sel = np.nonzero(pr <= pr.min() + p['sheet'])[0]                                                   # refine: parabola u = a v^2 + b v + c on the tip (one sheet width deep)
        if len(sel) >= 7:
            v = ((poly[i2 + sel] - apex) * perp).sum(1); u = pr[sel] - pr.min(); A = np.stack([v * v, v, np.ones_like(v)], 1); cf = np.linalg.lstsq(A, u, rcond=None)[0]
            if cf[0] > 1e-6:
                v0 = -cf[1] / (2 * cf[0])
                if abs(v0) <= p['sheet']: apex = apex + v0 * perp
        turns.append({'apex': apex.tolist(), 'open': o.tolist(), 'turn_deg': float(np.rad2deg(abs(rot))), 'i': int(i2), 'j': int(j2), 'a': int(a), 'arc_len': int(j2 - i2), 'ridge_frac': strong, 'arm_len': [int(i2), int(len(poly) - 1 - j2)], 'arm_ends': [e1.tolist(), e2.tolist()], 'sep_at_ends': float(np.hypot(*(e1 - e2)))})
    return turns

def interior_count(cl, apex, o, e1, e2, p):
    """Ridge-centreline pixels strictly between the arms within interior_pitches of the apex, excluding one sheet width from each arm."""
    Z, X = cl.shape; apex = np.array(apex, float); o = np.array(o, float); perp = np.array([-o[1], o[0]]); L = p['interior_pitches'] * p['pitch']; half = 0.5 * np.hypot(*(np.array(e1) - np.array(e2))); dist_end = max(1.0, float(np.dot(0.5 * (np.array(e1) + np.array(e2)) - apex, o)))
    cnt = 0; tot = 0
    for s in np.arange(p['sheet'], L, 2.0):
        w = half * min(1.0, s / dist_end) - p['sheet']                                        # the wedge half-width grows linearly to the arm ends
        if w <= 1: continue
        for t in np.arange(-w, w + 1e-6, 2.0):
            q = apex + s * o + t * perp; zi, xi = int(round(q[0])), int(round(q[1]))
            if 0 <= zi < Z and 0 <= xi < X: tot += 1; cnt += int(cl[zi, xi])
    return int(cnt), int(tot)

def detect(img, mask, p, want_cl=False):
    """All U-turns in one (z, x) window image (float32, stripe-removed). Returns dict with turns, counts, timing."""
    t0 = time.time(); R, nz, nx = hessian_ridge(img, p['sigma_r']); cl, tau = centreline(R, nz, nx, mask, p['k_mad'])
    g = np.zeros_like(cl); g[::p['seed_stride'], :] = True; g[:, ::p['seed_stride']] = True; seeds = np.argwhere(cl & g);              # every centreline crossing of a grid line rng = np.random.default_rng(0); seeds = seeds[rng.permutation(len(seeds))]
    visited = np.zeros(cl.shape, bool); polys = []; used = 0
    for b0 in range(0, len(seeds), p['batch']):                                              # batches: seeds already covered by earlier traces are skipped
        sb = seeds[b0:b0 + p['batch']]; sb = sb[~visited[sb[:, 0], sb[:, 1]]]
        if len(sb) == 0: continue
        used += len(sb); tr = trace(R, nz, nx, mask, sb, tau, p); pl = merge_traces(tr, len(sb)); polys += pl
        for q in pl:
            zi = np.clip(np.rint(q[:, 0]).astype(int), 0, cl.shape[0] - 1); xi = np.clip(np.rint(q[:, 1]).astype(int), 0, cl.shape[1] - 1)
            for dz in (-1, 0, 1):
                for dx in (-1, 0, 1): visited[np.clip(zi + dz, 0, cl.shape[0] - 1), np.clip(xi + dx, 0, cl.shape[1] - 1)] = True
    turns = []
    for q, poly in enumerate(polys):
        for t in find_turns(poly, p, R, tau): t['poly'] = q; turns.append(t)
    # merge apexes closer than one sheet width (keep the larger turn angle)
    turns.sort(key=lambda t: -(min(t['arm_len']) + t['turn_deg'])); kept = []       # fullest traces first
    for t in turns:
        if all(np.hypot(t['apex'][0] - k['apex'][0], t['apex'][1] - k['apex'][1]) > 0.5 * p['pitch'] for k in kept): kept.append(t)
    xe = np.array([np.argmax(mask[z]) if mask[z].any() else -1 for z in range(mask.shape[0])], float); xe[xe < 0] = np.nan      # first mask column per row
    xe = ndi.median_filter(np.nan_to_num(xe, nan=np.nanmedian(xe) if np.isfinite(xe).any() else 0), size=int(2 * p['pitch']) | 1)
    for t in kept:
        t['depth'] = float(t['apex'][1] - xe[int(np.clip(round(t['apex'][0]), 0, mask.shape[0] - 1))])                            # apex depth from the LOCAL mask edge (a curved edge does not fake a V)
        c, n = interior_count(cl, t['apex'], t['open'], t['arm_ends'][0], t['arm_ends'][1], p); t['interior_ridge_px'] = c; t['interior_samples'] = n; t['interior_empty'] = bool(n > 0 and c < p['sheet'])                      # a ridge inside = at least one sheet width of centreline
        t['open_deg_from_x'] = float(np.rad2deg(np.arctan2(t['open'][0], t['open'][1])))
    res = {'n_seeds': int(len(seeds)), 'n_seeds_traced': int(used), 'n_polys': int(len(polys)), 'n_turns_raw': int(len(turns)), 'n_turns': int(len(kept)), 'tau': tau, 'secs': round(time.time() - t0, 1), 'turns': kept}
    if want_cl: res['cl'] = cl
    return res

def innermost(turns, p, Z=None, X=None):
    """Innermost U-turn of a column (x into the stack): opening within open_tol of +x, empty interior, largest apex x among nested neighbours."""
    tol = p['open_tol_deg']; ws = [t for t in turns if t['sep_at_ends'] >= p['pitch'] and min(t['arm_len']) >= 2 * p['pitch']]          # winding-scale U-turns (smaller loops = curls, recorded, never candidates)
    cand = [t for t in ws if abs(t['open_deg_from_x']) <= tol and (X is None or t['apex'][1] <= X - 3 * p['pitch'])]   # fully inside the window: not within 3 pitches of the deep boundary
    if not cand: return None, cand
    for t in cand: t['z_span'] = sorted([t['arm_ends'][0][0], t['arm_ends'][1][0]])
    empty = [t for t in cand if t['interior_empty']]
    best = None
    for t in sorted(empty, key=lambda t: -t['depth']):
        nb = [u for u in cand if u is not t and u['z_span'][0] <= t['apex'][0] <= u['z_span'][1]]       # nested neighbours: arm spans containing this apex height
        deeper = [u for u in nb if u['depth'] > t['depth']]
        if not deeper: best = t; break
    if best is None and empty: best = max(empty, key=lambda t: t['depth'])
    return best, cand

def nesting(cand, zc, p):
    """Spearman-like sign of apex x vs |z - zc| above and below zc (nested loops: x decreases away from zc)."""
    out = {}
    for name, sel in (('above', [t for t in cand if t['apex'][0] < zc]), ('below', [t for t in cand if t['apex'][0] > zc])):
        if len(sel) < 4: out[name] = None; continue
        d = np.array([abs(t['apex'][0] - zc) for t in sel]); x = np.array([t['depth'] for t in sel]); out[name] = round(float(np.corrcoef(d, x)[0, 1]), 3)
    return out

def window_summary(img, mask, p, vox_mm):
    """Run the operator on one edge window (x into the stack) and return the record core_native stores."""
    res = detect(img, mask, p); best, cand = innermost(res['turns'], p, X=img.shape[1]); zc = best['apex'][0] if best else None
    turns = [{'z_mm': round(t['apex'][0] / vox_mm, 3), 'x_mm': round(t['apex'][1] / vox_mm, 3), 'depth_mm': round(t['depth'] / vox_mm, 3), 'open_deg': round(t['open_deg_from_x'], 1), 'turn_deg': round(t['turn_deg'], 1), 'arc_mm': round(t['arc_len'] / vox_mm, 2),
              'arms_mm': [round(a / vox_mm, 2) for a in t['arm_len']], 'sep_mm': round(t['sep_at_ends'] / vox_mm, 3), 'interior_px': t['interior_ridge_px'], 'empty': t['interior_empty'], 'ridge_frac': None if t.get('ridge_frac') is None else round(t['ridge_frac'], 2)} for t in res['turns']]
    nws = sum(1 for t in res['turns'] if t['sep_at_ends'] >= p['pitch'] and min(t['arm_len']) >= 2 * p['pitch'])
    out = {'n_turns': res['n_turns'], 'n_winding_scale': int(nws), 'n_curls': int(res['n_turns'] - nws), 'n_into_stack': len(cand), 'n_empty': int(sum(t['interior_empty'] for t in cand)), 'secs_uturns': res['secs'], 'turns': turns}
    if best:
        out.update({'zc_mm': round(zc / vox_mm, 3), 'apex_depth_mm': round(best['depth'] / vox_mm, 3), 'apex_x_mm': round(best['apex'][1] / vox_mm, 3), 'innermost_interior_px': best['interior_ridge_px'], 'innermost_turn_deg': round(best['turn_deg'], 1), 'nesting': nesting(cand, zc, p)})
        deeper_any = [t for t in cand if t['depth'] > best['depth']]; out['n_deeper_non_empty'] = len(deeper_any)              # deeper U-turns that failed the interior test (recorded, not hidden)
    return out

def phantom(Z=1600, X=1000, n_loops=10, pitch=44.0, sheet=14.0, zc=800.0, r_in=60.0, x_in=520.0, seed=0, noise=0.15, seams=True):
    """Flattened spiral seen at one edge, x into the stack: loop k (0 = innermost) is a semicircle of radius r_in + k pitch centred at
    (zc, x_in + r_in) opening to +x, with straight arms at z = zc +- r_k running to the window's +x edge; the innermost apex is the
    deepest (largest x). A seam (dark gap) cuts the column at z = zc - 5 pitches."""
    rng = np.random.default_rng(seed); zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32); img = np.zeros((Z, X), np.float32); truth = []
    cz, cx = zc, x_in + r_in
    for k in range(n_loops):
        r = r_in + k * pitch; dist_arc = np.abs(np.hypot(zz - cz, xx - cx) - r); arc = (xx <= cx) & (dist_arc < sheet / 2)
        arm_up = (np.abs(zz - (cz - r)) < sheet / 2) & (xx > cx); arm_dn = (np.abs(zz - (cz + r)) < sheet / 2) & (xx > cx)
        img[arc | arm_up | arm_dn] = 1.0; truth.append({'apex': [float(cz), float(cx - r)], 'r': float(r)})
    if seams: img[int(zc - 5 * pitch - 3):int(zc - 5 * pitch + 3), :] = 0.0
    img = ndi.gaussian_filter(img, 1.5) + noise * rng.standard_normal((Z, X)).astype(np.float32); mask = np.ones((Z, X), bool)
    return img.astype(np.float32), mask, {'zc': zc, 'innermost_apex': truth[0]['apex'], 'apexes': truth}

def overlay(img, res, best, path, scale=1):
    from PIL import Image, ImageDraw
    a = img - np.percentile(img, 1); a = np.clip(a / (np.percentile(a, 99) + 1e-6), 0, 1); im = Image.fromarray((a * 255).astype(np.uint8)).convert('RGB')
    if scale != 1: im = im.resize((im.width // scale, im.height // scale))
    d = ImageDraw.Draw(im)
    for t in res['turns']:
        z, x = t['apex'][0] / scale, t['apex'][1] / scale; col = (0, 255, 0) if t['interior_empty'] else (255, 0, 0)
        d.ellipse([x - 3, z - 3, x + 3, z + 3], outline=col); d.line([x, z, x + 12 * t['open'][1], z + 12 * t['open'][0]], fill=col)
    if best: z, x = best['apex'][0] / scale, best['apex'][1] / scale; d.ellipse([x - 8, z - 8, x + 8, z + 8], outline=(255, 255, 0), width=2)
    im.save(path)

def selftest():
    p = dict(DEFAULTS); img, mask, T = phantom(); res = detect(img, mask, p); best, cand = innermost(res['turns'], p)
    ap = np.array([t['apex'] for t in res['turns']]); tr = np.array([t['apex'] for t in T['apexes']])
    hit = [float(np.min(np.hypot(ap[:, 0] - a[0], ap[:, 1] - a[1]))) if len(ap) else 1e9 for a in tr]; recall = float(np.mean([h <= p['sheet'] for h in hit]))
    fp = int(sum(np.min(np.hypot(tr[:, 0] - a[0], tr[:, 1] - a[1])) > p['sheet'] for a in ap)) if len(ap) else 0
    err = np.hypot(best['apex'][0] - T['innermost_apex'][0], best['apex'][1] - T['innermost_apex'][1]) if best else None
    out = {'n_turns': res['n_turns'], 'recall_apex_within_sheet': recall, 'false_apexes': fp, 'innermost_err_vox': None if err is None else round(float(err), 1), 'innermost_empty': best['interior_empty'] if best else None,
           'n_empty_interior': int(sum(t['interior_empty'] for t in res['turns'])), 'secs': res['secs'], 'pass': bool(best is not None and err <= p['sheet'] and recall >= 0.9)}
    os.makedirs('/dev/shm/umb', exist_ok=True); overlay(img, res, best, '/dev/shm/umb/uturns_selftest.png'); print(json.dumps(out)); return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--img'); ap.add_argument('--side', default='left'); ap.add_argument('--out'); ap.add_argument('--png'); ap.add_argument('--scale', type=int, default=4); ap.add_argument('--selftest', action='store_true')
    for k, v in DEFAULTS.items(): ap.add_argument('--' + k, type=type(v), default=v)
    a = ap.parse_args(); p = {k: getattr(a, k) for k in DEFAULTS}
    if a.selftest: sys.exit(0 if selftest()['pass'] else 1)
    if a.img.endswith('.npz'):                                                               # a core_native cache is already in the stack frame (x into the stack): never mirrored here
        F = np.load(a.img); img = F['img_full'].astype(np.float32) / 255.0 if 'img_full' in F else F['img'].astype(np.float32); mask = img > 0
    else:
        from PIL import Image; img = np.asarray(Image.open(a.img).convert('L')).astype(np.float32) / 255.0; mask = img > 0
        if a.side == 'right': img, mask = img[:, ::-1], mask[:, ::-1]
    res = detect(img, mask, p); best, cand = innermost(res['turns'], p); zc = best['apex'][0] if best else None
    res['innermost'] = best; res['n_opening_into_stack'] = len(cand); res['nesting'] = nesting(cand, zc, p) if zc is not None else None
    if a.png: overlay(img, res, best, a.png, a.scale)
    summ = {k: res[k] for k in res if k != 'turns'}; print(json.dumps(summ, default=float))
    if a.out: json.dump(res, open(a.out, 'w'), default=float)

if __name__ == '__main__': main()
