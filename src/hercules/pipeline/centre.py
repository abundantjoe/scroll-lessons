# Provenance: Project HERCULES | owner the owner | [id removed]
"""Centre curves c(z) (umbilicus) for the outward direction r_out.

Priority (window pipeline brief): the official umbilicus JSON of the SAME
volume if one exists (s3://vesuvius-challenge-open-data/<scroll>/
representations/umbilicus/<volume id>-umbilicus-*.json, whose
``metadata.volume`` names the volume), else the CT-mask centroid per slice of
the masked volume at zarr level 4, smoothed in z (:func:`mask_centroid_curve`).

Geometry-only fallbacks that read no CT (used where CT access is not allowed):
:func:`geometric_centre_curve` (least-squares intersection of the xy-projected
vertex normal lines per z band = local centre of curvature) and
:func:`volume_axis_centre` (reconstruction centre = scanner rotation axis, from
the level-0 ``.zarray`` shape only).
"""

from __future__ import annotations

import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from hercules.geometry.level_mesh import CentreCurve
from hercules.geometry.tifxyz import valid_mask

BUCKET = "vesuvius-challenge-open-data"
SEALED_SCROLLS = ("PHerc0841",)  # no CT access until the J seal is committed (brief, hard rule 1)


def _s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16))


def parse_s3_url(url: str) -> tuple[str, str]:
    m = re.match(r"^s3://([^/]+)/(.*?)/?$", url)
    if not m:
        raise ValueError(f"not an s3:// url: {url}")
    return m.group(1), m.group(2)


def _guard(url: str, allow_sealed: bool) -> None:
    if not allow_sealed and any(s in url for s in SEALED_SCROLLS):
        raise PermissionError(f"CT access to {url} is not allowed (sealed scroll); geometry-only fallbacks exist")


# ---------------------------------------------------------------------------
# official umbilicus
# ---------------------------------------------------------------------------

def umbilicus_from_json(obj: dict | str, *, expect_volume: str | None = None) -> CentreCurve:
    """CentreCurve from an official umbilicus JSON ({"control_points": [{x,y,z,..}],
    "metadata": {"volume": ...}}). Raises if ``expect_volume`` (a volume id or
    zarr name) does not match ``metadata.volume``."""
    d = json.loads(obj) if isinstance(obj, str) else obj
    vol = str(d.get("metadata", {}).get("volume", ""))
    if expect_volume is not None and expect_volume not in vol:
        raise ValueError(f"umbilicus is for volume {vol!r}, not {expect_volume!r}")
    cp = d["control_points"]
    return CentreCurve(z=np.array([p["z"] for p in cp], float), x=np.array([p["x"] for p in cp], float),
                       y=np.array([p["y"] for p in cp], float))


def find_official_umbilicus(scroll: str, volume_id: str, client=None) -> str | None:
    """Key of the official umbilicus JSON for ``volume_id`` (timestamp id such as
    20250728140407) under ``<scroll>/representations/umbilicus/``, or None."""
    s3 = client or _s3()
    r = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{scroll}/representations/umbilicus/")
    keys = [o["Key"] for o in r.get("Contents", [])]
    hits = sorted(k for k in keys if k.rsplit("/", 1)[-1].startswith(f"{volume_id}-umbilicus"))
    return hits[-1] if hits else None


# ---------------------------------------------------------------------------
# CT-mask centroid at a low-resolution level
# ---------------------------------------------------------------------------

@dataclass
class MaskCentroid:
    curve: CentreCurve
    z_full: np.ndarray  # full-resolution z of each sampled slice
    x_raw: np.ndarray
    y_raw: np.ndarray
    area_px: np.ndarray  # mask pixels per sampled slice (level units)
    level: int
    z_stride: int
    n_requests: int
    seconds: float
    meta: dict[str, Any] = field(default_factory=dict)


