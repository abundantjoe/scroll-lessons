"""Top-margin natural experiment over a set of strip overlays (stripqc.margins.top_margin_experiment), aggregate only.

  python natural_experiment.py OUT.json OVERLAY.jpg [OVERLAY.jpg ...]

Ink proxy per pixel = clip(R - B, 0) / 224 of a fixed-scale ink overlay (orange alpha for p 0.40 -> 0.70 painted on a
grey CT layer); validity = non-black pixels. For each strip, columns with a homogeneous 30-row vs 10-row blank top
margin are compared at the same render rows 50-90. Writes only aggregate numbers: per-height means, anonymised per-strip pairs and the pooled per-row profile for render
heights with at least 20 strips (only n_strips otherwise; no images, no strip names).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stripqc import margins  # noqa: E402

out, paths = sys.argv[1], sys.argv[2:]
per, prof = {}, {}
for p in paths:
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
    valid = margins.valid_from_overlay(a)
    ink = np.clip(a[..., 0] - a[..., 2], 0, None) / 224.0
    H = a.shape[0]
    r = margins.top_margin_experiment(ink, valid)
    if np.isfinite(r[30][0]) and np.isfinite(r[10][0]):
        per.setdefault(H, []).append((r[30][0], r[10][0]))
    prof.setdefault(H, []).append([float(ink[i][valid[i]].mean()) if valid[i].any() else np.nan for i in range(H)])
res = dict(n_strips_total=len(paths), proxy='alpha = clip(R-B,0)/224 at render rows 50-90', by_render_height={})
for H, v in sorted(per.items()):
    v = np.array(v)
    res['by_render_height'][str(H)] = dict(n_strips_with_both_classes=int(len(v)), mean_alpha_30row_margin=float(v[:, 0].mean()),
                                           mean_alpha_10row_margin=float(v[:, 1].mean()),
                                           strips_where_30_gt_10=int((v[:, 0] > v[:, 1]).sum()),
                                           per_strip_pairs_anonymised=sorted([round(float(x), 5), round(float(y), 5)] for x, y in v))
for H, rows in sorted(prof.items()):
    m = np.nanmean(np.array(rows, float), 0)
    res.setdefault('row_profile_mean_alpha', {})[str(H)] = (dict(n_strips=len(rows), mean_alpha_by_row=[None if not np.isfinite(x) else round(float(x), 5) for x in m])
                                                             if len(rows) >= 20 else dict(n_strips=len(rows)))   # no near-per-strip profiles
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps(res, indent=1))
