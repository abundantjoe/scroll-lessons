"""tifxyz surfaces (x.tif, y.tif, z.tif + meta.json; -1 = no node): load, save, node normals, outward orientation."""
import json
import os

import numpy as np
import tifffile


def load(d):
    """-> P (rows, cols, 3) float64 positions (x, y, z), ok (rows, cols) bool, meta dict."""
    X, Y, Z = (tifffile.imread(os.path.join(d, f'{c}.tif')).astype(np.float64) for c in 'xyz')
    ok = (X > -0.5) & (Y > -0.5) & (Z > -0.5) & np.isfinite(X) & np.isfinite(Y) & np.isfinite(Z)
    mp = os.path.join(d, 'meta.json')
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
    return np.stack([X, Y, Z], -1), ok, meta


def save(d, P, ok, meta=None, **update):
    """Write x/y/z.tif (float32, -1 where not ok) and meta.json (bbox recomputed)."""
    os.makedirs(d, exist_ok=True)
    for i, c in enumerate('xyz'):
        tifffile.imwrite(os.path.join(d, f'{c}.tif'), np.where(ok, P[..., i], -1).astype(np.float32))
    m = dict(meta or {'type': 'seg', 'format': 'tifxyz', 'scale': [0.05, 0.05]})
    V = P[ok]
    if V.size:
        m['bbox'] = [V.min(0).tolist(), V.max(0).tolist()]
    m.update(update)
    json.dump(m, open(os.path.join(d, 'meta.json'), 'w'), indent=1)


def normals_central(P, ok):
    """Central-difference unit normals n = dP/dcol x dP/drow; NaN on border nodes and next to invalid nodes.
    This is the convention behind the blank render margin: a node without a normal renders nothing."""
    Q = P.copy()
    Q[~ok] = np.nan
    N = np.full(P.shape, np.nan)
    dc = Q[1:-1, 2:] - Q[1:-1, :-2]
    dr = Q[2:, 1:-1] - Q[:-2, 1:-1]
    n = np.cross(dc, dr)
    N[1:-1, 1:-1] = n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12)
    return N


def normals_gradient(P, ok):
    """Unit normals from np.gradient (one-sided at the edges), so edge nodes get a normal too; NaN where P is invalid."""
    Q = P.copy()
    Q[~ok] = np.nan
    n = np.cross(np.gradient(Q, axis=1), np.gradient(Q, axis=0))
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12)


def load_umbilicus(path):
    """Scroll axis as (z, x, y) arrays sorted by z, from a JSON list of {z, x, y} or {'control_points': [...]}."""
    U = json.load(open(path))
    U = U.get('control_points', U) if isinstance(U, dict) else U
    U = sorted(U, key=lambda p: p['z'])
    return tuple(np.array([p[k] for p in U], float) for k in ('z', 'x', 'y'))


def outward_fraction(P, N, ok, umb):
    """Share of nodes whose normal points away from the scroll axis (radially, in the xy plane)."""
    cx = np.interp(P[..., 2], umb[0], umb[1])
    cy = np.interp(P[..., 2], umb[0], umb[2])
    R = np.stack([P[..., 0] - cx, P[..., 1] - cy, np.zeros_like(cx)], -1)
    R /= np.linalg.norm(R, axis=-1, keepdims=True) + 1e-12
    d = np.sum(N * R, -1)
    m = ok & np.isfinite(d)
    return float((d[m] > 0).mean()) if m.any() else float('nan')
