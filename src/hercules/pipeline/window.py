# Provenance: Project HERCULES | owner the owner | [id removed]
"""Window pipeline: organizer mesh + window on the organizer canvas ->
levelled, reading-oriented tifxyz, exact coordinate maps, render command and
alignment gate.

Frames
------
* organizer canvas: pixel (y, x) of the official render of the ORIGINAL
  organizer mesh at --scale 1 (the frame of the organizer SVs, the J windows
  and ref9); pixel P samples grid (P + 0.5) s (see canvas.py).
* levelled canvas: pixel (y, x) of the official render of the levelled,
  oriented (and possibly padded) tifxyz written by :func:`write_levelled_tifxyz`.
* levelled window: the h x w square of the levelled canvas centred on the
  image of the organizer window centre (``frame="window"``).

Composition (all steps affine, so the maps are exact and invertible):
organizer pixel -> organizer grid (canvas.RenderCanvas.pixel_to_grid) ->
cut sub-grid (subtract r0, c0) -> levelled grid (LevelResult.to_level_index)
-> mirror (OrientResult flips) -> padding -> levelled canvas pixel
(RenderCanvas.grid_to_pixel) -> levelled window (subtract its origin).

Maps are exact in the (u, v) parameter domain. The levelled surface is a
bilinear resample of the original, so its xyz differs from the original
surface at the same (u, v) by a second-order (sub-voxel) amount.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from hercules.geometry.level_mesh import (
    CentreLike,
    LevelResult,
    NormalSignReport,
    OrientResult,
    estimate_level_angle,
    iso_z_tilt_deg,
    level_mesh,
    normal_sign_report,
    orient_for_reading,
)
from hercules.geometry.tifxyz import (
    SENTINEL,
    TifxyzMesh,
    edge_fraction_within,
    valid_mask,
    vertex_normals,
    write_tifxyz,
)

from . import canvas as C
from .centre import SEALED_SCROLLS, mask_centroid_curve  # noqa: F401  (re-export)

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"
S3_BUCKET = "vesuvius-challenge-open-data"

# J windows on the organizer 9.366 um canvas (2136 x 2136 px), (y0, x0) top-left.
J_WINDOW_PX = 2136
J_WINDOWS_0841 = {
    "J1": ("214732", 300, 2315),
    "J2": ("w00", 2030, 2340),
    "J3": ("214732", 1950, 104),
    "J4": ("022814", 1000, 624),
    "J5": ("022814", 1000, 2760),
}
SEGMENTS_0841 = {
    "w00": "20260220213127-w00",
    "214732": "20260220214732-auto_grown_20260220144552896",
    "022814": "20260221022814-auto_grown_20260220174252405",
}
SEALED_CLEARANCE_PX = 256


@dataclass(frozen=True)
class Window:
    """Axis-aligned window on a canvas: rows y0..y0+h-1, cols x0..x0+w-1."""

    y0: int
    x0: int
    h: int
    w: int

    @property
    def centre(self) -> tuple[float, float]:
        return (self.y0 + (self.h - 1) / 2.0, self.x0 + (self.w - 1) / 2.0)

    def grow(self, m: int) -> "Window":
        return Window(self.y0 - m, self.x0 - m, self.h + 2 * m, self.w + 2 * m)


# ---------------------------------------------------------------------------
# cut
# ---------------------------------------------------------------------------

@dataclass
class Cut:
    mesh: TifxyzMesh  # sub-grid (same scale as the organizer mesh)
    r0: int  # organizer grid row of sub-grid row 0
    c0: int  # organizer grid col of sub-grid col 0
    org_canvas: C.RenderCanvas  # full organizer canvas (origin 0, 0)
    window: Window
    margin_px: int
    region: tuple[slice, slice]  # window + margin (unrotated) inside the sub-grid

    @property
    def points(self) -> np.ndarray:
        return self.mesh.points


def _grid_bounds(org: C.RenderCanvas, y_lo, y_hi, x_lo, x_hi):
    v_lo, u_lo = org.pixel_to_grid(y_lo, x_lo)
    v_hi, u_hi = org.pixel_to_grid(y_hi, x_hi)
    return float(v_lo), float(v_hi), float(u_lo), float(u_hi)


def cut_window(mesh: TifxyzMesh, y0: int, x0: int, h: int, w: int, margin_px: int = SEALED_CLEARANCE_PX, *,
               rotation_extra: bool = True, slack: float = 1.15, pad_cells: int = 2) -> Cut:
    """Sub-grid of the organizer mesh covering the window + margin.

    With ``rotation_extra`` the cut covers the disc circumscribing the window
    + margin (times ``slack`` for grid-metric variation), so the levelled
    window + margin of the same size fits inside the cut at any rotation.
    """
    org = C.canvas_for(mesh.points, mesh.scale)
    H, W = mesh.shape
    win = Window(int(y0), int(x0), int(h), int(w))
    yc, xc = win.centre
    hy, hx = h / 2.0 + margin_px, w / 2.0 + margin_px
    if rotation_extra:
        hy = hx = math.hypot(hy, hx) * slack
    v_lo, v_hi, u_lo, u_hi = _grid_bounds(org, yc - hy, yc + hy, xc - hx, xc + hx)
    r0 = max(0, int(math.floor(v_lo)) - pad_cells)
    r1 = min(H - 1, int(math.ceil(v_hi)) + pad_cells)
    c0 = max(0, int(math.floor(u_lo)) - pad_cells)
    c1 = min(W - 1, int(math.ceil(u_hi)) + pad_cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        raise ValueError("window does not overlap the mesh grid")
    sub = np.array(mesh.points[r0:r1 + 1, c0:c1 + 1], dtype=np.float32, copy=True)
    wv_lo, wv_hi, wu_lo, wu_hi = _grid_bounds(org, y0 - margin_px - 0.5, y0 + h - 1 + margin_px + 0.5,
                                              x0 - margin_px - 0.5, x0 + w - 1 + margin_px + 0.5)
    hs, ws = sub.shape[:2]
    region = (slice(max(0, int(math.floor(wv_lo)) - r0), min(hs, int(math.ceil(wv_hi)) - r0 + 1)),
              slice(max(0, int(math.floor(wu_lo)) - c0), min(ws, int(math.ceil(wu_hi)) - c0 + 1)))
    meta = dict(mesh.meta)
    meta.update(hercules_cut_r0=r0, hercules_cut_c0=c0)
    sm = TifxyzMesh(points=sub, scale=tuple(mesh.scale), uuid=mesh.uuid, meta=meta)
    return Cut(mesh=sm, r0=r0, c0=c0, org_canvas=org, window=win, margin_px=int(margin_px), region=region)


# ---------------------------------------------------------------------------
# level
# ---------------------------------------------------------------------------

@dataclass
class LevelWindow:
    level: LevelResult
    angle_deg: float  # z-gradient direction over the window + margin region
    spread_deg: float  # MAD of per-cell directions over that region
    step_vox: float


def level_window(cut: Cut | TifxyzMesh | np.ndarray, step_vox: float = 20.0, *, method: str = "median",
                 angle_deg: float | None = None) -> LevelWindow:
    """hercules.geometry.level_mesh on the cut. For a :class:`Cut` the
    rotation is estimated over the window + margin region only (the
    rotation-extra ring does not vote); for a bare sub-mesh or (H, W, 3) grid
    over all of it."""
    if isinstance(cut, Cut):
        pts, reg = cut.points, cut.points[cut.region]
    else:
        pts = cut.points if isinstance(cut, TifxyzMesh) else np.asarray(cut)
        reg = pts
    a, spread = estimate_level_angle(reg, method=method)
    if angle_deg is not None:
        a = float(angle_deg)
    lev = level_mesh(pts, step_vox, angle_deg=a, method=method, crop=True)
    return LevelWindow(level=lev, angle_deg=float(a), spread_deg=float(spread), step_vox=float(step_vox))


# ---------------------------------------------------------------------------
# orient
# ---------------------------------------------------------------------------

@dataclass
class OrientWindow:
    result: OrientResult
    sign_levelled: NormalSignReport  # n . r_out of the oriented levelled grid
    sign_organizer: NormalSignReport  # n . r_out of the ORIGINAL organizer cut
    z_ascending: bool
    convention_sign: int

    @property
    def flip_u(self) -> bool:
        return self.result.flip_u

    @property
    def flip_v(self) -> bool:
        return self.result.flip_v


def orient(levelled: LevelWindow | LevelResult | np.ndarray, centre_curve: CentreLike, z_ascending: bool = True,
           convention_sign: int = 1, *, organizer_points: np.ndarray | None = None,
           cos_thresh: float = 0.3) -> OrientWindow:
    """hercules.geometry.level_mesh.orient_for_reading plus n . r_out sign
    statistics (fraction of vertices with |cos| > cos_thresh; ambiguous flag).

    ``convention_sign`` = chirality sign(det[du, dv, r_out]) of the output grid;
    +1 = viewer on the umbilicus side (u right, v down). The official renderer
    comment (vc_render_tifxyz.cpp 1136-1144) describes the readable standard
    orientation as du x dv pointing outward, i.e. +1; it is a parameter until
    validated on known text.
    """
    pts = levelled.level.points if isinstance(levelled, LevelWindow) else (
        levelled.points if isinstance(levelled, LevelResult) else np.asarray(levelled))
    res = orient_for_reading(pts, bool(z_ascending), int(convention_sign), outward=centre_curve)
    rep_l = normal_sign_report(res.points, vertex_normals(res.points), centre_curve, cos_thresh=cos_thresh)
    op = pts if organizer_points is None else organizer_points
    rep_o = normal_sign_report(op, vertex_normals(op), centre_curve, cos_thresh=cos_thresh)
    return OrientWindow(result=res, sign_levelled=rep_l, sign_organizer=rep_o, z_ascending=bool(z_ascending),
                        convention_sign=int(convention_sign))


# ---------------------------------------------------------------------------
# maps
# ---------------------------------------------------------------------------

@dataclass
class WindowMaps:
    """Exact organizer-canvas <-> levelled-canvas maps (vectorised)."""

    org: C.RenderCanvas  # organizer full canvas, origin (0, 0)
    r0: int
    c0: int
    level: LevelResult
    lev_grid_shape: tuple[int, int]  # levelled grid before flips / padding
    flip_u: bool
    flip_v: bool
    pad_top: int
    pad_left: int
    lev: C.RenderCanvas  # canvas of the final levelled grid, origin (0, 0)
    window: Window  # organizer window
    lev_window: Window  # levelled window on the levelled canvas

    # -- helpers ---------------------------------------------------------
    def _lev_offset(self, frame: str) -> tuple[int, int]:
        if frame == "window":
            return self.lev_window.y0, self.lev_window.x0
        if frame == "canvas":
            return 0, 0
        raise ValueError("frame must be 'window' or 'canvas'")

    def org_to_lev(self, y, x, *, frame: str = "window"):
        """Organizer canvas pixel (y, x) -> levelled pixel (y', x')."""
        v, u = self.org.pixel_to_grid(y, x)
        rl, cl = self.level.to_level_index(u - self.c0, v - self.r0)
        Hl, Wl = self.lev_grid_shape
        if self.flip_v:
            rl = (Hl - 1) - rl
        if self.flip_u:
            cl = (Wl - 1) - cl
        Y, X = self.lev.grid_to_pixel(rl + self.pad_top, cl + self.pad_left)
        oy, ox = self._lev_offset(frame)
        return Y - oy, X - ox

    def lev_to_org(self, y, x, *, frame: str = "window"):
        """Levelled pixel (y, x) -> organizer canvas pixel."""
        oy, ox = self._lev_offset(frame)
        rl, cl = self.lev.pixel_to_grid(np.asarray(y, dtype=np.float64) + oy, np.asarray(x, dtype=np.float64) + ox)
        rl = rl - self.pad_top
        cl = cl - self.pad_left
        Hl, Wl = self.lev_grid_shape
        if self.flip_v:
            rl = (Hl - 1) - rl
        if self.flip_u:
            cl = (Wl - 1) - cl
        L = self.level
        U = L.origin[0] + cl * L.du
        V = L.origin[1] + rl * L.dv
        u = U * L.e_u[0] + V * L.e_v[0]
        v = U * L.e_u[1] + V * L.e_v[1]
        return self.org.grid_to_pixel(v + self.r0, u + self.c0)

    def affine_org_to_lev(self, frame: str = "window") -> np.ndarray:
        """3x3 matrix A with [y', x', 1] = A [y, x, 1] (the map is affine)."""
        pts = np.array([[0.0, 0.0], [1000.0, 0.0], [0.0, 1000.0]])
        yy, xx = self.org_to_lev(pts[:, 0], pts[:, 1], frame=frame)
        M = np.linalg.solve(np.c_[pts, np.ones(3)], np.c_[yy, xx])
        A = np.eye(3)
        A[:2, :] = M.T
        return A

    def render_crop(self, margin_px: int) -> tuple[int, int, int, int]:
        """(x, y, w, h) on the levelled canvas: the levelled window + margin.
        Raises if it leaves the canvas (the renderer would move the origin)."""
        g = self.lev_window.grow(int(margin_px))
        clipped = C.intersect_crop(g.x0, g.y0, g.w, g.h, self.lev.shape)
        if clipped != (g.x0, g.y0, g.w, g.h):
            raise ValueError(f"render crop {(g.x0, g.y0, g.w, g.h)} leaves the levelled canvas {self.lev.shape}")
        return g.x0, g.y0, g.w, g.h


def _make_maps(cut: Cut, lw: LevelWindow, ow: OrientWindow | None, pad_top: int, pad_left: int,
               final_shape: tuple[int, int], lev_size: tuple[int, int]) -> WindowMaps:
    lev_scale = (1.0 / lw.step_vox, 1.0 / lw.step_vox)
    lev = C.RenderCanvas(grid_shape=final_shape, scale=lev_scale)
    m = WindowMaps(org=cut.org_canvas, r0=cut.r0, c0=cut.c0, level=lw.level,
                   lev_grid_shape=tuple(lw.level.points.shape[:2]),
                   flip_u=bool(ow.flip_u) if ow else False, flip_v=bool(ow.flip_v) if ow else False,
                   pad_top=int(pad_top), pad_left=int(pad_left), lev=lev, window=cut.window,
                   lev_window=Window(0, 0, int(lev_size[0]), int(lev_size[1])))
    yc, xc = cut.window.centre
    ylc, xlc = m.org_to_lev(yc, xc, frame="canvas")
    hl, wl = lev_size
    m.lev_window = Window(int(round(float(ylc) - (hl - 1) / 2.0)), int(round(float(xlc) - (wl - 1) / 2.0)), int(hl), int(wl))
    return m


def pad_grid(points: np.ndarray, top: int, bottom: int, left: int, right: int) -> np.ndarray:
    H, W = points.shape[:2]
    out = np.full((H + top + bottom, W + left + right, 3), SENTINEL, dtype=np.float32)
    out[top:top + H, left:left + W] = points
    return out


# ---------------------------------------------------------------------------
# the whole window
# ---------------------------------------------------------------------------

@dataclass
class WindowResult:
    cut: Cut
    level: LevelWindow
    orient: OrientWindow | None
    maps: WindowMaps
    points: np.ndarray  # final levelled (oriented, padded) grid
    step_vox: float
    render_margin_px: int
    stats: dict[str, Any] = field(default_factory=dict)

    def mesh(self, uuid: str, meta: dict | None = None) -> TifxyzMesh:
        s = 1.0 / self.step_vox
        return TifxyzMesh(points=self.points.copy(), scale=(s, s), uuid=uuid, meta=dict(meta or {}))


def _region_rows_cols(cv: C.RenderCanvas, win: Window, shape: tuple[int, int]) -> tuple[slice, slice]:
    v_lo, u_lo = cv.pixel_to_grid(win.y0 - 0.5, win.x0 - 0.5)
    v_hi, u_hi = cv.pixel_to_grid(win.y0 + win.h - 0.5, win.x0 + win.w - 0.5)
    H, W = shape
    return (slice(max(0, int(math.floor(v_lo))), min(H, int(math.ceil(v_hi)) + 1)),
            slice(max(0, int(math.floor(u_lo))), min(W, int(math.ceil(u_hi)) + 1)))


def _sign_dict(rep: NormalSignReport) -> dict[str, Any]:
    return dict(sign=int(rep.sign), frac_clear=float(rep.frac_clear), frac_positive=float(rep.frac_positive),
                ambiguous=bool(rep.ambiguous), n_valid=int(rep.n_valid))


def run_window(mesh: TifxyzMesh, window: Window, centre_curve: CentreLike | None, *, margin_px: int = SEALED_CLEARANCE_PX,
               step_vox: float = 20.0, z_ascending: bool = True, convention_sign: int = 1,
               lev_size: tuple[int, int] | None = None, method: str = "median",
               render_valid_stats: bool = True) -> WindowResult:
    """cut -> level -> orient -> maps (+ padding so that the levelled window +
    margin lies on the levelled canvas). ``centre_curve=None`` skips orient
    (no flips)."""
    cut = cut_window(mesh, window.y0, window.x0, window.h, window.w, margin_px)
    lw = level_window(cut, step_vox, method=method)
    ow = None
    pts = lw.level.points
    if centre_curve is not None:
        ow = orient(lw, centre_curve, z_ascending, convention_sign, organizer_points=cut.points[cut.region])
        pts = ow.result.points
    size = lev_size or (window.h, window.w)
    maps = _make_maps(cut, lw, ow, 0, 0, pts.shape[:2], size)
    g = maps.lev_window.grow(margin_px)
    Hc, Wc = maps.lev.shape
    s = 1.0 / step_vox
    top = int(math.ceil(max(0, -g.y0) * s)) + (1 if g.y0 < 0 else 0)
    left = int(math.ceil(max(0, -g.x0) * s)) + (1 if g.x0 < 0 else 0)
    bottom = int(math.ceil(max(0, g.y0 + g.h - Hc) * s)) + (1 if g.y0 + g.h > Hc else 0)
    right = int(math.ceil(max(0, g.x0 + g.w - Wc) * s)) + (1 if g.x0 + g.w > Wc else 0)
    if top or left or bottom or right:
        pts = pad_grid(pts, top, bottom, left, right)
        maps = _make_maps(cut, lw, ow, top, left, pts.shape[:2], size)
    res = WindowResult(cut=cut, level=lw, orient=ow, maps=maps, points=np.ascontiguousarray(pts, dtype=np.float32),
                       step_vox=float(step_vox), render_margin_px=int(margin_px))
    res.stats = window_stats(res, render_valid_stats=render_valid_stats)
    return res


def window_stats(res: WindowResult, *, render_valid_stats: bool = True) -> dict[str, Any]:
    cut, lw, ow, maps = res.cut, res.level, res.orient, res.maps
    st: dict[str, Any] = {}
    step = res.step_vox
    org_reg = cut.points[cut.region]
    st["cut"] = dict(r0=cut.r0, c0=cut.c0, shape=list(cut.points.shape[:2]),
                     region_shape=list(org_reg.shape[:2]))
    st["angle_deg"] = lw.angle_deg
    st["spread_deg"] = lw.spread_deg
    st["organizer_edge_frac_5pct"] = edge_fraction_within(org_reg, step, 5)
    st["organizer_edge_frac_10pct"] = edge_fraction_within(org_reg, step, 10)
    wr = _region_rows_cols(maps.lev, maps.lev_window.grow(res.render_margin_px), res.points.shape[:2])
    lreg = res.points[wr]
    st["levelled_region_shape"] = list(lreg.shape[:2])
    st["edge_frac_5pct"] = edge_fraction_within(lreg, step, 5)
    st["edge_frac_10pct"] = edge_fraction_within(lreg, step, 10)
    try:
        st["levelled_iso_z_tilt_deg"] = iso_z_tilt_deg(lreg)
        st["levelled_residual_angle_deg"], st["levelled_residual_spread_deg"] = estimate_level_angle(lreg)
    except ValueError:
        st["levelled_iso_z_tilt_deg"] = math.nan
    st["level_metric_vox_per_cell"] = [float(x) for x in lw.level.metric]
    st["level_du_dv"] = [lw.level.du, lw.level.dv]
    A = maps.affine_org_to_lev()
    J = A[:2, :2]
    st["map_det"] = float(np.linalg.det(J))
    st["map_singular_values"] = [float(x) for x in np.linalg.svd(J, compute_uv=False)]
    st["map_mirrored"] = bool(np.linalg.det(J) < 0)
    if ow is not None:
        st["flip_u_mirror"] = bool(ow.flip_u)
        st["flip_v"] = bool(ow.flip_v)
        st["chirality_before"] = int(ow.result.chirality_before)
        st["chirality_after"] = int(ow.result.chirality_after)
        st["z_ascending"] = ow.z_ascending
        st["convention_sign"] = ow.convention_sign
        st["sign_organizer"] = _sign_dict(ow.sign_organizer)
        st["sign_levelled"] = _sign_dict(ow.sign_levelled)
        st["ambiguous"] = bool(ow.sign_levelled.ambiguous or ow.sign_organizer.ambiguous)
    st["pad"] = dict(top=maps.pad_top, left=maps.pad_left, final_shape=list(res.points.shape[:2]))
    st["lev_canvas_shape"] = list(maps.lev.shape)
    st["lev_window"] = dict(y0=maps.lev_window.y0, x0=maps.lev_window.x0, h=maps.lev_window.h, w=maps.lev_window.w)
    st["render_crop_xywh"] = list(maps.render_crop(res.render_margin_px))
    if render_valid_stats:
        cv = maps.lev.with_origin(maps.lev_window.y0, maps.lev_window.x0)
        co, no = C.emulate_gen(res.points, cv, (maps.lev_window.h, maps.lev_window.w))
        st["lev_window_render_valid_frac"] = float(C.render_valid(co, no).mean())
    return st


# ---------------------------------------------------------------------------
# resampling
# ---------------------------------------------------------------------------

def bilinear(img: np.ndarray, y, x) -> np.ndarray:
    """Bilinear sample of a 2-D image at fractional (y, x) (pixel centres at
    integers). NaN outside [0, H-1] x [0, W-1]; a NaN corner gives NaN."""
    a = np.asarray(img, dtype=np.float64)
    H, W = a.shape
    y = np.asarray(y, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    y, x = np.broadcast_arrays(y, x)
    out = np.full(y.shape, np.nan)
    ok = np.isfinite(y) & np.isfinite(x) & (y >= 0) & (y <= H - 1) & (x >= 0) & (x <= W - 1)
    if not ok.any():
        return out
    yy, xx = y[ok], x[ok]
    y0 = np.minimum(np.floor(yy).astype(np.int64), max(H - 2, 0))
    x0 = np.minimum(np.floor(xx).astype(np.int64), max(W - 2, 0))
    y1 = np.minimum(y0 + 1, H - 1)
    x1 = np.minimum(x0 + 1, W - 1)
    ty, tx = yy - y0, xx - x0
    out[ok] = ((a[y0, x0] * (1 - tx) + a[y0, x1] * tx) * (1 - ty) + (a[y1, x0] * (1 - tx) + a[y1, x1] * tx) * ty)
    return out


def resample_to_levelled(image_on_org_canvas: np.ndarray, maps: WindowMaps, out_shape: tuple[int, int], *,
                         org_origin: tuple[int, int] = (0, 0), lev_origin: tuple[int, int] = (0, 0),
                         frame: str = "window") -> np.ndarray:
    """Geometric bilinear resampling of an organizer-canvas image onto the
    levelled frame. Output pixel (i, j) is levelled pixel (i + lev_origin[0],
    j + lev_origin[1]) of ``frame``; ``org_origin`` is the organizer-canvas
    pixel of ``image_on_org_canvas[0, 0]``. NaN outside."""
    h, w = out_shape
    ii, jj = np.mgrid[0:h, 0:w].astype(np.float64)
    y, x = maps.lev_to_org(ii + lev_origin[0], jj + lev_origin[1], frame=frame)
    return bilinear(image_on_org_canvas, y - org_origin[0], x - org_origin[1])


def resample_to_organizer(image_on_lev: np.ndarray, maps: WindowMaps, org_region: Window, *,
                          lev_origin: tuple[int, int] = (0, 0), frame: str = "canvas") -> np.ndarray:
    """Inverse direction: sample a levelled-frame image (whose [0, 0] is
    levelled pixel ``lev_origin`` of ``frame``) at every organizer pixel of
    ``org_region``. NaN outside."""
    ii, jj = np.mgrid[0:org_region.h, 0:org_region.w].astype(np.float64)
    ly, lx = maps.org_to_lev(ii + org_region.y0, jj + org_region.x0, frame=frame)
    return bilinear(image_on_lev, ly - lev_origin[0], lx - lev_origin[1])


# ---------------------------------------------------------------------------
# writing and render command
# ---------------------------------------------------------------------------

def _provenance_first(path: Path) -> None:
    d = json.loads(path.read_text(encoding="utf-8"))
    d.pop("provenance", None)
    out = {"provenance": PROVENANCE.split(": ", 1)[1]}
    out.update(d)
    path.write_text(json.dumps(out, indent=4) + "\n", encoding="utf-8")


def write_levelled_tifxyz(res: WindowResult, path: str | os.PathLike, uuid: str, *, voxel_size_um: float | None = None,
                          source: str = "", overwrite: bool = False) -> Path:
    """Write the final levelled grid with hercules.geometry.tifxyz (C++ layout),
    scale 1/step_vox; meta.json carries the map parameters (provenance key
    first; key order is not significant to the official loader)."""
    m = res.maps
    L = m.level
    meta = dict(
        hercules_source_mesh=str(source),
        hercules_org_window=[m.window.y0, m.window.x0, m.window.h, m.window.w],
        hercules_org_grid_shape=list(m.org.grid_shape),
        hercules_org_scale=list(m.org.scale),
        hercules_cut_r0_c0=[m.r0, m.c0],
        hercules_level_angle_deg=res.level.angle_deg,
        hercules_level_spread_deg=res.level.spread_deg,
        hercules_level_e_u=[float(x) for x in L.e_u],
        hercules_level_e_v=[float(x) for x in L.e_v],
        hercules_level_origin=[float(x) for x in L.origin],
        hercules_level_du_dv=[L.du, L.dv],
        hercules_level_grid_shape=list(m.lev_grid_shape),
        hercules_flip_u=m.flip_u,
        hercules_flip_v=m.flip_v,
        hercules_pad_top_left=[m.pad_top, m.pad_left],
        hercules_lev_window=[m.lev_window.y0, m.lev_window.x0, m.lev_window.h, m.lev_window.w],
        hercules_step_vox=res.step_vox,
    )
    p = write_tifxyz(path, res.mesh(uuid, meta), overwrite=overwrite, voxel_size_um=voxel_size_um)
    _provenance_first(p / "meta.json")
    return p


def volume_url(scroll: str, volume_zarr: str) -> str:
    """s3://vesuvius-challenge-open-data/<scroll>/volumes/<volume>.zarr/"""
    v = volume_zarr if volume_zarr.endswith(".zarr") else volume_zarr + ".zarr"
    return f"s3://{S3_BUCKET}/{scroll}/volumes/{v}/"


