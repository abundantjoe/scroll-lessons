#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
"""Held-out evaluation of a Master checkpoint on a validation shard (DECL-FL-7 item 3 bars): pixel AUC, pixel AP and the
tile AUC (64x64 crops scored by their mean probability against the crop's label fraction > 0.05), fp32, no TTA.
usage: eval_master.py <ckpt.pt> <val_shard.npz> <out.json>"""
import sys, os, json, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from master import Master; from train_master import auc, avg_precision
ck, shard, out = sys.argv[1:4]; d = np.load(shard); X, Y = d['x'], d['y']; c = torch.load(ck, map_location='cpu'); m = Master(ssl_encoder=None, base=c.get('base', 16), ssl_dim=192); m.load_state_dict(c['model']); m.eval(); torch.set_num_threads(max(1, os.cpu_count() or 4))
sc, lb, tile_s, tile_l = [], [], [], []
with torch.no_grad():
    for i in range(0, len(X), 8):
        x = torch.from_numpy(X[i:i + 8]).float().unsqueeze(1) / 255.0; p = torch.sigmoid(m(x).float()).numpy()[:, 0]; y = Y[i:i + 8] / 255.0
        sc.append(p.ravel()); lb.append(y.ravel()); tile_s.append(p.reshape(len(p), -1).mean(1)); tile_l.append((y.reshape(len(y), -1) > 0.5).mean(1) > 0.05)
sc, lb, ts, tl = np.concatenate(sc), np.concatenate(lb), np.concatenate(tile_s), np.concatenate(tile_l)
res = {'ckpt': ck, 'shard': shard, 'n_crops': int(len(X)), 'pixel_auc': round(auc(sc, lb), 4), 'pixel_ap': round(avg_precision(sc, lb), 4), 'tile_auc': round(auc(ts, tl.astype(float)), 4) if 0 < tl.sum() < len(tl) else None, 'label_frac': round(float((lb > 0.5).mean()), 4), 'bars': {'auc': 0.9, 'ap': 0.5, 'tile_auc': 0.85}}
res['pass'] = bool(res['pixel_auc'] >= 0.9 and res['pixel_ap'] >= 0.5 and (res['tile_auc'] or 0) >= 0.85); json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res))
