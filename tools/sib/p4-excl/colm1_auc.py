"""DECL-P4-23 item 6(c): col. -1 (w010-027 r0-r1 c11-c13) pixel AUC of a P4-OWN arm's prediction arrays against the
organizer ink labels, code only (DECL-P4-21-A1). X label values stay in memory; only AUCs and counts are written.

Grid: x4 of the tile (pixel (y, x) = tile px [4y, 4y+4) x [4x, 4x+4)); score = mean of the arm's u8 over the valid px
of the block (block kept if >= 8 of 16 px valid). Labels: same mapping as label_shards.py (exact closest point at strip
vertices, <= 20 vox; segment UV bilinear inside the strip quad; label px round(uv*20); nearest covering segment decides).
AUC = Mann-Whitney with average ranks over label-covered blocks (ink = positive).
usage: colm1_auc.py <arm> <arrays_dir> <ref_desc> <strip_mesh> <grid_json> <struct> <labels> <out>
"""
import sys, os, json, time
import numpy as np, tifffile, zarr
from scipy.stats import rankdata
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from uvmap import nearest_uv
from process import SEGS, PROV, sha

arm, adir, ref, mdir, gjson, sdir, ldir, out = sys.argv[1:9]
TILES = [(0, 11), (0, 12), (0, 13), (1, 11), (1, 12), (1, 13)]
TOL = 20.0; DS = 4; s = 20
t0 = time.time()
T = int(json.load(open(gjson))['T_canvas_px'])
G = np.stack([tifffile.imread(f'{mdir}/{a}.tif') for a in 'xyz'], -1)
V = (G >= 0).all(-1) & np.isfinite(G).all(-1)
Ss = {sg: Surface(np.load(f'{sdir}/{sg}.npz')['grid']) for sg in SEGS}
bb = {sg: (S.V.min(0), S.V.max(0)) for sg, S in Ss.items()}
LZ = {sg: (zarr.open_array(f'{ldir}/{sg}/inklabels.zarr/0', mode='r'), zarr.open_array(f'{ldir}/{sg}/supervision.zarr/0', mode='r')) for sg in SEGS}


def auc(y, sc):
    y = np.asarray(y, bool); npos, nneg = int(y.sum()), int((~y).sum())
    if npos == 0 or nneg == 0:
        return None
    rk = rankdata(sc)
    return float((rk[y].sum() - npos * (npos + 1) / 2) / (npos * nneg))


res = {'provenance': PROV, 'arm': arm, 'what': 'DECL-P4-23 item 6(c) col. -1 pixel AUC vs organizer ink labels (code only, '
       'DECL-P4-21-A1); no X label value written', 'arrays_ref': ref, 'tiles': {}}
