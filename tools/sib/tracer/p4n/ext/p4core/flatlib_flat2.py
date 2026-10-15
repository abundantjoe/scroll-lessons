# Provenance: Project HERCULES | owner the owner | [id removed]
# FLAT-2 tooling, VERBATIM copy (not modified) for DECL-P4-7 item 3 metric (d).
# source: origin/claude/gifted-bell-gavnl5-sib-flat1:tools/sib/flat1/flatlib.py
# source commit: 9f14b5334594539d85b263581ee0a901b8be8e20
# git blob sha1: 67f6785543a17b887f12cacbb82c1e608daad5df
# body sha256:   bc5056bf2f269153237942271473ede4def6beb4bca8792b9b8a83a6328d2d5b (17894 bytes)
# The body is every byte after the marker line below; its git blob sha1 and
# sha256 are checked by tests/sib_p4core_test_metrics.py.
# ---- BEGIN VERBATIM FLAT-2 flatlib.py ----
# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-1 library: flattening of tifxyz grid patches and distortion metrics.

Geometry only. No volume, no image, no ink model is touched here.

Conventions
-----------
* ``points[r, c] = (x, y, z)`` in voxels, invalid = (-1, -1, -1)
  (hercules.geometry.tifxyz). A quad (r, c) has corners (r, c), (r, c+1),
  (r+1, c), (r+1, c+1).
* Triangulation is the one the official ABF++ code uses
  (villa core/src/ABFFlattening.cpp, 41701aa): T1 = (p10, p00, p01),
  T2 = (p10, p01, p11), i.e. the p10-p01 diagonal. SLIM and ARAP get exactly
  the same triangles, so all three methods flatten the same mesh.
* ``uv`` grids are (H, W, 2) float64, NaN where undefined.

Main metric (FLAT-1, RULES.md DECL-FACTORY / DECL-SG item 10)
-------------------------------------------------------------
% of quads whose four edges all have flat length within +-tol of their 3-D
length. Before the ratios are taken the flattening is multiplied by ONE
global factor s = sqrt(A3 / A2) (3-D area over flat area, summed over the
evaluated triangles), so a method is not penalised for an arbitrary global
scale; the raw (s = 1) value is reported too. For SLIM and ARAP s is ~1 by
construction; vc_flatten already rescales to the 3-D area by default.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

SENTINEL = -1.0


# ---------------------------------------------------------------------------
# grid <-> triangle mesh
# ---------------------------------------------------------------------------

def valid_mask(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points)
    return np.all(np.isfinite(p), axis=-1) & ~np.any(p == SENTINEL, axis=-1)


def quad_mask(points: np.ndarray) -> np.ndarray:
    v = valid_mask(points)
    return v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]


@dataclass
class GridMesh:
    V: np.ndarray  # (n, 3) float64
    F: np.ndarray  # (m, 3) int64
    index: np.ndarray  # (H, W) int64 vertex index or -1
    quads: np.ndarray  # (H-1, W-1) bool, quads that were triangulated
    tri_quad: np.ndarray  # (m, 2) int (r, c) of the quad a triangle belongs to


def grid_to_mesh(points: np.ndarray, quads: np.ndarray | None = None) -> GridMesh:
    """Triangle mesh of the given quads (default: all quads with 4 valid
    corners). Only vertices used by a quad are kept."""
    p = np.asarray(points, dtype=np.float64)
    q = quad_mask(p) if quads is None else (np.asarray(quads, bool) & quad_mask(p))
    H, W = p.shape[:2]
    used = np.zeros((H, W), bool)
    used[:-1, :-1] |= q
    used[1:, :-1] |= q
    used[:-1, 1:] |= q
    used[1:, 1:] |= q
    index = np.full((H, W), -1, np.int64)
    index[used] = np.arange(int(used.sum()))
    V = p[used]
    qr, qc = np.nonzero(q)
    i00 = index[qr, qc]
    i01 = index[qr, qc + 1]
    i10 = index[qr + 1, qc]
    i11 = index[qr + 1, qc + 1]
    F = np.concatenate([np.stack([i10, i00, i01], 1), np.stack([i10, i01, i11], 1)], 0)
    tq = np.concatenate([np.stack([qr, qc], 1), np.stack([qr, qc], 1)], 0)
    return GridMesh(V=V, F=F.astype(np.int64), index=index, quads=q, tri_quad=tq)


