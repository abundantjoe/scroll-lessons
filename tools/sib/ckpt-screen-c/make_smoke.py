# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic smoke render (31, H, W) uint8 for the screen wrapper: smooth random texture with a depth profile
(papyrus-like band around the surface index 15) and the right-most quarter set to 0 (invalid, like off-mesh canvas).
No CT data. Usage: python make_smoke.py OUT.npy [H W seed]"""
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

out = sys.argv[1]
H, W, seed = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (384, 384, 20260926)
rng = np.random.default_rng(seed)
z = np.arange(31)[:, None, None]
tex = gaussian_filter(rng.standard_normal((31, H, W)).astype(np.float32), (1.5, 3, 3))
tex = tex / tex.std()
band = np.exp(-0.5 * ((z - 15) / 5.0) ** 2)
a = np.clip(60 + 90 * band + 25 * tex, 0, 255).astype(np.uint8)
a[:, :, (3 * W) // 4:] = 0
np.save(out, a)
print(out, a.shape, a.dtype, float(a.mean()))
