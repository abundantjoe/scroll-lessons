# Provenance: Project HERCULES | owner the owner | [id removed]
"""Coordinate mapping between the 2.4 um reference canvas and the 9 um canvas.

Per axis, with N2 and N9 the extents of the SAME mesh on the 2.4 um and 9 um
canvases and a fixed offset of 10 px:

    c9 = (c2 + 10) * N9 / N2 - 10
    c2 = (c9 + 10) * N2 / N9 - 10          (exact inverse)

Axis order of every (..., 2) array and extent pair is (x, y) = (column, row).
The offset (10) and the extents are inputs; they are not derived here and
must be validated against real canvas pairs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

OFFSET_PX = 10.0


def _pair(n) -> np.ndarray:
    a = np.asarray(n, dtype=np.float64)
    if a.shape == ():
        a = np.array([a, a])
    if a.shape != (2,) or np.any(a <= 0):
        raise ValueError("extents must be positive scalars or (x, y) pairs")
    return a


def map_2p4_to_9(c2, n2, n9, offset: float = OFFSET_PX) -> np.ndarray:
    """2.4 um canvas coordinate(s) -> 9 um canvas.

    ``c2``: scalar or (..., 2) array of (x, y); ``n2``/``n9``: scalar (one
    axis) or (x, y) extents."""
    c = np.asarray(c2, dtype=np.float64)
    if c.ndim == 0:
        return (c + offset) * float(n9) / float(n2) - offset
    r = _pair(n9) / _pair(n2)
    return (c + offset) * r - offset


def map_9_to_2p4(c9, n2, n9, offset: float = OFFSET_PX) -> np.ndarray:
    """Inverse of :func:`map_2p4_to_9`."""
    c = np.asarray(c9, dtype=np.float64)
    if c.ndim == 0:
        return (c + offset) * float(n2) / float(n9) - offset
    r = _pair(n2) / _pair(n9)
    return (c + offset) * r - offset


@dataclass
class Window:
    x0: int
    y0: int
    x1: int  # exclusive
    y1: int  # exclusive

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0


def map_window_2p4_to_9(
    x0: float, y0: float, x1: float, y1: float, n2, n9, *, clamp: bool = True, offset: float = OFFSET_PX
) -> Window:
    """Map a half-open pixel window [x0, x1) x [y0, y1) from the 2.4 um canvas
    to the smallest enclosing integer window on the 9 um canvas (floor of the
    mapped start, ceil of the mapped end), optionally clamped to [0, N9]."""
    lo = map_2p4_to_9(np.array([x0, y0], dtype=np.float64), n2, n9, offset)
    hi = map_2p4_to_9(np.array([x1, y1], dtype=np.float64), n2, n9, offset)
    w = Window(int(math.floor(lo[0] + 1e-9)), int(math.floor(lo[1] + 1e-9)),
               int(math.ceil(hi[0] - 1e-9)), int(math.ceil(hi[1] - 1e-9)))
    if clamp:
        N9 = _pair(n9)
        w = Window(max(0, w.x0), max(0, w.y0), min(int(N9[0]), w.x1), min(int(N9[1]), w.y1))
    return w


def map_window_9_to_2p4(
    x0: float, y0: float, x1: float, y1: float, n2, n9, *, clamp: bool = True, offset: float = OFFSET_PX
) -> Window:
    """Inverse direction of :func:`map_window_2p4_to_9`."""
    lo = map_9_to_2p4(np.array([x0, y0], dtype=np.float64), n2, n9, offset)
    hi = map_9_to_2p4(np.array([x1, y1], dtype=np.float64), n2, n9, offset)
    w = Window(int(math.floor(lo[0] + 1e-9)), int(math.floor(lo[1] + 1e-9)),
               int(math.ceil(hi[0] - 1e-9)), int(math.ceil(hi[1] - 1e-9)))
    if clamp:
        N2 = _pair(n2)
        w = Window(max(0, w.x0), max(0, w.y0), min(int(N2[0]), w.x1), min(int(N2[1]), w.y1))
    return w
