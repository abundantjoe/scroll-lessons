"""bi_common.py: shared pieces of the batch render + ink pipeline (scripts/pipeline/batch_ink.sh).

Scroll table, umbilicus, node normals (n = dP/dcol x dP/drow, the convention of poc_chain.sh 'render' and of Erwin's
make_submission_image.py), outward-normal fraction, theta per node, reading orientation (Erwin's rule: high z at the
top, theta decreasing to the right), mesh quad area.
"""
import json, numpy as np, tifffile

VOX_UM = 8.64
import os as _os
# Scroll table. The umbilicus (scroll axis) JSON is needed to orient normals outward: set UMB_<scroll>, e.g.
# UMB_PHerc0343=<pherc343-first-letters>/inputs/umbilicus_PHerc0343.json. Local CT mirrors default to
# $BI_ROOT/ct_<scroll>.zarr; override with BI_MIRROR_<scroll>.
SCROLLS = {
    'PHerc0268': dict(ct='vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr'),
    'PHerc0343': dict(ct='vesuvius-challenge-open-data/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr'),
}
for _k in SCROLLS:
    SCROLLS[_k]['umb'] = _os.environ.get(f'UMB_{_k}')
    SCROLLS[_k]['mirror'] = _os.environ.get(f'BI_MIRROR_{_k}') or _os.path.join(_os.environ.get('BI_ROOT', '.'), f'ct_{_k}.zarr')
MODELS = ['hybrid_3d2d-seed42_step-075000', 'hybrid_3d2d-seed43_step-075000', 'dense_native-016000.rebuilt']


def load_xyz(d):
    X, Y, Z = (tifffile.imread(f'{d}/{c}.tif').astype(np.float64) for c in 'xyz')
    ok = (X > -0.5) & (Y > -0.5) & (Z > -0.5) & np.isfinite(X) & np.isfinite(Y) & np.isfinite(Z)
    return X, Y, Z, ok


def load_umb(path):
    U = json.load(open(path)); U = U.get('control_points', U) if isinstance(U, dict) else U
    U = sorted(U, key=lambda p: p['z'])
    return (np.array([p['z'] for p in U], float), np.array([p['x'] for p in U], float), np.array([p['y'] for p in U], float))


def normals(X, Y, Z, ok):
    """central-difference node normals n = dP/dcol x dP/drow (unit), NaN where a neighbour is invalid; interior only."""
    P = np.stack([X, Y, Z], -1).copy(); P[~ok] = np.nan
    N = np.full(P.shape, np.nan)
    dc = P[1:-1, 2:] - P[1:-1, :-2]; dr = P[2:, 1:-1] - P[:-2, 1:-1]
    n = np.cross(dc, dr); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    N[1:-1, 1:-1] = n
    return N


def outward_fraction(X, Y, Z, ok, umb):
    """share of interior nodes whose normal has a positive component along the radial direction away from the axis."""
    N = normals(X, Y, Z, ok)
    cx = np.interp(Z, umb[0], umb[1]); cy = np.interp(Z, umb[0], umb[2])
    R = np.stack([X - cx, Y - cy, np.zeros_like(X)], -1); R /= np.linalg.norm(R, axis=-1, keepdims=True) + 1e-12
    d = np.sum(N * R, -1); d = d[np.isfinite(d)]
    return (float((d > 0).mean()) if d.size else float('nan')), (float(np.median(d)) if d.size else float('nan')), int(d.size)


def theta_by_column(X, Y, Z, ok, umb):
    """theta (deg) per node unwrapped along the columns (circular mean per column, np.unwrap over columns, each node put
    on its column's turn); the whole field is then shifted by a multiple of 360 so that its median lies in [0, 360)."""
    import warnings
    cx = np.interp(Z, umb[0], umb[1]); cy = np.interp(Z, umb[0], umb[2])
    phi = np.where(ok, np.degrees(np.arctan2(Y - cy, X - cx)), np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        c = np.nanmean(np.cos(np.radians(phi)), 0); s = np.nanmean(np.sin(np.radians(phi)), 0)
    psi = np.degrees(np.arctan2(s, c)); v = np.isfinite(psi); j = np.arange(psi.size)
    Psi = np.interp(j, j[v], np.degrees(np.unwrap(np.radians(psi[v]))))
    T = phi + 360.0 * np.round((Psi[None, :] - phi) / 360.0)
    med = np.nanmedian(T); T -= 360.0 * np.floor(med / 360.0)
    return T


def reading_orientation(X, Y, Z, ok, umb):
    """Erwin's rule (make_submission_image.measure_orientation): flip_lr = sign(dtheta/dcol) > 0, flip_ud = sign(dz/drow) > 0."""
    import warnings
    T = theta_by_column(X, Y, Z, ok, umb)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        dth = float(np.nanmedian(np.diff(T, axis=1)))
        zr = np.nanmedian(np.where(ok, Z, np.nan), axis=1); dz = float(np.nanmedian(np.diff(zr)))
    return dict(dtheta_deg_per_col=round(dth, 5), dz_vox_per_row=round(dz, 4), flip_lr=bool(dth > 0), flip_ud=bool(dz > 0),
                rule='reading = high z at top, theta decreasing to the right (Erwin, PHerc0343): flip_lr = dtheta/dcol > 0, '
                     'flip_ud = dz/drow > 0')


def quad_area_vox2(X, Y, Z, ok, step=None):
    """3D area (voxel^2) per mesh quad (NaN where a corner is invalid). Node coordinates are voxels, so the quad edge
    vectors already span the node spacing; `step` is unused (kept for call compatibility)."""
    P = np.stack([X, Y, Z], -1).copy(); P[~ok] = np.nan
    dc = 0.5 * ((P[:-1, 1:] - P[:-1, :-1]) + (P[1:, 1:] - P[1:, :-1]))
    dr = 0.5 * ((P[1:, :-1] - P[:-1, :-1]) + (P[1:, 1:] - P[:-1, 1:]))
    return np.linalg.norm(np.cross(dc, dr), axis=-1)


def scroll_of(name_or_path, default='PHerc0268'):
    s = str(name_or_path)
    for k in SCROLLS:
        if k.lower() in s.lower() or k.replace('PHerc0', 'pherc').lower() in s.lower(): return k
    return default
