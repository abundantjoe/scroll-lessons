# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic tifxyz-like grids of an Archimedean spiral sheet (DECL-P4-7 item 3
metric tests). Geometry and synthetic numbers only: no CT, no image.

Spiral (in the frame of a possibly z-varying roll axis ``umb(z) -> (ux, uy)``)::

    r(theta) = r0 + pitch * theta / (2 pi),  theta >= 0 (absolute angle)
    x = ux(z) + sx * (r + dr) * cos(theta)
    y = uy(z) + sy * (r + dr) * sin(theta)

Winding n occupies theta in [2 pi n, 2 pi (n + 1)), so "w010" is the turn
``turn_start=10``. Grid rows are iso-z lines (z0 + i * step), columns are
samples at arc-length step ``step`` (default 20 vox) along the (unsquashed)
spiral. ``points[r, c] = (x, y, z)`` float64, invalid = (-1, -1, -1).

Planted defects (each a separate helper so tests can combine them):
  (a) ``fold_offsets``      prolate-cycloid loop (a > 1): the sheet folds back
                            and passes through itself -> true self-intersection;
  (b) ``jump_offsets``      from column ``c_jump`` on, dr = -pitch: the trace
                            hops to the adjacent inner winding mid-mesh;
  (c) ``dr`` = +0.7 pitch   trace at 30 % of the spacing from the outer
                            neighbour (see tests);
  (d) ``bump_offsets``      Gaussian radial bump: a doubly curved,
                            non-developable patch;
  (e) ``hv_fibre_texture`` / ``isotropic_texture`` / ``diagonal_fibre_texture``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy import ndimage

TWO_PI = 2.0 * math.pi


def make_umbilicus(cx: float = 0.0, cy: float = 0.0, drift: tuple[float, float] = (0.0, 0.0),
                   wobble: float = 0.0, period: float = 4000.0) -> Callable:
    """Roll axis umb(z) -> (ux, uy): straight line (drift per vox of z) plus an
    optional sinusoidal wobble of amplitude ``wobble`` (vox)."""
    def umb(z):
        z = np.asarray(z, dtype=np.float64)
        ux = cx + drift[0] * z + wobble * np.sin(TWO_PI * z / period)
        uy = cy + drift[1] * z + wobble * np.cos(TWO_PI * z / period)
        return ux, uy
    return umb


@dataclass
class Spiral:
    r0: float = 40.0
    pitch: float = 60.0
    squash: tuple[float, float] = (1.0, 1.0)
    umb: Callable = field(default_factory=make_umbilicus)

    def radius(self, theta):
        return self.r0 + self.pitch * np.asarray(theta, dtype=np.float64) / TWO_PI

    def _arc_table(self, th0: float, th1: float, n: int = 20001):
        th = np.linspace(th0, th1, n)
        b = self.pitch / TWO_PI
        speed = np.sqrt(self.radius(th) ** 2 + b * b)
        s = np.concatenate([[0.0], np.cumsum(0.5 * (speed[1:] + speed[:-1]) * np.diff(th))])
        return th, s

    def point(self, theta, z, dr=0.0):
        theta = np.asarray(theta, dtype=np.float64)
        z = np.asarray(z, dtype=np.float64)
        r = self.radius(theta) + dr
        ux, uy = self.umb(z)
        return np.stack([ux + self.squash[0] * r * np.cos(theta),
                         uy + self.squash[1] * r * np.sin(theta),
                         np.broadcast_to(z, np.broadcast(theta, z).shape)], -1)


def spiral_grid(sp: Spiral, turn_start: float, turn_end: float, z0: float, z1: float, *,
                step: float = 20.0, noise: float = 0.0, rng: np.random.Generator | None = None,
                dr: np.ndarray | Callable | None = None, ds: np.ndarray | None = None) -> dict:
    """Grid of the spiral between absolute turns [turn_start, turn_end] and
    z in [z0, z1]. ``dr``: extra radial offset, (H, W) array or callable
    (s_col (W,), z_row (H,)) -> (H, W). ``ds``: extra arc-length offset
    (W,) or (H, W). Returns dict(points, theta (H, W) absolute angle before
    ds, s (W,), z (H,))."""
    th_tab, s_tab = sp._arc_table(TWO_PI * turn_start, TWO_PI * turn_end)
    s_cols = np.arange(0.0, s_tab[-1] + 1e-9, step)
    z_rows = np.arange(z0, z1 + 1e-9, step)
    H, W = z_rows.size, s_cols.size
    S = np.broadcast_to(s_cols[None, :], (H, W)).astype(np.float64)
    if ds is not None:
        S = S + np.broadcast_to(ds, (H, W))
    # extrapolate linearly outside the table (folds may push s slightly out)
    th = np.interp(S, s_tab, th_tab)
    lo, hi = S < 0, S > s_tab[-1]
    th[lo] = th_tab[0] + S[lo] / sp.radius(th_tab[0])
    th[hi] = th_tab[-1] + (S[hi] - s_tab[-1]) / sp.radius(th_tab[-1])
    Z = np.broadcast_to(z_rows[:, None], (H, W))
    if callable(dr):
        DR = np.asarray(dr(s_cols, z_rows), dtype=np.float64)
    elif dr is None:
        DR = 0.0
    else:
        DR = np.broadcast_to(np.asarray(dr, dtype=np.float64), (H, W))
    P = sp.point(th, Z, DR)
    if noise > 0:
        rng = rng or np.random.default_rng(0)
        P = P + rng.normal(0.0, noise, P.shape)
    theta_nominal = np.interp(np.broadcast_to(s_cols[None, :], (H, W)), s_tab, th_tab)
    return {"points": P, "theta": theta_nominal, "s": s_cols, "z": z_rows}


