# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-C3-R1 crop rule: 2048 px square on a 256 px grid, no overlap with the run-1
crop, fully render-valid (mesh-valid canvas), maximum supervision-mask pixel count;
ties -> smaller y0, then smaller x0. Prints the chosen (y0, x0) and its count."""
import json
import sys

import numpy as np
import zarr

SUP, VALID = sys.argv[1], sys.argv[2]  # supervision mask zarr array path; mesh-valid .npy (H, W) bool
S = np.asarray(zarr.open(SUP, mode="r"))
S = (S[S.shape[0] // 2] if S.ndim == 3 else S) > 0
V = np.load(VALID).astype(bool)
H, W = V.shape
N, G = 2048, 256
R1 = (2048, 1152)  # run-1 crop (y0, x0)
ci = np.pad(np.cumsum(np.cumsum(S & V, 0), 1), ((1, 0), (1, 0)))
cv = np.pad(np.cumsum(np.cumsum(V, 0), 1), ((1, 0), (1, 0)))


def box(c, y, x):
    return c[y + N, x + N] - c[y, x + N] - c[y + N, x] + c[y, x]


best = None
for y in range(0, H - N + 1, G):
    for x in range(0, W - N + 1, G):
        if not (y + N <= R1[0] or y >= R1[0] + N or x + N <= R1[1] or x >= R1[1] + N):
            continue
        if box(cv, y, x) != N * N:
            continue
        k = (int(box(ci, y, x)), -y, -x)
        if best is None or k > best[0]:
            best = (k, y, x)
print(json.dumps({"y0": best[1], "x0": best[2], "supervision_px": best[0][0]} if best else {"none": True}))
