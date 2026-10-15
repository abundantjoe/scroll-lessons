# Provenance: Project HERCULES | owner the owner | [id removed]
"""Self-test of p4o_tiles.py (synthetic data only, no CT): the banded tiling equals the card's loop on the full
(H, W, 62) stack, in both directions; model files verified; seconds per window measured at 4 threads."""
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p4o_tiles as P  # noqa: E402

torch.set_num_threads(4)
files = P.verify_model_files()
model = P.load_model()
rng = np.random.default_rng(20260926)
Hc, Wc = 512, 512
vol = rng.integers(0, 256, size=(P.D_MODEL, Hc, Wc), dtype=np.uint8)   # (62, H, W)
fm = np.ones((Hc, Wc), np.uint8)
fm[:40, :100] = 0


class B:
    def __init__(self, ry):
        self.a = vol[:, ry:ry + P.CH, :] if ry + P.CH <= Hc else np.zeros((P.D_MODEL, P.CH, Wc), np.uint8)


res = {'model_files': files}
for rev in (True, False):
    t0 = time.time()
    pb, cb, n = P.card_tiling_banded(model, 0, 0, Hc, Wc, fm, lambda ry: B(ry), P.train_norm, rev)
    dt = time.time() - t0
    # reference: the card loop on image = (H, W, 62) stack
    img = np.transpose(vol[::-1] if rev else vol, (1, 2, 0))
    mp = np.zeros((Hc, Wc), np.float32)
    mc = np.zeros((Hc, Wc), np.float32)
    with torch.no_grad():
        for y in range(0, Hc - 256 + 1, 128):
            for x in range(0, Wc - 256 + 1, 128):
                if np.any(fm[y:y + 256, x:x + 256] == 0):
                    continue
                t = torch.from_numpy(np.ascontiguousarray(img[y:y + 256, x:x + 256])).permute(2, 0, 1)
                t = P.train_norm(t.unsqueeze(0).unsqueeze(0).float())
                prob = F.interpolate(torch.sigmoid(model(t).logits), scale_factor=4, mode="bilinear").squeeze().numpy()
                mp[y:y + 256, x:x + 256] += prob
                mc[y:y + 256, x:x + 256] += 1
    pr = np.divide(mp, mc, out=np.zeros_like(mp), where=mc != 0)
    res['reverse' if rev else 'forward'] = dict(windows=n, max_abs_diff=float(np.abs(pr - pb).max()),
                                                count_equal=bool(np.array_equal(mc, cb)),
                                                seconds_per_window=round(dt / n, 3))
res['pass'] = all(res[k]['max_abs_diff'] == 0.0 and res[k]['count_equal'] for k in ('reverse', 'forward'))
print(json.dumps(res, indent=1))
sys.exit(0 if res['pass'] else 1)
