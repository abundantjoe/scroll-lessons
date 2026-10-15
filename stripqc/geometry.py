"""Surface edits used as controls and fixes: normal displacement (negative control) and extrapolated row padding."""
import numpy as np

from . import tifxyz


def displace(P, ok, umb, d=8.0):
    """Move every valid node that has a finite gradient normal d vox along its outward unit normal (one-sided
    differences at the grid border; a node next to an invalid node has no normal and is dropped from okq; sign set so
    the majority points away from the scroll axis). d = +8 is half the sheet spacing of a ~16 vox pitch: the copy
    has its centre between sheets (the negative arm). A 17-layer ink window can still reach the original sheet
    (docs/METHODS.md §2). -> (Q, okq, outward_majority)."""
    N = tifxyz.normals_gradient(P, ok)
    okn = ok & np.isfinite(N).all(-1)
    frac = tifxyz.outward_fraction(P, N, okn, umb)
    sign = 1.0 if frac >= 0.5 else -1.0
    return P + d * sign * np.nan_to_num(N), okn, frac


def xpad(P, ok, r0, r1, k=2):
    """Rows r0:r1 of a surface plus k rows extrapolated linearly on each side from each column's two outermost valid rows.
    The original rows are kept bit-identical; score only rows k:k + (r1 - r0) of the result. -> (Q, okq)."""
    S, okS = P[r0:r1], ok[r0:r1]
    H, W = okS.shape
    out = np.full((H + 2 * k, W, 3), -1.0)
    oko = np.zeros((H + 2 * k, W), bool)
    out[k:k + H], oko[k:k + H] = S, okS
    for j in range(W):
        rv = np.flatnonzero(okS[:, j])
        if rv.size < 2:
            continue
        t0, t1 = rv[0], rv[-1]
        n0, n1 = rv[1], rv[-2]  # nearest valid rows (a hole may sit next to a boundary row)
        dlo, dhi = (S[t0, j] - S[n0, j]) / (n0 - t0), (S[t1, j] - S[n1, j]) / (t1 - n1)
        for i in range(1, k + 1):
            if k + t0 - i >= 0:
                out[k + t0 - i, j], oko[k + t0 - i, j] = S[t0, j] + i * dlo, True
            if k + t1 + i < H + 2 * k:
                out[k + t1 + i, j], oko[k + t1 + i, j] = S[t1, j] + i * dhi, True
    return out, oko
