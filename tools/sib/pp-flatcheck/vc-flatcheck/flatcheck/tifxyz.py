"""Minimal tifxyz reader/writer.

A tifxyz mesh is a directory with ``x.tif``, ``y.tif``, ``z.tif`` (float32
grids of voxel coordinates, -1 = invalid) and ``meta.json`` whose ``scale``
is grid vertices per voxel, so the nominal grid step is ``1/scale`` voxels.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import tifffile


def read_tifxyz(path: str | Path) -> tuple[np.ndarray, dict]:
    """Return ``(points (H, W, 3) float64, meta dict)``. Invalid vertices
    (any coordinate -1 or non-finite, or 0 in an optional ``mask.tif``) are
    set to (-1, -1, -1)."""
    d = Path(path)
    pts = np.stack([tifffile.imread(d / f"{a}.tif").astype(np.float64) for a in "xyz"], -1)
    meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
    bad = ~np.isfinite(pts).all(-1) | np.any(pts == -1.0, -1)
    if (d / "mask.tif").exists():
        m = tifffile.imread(d / "mask.tif")
        if m.ndim == 3:
            m = m[..., 0]
        if m.shape == bad.shape:
            bad |= m == 0
    pts[bad] = -1.0
    return pts, meta


def step_from_meta(meta: dict) -> float | None:
    sc = meta.get("scale")
    if not sc:
        return None
    return 1.0 / float(sc[0])


def write_tifxyz(path: str | Path, points: np.ndarray, step: float = 20.0, uuid: str = "mesh") -> None:
    d = Path(path)
    d.mkdir(parents=True, exist_ok=True)
    p = np.asarray(points, np.float32)
    for i, a in enumerate("xyz"):
        tifffile.imwrite(d / f"{a}.tif", np.ascontiguousarray(p[..., i]), metadata=None)
    ok = np.all(p != -1, -1)
    q = p[ok] if ok.any() else np.zeros((1, 3))
    meta = {"bbox": [q.min(0).tolist(), q.max(0).tolist()], "format": "tifxyz",
            "scale": [1.0 / step, 1.0 / step], "type": "seg", "uuid": uuid}
    (d / "meta.json").write_text(json.dumps(meta, indent=4, sort_keys=True))


def read_uv(u_path: str | Path, v_path: str | Path) -> np.ndarray:
    """(H, W, 2) UV grid from two float TIFFs; -1 or non-finite = undefined."""
    u = tifffile.imread(u_path).astype(np.float64)
    v = tifffile.imread(v_path).astype(np.float64)
    uv = np.stack([u, v], -1)
    uv[(u == -1) | (v == -1) | ~np.isfinite(u) | ~np.isfinite(v)] = np.nan
    return uv


def write_uv(u_path: str | Path, v_path: str | Path, uv: np.ndarray) -> None:
    bad = ~np.isfinite(uv).all(-1)
    for path, k in ((u_path, 0), (v_path, 1)):
        tifffile.imwrite(path, np.where(bad, -1.0, uv[..., k]).astype("<f4"), metadata=None)
