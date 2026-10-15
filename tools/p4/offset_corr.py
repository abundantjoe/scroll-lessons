# Provenance: Project HERCULES | [id removed]
"""DECL-P4-26-A2 item 5 as made exact by DECL-P4-26-A2-A1: the OFFSET-CORR informativeness test of the verso
(offset) channel on w010-027. Numbers only: maps are decoded to arrays and correlated; nothing is displayed.

usage: offset_corr.py <verso_tiles_dir> <forward_tiles_dir> <facing_dir> <out.json> [n_draws]
  verso/forward dirs hold staged <seg>_r{r}_c{c}.png maps (1068 x 1068 u8); facing_dir holds p4-core
  facing_all r{r}_c{c}.npz ('outer'/'inner': 32 x 32 x 2 facing canvas row/col, NaN where none)."""
import glob, hashlib, json, os, sys
import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import mannwhitneyu

SEG = '20260701183124-w010-027'
T, P, NR, NC = 8343, 1068, 9, 21
S = P / T
TEXT = [(r, c) for r in (0, 1) for c in range(9, 14)]
MIN_PX = 20000
SEEDS = {'outer': 26201, 'inner': 26202}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load_tiles(d):
    out = {}
    for p in sorted(glob.glob(os.path.join(d, f'{SEG}_r*_c*.png'))):
        r, c = (int(x) for x in os.path.basename(p)[len(SEG) + 2:-4].split('_c'))
        a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        assert a is not None and a.shape == (P, P) and a.dtype == np.uint8, p
        out[(r, c)] = (a, sha(p))
    return out


def valid(a):
    return (a != 0) & (a != 91)


def mosaic(F):
    M = np.zeros((NR * P, NC * P), np.uint8)
    for (r, c), (a, _) in F.items():
        M[r * P:(r + 1) * P, c * P:(c + 1) * P] = a
    txt = np.zeros(M.shape, np.uint8)
    for r, c in TEXT:
        txt[r * P:(r + 1) * P, c * P:(c + 1) * P] = 1
    return M.astype(np.float32), valid(M).astype(np.float32), txt


def upsample(field):
    """32x32x2 canvas (row, col) -> per-pixel mosaic coords (map_x, map_y) and pixel validity (nearest cell finite)."""
    ok = np.all(np.isfinite(field), -1)
    if not ok.any():
        return None
    idx = distance_transform_edt(~ok, return_distances=False, return_indices=True)
    f = field[idx[0], idx[1]]
    fr = cv2.resize(np.ascontiguousarray(f[..., 0]), (P, P), interpolation=cv2.INTER_LINEAR)
    fc = cv2.resize(np.ascontiguousarray(f[..., 1]), (P, P), interpolation=cv2.INTER_LINEAR)
    pv = cv2.resize(ok.astype(np.uint8), (P, P), interpolation=cv2.INTER_NEAREST).astype(bool)
    return (fc * S - 0.5).astype(np.float32), (fr * S - 0.5).astype(np.float32), pv, field, ok


def pearson(x, y):
    x = x - x.mean(); y = y - y.mean()
    d = np.sqrt((x * x).sum() * (y * y).sum())
    return float((x * y).sum() / d) if d > 0 else float('nan')


def touches_text(field, ok, dy, dx):
    """Cheap pre-check on the 32x32 cells: does any shifted facing cell fall within one cell of the text set?"""
    rr = (field[..., 0][ok] + dy) / T
    cc = (field[..., 1][ok] + dx) / T
    m = 1.0 / 32
    return bool(np.any((rr > -m) & (rr < 2 + m) & (cc > 9 - m) & (cc < 14 + m)))