def voxel_size_from_metadata(metadata: dict | str | os.PathLike) -> float:
    """Voxel size (um) from a volume metadata.json
    (scan.tomo.acquisition.detector.samplePixelSize, mm)."""
    if not isinstance(metadata, dict):
        metadata = json.loads(Path(metadata).read_text(encoding="utf-8"))
    mm = float(metadata["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    return round(mm * 1000.0, 6)


def render_command(vol_url: str, segmentation: str | os.PathLike, out_zarr: str | os.PathLike, voxel_size_um: float, *,
                   crop_xywh: Sequence[int] | None = None, num_slices: int = 31, slice_step: float = 1.0,
                   flip_normals: bool = True, cache_gb: int = 4, allow_sealed: bool = False,
                   app: str = "vc_render_tifxyz") -> list[str]:
    """Argument list for the official renderer (prefix with /work/bin/vc).

    The levelled canvas origin stays known because a manual crop that lies
    inside the canvas is the output origin exactly (canvas.py); --auto-crop is
    never used. ``flip_normals`` should come from
    canvas.flip_normals_after_orient to keep the organizer SV slice direction.
    """
    if not allow_sealed and any(s in vol_url for s in SEALED_SCROLLS):
        raise PermissionError("rendering a sealed scroll is not allowed until its seal is committed")
    cmd = [app, "-v", vol_url, "--remote-url", vol_url, "--segmentation", str(segmentation),
           "--scale", "1", "--group-idx", "0", "--num-slices", str(int(num_slices)),
           "--slice-step", f"{float(slice_step):g}", "--voxel-size", f"{float(voxel_size_um):g}",
           "--voxel-unit", "micrometer"]
    if crop_xywh is not None:
        x, y, w, h = (int(v) for v in crop_xywh)
        cmd += ["--crop-x", str(x), "--crop-y", str(y), "--crop-width", str(w), "--crop-height", str(h)]
    if flip_normals:
        cmd.append("--flip-normals")
    cmd += ["--cache-gb", str(int(cache_gb)), "--zarr-output", str(out_zarr)]
    return cmd


# ---------------------------------------------------------------------------
# alignment gate
# ---------------------------------------------------------------------------

def ncc(a: np.ndarray, b: np.ndarray, min_valid: int = 100) -> tuple[float, int]:
    """Zero-mean normalised cross-correlation over pixels finite in both."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ok = np.isfinite(a) & np.isfinite(b)
    n = int(ok.sum())
    if n < min_valid:
        return math.nan, n
    x = a[ok] - a[ok].mean()
    y = b[ok] - b[ok].mean()
    den = math.sqrt(float(np.dot(x, x)) * float(np.dot(y, y)))
    return (float(np.dot(x, y)) / den if den > 0 else math.nan), n


def alignment_gate(our_render_stack, organizer_sv, maps: WindowMaps, window: Window | None = None, *,
                   render_origin: tuple[int, int] | None = None, render_margin_px: int | None = None,
                   max_shift: int = 5, pass_ncc: float = 0.80, pass_shift_px: float = 2.0,
                   sv_slices: Sequence[int] | None = None, zero_is_invalid: bool = True) -> dict[str, Any]:
    """Our levelled render slice n//2 (offset 0), resampled onto the organizer
    canvas, vs the organizer SV mean of its surface slices (13, 14 for 28
    slices: offsets +-0.5), NCC over the window at integer shifts within
    +-max_shift. PASS iff best NCC >= pass_ncc at Euclidean |shift| <=
    pass_shift_px. Shift (dy, dx): our image taken at organizer (y+dy, x+dx).

    ``our_render_stack`` is (n, h, w) whose [.., 0, 0] is levelled-canvas pixel
    ``render_origin`` (default: the render crop of ``render_margin_px``).
    ``organizer_sv`` is the full organizer SV (n_sv, Hc, Wc) (numpy or zarr).
    Pixels equal to 0 (the renderer's empty value) are invalid in both.
    """
    win = window or maps.window
    n = int(our_render_stack.shape[0])
    k = n // 2
    offs = C.slice_offsets(n)
    if render_origin is None:
        x, y, _, _ = maps.render_crop(render_margin_px if render_margin_px is not None else 0)
        render_origin = (y, x)
    ours = np.asarray(our_render_stack[k], dtype=np.float64)
    if zero_is_invalid:
        ours = np.where(ours == 0, np.nan, ours)
    S = int(max_shift)
    big = Window(win.y0 - S, win.x0 - S, win.h + 2 * S, win.w + 2 * S)
    ours_org = resample_to_organizer(ours, maps, big, lev_origin=render_origin, frame="canvas")
    ns = int(organizer_sv.shape[0])
    sl = list(sv_slices) if sv_slices is not None else C.surface_slices(ns)
    sv = np.zeros((win.h, win.w), dtype=np.float64)
    bad = np.zeros((win.h, win.w), dtype=bool)
    for i in sl:
        a = np.asarray(organizer_sv[i, win.y0:win.y0 + win.h, win.x0:win.x0 + win.w], dtype=np.float64)
        if a.shape != (win.h, win.w):
            raise ValueError("window leaves the organizer SV")
        bad |= (a == 0) if zero_is_invalid else ~np.isfinite(a)
        sv += a
    sv /= len(sl)
    sv[bad] = np.nan
    grid = np.full((2 * S + 1, 2 * S + 1), np.nan)
    for dy in range(-S, S + 1):
        for dx in range(-S, S + 1):
            a = ours_org[S + dy:S + dy + win.h, S + dx:S + dx + win.w]
            grid[dy + S, dx + S] = ncc(a, sv)[0]
    ncc0, nvalid = ncc(ours_org[S:S + win.h, S:S + win.w], sv)
    bi = np.unravel_index(np.nanargmax(grid), grid.shape)
    best = (int(bi[0] - S), int(bi[1] - S))
    best_ncc = float(grid[bi])
    norm = math.hypot(*best)
    ctrl = {f"{dy},{dx}": float(grid[dy + S, dx + S]) for dy, dx in ((S, 0), (-S, 0), (0, S), (0, -S))}
    return dict(
        render_slice=k, render_slice_offset=float(offs[k]), sv_slices=sl,
        sv_slice_offsets=[float(C.slice_offsets(ns)[i]) for i in sl],
        ncc_zero_shift=float(ncc0), n_valid=nvalid, best_shift=list(best), best_shift_norm=norm,
        best_ncc=best_ncc, control_shift_px=S, control_ncc=ctrl, control_ncc_max=max(ctrl.values()),
        passed=bool(best_ncc >= pass_ncc and norm <= pass_shift_px), pass_ncc=pass_ncc, pass_shift_px=pass_shift_px,
        ncc_grid=grid.tolist(), valid_frac_ours=float(np.isfinite(ours_org[S:S + win.h, S:S + win.w]).mean()),
        valid_frac_sv=float(np.isfinite(sv).mean()),
    )
