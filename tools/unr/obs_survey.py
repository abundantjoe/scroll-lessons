#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-3 item 1: band-observability survey of PHerc0268 at level 0. No tracking, no seed: at one y and one (z, x) window the 12 raw
sections y-4..y+7 give two 8-section means a 4-section step apart; the survey cells are the gated-ridge centreline pixels of the first
mean; for them the acceptance at Delta 4 in the second mean (T) is compared with between-laminae (C1) and random (C3) positions, with
G5-on-M, the texture Z_same against the twin-swap null, the twin-distance change, the NCC motion lag, and the competitor distances.
usage: obs_survey.py <params.json> <config.json> <out_dir> --y 5820 [--l4 /dev/shm/e2e/ct_L4_PHerc0268.npy] [--windows 3] [--win 2560]
       [--block <local (Y,Z,X) block.npy> --block_origin y0 z0 x0]   (local test on a fetched block instead of S3)"""
import os, sys, json, time, argparse, numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'master')); import ord3
VOX = 8.64
def J(o): return o.item() if hasattr(o, 'item') else str(o)

def windows_at(l4_path, y, n_win, win):
    """Window centres at 30/50/70 % of the level-4 mask's z extent at this y, at the mask's x centre (level-0 coords)."""
    L4 = np.load(l4_path, mmap_mode='r'); y4 = min(L4.shape[1] - 1, y // 16); sec = np.asarray(L4[:, y4, :]) > 0
    if sec.sum() < 100: return [], {'mask_frac': float(sec.mean())}
    zz = np.nonzero(sec.any(1))[0]; z_lo, z_hi = zz.min() * 16, (zz.max() + 1) * 16; fr = np.linspace(0.3, 0.7, n_win) if n_win > 1 else [0.5]; out = []
    for f in fr:
        zc = int(z_lo + f * (z_hi - z_lo)); row = sec[min(sec.shape[0] - 1, zc // 16)]; xx = np.nonzero(row)[0]
        xc = int((xx.min() + xx.max() + 1) * 8) if len(xx) else int(sec.any(0).nonzero()[0].mean() * 16)
        z0 = max(0, (zc - win // 2) // 128 * 128); x0 = max(0, (xc - win // 2) // 128 * 128); out.append((z0, z0 + win, x0, x0 + win))
    return out, {'mask_frac': float(sec.mean()), 'z_extent': [int(z_lo), int(z_hi)]}

def fetch_stack(cfg, y, bb, a):
    if a.block:
        blk = np.load(a.block, mmap_mode='r'); oy, oz, ox = a.block_origin; S = np.asarray(blk[y - 4 - oy:y + 8 - oy, bb[0] - oz:bb[1] - oz, bb[2] - ox:bb[3] - ox]); return S, {'source': 'local block', 'n_missing': None}
    from e2e_sheet import Zarr0; ct = Zarr0(cfg['ct_l0'], 32); t0 = time.time(); B = ct.block(bb[0], bb[1], y - 4, y + 8, bb[2], bb[3]); S = np.ascontiguousarray(np.transpose(B, (1, 0, 2))); del B
    return S, {'source': 's3', 'fetch_s': round(time.time() - t0, 1), 'bytes_nominal': int(S.nbytes)}

def means(S):
    """Stripe-removed, window-scaled uint8 means of sections 0..7 and 4..11 (a 4-section step) and the mask."""
    F = np.empty(S.shape, np.float32)
    for i in range(S.shape[0]):
        c = S[i].astype(np.float32); c[c == 0] = np.nan; med = np.nanmedian(c, 0); med[~np.isfinite(med)] = 0; F[i] = np.where(np.isfinite(c), c - med[None, :], 0)
    mask = S[6] > 0; v = F[:, mask]; lo, hi = np.percentile(v, [0.5, 99.5]) if v.size else (0, 1)
    u8 = lambda M: (np.clip((M - lo) / (hi - lo + 1e-6), 0, 1) * 254 + 1).astype(np.uint8) * mask
    return u8(F[0:8].mean(0)), u8(F[4:12].mean(0)), mask

def survey_window(P, Mk, Mk1, mask, max_cells=20000, grid=4):
    Rs, FZ, FX, coh, void, tau = ord3.gated_fields(Mk, mask, P['fields']); Rs1, FZ1, FX1, coh1, void1, tau1 = ord3.gated_fields(Mk1, mask, P['fields']); Z, X = Mk.shape
    nz, nx = FZ.astype(np.float32), FX.astype(np.float32); zz, xx = np.mgrid[0:Z, 0:X].astype(np.float32)
    up = ndi.map_coordinates(Rs, [zz + nz, xx + nx], order=1, mode='nearest'); dn = ndi.map_coordinates(Rs, [zz - nz, xx - nx], order=1, mode='nearest'); cl = (Rs >= tau) & (Rs >= up) & (Rs >= dn); del up, dn
    g = np.zeros_like(cl); g[::grid, ::grid] = True; cells = np.argwhere(cl & g); rng = np.random.default_rng(0)
    if len(cells) > max_cells: cells = cells[rng.choice(len(cells), max_cells, replace=False)]
    C = cells.astype(np.float64); n = np.stack([nz[cells[:, 0], cells[:, 1]], nx[cells[:, 0], cells[:, 1]]], 1).astype(np.float64); t = np.stack([-n[:, 1], n[:, 0]], 1)
    res = {'tau': float(tau), 'tau_k1': float(tau1), 'n_cells': int(len(C)), 'centreline_density_per_Mpx': round(float(cl.sum()) / (Z * X / 1e6), 1), 'in_mask_frac': float(mask.mean()), 'void_frac': float(void[mask].mean()) if mask.any() else None, 'rs_pos_frac': float((Rs[mask] > 0).mean()) if mask.any() else None}
    if len(C) < 100: res['note'] = 'fewer than 100 survey cells'; return res
    dA, dB = ord3.find_twins(Rs, tau, C, n, P['twins']); fa, fb = np.isfinite(dA), np.isfinite(dB); dcomp = np.minimum(np.abs(np.where(fa, dA, ord3.OPEN)), np.abs(np.where(fb, dB, ord3.OPEN)))
    res.update({'dcomp_p10_25_50': [round(float(v), 1) for v in np.percentile(dcomp, [10, 25, 50])], 'open_frac': {'A': round(float((~fa).mean()), 3), 'B': round(float((~fb).mean()), 3)}, 'dA_p10_50_90': [round(float(v), 1) for v in np.nanpercentile(dA, [10, 50, 90])] if fa.any() else None})
    def accept(F, tau_, pts, nn, D=4):
        V = np.arange(-D, D + 1).astype(np.float64); q = pts[:, None, :] + V[None, :, None] * nn[:, None, :]; r = ord3.sample(F, q) / tau_ * ord3.inside(F.shape, q); lm = (r >= np.roll(r, 1, 1)) & (r >= np.roll(r, -1, 1)) & (r >= 0.5); lm[:, 0] = r[:, 0] >= 0.5; lm[:, -1] = r[:, -1] >= 0.5; return float(lm.any(1).mean())
    def g5(M, pts, nn):
        Mf = M.astype(np.float32); c = ord3.sample(Mf, pts); return float(((c > ord3.sample(Mf, pts + 6 * nn)) & (c > ord3.sample(Mf, pts - 6 * nn))).mean())
    m1 = fa; C1 = C[m1] + 0.5 * dA[m1, None] * n[m1]; zzm, xxm = np.nonzero(mask); i = rng.integers(0, len(zzm), min(len(zzm), max(2000, len(C)))); C3 = np.stack([zzm[i], xxm[i]], 1).astype(np.float64); th = rng.uniform(0, np.pi, len(C3)); n3 = np.stack([np.sin(th), np.cos(th)], 1)
    sets = {'T': (C, n), 'C1_between': (C1, n[m1]), 'C3_random': (C3, n3)}; res['accept_d4_in_Mk1'] = {k: round(accept(Rs1, tau, p, nn), 4) for k, (p, nn) in sets.items()}; res['accept_d4_in_Mk_self'] = round(accept(Rs, tau, C, n), 4)
    res['g5_on_Mk1'] = {k: round(g5(Mk1, p, nn), 4) for k, (p, nn) in sets.items()}; a = res['accept_d4_in_Mk1']; res['margin_T_minus_C1'] = round(a['T'] - a['C1_between'], 4); res['margin_T_minus_C3'] = round(a['T'] - a['C3_random'], 4); res['observable_at_dy4'] = bool(res['margin_T_minus_C1'] >= 0.30 and res['margin_T_minus_C3'] >= 0.30)
    # texture power: Z_same (cell profile in Mk vs Mk1) against the twin-swap null (cell in Mk vs twin position in Mk1)
    half = P['I4']['half']; v0 = ord3.texture(Mk, C, t, half); v1 = ord3.texture(Mk1, C, t, half); zs = ord3.zncc(v0, v1); nullv = []
    for d_, f_ in ((dA, fa), (dB, fb)):
        if f_.sum() >= 20: nullv.append(ord3.zncc(v0[f_], ord3.texture(Mk1, C[f_] + d_[f_, None] * n[f_], t[f_], half)))
    if nullv:
        nullv = np.concatenate(nullv); thr = float(np.percentile(nullv, 95)); res['texture'] = {'null_p95': round(thr, 3), 'zsame_median': round(float(np.median(zs)), 3), 'null_median': round(float(np.median(nullv)), 3), 'power': round(float((zs > thr).mean()), 4)}
    # twin-distance change at the same cells (untracked) and motion lag of the normal profile within +-8
    dA1, dB1 = ord3.find_twins(Rs1, tau, C, n, P['twins']); both = fa & np.isfinite(dA1); res['twin_dA_change_p50_p90'] = [round(float(v), 2) for v in np.percentile(np.abs(dA1[both] - dA[both]), [50, 90])] if both.sum() >= 20 else None
    W = np.arange(-24, 25).astype(np.float64); p0 = ord3.sample(Mk.astype(np.float32), C[:, None, :] + W[None, :, None] * n[:, None, :]); p1 = ord3.sample(Mk1.astype(np.float32), C[:, None, :] + W[None, :, None] * n[:, None, :])
    p0 = (p0 - p0.mean(1, keepdims=True)) / (p0.std(1, keepdims=True) + 1e-6); p1 = (p1 - p1.mean(1, keepdims=True)) / (p1.std(1, keepdims=True) + 1e-6); core = slice(8, 41); lags = np.arange(-8, 9); ncc = np.stack([(p0[:, core] * p1[:, core.start + l:core.stop + l]).mean(1) for l in lags], 1); best = lags[np.argmax(ncc, 1)]
    res['motion_abs_lag_p50_p90'] = [float(np.percentile(np.abs(best), 50)), float(np.percentile(np.abs(best), 90))]; res['motion_frac_gt4'] = round(float((np.abs(best) > 4).mean()), 3)
    return res, (Rs, cl)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('params'); ap.add_argument('config'); ap.add_argument('out'); ap.add_argument('--y', type=int, required=True); ap.add_argument('--l4', default='/dev/shm/e2e/ct_L4_PHerc0268.npy'); ap.add_argument('--windows', type=int, default=3); ap.add_argument('--win', type=int, default=2560); ap.add_argument('--block', default=None); ap.add_argument('--block_origin', type=int, nargs=3, default=None); ap.add_argument('--bbox', type=int, nargs=4, default=None)
    a = ap.parse_args(); P = json.load(open(a.params)); cfg = json.load(open(a.config)); os.makedirs(a.out, exist_ok=True); t0 = time.time()
    if a.bbox: wins, info = [tuple(a.bbox)], {'bbox': 'given'}
    else: wins, info = windows_at(a.l4, a.y, a.windows, a.win)
    for w, bb in enumerate(wins):
        fn = os.path.join(a.out, f'obs_y{a.y}_w{w}.json')
        if os.path.exists(fn): print('exists', fn); continue
        t1 = time.time(); S, finfo = fetch_stack(cfg, a.y, bb, a); Mk, Mk1, mask = means(S); del S; out = survey_window(P, Mk, Mk1, mask)
        if isinstance(out, tuple): res, (Rs, cl) = out
        else: res, cl = out, None
        res.update({'declaration': 'DECL-E2E-3 item 1', 'y': a.y, 'window': w, 'bbox_zx': list(bb), 'fetch': finfo, 'l4_info': info, 'secs': round(time.time() - t1, 1), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}); json.dump(res, open(fn, 'w'), indent=1, default=J)
        try:
            from PIL import Image; im = Image.fromarray(Mk[::4, ::4]).convert('RGB'); arr = np.array(im)
            if cl is not None: arr[cl[::4, ::4]] = (255, 200, 0)
            Image.fromarray(arr).save(os.path.join(a.out, f'obs_y{a.y}_w{w}.png'))
        except Exception: pass
        print(json.dumps({k: res.get(k) for k in ('y', 'window', 'n_cells', 'dcomp_p10_25_50', 'accept_d4_in_Mk1', 'margin_T_minus_C1', 'margin_T_minus_C3', 'observable_at_dy4', 'texture', 'motion_abs_lag_p50_p90', 'secs')}, default=J), flush=True)
    print('done', a.y, round(time.time() - t0, 1), 's')

if __name__ == '__main__': main()
