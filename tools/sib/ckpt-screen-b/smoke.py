#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic smoke tests for infer_1667.py (numbers only; synthetic arrays, no CT data, no image viewed).

T1 resampler: a linear ramp render r = az + by + cx must come out of SpecGrid.tile as the analytic ramp at the
   mapped coordinates (max abs error, interior tiles).
T2 tiling:    card_tiling on a (512,512) grid whose fmask admits exactly the top-left 256 tile must equal the
   direct official call sigmoid(model(x)) upsampled x4 (max abs diff).
T3 end to end per checkpoint (native and spec), both directions: shapes, valid coverage, determinism (sha of a
   second native forward run), forward != reverse, zero output outside fmask, seconds per tile.
Writes logs/sib/ckpt-screen-b/smoke.json.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import infer_1667 as I  # noqa: E402

OUT = '/work/smoke'


def synth_render(seed, Z=31, H=160, W=160, hole=True):
    """Seeded smooth noise, mean ~ 64 (normalised mean ~0.25, the training scale), a zero block as a hole."""
    import cv2
    rng = np.random.default_rng(seed)
    v = rng.normal(0, 1, (Z, H, W)).astype(np.float32)
    v = np.stack([cv2.GaussianBlur(s, (0, 0), 2.0) for s in v])
    v = 64 + 40 * v / (v.std() + 1e-6)
    v = np.clip(np.rint(v), 1, 255).astype(np.uint8)
    if hole:
        v[:, :24, :24] = 0
    return v


def t1():
    Z, H, W = 31, 200, 200
    zz, yy, xx = np.meshgrid(np.arange(Z), np.arange(H), np.arange(W), indexing='ij')
    a, b, c = 0.7, 0.9, 0.4
    r = (a * zz + b * yy + c * xx).astype(np.float32)   # float render for exactness (tile() casts to float32)
    out = {}
    for d in ('forward', 'reverse'):
        g = I.SpecGrid(r, 15, 2.399, 9.362, d)
        errs = []
        for (y, x) in [(128, 128), (384, 128), (128, 384), (512, 512)]:
            t = g.tile(y, x)
            ry = g.coords(y, I.WINDOW, H)[:, None, None]
            rx = g.coords(x, I.WINDOW, W)[None, :, None]
            z = (g.z0 + g.wz)[None, None, :]
            ref = a * z + b * ry + c * rx
            errs.append(float(np.abs(t - ref).max()))
        out[d] = dict(max_abs_err=max(errs), zpos_first_last=[float(g.zpos[0]), float(g.zpos[-1])],
                      zoom=g.f, model_grid=[g.Hm, g.Wm])
    return out


def t2(model):
    import torch
    import torch.nn.functional as F
    rng = np.random.default_rng(7)
    img = rng.integers(0, 256, (512, 512, 62), dtype=np.uint8)
    fm = np.zeros((512, 512), np.uint8)
    fm[:256, :256] = 1
    pred, cnt = I.card_tiling(model, 512, 512, fm, lambda y, x: img[y:y + 256, x:x + 256], I.train_norm)
    x = torch.from_numpy(img[:256, :256]).permute(2, 0, 1)[None, None].float().clamp(0, 200) / 255
    with torch.no_grad():
        p = F.interpolate(torch.sigmoid(model(x).logits), scale_factor=4, mode='bilinear').squeeze().numpy()
    return dict(tiles_run=int((cnt > 0).any() and cnt.max()), max_abs_diff=float(np.abs(pred[:256, :256] - p).max()),
                outside_zero=bool((pred[256:] == 0).all() and (pred[:, 256:] == 0).all()))


def t3(it):
    os.makedirs(OUT, exist_ok=True)
    rp = f'{OUT}/render_native.npy'
    rs = f'{OUT}/render_spec.npy'
    if not os.path.exists(rp):
        np.save(rp, synth_render(1, H=400, W=400))
        np.save(rs, synth_render(2, H=200, W=200))
    res = {}
    for mode, path in (('native', rp), ('spec', rs)):
        o = f'{OUT}/it{it}_{mode}/map.tif'
        rec = I.main(['--iteration', str(it), '--render', path, '--out', o, '--mode', mode, '--threads', '4',
                      '--record', f'{OUT}/it{it}_{mode}/rec.json'])
        f, r = rec['outputs']['forward'], rec['outputs']['reverse']
        import tifffile
        mf = tifffile.imread(f['path'])
        render = np.load(path)
        valid = (render != 0).any(0)
        res[mode] = dict(render_shape=rec['render']['shape'], map_shape=list(mf.shape), map_dtype=str(mf.dtype),
                         tiles=f['tiles'], seconds_per_tile=f['seconds_per_tile'],
                         covered_frac_of_valid=f['covered_frac_of_valid'],
                         zero_where_uncovered=bool((mf[~valid] == 0).all()),
                         fwd_mean=f['map_mean'], rev_mean=r['map_mean'], fwd_sha=f['map_sha256'],
                         rev_sha=r['map_sha256'], fwd_ne_rev=f['map_sha256'] != r['map_sha256'],
                         model_grid_hw=f.get('model_grid_hw'), wrapper_sha256=rec['wrapper_sha256'],
                         checkpoint=rec['checkpoint'])
        if mode == 'native':
            rec2 = I.main(['--iteration', str(it), '--render', path, '--out', f'{OUT}/it{it}_{mode}/again.tif',
                           '--mode', mode, '--direction', 'forward', '--threads', '4'])
            res[mode]['deterministic'] = rec2['outputs']['forward']['map_sha256'] == f['map_sha256']
    return res


def main():
    its = [int(a) for a in sys.argv[1:]] or list(range(6))
    rep = dict(provenance=I.PROV, start_utc=I.utc(), wrapper_sha256=I.sha256(os.path.join(HERE, 'infer_1667.py')),
               smoke_sha256=I.sha256(os.path.abspath(__file__)), T1_resampler=t1())
    print(json.dumps(rep['T1_resampler']), flush=True)
    model, _ = I.load_model(its[0])
    import torch
    torch.set_num_threads(4)
    rep['T2_tiling_vs_direct'] = t2(model)
    print(json.dumps(rep['T2_tiling_vs_direct']), flush=True)
    del model
    rep['T3'] = {}
    for it in its:
        t = time.time()
        rep['T3'][f'iteration-{it}'] = t3(it)
        print(it, round(time.time() - t, 1), flush=True)
    rep['end_utc'] = I.utc()
    p = os.path.join(I.REPO, 'logs/sib/ckpt-screen-b/smoke.json')
    json.dump(rep, open(p, 'w'), indent=1)
    print('wrote', p)


if __name__ == '__main__':
    main()
