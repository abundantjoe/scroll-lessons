# Provenance: Project HERCULES | owner the owner | [id removed]
"""Numbers-only checks of the phase-1 smoke maps (synthetic input; no CT): format, invalid-area behaviour,
determinism, precision sensitivity, forward/reverse difference, cost per 2 cm DEV window. Writes smoke_check.json.
Usage: python smoke_check.py SMOKE.npy OUTDIR"""
import glob
import json
import os
import sys

import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screen_infer as S  # noqa: E402

render = np.load(sys.argv[1])
od = sys.argv[2]
valid = np.any(render != 0, axis=0)
DEV_PX = 2136 + 2 * 256  # devloop window (2 cm at 9.362 um) + 256 px render margin per side


def n_tiles(L, tile, stride):
    return len(S._grid_1d(L, tile, stride)) if hasattr(S, '_grid_1d') else None


def grid(L, t, s):
    xs = list(range(0, max(1, L - t + 1), s))
    if not xs or xs[-1] != max(0, L - t):
        xs.append(max(0, L - t))
    return len(xs)


out = {'render_shape': list(render.shape), 'valid_frac': float(valid.mean()), 'dev_window_px': DEV_PX, 'runs': {}}
for rj in sorted(glob.glob(f'{od}/*.run.json')):
    r = json.load(open(rj))
    tag = os.path.basename(rj)[:-9]
    e = dict(ckpt=r['ckpt'], precision=r['precision'], window=r['window'], n_slices=len(r['offsets']),
             wrapper_sha256=r['wrapper_sha256'], missing_keys=len(r['model']['missing_keys']),
             unexpected_keys=len(r['model']['unexpected_keys']), shape_mismatch=len(r['model']['shape_mismatch']),
             n_params=r['model']['n_params'], orders={})
    maps = {}
    for o, v in r['orders'].items():
        m = tifffile.imread(v['path'])
        maps[o] = m
        t = r['spec']['tile']; s = r['spec']['stride']
        tiles_dev = grid(DEV_PX, t, s) ** 2
        rate = v['partition_tiles'] / v['seconds']
        e['orders'][o] = dict(sha256=v['sha256'], dtype=str(m.dtype), ndim=m.ndim, shape_ok=list(m.shape) == list(render.shape[1:]),
                              invalid_all_zero=bool((m[~valid] == 0).all()),
                              valid_mean=float(m[valid].mean()), valid_std=float(m[valid].std()),
                              valid_eq0_frac=float((m[valid] == 0).mean()),
                              seconds=v['seconds'], tiles=v['partition_tiles'], tiles_per_s=round(rate, 3),
                              dev_window_tiles=tiles_dev, dev_window_cpu_min_est=round(tiles_dev / rate / 60, 1))
    if len(maps) == 2:
        d = np.abs(maps['forward'].astype(int) - maps['reverse'].astype(int))[valid]
        e['forward_vs_reverse'] = dict(mean_abs=float(d.mean()), max_abs=int(d.max()),
                                       pearson=float(np.corrcoef(maps['forward'][valid], maps['reverse'][valid])[0, 1]))
    out['runs'][tag] = e


def cmp(a, b):
    ra, rb = json.load(open(f'{od}/{a}.run.json')), json.load(open(f'{od}/{b}.run.json'))
    res = {}
    for o in ra['orders']:
        ma, mb = tifffile.imread(ra['orders'][o]['path']), tifffile.imread(rb['orders'][o]['path'])
        d = np.abs(ma.astype(int) - mb.astype(int))[valid]
        res[o] = dict(identical=bool((ma == mb).all()), mean_abs=float(d.mean()), max_abs=int(d.max()),
                      frac_diff_gt2=float((d > 2).mean()))
    return res


if os.path.exists(f'{od}/gp_fp32_repeat.run.json'):
    out['determinism_gp_fp32_vs_repeat'] = cmp('gp_fp32', 'gp_fp32_repeat')
if os.path.exists(f'{od}/gp_official.run.json'):
    out['precision_gp_fp32_vs_official_cpu_autocast'] = cmp('gp_fp32', 'gp_official')
t = json.dumps(out, indent=1) + '\n'
assert t.isascii()
open(f'{od}/smoke_check.json', 'w').write(t)
print(t)
