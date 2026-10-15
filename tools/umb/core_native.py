#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-2: native-resolution (8.64 um, OME level 0) umbilicus of the flattened roll PHerc0268.
For each sampled y: fetch a 16-section y-slab of the LEFT and RIGHT edge windows (from the mask edge `--depth_mm` into
the stack, full stack height) and a central vertical strip; per section: stripe removal, 2-D structure tensor
(sigma_d 2, sigma_i 8 voxels), director-index maps at R = 0.5 and 1.0 mm on a stride-4 grid; +1/2 plateaus = hairpin
apexes (nested U-turns), -1/2 = lobe boundaries; the apex-depth profile x_apex(z) is V-shaped for nested loops with its
vertex at the innermost winding: z_c = the height of the deepest apex (robust: the median z of the deepest 5 % of apexes
within the main V); the slit = left apex .. right apex at z_c. Crossing balance: layer peaks (prominence >= 3 MAD) counted
above and below z_c along vertical lines of the central strip. Writes <out>/core_native.json.
usage: core_native.py <out_dir> [--src s3://.../0 | --npy phantom.npy --truth phantom.json] [--y 5820 ...] [--n_y 10]
"""
import argparse, json, os, sys, time, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from st_axis import stripe_removal, st_accumulate, st_eigen; from topo_axis import index_map, plateaus
import uturns as UT
VOX = 8.64; mm = 1000.0 / VOX

class L0:
    def __init__(self, key, threads=32):
        import s3fs; self.fs = s3fs.S3FileSystem(anon=True); self.key = key[5:] if key.startswith('s3://') else key; za = json.loads(self.fs.cat_file(self.key + '/.zarray'))
        self.shape, self.chunks, self.sep = za['shape'], za['chunks'], za.get('dimension_separator', '.'); self.ex = ThreadPoolExecutor(threads)
    def slab(self, y0, n, z0, z1, x0, x1):
        """(n, z1-z0, x1-x0) uint8 from level 0, y0..y0+n (sections), threaded chunk fetch keeping only the needed sections."""
        cz, cy, cx = self.chunks; Z, Y, X = self.shape; z1, x1 = min(z1, Z), min(x1, X); out = np.zeros((n, z1 - z0, x1 - x0), np.uint8)
        keys = [(i, j, k) for i in range(z0 // cz, (z1 - 1) // cz + 1) for j in range(y0 // cy, (y0 + n - 1) // cy + 1) for k in range(x0 // cx, (x1 - 1) // cx + 1)]
        def get(ijk):
            i, j, k = ijk
            try: raw = self.fs.cat_file(f'{self.key}/{i}{self.sep}{j}{self.sep}{k}')
            except FileNotFoundError: return ijk, None
            a = np.frombuffer(raw, np.uint8).reshape(cz, cy, cx); ys, ye = max(y0, j * cy) - j * cy, min(y0 + n, (j + 1) * cy) - j * cy; return ijk, a[:, ys:ye, :].copy()
        t0 = time.time(); got = 0
        for b0 in range(0, len(keys), 256):                                                       # batches: bounded number of chunk buffers in flight
            for (i, j, k), a in self.ex.map(get, keys[b0:b0 + 256]):
                if a is None: continue
                got += 1; zs, ze = max(z0, i * cz), min(z1, (i + 1) * cz); xs, xe = max(x0, k * cx), min(x1, (k + 1) * cx); ys = max(y0, j * cy) - y0
                out[ys:ys + a.shape[1], zs - z0:ze - z0, xs - x0:xe - x0] = a[zs - i * cz:ze - i * cz, :, xs - k * cx:xe - k * cx].transpose(1, 0, 2)
        return out, {'chunks': got, 'of': len(keys), 'secs': round(time.time() - t0, 1), 'MB': round(out.nbytes / 1e6)}

def analyse_window(holder, side, p):
    """holder = [stack (n, Z, X) uint8] of one edge window; the list is emptied so the slab can be freed before the operator runs (x increasing into the stack for 'left'; mirrored for 'right')."""
    stack = holder.pop() if isinstance(holder, list) else holder
    if side == 'right': stack = stack[:, :, ::-1]
    n, Z, X = stack.shape; cnt = np.zeros((Z, X), np.uint8)
    for i in range(n): cnt += (stack[i] > 0)
    mask = cnt > n // 2; del cnt                                                                                       # streamed mask (no (n, Z, X) temporary)
    if mask.sum() < 1000: return {'status': 'no mask'}
    J = None; mean_img = np.zeros((Z, X), np.float32)                                  # stream the sections: one float32 section resident at a time (a 10400 x 2800 window is 116 MB per section)
    for i in range(n):
        s_ = stripe_removal(stack[i].astype(np.float32) / 255.0, mask); mean_img += s_ / n
        gx = ndi.gaussian_filter(s_, p['sd'], order=(0, 1)); gy = ndi.gaussian_filter(s_, p['sd'], order=(1, 0)); del s_
        if J is None: J = np.zeros((3,) + gx.shape, np.float32)
        J[0] += gx * gx; J[1] += gx * gy; J[2] += gy * gy; del gx, gy                                                             # in place: no (3, Z, X) temporary
    del stack; th, coh, con = st_eigen(J, p['si']); del J; stride = p['stride']; ths, cos_ = th[::stride, ::stride].copy(), (coh[::stride, ::stride] * mask[::stride, ::stride]).copy(); coh_med = float(np.median(coh[mask])); del th, coh, con
    out = {'status': 'ok', 'coh_median_mask': round(coh_med, 3)}; apex = []
    if p.get('cache'):                                                                   # keep the stride-4 fields for offline re-analysis (no re-fetch)
        os.makedirs(p['cache'], exist_ok=True); np.savez_compressed(os.path.join(p['cache'], f"{p.get('tag','w')}_{side}.npz"), theta=ths.astype(np.float32), coh=cos_.astype(np.float32), mask=mask[::stride, ::stride], img=ndi.uniform_filter(mean_img, stride)[::stride, ::stride].astype(np.float32), img_full=np.clip((mean_img - np.percentile(mean_img[mask], 0.5)) / (np.percentile(mean_img[mask], 99.5) - np.percentile(mean_img[mask], 0.5) + 1e-6) * 254 + 1, 1, 255).astype(np.uint8) * mask, stride=stride)   # 0 = outside the mask; 1..255 = the stripe-removed mean section scaled between its 0.5 and 99.5 percentiles
    for R in (p['radii_mm'] if not p.get('uturns', True) else []):                                  # legacy index-map swarm only without the operator (pass 1)
        idx = index_map(ths, cos_, cos_ > 1e-6, stride, R * mm); P = plateaus(idx, 0.3, 0.75, 2); Nn = plateaus(idx, -0.75, -0.3, 2)
        out[f'n_plus_half_R{R}'] = len(P); out[f'n_minus_half_R{R}'] = len(Nn)
        if R == p['radii_mm'][0]: apex = [(cx * stride, cy * stride) for cx, cy, nc, v in P]; neg = [(cx * stride, cy * stride) for cx, cy, nc, v in Nn]
    if p.get('uturns', True):                                                                   # DECL-UMB-2-A1 item 2: the U-turn operator on the full-resolution mean section
        lo, hi = np.percentile(mean_img[mask], [0.5, 99.5]); imgn = (np.clip((mean_img - lo) / (hi - lo + 1e-6), 0, 1) * mask).astype(np.float32)
        pu = dict(UT.DEFAULTS); pu.update(p.get('ut', {})); out['uturns'] = UT.window_summary(imgn, mask, pu, mm); del imgn
        u = out['uturns']
        if 'zc_mm' in u: out['zc_mm'] = u['zc_mm']; out['apex_depth_mm_at_zc'] = u['apex_depth_mm']; out['nesting_corr_above'] = u['nesting']['above']; out['nesting_corr_below'] = u['nesting']['below']; out['interior_ridges_within_3_pitches'] = u['innermost_interior_px']
        else: out['status'] = 'no innermost U-turn'
    if len(apex) < 5: out['n_apex'] = len(apex); return out
    A = np.array(apex, float); x, z = A[:, 0], A[:, 1]
    # V-profile: smooth the deepest-apex envelope along z (bins of 1 mm), the vertex = the z of the deepest envelope
    zb = (z / (1.0 * mm)).astype(int); env = {}
    for b in np.unique(zb): env[b] = float(np.max(x[zb == b]))
    bz = np.array(sorted(env)); bx = np.array([env[b] for b in bz]); sm = ndi.median_filter(bx, size=5, mode='nearest') if len(bx) >= 5 else bx
    k = int(np.argmax(sm)); zc_mm = float((bz[k] + 0.5)); deep_x = float(sm[k])
    # nesting monotonicity on both sides of the vertex (Spearman sign of envelope vs |z - zc|)
    def mono(sel):
        if sel.sum() < 4: return None
        d = np.abs(bz[sel] + 0.5 - zc_mm); r = np.corrcoef(d, sm[sel])[0, 1]; return round(float(r), 3)
    out.update({'n_apex': int(len(apex)), 'n_neg': int(len(neg)), 'swarm_zc_mm': round(zc_mm, 2), 'swarm_apex_depth_mm_at_zc': round(deep_x / mm, 2), 'swarm_nesting_corr_above': mono(bz + 0.5 < zc_mm), 'swarm_nesting_corr_below': mono(bz + 0.5 > zc_mm),
                'envelope_mm': [[round(float(b + 0.5), 1), round(float(v / mm), 2)] for b, v in zip(bz, sm)], 'apex_xz_mm': [[round(a / mm, 2), round(b / mm, 2)] for a, b in apex], 'neg_xz_mm': [[round(a / mm, 2), round(b / mm, 2)] for a, b in neg]})
    # innermost U-turn interior test: in the section mean, along the ray from the deepest apex into the stack, is there a ridge within 3 pitches?
    img = ndi.gaussian_filter(mean_img, 1.0); za_ = int(round(zc_mm * mm)); xa = int(round(deep_x))
    if 0 <= za_ < Z and 0 <= xa < X:
        prof = img[za_, xa:min(X, xa + int(3 * p['pitch_mm'] * mm))]; mad = np.median(np.abs(prof - np.median(prof))) + 1e-6; pk, _ = find_peaks(prof, prominence=3 * mad, width=3); out['swarm_interior_ridges'] = int(len(pk))
    if 'zc_mm' not in out: out['status'] = out.get('status', 'ok') if out.get('status') != 'ok' else 'no innermost U-turn'
    return out

def crossing_balance(stack, zc_vox, p, n_lines=9):
    n, Z, X = stack.shape; mask = (stack > 0).mean(0) > 0.5; img = np.zeros((Z, X), np.float32)
    for i in range(n): img += stripe_removal(stack[i].astype(np.float32) / 255.0, mask) / n
    img = ndi.gaussian_filter(img, 1.0); rows = []
    for x in np.linspace(X * 0.1, X * 0.9, n_lines).astype(int):
        col = img[:, x]; m = mask[:, x]
        if m.sum() < 100: continue
        mad = np.median(np.abs(col[m] - np.median(col[m]))) + 1e-6; pk, _ = find_peaks(np.where(m, col, 0), prominence=3 * mad, width=3)
        up, dn = int((pk < zc_vox).sum()), int((pk > zc_vox).sum()); rows.append({'x': int(x), 'up': up, 'down': dn})
    bal = [abs(r['up'] - r['down']) <= 1 for r in rows]; return {'rows': rows, 'balanced_frac': round(float(np.mean(bal)), 2) if rows else None, 'mean_total': round(float(np.mean([r['up'] + r['down'] for r in rows])), 1) if rows else None}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--src', default='s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/0'); ap.add_argument('--npy', default=None); ap.add_argument('--truth', default=None)
    ap.add_argument('--y', type=int, nargs='*', default=None); ap.add_argument('--n_y', type=int, default=10); ap.add_argument('--depth_mm', type=float, default=0.0, help='window depth from the mask edge; 0 = to the section mid-x (DECL-UMB-2-A1)'); ap.add_argument('--l3', default='logs/umb/PHerc0268/fields.npz'); ap.add_argument('--sd', type=float, default=2.0); ap.add_argument('--si', type=float, default=8.0); ap.add_argument('--stride', type=int, default=4); ap.add_argument('--radii_mm', type=float, nargs='+', default=[0.5, 1.0]); ap.add_argument('--pitch_mm', type=float, default=0.38); ap.add_argument('--n_sec', type=int, default=16); ap.add_argument('--cache', default='/dev/shm/umb_fields', help='directory for the stride-4 fields per window (offline re-analysis); empty to disable'); ap.add_argument('--no_uturns', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); done_y = set()
    prev = os.path.join(a.out, 'core_native.json')
    if os.path.exists(prev):
        try: done_y = {r['y'] for r in json.load(open(prev)).get('records', [])}
        except Exception: done_y = set()
    p = {'sd': a.sd, 'si': a.si, 'stride': a.stride, 'radii_mm': a.radii_mm, 'pitch_mm': a.pitch_mm, 'cache': a.cache, 'uturns': not a.no_uturns}; recs = [r for r in (json.load(open(prev)).get('records', []) if done_y else [])]
    if done_y: print('resuming: records present for y', sorted(done_y), flush=True)
    if a.npy:
        V = np.load(a.npy, mmap_mode='r'); T = json.load(open(a.truth)) if a.truth else {}; Zs, Ys, Xs = V.shape; ys = a.y or [Ys // 2]
        for y in ys:
            st = np.asarray(V[:, y:y + a.n_sec, :]).transpose(1, 0, 2); m = (st > 0).mean(0) > 0.5; xs = np.nonzero(m.any(0))[0]; xl, xr = int(xs.min()), int(xs.max()); d = int(a.depth_mm * mm) if a.depth_mm > 0 else (xr - xl) // 2 + 100
            L = analyse_window([st[:, :, xl:xl + d].copy()], 'left', p); Rr = analyse_window([st[:, :, max(0, xr - d):xr + 1].copy()], 'right', p); rec = {'y': y, 'left': L, 'right': Rr, 'x_edges': [xl, xr]}
            if L.get('status') == 'ok' and Rr.get('status') == 'ok':
                zc = 0.5 * (L['zc_mm'] + Rr['zc_mm']) * mm; cx = (xl + xr) // 2; rec['crossings'] = crossing_balance(st[:, :, cx - int(2 * mm):cx + int(2 * mm)], zc, p); rec['zc_agree_mm'] = round(abs(L['zc_mm'] - Rr['zc_mm']), 2)
                if T:
                    ax = T.get('axis_y', {}); zt = ax.get(str(y), ax.get(y)); rec['truth_zc_mm'] = round(zt / mm, 2) if zt is not None else None; rec['err_zc_mm'] = round(abs(0.5 * (L['zc_mm'] + Rr['zc_mm']) - zt / mm), 3) if zt is not None else None
                    sec = next((q for q in T.get('sections', []) if q['y'] == y), None)
                    if sec and 'apex_x_mm' in L and 'apex_x_mm' in Rr:                                      # slit ends: window coordinates -> absolute x (the right window is mirrored)
                        xa_l = xl + L['apex_x_mm'] * mm; xa_r = xr - Rr['apex_x_mm'] * mm
                        rec['slit_mm'] = [round(xa_l / mm, 3), round(xa_r / mm, 3)]; rec['truth_slit_mm'] = [round(v / mm, 3) for v in sec['slit']]
                        rec['err_slit_mm'] = [round(abs(xa_l - sec['slit'][0]) / mm, 3), round(abs(xa_r - sec['slit'][1]) / mm, 3)]; rec['err_zc_lr_mm'] = [round(abs(L['zc_mm'] - sec['apex_left'][0] / mm), 3), round(abs(Rr['zc_mm'] - sec['apex_right'][0] / mm), 3)]
            recs.append(rec); print(json.dumps({k: rec[k] for k in rec if k not in ('left', 'right', 'crossings')} | {'L_zc': L.get('zc_mm'), 'R_zc': Rr.get('zc_mm'), 'L_status': L.get('status'), 'R_status': Rr.get('status'), 'L_turns': L.get('uturns', {}).get('n_winding_scale'), 'R_turns': Rr.get('uturns', {}).get('n_winding_scale'), 'cross': rec.get('crossings', {}).get('balanced_frac')}), flush=True)
            json.dump({'vox_um': VOX, 'params': p, 'records': recs}, open(os.path.join(a.out, 'core_native.json'), 'w'), indent=1)
    else:
        src = L0(a.src); Z0 = src.shape[0]
        if os.path.exists(a.l3): F = np.load(a.l3); IM, zmid3 = F['img'], F['z_mid']; s = int(F['stride']) * 8; ysrc = [(IM[i] > 0, float(zmid3[i] * 8)) for i in range(len(zmid3))]
        else:                                                                                         # lanes: the level-4 mask (0.54 GB, one threaded fetch) instead of the level-3 fields
            l4 = '/dev/shm/ct_L4.npy'
            if not os.path.exists(l4): os.system(f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetch_zarr.py')} vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/4 {l4} > /dev/null 2>&1")
            V4 = np.load(l4, mmap_mode='r'); s = 16; ysrc = [(np.asarray(V4[:, j, :]) > 0, float(j * 16 + 8)) for j in range(0, V4.shape[1], 4)]   # (mask in (z, x) at level 4, y at level 0), every 4 level-4 y
        ys = a.y or [int(round(v)) for v in np.linspace(1536, 11136, a.n_y)]
        for y in ys:
            if y in done_y: continue
            i3 = int(np.argmin(np.abs(np.array([q[1] for q in ysrc]) - y))); m3 = ysrc[i3][0]; rows_ok = np.nonzero(m3.sum(1) > 50)[0]
            if len(rows_ok) < 10: recs.append({'y': y, 'status': 'no mask'}); continue
            z3a, z3b = rows_ok.min(), rows_ok.max(); cols = np.nonzero(m3[(z3a + z3b) // 2 - 20:(z3a + z3b) // 2 + 20].mean(0) > 0.3)[0]
            if len(cols) < 10: recs.append({'y': y, 'status': 'no mask row'}); continue
            xl3, xr3 = cols.min(), cols.max()
            z0, z1 = max(0, int(z3a * s) - 400), min(Z0, int((z3b + 1) * s) + 400); xl0, xr0 = int(xl3 * s), int((xr3 + 1) * s); d = int(a.depth_mm * mm) if a.depth_mm > 0 else (xr0 - xl0) // 2 + 600   # 0: to mid-x (+300 margin each side)
            p['tag'] = f'y{y}'; L_st, ft1 = src.slab(y, a.n_sec, z0, z1, max(0, xl0 - 300), xl0 - 300 + d); h = [L_st]; del L_st; L = analyse_window(h, 'left', p); del h
            R_st, ft2 = src.slab(y, a.n_sec, z0, z1, xr0 + 300 - d, min(src.shape[2], xr0 + 300)); h = [R_st]; del R_st; Rr = analyse_window(h, 'right', p); del h
            cx = (xl0 + xr0) // 2; C_st, ft3 = src.slab(y, a.n_sec, z0, z1, cx - int(2 * mm), cx + int(2 * mm)); rec = {'y': y, 'z_window': [z0, z1], 'x_edges_l0': [xl0, xr0], 'x_windows_l0': [[max(0, xl0 - 300), xl0 - 300 + d], [xr0 + 300 - d, min(src.shape[2], xr0 + 300)]], 'fetch': [ft1, ft2, ft3], 'left': L, 'right': Rr}
            if L.get('status') == 'ok' and Rr.get('status') == 'ok':
                zc = 0.5 * (L['zc_mm'] + Rr['zc_mm']) * mm; rec['crossings'] = crossing_balance(C_st, zc, p); rec['zc_agree_mm'] = round(abs(L['zc_mm'] - Rr['zc_mm']), 2)
            recs.append(rec); print(json.dumps({'y': y, 'fetch_s': [f['secs'] for f in rec['fetch']], 'L': {k: L.get(k) for k in ['status', 'zc_mm', 'apex_depth_mm_at_zc', 'nesting_corr_above', 'nesting_corr_below', 'interior_ridges_within_3_pitches']} | {k: L.get('uturns', {}).get(k) for k in ['n_turns', 'n_into_stack', 'n_empty', 'n_deeper_non_empty', 'secs_uturns']}, 'R': {k: Rr.get(k) for k in ['status', 'zc_mm', 'apex_depth_mm_at_zc', 'nesting_corr_above', 'nesting_corr_below', 'interior_ridges_within_3_pitches']} | {k: Rr.get('uturns', {}).get(k) for k in ['n_turns', 'n_into_stack', 'n_empty', 'n_deeper_non_empty', 'secs_uturns']}, 'agree_mm': rec.get('zc_agree_mm'), 'cross': rec.get('crossings', {}).get('balanced_frac')}), flush=True)
            del C_st
            json.dump({'vox_um': VOX, 'params': p, 'records': recs}, open(os.path.join(a.out, 'core_native.json'), 'w'), indent=1)
    json.dump({'vox_um': VOX, 'params': p, 'records': recs}, open(os.path.join(a.out, 'core_native.json'), 'w'), indent=1); open(os.path.join(a.out, 'DONE'), 'w').write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())); print('done', len(recs))

if __name__ == '__main__': main()
