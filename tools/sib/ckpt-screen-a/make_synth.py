# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic smoke render (no CT): uint8 (31, H, W) Zarr group with array '0', shaped like a devloop DEV render.
A bright sheet near slice 15 (Gaussian in depth, sigma 3 slices) plus seeded noise, nonzero everywhere so no
tile is skipped (worst-case cost). Usage: make_synth.py OUT.zarr H W"""
import sys

import numpy as np
import zarr

out, H, W = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rng = np.random.default_rng(20260926)
z = np.arange(31, dtype=np.float32)[:, None, None]
a = 60 + 110 * np.exp(-((z - 15) ** 2) / (2 * 3.0 ** 2)) + rng.normal(0, 12, size=(31, H, W)).astype(np.float32)
a = np.clip(np.rint(a), 1, 255).astype(np.uint8)
g = zarr.open_group(out, mode='w', zarr_format=2)
g.create_array('0', data=a, chunks=(31, 128, 128))
print(out, a.shape, int(a.min()), int(a.max()))