def pair_r(v, U, Mf, Mv, Mt, dy, dx):
    mx, my, pv, field, ok = U
    sx, sy = mx + np.float32(dx * S), my + np.float32(dy * S)
    f = cv2.remap(Mf, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    fv = cv2.remap(Mv, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0.999
    ft = cv2.remap(Mt, sx, sy, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(bool)
    m = valid(v) & pv & fv & ft
    n = int(m.sum())
    return (pearson(v[m].astype(np.float64), f[m].astype(np.float64)), n) if n >= MIN_PX else (None, n)


def run(V, Mf, Mv, Mt, fields, direction, n_draws):
    U = {}
    for L in V:
        if L in fields and direction in fields[L]:
            u = upsample(fields[L][direction])
            if u is not None:
                U[L] = u
    obs = {}
    for L, u in U.items():
        if touches_text(u[3], u[4], 0, 0):
            r, n = pair_r(V[L][0], u, Mf, Mv, Mt, 0, 0)
            if r is not None and np.isfinite(r):
                obs[L] = (r, n)
    rng = np.random.default_rng(SEEDS[direction])
    medians, pooled, rejected, redrawn, draws = [], [], 0, 0, []
    while len(medians) < n_draws:
        dy, dx = rng.uniform(-2 * T, 2 * T), rng.uniform(-5 * T, 5 * T)
        if max(abs(dy), abs(dx)) < T:
            rejected += 1
            continue
        rs = []
        for L, u in U.items():
            if touches_text(u[3], u[4], dy, dx):
                r, n = pair_r(V[L][0], u, Mf, Mv, Mt, dy, dx)
                if r is not None and np.isfinite(r):
                    rs.append(r)
        if not rs:
            redrawn += 1
            continue
        medians.append(float(np.median(rs))); pooled += rs; draws.append([round(dy, 1), round(dx, 1), len(rs)])
    ro = [v[0] for v in obs.values()]
    res = {'n_tiles_with_field': len(U), 'n_pairs': len(ro),
           'pairs': {f'r{L[0]}_c{L[1]}': {'r': round(v[0], 5), 'n_px': v[1]} for L, v in sorted(obs.items())},
           'median_r_obs': float(np.median(ro)) if ro else None,
           'null': {'draws': n_draws, 'p95_of_medians': float(np.percentile(medians, 95)), 'median_of_medians': float(np.median(medians)),
                    'n_pooled': len(pooled), 'rejected_small_shift': rejected, 'redrawn_no_pair': redrawn, 'seed': SEEDS[direction]},
           'draw_shifts': draws}
    if len(ro) < 3:
        res.update(verdict='UNTESTABLE', mw_p=None)
    else:
        u, p = mannwhitneyu(ro, pooled, alternative='greater')
        res.update(mw_U=float(u), mw_p=float(p),
                   verdict='INFORMATIVE' if (res['median_r_obs'] > res['null']['p95_of_medians'] and p < 0.01) else 'NOT_INFORMATIVE')
    return res


def main(vd, fd, gd, out, n_draws=200):
    n_draws = int(n_draws)
    V, F = load_tiles(vd), load_tiles(fd)
    Mf, Mv, Mt = mosaic(F)
    fields, fsha = {}, {}
    for p in sorted(glob.glob(os.path.join(gd, 'r*_c*.npz'))):
        r, c = (int(x) for x in os.path.basename(p)[1:-4].split('_c'))
        z = np.load(p); fields[(r, c)] = {k: z[k].astype(np.float64) for k in ('outer', 'inner') if k in z}; fsha[f'r{r}_c{c}'] = sha(p)
    rec = {'rule': 'DECL-P4-26-A2 item 5 + DECL-P4-26-A2-A1', 'code_sha256': sha(os.path.abspath(__file__)),
           'n_verso': len(V), 'n_forward': len(F), 'n_facing': len(fields),
           'inputs_sha256': {'verso': {f'r{r}_c{c}': s for (r, c), (_, s) in sorted(V.items())},
                             'forward': {f'r{r}_c{c}': s for (r, c), (_, s) in sorted(F.items())}, 'facing': fsha}}
    rec['outer'] = run(V, Mf, Mv, Mt, fields, 'outer', n_draws)
    rec['inner_control'] = run(V, Mf, Mv, Mt, fields, 'inner', n_draws)
    o, i = rec['outer'], rec['inner_control']
    rec['verdict'] = o['verdict']
    if o['verdict'] == 'INFORMATIVE' and i.get('median_r_obs') is not None and i['median_r_obs'] > i['null']['p95_of_medians']:
        rec['verdict_annotation'] = 'not specific (inner control also exceeds its null p95)'
    st = {}
    for L, (v, _) in sorted(V.items()):
        if L in F:
            a = F[L][0]; m = valid(v) & valid(a)
            if m.sum() >= MIN_PX:
                st[f'r{L[0]}_c{L[1]}'] = round(pearson(v[m].astype(np.float64), a[m].astype(np.float64)), 5)
    rec['show_through_r'] = st
    json.dump(rec, open(out, 'w'), indent=1)
    print(json.dumps({'verdict': rec['verdict'], 'annotation': rec.get('verdict_annotation'), 'n_pairs': o['n_pairs'],
                      'median_r_obs': o['median_r_obs'], 'null_p95': o['null']['p95_of_medians'], 'mw_p': o['mw_p'],
                      'inner_median': i['median_r_obs'], 'inner_null_p95': i['null']['p95_of_medians'], 'n_show_through': len(st)}))


if __name__ == '__main__':
    main(*sys.argv[1:])
