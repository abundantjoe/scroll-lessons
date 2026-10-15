# Provenance: Project HERCULES | owner the owner | [id removed]
"""Census step 2: CT-mask shape per slice at pyramid level 4 (anonymous S3).

Reads the level-4 array of the masked volume chunk-row by chunk-row (whole
uncompressed chunks, never the full volume at once), takes the scroll mask as
non-zero voxels with interior holes filled, and records per level-4 slice:
area, centroid, second-moment axis ratio and orientation, solidity (area /
convex-hull area), equivalent radius, and the deepest interior point
(distance-transform maximum). Masks are kept bit-packed for seed planning.
Numbers only: no image is written or displayed.

Coordinates are mapped to level-0 voxels: level-k index i -> i*2^k + (2^k-1)/2.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull

BUCKET = "vesuvius-challenge-open-data"
LEVEL = 4


def s3client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16,
                                            retries={"max_attempts": 8, "mode": "adaptive"}))


def slice_stats(m: np.ndarray, f: int) -> dict:
    n = int(m.sum())
    if n < 50:
        return dict(area=n)
    yy, xx = np.nonzero(m)
    cx, cy = xx.mean(), yy.mean()
    cov = np.cov(np.vstack([xx - cx, yy - cy]))
    ev, evec = np.linalg.eigh(cov)
    axis_ratio = float(np.sqrt(max(ev[0], 0) / ev[1])) if ev[1] > 0 else 1.0
    ang = float(np.degrees(np.arctan2(evec[1, 1], evec[0, 1])))
    # convex hull on boundary pixels only (cheap)
    er = ndimage.binary_erosion(m)
    by, bx = np.nonzero(m & ~er)
    try:
        hull = ConvexHull(np.c_[bx, by].astype(float))
        hull_area = float(hull.volume) + 0.5 * hull.area + 1.0  # pixel-centre hull -> pixel area correction
        solidity = float(min(1.0, n / hull_area))
    except Exception:
        solidity = float("nan")
    dt = ndimage.distance_transform_edt(m)
    iy, ix = np.unravel_index(int(np.argmax(dt)), dt.shape)
    c = lambda i: float(i) * f + (f - 1) / 2.0
    return dict(area=n, cx=c(cx), cy=c(cy), axis_ratio=axis_ratio, major_angle_deg=ang,
                solidity=solidity, r_eq=float(np.sqrt(n / np.pi) * f), dt_max=float(dt.max() * f),
                dtx=c(ix), dty=c(iy))


def run(vol_url: str, out_prefix: str, workers: int = 8) -> dict:
    s3 = s3client()
    b, p = vol_url.replace("s3://", "").split("/", 1)
    p = p.rstrip("/")
    za = json.loads(s3.get_object(Bucket=b, Key=f"{p}/{LEVEL}/.zarray")["Body"].read())
    Z, Y, X = za["shape"]
    cz, cy, cx = za["chunks"]
    assert za["compressor"] is None and za.get("order", "C") == "C" and not za.get("filters")
    sep = za.get("dimension_separator", ".")
    dt = np.dtype(za["dtype"])
    ny, nx = -(-Y // cy), -(-X // cx)
    f = 2 ** LEVEL
    packed = []
    stats = []
    t0 = time.time()
    n_req = 0
    n_missing = 0

    def fetch(args):
        iz, iy, ix = args
        key = f"{p}/{LEVEL}/" + sep.join(map(str, (iz, iy, ix)))
        try:
            raw = s3.get_object(Bucket=b, Key=key)["Body"].read()
            return iy, ix, np.frombuffer(raw, dt).reshape(cz, cy, cx)
        except s3.exceptions.NoSuchKey:
            return iy, ix, None

    with ThreadPoolExecutor(workers) as ex:
        for iz in range(-(-Z // cz)):
            blk = np.zeros((cz, ny * cy, nx * cx), dt)
            for iy, ix, a in ex.map(fetch, [(iz, iy, ix) for iy in range(ny) for ix in range(nx)]):
                n_req += 1
                if a is None:
                    n_missing += 1
                    continue
                blk[:, iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = a
            nz = min(cz, Z - iz * cz)
            for k in range(nz):
                m = ndimage.binary_fill_holes(blk[k, :Y, :X] > 0)
                s = slice_stats(m, f)
                s["z"] = (iz * cz + k) * f + (f - 1) / 2.0
                stats.append(s)
                packed.append(np.packbits(m, axis=None))
            del blk
            print(f"chunk-row {iz} done, {time.time() - t0:.0f}s", flush=True)
    np.savez_compressed(out_prefix + "_mask_L4.npz", packed=np.stack(packed), shape=np.array([Z, Y, X]), level=LEVEL)
    keys = ["z", "area", "cx", "cy", "axis_ratio", "major_angle_deg", "solidity", "r_eq", "dt_max", "dtx", "dty"]
    arr = {k: np.array([s.get(k, np.nan) for s in stats], float) for k in keys}
    np.savez_compressed(out_prefix + "_shape_L4.npz", **arr)
    return dict(shape_L4=[Z, Y, X], chunks=[cz, cy, cx], requests=n_req, missing_chunks=n_missing,
                seconds=round(time.time() - t0, 1), slices=len(stats))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="data/catalogue/eligible_products.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vols", nargs="+", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cat = json.load(open(a.catalogue))
    for vol in a.vols:
        v = next(v for v in cat["volumes"] if v["scroll"] == "PHerc" + vol)
        if "0841" in v["scroll"]:
            raise PermissionError("PHerc0841 is not a census volume")
        pre = os.path.join(a.out, v["scroll"])
        if os.path.exists(pre + "_shape_L4.npz"):
            continue
        info = run(v["volume_zarr_s3"], pre)
        info.update(scroll=v["scroll"], volume_zarr_s3=v["volume_zarr_s3"])
        json.dump(info, open(pre + "_mask_run.json", "w"), indent=1)
        print(json.dumps(info), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
