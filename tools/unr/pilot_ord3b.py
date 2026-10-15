#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-2 item 8B + A5: pilot B of ORD-3 on the raw level-0 block (fetched by ord3_fetch_block.py): the operator at dy 4 with the CLEAN
export, then the bars on real sections: V2 (nulls per row, from grow_checks), V3 (coverage with the full denominator), V4 (injected hops on
raw sections with unshifted controls), V5 (I4 power per row), V6 (raw-ray peak counts between T and its twins), V8 (consistency: the two
sweeps meet at the seed row by construction; the increment and |n_y| histograms), V9 (render from the block: G5, fibre coherence,
orientation consistency; mesh self-intersection), V10 (gaps), V11 (bytes, seconds, RSS), V12 (seed-row ablations), and the PASS-B rule.
Everything is written to <out>/pilotB.json. Nothing here is a claim about ink or letters.
usage: pilot_ord3b.py <params.json> <out_dir> --block_dir /dev/shm/ord3 --seed_npz <surface.npz> --seed_y 5820 [--threads 3] [--only track,hops,bars]"""
import os, sys, json, time, hashlib, subprocess, argparse, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'umb')); import ord3
from st_axis import st_accumulate, st_eigen
PY = sys.executable; REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def J(o): return o.item() if hasattr(o, 'item') else str(o)

class ShiftedBlock(ord3.BlockSource):
    """Injected hop on raw sections (V4): for sections j > y_c the content inside the x-band is rigidly translated by (dz, dx)."""
    def __init__(self, path, n_avg, n_tensor, y_c, band_x, shift_zx): super().__init__(path, n_avg, n_tensor); self.y_c, self.band_x, self.shift = y_c, band_x, np.array(shift_zx, np.float64)
    def section(self, j, bb):
        c, mk = super().section(j, bb)
        if j > self.y_c and np.abs(self.shift).sum() > 0:
            xa, xb = max(0, int(self.band_x[0] - bb[2])), min(c.shape[1], int(self.band_x[1] - bb[2]))
            if xb > xa:
                sub = c[:, xa:xb]; zz, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]].astype(np.float32); c = c.copy(); mk = mk.copy()
                c[:, xa:xb] = ndi.map_coordinates(sub, [zz - self.shift[0], xx - self.shift[1]], order=1, mode='nearest'); mk[:, xa:xb] = ndi.map_coordinates(mk[:, xa:xb].astype(np.float32), [zz - self.shift[0], xx - self.shift[1]], order=0, mode='nearest') > 0.5
        return c, mk

def seed_block(seed_npz, seed_y, origin_zx, P):
    S = np.load(seed_npz); i = int(np.nonzero(S['ys'] == seed_y)[0][0]); C = ord3.resample(S['Z'][i], S['X'][i], 1.0) - np.array(origin_zx, np.float64); return ord3.smooth(C, P['sigma_u'])

def hops_raw(P, block_path, seed, seed_y, out, n_place=20, win=232, margin=100):
    t0 = time.time(); U = len(seed); base = ord3.BlockSource(block_path, P['n_avg'], P.get('n_tensor', 12)); tr0 = ord3.Tracker(base, P, seed, seed_y, P['dy'], os.path.join(out, 'hop_seed'), nulls=False, overlay_every=0, verbose=False); st0 = tr0.seed()
    dA, dB = st0['dA'], st0['dB']; dcomp = np.minimum(np.abs(np.where(np.isfinite(dA), dA, ord3.OPEN)), np.abs(np.where(np.isfinite(dB), dB, ord3.OPEN))); n0 = st0['n'][0]; starts = np.linspace(margin, U - win - margin, n_place).astype(int); res = []
    for shifted in (True, False):
        for u0 in starts:
            u1 = u0 + win; cells = slice(max(0, u0 - margin), min(U, u1 + margin)); d = float(np.median(dcomp[u0:u1])); nb = np.median(n0[u0:u1], 0); nb /= np.linalg.norm(nb) + 1e-9; xs = seed[u0:u1, 1]; band = (xs.min() - 8, xs.max() + 8)
            src = ShiftedBlock(block_path, P['n_avg'], P.get('n_tensor', 12), seed_y, band, d * nb if shifted else (0.0, 0.0)); tr = ord3.Tracker(src, P, seed[cells], seed_y, P['dy'], os.path.join(out, 'hop_tmp'), nulls=False, overlay_every=0, verbose=False); tr.seed(); tr.sweep(2, 0)
            w = slice(u0 - cells.start, u1 - cells.start); sa = tr.rows[0]['status'][0][w] == ord3.ANCHORED; fl = np.zeros(int(sa.sum()), bool); un = fl.copy()
            for k in (1, 2):
                s_ = tr.rows[k]['status'][0][w][sa]; v_ = tr.rows[k]['verified'][w][sa]; f = (s_ == ord3.UNRESOLVED) | (s_ == ord3.TERMINATED) | ((s_ == ord3.ANCHORED) & ~v_); fl |= f; un |= f | (s_ != ord3.ANCHORED)
            res.append({'shifted': shifted, 'u0': int(u0), 'd_vox': round(d, 1), 'n_seed_anchored': int(sa.sum()), 'flag_frac': round(float(fl.mean()), 3) if sa.sum() else None, 'flag_or_unexported_frac': round(float(un.mean()), 3) if sa.sum() else None, 'i4_power_rows': [tr.rows[k]['i4_power'] for k in (1, 2)]})
    sh = [r['flag_or_unexported_frac'] for r in res if r['shifted'] and r['flag_or_unexported_frac'] is not None and r['n_seed_anchored'] >= 10]; ct = [r['flag_or_unexported_frac'] for r in res if not r['shifted'] and r['flag_or_unexported_frac'] is not None and r['n_seed_anchored'] >= 10]
    shf = [r['flag_frac'] for r in res if r['shifted'] and r['flag_frac'] is not None and r['n_seed_anchored'] >= 10]
    return {'placements': res, 'detection_rate_ge50pct': round(float(np.mean([f >= 0.5 for f in sh])), 3) if sh else None, 'detection_rate_flag_only': round(float(np.mean([f >= 0.5 for f in shf])), 3) if shf else None, 'control_false_alarm_rate_ge50pct': round(float(np.mean([f >= 0.5 for f in ct])), 3) if ct else None, 'shifted_mean': round(float(np.mean(sh)), 3) if sh else None, 'control_mean': round(float(np.mean(ct)), 3) if ct else None, 'n_valid': [len(sh), len(ct)], 'secs': round(time.time() - t0, 1)}

def render_and_bars(P, block_path, out_track, origin_zx):
    """V6, V8, V9, V10 from the block and the tracker's export."""
    t0 = time.time(); G = np.load(os.path.join(out_track, 'grow_status.npz')); st = G['status']; pos = G['pos'] - np.array(origin_zx, np.float64); ys = G['ys']; ver = G['identity_verified']; clean = G['clean']; dA = G['dA']; dB = G['dB']; blk = np.load(block_path, mmap_mode='r'); R, U = ver.shape
    OFF = np.arange(-8, 9); T = np.zeros((17, R, U), np.uint8); g5n = g5d = 0; peaks0 = 0; peaksn = 0; colcount = {}
    for i in range(R):
        y = int(ys[i]); sec = np.asarray(blk[y]).astype(np.float32); C = pos[i, 0]; t_, n_ = ord3.frame(C, P['sigma_u']); v = ver[i]
        if v.sum() == 0: continue
        pts = C[v][:, None, :] + OFF[None, :, None] * n_[v][:, None, :]; vals = ndi.map_coordinates(sec, [pts[..., 0].ravel(), pts[..., 1].ravel()], order=1, mode='nearest').reshape(pts.shape[:2]); T[:, i, v] = np.clip(vals.T, 0, 255).astype(np.uint8)
        c = vals[:, 8]; g5n += int(((c > vals[:, 2]) & (c > vals[:, 14])).sum()); g5d += int(len(c))
        for L, dd in ((1, dA[i]), (2, dB[i])):                                                                       # V6: peaks between T and the twin along n on the raw section
            ok = v & np.isfinite(dd)
            for u in np.nonzero(ok)[0][::4]:
                d = float(dd[u]); n_s = int(abs(d)) - 6
                if n_s < 4: continue
                tt = np.sign(d) * np.arange(3, 3 + n_s); q = C[u][None, :] + tt[:, None] * n_[u][None, :]; prof = ndi.map_coordinates(sec, [q[:, 0], q[:, 1]], order=1, mode='nearest'); mad = np.median(np.abs(prof - np.median(prof))) + 1e-6
                pk, _ = find_peaks(prof, prominence=3 * mad); peaks0 += int(len(pk) == 0); peaksn += 1; colcount.setdefault((L, u), []).append(len(pk))
    changes = sum(1 for v in colcount.values() if len(set(v)) > 1); ncols = len(colcount)
    cen = T[8].astype(np.float32); valid = cen > 0; coh_med = None; orient = None
    if valid.sum() > 1000:
        th, coh, _ = st_eigen(st_accumulate([ndi.gaussian_filter(cen / 255.0, 1.0)], 1.0), 4.0); coh = np.asarray(coh, np.float32); coh_med = float(np.median(coh[valid]))
        ang = np.degrees(np.asarray(th, np.float32)); colmed = []; 
        for u in range(0, U, 8):
            m = valid[:, u]
            if m.sum() >= 20: colmed.append(np.median(ang[m, u]))
        colmed = np.array(colmed); orient = float((np.abs(((colmed - np.median(colmed)) + 90) % 180 - 90) <= 20).mean()) if len(colmed) else None
    np.savez_compressed(os.path.join(out_track, 'render_block.npz'), T=T, OFF=OFF, ys=ys)
    try:
        from PIL import Image; Image.fromarray(T[8]).save(os.path.join(out_track, 'centre_block.png'))
    except Exception: pass
    inc = G['inc'][:, 0].astype(np.float32); anch = st[:, 0] == ord3.ANCHORED; s_ = G['s'][:, 0].astype(np.float32); ny = np.abs(s_) / np.sqrt(1 + s_ ** 2)
    res = {'V9_G5_centre_gt_pm6_frac': round(g5n / max(1, g5d), 4), 'V9_n_cells': g5d, 'V9_fibre_coherence_median': coh_med, 'V9_orientation_consistency_cols_within_20deg': orient, 'V6_frac_zero_peaks_between_T_and_twin': round(peaks0 / max(1, peaksn), 4), 'V6_n_rays': peaksn, 'V6_columns_with_count_change': changes, 'V6_columns': ncols,
           'V8_increment_abs_p50_p90_p99': [round(float(v), 2) for v in np.percentile(np.abs(inc[anch]), [50, 90, 99])] if anch.any() else None, 'V8_abs_ny_p10_50_90': [round(float(v), 3) for v in np.percentile(ny[anch], [10, 50, 90])] if anch.any() else None, 'secs': round(time.time() - t0, 1)}
    md = os.path.join(out_track, 'mesh_checks')
    try:
        r = subprocess.run([PY, os.path.join(HERE, 'mesh_checks.py'), 'check', os.path.join(out_track, 'surface_tifxyz'), md], capture_output=True, text=True, timeout=900, cwd=REPO); cand = [os.path.join(md, f) for f in os.listdir(md) if f.endswith('.json')] if os.path.isdir(md) else []
        m = json.load(open(cand[0])) if cand else {'error': (r.stdout + r.stderr)[-500:]}; res['V9_mesh'] = {k: m.get(k) for k in ('n_vertices', 'n_triangles', 'self_intersection', 'stretch_arclength_uv') if k in m} if 'error' not in m else m
    except Exception as e: res['V9_mesh'] = {'error': str(e)}
    return res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('params'); ap.add_argument('out'); ap.add_argument('--block_dir', default='/dev/shm/ord3'); ap.add_argument('--seed_npz', required=True); ap.add_argument('--seed_y', type=int, default=5820); ap.add_argument('--threads', type=int, default=3); ap.add_argument('--only', default='track,hops,bars')
    a = ap.parse_args(); P = json.load(open(a.params)); out = a.out; os.makedirs(out, exist_ok=True); T0 = time.time(); only = set(a.only.split(',')); fetch = json.load(open(os.path.join(a.block_dir, 'fetch.json'))); origin = (fetch['z'][0], fetch['x'][0]); y0 = fetch['y'][0]; Y = fetch['shape_yzx'][0]
    rec = {'declaration': ['DECL-E2E-2', 'A1', 'A2', 'A3', 'A4', 'A5'], 'start_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'hashes': {f: sha(os.path.join(HERE, f)) for f in ('ord3.py', 'pilot_ord3b.py', 'ord3_fetch_block.py')}, 'params_sha256': sha(a.params), 'fetch': fetch, 'free_mb_before': subprocess.run(['free', '-m'], capture_output=True, text=True).stdout.split('\n')[1]}
    json.dump(rec, open(os.path.join(out, 'pilotB.json'), 'w'), indent=1, default=J)
    seed = seed_block(a.seed_npz, a.seed_y, origin, P); seed_npy = os.path.join(out, 'seed_block.npy'); np.save(seed_npy, seed); ysb = a.seed_y - y0; rows_neg = min(47, (ysb - 6) // P['dy']); rows_pos = min(48, (Y - 7 - ysb) // P['dy']); d1 = os.path.join(out, 'track'); block = os.path.join(a.block_dir, 'block.npy')
    if 'track' in only:
        t1 = time.time(); env = dict(os.environ, OMP_NUM_THREADS=str(a.threads)); r = subprocess.run([PY, os.path.join(HERE, 'ord3.py'), 'raw', a.params, d1, '--block', block, '--seed_npy', seed_npy, '--seed_y', str(ysb), '--rows', str(rows_neg), str(rows_pos), '--origin', str(origin[0]), str(origin[1])], stdout=open(os.path.join(out, 'track.log'), 'w'), stderr=subprocess.STDOUT, env=env, cwd=REPO)
        rec['track'] = {'returncode': r.returncode, 'wall_s': round(time.time() - t1, 1), 'rows': [int(rows_neg), int(rows_pos)], 'seed_y_block': int(ysb)}
        if r.returncode == 0:
            gc = json.load(open(os.path.join(d1, 'grow_checks.json'))); rec['track']['grow_checks'] = {k: v for k, v in gc.items() if k != 'per_row'}
            rec['track']['per_row_brief'] = [{k2: rr[k2] for k2 in ('tag', 'k', 'y', 'secs', 'rss_gb', 'identity_verified_frac', 'clean_anchored_frac_T', 'swap_merge_cells')} | {'T_anch': rr['T']['anchored_frac'], 'T_dorm': rr['T']['DORMANT'], 'T_br': rr['T']['BRIDGED'], 'T_term': rr['T']['TERMINATED'], 'I4_power': rr['I4']['power'], 'nulls_accept_d4': {k3: v3.get('accept_d4') for k3, v3 in rr['nulls'].items()}, 'nulls_g5': {k3: v3.get('g5_on_M') for k3, v3 in rr['nulls'].items()}, 'twin_jumps': rr.get('twin_jumps')} for rr in gc['per_row']]
            rec['track']['row_secs_median'] = float(np.median([rr['secs'] for rr in gc['per_row']])); rec['track']['rss_gb_peak'] = gc['rss_gb_peak']
        else: rec['track']['log_tail'] = open(os.path.join(out, 'track.log')).read()[-2500:]
        json.dump(rec, open(os.path.join(out, 'pilotB.json'), 'w'), indent=1, default=J); print('track done rc', r.returncode, round(time.time() - t1), 's', flush=True)
    if 'hops' in only:
        os.environ['OMP_NUM_THREADS'] = str(a.threads); rec['V4_hops'] = hops_raw(P, block, seed, ysb, os.path.join(out, 'hops')); json.dump(rec, open(os.path.join(out, 'pilotB.json'), 'w'), indent=1, default=J); print('hops done', rec['V4_hops']['secs'], 's', flush=True)
    if 'bars' in only and os.path.exists(os.path.join(d1, 'grow_status.npz')):
        rec['bars_block'] = render_and_bars(P, block, d1, origin); json.dump(rec, open(os.path.join(out, 'pilotB.json'), 'w'), indent=1, default=J); print('bars done', flush=True)
    # PASS-B (DECL-E2E-2 item 8B, unchanged): V2, V3 (+-0.28 mm and block ends), V4, V5, V6, V7, V9.G5 all pass
    tr = rec.get('track', {}); pr = tr.get('per_row_brief', []); sweep = [r for r in pr if not r['tag']]; mm = 1000.0 / 8.64
    def near(rows, lo_mm, hi_mm): return [r for r in rows if lo_mm <= abs(r['y'] - ysb) * 8.64 / 1000.0 <= hi_mm]
    v2 = None
    if sweep:
        m1 = [r['nulls_accept_d4'].get('T', 0) - r['nulls_accept_d4'].get('C1_between', 0) for r in sweep if r['nulls_accept_d4'].get('C1_between') is not None]; m3 = [r['nulls_accept_d4'].get('T', 0) - r['nulls_accept_d4'].get('C3_random', 0) for r in sweep if r['nulls_accept_d4'].get('C3_random') is not None]; g = [r['nulls_g5'].get('T', 0) - r['nulls_g5'].get('C1_between', 0) for r in sweep if r['nulls_g5'].get('C1_between') is not None]
        v2 = {'anch_T_minus_C1_median': round(float(np.median(m1)), 3) if m1 else None, 'anch_T_minus_C3_median': round(float(np.median(m3)), 3) if m3 else None, 'g5_T_minus_C1_median': round(float(np.median(g)), 3) if g else None}; v2['pass'] = bool(m1 and m3 and g and np.median(m1) >= 0.30 and np.median(m3) >= 0.30 and np.median(g) >= 0.10)
    v3 = None
    if sweep:
        c028 = [r['clean_anchored_frac_T'] for r in near(sweep, 0, 0.28)]; c11 = [r['clean_anchored_frac_T'] for r in near(sweep, 0, 1.1)]; cend = [r['clean_anchored_frac_T'] for r in sweep if abs(r['y'] - ysb) >= 180]
        v3 = {'clean_anchored_min_within_0.28mm': round(min(c028), 4) if c028 else None, 'clean_anchored_min_within_1.1mm': round(min(c11), 4) if c11 else None, 'clean_anchored_min_block_ends': round(min(cend), 4) if cend else None, 'seed_row_anchored': sweep[0]['T_anch'] if sweep else None}
        v3['pass_0.28mm_ge_0.80'] = bool(c028 and min(c028) >= 0.80); v3['pass_1.1mm_ge_0.50'] = bool(c11 and min(c11) >= 0.50); v3['pass_ends_ge_0.30'] = bool(cend and min(cend) >= 0.30)
    v4 = rec.get('V4_hops', {}); v5 = {'frac_rows_power_ge_0.8': round(float(np.mean([(r['I4_power'] or 0) >= 0.8 for r in sweep[1:]])), 3) if len(sweep) > 1 else None}; v5['pass'] = bool(v5['frac_rows_power_ge_0.8'] is not None and v5['frac_rows_power_ge_0.8'] >= 0.80)
    bb = rec.get('bars_block', {}); v6 = {'frac_zero_peaks': bb.get('V6_frac_zero_peaks_between_T_and_twin'), 'count_changes': bb.get('V6_columns_with_count_change'), 'pass': bool(bb.get('V6_frac_zero_peaks') is not None and bb['V6_frac_zero_peaks_between_T_and_twin'] >= 0.98 and bb.get('V6_columns_with_count_change', 1) == 0)}
    v9 = {'G5': bb.get('V9_G5_centre_gt_pm6_frac'), 'pass_G5_ge_0.90': bool(bb.get('V9_G5_centre_gt_pm6_frac') is not None and bb['V9_G5_centre_gt_pm6_frac'] >= 0.90), 'coherence_median': bb.get('V9_fibre_coherence_median'), 'orientation_consistency': bb.get('V9_orientation_consistency_cols_within_20deg')}
    rec['PASS_B'] = {'V2': v2, 'V3': v3, 'V4': {k: v4.get(k) for k in ('detection_rate_ge50pct', 'detection_rate_flag_only', 'control_false_alarm_rate_ge50pct')} | {'pass': bool(v4.get('detection_rate_ge50pct') is not None and v4['detection_rate_ge50pct'] >= 0.90 and v4.get('control_false_alarm_rate_ge50pct') is not None and v4['control_false_alarm_rate_ge50pct'] <= 0.10)}, 'V5': v5, 'V6': v6, 'V7': 'not run (clearance needs the S3 volume; recorded as not run)', 'V9': v9}
    rec['PASS_B']['pass'] = bool(v2 and v2['pass'] and v3 and v3['pass_0.28mm_ge_0.80'] and v3['pass_ends_ge_0.30'] and rec['PASS_B']['V4']['pass'] and v5['pass'] and v6['pass'] and v9['pass_G5_ge_0.90']) and False   # V7 not run: PASS-B cannot be declared passed in this run
    rec['PASS_B']['note'] = 'V7 (clearance) not run in this pilot: PASS-B is reported as false whatever the other bars show; every other bar carries its number'
    rec['wall_min_total'] = round((time.time() - T0) / 60, 2); rec['end_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()); rec['rss_gb_main'] = round(ord3.rss_gb(), 2); json.dump(rec, open(os.path.join(out, 'pilotB.json'), 'w'), indent=1, default=J); print(json.dumps(rec['PASS_B'], default=J)[:1500], 'wall', rec['wall_min_total'], 'min')

if __name__ == '__main__': main()
