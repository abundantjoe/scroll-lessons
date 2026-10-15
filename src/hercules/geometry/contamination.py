# Provenance: Project HERCULES | owner the owner | [id removed]
"""KD-tree tools for surface identity and train/test contamination checks.

All inputs are point clouds (N, 3) in voxels, normally the valid vertices of
meshes densified to ~1 vox spacing (``dense_cloud``). The ``same_papyrus``
distance-bin rule assumes that sampling density: at coarser spacing the
in-plane nearest-neighbour distance alone exceeds 1-2 vox and the rule will
under-call SAME. Use the normal-distance statistics as a density-independent
cross-check.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np
from scipy.spatial import cKDTree

from .tifxyz import densify, valid_mask


def cloud(points: np.ndarray) -> np.ndarray:
    """Valid vertices of an (H, W, 3) grid as (N, 3) float64, or pass an
    (N, 3) array through."""
    p = np.asarray(points, dtype=np.float64)
    if p.ndim == 3:
        return p[valid_mask(p)]
    if p.ndim == 2 and p.shape[1] == 3:
        return p
    raise ValueError(f"expected (H, W, 3) grid or (N, 3) cloud, got {p.shape}")


def dense_cloud(points: np.ndarray, step_vox: float, target_spacing_vox: float = 1.0) -> np.ndarray:
    """Densify an (H, W, 3) grid with nominal step ``step_vox`` to about
    ``target_spacing_vox`` and return its valid points."""
    k = max(1, int(math.ceil(step_vox / target_spacing_vox)))
    return cloud(densify(points, k))


def _dense_with_normals(points: np.ndarray, normals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(points, dtype=np.float64)
    n = np.asarray(normals, dtype=np.float64)
    if p.shape != n.shape:
        raise ValueError("points and normals must have the same shape")
    if p.ndim == 3:
        ok = valid_mask(p) & np.isfinite(n).all(-1)
        return p[ok], n[ok]
    return p, n


@dataclass
class SamePapyrusResult:
    counts: tuple[int, int, int]  # A points with nearest B in [0,1), [1,2), [2,3) vox
    n_within_2: int
    same: bool
    n_a: int
    normal_dist: dict = field(default_factory=dict)  # stats of |(a-b).n_b| for pairs < 3 vox


def same_papyrus(
    A: np.ndarray,
    B: np.ndarray,
    normals_B: np.ndarray | None = None,
    *,
    min_within_2: int = 1000,
    ratio: float = 2.0,
    workers: int = 1,
) -> SamePapyrusResult:
    """Are A and B traces of the same papyrus sheet?

    SAME iff (#A points with nearest B < 2 vox) >= ``min_within_2`` AND
    count[0,1) >= ``ratio`` * count[2,3). ``normals_B`` (same layout as B)
    enables the normal-distance statistics |(a - b) . n_b|.
    """
    a = cloud(A)
    if normals_B is not None:
        b, nb = _dense_with_normals(B, normals_B)
    else:
        b, nb = cloud(B), None
    if a.shape[0] == 0 or b.shape[0] == 0:
        return SamePapyrusResult((0, 0, 0), 0, False, int(a.shape[0]), {})
    tree = cKDTree(b)
    d, idx = tree.query(a, k=1, distance_upper_bound=3.0, workers=workers)
    c0 = int(np.sum(d < 1.0))
    c1 = int(np.sum((d >= 1.0) & (d < 2.0)))
    c2 = int(np.sum((d >= 2.0) & (d < 3.0)))
    within2 = c0 + c1
    same = (within2 >= min_within_2) and (c0 >= ratio * c2)
    stats: dict = {}
    if nb is not None:
        m = np.isfinite(d) & (d < 3.0)
        if m.any():
            nd = np.abs(np.einsum("ij,ij->i", a[m] - b[idx[m]], nb[idx[m]]))
            stats = dict(
                n=int(m.sum()),
                mean=float(nd.mean()),
                median=float(np.median(nd)),
                p90=float(np.percentile(nd, 90)),
                max=float(nd.max()),
            )
        else:
            stats = dict(n=0)
    return SamePapyrusResult((c0, c1, c2), within2, bool(same), int(a.shape[0]), stats)


@dataclass
class ClearanceCertificate:
    min_distance: float
    passed: bool
    threshold: float
    offending_ids: list
    per_set_min: dict


def clearance_certificate(
    region_points: np.ndarray,
    training_points_list: Sequence[np.ndarray] | Mapping[object, np.ndarray],
    min_vox: float = 128.0,
    halo_vox: float = 64.0,
    *,
    workers: int = 1,
) -> ClearanceCertificate:
    """Certify that an evaluation region is far from every training surface.

    PASS iff the minimum distance between any region point and any training
    point is >= min_vox + halo_vox. ``training_points_list`` is a sequence
    (IDs = indices) or a mapping ID -> points; offending IDs are the sets
    closer than the threshold. Empty training sets are ignored.
    """
    thr = float(min_vox) + float(halo_vox)
    region = cloud(region_points)
    if region.shape[0] == 0:
        raise ValueError("region has no valid points")
    items = training_points_list.items() if isinstance(training_points_list, Mapping) else enumerate(training_points_list)
    tree = cKDTree(region)
    per: dict = {}
    for key, pts in items:
        t = cloud(pts)
        if t.shape[0] == 0:
            continue
        d, _ = tree.query(t, k=1, workers=workers)
        per[key] = float(np.min(d))
    mn = min(per.values()) if per else math.inf
    offending = [k for k, v in per.items() if v < thr]
    return ClearanceCertificate(min_distance=mn, passed=bool(mn >= thr), threshold=thr,
                                offending_ids=offending, per_set_min=per)


def overlap_fraction(A: np.ndarray, B: np.ndarray, tol: float, *, workers: int = 1) -> float:
    """Fraction of A points whose nearest B point is within ``tol`` vox
    (inclusive)."""
    a, b = cloud(A), cloud(B)
    if a.shape[0] == 0:
        return math.nan
    if b.shape[0] == 0:
        return 0.0
    d, _ = cKDTree(b).query(a, k=1, distance_upper_bound=float(tol) * (1 + 1e-12) + 1e-12, workers=workers)
    return float(np.mean(d <= tol))
