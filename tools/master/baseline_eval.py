#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-FL-7 item 3(ii): score ANY 2-D ink map (a tif/png on the 8.64 um surface-volume canvas) against the pseudo-labels of a
shard at the shard's own crop positions, with the same metrics train_master.py reports (pixel AUC, pixel AP) plus the
tile-level AUC of item 3(iii) (crop max score vs crop contains ink). usage:
  baseline_eval.py <shard.npz> <map.tif|png|crops.npy> <out.json> [--name ink_9um_s42] [--invert]
A .npy map is a per-crop stack (N,S,S) of probabilities in the shard's crop order (tools/master/v8in_infer.py shard mode):
scored crop by crop, with no canvas and no stitching (exact alignment).
"""
import argparse, json, numpy as np, cv2, tifffile

def auc(s, l):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); l = l > 0.5; n1 = l.sum(); n0 = len(l) - n1
    return float((r[l].sum() - n1 * (n1 + 1) / 2) / max(n1 * n0, 1))

def avg_precision(s, l):
    o = np.argsort(-s); l = (l[o] > 0.5); tp = np.cumsum(l); prec = tp / np.arange(1, len(l) + 1); return float((prec * l).sum() / max(l.sum(), 1))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('shard'); ap.add_argument('map'); ap.add_argument('out'); ap.add_argument('--name', default='map'); ap.add_argument('--invert', action='store_true')
    a = ap.parse_args(); d = np.load(a.shard, allow_pickle=True); meta = json.loads(str(d['meta'])); Y = d['y']; pos = d['pos']; S = Y.shape[-1]
    if a.map.endswith('.npy'):
        C = np.load(a.map).astype(np.float32); assert C.shape[1:] == (S, S) and len(C) <= len(Y), (C.shape, Y.shape)
        C = (C - C.min()) / max(C.max() - C.min(), 1e-6); C = 1 - C if a.invert else C
        lb = Y[:len(C)].reshape(len(C), -1) / 255.0; tmax = np.percentile(C.reshape(len(C), -1), 95, axis=1); tlab = (Y[:len(C)].reshape(len(C), -1).max(1) / 255.0 > 0.5).astype(float)
        sc, lb = C.ravel(), lb.ravel()
        r = {'name': a.name, 'shard': a.shard, 'map': a.map, 'mode': 'per_crop', 'n_crops': int(len(C)), 'pixel_auc': auc(sc, lb), 'pixel_ap': avg_precision(sc, lb),
             'tile_auc_p95': auc(tmax, tlab), 'label_pos_frac': float((lb > 0.5).mean()), 'crops_with_ink': float(tlab.mean())}
        json.dump(r, open(a.out, 'w'), indent=1); print(json.dumps(r)); return
    m = tifffile.imread(a.map) if a.map.endswith(('.tif', '.tiff')) else cv2.imread(a.map, cv2.IMREAD_UNCHANGED)
    if m.ndim == 3: m = m[..., 0]
    m = m.astype(np.float32); m = (m - m.min()) / max(m.max() - m.min(), 1e-6)
    if a.invert: m = 1 - m
    H, W = meta['H'], meta['W']
    if m.shape != (H, W): m = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA); resized = True
    else: resized = False
    sc, lb, tmax, tlab = [], [], [], []
    for (y0, x0), y in zip(pos, Y):
        c = m[y0:y0 + S, x0:x0 + S]
        if c.shape != (S, S): continue
        sc.append(c.ravel()); lb.append(y.ravel() / 255.0); tmax.append(float(np.percentile(c, 95))); tlab.append(float(y.max() / 255.0 > 0.5))
    sc, lb, tmax, tlab = np.concatenate(sc), np.concatenate(lb), np.array(tmax), np.array(tlab)
    r = {'name': a.name, 'shard': a.shard, 'map': a.map, 'map_shape_resized': resized, 'n_crops': int(len(tmax)), 'pixel_auc': auc(sc, lb), 'pixel_ap': avg_precision(sc, lb),
         'tile_auc_p95': auc(tmax, tlab), 'label_pos_frac': float((lb > 0.5).mean()), 'crops_with_ink': float(tlab.mean())}
    json.dump(r, open(a.out, 'w'), indent=1); print(json.dumps(r))

if __name__ == '__main__': main()