Yall, Sall = [], []
for (r, c) in TILES:
    k = f'r{r}_c{c}'; f = f'{adir}/{k}.npz'
    if not os.path.exists(f):
        res['tiles'][k] = {'present': False}; continue
    z = np.load(f); u8, vm = z['u8'], z['valid']
    n = -(-T // DS); pad = n * DS
    U = np.zeros((pad, pad), np.float64); M = np.zeros((pad, pad), np.float64)
    U[:u8.shape[0], :u8.shape[1]] = np.where(vm, u8, 0); M[:vm.shape[0], :vm.shape[1]] = vm
    su = U.reshape(n, DS, n, DS).sum((1, 3)); sm = M.reshape(n, DS, n, DS).sum((1, 3))
    keep = sm >= 8
    score = np.where(keep, su / np.maximum(sm, 1), np.nan)
    yy, xx = np.nonzero(keep)
    gy = (r * T + DS * yy + (DS - 1) / 2) / s; gx = (c * T + DS * xx + (DS - 1) / 2) / s
    ci = np.floor(gy).astype(int); cj = np.floor(gx).astype(int); fy = gy - ci; fx = gx - cj
    inb = (ci + 1 < V.shape[0]) & (cj + 1 < V.shape[1])
    yy, xx, ci, cj, fy, fx = yy[inb], xx[inb], ci[inb], cj[inb], fy[inb], fx[inb]
    i0, i1 = ci.min(), ci.max() + 2; j0, j1 = cj.min(), cj.max() + 2
    sub = V[i0:i1, j0:j1]; vi, vj = np.nonzero(sub); P = G[vi + i0, vj + j0].astype(np.float64)
    lo, hi = P.min(0) - 25, P.max(0) + 25
    best = np.full(len(yy), np.inf); SUP = np.zeros(len(yy), bool); INK = np.zeros(len(yy), bool)
    for sg in SEGS:
        a, b = bb[sg]
        if (a > hi).any() or (b < lo).any():
            continue
        S = Ss[sg]; D = np.full(len(P), np.inf); UVv = np.full((len(P), 2), np.nan)
        for q in range(0, len(P), 100_000):
            d, uv, _ = nearest_uv(S, P[q:q + 100_000], TOL); D[q:q + 100_000] = d; UVv[q:q + 100_000] = uv
        if not np.isfinite(D).any():
            continue
        Dg = np.full(sub.shape, np.inf); Ug = np.full(sub.shape + (2,), np.nan); Dg[vi, vj] = D; Ug[vi, vj] = UVv
        li, lj = ci - i0, cj - j0
        cs = [Dg[li, lj], Dg[li, lj + 1], Dg[li + 1, lj], Dg[li + 1, lj + 1]]
        ok = np.all([np.isfinite(x) for x in cs], 0)
        w = [(1 - fy) * (1 - fx), (1 - fy) * fx, fy * (1 - fx), fy * fx]
        Uq = [Ug[li, lj], Ug[li, lj + 1], Ug[li + 1, lj], Ug[li + 1, lj + 1]]
        Ui = sum(wi[:, None] * u for wi, u in zip(w, Uq)); Dp = sum(wi * d for wi, d in zip(w, cs))
        span = np.maximum(np.abs(Uq[0] - Uq[3]).max(1), np.abs(Uq[1] - Uq[2]).max(1))
        ok &= span < 3.0
        idx = np.nonzero(ok)[0]
        if idx.size == 0:
            continue
        zi, zs = LZ[sg]
        pr = np.clip(np.rint(Ui[idx, 0] * 20).astype(np.int64), 0, zi.shape[0] - 1)
        pc = np.clip(np.rint(Ui[idx, 1] * 20).astype(np.int64), 0, zi.shape[1] - 1)
        r0, c0 = pr.min(), pc.min()
        bs = zs[r0:pr.max() + 1, c0:pc.max() + 1]; sv = bs[pr - r0, pc - c0] == 255; del bs
        bi = zi[r0:pr.max() + 1, c0:pc.max() + 1]; iv = bi[pr - r0, pc - c0] == 255; del bi
        upd = sv & (Dp[idx] < best[idx])
        best[idx[upd]] = Dp[idx[upd]]; SUP[idx[upd]] = True; INK[idx[upd]] = iv[upd]
    sc = score[yy, xx]
    y = INK[SUP]; scs = sc[SUP]
    res['tiles'][k] = {'present': True, 'array_sha256': sha(f), 'n_blocks_valid': int(len(yy)), 'n_blocks_covered': int(SUP.sum()),
                       'coverage_fraction': round(float(SUP.mean()), 6), 'n_ink': int(y.sum()), 'n_noink': int((~y).sum()),
                       'auc': auc(y, scs)}
    Yall.append(y); Sall.append(scs)
    print(k, res['tiles'][k]['auc'], res['tiles'][k]['n_blocks_covered'], round(time.time() - t0), 's', flush=True)
    del y, scs, INK, SUP
if Yall:
    Y = np.concatenate(Yall); Sc = np.concatenate(Sall)
    res['pooled'] = {'n_tiles': len(Yall), 'n_covered': int(len(Y)), 'n_ink': int(Y.sum()), 'auc': auc(Y, Sc)}
res['method'] = {'grid': 'x4 of tile', 'score': 'mean u8 over valid px of the 4x4 block (>= 8 valid)', 'mapping_tolerance_vox': TOL,
                 'labels': 'official 20260918 set, level 0 (sha256 in downloads.jsonl)', 'auc': 'Mann-Whitney, average ranks'}
res['seconds'] = round(time.time() - t0, 1)
json.dump(res, open(out, 'w'), indent=1); print('pooled', res.get('pooled'))
