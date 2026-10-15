#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1 stage C: piecewise-smooth global axis from the per-slab centres of st_axis.py.
  - evidence-weighted (weights = slab confidence), Huber-robust, second-difference penalised curve (Whittaker smoother =
    discrete cubic smoothing spline) for x(z) and y(z); lambda chosen by leave-one-slab-out cross-validation, never hand-set;
  - explicit C0 breaks: a candidate break between slabs k and k+1 where the jump of the independent centres exceeds
    `--break_mm` with confidence >= `--break_conf` on both sides and the jump exceeds 3x the local split-half noise;
    accepted when the broken fit lowers the CV error; across a break the penalty is cut (no smoothing through it);
  - optional refinement: re-analyse 8-slice slabs around each candidate break from the source volume (localises the break);
  - confidence envelope: per-z confidence interpolated from the slabs; gaps (slabs with confidence < `--min_conf`) are
    bridged by the curve but carry the bridged flag and an envelope = the distance between the two one-sided extrapolations.
Writes <out>/umbilicus.json: z (every slice), x, y, confidence, bridged, breaks, lambda, cv, per-slab table.
usage: axis_spline.py <out_dir of st_axis.py> [--src volume for refinement] [--vox_um 69.12]
"""
import argparse, json, os, numpy as np

def whittaker(z, v, w, lam, breaks):
    """Minimise sum w (f - v)^2 + lam sum (D2 f)^2 over nodes at z (any spacing, uses divided second differences); the
    penalty rows that straddle a break index are removed (C0 there)."""
    n = len(z); rows = []
    for i in range(1, n - 1):
        if any(b in (i - 1, i) for b in breaks): continue               # a break between nodes b and b+1 removes the two second differences spanning it
        h1, h2 = z[i] - z[i - 1], z[i + 1] - z[i]; r = np.zeros(n); r[i - 1] = 2 / (h1 * (h1 + h2)); r[i] = -2 / (h1 * h2); r[i + 1] = 2 / (h2 * (h1 + h2)); rows.append(r)
    D = np.array(rows) if rows else np.zeros((0, n)); W = np.diag(w); A = W + lam * D.T @ D; return np.linalg.solve(A + 1e-9 * np.eye(n), W @ v)

def huber_fit(z, v, w, lam, breaks, delta, iters=5):
    ww = w.copy()
    for _ in range(iters):
        f = whittaker(z, v, ww, lam, breaks); r = np.abs(f - v); hw = np.where(r <= delta, 1.0, delta / np.maximum(r, 1e-9)); ww = w * hw
    return f

def loo_cv(z, v, w, lam, breaks, delta):
    err, cnt = 0.0, 0
    for i in range(len(z)):
        if w[i] <= 0: continue
        m = np.ones(len(z), bool); m[i] = False; f = huber_fit(z[m], v[m], w[m], lam, [b - (1 if b >= i else 0) for b in breaks if b != i and b != i - 1], delta)
        fi = np.interp(z[i], z[m], f); err += w[i] * min((fi - v[i]) ** 2, (4 * delta) ** 2); cnt += w[i]
    return err / max(cnt, 1e-9)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--src', default=None); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--min_conf', type=float, default=0.5); ap.add_argument('--source', default='slabs', choices=['slabs', 'topo']); ap.add_argument('--break_mm', type=float, default=1.0); ap.add_argument('--break_conf', type=float, default=0.6); ap.add_argument('--huber_mm', type=float, default=0.3)
    a = ap.parse_args(); S = json.load(open(os.path.join(a.out, 'slabs.json'))); mm = 1000.0 / a.vox_um; slabs = S['slabs']; Z = S['shape'][0]
    if a.source == 'topo':                                                   # the topological estimator's cores become the per-slab centres
        T = json.load(open(os.path.join(a.out, 'topo.json')))['sections']; byz = {r['z_mid']: r for r in slabs}
        slabs = []
        for t in T:
            r = dict(byz.get(t['z_mid'], {'z_mid': t['z_mid'], 'z0': int(t['z_mid'] - S['slab'] / 2 + 0.5), 'z1': int(t['z_mid'] + S['slab'] / 2 + 0.5)}))
            if t.get('status') == 'ok': r.update({'status': 'ok', 'centre': t['core'], 'confidence': t['confidence'], 'split_half_mm': t.get('max_shift_mm', 0.1), 'kind': t['kind'], 'slit_ends': t.get('slit_ends')}); r.pop('half_first_last_mm', None)
            else: r['status'] = t.get('status', 'none')
            slabs.append(r)
    ok = [r for r in slabs if r.get('status') == 'ok']
    z = np.array([r['z_mid'] for r in ok]); x = np.array([r['centre'][0] for r in ok]); y = np.array([r['centre'][1] for r in ok]); c = np.array([r.get('confidence') or 0.0 for r in ok]); sh = np.array([r.get('split_half_mm') or 0.05 for r in ok])
    # candidate breaks between consecutive confident slabs: jump > break_mm and > 3x the local split-half noise
    cands = []; seen = set()
    for i in range(len(z) - 1):
        for span in (1, 2):                                                  # a kink inside a slab splits over two consecutive jumps: test the two-slab jump too
            j = i + span
            if j >= len(z): continue
            jump = float(np.hypot(x[j] - x[i], y[j] - y[i])) / mm; noise = 3 * max(sh[i], sh[j])
            if not (c[i] >= a.break_conf and c[j] >= a.break_conf and jump >= a.break_mm and jump > noise): continue
            if span == 2: k = i if np.hypot(x[i + 1] - x[i], y[i + 1] - y[i]) >= np.hypot(x[j] - x[i + 1], y[j] - y[i + 1]) else i + 1   # place the break at the larger single jump
            else: k = i
            if k in seen: continue
            seen.add(k); cands.append({'between': [int(ok[max(k - (span - 1), 0)]['z0']), int(ok[min(k + span, len(ok) - 1)]['z1'])], 'i': k, 'span': span, 'jump_mm': round(jump, 3), 'noise_mm': round(noise, 3)})
    # within-slab kinks: first-half vs last-half centres differ by >= break_mm and > 3x the odd/even noise, in a slab of confidence >= min_conf
    for i, r in enumerate(ok):
        hfl = r.get('half_first_last_mm')
        if hfl is None or i in seen: continue
        if (r.get('confidence') or 0) >= a.min_conf and hfl >= a.break_mm and hfl > 3 * max(sh[i], 0.02):
            seen.add(i); cands.append({'between': [int(r['z0']), int(r['z1'])], 'i': i, 'span': 0, 'jump_mm': round(float(hfl), 3), 'noise_mm': round(float(3 * sh[i]), 3), 'within_slab': True})
    cands.sort(key=lambda q: q['i'])
    # refinement: 8-slice slabs across each candidate break (localises it to +-4 slices)
    refined = []
    if a.src and cands:
        import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import st_axis as SA
        V = SA.open_source(a.src); p = dict(S['params']); rng = np.random.default_rng(1); ic = tuple(S['image_centre'])
        for cd in cands:
            z0, z1 = cd['between']; pts = []
            for zz in range(z0, z1, 8):
                stack = np.asarray(V[zz:min(zz + 8, z1)]).astype(np.float32) / 255.0; rec, _ = SA.analyse_slab(stack, a.vox_um, p, rng, ic)
                if rec.get('status') == 'ok': pts.append((zz + 3.5, rec['centre'][0], rec['centre'][1], rec['confidence']))
            if len(pts) >= 3:
                P = np.array(pts); jumps = np.hypot(np.diff(P[:, 1]), np.diff(P[:, 2])) / mm; k = int(np.argmax(jumps)); cd['refined_break_z'] = float((P[k, 0] + P[k + 1, 0]) / 2); cd['refined_jump_mm'] = round(float(jumps[k]), 3); cd['refined_points'] = [[round(float(q), 2) for q in row] for row in P.tolist()]
                refined.append(cd)
    w = c.copy(); delta = a.huber_mm * mm; lams = [10 ** k for k in np.arange(-2, 6, 0.5)]
    def fit_all(breaks):
        best = None
        for lam in lams:
            cv = loo_cv(z, x, w, lam, breaks, delta) + loo_cv(z, y, w, lam, breaks, delta)
            if best is None or cv < best[0]: best = (cv, lam)
        cv, lam = best; return cv, lam, huber_fit(z, x, w, lam, breaks, delta), huber_fit(z, y, w, lam, breaks, delta)
    cv0, lam0, fx0, fy0 = fit_all([]); breaks = []
    for cd in cands:                                                        # accept a break only if it lowers the CV error
        if cd.get('within_slab') and 'refined_break_z' in cd: cd['i'] = cd['i'] if cd['refined_break_z'] >= z[cd['i']] else max(cd['i'] - 1, 0)
        trial = breaks + [cd['i']]; cv1, lam1, fx1, fy1 = fit_all(trial)
        cd['cv_without'] = round(float(cv0 if not breaks else fit_all(breaks)[0]), 4); cd['cv_with'] = round(float(cv1), 4); cd['accepted'] = bool(cv1 < cd['cv_without'])
        if cd['accepted']: breaks = trial
    cv, lam, fx, fy = fit_all(breaks)
    # smoothing sensitivity (bar M8): axis change under lambda/3 and 3 lambda
    fx3a, fy3a = huber_fit(z, x, w, lam / 3, breaks, delta), huber_fit(z, y, w, lam / 3, breaks, delta); fx3b, fy3b = huber_fit(z, x, w, lam * 3, breaks, delta), huber_fit(z, y, w, lam * 3, breaks, delta)
    sens = float(max(np.max(np.hypot(fx3a - fx, fy3a - fy)[c >= a.min_conf]) if (c >= a.min_conf).any() else 0, np.max(np.hypot(fx3b - fx, fy3b - fy)[c >= a.min_conf]) if (c >= a.min_conf).any() else 0)) / mm
    # per-slice curve with confidence and bridging envelope
    zz = np.arange(Z); bz = [ok[b]['z1'] if b < len(ok) else Z for b in breaks]
    def interp_piece(f):
        out = np.zeros(Z); edges = [0] + sorted(bz) + [Z]
        for e0, e1 in zip(edges[:-1], edges[1:]):
            m = (z >= e0) & (z < e1)
            if m.sum() == 0: continue
            out[e0:e1] = np.interp(zz[e0:e1], z[m], f[m]) if m.sum() > 1 else f[m][0]
        return out
    X, Y = interp_piece(fx), interp_piece(fy); conf = np.interp(zz, z, c); bridged = conf < a.min_conf
    # envelope in low-confidence gaps: distance between the two one-sided linear extrapolations of the confident neighbours
    env = np.zeros(Z); lab = np.diff(np.concatenate([[0], bridged.astype(int), [0]])); starts = np.nonzero(lab == 1)[0]; ends = np.nonzero(lab == -1)[0]
    gaps = []
    for s0, s1 in zip(starts, ends):
        left = [i for i in range(len(z)) if z[i] < s0 and c[i] >= a.min_conf][-2:]; right = [i for i in range(len(z)) if z[i] >= s1 and c[i] >= a.min_conf][:2]
        if len(left) == 2 and len(right) == 2:
            def ext(i0, i1, zq): t = (zq - z[i0]) / (z[i1] - z[i0]); return fx[i0] + t * (fx[i1] - fx[i0]), fy[i0] + t * (fy[i1] - fy[i0])
            zq = zz[s0:s1]; lx, ly = ext(left[0], left[1], zq); rx, ry = ext(right[1], right[0], zq); env[s0:s1] = np.hypot(lx - rx, ly - ry) / mm
        else: env[s0:s1] = np.inf
        gaps.append({'z': [int(s0), int(s1)], 'len_mm': round((s1 - s0) / mm, 2), 'envelope_max_mm': (None if not np.isfinite(env[s0:s1]).all() else round(float(env[s0:s1].max()), 3))})
    U = {'vox_um': a.vox_um, 'n_slabs_ok': len(ok), 'lambda': lam, 'cv_err_vox2': round(float(cv), 4), 'breaks': [float(cd.get('refined_break_z', (z[cd['i']] + z[cd['i'] + 1]) / 2)) for cd in cands if cd.get('accepted')], 'break_candidates': cands,
         'smoothing_sensitivity_mm': round(sens, 4), 'gaps': gaps, 'frac_z_confident': round(float((~bridged).mean()), 4), 'z': zz.tolist(), 'x': np.round(X, 2).tolist(), 'y': np.round(Y, 2).tolist(), 'confidence': np.round(conf, 3).tolist(), 'bridged': bridged.tolist(), 'envelope_mm': [None if not np.isfinite(e) else round(float(e), 3) for e in env],
         'slab_table': [{'z_mid': float(zi), 'x': float(xi), 'y': float(yi), 'conf': float(ci), 'fit_x': float(fxi), 'fit_y': float(fyi), 'resid_mm': round(float(np.hypot(fxi - xi, fyi - yi)) / mm, 4)} for zi, xi, yi, ci, fxi, fyi in zip(z, x, y, c, fx, fy)]}
    U['source'] = a.source; json.dump(U, open(os.path.join(a.out, 'umbilicus.json'), 'w')); print(json.dumps({k: U[k] for k in ['n_slabs_ok', 'lambda', 'cv_err_vox2', 'breaks', 'smoothing_sensitivity_mm', 'gaps', 'frac_z_confident']}))

if __name__ == '__main__': main()
