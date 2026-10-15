"""Papyrus grey level of the control strips over the +-20 um slab (numbers only), for the injection amplitude.

Provenance: Project HERCULES | owner the owner | [id removed]
Median over mesh-valid, non-zero slab voxels of 256 random chunks (default_rng(20260926)) inside eligible control tiles.
Usage: python gpap.py <MAT> <scratch>
"""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold as G  # noqa: E402

name, scr = sys.argv[1], sys.argv[2]
mat = G.load_material(name, scr)
rng = np.random.default_rng(20260926)
f, T = 2 ** mat["m"]["level"], mat["T"]
z0, z1 = G.slab(name, 20)
h = np.zeros(256, np.int64)
got = 0
while got < 256:
    t = mat["tiles"][rng.integers(len(mat["tiles"]))]
    yc = (t["r"] * T // f + rng.integers(T // f)) // G.CH
    xc = (t["c"] * T // f + rng.integers(T // f)) // G.CH
    a = G.fetch_chunk(mat, yc, xc, z0, z1)
    if a is None:
        continue
    vm = G.level_valid(mat, yc * G.CH + np.arange(G.CH), xc * G.CH + np.arange(G.CH))
    v = a[:, vm]
    v = v[v > 0]
    if v.size == 0:
        continue
    h += np.bincount(v, minlength=256)
    got += 1
c = np.cumsum(h)
med = int(np.searchsorted(c, 0.5 * c[-1]))
print(json.dumps({"mat": name, "slab": [z0, z1], "chunks": got, "voxels": int(c[-1]), "median_grey": med,
                  "p10": int(np.searchsorted(c, 0.1 * c[-1])), "p90": int(np.searchsorted(c, 0.9 * c[-1]))}))
