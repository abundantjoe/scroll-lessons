#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Resumable 2-D Hecate inference: the same tiling, central-depth selection, /divisor normalisation, support mask, floored Hann
blending and uint8 rounding as hecate.predict() (tools/master/hecate/hecate.py, imported unmodified), with the accumulators
held in RAM and checkpointed atomically to disk every --flush batches so a container restart resumes instead of restarting.
Verified byte-identical to hecate.py's PNG on a real sub-volume (see logs/fl7/baseline_hecate/*/tiled_identity.json).
usage: hecate_tiled.py --checkpoint C --input V.npy --spacing-um 9.6 --output out.png --state DIR [--reverse] [--batch-size 16] [--stride 32] [--flush 25]"""
import argparse, json, os, sys, time, numpy as np, torch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hecate'))
from hecate import load_model, axis_starts, open_volume, write_png

@torch.inference_mode()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--checkpoint', required=True); ap.add_argument('--input', required=True); ap.add_argument('--array', default='0')
    ap.add_argument('--output', required=True); ap.add_argument('--state', required=True); ap.add_argument('--spacing-um', type=float, required=True); ap.add_argument('--reverse', action='store_true')
    ap.add_argument('--batch-size', type=int, default=16); ap.add_argument('--stride', type=int); ap.add_argument('--flush', type=int, default=25); ap.add_argument('--threads', type=int, default=int(os.environ.get('OMP_NUM_THREADS', '4')))
    a = ap.parse_args(); torch.set_num_threads(a.threads)
    model = load_model(a.checkpoint, 'cpu')
    if abs(a.spacing_um / model.sampling_um - 1) > .02: sys.exit(f'Resample the render to {model.sampling_um} um first')
    volume = open_volume(a.input, a.array); d, p, _ = model.patch_size; depth, h, w = volume.shape; stride = p // 2 if a.stride is None else a.stride
    assert depth >= d and 0 < stride <= p
    z0 = depth // 2 - d // 2; zs = slice(depth - z0 - d, depth - z0) if a.reverse else slice(z0, z0 + d)
    win = torch.hann_window(p, periodic=False); win = win[:, None] * win[None, :]; win = (win / win.max().clamp_min(torch.finfo(torch.float32).eps)).clamp_min(.001); window = win.numpy()
    origins = [(y, x) for y in axis_starts(h, p, stride) for x in axis_starts(w, p, stride)]
    os.makedirs(a.state, exist_ok=True); ck = os.path.join(a.state, 'acc.npz'); start0 = 0
    if os.path.exists(ck):
        s = np.load(ck); numerator, denominator, start0 = s['num'], s['den'], int(s['next'])
        assert numerator.shape == (h, w) and int(s['n_origins']) == len(origins) and bool(s['reverse']) == a.reverse, 'state does not match this run'
        print(f'resuming at origin {start0}/{len(origins)}', flush=True)
    else: numerator = np.zeros((h, w), np.float32); denominator = np.zeros((h, w), np.float32)
    def save(nxt):
        tmp = ck + '.tmp.npz'; np.savez(tmp, num=numerator, den=denominator, next=nxt, n_origins=len(origins), reverse=a.reverse); os.replace(tmp, ck)
    t0 = time.time(); nb = 0
    for start in range(start0, len(origins), a.batch_size):
        active, patches = [], []
        for y, x in origins[start:start + a.batch_size]:
            ph, pw = min(p, h - y), min(p, w - x); denominator[y:y + ph, x:x + pw] += window[:ph, :pw]
            raw = np.asarray(volume[zs, y:y + ph, x:x + pw])
            if a.reverse: raw = raw[::-1]
            if not raw.any(): continue
            patch = np.zeros((d, p, p), dtype=np.uint8); patch[:, :ph, :pw] = raw; patches.append(patch); active.append((y, x, ph, pw))
        if patches:
            raw = torch.from_numpy(np.stack(patches)); support = raw.any(1)
            normalized = np.stack(patches).astype(np.float32); normalized /= model.divisor
            image = torch.from_numpy(normalized[:, None]); valid = support[:, None, None].expand(-1, 1, d, -1, -1)
            probability = model(image, valid).float().sigmoid()[:, 0]
            weighted = (probability * support * win).numpy()
            for pred, (y, x, ph, pw) in zip(weighted, active): numerator[y:y + ph, x:x + pw] += pred[:ph, :pw]
        nb += 1; nxt = min(start + a.batch_size, len(origins))
        if nb % a.flush == 0 or nxt == len(origins):
            save(nxt); print(f'{nxt}/{len(origins)} origins, {time.time() - t0:.0f} s, checkpoint saved', flush=True)
    prob = numerator / denominator
    if not np.isfinite(prob).all(): raise FloatingPointError('Non-finite inference output')
    result = np.rint(prob.clip(0, 1) * 255).astype(np.uint8); partial = a.output + '.partial'; write_png(result, partial); os.replace(partial, a.output)
    json.dump({'checkpoint': os.path.basename(a.checkpoint), 'sampling_um': a.spacing_um, 'shape_yx': [h, w], 'reverse_z': a.reverse, 'central_depth': d, 'planes': [zs.start, zs.stop], 'precision': 'fp32', 'stride': stride,
               'n_origins': len(origins), 'probabilities': 'uint8 = round(255 * probability); no min-max scaling', 'driver': 'hecate_tiled.py (resumable re-implementation of hecate.predict)'}, open(os.path.splitext(a.output)[0] + '.json', 'w'), indent=2)
    print(a.output, flush=True)

if __name__ == '__main__': main()