# ---------------------------------------------------------------------------
# planted defects
# ---------------------------------------------------------------------------

def fold_offsets(W: int, c0: int, K: int = 16, a: float = 2.5, b: float = 12.0, step: float = 20.0):
    """(ds (W,), dr (W,)) of a prolate-cycloid loop over columns [c0, c0 + K].
    With t = 2 pi (c - c0) / K - pi in [-pi, pi] the local curve is
    s = S (t - a sin t) / 2 pi, n = b (1 + cos t), S = K * step; for a > 1
    ds/dt < 0 around t = 0 and the curve crosses itself at +-t1 with
    t1 = a sin t1, so the sheet extruded along z self-intersects along a
    line. Outside the window ds = dr = 0 (continuous at t = +-pi)."""
    c = np.arange(W, dtype=np.float64)
    t = TWO_PI * (c - c0) / K - math.pi
    inside = (c >= c0) & (c <= c0 + K)
    ds = np.where(inside, -a * np.sin(t) * K * step / TWO_PI, 0.0)
    dr = np.where(inside, b * (1.0 + np.cos(t)), 0.0)
    return ds, dr


def jump_offsets(H: int, W: int, c_jump: int, pitch: float) -> np.ndarray:
    """dr (H, W): -pitch from column c_jump on (hop to the adjacent inner
    winding, theta continuous)."""
    dr = np.zeros((H, W))
    dr[:, c_jump:] = -pitch
    return dr


def bump_offsets(amp: float, sigma: float, s_c: float | None = None, z_c: float | None = None) -> Callable:
    """Callable dr(s_cols, z_rows): Gaussian radial bump (doubly curved)."""
    def f(s_cols, z_rows):
        sc = 0.5 * (s_cols[0] + s_cols[-1]) if s_c is None else s_c
        zc = 0.5 * (z_rows[0] + z_rows[-1]) if z_c is None else z_c
        S, Z = np.meshgrid(s_cols, z_rows)
        return amp * np.exp(-((S - sc) ** 2 + (Z - zc) ** 2) / (2 * sigma ** 2))
    return f


def invalidate(points: np.ndarray, mask: np.ndarray) -> np.ndarray:
    p = np.array(points, dtype=np.float64, copy=True)
    p[mask] = -1.0
    return p


# ---------------------------------------------------------------------------
# textures (synthetic arrays only)
# ---------------------------------------------------------------------------

def _streaks(shape, rng, sigma_long, sigma_short, axis):
    n = rng.normal(size=shape)
    sig = (sigma_long, sigma_short) if axis == 0 else (sigma_short, sigma_long)
    f = ndimage.gaussian_filter(n, sig, mode="wrap")
    return f / f.std()


def hv_fibre_texture(shape=(512, 512), rng=None, *, sigma_long=16.0, sigma_short=1.0,
                     w_h=1.0, w_v=1.0, noise=0.1) -> np.ndarray:
    """Crossed horizontal (along axis 1) and vertical (along axis 0) fibres
    plus white noise of relative std ``noise``."""
    rng = rng or np.random.default_rng(0)
    t = w_h * _streaks(shape, rng, sigma_long, sigma_short, 1) + w_v * _streaks(shape, rng, sigma_long, sigma_short, 0)
    return t + noise * t.std() * rng.normal(size=shape)


def isotropic_texture(shape=(512, 512), rng=None, *, sigma=1.5) -> np.ndarray:
    rng = rng or np.random.default_rng(0)
    return ndimage.gaussian_filter(rng.normal(size=shape), sigma, mode="wrap")


def diagonal_fibre_texture(shape=(512, 512), rng=None, *, angle_deg=45.0, **kw) -> np.ndarray:
    """H+V fibre texture rotated by angle_deg (45 deg -> fibres on diagonals)."""
    rng = rng or np.random.default_rng(0)
    big = int(math.ceil(max(shape) * 1.5))
    t = hv_fibre_texture((big, big), rng, **kw)
    r = ndimage.rotate(t, angle_deg, reshape=False, order=1, mode="wrap")
    o0, o1 = (big - shape[0]) // 2, (big - shape[1]) // 2
    return r[o0:o0 + shape[0], o1:o1 + shape[1]]