def uv_to_grid(mesh: GridMesh, UV: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    uv = np.full((*shape, 2), np.nan)
    ok = mesh.index >= 0
    uv[ok] = np.asarray(UV, dtype=np.float64)[mesh.index[ok], :2]
    return uv


def grid_init_uv(mesh: GridMesh, step: float) -> np.ndarray:
    """(u, v) = (col, row) * step. A regular grid embedding: every triangle
    has the same positive orientation, so it is a flip-free initialisation."""
    rr, cc = np.nonzero(mesh.index >= 0)
    UV = np.zeros((mesh.V.shape[0], 2))
    UV[mesh.index[rr, cc]] = np.stack([cc * step, rr * step], 1)
    return UV


def tutte_init_uv(mesh: GridMesh) -> np.ndarray:
    """Tutte/harmonic embedding with the longest boundary loop on a circle
    of the same perimeter-derived radius (libigl), then rescaled to the 3-D
    area. Used only as a sensitivity check of the initialisation."""
    import igl

    F = np.ascontiguousarray(mesh.F, dtype=np.int64)
    bnd = igl.boundary_loop(F)
    bnd_uv = igl.map_vertices_to_circle(np.asfortranarray(mesh.V), np.ascontiguousarray(bnd, dtype=np.int32))
    UV = igl.harmonic(np.ascontiguousarray(mesh.V), F, bnd.astype(np.int64), np.ascontiguousarray(bnd_uv), 1)
    s = math.sqrt(tri_areas_3d(mesh.V, mesh.F).sum() / max(np.abs(signed_areas_2d(UV, mesh.F)).sum(), 1e-30))
    return np.asarray(UV) * s


# ---------------------------------------------------------------------------
# flatteners (libigl)
# ---------------------------------------------------------------------------

def tri_areas_3d(V: np.ndarray, F: np.ndarray) -> np.ndarray:
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)


def signed_areas_2d(UV: np.ndarray, F: np.ndarray) -> np.ndarray:
    a, b, c = UV[F[:, 0], :2], UV[F[:, 1], :2], UV[F[:, 2], :2]
    e1, e2 = b - a, c - a
    return 0.5 * (e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])


