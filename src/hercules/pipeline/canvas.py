# Provenance: Project HERCULES | owner the owner | [id removed]
"""The official renderer's canvas: output pixel <-> tifxyz grid coordinate.

Source: ScrollPrize/villa commit 41701aa0eaa1aa765523db3f9f972b5830abf549
(/work/villa). Abbreviations: ``R`` = volume-cartographer/apps/src/
vc_render_tifxyz.cpp, ``QS`` = volume-cartographer/core/src/QuadSurface.cpp,
``GEO`` = volume-cartographer/core/src/Geometry.cpp. Every statement below was
also checked by rendering synthetic ramp volumes with the built binary
(``/work/bin/vc vc_render_tifxyz``; tests/test_pipeline_canvas.py).

Canvas size (R 1594-1611): for a grid of W columns x H rows with meta
``scale = [s_u, s_v]`` and ``render_scale = Pg * scale_segmentation * sA *
2^-group`` (= 1 for ``--scale 1 --group-idx 0`` and no affine):
``Wc = lround(W * render_scale / f32(s_u))``, ``Hc`` likewise. ``_scale`` is a
``cv::Vec2f``, so s is used as a float32 (0.05 -> 0.0500000007).

Pixel -> grid (R 279-283 computeCanvasOrigin; R 546-552 / 662-665 / 877-881
add crop.x, crop.y and the tile offset; QS 281-296 ``_center = N / 2 / s``;
QS 761-764 internal_loc; QS 1299 ``ul = (offset/scale + _center) * _scale``;
QS 1310-1313 ``sx = s/scale, ox = ul - 4 sx``; QS 1446 the 4 px halo is
cropped away). Output pixel i of a band that starts at canvas pixel P0 samples
grid column ``ox + (i + 4) sx``; with canvas pixel ``P = crop.x + x0 + i``:

    u(P) = (s_u / render_scale) * (P - (Wc - 1) / 2) + W / 2
         = s_u (P + 0.5)        when Wc = W / s_u exactly (render_scale 1)

and the same for v with rows. So at ``--scale 1`` pixel P samples grid
coordinate (P + 0.5) s, i.e. (P + 0.5)/20 for s = 0.05: "(P+0.5)/20" is right.
Consequence for the 2.4 -> 9 um label map: the organizer meshes satisfy
(g2 + 0.5) = r (g9 + 0.5) per axis (fitted intercept 1.4503 grid = 0.5 (r - 1),
/work/bank/0841/meshcorr.json), which with g = (P + 0.5)/20 gives
``c9 = (c2 + 10.5) N9/N2 - 10.5`` exactly. The declared formula's offset 10
omits the renderer's half pixel (0.5 px on the 2.4 um canvas; 0.37 px on the
9 um canvas); 10.5 is the code-consistent value.

Sampling (QS 545-588, 1384): xyz is bilinear over the 4 surrounding grid
vertices with the source coordinate clamped to [0, W-1] (replicate border); a
NaN (invalid, R 1583 turns -1 into NaN) corner makes the pixel NaN.
Validity (QS 596-625, 1389): the NEAREST vertex (C lround) must be valid.
Normals (QS 1400-1440, GEO 29-60): the nearest vertex's
``normalize((p[r,c+1]-p[r,c-1]) x (p[r+1,c]-p[r-1,c]))`` = du x dv; NaN on the
grid border and next to an invalid N/S/E/W neighbour. A NaN normal leaves the
pixel empty in every slice (checked: a pixel whose nearest vertex is on the
grid border renders 0 even at offset 0), so the valid render is inset by
half a cell (10 px) from the valid grid.

--auto-crop (R 1584-1592, 1626-1632): ``crop = (floor(col_min*sx),
floor(row_min*sy), ceil((col_max+1)*sx) - floor(col_min*sx), ...) & canvas``
with ``sx = render_scale / f32(s_u)`` over valid vertices. The output origin is
that crop's (x, y): e.g. col_min = 2 at s = 0.05 gives x = floor(39.9999994)
= 39, NOT 40 (verified). Manual ``--crop-*`` (R 1633-1636) is intersected with
the canvas, so a crop that leaves the canvas silently moves the origin.

Slices (R 353-373 buildOffsetList): slice k of ``-n N`` lies at signed
distance ``(k - 0.5 (N - 1)) * slice_step`` along the unit normal: N = 31 puts
the surface at slice 15; N = 28 puts it between slices 13 and 14 (+-0.5).
--flip-normals (R 306, 1352, help comment R 1136-1144) negates the normal, so
slice index grows along -(du x dv); the official comment says that with the
standard orientation (v down = +z, text readable, u winding outside -> inside)
du x dv points to the scroll OUTSIDE, so --flip-normals makes the stack grow
toward the scroll centre.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np

from hercules.geometry.tifxyz import valid_mask

VILLA_COMMIT = "41701aa0eaa1aa765523db3f9f972b5830abf549"


def f32(x: float) -> float:
    """The value a C++ ``float`` holds for ``x``."""
    return float(np.float32(x))


def c_lround(x):
    """C ``lround``: round half away from zero (numpy arrays or scalars)."""
    a = np.asarray(x, dtype=np.float64)
    r = np.sign(a) * np.floor(np.abs(a) + 0.5)
    return r.astype(np.int64) if r.ndim else int(r)


@dataclass(frozen=True)
class RenderCanvas:
    """Canvas of one tifxyz grid rendered by vc_render_tifxyz.

    grid_shape   : (H, W) = (rows, cols) of the tifxyz grid
    scale        : (s_u, s_v) exactly as in meta.json
    render_scale : Pg * scale_segmentation * sA * 2^-group (1 for --scale 1 -g 0)
    origin       : canvas (row, col) of output pixel (0, 0), i.e. (crop.y, crop.x)
    """

    grid_shape: tuple[int, int]
    scale: tuple[float, float]
    render_scale: float = 1.0
    origin: tuple[int, int] = (0, 0)

    @property
    def shape(self) -> tuple[int, int]:
        """Full canvas (Hc, Wc) (R 1605-1611)."""
        H, W = self.grid_shape
        su, sv = f32(self.scale[0]), f32(self.scale[1])
        rs = float(self.render_scale)
        return (max(1, c_lround(H * rs / sv)), max(1, c_lround(W * rs / su)))

    def with_origin(self, row: int, col: int) -> "RenderCanvas":
        return replace(self, origin=(int(row), int(col)))

    def pixel_to_grid(self, row, col):
        """Output pixel (row, col) -> fractional grid (v, u) sampled there."""
        H, W = self.grid_shape
        Hc, Wc = self.shape
        su, sv = f32(self.scale[0]), f32(self.scale[1])
        rs = float(self.render_scale)
        P = np.asarray(col, dtype=np.float64) + self.origin[1]
        Q = np.asarray(row, dtype=np.float64) + self.origin[0]
        u = (su / rs) * (P - 0.5 * (Wc - 1)) + 0.5 * W
        v = (sv / rs) * (Q - 0.5 * (Hc - 1)) + 0.5 * H
        return v, u

    def grid_to_pixel(self, v, u):
        """Exact inverse of :meth:`pixel_to_grid`: grid (v, u) -> output (row, col)."""
        H, W = self.grid_shape
        Hc, Wc = self.shape
        su, sv = f32(self.scale[0]), f32(self.scale[1])
        rs = float(self.render_scale)
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        P = (u - 0.5 * W) * rs / su + 0.5 * (Wc - 1)
        Q = (v - 0.5 * H) * rs / sv + 0.5 * (Hc - 1)
        return Q - self.origin[0], P - self.origin[1]


def canvas_for(points_or_shape, scale, render_scale: float = 1.0) -> RenderCanvas:
    shp = points_or_shape if isinstance(points_or_shape, tuple) else np.asarray(points_or_shape).shape[:2]
    return RenderCanvas(grid_shape=(int(shp[0]), int(shp[1])), scale=(float(scale[0]), float(scale[1])),
                        render_scale=float(render_scale))


def intersect_crop(x: int, y: int, w: int, h: int, canvas_shape: tuple[int, int]) -> tuple[int, int, int, int]:
    """``cv::Rect(x, y, w, h) & canvas`` as the renderer does for --crop-* (R 1634)."""
    Hc, Wc = canvas_shape
    x0, y0 = max(int(x), 0), max(int(y), 0)
    x1, y1 = min(int(x) + int(w), Wc), min(int(y) + int(h), Hc)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("crop outside canvas")
    return x0, y0, x1 - x0, y1 - y0


def auto_crop_rect(points: np.ndarray, scale, render_scale: float = 1.0) -> tuple[int, int, int, int]:
    """(x, y, w, h) that --auto-crop selects (R 1584-1592, 1626-1632)."""
    v = valid_mask(np.asarray(points))
    if not v.any():
        raise ValueError("no valid vertex")
    rows = np.nonzero(v.any(axis=1))[0]
    cols = np.nonzero(v.any(axis=0))[0]
    sx = float(render_scale) / f32(scale[0])
    sy = float(render_scale) / f32(scale[1])
    x = int(math.floor(cols[0] * sx))
    y = int(math.floor(rows[0] * sy))
    w = int(math.ceil((cols[-1] + 1) * sx)) - x
    h = int(math.ceil((rows[-1] + 1) * sy)) - y
    cv = canvas_for(np.asarray(points), scale, render_scale)
    return intersect_crop(x, y, w, h, cv.shape)


def slice_offsets(n: int, slice_step: float = 1.0) -> np.ndarray:
    """Signed distance of every slice from the surface (R 359-373)."""
    n1 = max(1, int(n))
    centre = 0.5 * (n1 - 1.0)
    return np.array([np.float32((k - centre) * float(slice_step)) for k in range(int(n))], dtype=np.float64)


def surface_slices(n: int) -> list[int]:
    """Slice index(es) nearest the surface: [n//2] for odd n, [n/2-1, n/2] for even n."""
    off = np.abs(slice_offsets(n))
    return [int(i) for i in np.nonzero(np.isclose(off, off.min()))[0]]


def slice_normal_sign(flip_normals: bool) -> int:
    """+1: slice index grows along normalize(du x dv); -1 with --flip-normals."""
    return -1 if flip_normals else 1


def flip_normals_after_orient(base_flip: bool, flip_u: bool, flip_v: bool) -> bool:
    """--flip-normals value for a grid mirrored in u and/or v that keeps the
    physical slice direction of a render of the unmirrored grid made with
    ``base_flip``: each single-axis mirror negates du x dv."""
    return bool(base_flip) != (bool(flip_u) != bool(flip_v))


def vertex_normals_official(points: np.ndarray) -> np.ndarray:
    """Per-vertex normal as the renderer caches it (QS 1400-1433, GEO 29-60):
    central differences of the 4 neighbours, NaN on the grid border, where a
    neighbour is invalid, or where the vertex itself is invalid (the latter is
    masked by the validity pass anyway)."""
    p = np.asarray(points, dtype=np.float64)
    H, W = p.shape[:2]
    n = np.full(p.shape, np.nan)
    if H < 3 or W < 3:
        return n
    ok = valid_mask(p)
    xv = p[1:-1, 2:] - p[1:-1, :-2]
    yv = p[2:, 1:-1] - p[:-2, 1:-1]
    c = np.cross(xv, yv)
    L = np.linalg.norm(c, axis=-1, keepdims=True)
    good = ok[1:-1, 2:] & ok[1:-1, :-2] & ok[2:, 1:-1] & ok[:-2, 1:-1] & ok[1:-1, 1:-1] & (L[..., 0] > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        c = c / L
    c[~good] = np.nan
    n[1:-1, 1:-1] = c
    return n


def emulate_gen(points: np.ndarray, canvas: RenderCanvas, out_shape: tuple[int, int]):
    """Python emulation of QuadSurface::gen for a single-component surface.

    Returns (coords, normals), each (h, w, 3) float64 with NaN where the
    renderer leaves the pixel empty: bilinear xyz with a clamped source
    coordinate, NaN if any bilinear corner is invalid or the nearest vertex is
    invalid; normal of the nearest vertex (NaN if not computable). A pixel is
    rendered iff both are finite (see :func:`render_valid`).
    """
    p = np.asarray(points, dtype=np.float64).copy()
    ok = valid_mask(p)
    p[~ok] = np.nan
    H, W = p.shape[:2]
    h, w = out_shape
    v, _ = canvas.pixel_to_grid(np.arange(h, dtype=np.float64), 0.0)
    _, u = canvas.pixel_to_grid(0.0, np.arange(w, dtype=np.float64))
    fx = np.clip(u, 0, W - 1)
    fy = np.clip(v, 0, H - 1)
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    x1 = np.minimum(x0 + 1, W - 1)
    y1 = np.minimum(y0 + 1, H - 1)
    wx = (fx - x0)[None, :, None]
    wy = (fy - y0)[:, None, None]
    Y0, X0 = np.meshgrid(y0, x0, indexing="ij")
    Y1, X1 = np.meshgrid(y1, x1, indexing="ij")
    coords = ((p[Y0, X0] * (1 - wx) + p[Y0, X1] * wx) * (1 - wy)
              + (p[Y1, X0] * (1 - wx) + p[Y1, X1] * wx) * wy)
    xi = c_lround(u)
    yi = c_lround(v)
    inx = (xi >= 0) & (xi < W)
    iny = (yi >= 0) & (yi < H)
    YI, XI = np.meshgrid(np.clip(yi, 0, H - 1), np.clip(xi, 0, W - 1), indexing="ij")
    near_ok = ok[YI, XI] & iny[:, None] & inx[None, :]
    nrm_v = vertex_normals_official(np.where(ok[..., None], p, -1.0))
    normals = nrm_v[YI, XI]
    normals[~(iny[:, None] & inx[None, :])] = np.nan
    coords[~near_ok] = np.nan
    normals[~near_ok] = np.nan
    return coords, normals


def render_valid(coords: np.ndarray, normals: np.ndarray) -> np.ndarray:
    """Pixels the renderer fills: finite xyz and finite normal."""
    return np.isfinite(coords).all(-1) & np.isfinite(normals).all(-1)
