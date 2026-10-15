# Provenance: Project HERCULES | owner the owner | [id removed]
"""Phase-1 smoke of scrollprize/fiber_ink_4class_selfdistill (task ckpt-screen-c). Numbers only; synthetic input.
Builds the student with the OFFICIAL villa scripts/fiber_5class/model.py build_fiber_unet (vesuvius NetworkFromConfig,
imported from the pinned villa source tree), loads the EMA state strictly, applies the official per-crop
percentile_minmax_normalize (dataset.py), runs one forward pass per patch size on smooth synthetic noise at the given
thread count (fp32) and records: embedded training config (selected keys), key match, output channels, class-3 (ink)
softmax statistics, seconds per patch. No map of any CT data is produced.
Usage: python fiber_smoke.py CKPT OUT.json [--threads 4] [--sizes 128 256]"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

VILLA = os.environ.get('CKSCR_VILLA', '/work/villa')
sys.path.insert(0, os.path.join(VILLA, 'vesuvius', 'src'))
sys.path.insert(0, os.path.join(VILLA, 'scripts', 'fiber_5class'))


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ckpt')
    ap.add_argument('out')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--sizes', type=int, nargs='+', default=[128, 256])
    a = ap.parse_args()
    for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[k] = str(a.threads)
    import torch
    from scipy.ndimage import gaussian_filter
    torch.set_num_threads(a.threads)
    from model import build_fiber_unet  # villa scripts/fiber_5class/model.py, unchanged
    from dataset import percentile_minmax_normalize  # villa scripts/fiber_5class/dataset.py, unchanged

    rec = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]',
               ckpt=a.ckpt, ckpt_sha256=sha256(a.ckpt), threads=a.threads, torch=torch.__version__,
               wrapper_sha256=sha256(os.path.abspath(__file__)))
    t0 = time.time()
    ck = torch.load(a.ckpt, map_location='cpu', weights_only=False)
    rec['load_s'] = round(time.time() - t0, 1)
    rec['ckpt_keys'] = sorted(ck.keys())
    cfg = ck.get('config', {}) or {}
    keep = ('patch_size', 'target_name', 'out_channels', 'activation', 'in_channels', 'mixed_precision', 'dataset',
            'pseudo', 'num_iterations', 'wandb_run_name', 'ema')
    rec['config'] = {k: cfg.get(k) for k in keep if k in cfg}
    rec['step'] = ck.get('step')
    state = ck['ema']['model_state']
    ps = tuple(cfg.get('patch_size', [256, 256, 256]))
    net = build_fiber_unet(crop_size=ps, target_name=cfg.get('target_name', 'labels'),
                           out_channels=int(cfg.get('out_channels', 4)), activation=cfg.get('activation', 'none'),
                           in_channels=int(cfg.get('in_channels', 1)))
    ref = net.state_dict()
    rec['missing_keys'] = sorted(set(ref) - set(state))
    rec['unexpected_keys'] = sorted(set(state) - set(ref))
    net.load_state_dict(state, strict=True)
    net.eval()
    rec['n_params'] = int(sum(p.numel() for p in net.parameters()))
    del ck, state
    rec['forward'] = {}
    rng = np.random.default_rng(20260926)
    for s in a.sizes:
        raw = gaussian_filter(rng.standard_normal((s, s, s)).astype(np.float32), 2.0)
        raw = np.clip(110 + 40 * raw / raw.std(), 0, 255).astype(np.uint8)
        x = torch.from_numpy(percentile_minmax_normalize(raw)[None].astype(np.float32, copy=False))[None]  # as dataset.py
        t1 = time.time()
        with torch.inference_mode():
            y = net(x)
        secs = time.time() - t1
        y = y['labels'] if isinstance(y, dict) else y
        p = torch.softmax(y.float(), 1)[0].numpy()
        rec['forward'][str(s)] = dict(seconds=round(secs, 2), out_shape=list(y.shape),
                                      class_frac_argmax=[float((p.argmax(0) == c).mean()) for c in range(p.shape[0])],
                                      ink_prob_mean=float(p[3].mean()) if p.shape[0] > 3 else None)
        print(s, rec['forward'][str(s)], flush=True)
    t = json.dumps(rec, indent=1, default=str) + '\n'
    assert t.isascii()
    open(a.out, 'w').write(t)


if __name__ == '__main__':
    main()
