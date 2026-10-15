# Provenance: Project HERCULES | owner the owner | [id removed]
"""TEST HELPER ONLY: a synthetic scroll world for the planted-fault suite.

* volume ``vol[z, y, x]`` (uint8): concentric cylindrical papyrus sheets around a
  vertical axis, each with a Gaussian cross-section, modulated by a 3-D random
  texture (so every render slice differs in-plane and the stack is not symmetric in
  depth), plus a weak textured background;
* meshes: tifxyz grids on a sheet (``render_synth.cylinder_grid``);
* the "delivered" render is produced by a code path that is independent of the
  reference render used by :mod:`tribunal.preread` (tifxyz.sample_grid +
  tifxyz.vertex_normals + render_synth.render_along_normals here, versus
  canvas.emulate_gen + a block read + map_coordinates there), so a clean world
  passes because two implementations agree, not because one is compared with itself.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from hercules.geometry.render_synth import cylinder_grid, render_along_normals
from hercules.geometry.tifxyz import TifxyzMesh, sample_grid, valid_mask, vertex_normals, write_tifxyz

VOXEL_UM_DEFAULT = 9.366  # the synthetic metadata.json value (any value works)


@dataclass
class World:
    vol: np.ndarray            # (Z, Y, X) uint8
    centre_xy: tuple[float, float]
    radii: tuple[float, ...]   # sheet radii (vox)
    voxel_um: float
    seed: int


def make_volume(shape_zyx=(112, 192, 192), centre_xy=(96.0, 96.0), radii=(30.0, 42.0, 54.0, 66.0, 78.0),
                sheet_sigma=1.2, texture_sigma=1.0, seed=0, voxel_um=VOXEL_UM_DEFAULT) -> World:
    rng = np.random.default_rng(seed)
    Z, Y, X = shape_zyx
    tex = gaussian_filter(rng.standard_normal(shape_zyx).astype(np.float32), texture_sigma)
    tex /= tex.std() + 1e-12
    bg = gaussian_filter(rng.standard_normal(shape_zyx).astype(np.float32), 2.0)
    bg /= bg.std() + 1e-12
    yy, xx = np.mgrid[0:Y, 0:X].astype(np.float64)
    r = np.hypot(xx - centre_xy[0], yy - centre_xy[1])
    sheets = np.zeros((Y, X), dtype=np.float64)
    for i, r0 in enumerate(radii):
        amp = 0.8 + 0.2 * ((i * 7919 + seed) % 5) / 4.0  # sheets differ in brightness
        sheets += amp * np.exp(-0.5 * ((r - r0) / sheet_sigma) ** 2)
    v = sheets[None].astype(np.float32) * (0.65 + 0.35 * tex) + 0.08 * bg + 0.12
    v = np.clip(v / 1.4 * 255.0, 1, 255)  # 0 is reserved for "empty"
    return World(vol=np.rint(v).astype(np.uint8), centre_xy=tuple(centre_xy), radii=tuple(radii),
                 voxel_um=float(voxel_um), seed=int(seed))


def sheet_mesh(world: World, sheet: int = 2, shape_hw=(24, 40), step=4.0, angle_deg=0.0, s0=0.0, z0=8.0,
               phi_ref=0.0, radial_noise=0.0, seed=0) -> np.ndarray:
    """(H, W, 3) float32 grid on sheet ``sheet`` (index into world.radii)."""
    p = cylinder_grid(world.radii[sheet], world.centre_xy, shape_hw, step, angle_deg, s0=s0, z0=z0,
                      phi_ref=phi_ref).astype(np.float64)
    if radial_noise > 0:
        rng = np.random.default_rng(seed)
        d = np.stack([p[..., 0] - world.centre_xy[0], p[..., 1] - world.centre_xy[1]], -1)
        d /= np.linalg.norm(d, axis=-1, keepdims=True)
        e = rng.normal(0.0, radial_noise, p.shape[:2])
        p[..., 0] += e * d[..., 0]
        p[..., 1] += e * d[..., 1]
    return p.astype(np.float32)


def write_mesh(points: np.ndarray, path: Path, step: float, uuid: str, voxel_um: float) -> Path:
    s = 1.0 / float(step)
    return write_tifxyz(path, TifxyzMesh(points=points, scale=(s, s), uuid=uuid, meta={}), overwrite=True,
                        voxel_size_um=voxel_um)


def write_metadata(path: Path, voxel_um: float) -> Path:
    """Minimal volume metadata.json with the official voxel-size field (mm)."""
    obj = {"scan": {"tomo": {"acquisition": {"detector": {"samplePixelSize": round(voxel_um / 1000.0, 9)}}}}}
    path = Path(path)
    path.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    return path


def render_delivered(vol: np.ndarray, points: np.ndarray, step: float, origin_yx, shape_hw, n: int,
                     slice_step: float = 1.0, flip_normals: bool = True, slice_shift: int = 0) -> np.ndarray:
    """Delivered render stack (n, h, w) uint8, 0 = empty (independent code path).

    Canvas pixel (P, Q) samples grid (row, col) = ((P + 0.5) s, (Q + 0.5) s) for a
    --scale 1 render of a grid with scale s = 1/step (canvas.py). ``slice_shift`` shifts
    every slice by that many slice steps along the stack direction (fault injection).
    """
    if n % 2 != 1:
        raise ValueError("synthetic renders use odd n (surface on slice n//2)")
    s = 1.0 / float(step)
    y0, x0 = origin_yx
    h, w = shape_hw
    rows = (np.arange(y0, y0 + h, dtype=np.float64) + 0.5) * s
    cols = (np.arange(x0, x0 + w, dtype=np.float64) + 0.5) * s
    R, C = np.meshgrid(rows, cols, indexing="ij")
    pts = sample_grid(points, R, C)
    nv = vertex_normals(points)
    H, W = points.shape[:2]
    ri = np.clip(np.floor(R + 0.5).astype(int), 0, H - 1)
    ci = np.clip(np.floor(C + 0.5).astype(int), 0, W - 1)
    nrm = nv[ri, ci]
    if flip_normals:
        nrm = -nrm
    ok = valid_mask(pts) & np.isfinite(nrm).all(-1)
    shifted = pts + (float(slice_shift) * float(slice_step)) * np.where(ok[..., None], nrm, 0.0)
    shifted[~ok] = -1.0
    stack = render_along_normals(vol, shifted, np.where(ok[..., None], nrm, np.nan), n=n, spacing=slice_step,
                                 invalid_value=np.nan)
    out = np.where(np.isfinite(stack), np.clip(np.rint(stack), 1, 255), 0).astype(np.uint8)
    return out


def array_sha256(a: np.ndarray) -> str:
    """Content hash of an array: dtype, shape and C-order bytes (chunking-independent)."""
    a = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(f"{a.dtype.str}|{','.join(map(str, a.shape))}|".encode())
    h.update(a.tobytes())
    return h.hexdigest()


def write_stack_zarr(stack: np.ndarray, path: Path, attrs: dict | None = None) -> Path:
    """Write (n, h, w) uint8 to a zarr v2 group with array '0' (render-output layout)."""
    import zarr

    g = zarr.open_group(str(path), mode="w")
    g.create_dataset("0", data=stack, chunks=(stack.shape[0], min(64, stack.shape[1]), min(64, stack.shape[2])))
    if attrs:
        g.attrs.update(attrs)
    return Path(path)


def write_volume_zarr(vol: np.ndarray, path: Path) -> Path:
    import zarr

    g = zarr.open_group(str(path), mode="w")
    g.create_dataset("0", data=vol, chunks=(32, 64, 64))
    return Path(path)
