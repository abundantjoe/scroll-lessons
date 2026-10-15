"""Levelling: rotate the (u, v) grid of a tifxyz so iso-z curves run along
rows, and resample at a fixed arc-length step.

Levelling method
----------------
1. z-gradient direction. For every valid quad the cell-centred z gradient in
   grid units is ``g = (dz/du, dz/dv)`` (average of the two opposite edge
   differences). The angle ``theta = atan2(dz/dv, dz/du)`` of the direction in
   which z increases is estimated robustly (default ``method="median"``): the
   circular mean of the unit gradient directions is taken as a centre, and
   ``theta`` = centre + median of the wrapped angular deviations (two passes).
   ``method="lsq"`` instead fits the plane ``z = a u + b v + c`` over all
   valid vertices by least squares and uses ``atan2(b, a)``. The median-
   absolute-deviation of the per-cell angles is returned as a diagnostic: a
   single global rotation only levels a tile whose iso-z direction is
   uniform, so large-spread meshes should be levelled tile by tile.
2. Proper rotation (det = +1, so handedness is untouched). New axes in the
   (u, v) plane: ``e_v = (cos theta, sin theta)`` (z increases along +v'),
   ``e_u = (sin theta, -cos theta)``. Hence rows of the output have constant
   z and z increases with the row index.
3. Arc-length spacing. The metric along each new axis
   ``s = |dp/du * e[0] + dp/dv * e[1]|`` (voxels per grid unit) is taken as
   the median over valid quads; the new grid spacing in grid units is
   ``step_vox / s``. This yields step_vox arc-length spacing when the input
   parameterisation is (near-)isometric, as tracer output is; the realised
   edge lengths should always be checked with
   ``tifxyz.edge_fraction_within``.
4. Resampling. Every output node is mapped back to fractional source (row,
   col) and xyz is bilinearly interpolated over the source grid; a node is
   valid only if its source quad has four valid corners (invalid propagates).

"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .tifxyz import SENTINEL, quad_valid_mask, valid_mask


def sample_grid(points: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Bilinear interpolation of an (H, W, 3) grid at fractional (row, col).

    A sample is valid iff it lies inside the grid and all four corners of its
    containing quad are valid (invalidity propagates); invalid samples get
    the sentinel. Samples exactly on the last row/column use the last quad.
    """
    p = np.asarray(points, dtype=np.float64)
    H, W = p.shape[:2]
    r = np.asarray(rows, dtype=np.float64)
    c = np.asarray(cols, dtype=np.float64)
    shape = np.broadcast(r, c).shape
    r = np.broadcast_to(r, shape).ravel()
    c = np.broadcast_to(c, shape).ravel()
    out = np.full((r.size, 3), SENTINEL, dtype=np.float64)
    eps = 1e-9
    inside = np.isfinite(r) & np.isfinite(c) & (r >= -eps) & (r <= H - 1 + eps) & (c >= -eps) & (c <= W - 1 + eps)
    idx = np.nonzero(inside)[0]
    if idx.size:
        rr = np.clip(r[idx], 0, H - 1)
        cc = np.clip(c[idx], 0, W - 1)
        j = np.minimum(np.floor(rr).astype(np.int64), H - 2)
        i = np.minimum(np.floor(cc).astype(np.int64), W - 2)
        t = (rr - j)[:, None]
        s = (cc - i)[:, None]
        qv = quad_valid_mask(p)[j, i]
        val = ((1 - s) * (1 - t) * p[j, i] + s * (1 - t) * p[j, i + 1]
               + (1 - s) * t * p[j + 1, i] + s * t * p[j + 1, i + 1])
        out[idx[qv]] = val[qv]
    return out.reshape(*shape, 3)


