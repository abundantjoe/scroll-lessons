#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 item 6 (X4 grow and render) mesh checks, pure numpy/scipy:
  (1) external mesh self-intersection test and neighbour-crossing test between two meshes
      (exact Moller-1997 triangle-triangle interval test + coplanar 2-D overlap, uniform-grid broadphase);
  (2) per-triangle stretch of the arc-length uv map versus the 3-D mesh (area ratio, singular values, angle
      deviation), median and p95; the nominal grid uv (1/scale voxels per cell) is reported alongside;
  (3) W3 clearance: for each vertex the distance along the local normal to the nearest lamina peak on either side in the
      raw CT at native resolution (8.64 um, OME level 0; peaks = scipy find_peaks, prominence >= 3 MAD of the profile,
      width >= 3 vox, the same convention as tools/umb/core_native.py crossing_balance), level-0 128^3 chunks fetched
      with class L0.slab of tools/umb/core_native.py and cached in RAM for the run.
Input meshes: VC3D tifxyz directories (x.tif, y.tif, z.tif float32 grids of level-0 voxel coordinates, invalid cells
-1/NaN/0, meta.json with "scale") as written by vc_grow_seg_from_seed / vc_render_tifxyz, or Wavefront OBJ (v, vt, f).
Only bars are reported; the tool classifies nothing as SHEET/PAIR/FUSED (that is X2) and claims no letters.
usage:
  mesh_checks.py selftest <out_dir>                      synthetic meshes + synthetic laminae volume (no network)
  mesh_checks.py check <mesh> <out_dir> [--neighbour <mesh2>] [--w3] [--volume s3://.../0] [--w3-half 80]
                 [--w3-sigma 1.0] [--w3-own-tol 8] [--w3-tube 2] [--normal-smooth k] [--w3-window i0:i1,j0:j1] [--w3-stride 1] [--save-vertex]
"""
import os, sys, json, time, argparse
os.environ.setdefault('OMP_NUM_THREADS', '3'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '3'); os.environ.setdefault('MKL_NUM_THREADS', '3')
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

VOX_UM = 8.64
DEFAULT_VOLUME = 's3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/0'
HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------------------------------------- mesh I/O
def load_tifxyz(d):
    """tifxyz dir -> dict(P (H,W,3) float64 level-0 coords, valid (H,W) bool, scale (su,sv) cells per voxel, meta)."""
    import tifffile
    X, Y, Z = [tifffile.imread(os.path.join(d, c + '.tif')).astype(np.float64) for c in 'xyz']
    valid = ((X > 0) | (Y > 0) | (Z > 0)) & ~(np.isnan(X) | np.isnan(Y) | np.isnan(Z) | (X == -1) | (Y == -1) | (Z == -1))
    meta = json.load(open(os.path.join(d, 'meta.json'))) if os.path.exists(os.path.join(d, 'meta.json')) else {}
    scale = meta.get('scale', [0.05, 0.05])
    P = np.stack([X, Y, Z], -1); P[~valid] = np.nan
    return {'kind': 'tifxyz', 'path': d, 'P': P, 'valid': valid, 'scale': [float(scale[0]), float(scale[1])], 'meta': meta}

def load_obj(path):
    V, VT, F, FT = [], [], [], []
    for line in open(path):
        t = line.split()
        if not t: continue
        if t[0] == 'v': V.append([float(x) for x in t[1:4]])
        elif t[0] == 'vt': VT.append([float(x) for x in t[1:3]])
        elif t[0] == 'f':
            idx = [c.split('/') for c in t[1:]]
            vi = [int(c[0]) - 1 for c in idx]; ti = [int(c[1]) - 1 if len(c) > 1 and c[1] else -1 for c in idx]
            for a in range(1, len(vi) - 1): F.append([vi[0], vi[a], vi[a + 1]]); FT.append([ti[0], ti[a], ti[a + 1]])
    V = np.asarray(V, np.float64); F = np.asarray(F, np.int64); FT = np.asarray(FT, np.int64); VT = np.asarray(VT, np.float64) if VT else None
    UV = None
    if VT is not None and FT.size and (FT >= 0).all():
        UV = np.full((len(V), 2), np.nan); UV[F.ravel()] = VT[FT.ravel()]            # per-vertex uv (last write wins on seams)
    return {'kind': 'obj', 'path': path, 'V': V, 'F': F, 'UV': UV}

def load_mesh(path):
    return load_tifxyz(path) if os.path.isdir(path) else load_obj(path)

def grid_to_mesh(P, valid):
    """Grid -> (V (n,3), F (m,3), vid (H,W) int (-1 invalid), ij (n,2)). Quads with 4 valid corners -> 2 triangles
    (diagonal (i,j)-(i+1,j+1)); quads with exactly 3 valid corners -> 1 triangle. Consistent orientation."""
    H, W = valid.shape; vid = np.full((H, W), -1, np.int64); n = int(valid.sum()); vid[valid] = np.arange(n)
    ij = np.argwhere(valid); V = P[valid]
    a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, 1:], vid[1:, :-1]          # a=(i,j) b=(i,j+1) c=(i+1,j+1) d=(i+1,j)
    va, vb, vc, vd = a >= 0, b >= 0, c >= 0, d >= 0; four = va & vb & vc & vd
    tris = [np.stack([a[four], b[four], c[four]], 1), np.stack([a[four], c[four], d[four]], 1)]
    for m, (p, q, r) in [(va & vb & vc & ~vd, (a, b, c)), (va & vc & vd & ~vb, (a, c, d)), (va & vb & vd & ~vc, (a, b, d)), (vb & vc & vd & ~va, (b, c, d))]:
        if m.any(): tris.append(np.stack([p[m], q[m], r[m]], 1))
    F = np.concatenate(tris, 0) if tris else np.zeros((0, 3), np.int64)
    return V, F, vid, ij

def mesh_arrays(m, normal_smooth=0):
    """Any loaded mesh -> V, F plus per-vertex normals N (grid: du x dv like tools/fl4/sheetcheck.py; obj: area-weighted)."""
    if m['kind'] == 'tifxyz':
        V, F, vid, ij = grid_to_mesh(m['P'], m['valid']); m['vid'], m['ij'] = vid, ij
        P = m['P']; Pf = np.where(np.isnan(P), 0, P)
        du = np.gradient(Pf, axis=1); dv = np.gradient(Pf, axis=0); ng = np.cross(du, dv); ng[~m['valid']] = 0
        if normal_smooth > 0:                                                    # box average of unit normals over (2k+1)^2 valid cells
            from scipy.ndimage import uniform_filter
            u = ng / np.maximum(np.linalg.norm(ng, axis=-1, keepdims=True), 1e-12); u[~m['valid']] = 0; w = 2 * int(normal_smooth) + 1
            ng = np.stack([uniform_filter(u[..., c], w, mode='constant') for c in range(3)], -1)
        n = ng[m['valid']]
    else:
        V, F = m['V'], m['F']; fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); n = np.zeros_like(V)
        for k in range(3): np.add.at(n, F[:, k], fn)
    nn = np.linalg.norm(n, axis=-1); N = n / np.maximum(nn, 1e-12)[:, None]; N[nn == 0] = np.nan
    m['V'], m['F'], m['N'] = V, F, N
    return V, F, N

# ------------------------------------------------------------------------------------------- triangle-triangle tests
def _expand_ranges(starts, ends):
    """Concatenate ranges [s,e) vectorised: returns (values, owner index of each value)."""
    cnt = ends - starts; tot = int(cnt.sum())
    if tot == 0: return np.zeros(0, np.int64), np.zeros(0, np.int64)
    owner = np.repeat(np.arange(len(cnt)), cnt); off = np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    return np.repeat(starts, cnt) + off, owner

def _grid_cells(lo, hi, origin, h, dims):
    """Cells covered by each AABB (lo, hi) (n,3) on a uniform grid -> (cell linear ids, owner tri)."""
    c0 = np.floor((lo - origin) / h).astype(np.int64); c1 = np.floor((hi - origin) / h).astype(np.int64)
    c0 = np.clip(c0, 0, dims - 1); c1 = np.clip(c1, 0, dims - 1); nx, ny, nz = (c1 - c0 + 1).T
    xs, ox = _expand_ranges(c0[:, 0], c1[:, 0] + 1)                       # x cells per tri
    ys, oy = _expand_ranges(c0[ox, 1], c1[ox, 1] + 1); xs = xs[oy]; ox = ox[oy]
    zs, oz = _expand_ranges(c0[ox, 2], c1[ox, 2] + 1); xs = xs[oz]; ys = ys[oz]; ox = ox[oz]
    lin = (xs * dims[1] + ys) * dims[2] + zs
    return lin, ox

def _coplanar_overlap(A, B, eps=1e-9):
    """2-D triangle overlap (separating axis) for coplanar pairs; A,B (n,3,3). Projects on the dominant normal axis."""
    n = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]); ax = np.argmax(np.abs(n), 1)
    keep = np.array([[1, 2], [0, 2], [0, 1]])[ax]                                   # (n,2) axes kept
    A2 = np.take_along_axis(A, keep[:, None, :], 2); B2 = np.take_along_axis(B, keep[:, None, :], 2)
    sep = np.zeros(len(A), bool)
    for T, U in ((A2, B2), (B2, A2)):
        for k in range(3):
            e = T[:, (k + 1) % 3] - T[:, k]; nrm = np.stack([-e[:, 1], e[:, 0]], 1)
            pt = ((T - T[:, k:k + 1]) * nrm[:, None]).sum(2); pu = ((U - T[:, k:k + 1]) * nrm[:, None]).sum(2)
            sc = np.linalg.norm(nrm, axis=1) + 1e-300
            sep |= (pu.max(1) <= pt.min(1) + eps * sc) | (pu.min(1) >= pt.max(1) - eps * sc)
    return ~sep

def tri_tri_pairs_intersect(TA, TB, rel_eps=1e-9):
    """Exact Moller (1997) interval test for candidate pairs TA,TB (n,3,3). A pair intersects when each triangle has vertices
    strictly on both sides of the other's plane (so same-side touching, vertex-on-face and edge-on-edge contacts are NOT
    counted) and the two intervals on the intersection line overlap with positive length; coplanar pairs use a 2-D
    separating-axis overlap. Returns (hit bool (n,), point (n,3) = midpoint of the overlap interval)."""
    n = len(TA); hit = np.zeros(n, bool); pt = np.full((n, 3), np.nan)
    nA = np.cross(TA[:, 1] - TA[:, 0], TA[:, 2] - TA[:, 0]); nB = np.cross(TB[:, 1] - TB[:, 0], TB[:, 2] - TB[:, 0])
    diam = np.maximum(np.linalg.norm(TA.max(1) - TA.min(1), axis=1), np.linalg.norm(TB.max(1) - TB.min(1), axis=1)) + 1e-300
    dB = ((TB - TA[:, 0:1]) * nA[:, None]).sum(2); dA = ((TA - TB[:, 0:1]) * nB[:, None]).sum(2)          # (n,3) signed, unnormalised
    eA = rel_eps * np.linalg.norm(nA, axis=1) * diam + 1e-300; eB = rel_eps * np.linalg.norm(nB, axis=1) * diam + 1e-300
    dB = np.where(np.abs(dB) < eA[:, None], 0.0, dB); dA = np.where(np.abs(dA) < eB[:, None], 0.0, dA)
    cop = (dB == 0).all(1) & (dA == 0).all(1)
    both = ((dB > 0).any(1) & (dB < 0).any(1)) & ((dA > 0).any(1) & (dA < 0).any(1))
    if both.any():
        idx = np.where(both)[0]; A, B, da, db = TA[idx], TB[idx], dA[idx], dB[idx]
        D = np.cross(nA[idx], nB[idx]); k = np.argmax(np.abs(D), 1); pA = np.take_along_axis(A, k[:, None, None], 2)[:, :, 0]; pB = np.take_along_axis(B, k[:, None, None], 2)[:, :, 0]
        def interval(p, d):
            d0, d1, d2 = d.T
            alone = np.select([d0 * d1 > 0, d0 * d2 > 0, d1 * d2 > 0, d0 != 0, d1 != 0], [2, 1, 0, 0, 1], 2)
            j1 = (alone + 1) % 3; j2 = (alone + 2) % 3; r = np.arange(len(d))
            pa, da_ = p[r, alone], d[r, alone]
            t1 = pa + (p[r, j1] - pa) * da_ / (da_ - d[r, j1]); t2 = pa + (p[r, j2] - pa) * da_ / (da_ - d[r, j2])
            return np.minimum(t1, t2), np.maximum(t1, t2)
        a0, a1 = interval(pA, da); b0, b1 = interval(pB, db); lo = np.maximum(a0, b0); hi = np.minimum(a1, b1)
        ov = hi - lo > rel_eps * diam[idx]; sel = idx[ov]; hit[sel] = True
        # point: the overlap midpoint on the intersection line, reconstructed on A's plane along the crossing edge of B
        mid = (lo[ov] + hi[ov]) / 2; Bo, dbo, ko = B[ov], db[ov], k[ov]
        d0, d1, d2 = dbo.T; alone = np.select([d0 * d1 > 0, d0 * d2 > 0, d1 * d2 > 0, d0 != 0, d1 != 0], [2, 1, 0, 0, 1], 2); r = np.arange(len(Bo)); j1 = (alone + 1) % 3
        pa = Bo[r, alone]; p1 = Bo[r, j1]; w = dbo[r, alone] / (dbo[r, alone] - dbo[r, j1]); q = pa + (p1 - pa) * w[:, None]       # a point of B on plane A
        line = np.cross(nA[sel], nB[sel]); line /= np.maximum(np.linalg.norm(line, axis=1, keepdims=True), 1e-300)
        qk = np.take_along_axis(q, ko[:, None], 1)[:, 0]; lk = np.take_along_axis(line, ko[:, None], 1)[:, 0]
        pt[sel] = q + ((mid - qk) / np.where(np.abs(lk) < 1e-300, 1e-300, lk))[:, None] * line
    if cop.any():
        idx = np.where(cop)[0]; ov = _coplanar_overlap(TA[idx], TB[idx]); sel = idx[ov]; hit[sel] = True; pt[sel] = (TA[sel].mean(1) + TB[sel].mean(1)) / 2
    return hit, pt

def candidate_pairs(V1, F1, V2=None, F2=None, cell=None):
    """Uniform-grid broadphase. Returns int pairs (n,2): (tri of mesh1, tri of mesh2) with overlapping AABBs; self mode if V2 is None."""
    T1 = V1[F1]; lo1, hi1 = T1.min(1), T1.max(1); selfmode = V2 is None
    if selfmode: lo2, hi2 = lo1, hi1
    else: T2 = V2[F2]; lo2, hi2 = T2.min(1), T2.max(1)
    if cell is None: cell = 2.0 * max(float(np.median((hi1 - lo1).max(1))), 1e-6)
    origin = np.minimum(lo1.min(0), lo2.min(0)) - 1e-6; top = np.maximum(hi1.max(0), hi2.max(0)) + 1e-6
    dims = np.maximum(np.ceil((top - origin) / cell).astype(np.int64), 1)
    c1, o1 = _grid_cells(lo1, hi1, origin, cell, dims); order = np.argsort(c1, kind='stable'); c1s, o1s = c1[order], o1[order]
    c2, o2 = _grid_cells(lo2, hi2, origin, cell, dims)
    s = np.searchsorted(c1s, c2, 'left'); e = np.searchsorted(c1s, c2, 'right'); vals, own = _expand_ranges(s, e)
    pairs = np.stack([o1s[vals], o2[own]], 1)
    if selfmode: pairs = pairs[pairs[:, 0] < pairs[:, 1]]
    if len(pairs) == 0: return pairs.reshape(0, 2)
    pairs = np.unique(pairs, axis=0)
    ok = (lo1[pairs[:, 0]] <= hi2[pairs[:, 1]]).all(1) & (hi1[pairs[:, 0]] >= lo2[pairs[:, 1]]).all(1)
    return pairs[ok]

def intersections(V1, F1, V2=None, F2=None, batch=400000):
    """Self-intersection (V2 None; triangles sharing a vertex are excluded) or crossing test between two meshes.
    Returns dict with the number of intersecting pairs, the pairs, hit points, and broadphase counts."""
    t0 = time.time(); pairs = candidate_pairs(V1, F1, V2, F2); selfmode = V2 is None
    if selfmode:
        fa, fb = F1[pairs[:, 0]], F1[pairs[:, 1]]; shared = (fa[:, :, None] == fb[:, None, :]).any((1, 2)); pairs = pairs[~shared]
    hits = []; pts = []
    for s in range(0, len(pairs), batch):
        p = pairs[s:s + batch]; TA = V1[F1[p[:, 0]]]; TB = (V1[F1[p[:, 1]]] if selfmode else V2[F2[p[:, 1]]])
        h, q = tri_tri_pairs_intersect(TA, TB); hits.append(p[h]); pts.append(q[h])
    hp = np.concatenate(hits, 0) if hits else np.zeros((0, 2), np.int64); pp = np.concatenate(pts, 0) if pts else np.zeros((0, 3))
    return {'mode': 'self' if selfmode else 'cross', 'n_tri_1': int(len(F1)), 'n_tri_2': int(len(F1) if selfmode else len(F2)),
            'candidate_pairs': int(len(pairs)), 'intersecting_pairs': int(len(hp)), 'pairs': hp, 'points': pp, 'secs': round(time.time() - t0, 2)}

def mesh_min_distance(V1, V2, sample=200000):
    """Nearest vertex-to-vertex distance between two meshes (a sanity number next to a crossing test; not a bar)."""
    rng = np.random.default_rng(0); a = V1 if len(V1) <= sample else V1[rng.choice(len(V1), sample, replace=False)]
    d, _ = cKDTree(V2).query(a); return {'min': float(d.min()), 'median': float(np.median(d)), 'p95': float(np.percentile(d, 95))}

# ---------------------------------------------------------------------------------------------------------- stretch
def arclength_uv(P, valid, scale):
    """Rectilinear arc-length uv of a tifxyz grid: u(j) = cumulative median 3-D length of column steps over valid rows,
    v(i) likewise over rows; a step with no valid pair falls back to the nominal 1/scale voxels. Returns UV (H,W,2)."""
    H, W = valid.shape; nom_u, nom_v = 1.0 / scale[0], 1.0 / scale[1]
    def steps(axis, nom):
        if axis == 1: d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1); ok = valid[:, 1:] & valid[:, :-1]; red = 0
        else: d = np.linalg.norm(P[1:] - P[:-1], axis=-1); ok = valid[1:] & valid[:-1]; red = 1
        d = np.where(ok, d, np.nan)
        with np.errstate(all='ignore'):
            import warnings; warnings.simplefilter('ignore', RuntimeWarning); med = np.nanmedian(d, axis=red) if ok.any() else np.full(d.shape[1 - red], np.nan)
        return np.where(np.isfinite(med), med, nom)
    du = steps(1, nom_u); dv = steps(0, nom_v)
    u = np.concatenate([[0.0], np.cumsum(du)]); v = np.concatenate([[0.0], np.cumsum(dv)])
    return np.stack(np.meshgrid(u, v), -1), {'median_step_u': float(np.median(du)), 'median_step_v': float(np.median(dv)), 'nominal_step': [nom_u, nom_v]}

def triangle_stretch(V, F, UV):
    """Per-triangle Jacobian of the uv->3-D map: singular values s1>=s2, area ratio A3d/Auv = s1*s2, conformal ratio
    s1/s2, L2 stretch sqrt((s1^2+s2^2)/2), and the maximum interior-angle deviation (deg) between the uv and 3-D triangle."""
    p0, p1, p2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]; q0, q1, q2 = UV[F[:, 0]], UV[F[:, 1]], UV[F[:, 2]]
    E = np.stack([p1 - p0, p2 - p0], 2); e = np.stack([q1 - q0, q2 - q0], 2)                     # (n,3,2), (n,2,2)
    det = e[:, 0, 0] * e[:, 1, 1] - e[:, 0, 1] * e[:, 1, 0]; ok = np.abs(det) > 1e-12
    inv = np.zeros_like(e); inv[ok, 0, 0] = e[ok, 1, 1] / det[ok]; inv[ok, 1, 1] = e[ok, 0, 0] / det[ok]
    inv[ok, 0, 1] = -e[ok, 0, 1] / det[ok]; inv[ok, 1, 0] = -e[ok, 1, 0] / det[ok]
    J = E @ inv; M = np.einsum('nij,nik->njk', J, J); tr = M[:, 0, 0] + M[:, 1, 1]; dt = M[:, 0, 0] * M[:, 1, 1] - M[:, 0, 1] ** 2
    disc = np.sqrt(np.maximum(tr ** 2 / 4 - dt, 0)); s1 = np.sqrt(np.maximum(tr / 2 + disc, 0)); s2 = np.sqrt(np.maximum(tr / 2 - disc, 0))
    def angles(a, b, c):
        out = []
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            u, w = y - x, z - x; cs = (u * w).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(w, axis=1), 1e-300)
            out.append(np.degrees(np.arccos(np.clip(cs, -1, 1))))
        return np.stack(out, 1)
    ang = np.abs(angles(p0, p1, p2) - angles(q0, q1, q2)).max(1)
    A3 = 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1); A2 = 0.5 * np.abs(det)
    r = {'s1': s1, 's2': s2, 'area_ratio': s1 * s2, 'conformal': s1 / np.maximum(s2, 1e-300), 'L2': np.sqrt((s1 ** 2 + s2 ** 2) / 2), 'angle_dev_deg': ang, 'area3d': A3, 'areauv': A2, 'ok': ok}
    return r

def stretch_summary(r):
    ok = r['ok'] & np.isfinite(r['s1']) & np.isfinite(r['s2']) & (r['s2'] > 0)
    def mp(x): x = x[ok]; return {'median': float(np.median(x)), 'p95': float(np.percentile(x, 95)), 'max': float(x.max())} if x.size else None
    ar = r['area_ratio']; sym = np.maximum(ar, 1 / np.maximum(ar, 1e-300))
    return {'n_tri': int(ok.sum()), 'n_degenerate_uv': int((~ok).sum()),
            'area_ratio': mp(ar), 'area_stretch_sym(max(r,1/r))': mp(sym), 'abs_log_area_ratio': mp(np.abs(np.log(np.maximum(ar, 1e-300)))),
            'conformal_s1_over_s2': mp(r['conformal']), 'L2_stretch': mp(r['L2']), 's1': mp(r['s1']), 's2': mp(r['s2']), 'angle_dev_deg': mp(r['angle_dev_deg']),
            'area_weighted_L2sq': float((r['L2'][ok] ** 2 * r['areauv'][ok]).sum() / max(r['areauv'][ok].sum(), 1e-300)),
            'total_area_3d_vox2': float(r['area3d'][ok].sum()), 'total_area_uv_vox2': float(r['areauv'][ok].sum())}

# --------------------------------------------------------------------------------------------------------------- W3
class ChunkStore:
    """RAM cache of level-0 128^3 chunks keyed (ci,cj,ck) in (z,y,x) order, filled through an L0-like .slab(y0,n,z0,z1,x0,x1)."""
    def __init__(self, src):
        self.src = src; self.cz, self.cy, self.cx = src.chunks; self.Z, self.Y, self.X = src.shape; self.store = {}; self.bytes = 0; self.fetch_secs = 0.0; self.missing = 0
        self.arr = np.zeros((64, self.cz, self.cy, self.cx), np.uint8); self.keys = np.zeros(64, np.int64); self.n = 0      # chunk slots (grown by doubling)
        self.dims = (-(-self.Z // self.cz), -(-self.Y // self.cy), -(-self.X // self.cx))
    def lin(self, ci, cj, ck): return (ci * self.dims[1] + cj) * self.dims[2] + ck
    def _put(self, key, chunk):
        if self.n == len(self.keys):
            self.arr = np.concatenate([self.arr, np.zeros_like(self.arr)], 0); self.keys = np.concatenate([self.keys, np.zeros_like(self.keys)])
        self.arr[self.n] = chunk; self.keys[self.n] = key; self.store[key] = self.n; self.n += 1; self.bytes += chunk.nbytes
    def ensure(self, lin_ids):
        need = sorted(set(int(l) for l in np.unique(lin_ids)) - set(self.store)); t0 = time.time()
        if not need: return 0
        # group by (ci,cj), runs of contiguous ck -> one slab call each (L0.slab fetches the run's chunks threaded)
        trip = [(l // (self.dims[1] * self.dims[2]), (l // self.dims[2]) % self.dims[1], l % self.dims[2]) for l in need]
        trip.sort(); i = 0
        while i < len(trip):
            ci, cj, k0 = trip[i]; j = i
            while j + 1 < len(trip) and trip[j + 1][0] == ci and trip[j + 1][1] == cj and trip[j + 1][2] == trip[j][2] + 1: j += 1
            k1 = trip[j][2]; z0, y0, x0 = ci * self.cz, cj * self.cy, k0 * self.cx
            slab, info = self.src.slab(y0, self.cy, z0, z0 + self.cz, x0, (k1 + 1) * self.cx)       # (y, z, x)
            self.missing += info.get('of', 0) - info.get('chunks', 0)
            for k in range(k0, k1 + 1):
                a = slab[:, :, (k - k0) * self.cx:(k - k0 + 1) * self.cx]
                if a.shape[2] < self.cx or a.shape[0] < self.cy or a.shape[1] < self.cz:                 # edge chunk: pad
                    b = np.zeros((self.cy, self.cz, self.cx), np.uint8); b[:a.shape[0], :a.shape[1], :a.shape[2]] = a; a = b
                self._put(self.lin(ci, cj, k), a.transpose(1, 0, 2))
            i = j + 1
        self.fetch_secs += time.time() - t0; return len(need)
    def sample(self, pts):
        """Trilinear sample of (n,3) points given as (x,y,z) level-0 coordinates -> float32 in 0..1 (0 outside the volume/missing)."""
        zyx = pts[:, ::-1]; f = np.floor(zyx); fr = (zyx - f).astype(np.float32); i0 = f.astype(np.int64)
        out = np.zeros(len(pts), np.float32); lin_all = []
        corners = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)]
        idx = [i0 + np.array(cn) for cn in corners]
        for ii in idx:
            inside = (ii >= 0).all(1) & (ii[:, 0] < self.Z) & (ii[:, 1] < self.Y) & (ii[:, 2] < self.X)
            lin_all.append(self.lin(ii[:, 0] // self.cz, ii[:, 1] // self.cy, ii[:, 2] // self.cx)[inside])
        self.ensure(np.concatenate(lin_all))
        order = np.argsort(self.keys[:self.n]); skeys = self.keys[:self.n][order]
        for cn, ii in zip(corners, idx):
            w = np.prod(np.where(np.array(cn)[None, :] == 1, fr, 1 - fr), 1)
            inside = (ii >= 0).all(1) & (ii[:, 0] < self.Z) & (ii[:, 1] < self.Y) & (ii[:, 2] < self.X)
            val = np.zeros(len(pts), np.float32)
            if self.n:
                l = self.lin(ii[:, 0] // self.cz, ii[:, 1] // self.cy, ii[:, 2] // self.cx); pos = np.clip(np.searchsorted(skeys, l), 0, self.n - 1); have = inside & (skeys[pos] == l)
                if have.any(): val[have] = self.arr[order[pos[have]], ii[have, 0] % self.cz, ii[have, 1] % self.cy, ii[have, 2] % self.cx]
            out += w * val / 255.0
        return out

class NpyVolume:
    """In-memory (z,y,x) uint8 volume with the L0 interface (shape, chunks, slab) for the self-test."""
    def __init__(self, vol, chunk=128):
        self.vol = vol; self.shape = list(vol.shape); self.chunks = [chunk] * 3; self.calls = 0
    def slab(self, y0, n, z0, z1, x0, x1):
        Z, Y, X = self.shape; z1, x1 = min(z1, Z), min(x1, X); self.calls += 1
        a = self.vol[z0:z1, y0:y0 + n, x0:x1].transpose(1, 0, 2).copy()
        cz, cy, cx = self.chunks; keys = len(range(z0 // cz, (z1 - 1) // cz + 1)) * len(range(y0 // cy, (y0 + n - 1) // cy + 1)) * len(range(x0 // cx, (x1 - 1) // cx + 1))
        return a, {'chunks': keys, 'of': keys, 'secs': 0.0, 'MB': round(a.nbytes / 1e6)}

def w3_clearance(V, N, store, half=80, step=1.0, sigma=1.0, own_tol=8.0, peak_width=3, tube=2, batch=600):
    """For every vertex: raw-CT profile along the vertex normal, t in [-half, half] (voxels); peaks = find_peaks with
    prominence >= 3 MAD of the in-mask profile (MAD + 1e-6, core_native convention) and width >= peak_width; the vertex's
    own lamina = the peak nearest t=0 within own_tol (else OFF_LAMINA); clearance_plus/minus = distance from the vertex
    (t=0) to the nearest other peak with t > t_own / t < t_own; local spacing = (t_plus - t_minus)/2 when both exist,
    else |t_side - t_own| (ONE_SIDED, the missing side censored at `half`); ratio = min(clearance)/spacing.
    Each profile sample is the mean over the integer lattice disc of radius `tube` voxels in the tangent plane
    (13 points for tube=2, i.e. a 17 um tube), the native-resolution analogue of core_native's 16-section average.
    Returns per-vertex arrays and the W3 bar numbers (>= 0.5 x spacing for >= 98 % of vertices; < 0.3 masked)."""
    n = len(V); ts = np.arange(-half, half + 1e-9, step); m = len(ts)
    cp = np.full(n, np.nan); cm = np.full(n, np.nan); sp = np.full(n, np.nan); own = np.full(n, np.nan); npk = np.zeros(n, np.int16)
    status = np.full(n, 'NO_NORMAL', dtype='<U12'); mad_all = np.full(n, np.nan); inmask = np.zeros(n, np.float32)
    rr = int(np.ceil(tube)); disc = np.array([(a, b) for a in range(-rr, rr + 1) for b in range(-rr, rr + 1) if a * a + b * b <= tube * tube], float).reshape(-1, 2); nd = len(disc)
    for s in range(0, n, batch):
        sl = slice(s, min(s + batch, n)); Vb, Nb = V[sl], N[sl]; okn = np.isfinite(Nb).all(1); Nz = np.where(okn[:, None], np.nan_to_num(Nb), 0.0)
        arb = np.where(np.abs(Nz[:, 0:1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]])); e1 = np.cross(Nz, arb); e1 /= np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12); e2 = np.cross(Nz, e1)
        off = disc[:, 0, None] * e1[:, None, :] + disc[:, 1, None] * e2[:, None, :]                                   # (nb, k, 3)
        pts = (Vb[:, None, None, :] + ts[None, :, None, None] * Nz[:, None, None, :] + off[:, None, :, :]).reshape(-1, 3)
        prof = store.sample(pts).reshape(len(Vb), m, nd).mean(2)
        for r in range(len(Vb)):
            i = s + r
            if not okn[r]: continue
            p = prof[r]; mk = p > 0; inmask[i] = mk.mean()
            if mk.sum() < 0.5 * m: status[i] = 'OUT_OF_MASK'; continue
            q = gaussian_filter1d(p, sigma) if sigma > 0 else p
            mad = float(np.median(np.abs(q[mk] - np.median(q[mk]))) + 1e-6); mad_all[i] = mad
            pk, _ = find_peaks(np.where(mk, q, 0), prominence=3 * mad, width=peak_width); tp = ts[pk]; npk[i] = len(pk)
            if len(pk) == 0: status[i] = 'NO_PEAKS'; continue
            k = int(np.argmin(np.abs(tp)))
            if abs(tp[k]) > own_tol:
                status[i] = 'OFF_LAMINA'; plus = tp[tp > 0]; minus = tp[tp < 0]
                cp[i] = plus.min() if plus.size else np.nan; cm[i] = -minus.max() if minus.size else np.nan; continue
            own[i] = tp[k]; plus = tp[tp > tp[k]]; minus = tp[tp < tp[k]]
            cp[i] = plus.min() if plus.size else np.nan; cm[i] = -minus.max() if minus.size else np.nan
            if plus.size and minus.size: sp[i] = (plus.min() - minus.max()) / 2; status[i] = 'OK'
            elif plus.size: sp[i] = plus.min() - tp[k]; status[i] = 'ONE_SIDED'
            elif minus.size: sp[i] = tp[k] - minus.max(); status[i] = 'ONE_SIDED'
            else: status[i] = 'ISOLATED'
    cmin = np.fmin(np.where(np.isnan(cp), half, cp), np.where(np.isnan(cm), half, cm)); ratio = cmin / sp
    near = np.where(np.isfinite(own), np.abs(own), np.fmin(np.where(np.isnan(cp), np.inf, cp), np.where(np.isnan(cm), np.inf, cm)))   # vertex -> nearest peak, any status
    near_f = near[np.isfinite(near)]
    meas = status == 'OK'; ones = status == 'ONE_SIDED'; valid = meas | ones
    frac = lambda m_: float(m_.sum() / max(n, 1))
    bar = {'n_vertices': int(n), 'status_counts': {k: int((status == k).sum()) for k in np.unique(status)},
           'frac_ratio_ge_0.5_of_all_vertices': frac(valid & (ratio >= 0.5)), 'frac_ratio_lt_0.3_masked_of_all': frac(~valid | (ratio < 0.3)),
           'frac_ratio_ge_0.5_of_measured(OK)': float((ratio[meas] >= 0.5).mean()) if meas.any() else None,
           'bar_W3_pass(>=0.98 of all vertices, OFF_LAMINA/NO_PEAKS/OUT_OF_MASK count as fail)': bool(frac(valid & (ratio >= 0.5)) >= 0.98),
           'clearance_plus_vox': _pct(cp), 'clearance_minus_vox': _pct(cm), 'clearance_min_vox': _pct(cmin[valid]), 'local_spacing_vox': _pct(sp[valid]),
           'local_spacing_um': _pct(sp[valid] * VOX_UM), 'ratio_min_clearance_over_spacing': _pct(ratio[valid]), 'own_peak_offset_vox': _pct(own),
           'n_peaks_per_profile': _pct(npk[valid].astype(float)), 'mad': _pct(mad_all), 'in_mask_fraction': _pct(inmask.astype(float)),
           'nearest_peak_distance_vox(all vertices with peaks, tolerance-free)': _pct(near_f),
           'frac_of_all_vertices_with_a_peak_within': {str(d): float((near_f <= d).sum() / max(n, 1)) for d in (4, 8, 12, 16, 24)},
           'params': {'half_vox': half, 'step': step, 'sigma_vox': sigma, 'own_tol_vox': own_tol, 'peak_width_vox': peak_width, 'tube_radius_vox': tube, 'tube_points': nd, 'prominence': '3 x MAD(profile in mask) + 1e-6'}}
    return {'clearance_plus': cp, 'clearance_minus': cm, 'spacing': sp, 'ratio': ratio, 'own_offset': own, 'n_peaks': npk, 'status': status}, bar

def _pct(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if x.size == 0: return None
    return {'n': int(x.size), 'p05': float(np.percentile(x, 5)), 'median': float(np.median(x)), 'p95': float(np.percentile(x, 95)), 'min': float(x.min()), 'max': float(x.max())}

# ------------------------------------------------------------------------------------------------------------ check
def open_volume(key, threads=3):
    sys.path.insert(0, os.path.join(HERE, '..', 'umb')); from core_native import L0
    return L0(key, threads=threads)

def run_check(mesh_path, out_dir, neighbour=None, w3=False, volume=DEFAULT_VOLUME, w3_half=80, w3_sigma=1.0, w3_own_tol=8.0, w3_window=None, w3_stride=1, save_vertex=False, store=None, tag=None, w3_tube=2, normal_smooth=0):
    os.makedirs(out_dir, exist_ok=True); t0 = time.time(); m = load_mesh(mesh_path); V, F, N = mesh_arrays(m, normal_smooth)
    rep = {'mesh': mesh_path, 'kind': m['kind'], 'n_vertices': int(len(V)), 'n_triangles': int(len(F)), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'vox_um': VOX_UM}
    if m['kind'] == 'tifxyz': rep['grid'] = list(m['valid'].shape); rep['valid_cells'] = int(m['valid'].sum()); rep['scale'] = m['scale']; rep['meta_target_volume'] = m['meta'].get('target_volume')
    bbox = [V.min(0).tolist(), V.max(0).tolist()]; rep['bbox_xyz'] = bbox
    # (1) self-intersection
    si = intersections(V, F); rep['self_intersection'] = {k: si[k] for k in ('n_tri_1', 'candidate_pairs', 'intersecting_pairs', 'secs')}
    rep['self_intersection']['bar_pass(0 intersections)'] = si['intersecting_pairs'] == 0
    if si['intersecting_pairs']:
        rep['self_intersection']['hit_points_xyz_sample'] = si['points'][:20].round(2).tolist(); rep['self_intersection']['hit_bbox'] = [si['points'].min(0).round(1).tolist(), si['points'].max(0).round(1).tolist()]
        inv = np.zeros(len(F), bool); inv[si['pairs'].ravel()] = True; rep['self_intersection']['frac_triangles_involved'] = float(inv.mean())
        if m['kind'] == 'tifxyz':
            ij = m['ij']; ca = ij[F[si['pairs'][:, 0]]].mean(1); cb = ij[F[si['pairs'][:, 1]]].mean(1); gd = np.abs(ca - cb).max(1)
            rep['self_intersection']['grid_distance_cells_between_intersecting_triangles'] = {'p05': float(np.percentile(gd, 5)), 'median': float(np.median(gd)), 'p95': float(np.percentile(gd, 95)), 'max': float(gd.max()),
                'frac_le_5_cells(local crumple)': float((gd <= 5).mean()), 'frac_gt_5_cells(fold-over)': float((gd > 5).mean())}
            rep['self_intersection']['grid_cells_involved_sample'] = ij[F[si['pairs'][:20].ravel()][:, 0]].tolist()
    # (1b) neighbour crossing
    if neighbour is not None:
        m2 = load_mesh(neighbour); V2, F2, _ = mesh_arrays(m2); cr = intersections(V, F, V2, F2)
        rep['neighbour_crossing'] = {'neighbour': neighbour, **{k: cr[k] for k in ('n_tri_1', 'n_tri_2', 'candidate_pairs', 'intersecting_pairs', 'secs')}, 'bar_pass(0 intersections)': cr['intersecting_pairs'] == 0,
                                     'vertex_distance_vox': mesh_min_distance(V, V2)}
        if cr['intersecting_pairs']: rep['neighbour_crossing']['hit_points_xyz_sample'] = cr['points'][:20].round(2).tolist(); rep['neighbour_crossing']['hit_bbox'] = [cr['points'].min(0).round(1).tolist(), cr['points'].max(0).round(1).tolist()]
    # (2) stretch
    if m['kind'] == 'tifxyz':
        UVa, info = arclength_uv(m['P'], m['valid'], m['scale']); UVn = np.stack(np.meshgrid(np.arange(m['valid'].shape[1]) / m['scale'][0], np.arange(m['valid'].shape[0]) / m['scale'][1]), -1)
        rep['stretch_arclength_uv'] = {**stretch_summary(triangle_stretch(V, F, UVa[m['valid']])), 'uv_steps': info}
        rep['stretch_nominal_grid_uv'] = stretch_summary(triangle_stretch(V, F, UVn[m['valid']]))
    elif m.get('UV') is not None and np.isfinite(m['UV']).all():
        rep['stretch_obj_vt_uv'] = stretch_summary(triangle_stretch(V, F, m['UV']))
    else: rep['stretch'] = 'no uv available (OBJ without vt)'
    # (3) W3
    if w3:
        sel = np.ones(len(V), bool)
        if m['kind'] == 'tifxyz' and w3_window:
            (i0, i1), (j0, j1) = [tuple(int(x) for x in part.split(':')) for part in w3_window.split(',')]; ij = m['ij']; sel &= (ij[:, 0] >= i0) & (ij[:, 0] < i1) & (ij[:, 1] >= j0) & (ij[:, 1] < j1)
        if w3_stride > 1 and m['kind'] == 'tifxyz': sel &= (m['ij'][:, 0] % w3_stride == 0) & (m['ij'][:, 1] % w3_stride == 0)
        if store is None:
            tv = m.get('meta', {}).get('target_volume') or ''
            scan_id = volume.split('/volumes/')[-1].split('/')[0].split('-')[0] if '/volumes/' in volume else None
            if tv and scan_id and not tv.startswith(scan_id): raise SystemExit(f'refusing W3: mesh meta target_volume {tv!r} does not share the scan id {scan_id!r} of --volume {volume}')
            store = ChunkStore(open_volume(volume, threads=3))
        per, bar = w3_clearance(V[sel], N[sel], store, half=w3_half, sigma=w3_sigma, own_tol=w3_own_tol, tube=w3_tube)
        bar['vertices_tested'] = int(sel.sum()); bar['window'] = w3_window; bar['stride'] = w3_stride; bar['normal_smooth_cells'] = normal_smooth
        bar['level0_chunks_fetched'] = store.n; bar['level0_MB_fetched'] = round(store.bytes / 1e6, 1); bar['fetch_secs'] = round(store.fetch_secs, 1); bar['chunks_missing'] = int(store.missing); bar['volume'] = getattr(store.src, 'key', 'in-memory')
        rep['W3_clearance'] = bar
        if save_vertex:
            np.savez_compressed(os.path.join(out_dir, (tag or 'mesh') + '_w3_vertex.npz'), xyz=V[sel].astype(np.float32), normal=N[sel].astype(np.float32), ij=(m['ij'][sel] if m['kind'] == 'tifxyz' else np.zeros((sel.sum(), 2), np.int32)),
                                **{k: (v if v.dtype.kind == 'U' else v.astype(np.float32)) for k, v in per.items()})
    rep['secs_total'] = round(time.time() - t0, 1)
    json.dump(rep, open(os.path.join(out_dir, (tag or 'mesh_checks') + '.json'), 'w'), indent=1, default=_json_default); return rep

def _json_default(o):
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(str(type(o)))

# ---------------------------------------------------------------------------------------------------------- selftest
def _sheet(fu, nu=60, nv=50, step=20.0, origin=(0, 0, 0)):
    """Synthetic tifxyz-like grid from parametric maps. Returns mesh dict like load_tifxyz (scale = 1/step)."""
    u = np.arange(nu) * step; v = np.arange(nv) * step; U, Vv = np.meshgrid(u, v); P = np.stack(fu(U, Vv), -1) + np.asarray(origin, float)
    return {'kind': 'tifxyz', 'path': 'synthetic', 'P': P.astype(np.float64), 'valid': np.ones(P.shape[:2], bool), 'scale': [1 / step, 1 / step], 'meta': {}}

def selftest(out_dir):
    os.makedirs(out_dir, exist_ok=True); R = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'tests': {}, 'deviations': []}; T = R['tests']
    def expect(name, cond, detail):
        T[name] = {'pass': bool(cond), **detail}
        if not cond: R['deviations'].append(name)
    step = 20.0
    # A. flat sheet with a mild ripple (inextensional in u, so arc-length uv is nearly isometric): 0 self-intersections
    flat = _sheet(lambda U, V: (U, V, 30 * np.sin(U / 300.0)), 60, 50, step, (1000, 1000, 1000)); Vf, Ff, Nf = mesh_arrays(flat)
    si = intersections(Vf, Ff); UVa, info = arclength_uv(flat['P'], flat['valid'], flat['scale']); st = stretch_summary(triangle_stretch(Vf, Ff, UVa[flat['valid']]))
    UVn = np.stack(np.meshgrid(np.arange(60) * step, np.arange(50) * step), -1); stn = stretch_summary(triangle_stretch(Vf, Ff, UVn[flat['valid']]))
    expect('A_flat_sheet_no_self_intersection', si['intersecting_pairs'] == 0, {'n_tri': si['n_tri_1'], 'candidate_pairs': si['candidate_pairs'], 'intersecting_pairs': si['intersecting_pairs'], 'secs': si['secs']})
    expect('A_flat_sheet_arclength_uv_near_isometric', st['area_stretch_sym(max(r,1/r))']['p95'] < 1.02 and st['angle_dev_deg']['p95'] < 2.0,
           {'arclength': {k: st[k] for k in ('area_ratio', 'conformal_s1_over_s2', 'angle_dev_deg')}, 'nominal_grid_uv_area_ratio': stn['area_ratio'], 'uv_steps': info,
            'note': 'the ripple stretches the nominal grid uv (area ratio > 1); the arc-length uv absorbs it along u'})
    # B. folded sheet that self-intersects: limacon r = 1 + 2 cos(theta) extruded along v; the inner loop crosses the outer loop at the origin
    th0, th1 = 0.3, 2 * np.pi - 0.3; nu = 90; scale_r = 300.0
    def limacon(U, V):
        th = th0 + (th1 - th0) * U / U.max(); r = scale_r * (1 + 2 * np.cos(th)); return (r * np.cos(th), V, r * np.sin(th))
    fold = _sheet(limacon, nu, 40, step, (3000, 1000, 3000)); Vl, Fl, _ = mesh_arrays(fold); si = intersections(Vl, Fl)
    hp = si['points']; near = (np.abs(hp[:, 0] - 3000) < 60) & (np.abs(hp[:, 2] - 3000) < 60) if len(hp) else np.zeros(0, bool)
    expect('B_folded_sheet_self_intersects_at_known_crossing', si['intersecting_pairs'] > 0 and near.all() and si['intersecting_pairs'] >= 39,
           {'intersecting_pairs': si['intersecting_pairs'], 'candidate_pairs': si['candidate_pairs'], 'hit_points_within_60vox_of_crossing_line': int(near.sum()), 'expected_min_pairs': 39, 'secs': si['secs'],
            'note': 'limacon inner loop crosses the outer loop along the line x=3000,z=3000 for all 40 rows; >= 1 pair per row expected'})
    # C. two parallel sheets 44 voxels apart: 0 crossings, nearest-vertex distance 44
    sa = _sheet(lambda U, V: (U, V, 0 * U), 60, 50, step, (1000, 1000, 2000)); sb = _sheet(lambda U, V: (U, V, 0 * U + 44), 60, 50, step, (1000, 1000, 2000))
    Va, Fa, Na = mesh_arrays(sa); Vb, Fb, _ = mesh_arrays(sb); cr = intersections(Va, Fa, Vb, Fb); md = mesh_min_distance(Va, Vb)
    expect('C_parallel_sheets_44vox_no_crossing', cr['intersecting_pairs'] == 0 and abs(md['min'] - 44) < 1e-6, {'intersecting_pairs': cr['intersecting_pairs'], 'candidate_pairs': cr['candidate_pairs'], 'vertex_distance': md, 'secs': cr['secs']})
    # D. two crossing sheets: C tilted through A along the line x = 1000 + 590 (between grid columns, so the crossing is transversal in every pair;
    #    a crossing exactly on a shared grid line is, pair by pair, the same as the touching case D2 and is deliberately not counted)
    sc = _sheet(lambda U, V: (U, V, 0.3 * (U - 590)), 60, 50, step, (1000, 1000, 2000)); Vc, Fc, _ = mesh_arrays(sc); cr = intersections(Va, Fa, Vc, Fc)
    hp = cr['points']; nearx = np.abs(hp[:, 0] - 1590) < 25 if len(hp) else np.zeros(0, bool)
    expect('D_crossing_sheets_detected_on_known_line', cr['intersecting_pairs'] > 0 and nearx.all() and cr['intersecting_pairs'] >= 49,
           {'intersecting_pairs': cr['intersecting_pairs'], 'candidate_pairs': cr['candidate_pairs'], 'hit_points_within_25vox_of_x1590': int(nearx.sum()), 'hit_x_range': [float(hp[:, 0].min()), float(hp[:, 0].max())] if len(hp) else None, 'secs': cr['secs']})
    # D2. touching-not-crossing: sheet whose edge ends exactly on sheet A (shares the plane along its boundary): must NOT count
    sd = _sheet(lambda U, V: (U, V, 0.3 * U), 60, 50, step, (1000, 1000, 2000)); Vd, Fd, _ = mesh_arrays(sd); cr2 = intersections(Va, Fa, Vd, Fd)
    expect('D2_sheet_touching_along_edge_not_counted', cr2['intersecting_pairs'] == 0, {'intersecting_pairs': cr2['intersecting_pairs'], 'candidate_pairs': cr2['candidate_pairs']})
    # D3. coplanar overlap: the same flat sheet shifted half a cell in its own plane (coplanar triangles overlap) must count
    se = _sheet(lambda U, V: (U, V, 0 * U), 60, 50, step, (1010, 1010, 2000)); Ve, Fe, _ = mesh_arrays(se); cr3 = intersections(Va, Fa, Ve, Fe)
    expect('D3_coplanar_overlap_counted', cr3['intersecting_pairs'] > 0, {'intersecting_pairs': cr3['intersecting_pairs'], 'candidate_pairs': cr3['candidate_pairs']})
    # E. OBJ round trip (with vt) of the flat sheet
    obj = os.path.join(out_dir, 'selftest_flat.obj')
    with open(obj, 'w') as f:
        for p in Vf: f.write('v %.4f %.4f %.4f\n' % tuple(p))
        for q in UVa[flat['valid']]: f.write('vt %.4f %.4f\n' % tuple(q))
        for t in Ff: f.write('f %d/%d %d/%d %d/%d\n' % (t[0] + 1, t[0] + 1, t[1] + 1, t[1] + 1, t[2] + 1, t[2] + 1))
    mo = load_obj(obj); Vo, Fo, _ = mesh_arrays(mo); sto = stretch_summary(triangle_stretch(Vo, Fo, mo['UV'])); os.remove(obj)
    expect('E_obj_roundtrip', len(Vo) == len(Vf) and len(Fo) == len(Ff) and abs(sto['area_ratio']['median'] - st['area_ratio']['median']) < 1e-3, {'n_v': len(Vo), 'n_f': len(Fo), 'area_ratio_median_obj': sto['area_ratio']['median']})
    # F. W3 on a synthetic laminae volume: planar laminae at z = 40 + 44 k (Gaussian sigma 4 vox = 81 um FWHM, amplitude 150/255 on a 40/255 ash
    #    background, noise sigma 10/255), 300 x 300 x 300, chunk 128 (so the probes cross chunk boundaries); meshes: on lamina k=3
    #    (expect clearance 44/44, ratio 1), offset +5 vox (expect 39/49, ratio 39/44 = 0.886, own peak at -5), midway +22 (OFF_LAMINA, 22/22)
    rng = np.random.default_rng(7); Zs = 300; z = np.arange(Zs, dtype=float); prof = 40 + 150 * sum(np.exp(-0.5 * ((z - (40 + 44 * k)) / 4.0) ** 2) for k in range(6))
    vol = np.clip(prof[:, None, None] + rng.normal(0, 10, (Zs, 300, 300)), 0, 255).astype(np.uint8); store = ChunkStore(NpyVolume(vol))
    z3 = 40 + 44 * 3; res = {}
    for name, dz, exp in (('on_lamina', 0.0, (44, 44, 1.0, 'OK')), ('offset_5', 5.0, (39, 49, 39 / 44, 'OK')), ('midway_22', 22.0, (22, 22, None, 'OFF_LAMINA'))):
        sh = _sheet(lambda U, V, dz=dz: (U, V, 0 * U + z3 + dz), 12, 12, step, (30, 30, 0)); Vs, Fs, Ns = mesh_arrays(sh); per, bar = w3_clearance(Vs, Ns, store, half=80, sigma=1.0, own_tol=8.0)
        st_ = bar['status_counts']; mcp, mcm = np.nanmedian(per['clearance_plus']), np.nanmedian(per['clearance_minus']); mr = np.nanmedian(per['ratio']) if exp[2] is not None else None
        ok = st_.get(exp[3], 0) == len(Vs) and abs(min(mcp, mcm) - exp[0]) <= 1.5 and abs(max(mcp, mcm) - exp[1]) <= 1.5 and (exp[2] is None or abs(mr - exp[2]) < 0.05)
        res[name] = {'pass': bool(ok), 'status_counts': st_, 'median_clearance_plus': float(mcp), 'median_clearance_minus': float(mcm), 'median_ratio': (float(mr) if mr is not None else None), 'median_spacing': (float(np.nanmedian(per['spacing'])) if np.isfinite(per['spacing']).any() else None),
                     'median_own_offset': (float(np.nanmedian(per['own_offset'])) if np.isfinite(per['own_offset']).any() else None), 'expected': {'clearance_min': exp[0], 'clearance_max': exp[1], 'ratio': exp[2], 'status': exp[3]}, 'bar_pass': bar['bar_W3_pass(>=0.98 of all vertices, OFF_LAMINA/NO_PEAKS/OUT_OF_MASK count as fail)']}
    expect('F_W3_synthetic_laminae', all(r['pass'] for r in res.values()) and res['on_lamina']['bar_pass'] and not res['midway_22']['bar_pass'],
           {'cases': res, 'chunks_fetched': store.n, 'slab_calls': store.src.calls, 'MB': round(store.bytes / 1e6, 1), 'note': 'mesh normals point +z; prominence 3 MAD; laminae every 44 vox'})
    # F2. W3 on a tilted mesh (normal not axis-aligned) through the same laminae: clearance measured along the normal = 44 / cos(tilt) is NOT expected;
    #     the laminae are horizontal so the peak distance along a tilted normal is 44 / cos(theta); check the tool reports that (theta = 20 deg)
    th = np.radians(20.0); shz = _sheet(lambda U, V: (U * np.cos(th), V, z3 + U * np.sin(th)), 12, 12, step, (30, 30, 0)); Vz, Fz, Nz = mesh_arrays(shz)
    keep = np.abs(Vz[:, 2] - z3 - np.round((Vz[:, 2] - z3) / 44) * 44) < 1.0      # vertices that sit on a lamina (within 1 vox)
    per, bar = w3_clearance(Vz[keep], Nz[keep], store, half=80, sigma=1.0, own_tol=8.0); expct = 44 / np.cos(th)
    expect('F2_W3_tilted_normal_geometry', keep.sum() > 10 and abs(np.nanmedian(per['clearance_plus']) - expct) < 1.5 and abs(np.nanmedian(per['clearance_minus']) - expct) < 1.5,
           {'n_vertices_on_lamina': int(keep.sum()), 'expected_clearance_along_normal': float(expct), 'median_clearance_plus': float(np.nanmedian(per['clearance_plus'])), 'median_clearance_minus': float(np.nanmedian(per['clearance_minus'])), 'status_counts': bar['status_counts']})
    R['all_pass'] = not R['deviations']; json.dump(R, open(os.path.join(out_dir, 'selftest.json'), 'w'), indent=1, default=_json_default)
    for k, v in T.items(): print(('PASS ' if v['pass'] else 'FAIL '), k)
    print('all_pass', R['all_pass']); return R

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('selftest'); s.add_argument('out')
    c = sub.add_parser('check'); c.add_argument('mesh'); c.add_argument('out'); c.add_argument('--neighbour'); c.add_argument('--w3', action='store_true'); c.add_argument('--volume', default=DEFAULT_VOLUME)
    c.add_argument('--w3-half', type=float, default=80); c.add_argument('--w3-sigma', type=float, default=1.0); c.add_argument('--w3-own-tol', type=float, default=8.0); c.add_argument('--w3-window'); c.add_argument('--w3-stride', type=int, default=1)
    c.add_argument('--w3-tube', type=float, default=2); c.add_argument('--normal-smooth', type=int, default=0, help='box-average unit normals over (2k+1)^2 grid cells before the W3 probe'); c.add_argument('--save-vertex', action='store_true'); c.add_argument('--tag')
    a = ap.parse_args()
    if a.cmd == 'selftest': R = selftest(a.out); sys.exit(0 if R['all_pass'] else 1)
    rep = run_check(a.mesh, a.out, a.neighbour, a.w3, a.volume, a.w3_half, a.w3_sigma, a.w3_own_tol, a.w3_window, a.w3_stride, a.save_vertex, tag=a.tag, w3_tube=a.w3_tube, normal_smooth=a.normal_smooth)
    print(json.dumps({k: rep[k] for k in rep if k in ('self_intersection', 'neighbour_crossing', 'W3_clearance', 'secs_total')}, indent=1, default=_json_default))

if __name__ == '__main__': main()
