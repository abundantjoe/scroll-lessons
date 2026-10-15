# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN CPU timing test (DECL-P4-23 item 4 / step 1), on T input only (w010-027 c0-c8 are T tiles; the region
used is inside tile r4 c2, far from X c9+), with RANDOM labels. Numbers only.
Measures, per candidate architecture: params, train step seconds (batch B, patch P, fwd+bwd+AdamW) and inference
seconds per 1e6 canvas px (fp32, eval, 1024 px windows with 64 px halo); projects arm training hours for S steps and
the 2 x 2 cm tile (8343^2 px) inference minutes, plus the measured S3 read rate."""
import argparse
import json
import os
import time

import numpy as np

import own_common as C

CFGS = {
    'A': dict(w=(8, 16, 32), head=32, dil=(1, 2, 4, 8), res3=(False, False, True, True)),
    'B': dict(w=(8, 24, 48), head=48, dil=(1, 2, 4, 8), res3=(False, True, True, True)),
    'C': dict(w=(16, 32, 64), head=64, dil=(1, 2, 4, 8, 16), res3=(False, True, True, True)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--cfgs', default='A,B,C')
    ap.add_argument('--patches', default='128,192')
    ap.add_argument('--batch', type=int, default=16)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    seg, r, c = C.X_SEG, 4, 2
    assert not C.in_x_zone(seg, r, c)
    y0, x0 = r * C.T_TILE + 3000, c * C.T_TILE + 3000
    t0 = time.time()
    img, rd = C.read_region(seg, y0, y0 + 1344, x0, x0 + 1344)
    t_read = time.time() - t0
    res = dict(provenance=C.PROV, declaration='RULES.md DECL-P4-23 item 4 (CPU timing test, T only, random labels)',
               region=dict(seg=seg, tile=[r, c], rows=[y0, y0 + 1344], cols=[x0, x0 + 1344]), read=rd,
               read_seconds=round(t_read, 2), read_MBps=round(img.nbytes / 1e6 / t_read, 1),
               input_mean_norm=float(C.norm(img).mean()), threads=a.threads, torch=torch.__version__, cfgs={})
    x_all = torch.from_numpy(C.norm(img)).permute(2, 0, 1)[None, None]  # (1,1,62,H,W)
    rng = np.random.default_rng(0)
    for name in a.cfgs.split(','):
        cfg = CFGS[name]
        m = C.build_model(cfg)
        rec = dict(cfg=cfg, params=C.n_params(m))
        opt = torch.optim.AdamW(m.parameters(), 1e-3)
        for P in [int(v) for v in a.patches.split(',')]:
            m.train()
            ts = []
            for it in range(4):
                ys = rng.integers(0, 1344 - P, a.batch)
                xs = rng.integers(0, 1344 - P, a.batch)
                xb = torch.cat([x_all[..., y:y + P, x:x + P] for y, x in zip(ys, xs)])
                lab = torch.from_numpy(rng.random((a.batch, 1, P // 4, P // 4)) < 0.1).float()
                t1 = time.time()
                out = m(xb)
                loss = torch.nn.functional.binary_cross_entropy_with_logits(out, lab)
                opt.zero_grad()
                loss.backward()
                opt.step()
                ts.append(time.time() - t1)
            rec[f'train_step_s_P{P}_B{a.batch}'] = round(float(np.median(ts[1:])), 3)
        m.eval()
        W, HALO = 1024, 160
        with torch.no_grad():
            ts = []
            for it in range(2):
                t1 = time.time()
                o = m(x_all[..., :W + 2 * HALO, :W + 2 * HALO])
                ts.append(time.time() - t1)
        s_per_mpx = float(min(ts)) / (W * W / 1e6)
        rec['infer_s_per_Mpx'] = round(s_per_mpx, 3)
        rec['tile_infer_min_full_valid'] = round(s_per_mpx * C.T_TILE ** 2 / 1e6 / 60, 1)  # compute incl. halo overhead
        rec['out_shape'] = list(o.shape)
        res['cfgs'][name] = rec
        print(json.dumps({name: rec}), flush=True)
    res['utc'] = C.utc()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps(res), flush=True)


if __name__ == '__main__':
    main()
