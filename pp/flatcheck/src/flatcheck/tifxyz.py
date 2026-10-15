"""Minimal tifxyz I/O following the official volume-cartographer format:
a directory with x.tif, y.tif, z.tif (float32, one sample per pixel) and
meta.json ({"bbox", "format": "tifxyz", "scale": [su, sv], "type": "seg",
"uuid"}). points[row, col] = (x, y, z) in voxels; invalid = (-1, -1, -1);
the official loader also invalidates z <= 0 and honours mask.tif (>= 255
keeps). scale = grid vertices per voxel, so the nominal step is 1/scale."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import tifffile

SENTINEL = -1.0
REQUIRED = ("bbox", "format", "scale", "type", "uuid")


@dataclass
class Tifxyz:
    points: np.ndarray
    scale: tuple[float, float] = (0.05, 0.05)
    uuid: str = "surface"
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def step_vox(self) -> tuple[float, float]:
        return (1.0 / self.scale[0], 1.0 / self.scale[1])


def valid_mask(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points)
    return np.all(np.isfinite(p), axis=-1) & ~np.any(p == SENTINEL, axis=-1)


def quad_valid_mask(points: np.ndarray) -> np.ndarray:
    v = valid_mask(points)
    return v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]


def canonicalize(points: np.ndarray) -> np.ndarray:
    out = np.array(points, dtype=np.float32, copy=True)
    out[~valid_mask(out)] = SENTINEL
    return out


def bbox(points: np.ndarray) -> list[list[float]]:
    v = valid_mask(points)
    if not v.any():
        return [[SENTINEL] * 3, [SENTINEL] * 3]
    p = np.asarray(points, dtype=np.float32)[v]
    return [[float(c) for c in p.min(0)], [float(c) for c in p.max(0)]]


def read(path: str | os.PathLike) -> Tifxyz:
    d = Path(path)
    meta = json.loads((d / "meta.json").read_text())
    bands = [tifffile.imread(str(d / f"{n}.tif")).astype(np.float32) for n in "xyz"]
    pts = np.stack(bands, -1)
    bad = ~valid_mask(pts) | (pts[..., 2] <= 0)
    if (d / "mask.tif").exists():
        m = tifffile.imread(str(d / "mask.tif"))
        m = m[..., 0] if m.ndim == 3 else m
        H, W = pts.shape[:2]
        if m.shape[0] % H == 0 and m.shape[1] % W == 0:
            fy, fx = m.shape[0] // H, m.shape[1] // W
            bad |= ~(m >= 255).reshape(H, fy, W, fx).all(axis=(1, 3))
    pts[bad] = SENTINEL
    return Tifxyz(pts, (float(meta["scale"][0]), float(meta["scale"][1])), str(meta.get("uuid", "")),
                  {k: v for k, v in meta.items() if k not in REQUIRED})


def write(path: str | os.PathLike, t: Tifxyz, *, overwrite: bool = False, compression: str | None = None) -> Path:
    """Official C++ layout by default (float32, single strip, uncompressed);
    compression="zlib" writes tiled deflate (also readable by libtiff)."""
    d = Path(path)
    if d.exists() and not overwrite:
        raise FileExistsError(d)
    pts = canonicalize(t.points)
    d.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".tmp_tifxyz_", dir=str(d.parent)))
    try:
        for i, n in enumerate("xyz"):
            kw = dict(photometric="minisblack", metadata=None, software=False)
            if compression:
                kw.update(compression=compression, tile=(512, 512))
            else:
                kw.update(compression=None, rowsperstrip=pts.shape[0])
            tifffile.imwrite(str(tmp / f"{n}.tif"), np.ascontiguousarray(pts[..., i], "<f4"), **kw)
        meta = {k: v for k, v in t.meta.items() if k not in REQUIRED}
        meta.update(bbox=bbox(pts), format="tifxyz", scale=[float(t.scale[0]), float(t.scale[1])], type="seg",
                    uuid=str(t.uuid))
        (tmp / "meta.json").write_text(json.dumps(meta, indent=4, sort_keys=True) + "\n")
        if d.exists():
            shutil.rmtree(d)
        os.replace(tmp, d)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return d
