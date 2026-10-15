#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-FL-7 item 3(ii), Hecate 9.6 um on shard crops only. Runs the released Hecate model (tools/master/hecate/hecate.py, unmodified)
one 16x64x64 patch per shard crop, replicating hecate.predict() per patch exactly (central-depth selection, optional z reversal,
/255, empty-column support mask, sigmoid, empty columns zeroed); a single patch needs no Hann blending (window cancels).
Default = NATIVE spacing: the crop stacks of the shard (8.64 um, 31 layers) are fed as if they were 9.6 um, which hecate.py
refuses on the CLI (spacing check); this is the declared mismatch experiment, not the model's recipe.
--volume <9.6um .npy> --scale 0.9: instead take the 64x64 patch of the resampled volume centred on each crop, map its output
back to the 8.64 um crop (bilinear), so the crop-only number is like-for-like with the native run.
Scores = baseline_eval.py metrics at the same crops. usage: hecate_crops.py <shard.npz> <ckpt> <out.json> [--reverse] [--volume V --scale 0.9] [--name N] [--save-probs P.npz]"""
import argparse, json, os, sys, time, numpy as np, torch, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hecate')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hecate import load_model
from baseline_eval import auc, avg_precision

def central(depth, d, reverse):
    z0 = depth // 2 - d // 2
    return slice(depth - z0 - d, depth - z0) if reverse else slice(z0, z0 + d)

@torch.inference_mode()
def run_patches(model, patches, batch):
    """patches: (N,d,p,p) uint8 -> (N,p,p) float32 probabilities, as hecate.predict() computes them per patch."""
    out = np.zeros((len(patches),) + patches.shape[-2:], np.float32)
    for s in range(0, len(patches), batch):
        raw = torch.from_numpy(patches[s:s + batch]); support = raw.any(1)
        image = torch.from_numpy(patches[s:s + batch].astype(np.float32) / model.divisor)[:, None]
        valid = support[:, None, None].expand(-1, 1, raw.shape[1], -1, -1)
        prob = model(image, valid).float().sigmoid()[:, 0] * support
        out[s:s + batch] = prob.numpy()
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('shard'); ap.add_argument('ckpt'); ap.add_argument('out'); ap.add_argument('--reverse', action='store_true')
    ap.add_argument('--volume'); ap.add_argument('--scale', type=float, default=0.9); ap.add_argument('--name', default='hecate_crops'); ap.add_argument('--save-probs'); ap.add_argument('--batch', type=int, default=16)
    a = ap.parse_args(); torch.set_num_threads(int(os.environ.get('OMP_NUM_THREADS', '4')))
    d = np.load(a.shard, allow_pickle=True); X = d['x']; Y = d['y']; pos = d['pos']; S = Y.shape[-1]; meta = json.loads(str(d['meta']))
    model = load_model(a.ckpt, 'cpu'); D, P, _ = model.patch_size; t0 = time.time()
    if a.volume is None:
        depth = X.shape[1]; zs = central(depth, D, a.reverse); patches = X[:, zs]
        if a.reverse: patches = patches[:, ::-1]
        patches = np.ascontiguousarray(patches); mode = f'native: shard stacks at {meta.get("um", 8.64)} um fed as 9.6 um, planes {zs.start}..{zs.stop}' + (' reversed' if a.reverse else '')
        probs = run_patches(model, patches, a.batch); crops = probs
    else:
        V = np.load(a.volume, mmap_mode='r'); depth, H9, W9 = V.shape; zs = central(depth, D, a.reverse); sc = a.scale
        origins = [(int(np.clip(round((y0 + S / 2) * sc - P / 2), 0, H9 - P)), int(np.clip(round((x0 + S / 2) * sc - P / 2), 0, W9 - P))) for y0, x0 in pos]
        patches = np.stack([np.asarray(V[zs, oy:oy + P, ox:ox + P]) for oy, ox in origins]); 
        if a.reverse: patches = np.ascontiguousarray(patches[:, ::-1])
        mode = f'resampled volume {a.volume} ({depth} planes, scale {sc}); one centred patch per crop, planes {zs.start}..{zs.stop}' + (' reversed' if a.reverse else '')
        probs = run_patches(model, patches, a.batch); crops = np.zeros((len(pos), S, S), np.float32)
        for i, ((y0, x0), (oy, ox)) in enumerate(zip(pos, origins)):   # map the 9.6 um patch back onto the 8.64 um crop window
            big = cv2.resize(probs[i], None, fx=1 / sc, fy=1 / sc, interpolation=cv2.INTER_LINEAR); by, bx = oy / sc, ox / sc
            ys = np.clip(np.arange(y0, y0 + S) - by, 0, big.shape[0] - 1).astype(int); xs = np.clip(np.arange(x0, x0 + S) - bx, 0, big.shape[1] - 1).astype(int)
            crops[i] = big[np.ix_(ys, xs)]
    sc_, lb = crops.reshape(len(crops), -1), Y.reshape(len(Y), -1) / 255.0
    tmax = np.percentile(crops.reshape(len(crops), -1), 95, axis=1); tlab = (Y.max((1, 2)) / 255.0 > 0.5).astype(float)
    r = {'name': a.name, 'shard': a.shard, 'ckpt': a.ckpt, 'mode': mode, 'reverse': a.reverse, 'n_crops': int(len(crops)), 'pixel_auc': auc(sc_.ravel(), lb.ravel()), 'pixel_ap': avg_precision(sc_.ravel(), lb.ravel()),
         'tile_auc_p95': auc(tmax, tlab), 'label_pos_frac': float((lb > 0.5).mean()), 'crops_with_ink': float(tlab.mean()), 'prob_mean': float(crops.mean()), 'prob_p99': float(np.percentile(crops, 99)), 'seconds': round(time.time() - t0, 1)}
    json.dump(r, open(a.out, 'w'), indent=1); print(json.dumps(r))
    if a.save_probs: np.savez_compressed(a.save_probs, probs=(crops * 255).round().astype(np.uint8), pos=pos)

if __name__ == '__main__': main()