def _gauss_smooth(z: np.ndarray, v: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0 or v.size < 3:
        return v.copy()
    out = np.empty_like(v)
    for i, zi in enumerate(z):
        w = np.exp(-0.5 * ((z - zi) / sigma) ** 2)
        out[i] = np.sum(w * v) / np.sum(w)
    return out


def mask_centroid_curve(
    volume_url: str,
    level: int = 4,
    *,
    z_range: tuple[float, float] | None = None,
    z_stride: int = 1,
    smooth_sigma_vox: float = 256.0,
    min_area_frac: float = 0.002,
    workers: int = 8,
    allow_sealed: bool = False,
    client=None,
) -> MaskCentroid:
    """Centroid of the non-zero (masked-scroll) voxels per slice of pyramid
    ``level`` of an OME-Zarr v2 volume on S3 (anonymous), mapped to level-0
    voxel coordinates (level-k index i -> i*2^k + (2^k - 1)/2), Gaussian-
    smoothed in z (sigma in level-0 voxels) and linearly interpolated.

    Only the requested level is read. For uncompressed C-order chunks each
    slice is fetched by byte-range (one 2-D plane per chunk); compressed
    chunks are fetched whole and decoded with numcodecs. ``z_range`` (level-0
    voxels) limits the slices; ``z_stride`` samples every n-th level slice.
    """
    _guard(volume_url, allow_sealed)
    s3 = client or _s3()
    bucket, prefix = parse_s3_url(volume_url)
    t0 = time.time()
    za = json.loads(s3.get_object(Bucket=bucket, Key=f"{prefix}/{level}/.zarray")["Body"].read())
    Z, Y, X = za["shape"]
    cz, cy, cx = za["chunks"]
    dt = np.dtype(za["dtype"])
    sep = za.get("dimension_separator", ".")
    comp = za.get("compressor")
    if za.get("order", "C") != "C" or za.get("filters"):
        raise NotImplementedError("only C-order, filter-free zarr v2 arrays are supported")
    f = 2 ** level
    z_lo, z_hi = 0, Z - 1
    if z_range is not None:
        z_lo = max(0, int(math.floor((z_range[0] - (f - 1) / 2) / f)))
        z_hi = min(Z - 1, int(math.ceil((z_range[1] - (f - 1) / 2) / f)))
    zs = list(range(z_lo, z_hi + 1, max(1, int(z_stride))))
    if zs[-1] != z_hi:
        zs.append(z_hi)
    ny, nx = -(-Y // cy), -(-X // cx)
    fill = za.get("fill_value") or 0
    plane_bytes = cy * cx * dt.itemsize
    n_req = 0

    def key(iz, iy, ix):
        return f"{prefix}/{level}/" + sep.join(str(i) for i in (iz, iy, ix))

    chunk_cache: dict[tuple[int, int, int], np.ndarray | None] = {}

    def fetch_plane(args):
        z, iy, ix = args
        iz, zz = divmod(z, cz)
        try:
            if comp is None:
                b = s3.get_object(Bucket=bucket, Key=key(iz, iy, ix),
                                  Range=f"bytes={zz * plane_bytes}-{(zz + 1) * plane_bytes - 1}")["Body"].read()
                a = np.frombuffer(b, dtype=dt).reshape(cy, cx)
            else:
                import numcodecs

                ck = (iz, iy, ix)
                if ck not in chunk_cache:
                    raw = s3.get_object(Bucket=bucket, Key=key(iz, iy, ix))["Body"].read()
                    chunk_cache[ck] = np.frombuffer(numcodecs.get_codec(comp).decode(raw), dtype=dt).reshape(cz, cy, cx)
                a = chunk_cache[ck][zz]
        except s3.exceptions.NoSuchKey:
            a = None
        return z, iy, ix, a

    jobs = [(z, iy, ix) for z in zs for iy in range(ny) for ix in range(nx)]
    n_req = len(jobs)
    planes: dict[int, np.ndarray] = {z: np.full((ny * cy, nx * cx), fill, dtype=dt) for z in zs}
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as ex:
        for z, iy, ix, a in ex.map(fetch_plane, jobs):
            if a is not None:
                planes[z][iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = a
    xs, ys, areas, zf = [], [], [], []
    yy, xx = np.mgrid[0:Y, 0:X]
    for z in zs:
        m = planes[z][:Y, :X] > 0
        n = int(m.sum())
        areas.append(n)
        zf.append(z * f + (f - 1) / 2)
        if n >= min_area_frac * Y * X:
            xs.append(float(xx[m].mean()) * f + (f - 1) / 2)
            ys.append(float(yy[m].mean()) * f + (f - 1) / 2)
        else:
            xs.append(np.nan)
            ys.append(np.nan)
    zf = np.array(zf, float)
    xr, yr = np.array(xs), np.array(ys)
    ok = np.isfinite(xr) & np.isfinite(yr)
    if ok.sum() == 0:
        raise ValueError("no slice with enough mask pixels")
    xs_s = _gauss_smooth(zf[ok], xr[ok], smooth_sigma_vox)
    ys_s = _gauss_smooth(zf[ok], yr[ok], smooth_sigma_vox)
    curve = CentreCurve(z=zf[ok], x=xs_s, y=ys_s)
    return MaskCentroid(curve=curve, z_full=zf, x_raw=xr, y_raw=yr, area_px=np.array(areas), level=level,
                        z_stride=int(z_stride), n_requests=n_req, seconds=time.time() - t0,
                        meta=dict(shape=[Z, Y, X], chunks=[cz, cy, cx], compressor=comp))


# ---------------------------------------------------------------------------
# geometry-only fallbacks (no CT)
# ---------------------------------------------------------------------------

def normal_line_centre(points_xy: np.ndarray, dirs_xy: np.ndarray) -> tuple[np.ndarray, float]:
    """Least-squares point closest to all 2-D lines p + t d (d unit). Returns
    (centre, condition number of the 2x2 system)."""
    p = np.asarray(points_xy, float)
    d = np.asarray(dirs_xy, float)
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    P = np.eye(2)[None] - d[:, :, None] * d[:, None, :]  # projector orthogonal to each line
    A = P.sum(axis=0)
    b = np.einsum("nij,nj->i", P, p)
    return np.linalg.solve(A, b), float(np.linalg.cond(A))


def geometric_centre_curve(points: np.ndarray, *, z_bin_vox: float = 400.0, min_vertices: int = 50,
                           stride: int = 2) -> tuple[CentreCurve, dict]:
    """Centre of curvature of the sheet per z band (no CT): intersection of
    the xy-projected normal lines of the mesh vertices in each band. A proxy
    for the umbilicus only where the winding is roughly circular; its sign of
    n . r_out is right wherever the sheet is convex toward the outside."""
    from .canvas import vertex_normals_official  # central differences only (no one-sided border normals)

    p = np.asarray(points, float)[::stride, ::stride]
    n = vertex_normals_official(np.asarray(points, float))[::stride, ::stride]
    ok = valid_mask(p) & np.isfinite(n).all(-1)
    nxy = n[..., :2]
    ok &= np.linalg.norm(nxy, axis=-1) > 0.3
    P, N = p[ok], nxy[ok]
    z = P[:, 2]
    edges = np.arange(z.min(), z.max() + z_bin_vox, z_bin_vox)
    zc, xc, yc, conds = [], [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (z >= a) & (z < b)
        if sel.sum() < min_vertices:
            continue
        c, cond = normal_line_centre(P[sel, :2], N[sel])
        zc.append(0.5 * (a + b))
        xc.append(c[0])
        yc.append(c[1])
        conds.append(cond)
    if not zc:
        c, cond = normal_line_centre(P[:, :2], N)
        zc, xc, yc, conds = [float(np.median(z))], [c[0]], [c[1]], [cond]
    info = dict(z=zc, x=xc, y=yc, cond=conds, z_bin_vox=z_bin_vox)
    return CentreCurve(z=np.array(zc), x=np.array(xc), y=np.array(yc)), info


def volume_axis_centre(volume_url: str, client=None) -> tuple[CentreCurve, dict]:
    """Straight centre at the middle of the reconstructed slice (the scanner
    rotation axis), from the level-0 ``.zarray`` shape only (no CT)."""
    s3 = client or _s3()
    bucket, prefix = parse_s3_url(volume_url)
    za = json.loads(s3.get_object(Bucket=bucket, Key=f"{prefix}/0/.zarray")["Body"].read())
    Z, Y, X = za["shape"]
    cx, cy = (X - 1) / 2.0, (Y - 1) / 2.0
    return CentreCurve.straight(cx, cy), dict(shape=[Z, Y, X], cx=cx, cy=cy)