def _cell_z_gradients(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(points, dtype=np.float64)
    qv = quad_valid_mask(p)
    z = p[..., 2]
    gu = 0.5 * ((z[:-1, 1:] - z[:-1, :-1]) + (z[1:, 1:] - z[1:, :-1]))
    gv = 0.5 * ((z[1:, :-1] - z[:-1, :-1]) + (z[1:, 1:] - z[:-1, 1:]))
    return gu[qv], gv[qv]


def _wrap(a: np.ndarray) -> np.ndarray:
    return (a + np.pi) % (2 * np.pi) - np.pi


def estimate_level_angle(points: np.ndarray, method: str = "median") -> tuple[float, float]:
    """Angle (degrees, from +u toward +v) of the direction in which z
    increases in the (u, v) grid, and the MAD spread (degrees) of the
    per-cell directions. See module docstring."""
    p = np.asarray(points, dtype=np.float64)
    gu, gv = _cell_z_gradients(p)
    mag = np.hypot(gu, gv)
    keep = mag > 1e-9
    if keep.sum() == 0:
        raise ValueError("no valid quad with a non-zero z gradient")
    th = np.arctan2(gv[keep], gu[keep])
    if method == "median":
        centre = math.atan2(np.sin(th).sum(), np.cos(th).sum())
        for _ in range(2):
            centre = centre + float(np.median(_wrap(th - centre)))
        theta = centre
    elif method == "lsq":
        v = valid_mask(p)
        vv, uu = np.nonzero(v)
        A = np.stack([uu, vv, np.ones_like(uu)], axis=1).astype(np.float64)
        (a, b, _), *_ = np.linalg.lstsq(A, p[vv, uu, 2], rcond=None)
        if abs(a) + abs(b) < 1e-12:
            raise ValueError("least-squares z plane is flat")
        theta = math.atan2(b, a)
    else:
        raise ValueError(f"unknown method {method!r}")
    spread = float(np.degrees(np.median(np.abs(_wrap(th - theta)))))
    return math.degrees(_wrap(np.array(theta)).item()), spread


@dataclass
class LevelResult:
    points: np.ndarray  # (H', W', 3) float32, sentinel for invalid
    src_u: np.ndarray  # (H', W') fractional source column of each node
    src_v: np.ndarray  # (H', W') fractional source row of each node
    angle_deg: float  # z-gradient direction in the source (u, v) grid
    spread_deg: float  # MAD of per-cell gradient directions
    e_u: np.ndarray  # new +u' axis in source (u, v) grid units
    e_v: np.ndarray  # new +v' axis (z increases along it)
    origin: tuple[float, float]  # (U'0, V'0): rotated coords of node (0, 0)
    du: float  # source grid units per output column
    dv: float  # source grid units per output row
    step_vox: float
    metric: tuple[float, float]  # vox per source grid unit along e_u, e_v

    @property
    def valid(self) -> np.ndarray:
        return valid_mask(self.points)

    def to_level_index(self, u: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Source grid (u=col, v=row) -> fractional output (row, col)."""
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        U = u * self.e_u[0] + v * self.e_u[1]
        V = u * self.e_v[0] + v * self.e_v[1]
        return (V - self.origin[1]) / self.dv, (U - self.origin[0]) / self.du

    def map_back(self, source_shape: tuple[int, int]) -> np.ndarray:
        """Sample the levelled surface at every source grid vertex (bilinear
        over the levelled grid); sentinel where the levelled grid is invalid."""
        H, W = source_shape
        vv, uu = np.mgrid[0:H, 0:W].astype(np.float64)
        r, c = self.to_level_index(uu, vv)
        return sample_grid(self.points, r, c).astype(np.float32)



def _axis_metric(points: np.ndarray, e: np.ndarray) -> float:
    p = np.asarray(points, dtype=np.float64)
    qv = quad_valid_mask(p)
    dpdu = 0.5 * ((p[:-1, 1:] - p[:-1, :-1]) + (p[1:, 1:] - p[1:, :-1]))[qv]
    dpdv = 0.5 * ((p[1:, :-1] - p[:-1, :-1]) + (p[1:, 1:] - p[:-1, 1:]))[qv]
    s = np.linalg.norm(dpdu * e[0] + dpdv * e[1], axis=-1)
    s = s[np.isfinite(s) & (s > 0)]
    if s.size == 0:
        raise ValueError("cannot estimate the grid metric (no valid quads)")
    return float(np.median(s))


def level_mesh(
    points_grid: np.ndarray,
    step_vox: float = 20.0,
    *,
    angle_deg: float | None = None,
    method: str = "median",
    crop: bool = True,
) -> LevelResult:
    """Rotate the (u, v) parameterisation so iso-z curves are rows, and
    resample on a regular grid with ``step_vox`` arc-length spacing.

    ``angle_deg`` overrides the estimated z-gradient direction (e.g. to share
    one rotation between tiles). See the module docstring for the method.
    """
    p = np.asarray(points_grid, dtype=np.float64)
    if p.ndim != 3 or p.shape[-1] != 3:
        raise ValueError("points_grid must be (H, W, 3)")
    if step_vox <= 0:
        raise ValueError("step_vox must be > 0")
    v_ok = valid_mask(p)
    if not v_ok.any():
        raise ValueError("no valid vertices")
    if angle_deg is None:
        angle_deg, spread = estimate_level_angle(p, method=method)
    else:
        try:
            _, spread = estimate_level_angle(p, method="median")
        except ValueError:
            spread = math.nan
    th = math.radians(angle_deg)
    e_v = np.array([math.cos(th), math.sin(th)])
    e_u = np.array([math.sin(th), -math.cos(th)])  # det[e_u, e_v] = +1

    s_u = _axis_metric(p, e_u)
    s_v = _axis_metric(p, e_v)
    du = step_vox / s_u
    dv = step_vox / s_v

    vv, uu = np.nonzero(v_ok)
    U = uu * e_u[0] + vv * e_u[1]
    V = uu * e_v[0] + vv * e_v[1]
    U0, V0 = float(U.min()), float(V.min())
    nU = int(math.floor((U.max() - U0) / du + 1e-9)) + 1
    nV = int(math.floor((V.max() - V0) / dv + 1e-9)) + 1
    Ug = U0 + du * np.arange(nU)
    Vg = V0 + dv * np.arange(nV)
    VV, UU = np.meshgrid(Vg, Ug, indexing="ij")
    src_u = UU * e_u[0] + VV * e_v[0]
    src_v = UU * e_u[1] + VV * e_v[1]
    out = sample_grid(p, src_v, src_u)

    if crop:
        ok = valid_mask(out)
        if ok.any():
            rows = np.nonzero(ok.any(axis=1))[0]
            cols = np.nonzero(ok.any(axis=0))[0]
            r0, r1, c0, c1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
            out = out[r0:r1, c0:c1]
            src_u = src_u[r0:r1, c0:c1]
            src_v = src_v[r0:r1, c0:c1]
            U0 += c0 * du
            V0 += r0 * dv
    return LevelResult(
        points=out.astype(np.float32),
        src_u=src_u,
        src_v=src_v,
        angle_deg=float(angle_deg),
        spread_deg=float(spread),
        e_u=e_u,
        e_v=e_v,
        origin=(U0, V0),
        du=float(du),
        dv=float(dv),
        step_vox=float(step_vox),
        metric=(s_u, s_v),
    )


def iso_z_tilt_deg(points: np.ndarray) -> float:
    """Angle (deg) between the mean z-gradient and the +v (row) axis: 0 when
    iso-z curves are exactly horizontal rows with z increasing downward."""
    gu, gv = _cell_z_gradients(points)
    if gu.size == 0:
        return math.nan
    return abs(math.degrees(math.atan2(float(np.mean(gu)), float(np.mean(gv)))))
