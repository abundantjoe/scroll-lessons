"""Method E (RULES.md): per-crop rank-normalised mean of the v8 and GP-R1 score maps, smoothed at sigma = 0.08 mm.

  ensemble_e.py <seg>:<crop> ...
Writes s_bot_e.npy next to each crop.
"""
import sys, os, numpy as np
from scipy.stats import rankdata
from scipy.ndimage import gaussian_filter

PITCH_UM = 2.4
SIGMA_MM = 0.08
TAGS = ("v8", "gpr1")

for spec in sys.argv[1:]:
    seg, crop = spec.split(":")
    d = f"data/s1/{seg}/derived/{crop}"
    mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
    acc = np.zeros(mask.shape, np.float32)
    for t in TAGS:
        p = os.path.join(d, f"s_bot_{t}.npy")
        if not os.path.exists(p): raise SystemExit(f"missing {p}")
        x = np.load(p).astype(np.float32)
        r = np.zeros(mask.shape, np.float32)
        r[mask] = (rankdata(x[mask]) / mask.sum()).astype(np.float32)   # rank-normalise inside the judge mask
        acc += r
    acc /= len(TAGS)
    s = SIGMA_MM * 1000 / PITCH_UM
    mf = mask.astype(np.float32)
    sm = gaussian_filter(acc * mf, s) / np.maximum(gaussian_filter(mf, s), 1e-3)   # normalised convolution
    out = np.where(mask, sm, 0).astype(np.float16)
    np.save(os.path.join(d, "s_bot_e.npy"), out)
    print(spec, "E written (rank-mean of", ", ".join(TAGS), f"smoothed {SIGMA_MM} mm)", flush=True)
