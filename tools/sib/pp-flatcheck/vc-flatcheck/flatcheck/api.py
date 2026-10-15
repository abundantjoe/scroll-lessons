"""High-level API: flatten a tifxyz grid and report its flattening quality."""

from __future__ import annotations

import time

import numpy as np

from . import geometry as G

METHODS = ("slim", "arap")
RESCALE_LIMIT = 1.5  # an area rescale outside [1/1.5, 1.5] means the map shrank/grew (collapse)
MAIN_TOL = 0.05


def nominal_step(points: np.ndarray) -> float:
    """Median grid edge length (the nominal step of an isometric grid)."""
    p = np.asarray(points, dtype=np.float64)
    v = G.valid_mask(p)
    eh = (v[:, 1:] & v[:, :-1])
    ev = (v[1:] & v[:-1])
    L = np.concatenate([np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)[eh],
                        np.linalg.norm(p[1:] - p[:-1], axis=-1)[ev]])
    L = L[L > 0]
    if L.size == 0:
        raise ValueError("mesh has no valid edges")
    return float(np.median(L))


def flatten(points: np.ndarray, method: str = "slim", *, step: float | None = None,
            quads: np.ndarray | None = None, max_iter: int = 200) -> tuple[np.ndarray, dict]:
    """Flatten a tifxyz grid. Returns ``(uv (H, W, 2), info)``.

    * ``slim``: libigl SLIM, symmetric Dirichlet, free boundary, started from
      the grid (u, v) = (c, r) * step, which is flip-free; the barrier energy
      keeps it flip-free. Stops when the relative energy decrease over 5
      iterations is <= 1e-7 (max ``max_iter``).
    * ``arap``: libigl ARAP (per-element energy, ``max_iter`` local-global
      iterations, one pinned vertex, same start).
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    p = np.asarray(points, dtype=np.float64)
    st = nominal_step(p) if step is None else float(step)
    mesh = G.grid_to_mesh(p, quads)
    if mesh.F.shape[0] == 0:
        raise ValueError("mesh has no valid quads")
    UV0 = G.grid_init_uv(mesh, st)
    t0 = time.time()
    if method == "slim":
        UV, info = G.flatten_slim(mesh.V, mesh.F, UV0, max_iter=max_iter)
    else:
        UV, info = G.flatten_arap(mesh.V, mesh.F, UV0, max_iter=max_iter)
    info = dict(info, method=method, step_vox=st, seconds=time.time() - t0)
    return G.uv_to_grid(mesh, UV, p.shape[:2]), info


def metrics(points: np.ndarray, uv: np.ndarray, quads: np.ndarray | None = None) -> dict:
    p = np.asarray(points, dtype=np.float64)
    q = G.quad_mask(p) if quads is None else np.asarray(quads, bool)
    return G.evaluate(p, np.asarray(uv, np.float64), q, main_tol=MAIN_TOL)


def collapse_flags(m: dict, rescale_factor: float | None = None) -> dict:
    """Collapse / fold-over detector.

    ``rescale_factor``: the global scale a flattener applied to match the 3-D
    area (e.g. ABF++/LSCM "Scaling UVs by ..."); if not given, the metric's own
    area_scale_factor sqrt(A3/A2) is used, which catches a shrunken or blown-up
    map that was not rescaled.
    """
    s = rescale_factor if rescale_factor is not None else m.get("area_scale_factor")
    out = {"flipped": m["flipped_triangles"] > 0,
           "undefined_uv": m["n_triangles_uv_undefined"] > 0,
           "rescale_factor": s,
           "rescale_out_of_range": bool(s is not None and np.isfinite(s)
                                        and not (1 / RESCALE_LIMIT <= s <= RESCALE_LIMIT))}
    out["collapsed"] = out["flipped"] or out["undefined_uv"] or out["rescale_out_of_range"]
    return out


def report(points: np.ndarray, uv: np.ndarray, *, quads: np.ndarray | None = None,
           rescale_factor: float | None = None, bar: float = 93.1) -> dict:
    """Metrics + collapse flags + intrinsic curvature + pass/fail against ``bar``
    (% of quads within +-5 %)."""
    m = metrics(points, uv, quads)
    c = collapse_flags(m, rescale_factor)
    k = G.angle_defects(points, quads)
    pct = m["pct_quads_within_5pct"]
    return {"pct_quads_within_5pct": pct, "passes_bar": bool(pct >= bar), "bar_pct": bar,
            "fold_overs": m["flipped_triangles"], "collapse": c, "curvature": k, "metrics": m}
