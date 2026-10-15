#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-2 item 8A (+A1, A2): pilot A of ORD-3 on the cached band, no network. A1 the declared phantom through ORD-3 at dy 4 (V1) and
through the cached-means variant at dy 32; A2 the null baseline along the seed curve on the real means; A3 ORD-3-M over the 19 means
both ways plus the injected-hop test on the real means (with unshifted controls); A4 export, mesh checks, G1-G3; the PASS-A rule.
Every number is written to <out>/pilotA.json; nothing here is a claim about ink or letters.
usage: pilot_ord3a.py <params.json> <out_dir> --phantom <dir with block.npy truth.npz params.json> --store <dir of sec_<y>.npy>
       --seed_npz <surface.npz> --seed_y 5820 --origin 1312 544 [--only A1,A2,A3,A4] [--threads 4]"""
import os, sys, json, time, hashlib, subprocess, argparse, numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import ord3
PY = sys.executable; REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def J(o): return o.item() if hasattr(o, 'item') else str(o)
def run(cmd, env_threads, log):
    env = dict(os.environ, OMP_NUM_THREADS=str(env_threads), OPENBLAS_NUM_THREADS=str(env_threads), MKL_NUM_THREADS=str(env_threads)); return subprocess.Popen(cmd, stdout=open(log, 'w'), stderr=subprocess.STDOUT, env=env, cwd=REPO)

# ------------------------------------------------------------------ scoring against a phantom truth (V1)
def score_phantom(out_dir, truth, P, dy, clean_only=False):
    G = np.load(os.path.join(out_dir, 'grow_status.npz')); st = G['status'].copy(); pos = G['pos']; ys = G['ys']; ver = G['identity_verified'];
    if clean_only and 'clean' in G.files: st[:, 0][(st[:, 0] == ord3.ANCHORED) & ~G['clean']] = 99                                   # DECL-E2E-2-A5: score the CLEAN export set (non-clean anchored cells are neither anchored nor flagged)
    z = truth['z']; T = int(truth['target']); s_true = truth['s'].astype(np.float32); X = z.shape[2]; xx = np.arange(X)
    hops = truth['hops']; y_seed = int(truth['y_seed']); i_seed = int(np.nonzero(ys == y_seed)[0][0]); seed_anch = st[i_seed, 0] == ord3.ANCHORED
    rows = []; err_all = []; wrong = 0; nomat = 0; n_anch = 0; cov = {b: [0, 0] for b in ('0-0.25', '0.25-0.5', '0.5-1.0')}; cov_all = [0, 0]; cov_w = {}
    for i, y in enumerate(ys):
        a = st[i, 0] == ord3.ANCHORED; xs = pos[i, 0, :, 1]; zs = pos[i, 0, :, 0]; zt_row = z[T, y]; fin = np.isfinite(zt_row)
        if fin.sum() < 2: continue
        zt = np.interp(xs, xx[fin], zt_row[fin]); gap = np.interp(xs, xx, (~fin).astype(np.float32)) > 0.01; err = zs - zt
        up = z[T + 1, y] - z[T, y] if T + 1 < z.shape[0] else np.full(X, np.nan); dn = z[T, y] - z[T - 1, y] if T > 0 else np.full(X, np.nan); dc_row = np.fmin(np.where(np.isfinite(up), up, np.inf), np.where(np.isfinite(dn), dn, np.inf)); dc_row[~np.isfinite(dc_row)] = 44.0
        dc = np.interp(xs, xx, dc_row); good = a & ~gap; wr = good & (np.abs(err) > 0.5 * dc); wrong += int(wr.sum()); nomat += int((a & gap).sum()); n_anch += int(a.sum()); err_all.append(err[good])
        # coverage of the true lamina (cells whose x falls on material) per tilt bin
        sa = np.abs(np.interp(xs, xx, np.nan_to_num(s_true[T, y]))); onmat = ~gap
        for (lo, hi), key in zip(((0, 0.25), (0.25, 0.5), (0.5, 1.01)), cov): m = onmat & (sa >= lo) & (sa < hi); cov[key][0] += int((m & a).sum()); cov[key][1] += int(m.sum())
        cov_all[0] += int((onmat & a).sum()); cov_all[1] += int(onmat.sum())
        if 'width' in truth.files and truth['width'].ndim == 1: wT = float(truth['width'][T]); key_w = 'thin' if wT < 10 else 'sheet'; cov_w.setdefault(key_w, [0, 0]); cov_w[key_w][0] += int((onmat & a).sum()); cov_w[key_w][1] += int(onmat.sum())
        rows.append({'y': int(y), 'anchored_frac': round(float(a.mean()), 4), 'rms_err_anch': round(float(np.sqrt(np.mean(err[good] ** 2))), 3) if good.any() else None, 'wrong_lamina': int(wr.sum()), 'anchored_on_gap': int((a & gap).sum()), 'median_abs_err_all': round(float(np.nanmedian(np.abs(err))), 2)})
    err_all = np.concatenate(err_all) if err_all else np.zeros(1)
    # injected hops: detection = fraction of the window's seed-anchored cells flagged (UNRESOLVED, TERMINATED, or ANCHORED-but-I4-failed) within 2 rows past y_c on the hop side
    det = []; 
    for (x0, x1, yc, d, direction) in hops:
        sel_rows = [i for i, y in enumerate(ys) if (direction > 0 and yc < y <= yc + 2 * dy) or (direction < 0 and yc - 2 * dy <= y < yc)]
        if not sel_rows: det.append({'y_c': int(yc), 'rows': 0, 'flag_frac': None}); continue
        xs0 = pos[i_seed, 0, :, 1]; win = seed_anch & (xs0 >= x0) & (xs0 < x1)
        if win.sum() < 10: det.append({'y_c': int(yc), 'rows': len(sel_rows), 'flag_frac': None, 'note': 'fewer than 10 seed-anchored cells in the window'}); continue
        flagged = np.zeros(win.sum(), bool); unexp = np.zeros(win.sum(), bool)
        for i in sel_rows:
            s_ = st[i, 0][win]; f = (s_ == ord3.UNRESOLVED) | (s_ == ord3.TERMINATED) | ((s_ == ord3.ANCHORED) & ~ver[i][win]); flagged |= f; unexp |= f | (s_ != ord3.ANCHORED)
        det.append({'y_c': int(yc), 'x0': int(x0), 'd': int(d), 'dir': int(direction), 'rows': len(sel_rows), 'n_cells': int(win.sum()), 'flag_frac': round(float(flagged.mean()), 3), 'flag_or_unexported_frac': round(float(unexp.mean()), 3)})
    ff = [h['flag_frac'] for h in det if h['flag_frac'] is not None]; fu = [h['flag_or_unexported_frac'] for h in det if h.get('flag_or_unexported_frac') is not None]; det_rate = float(np.mean([f >= 0.5 for f in fu])) if fu else None; det_rate_flag_only = float(np.mean([f >= 0.5 for f in ff])) if ff else None   # DECL-E2E-2-A4 item 8
    # false SWAP/MERGE outside hop windows, bridges across the shear line and inside the termination region
    led = json.load(open(os.path.join(out_dir, 'ledger.json'))); sm = [e for e in led if e['type'] in ('SWAP', 'MERGE')]
    def in_hop(e):
        y = e['y']; u = e.get('u'); 
        if u is None: return True
        x = pos[int(np.nonzero(ys == y)[0][0]), 0, u, 1]
        return any((x0 <= x < x1) and ((direction > 0 and y > yc) or (direction < 0 and y < yc)) for (x0, x1, yc, d, direction) in hops)
    false_sm = sum(1 for e in sm if not in_hop(e)); both = int(np.isfinite(G['dA']).sum() + 0) ; pairs = int((np.isfinite(G['dA']) & np.isfinite(G['dB'])).sum())
    shear = truth['shear']; zp, xp, ang, side = float(shear[0]), float(shear[1]), float(shear[2]), int(shear[3]); term = truth['term']; tx0, tx1, yt = int(term[0]), int(term[1]), int(term[2])
    br_shear = 0; br_term_late = 0; br_term_early = 0
    for i, y in enumerate(ys):
        b = st[i, 0] == ord3.BRIDGED; xs = pos[i, 0, :, 1]; zs = pos[i, 0, :, 0]; xl = xp + (zs - zp) * np.tan(np.deg2rad(ang)); br_shear += int((b & (np.abs(xs - xl) < 24)).sum())
        inreg = b & (xs >= tx0) & (xs < tx1) & (y > yt)
        if y > yt + P['status']['G_y_sections']: br_term_late += int(inreg.sum())
        else: br_term_early += int(inreg.sum())
    res = {'rows': rows, 'n_anchored_cells': n_anch, 'rms_err_anchored': round(float(np.sqrt(np.mean(err_all ** 2))), 3), 'p95_abs_err_anchored': round(float(np.percentile(np.abs(err_all), 95)), 3), 'wrong_lamina_anchored': wrong, 'anchored_on_gap_or_void': nomat,
           'coverage_by_tilt': {k: (round(v[0] / v[1], 4) if v[1] else None) for k, v in cov.items()}, 'coverage_all': round(cov_all[0] / max(1, cov_all[1]), 4), 'target_width_vox': (float(truth['width'][T]) if 'width' in truth.files and truth['width'].ndim == 1 else None), 'coverage_by_target_width_class': {k: (round(v[0] / v[1], 4) if v[1] else None) for k, v in cov_w.items()}, 'hops': det, 'hop_detection_rate_ge50pct': det_rate, 'hop_detection_rate_flag_only': det_rate_flag_only, 'hop_flag_frac_mean': round(float(np.mean(ff)), 3) if ff else None, 'hop_flag_or_unexported_mean': round(float(np.mean(fu)), 3) if fu else None,
           'false_swap_merge_events': false_sm, 'cell_rows_both_twins': pairs, 'false_swap_merge_frac': round(false_sm / max(1, pairs), 5), 'bridged_near_shear_line': br_shear, 'bridged_in_termination_region_after_Gy': br_term_late, 'bridged_in_termination_region_within_Gy': br_term_early}
    res['revived_cells'] = int(G['revived'].sum()) if 'revived' in G.files else None; res['dormant_frac_mean'] = round(float((st[:, 0] == ord3.DORMANT).mean()), 4)
    res['V1'] = {'rms_le_2': res['rms_err_anchored'] <= 2.0, 'zero_wrong_lamina': wrong == 0 and n_anch >= 10000, 'n_anchored_ge_1e4': n_anch >= 10000, 'coverage_ge_0.90_all_bins': all((v is None) or (v >= 0.90) for v in res['coverage_by_tilt'].values()), 'hops_ge_0.95': (det_rate is not None) and det_rate >= 0.95, 'no_bridge_shear_or_termination': br_shear == 0 and br_term_late == 0, 'false_swap_merge_le_1pct': res['false_swap_merge_frac'] <= 0.01}
    res['V1']['pass'] = all(res['V1'].values()); return res

def phantom_seed(truth, out_npy, P, rng):
    z = truth['z']; T = int(truth['target']); ys_ = int(truth['y_seed']); zt = z[T, ys_]; X = len(zt); xx = np.arange(X); fin = np.isfinite(zt); x0, x1 = int(np.nonzero(fin)[0][0]), int(np.nonzero(fin)[0][-1])
    zi = np.interp(xx[x0:x1 + 1], xx[fin], zt[fin]); pert = ndi.gaussian_filter1d(rng.normal(0, 1.5, x1 - x0 + 1), 8.0); C = np.stack([zi + pert, xx[x0:x1 + 1].astype(np.float64)], 1); np.save(out_npy, C); return C

def phantom_means(block_path, out_store, y_seed, dy=32, n=16):
    """The declared cached-step variant of the phantom: 16-section means at dy 32, scaled like ct_sections (per section p0.5-p99.5 to 1..255)."""
    blk = np.load(block_path, mmap_mode='r'); Y = blk.shape[0]; os.makedirs(out_store, exist_ok=True); ys = [y for y in range(y_seed % dy, Y - n + 1, dy)]
    if y_seed not in ys: ys = sorted(set(ys) | {y_seed})
    for y in ys:
        m = np.asarray(blk[y:y + n]).astype(np.float32).mean(0); mk = m > 0; lo, hi = np.percentile(m[mk], [0.5, 99.5]); sec = (np.clip((m - lo) / (hi - lo + 1e-6), 0, 1) * 254 + 1).astype(np.uint8) * mk; np.save(f'{out_store}/sec_{y}.npy', sec)
    return ys

# ------------------------------------------------------------------ A2: nulls on the real means along the seed curve
def A2_nulls(P, store, ys, seed_npz, seed_y, origin, out):
    t0 = time.time(); src = ord3.MeansSource(store, ys); seed = ord3.seed_from_e2e(seed_npz, seed_y, origin, P['sigma_u']); tr = ord3.Tracker(src, P, seed, seed_y, ys[1] - ys[0], out, origin=origin, nulls=True, overlay_every=0, verbose=False); st = tr.seed()
    F = tr.seed_fields; Rs, M, void, mask, tex, bb = F['Rs'], F['M'], F['void'], F['mask'], F['tex'], F['bb']; o = np.array([bb[0], bb[2]], np.float64); C0 = F['C0'] - o; n0 = F['n0']; tau = tr.tau; U = len(C0)
    dA, dB = st['dA'], st['dB']; dcomp = np.minimum(np.abs(np.where(np.isfinite(dA), dA, ord3.OPEN)), np.abs(np.where(np.isfinite(dB), dB, ord3.OPEN)))
    V = np.arange(-13, 14).astype(np.float64); pts = C0[:, None, :] + V[None, :, None] * n0[:, None, :]; rs = ord3.sample(Rs, pts) / tau; lm = (rs >= np.roll(rs, 1, 1)) & (rs >= np.roll(rs, -1, 1)) & (rs >= 0.5); lm[:, 0] = lm[:, -1] = False
    two9 = (lm[:, 4:23].sum(1) >= 2).mean(); two13 = (lm.sum(1) >= 2).mean()
    rh = ord3.rho_of(F['C0'], P['sigma_u']); sets = {'T': (C0, n0)}; m1 = np.isfinite(dA); sets['C1_between'] = ((C0 + 0.5 * np.nan_to_num(dA)[:, None] * n0)[m1], n0[m1]); sets['C2_twinA'] = ((st['C'][1] - o)[m1], st['n'][1][m1])
    rng = np.random.default_rng(0); zz, xx = np.nonzero(mask); i = rng.integers(0, len(zz), 2000); th = rng.uniform(0, np.pi, 2000); sets['C3_random'] = (np.stack([zz[i], xx[i]], 1).astype(np.float64), np.stack([np.sin(th), np.cos(th)], 1))
    nulls = {k: {'n': int(len(p)), 'accept_d4': round(tr.accept_stat(Rs, void, tau, p, n, 4), 4), 'accept_d12': round(tr.accept_stat(Rs, void, tau, p, n, 12), 4), 'g5_on_M': round(tr.g5_stat(M, p, n), 4)} for k, (p, n) in sets.items()}
    # per-step motion seed -> next mean: NCC lag of the normal profile within +-22, second-peak fraction
    y1 = ys[ys.index(seed_y) + 1]; M1 = np.asarray(src.mm[y1][bb[0]:bb[1], bb[2]:bb[3]]).astype(np.float32); W = np.arange(-40, 41).astype(np.float64); p0 = ord3.sample(M.astype(np.float32), C0[:, None, :] + W[None, :, None] * n0[:, None, :]); p1 = ord3.sample(M1, C0[:, None, :] + W[None, :, None] * n0[:, None, :])
    p0 = (p0 - p0.mean(1, keepdims=True)) / (p0.std(1, keepdims=True) + 1e-6); p1 = (p1 - p1.mean(1, keepdims=True)) / (p1.std(1, keepdims=True) + 1e-6); lags = np.arange(-22, 23); ncc = np.stack([(p0[:, 22 + 18 - 0:22 + 18 + 1 + 0] * 0).sum(1) for _ in [0]], 1) * 0
    core = slice(22, 59); ncc = np.stack([(p0[:, core] * p1[:, core.start + l:core.stop + l]).mean(1) for l in lags], 1); best = lags[np.argmax(ncc, 1)]; srt = np.sort(ncc, 1); second = srt[:, -2] >= 0.8 * srt[:, -1]
    motion = {'median_abs_lag': float(np.median(np.abs(best))), 'frac_gt8': round(float((np.abs(best) > 8).mean()), 3), 'frac_gt14': round(float((np.abs(best) > 14).mean()), 3), 'second_peak_frac': round(float(second.mean()), 3), 'y_pair': [int(seed_y), int(y1)]}
    # tau per section on the seed tube (adaptive gate)
    taus = {}
    for y in ys: Mi = np.asarray(src.mm[y][bb[0]:bb[1], bb[2]:bb[3]]); taus[int(y)] = round(float(ord3.gated_fields(Mi, Mi > 0, P['fields'])[5]), 5)
    # identifiability budget
    budget = {f'dy{dy}_s{s}': round(float((np.floor(0.5 * dcomp) - 1 - dy * s >= 1).mean()), 4) for dy in (32, 16, 8, 4) for s in (0.34, 1.0)}
    res = {'seed': tr.seed_info, 'ablation': tr.ablation, 'seed_row_record': tr.records[-1], 'dcomp_p10_25_50': [round(float(v), 1) for v in np.percentile(dcomp, [10, 25, 50])], 'frac_ge2_gated_maxima_within_9': round(float(two9), 4), 'frac_ge2_gated_maxima_within_13': round(float(two13), 4), 'open_side_frac': {'A': round(float(~np.isfinite(dA)).mean() if False else float((~np.isfinite(dA)).mean()), 4), 'B': round(float((~np.isfinite(dB)).mean()), 4)},
           'rho_frac_below': {str(r): round(float((rh < r).mean()), 3) for r in (20, 28, 48, 144)}, 'nulls_seed_row': nulls, 'motion_seed_to_next': motion, 'tau_per_section': taus, 'identifiability_budget': budget, 'secs': round(time.time() - t0, 1), 'rss_gb': round(ord3.rss_gb(), 2)}
    return res

# ------------------------------------------------------------------ A3 hop test on the real means (rigid band shift by d_comp along the mean normal, y >= seed + dy)
class ShiftedMeans(ord3.MeansSource):
    def __init__(self, store, ys, y_from, band_x, shift_zx): super().__init__(store, ys); self.y_from, self.band_x, self.shift = y_from, band_x, np.array(shift_zx, np.float64)
    def mean(self, y, bb, s_dense=None, nhat=None):
        c = np.asarray(self.mm[y][bb[0]:bb[1], bb[2]:bb[3]])
        if y >= self.y_from and np.abs(self.shift).sum() > 0:
            xa, xb = max(0, int(self.band_x[0] - bb[2])), min(c.shape[1], int(self.band_x[1] - bb[2]))
            if xb > xa:
                sub = c[:, xa:xb].astype(np.float32); zz, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]].astype(np.float32); sh = ndi.map_coordinates(sub, [zz - self.shift[0], xx - self.shift[1]], order=1, mode='nearest'); c = c.copy(); c[:, xa:xb] = np.clip(sh, 0, 255).astype(np.uint8)
        return c, c > 0, c

def A3_hops(P, store, ys, seed_npz, seed_y, origin, out, n_place=20, win=232, margin=100):
    t0 = time.time(); seed = ord3.seed_from_e2e(seed_npz, seed_y, origin, P['sigma_u']); U = len(seed); i0 = ys.index(seed_y); ys2 = ys[i0:i0 + 3]; dy = ys[1] - ys[0]
    base = ord3.MeansSource(store, ys2); tr0 = ord3.Tracker(base, P, seed, seed_y, dy, os.path.join(out, 'hop_seed'), origin=origin, nulls=False, overlay_every=0, verbose=False); st0 = tr0.seed(); dA, dB = st0['dA'], st0['dB']; dcomp = np.minimum(np.abs(np.where(np.isfinite(dA), dA, ord3.OPEN)), np.abs(np.where(np.isfinite(dB), dB, ord3.OPEN))); n0 = st0['n'][0]
    starts = np.linspace(margin, U - win - margin, n_place).astype(int); results = []
    for shifted in (True, False):
        for u0 in starts:
            u1 = u0 + win; cells = slice(max(0, u0 - margin), min(U, u1 + margin)); d = float(np.median(dcomp[u0:u1])); nb = np.median(n0[u0:u1], 0); nb /= np.linalg.norm(nb) + 1e-9; xs = seed[u0:u1, 1]; band = (xs.min() - 8, xs.max() + 8)
            src = ShiftedMeans(store, ys2, ys2[1], band, (d * nb if shifted else (0.0, 0.0))); tr = ord3.Tracker(src, P, seed[cells], seed_y, dy, os.path.join(out, 'hop_tmp'), origin=origin, nulls=False, overlay_every=0, verbose=False); st = tr.seed(); tr.sweep(2, 0)
            w = slice(u0 - cells.start, u1 - cells.start); sa = tr.rows[0]['status'][0][w] == ord3.ANCHORED; flagged = np.zeros(int(sa.sum()), bool)
            for k in (1, 2):
                s_ = tr.rows[k]['status'][0][w][sa]; v_ = tr.rows[k]['verified'][w][sa]; flagged |= (s_ == ord3.UNRESOLVED) | (s_ == ord3.TERMINATED) | ((s_ == ord3.ANCHORED) & ~v_)
            results.append({'shifted': shifted, 'u0': int(u0), 'd_vox': round(d, 1), 'n_seed_anchored': int(sa.sum()), 'flag_frac': round(float(flagged.mean()), 3) if sa.sum() else None, 'anchored_row1': round(float((tr.rows[1]['status'][0][w] == ord3.ANCHORED).mean()), 3), 'anchored_row2': round(float((tr.rows[2]['status'][0][w] == ord3.ANCHORED).mean()), 3), 'i4_power_rows': [tr.rows[k]['i4_power'] for k in (1, 2)]})
    sh = [r['flag_frac'] for r in results if r['shifted'] and r['flag_frac'] is not None and r['n_seed_anchored'] >= 10]; ct = [r['flag_frac'] for r in results if not r['shifted'] and r['flag_frac'] is not None and r['n_seed_anchored'] >= 10]
    return {'placements': results, 'detection_rate_ge50pct': round(float(np.mean([f >= 0.5 for f in sh])), 3) if sh else None, 'flag_frac_shifted_mean': round(float(np.mean(sh)), 3) if sh else None, 'flag_frac_control_mean': round(float(np.mean(ct)), 3) if ct else None, 'control_false_alarm_rate_ge50pct': round(float(np.mean([f >= 0.5 for f in ct])), 3) if ct else None, 'n_valid_shifted': len(sh), 'n_valid_control': len(ct), 'secs': round(time.time() - t0, 1)}

def A4_checks(P, out_means, seed_len_vox, vox_um, dy):
    G = np.load(os.path.join(out_means, 'grow_status.npz')); st = G['status']; pos = G['pos']; ys = G['ys']; U = st.shape[2]; anch = st[:, 0] == ord3.ANCHORED
    g2_rows = (anch.mean(1) >= 0.9); steps = []
    for i in range(1, len(ys)):
        both = anch[i] & anch[i - 1]
        if both.any(): steps.append(np.linalg.norm(pos[i, 0][both] - pos[i - 1, 0][both], axis=1))
    steps = np.concatenate(steps) if steps else np.zeros(1); mesh = None; md = os.path.join(out_means, 'mesh_checks'); 
    try:
        r = subprocess.run([PY, os.path.join(HERE, 'mesh_checks.py'), 'check', os.path.join(out_means, 'surface_tifxyz'), md], capture_output=True, text=True, timeout=600, cwd=REPO)
        cand = [os.path.join(md, f) for f in os.listdir(md) if f.endswith('.json')] if os.path.isdir(md) else []
        mesh = json.load(open(cand[0])) if cand else {'error': (r.stdout + r.stderr)[-600:]}
    except Exception as e: mesh = {'error': str(e)}
    return {'G1_seed_path_mm': round(seed_len_vox * vox_um / 1000.0, 2), 'G1_pass_ge_20mm': seed_len_vox * vox_um / 1000.0 >= 20, 'G2_frac_rows_ge_0.9_coverage': round(float(g2_rows.mean()), 4), 'G2_pass': bool(g2_rows.mean() >= 0.9), 'G3_step_vox_median_p90': [round(float(np.median(steps)), 2), round(float(np.percentile(steps, 90)), 2)], 'G3_note': f'steps between anchored cells of consecutive rows at dy {dy}; bounded by the label range by construction', 'mesh_checks': mesh}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('params'); ap.add_argument('out'); ap.add_argument('--phantom', required=True); ap.add_argument('--store', required=True); ap.add_argument('--seed_npz', required=True); ap.add_argument('--seed_y', type=int, default=5820); ap.add_argument('--origin', type=int, nargs=2, default=[1312, 544]); ap.add_argument('--only', default='A1,A2,A3,A4,means_variant'); ap.add_argument('--threads', type=int, default=4); ap.add_argument('--prior_a2', default=None, help='pilotA.json of a previous run whose A2 stands (DECL-E2E-2-A3 item 5)')
    a = ap.parse_args(); P = json.load(open(a.params)); out = a.out; os.makedirs(out, exist_ok=True); T0 = time.time(); only = set(a.only.split(','))
    rec = {'declaration': ['DECL-E2E-2', 'DECL-E2E-2-A1', 'DECL-E2E-2-A2', 'DECL-E2E-2-A3', 'DECL-E2E-2-A4'], 'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'hashes': {f: sha(os.path.join(HERE, f)) for f in ('ord3.py', 'phantom_ord3.py', 'pilot_ord3a.py')}, 'params_sha256': sha(a.params), 'params': P, 'phantom_params_sha256': sha(os.path.join(a.phantom, 'params.json')) if os.path.exists(os.path.join(a.phantom, 'params.json')) else None, 'free_mb_before': subprocess.run(['free', '-m'], capture_output=True, text=True).stdout.split('\n')[1]}
    json.dump(rec, open(os.path.join(out, 'pilotA.json'), 'w'), indent=1, default=J)                                        # hashes written before any real section is read
    ys = sorted(int(f[4:-4]) for f in os.listdir(a.store) if f.startswith('sec_')); dy = ys[1] - ys[0]; procs = {}
    phantoms = [q for q in a.phantom.split(',') if q]; truths = {}
    if 'A1' in only:                                                                                                       # A1 phantoms at dy 4 (1 CPU each, background processes)
        for pi, pd in enumerate(phantoms):
            tag = f'A1_raw' if pi == 0 else f'A1_raw_{os.path.basename(pd.rstrip("/"))}'; truth = np.load(os.path.join(pd, 'truth.npz'), allow_pickle=True); truths[tag] = (truth, pd)
            rng = np.random.default_rng(0); seed_npy = os.path.join(out, f'{tag}_seed.npy'); phantom_seed(truth, seed_npy, P, rng); Y = np.load(os.path.join(pd, 'block.npy'), mmap_mode='r').shape[0]; ysd = int(truth['y_seed'])
            rows_neg = min(47, (ysd - 6) // P['dy']); rows_pos = min(48, (Y - 7 - ysd) // P['dy']); d1 = os.path.join(out, tag)
            procs[tag] = (run([PY, os.path.join(HERE, 'ord3.py'), 'raw', a.params, d1, '--block', os.path.join(pd, 'block.npy'), '--seed_npy', seed_npy, '--seed_y', str(ysd), '--rows', str(rows_neg), str(rows_pos)], 1, os.path.join(out, f'{tag}.log')), time.time())
        rec['phantoms'] = {t: {'dir': pd, 'params_sha256': sha(os.path.join(pd, 'params.json')) if os.path.exists(os.path.join(pd, 'params.json')) else None, 'target': int(tr['target']), 'target_width': float(tr['width'][int(tr['target'])])} for t, (tr, pd) in truths.items()}; json.dump(rec, open(os.path.join(out, 'pilotA.json'), 'w'), indent=1, default=J)
        truth = truths['A1_raw'][0]
    if 'A3' in only:                                                                                                       # A3 ORD-3-M on the 19 real means (2 CPUs, background process)
        d3 = os.path.join(out, 'A3_means'); procs['A3'] = (run([PY, os.path.join(HERE, 'ord3.py'), 'means', a.params, d3, '--store', a.store, '--seed_npz', a.seed_npz, '--seed_y', str(a.seed_y), '--origin', str(a.origin[0]), str(a.origin[1])], 2, os.path.join(out, 'A3_means.log')), time.time())
    if 'A2' in only:
        os.environ['OMP_NUM_THREADS'] = '1'; rec['A2'] = A2_nulls(P, a.store, ys, a.seed_npz, a.seed_y, a.origin, os.path.join(out, 'A2_nulls')); json.dump(rec, open(os.path.join(out, 'pilotA.json'), 'w'), indent=1, default=J); print('A2 done', rec['A2']['secs'], 's', flush=True)
    if 'A3' in only:
        rec['A3_hops'] = A3_hops(P, a.store, ys, a.seed_npz, a.seed_y, a.origin, os.path.join(out, 'A3_hops')); json.dump(rec, open(os.path.join(out, 'pilotA.json'), 'w'), indent=1, default=J); print('A3 hop test done', rec['A3_hops']['secs'], 's', flush=True)
    if 'A1' in only and 'means_variant' in only:                                                                           # phantom at the cached step (means variant; seed-0 phantom only), in-process while the raw runs finish
        store_ph = os.path.join(out, 'A1_means_store'); ysp = phantom_means(os.path.join(phantoms[0], 'block.npy'), store_ph, int(truth['y_seed'])); C = np.load(os.path.join(out, 'A1_raw_seed.npy'))
        np.savez(os.path.join(out, 'A1_seed_surface.npz'), Z=C[None, ::4, 0].astype(np.float32), X=C[None, ::4, 1].astype(np.float32), U=np.arange(0, len(C), 4).astype(np.float32), ys=np.array([int(truth['y_seed'])]))
        d1m = os.path.join(out, 'A1_means'); p = run([PY, os.path.join(HERE, 'ord3.py'), 'means', a.params, d1m, '--store', store_ph, '--seed_npz', os.path.join(out, 'A1_seed_surface.npz'), '--seed_y', str(int(truth['y_seed']))], 1, os.path.join(out, 'A1_means.log')); p.wait()
        rec['A1_means_variant'] = {'returncode': p.returncode, 'ys': [int(y) for y in ysp]}
        if p.returncode == 0: rec['A1_means_variant'].update(score_phantom(d1m, truth, P, 32)); rec['A1_means_variant']['grow_checks'] = {k: v for k, v in json.load(open(os.path.join(d1m, 'grow_checks.json'))).items() if k != 'per_row'}
        else: rec['A1_means_variant']['log_tail'] = open(os.path.join(out, 'A1_means.log')).read()[-1500:]
    for key, (p, t0) in procs.items():
        p.wait(); rec[key] = {'returncode': p.returncode, 'wall_s': round(time.time() - t0, 1)}; dname = 'A3_means' if key == 'A3' else key; d = os.path.join(out, dname); log = open(os.path.join(out, f'{dname}.log')).read()
        if p.returncode == 0:
            gc = json.load(open(os.path.join(d, 'grow_checks.json'))); rec[key]['grow_checks'] = {k: v for k, v in gc.items() if k != 'per_row'}; rec[key]['per_row_brief'] = [{k2: r[k2] for k2 in ('tag', 'k', 'y', 'secs', 'rss_gb', 'identity_verified_frac', 'swap_merge_cells')} | {'T_anch': r['T']['anchored_frac'], 'T_unres': r['T']['UNRESOLVED'], 'T_br': r['T']['BRIDGED'], 'T_term': r['T']['TERMINATED'], 'I4_power': r['I4']['power'], 'nulls_accept_d4': {k3: v3.get('accept_d4') for k3, v3 in r['nulls'].items()}} for r in gc['per_row']]
            rec[key]['row_secs_median'] = float(np.median([r['secs'] for r in gc['per_row']])); rec[key]['rss_gb_peak'] = gc['rss_gb_peak']
            if key in truths: rec[key]['V1'] = score_phantom(d, truths[key][0], P, P['dy']); rec[key]['V1_clean'] = score_phantom(d, truths[key][0], P, P['dy'], clean_only=True)
        else: rec[key]['log_tail'] = log[-2000:]
        json.dump(rec, open(os.path.join(out, 'pilotA.json'), 'w'), indent=1, default=J); print(key, 'done rc', p.returncode, flush=True)
    if 'A4' in only and 'A3' in rec and rec['A3']['returncode'] == 0:
        seed = ord3.seed_from_e2e(a.seed_npz, a.seed_y, a.origin, P['sigma_u']); rec['A4'] = A4_checks(P, os.path.join(out, 'A3_means'), len(seed), 8.64, dy)
    # PASS-A rule (declared): (i) V1 passes at dy 4; (ii) real-means hop detection >= 0.90; (iii) identifiability at dy 4 and the p90 tilt >= 0.80
    v1s = {k: rec[k].get('V1', {}).get('V1', {}).get('pass') for k in truths}; v1 = all(v is True for v in v1s.values()) if v1s else None; hop = rec.get('A3_hops', {}).get('detection_rate_ge50pct'); ident = rec.get('A2', {}).get('identifiability_budget', {}).get('dy4_s1.0')
    if ident is None and a.prior_a2: ident = json.load(open(a.prior_a2)).get('A2', {}).get('identifiability_budget', {}).get('dy4_s1.0'); rec['A2_from'] = a.prior_a2
    ctrl = rec.get('A3_hops', {}).get('control_false_alarm_rate_ge50pct')
    rec['PASS_A'] = {'i_V1_pass': v1, 'ii_hop_detection': hop, 'control_false_alarm': ctrl, 'ii_pass': (hop is not None and hop >= P['pass_a']['real_hop_detection_min'] and ctrl is not None and ctrl <= P['pass_a'].get('control_false_alarm_max', 0.10)), 'iii_identifiable_dy4_p90': ident, 'iii_pass': (ident is not None and ident >= P['pass_a']['identifiable_frac_min_at_p90_tilt'])}
    rec['PASS_A']['i_per_phantom'] = v1s; rec['PASS_A']['ii_note'] = 'void on the cached means (DECL-E2E-2-A3 item 5): evaluated as V4 of pilot B'
    rec['PASS_A']['pass'] = bool(rec['PASS_A']['i_V1_pass'] and rec['PASS_A']['iii_pass']); rec['wall_min_total'] = round((time.time() - T0) / 60, 2); rec['end_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()); rec['rss_gb_main'] = round(ord3.rss_gb(), 2)
    json.dump(rec, open(os.path.join(out, 'pilotA.json'), 'w'), indent=1, default=J); print(json.dumps(rec['PASS_A']), 'wall', rec['wall_min_total'], 'min')

if __name__ == '__main__': main()
