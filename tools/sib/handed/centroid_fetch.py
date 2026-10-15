# Provenance: Project HERCULES | owner the owner | [id removed]
"""CT-mask centroid per slice at a pyramid level of an official masked
OME-Zarr volume (anonymous S3, byte-range reads of single planes of
uncompressed C-order chunks). Only per-slice statistics are kept (centroid,
area, second-moment axis ratio, fill); no plane is stored or printed.

Usage:
  python centroid_fetch.py VOLUME_S3_PREFIX OUT_JSON [--level 4] [--zstride 8]
         [--exclude-npy PTS.npy --exclude-radius 175]

--exclude-npy: (N, 3) level-0 (x, y, z) points; every level-k pixel whose
level-0 centre lies within --exclude-radius of any point is set to 0 BEFORE any
statistic (used for the PHerc0841 J windows). The count of excluded pixels
per slice is recorded.

Also records sha256 of metadata.json, .zattrs and the level .zarray, and the
voxel size read from metadata.json (never assumed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config

sys.path.insert(0, str(Path(__file__).resolve().parent))
import handed as H  # noqa: E402

BUCKET = "vesuvius-challenge-open-data"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("out")
    ap.add_argument("--level", type=int, default=4)
    ap.add_argument("--zstride", type=int, default=8)
    ap.add_argument("--exclude-npy")
    ap.add_argument("--exclude-radius", type=float, default=175.0)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=a.workers + 4,
                                          retries={"max_attempts": 8, "mode": "standard"}))
    pre = a.prefix.replace(f"s3://{BUCKET}/", "").rstrip("/")
    t0 = time.time()

    def get(key, **kw):
        return s3.get_object(Bucket=BUCKET, Key=key, **kw)["Body"].read()

    rec = {"volume": pre, "level": a.level, "zstride": a.zstride, "hashes": {}}
    meta_b = get(f"{pre}/metadata.json")
    zat_b = get(f"{pre}/.zattrs")
    za_b = get(f"{pre}/{a.level}/.zarray")
    for n, b in (("metadata.json", meta_b), (".zattrs", zat_b), (f"{a.level}/.zarray", za_b)):
        rec["hashes"][n] = hashlib.sha256(b).hexdigest()
    meta = json.loads(meta_b)
    try:
        px_mm = meta["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]
    except (KeyError, TypeError):
        px_mm = None
    rec["voxel_size_um_from_metadata"] = None if px_mm is None else round(float(px_mm) * 1000.0, 6)
    rec["zattrs"] = json.loads(zat_b)
    za = json.loads(za_b)
    rec["zarray"] = za
    if za.get("compressor") is not None or za.get("order", "C") != "C" or za.get("filters"):
        raise NotImplementedError("only uncompressed, filter-free C-order arrays")
    Z, Y, X = za["shape"]
    cz, cy, cx = za["chunks"]
    dt = np.dtype(za["dtype"])
    sep = za.get("dimension_separator", ".")
    f = 2 ** a.level
    zs = list(range(0, Z, a.zstride))
    ny, nx = -(-Y // cy), -(-X // cx)
    pb = cy * cx * dt.itemsize

    excl_tree = None
    if a.exclude_npy:
        from scipy.spatial import cKDTree

        ep = np.load(a.exclude_npy).astype(np.float64)
        excl_tree = cKDTree(ep)
        ez = (ep[:, 2].min(), ep[:, 2].max())
        rec["exclude"] = dict(n_points=int(ep.shape[0]), radius_vox=a.exclude_radius,
                              points_sha256=hashlib.sha256(Path(a.exclude_npy).read_bytes()).hexdigest())
    yy, xx = np.mgrid[0:Y, 0:X]
    ctr_x = xx * f + (f - 1) / 2
    ctr_y = yy * f + (f - 1) / 2

    def fetch(args):
        z, iy, ix = args
        iz, zz = divmod(z, cz)
        key = f"{pre}/{a.level}/" + sep.join(str(i) for i in (iz, iy, ix))
        for i in range(5):
            try:
                b = get(key, Range=f"bytes={zz * pb}-{(zz + 1) * pb - 1}")
                return z, iy, ix, np.frombuffer(b, dtype=dt).reshape(cy, cx)
            except s3.exceptions.NoSuchKey:
                return z, iy, ix, None
            except Exception:
                time.sleep(2 ** (i + 1))
        raise RuntimeError(f"failed {key}")

    rows = []
    n_req = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for z in zs:
            plane = np.zeros((ny * cy, nx * cx), dt)
            for _, iy, ix, arr in ex.map(fetch, [(z, iy, ix) for iy in range(ny) for ix in range(nx)]):
                n_req += 1
                if arr is not None:
                    plane[iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = arr
            m = plane[:Y, :X] > 0
            z0 = z * f + (f - 1) / 2
            n_ex = 0
            if excl_tree is not None and (ez[0] - a.exclude_radius <= z0 <= ez[1] + a.exclude_radius):
                cand = np.nonzero(m)
                q = np.stack([ctr_x[cand], ctr_y[cand], np.full(cand[0].size, z0)], 1)
                d, _ = excl_tree.query(q, distance_upper_bound=a.exclude_radius)
                hit = np.isfinite(d)
                m[cand[0][hit], cand[1][hit]] = False
                n_ex = int(hit.sum())
            st = H.slice_centroid_stats(m)
            rows.append(dict(z=z0, n=st["n"], n_excluded=n_ex,
                             cx=(st["cx"] * f + (f - 1) / 2) if st["n"] else None,
                             cy=(st["cy"] * f + (f - 1) / 2) if st["n"] else None,
                             axis_ratio=st.get("axis_ratio"), fill=st.get("fill")))
            del plane, m
    rec["slices"] = rows
    rec["n_requests"] = n_req
    rec["seconds"] = round(time.time() - t0, 1)
    rec["shape_level"] = [Z, Y, X]
    Path(a.out).write_text(json.dumps(rec, indent=0, default=lambda o: None if (isinstance(o, float) and math.isnan(o)) else o))
    print(json.dumps(dict(volume=pre, slices=len(rows), requests=n_req, seconds=rec["seconds"],
                          voxel_um=rec["voxel_size_um_from_metadata"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
