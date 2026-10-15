# Provenance: Project HERCULES | owner the owner | [id removed]
"""Candidate-window statistics on the official 2.401 um reference ink maps (task step 4).
Numbers only: no image is written or displayed; no ink model is run.
Per segment: the reference map (uint8, 2.401 um mesh canvas = 20 px per mesh grid cell) is reduced to
per-cell counts (20 x 20 px). Windows are 417 x 417 cells (8340 px = 2.002 cm at 2.401 um/px nominal),
stride 208 cells (~1 cm). Per window: mesh-valid fraction, ink fraction (px >= T of valid px, T = 150 primary,
128 reported), spread = fraction of the window's ~1 mm blocks (21 x 21 cells) with >= 5 % ink px.
Dense window (primary): valid >= 0.90 and ink >= 0.05 and spread >= 0.25. Reported grid of other bars.
Per papyrus unit: greedy selection by ink fraction of windows that do not overlap an accepted window
in 3-D (>= 10 % of a window's mesh points within 10 2.4-um vox of the other window's points)."""
import json, os, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/user/dominion/src')
from hercules.geometry.tifxyz import read_tifxyz, valid_mask

DATA = '/work/reg0009b/data'
OUT = '/home/user/dominion/logs/sib/reg0009b'
WIN, STR, BLK = 417, 208, 21
units = json.load(open(f'{OUT}/overlap_frame9.json'))['units']


def seg_stats(seg):
    sid = seg.split('-')[0]
    m = read_tifxyz(f'{DATA}/{seg}/mesh/{sid}-on-20250820154339-2.401um.tifxyz')
    P = m.points.astype(np.float64); V = valid_mask(P)
    H, W = V.shape
    f = [x for x in os.listdir(f'{DATA}/{seg}/ink-detection') if x.endswith('.tif')][0]
    ink = tifffile.imread(f'{DATA}/{seg}/ink-detection/{f}')
    assert ink.shape == (H * 20, W * 20), (ink.shape, H, W)
    c150 = (ink >= 150).reshape(H, 20, W, 20).sum((1, 3)).astype(np.int32)
    c128 = (ink >= 128).reshape(H, 20, W, 20).sum((1, 3)).astype(np.int32)
    nz = (ink > 0).reshape(H, 20, W, 20).sum((1, 3))
    hist = np.bincount(ink.ravel(), minlength=256)
    del ink
    c150[~V] = 0; c128[~V] = 0
    # physical scale of the canvas: mean mesh edge (vox) / 20 px
    du = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[V[:, 1:] & V[:, :-1]]
    dv = np.linalg.norm(P[1:] - P[:-1], axis=-1)[V[1:] & V[:-1]]
    info = dict(segment=seg, grid=[H, W], canvas_px=[H * 20, W * 20], valid_cells=int(V.sum()),
                valid_area_cm2=float(V.sum() * 400 * (2.401e-4) ** 2),
                edge_u_vox_median=float(np.median(du)), edge_v_vox_median=float(np.median(dv)),
                ink_nonzero_px_outside_valid=int(nz[~V].sum()), ink_px_ge150=int(c150.sum()), ink_px_ge128=int(c128.sum()),
                ink_hist_deciles=[int(np.searchsorted(np.cumsum(hist), q * hist.sum())) for q in np.linspace(0.1, 0.9, 9)])
    wins = []
    for r0 in range(0, max(H - WIN, 0) + 1, STR):
        for c0 in range(0, max(W - WIN, 0) + 1, STR):
            v = V[r0:r0 + WIN, c0:c0 + WIN]
            if v.shape != (WIN, WIN): continue
            vf = v.mean()
            if vf < 0.5: continue
            npx = v.sum() * 400
            a = c150[r0:r0 + WIN, c0:c0 + WIN]; b = c128[r0:r0 + WIN, c0:c0 + WIN]
            nb = WIN // BLK
            blk = a[:nb * BLK, :nb * BLK].reshape(nb, BLK, nb, BLK).sum((1, 3))
            bv = v[:nb * BLK, :nb * BLK].reshape(nb, BLK, nb, BLK).sum((1, 3))
            ok = bv >= 0.5 * BLK * BLK
            spread = float(((blk[ok] / (bv[ok] * 400.0)) >= 0.05).mean()) if ok.any() else 0.0
            wins.append(dict(r0=r0, c0=c0, valid=round(float(vf), 4), ink150=round(float(a.sum() / npx), 5),
                             ink128=round(float(b.sum() / npx), 5), spread=round(spread, 4),
                             canvas2_px=[c0 * 20, r0 * 20, (c0 + WIN) * 20, (r0 + WIN) * 20]))
    return info, wins, P, V


def dense(w, thr=(0.90, 0.05, 0.25)):
    return w['valid'] >= thr[0] and w['ink150'] >= thr[1] and w['spread'] >= thr[2]


res = dict(params=dict(win_cells=WIN, win_px=WIN * 20, win_cm_nominal=WIN * 20 * 2.401e-4, stride_cells=STR,
                       block_cells=BLK, primary=dict(valid=0.90, ink150=0.05, spread=0.25)), segments={}, units=[])
pts = {}
for u in units:
    for s in u['segments']:
        info, wins, P, V = seg_stats(s)
        info['n_windows_valid50'] = len(wins)
        grid = {}
        for vt in (0.75, 0.90):
            for it in (0.02, 0.05, 0.10):
                for st in (0.0, 0.25, 0.5):
                    grid[f'v{vt}_i{it}_s{st}'] = sum(dense(w, (vt, it, st)) for w in wins)
        info['counts_grid'] = grid
        info['n_dense_primary'] = sum(dense(w) for w in wins)
        res['segments'][s] = dict(info=info, windows=wins)
        pts[s] = (P, V)
        print(s[:14], info['n_windows_valid50'], info['n_dense_primary'], round(info['valid_area_cm2'], 2), flush=True)

for u in units:
    cand = []
    for s in u['segments']:
        for k, w in enumerate(res['segments'][s]['windows']):
            if dense(w): cand.append((w['ink150'], s, k))
    cand.sort(reverse=True)
    acc, clouds = [], []
    for ink, s, k in cand:
        w = res['segments'][s]['windows'][k]; P, V = pts[s]
        sub = P[w['r0']:w['r0'] + WIN:4, w['c0']:w['c0'] + WIN:4]; sv = V[w['r0']:w['r0'] + WIN:4, w['c0']:w['c0'] + WIN:4]
        c = sub[sv]
        clash = False
        for c2, t2 in clouds:
            d = t2.query(c, k=1, distance_upper_bound=10.0)[0]
            if np.isfinite(d).mean() >= 0.10: clash = True; break
        if not clash:
            acc.append(dict(segment=s, window_index=k, ink150=ink, spread=w['spread'], canvas2_px=w['canvas2_px']))
            clouds.append((c, cKDTree(c)))
    res['units'].append(dict(unit=u['unit'], segments=u['segments'], n_dense_candidates=len(cand),
                             n_dense_nonoverlapping_3d=len(acc), accepted=acc,
                             valid_area_cm2_sum=round(sum(res['segments'][s]['info']['valid_area_cm2'] for s in u['segments']), 3)))
    print(u['unit'], len(u['segments']), len(cand), len(acc), flush=True)
json.dump(res, open(f'{OUT}/windows.json', 'w'), indent=1)