def singular_values(V: np.ndarray, F: np.ndarray, UV: np.ndarray) -> np.ndarray:
    """(m, 2) singular values (s1 >= s2) of the per-triangle Jacobian from
    the triangle's own 3-D orthonormal frame to the flat plane. NaN for
    degenerate 3-D triangles."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = b - a, c - a
    l1 = np.linalg.norm(e1, axis=1)
    x = e1 / np.where(l1 > 0, l1, np.nan)[:, None]
    n = np.cross(e1, e2)
    nn = np.linalg.norm(n, axis=1)
    y = np.cross(n / np.where(nn > 0, nn, np.nan)[:, None], x)
    # local 2-D coordinates of the 3-D triangle
    P = np.stack([np.stack([l1, np.zeros_like(l1)], 1), np.stack([(e2 * x).sum(1), (e2 * y).sum(1)], 1)], 2)  # (m,2,2) columns e1,e2
    ua, ub, uc = UV[F[:, 0], :2], UV[F[:, 1], :2], UV[F[:, 2], :2]
    Q = np.stack([ub - ua, uc - ua], 2)  # (m,2,2)
    with np.errstate(invalid="ignore", divide="ignore"):
        J = Q @ np.linalg.inv(P)
    s = np.linalg.svd(np.nan_to_num(J), compute_uv=False)
    s[~np.isfinite(J).all(axis=(1, 2))] = np.nan
    return s


def sym_dirichlet(V: np.ndarray, F: np.ndarray, UV: np.ndarray) -> float:
    """Area-weighted mean symmetric Dirichlet energy (min 4 at an isometry);
    inf if any triangle is flipped or degenerate relative to the majority."""
    sa = signed_areas_2d(UV, F)
    sgn = 1.0 if np.sum(sa > 0) >= np.sum(sa < 0) else -1.0
    if np.any(sgn * sa <= 0):
        return math.inf
    s = singular_values(V, F, UV)
    A = tri_areas_3d(V, F)
    e = s[:, 0] ** 2 + s[:, 1] ** 2 + s[:, 0] ** -2 + s[:, 1] ** -2
    return float(np.nansum(A * e) / np.nansum(A))


def flatten_slim(V: np.ndarray, F: np.ndarray, UV0: np.ndarray, *, max_iter: int = 200,
                 chunk: int = 5, rel_tol: float = 1e-7) -> tuple[np.ndarray, dict]:
    """libigl SLIM, symmetric Dirichlet, free boundary (no constraints).
    Iterates in chunks until the relative energy decrease over a chunk is
    below rel_tol or max_iter is reached."""
    import igl

    Vf = np.asfortranarray(V, dtype=np.float64)
    Ff = np.asfortranarray(F, dtype=np.int32)
    data = igl.slim_precompute(Vf, Ff, np.asfortranarray(UV0[:, :2], dtype=np.float64),
                               igl.MappingEnergyType.SYMMETRIC_DIRICHLET,
                               np.zeros(0, np.int32), np.zeros((0, 2), order="F"), 0.0)
    hist = [sym_dirichlet(V, F, UV0)]
    UV = UV0
    it = 0
    while it < max_iter:
        UV = np.asarray(igl.slim_solve(data, chunk))
        it += chunk
        hist.append(sym_dirichlet(V, F, UV))
        if math.isfinite(hist[-2]) and (hist[-2] - hist[-1]) <= rel_tol * hist[-2]:
            break
    return UV[:, :2].copy(), {"iterations": it, "energy_history": hist,
                              "converged": it < max_iter}


def flatten_arap(V: np.ndarray, F: np.ndarray, UV0: np.ndarray, *, max_iter: int = 200) -> tuple[np.ndarray, dict]:
    """libigl ARAP parameterisation: dim 2, ARAP_ENERGY_TYPE_ELEMENTS,
    initial guess UV0, local-global iterations.

    libigl tutorial 503 uses with_dynamics=True and no constraint; its
    inertia term scales with the mass matrix (area, vox^2) while the ARAP
    Laplacian is scale-free, so at voxel scale the solve barely leaves UV0
    (measured: max move 0.025 vox on a 60 x 60 sphere patch). We therefore use
    with_dynamics=False and pin ONE vertex (index 0) at its UV0 position,
    which only removes the translation null space (rotation and shape stay
    free). Measured on the same patch: grid and Tutte initialisations reach
    the same fixed point.
    """
    import igl

    data = igl.ARAPData()
    data.energy = igl.ARAPEnergyType.ARAP_ENERGY_TYPE_ELEMENTS
    data.with_dynamics = False
    data.max_iter = int(max_iter)
    Vc = np.ascontiguousarray(V, dtype=np.float64)
    Fc = np.ascontiguousarray(F, dtype=np.int64)
    b = np.array([0], np.int32)
    U0 = np.ascontiguousarray(UV0[:, :2], dtype=np.float64)
    igl.arap_precomputation(Vc, Fc, 2, b, data)
    UV = np.asarray(igl.arap_solve(np.ascontiguousarray(U0[b]), data, U0))
    return UV[:, :2].copy(), {"iterations": int(max_iter), "energy": "ARAP_ENERGY_TYPE_ELEMENTS",
                              "with_dynamics": False, "pinned_vertices": [0]}


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def _edge_ratios(points: np.ndarray, uv: np.ndarray, s: float) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(points, dtype=np.float64)
    L3h = np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)
    L3v = np.linalg.norm(p[1:] - p[:-1], axis=-1)
    L2h = np.linalg.norm(uv[:, 1:] - uv[:, :-1], axis=-1) * s
    L2v = np.linalg.norm(uv[1:] - uv[:-1], axis=-1) * s
    with np.errstate(invalid="ignore", divide="ignore"):
        return L2h / L3h, L2v / L3v  # (H, W-1), (H-1, W)


def quad_edge_ok(points: np.ndarray, uv: np.ndarray, tol: float, s: float = 1.0) -> np.ndarray:
    """(H-1, W-1) bool: all four edges of the quad within +-tol (NaN -> False)."""
    rh, rv = _edge_ratios(points, uv, s)
    okh = np.abs(rh - 1.0) <= tol
    okv = np.abs(rv - 1.0) <= tol
    return okh[:-1, :] & okh[1:, :] & okv[:, :-1] & okv[:, 1:]


def evaluate(points: np.ndarray, uv: np.ndarray, quads: np.ndarray, *, tols=(0.01, 0.02, 0.05, 0.10),
             main_tol: float = 0.05) -> dict:
    """Distortion statistics of a flattening ``uv`` over the quads ``quads``.

    Quads whose uv is undefined at any corner count as failing (never
    dropped). Returns JSON-ready numbers only.
    """
    p = np.asarray(points, dtype=np.float64)
    q = np.asarray(quads, bool) & quad_mask(p)
    nq = int(q.sum())
    mesh = grid_to_mesh(p, q)
    UV = np.full((mesh.V.shape[0], 2), np.nan)
    rr, cc = np.nonzero(mesh.index >= 0)
    UV[mesh.index[rr, cc]] = uv[rr, cc]
    tri_ok = np.isfinite(UV[mesh.F]).all(axis=(1, 2))
    A3 = tri_areas_3d(mesh.V, mesh.F)
    sa = signed_areas_2d(UV, mesh.F)
    A2 = np.abs(sa)
    s_area = math.sqrt(A3[tri_ok].sum() / A2[tri_ok].sum()) if tri_ok.any() and A2[tri_ok].sum() > 0 else math.nan

    out: dict = {"n_quads": nq, "n_triangles": int(mesh.F.shape[0]),
                 "n_triangles_uv_undefined": int((~tri_ok).sum()),
                 "area_3d_vox2": float(A3.sum()), "area_scale_factor": s_area}
    for label, s in (("norm", s_area), ("raw", 1.0)):
        ok = quad_edge_ok(p, uv, main_tol, s) & q
        out[f"pct_quads_within_{int(round(main_tol * 100))}pct_{label}"] = 100.0 * ok.sum() / nq if nq else math.nan
    for t in tols:
        ok = quad_edge_ok(p, uv, t, s_area) & q
        out[f"pct_quads_within_{t * 100:g}pct"] = 100.0 * ok.sum() / nq if nq else math.nan

    # edge ratio distribution (edges of evaluated quads, area-normalised)
    rh, rv = _edge_ratios(p, uv, s_area)
    eh = np.zeros_like(rh, bool)
    eh[:-1] |= q
    eh[1:] |= q
    ev = np.zeros_like(rv, bool)
    ev[:, :-1] |= q
    ev[:, 1:] |= q
    er = np.concatenate([rh[eh], rv[ev]])
    er_f = er[np.isfinite(er)]
    out["edge_ratio_pctl"] = {str(k): float(np.percentile(er_f, k)) for k in (0.5, 5, 25, 50, 75, 95, 99.5)} if er_f.size else {}
    out["edge_abs_log_ratio_mean"] = float(np.mean(np.abs(np.log(er_f)))) if er_f.size else math.nan

    # per-triangle: flips, area, angle, conformal distortion
    sgn = 1.0 if np.sum(sa[tri_ok] > 0) >= np.sum(sa[tri_ok] < 0) else -1.0
    flipped = tri_ok & (sgn * sa < 0)
    degenerate = tri_ok & (sa == 0)
    out["flipped_triangles"] = int(flipped.sum())
    out["degenerate_triangles"] = int(degenerate.sum())
    good = tri_ok & ~flipped & ~degenerate & (A3 > 0)
    out["n_triangles_good"] = int(good.sum())
    if not good.any():  # total failure (e.g. no UV at all): quad metrics above already 0 %
        nan = math.nan
        out["area_ratio"] = {"weighted_mean_abs_log": nan, "pct_tri_within_5pct": nan, "p1": nan, "p50": nan, "p99": nan}
        out["conformal_sigma_ratio"] = {"weighted_mean": nan, "p50": nan, "p99": nan}
        out["angle_abs_err_deg"] = {"mean": nan, "p50": nan, "p99": nan, "max": nan}
        out["sym_dirichlet_area_weighted"] = nan
        return out
    UVs = UV * s_area
    sv = singular_values(mesh.V[:, :], mesh.F[good], UVs) if good.any() else np.zeros((0, 2))
    w = A3[good] / A3[good].sum() if good.any() else np.zeros(0)
    area_ratio = sv[:, 0] * sv[:, 1]
    conf = sv[:, 0] / sv[:, 1]
    out["area_ratio"] = {
        "weighted_mean_abs_log": float(np.sum(w * np.abs(np.log(area_ratio)))),
        "pct_tri_within_5pct": float(100.0 * np.mean(np.abs(area_ratio - 1) <= 0.05)),
        "p1": float(np.percentile(area_ratio, 1)), "p50": float(np.percentile(area_ratio, 50)),
        "p99": float(np.percentile(area_ratio, 99)),
    }
    out["conformal_sigma_ratio"] = {
        "weighted_mean": float(np.sum(w * conf)), "p50": float(np.percentile(conf, 50)),
        "p99": float(np.percentile(conf, 99)),
    }
    # angle distortion: |flat angle - 3-D angle| per corner, degrees
    ang3 = _tri_angles(mesh.V[mesh.F[good]])
    ang2 = _tri_angles(np.concatenate([UVs[mesh.F[good]], np.zeros((int(good.sum()), 3, 1))], 2))
    d = np.degrees(np.abs(ang2 - ang3))
    out["angle_abs_err_deg"] = {"mean": float(d.mean()), "p50": float(np.median(d)),
                                "p99": float(np.percentile(d, 99)), "max": float(d.max())}
    out["sym_dirichlet_area_weighted"] = float(np.sum(w * (sv[:, 0] ** 2 + sv[:, 1] ** 2 + sv[:, 0] ** -2 + sv[:, 1] ** -2)))
    return out


def _tri_angles(T: np.ndarray) -> np.ndarray:
    """(m, 3, 3) triangle corners -> (m, 3) interior angles (radians)."""
    out = np.empty(T.shape[:2])
    for k in range(3):
        a = T[:, k]
        b = T[:, (k + 1) % 3]
        c = T[:, (k + 2) % 3]
        u, v = b - a, c - a
        cosv = (u * v).sum(1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1))
        out[:, k] = np.arccos(np.clip(cosv, -1, 1))
    return out


# ---------------------------------------------------------------------------
# seeded rectangle rule
# ---------------------------------------------------------------------------

def rect_area_vox2(points: np.ndarray, r0: int, c0: int, h: int, w: int) -> float:
    sub = np.asarray(points[r0:r0 + h + 1, c0:c0 + w + 1], dtype=np.float64)
    m = grid_to_mesh(sub)
    return float(tri_areas_3d(m.V, m.F).sum())


def feasible_origins(qvalid: np.ndarray, h: int, w: int) -> np.ndarray:
    """(k, 2) quad origins (r0, c0) such that the h x w quad block is fully
    valid (integral image)."""
    q = np.asarray(qvalid, np.int64)
    H, W = q.shape
    if h > H or w > W:
        return np.zeros((0, 2), np.int64)
    S = np.zeros((H + 1, W + 1), np.int64)
    S[1:, 1:] = q.cumsum(0).cumsum(1)
    tot = S[h:, w:] - S[:-h, w:] - S[h:, :-w] + S[:-h, :-w]
    return np.argwhere(tot == h * w)


def choose_rectangle(points: np.ndarray, voxel_um: float, step_vox: float, rng: np.random.Generator, *,
                     target_cm2: float = 4.0, rel_tol: float = 0.01, max_aspect: float = 2.0,
                     max_tries: int = 50) -> dict | None:
    """Seeded rectangle rule (fixed in code before any flattening is run).

    1. aspect a ~ U[1, max_aspect] (width >= height; rows are iso-z lines);
    2. nominal quads h = round(sqrt(target / a) / q), w = round(a h), with q
       the nominal quad side in cm (step_vox * voxel);
    3. origin uniform among positions whose h x w quad block is fully valid;
    4. w is then adjusted (+-1 column steps, nearest first) until the 3-D
       triangle area is within +-rel_tol of the target, keeping the aspect
       <= max_aspect; if impossible, redraw (up to max_tries).
    Returns None if no feasible rectangle exists.
    """
    q_cm = step_vox * voxel_um * 1e-4
    vox2_per_cm2 = 1.0 / (voxel_um * 1e-4) ** 2
    qv = quad_mask(points)
    for _ in range(max_tries):
        a = float(rng.uniform(1.0, max_aspect))
        h = int(round(math.sqrt(target_cm2 / a) / q_cm))
        w0 = int(round(a * h))
        org = feasible_origins(qv, h, w0 + 3)  # room to widen by up to 3 columns
        if org.shape[0] == 0:
            continue
        r0, c0 = (int(x) for x in org[rng.integers(org.shape[0])])
        for dw in (0, 1, -1, 2, -2, 3, -3):
            w = w0 + dw
            if w < h or w > max_aspect * h or c0 + w > qv.shape[1]:
                continue
            if not qv[r0:r0 + h, c0:c0 + w].all():
                continue
            A = rect_area_vox2(points, r0, c0, h, w) / vox2_per_cm2
            if abs(A - target_cm2) <= rel_tol * target_cm2:
                return {"r0": r0, "c0": c0, "h_quads": h, "w_quads": w, "aspect_drawn": a,
                        "aspect": w / h, "area_cm2": A, "n_feasible_origins": int(org.shape[0])}
    return None
