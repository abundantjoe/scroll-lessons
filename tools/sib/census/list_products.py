# Provenance: Project HERCULES | owner the owner | [id removed]
"""Census step 1-3: list the m7 surface prediction, its normal grids, lasagna and
umbilicus products of the 11 JULY census volumes (anonymous S3 listing only; no
pixel data is read here).

Outputs (under --out):
  <vol>_ngrid_sizes.npz   per-file byte sizes of xy/xz/yz grids indexed by slice
  products.json           paths, sizes, per-level m7 zarr totals, 500-slice band bytes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BUCKET = "vesuvius-challenge-open-data"
CENSUS = ["0125", "0191", "0211", "0257", "0358", "0813", "0826", "0846A", "0846B", "1203", "1545"]
M7 = "surface-20260413222639-surface-m7-L0-th0.2"
BAND = 500


def s3client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=32,
                                            retries={"max_attempts": 8, "mode": "adaptive"}))


def list_all(s3, prefix, delimiter=None):
    kw = dict(Bucket=BUCKET, Prefix=prefix)
    if delimiter:
        kw["Delimiter"] = delimiter
    objs, prefs = [], []
    for page in s3.get_paginator("list_objects_v2").paginate(**kw):
        objs += [(o["Key"], o["Size"], o["LastModified"].isoformat()) for o in page.get("Contents", [])]
        prefs += [p["Prefix"] for p in page.get("CommonPrefixes", [])]
    return objs, prefs


def get_bytes(s3, key):
    b = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    return b, hashlib.sha256(b).hexdigest()


def volume_entry(cat, vol):
    for v in cat["volumes"]:
        if v["scroll"] == "PHerc" + vol:
            return v
    raise KeyError(vol)


def census_volume(s3, v, out):
    scroll, vid = v["scroll"], v["volume_id"]
    Z, Y, X = v["levels"]["0"]["shape"]
    rec = dict(scroll=scroll, volume_id=vid, shape_zyx=[Z, Y, X])
    pred = f"{scroll}/representations/predictions/surfaces/"
    m7 = f"{pred}{vid}-{M7}.zarr/"
    ng = f"{pred}{vid}-{M7}.normal-grids/"
    rec["m7_zarr"] = "s3://" + BUCKET + "/" + m7
    rec["normal_grids"] = "s3://" + BUCKET + "/" + ng

    # m7 zarr: metadata files (hashed) + per-level object count and bytes (listing per level in parallel)
    top, levels = list_all(s3, m7, "/")
    rec["m7_top_files"] = {}
    for k, sz, lm in top:
        b, h = get_bytes(s3, k)
        rec["m7_top_files"][k.rsplit("/", 1)[-1]] = dict(size=sz, sha256=h, last_modified=lm)
        if k.endswith("metadata.json"):
            open(os.path.join(out, f"{scroll}_m7_metadata.json"), "wb").write(b)
    lv = sorted(p[len(m7):].strip("/") for p in levels)

    def level_stats(L):
        za, h = get_bytes(s3, f"{m7}{L}/.zarray")
        zj = json.loads(za)
        nz = -(-zj["shape"][0] // zj["chunks"][0])
        # one listing per z-chunk prefix, in parallel (level 0 holds ~10^5 chunk objects)
        with ThreadPoolExecutor(24) as ex2:
            parts = list(ex2.map(lambda iz: list_all(s3, f"{m7}{L}/{iz}/")[0], range(nz)))
        objs = [o for part in parts for o in part]
        n = len(objs)
        by = sum(sz for k, sz, _ in objs)
        return L, dict(zarray=zj, zarray_sha256=h, objects=n, bytes=by, z_chunk_rows=nz)

    rec["m7_levels"] = dict(level_stats(L) for L in lv)
    rec["m7_bytes_total"] = int(sum(d["bytes"] for d in rec["m7_levels"].values()))

    # normal grids: every object, sizes by plane and slice index
    objs, _ = list_all(s3, ng)
    sizes = {p: {} for p in ("xy", "xz", "yz")}
    other = {}
    for k, sz, lm in objs:
        rel = k[len(ng):]
        m = re.match(r"^(xy|xz|yz)/(\d+)\.grid$", rel)
        if m:
            sizes[m.group(1)][int(m.group(2))] = sz
        else:
            d = rel.split("/")[0]
            o = other.setdefault(d, [0, 0])
            o[0] += 1
            o[1] += sz
    mb, mh = get_bytes(s3, ng + "metadata.json")
    rec["ngrid_metadata"] = json.loads(mb)
    rec["ngrid_metadata_sha256"] = mh
    n_axis = {"xy": Z, "xz": Y, "yz": X}
    arrs = {}
    for p in sizes:
        a = np.zeros(n_axis[p], np.int64)
        for i, sz in sizes[p].items():
            if i < a.size:
                a[i] = sz
        arrs[p] = a
        rec.setdefault("ngrid_planes", {})[p] = dict(files=len(sizes[p]), bytes=int(a.sum()),
                                                     slices_expected=int(n_axis[p]),
                                                     mean_file_bytes=float(a[a > 0].mean()) if (a > 0).any() else 0.0,
                                                     max_file_bytes=int(a.max()))
    rec["ngrid_other_dirs"] = {d: dict(objects=o[0], bytes=o[1]) for d, o in other.items()}
    rec["ngrid_bytes_total"] = int(sum(sz for _, sz, _ in objs))
    rec["ngrid_objects_total"] = len(objs)
    np.savez_compressed(os.path.join(out, f"{scroll}_ngrid_sizes.npz"), **arrs)
    # xy bytes per z band of 500 slices (the only plane whose files are indexed by z)
    xy = arrs["xy"]
    bands = []
    for z0 in range(0, Z, BAND):
        bands.append(dict(z0=z0, z1=min(Z, z0 + BAND) - 1, xy_files=int((xy[z0:z0 + BAND] > 0).sum()),
                          xy_bytes=int(xy[z0:z0 + BAND].sum())))
    rec["xy_bytes_per_500_band"] = bands

    # lasagna and umbilicus availability (listing only; small JSON hashed, zarrs listed)
    rep = f"{scroll}/representations/"
    _, reps = list_all(s3, rep, "/")
    rec["representation_dirs"] = [p[len(rep):] for p in reps]
    # lasagna: top-level listing only (its OME-Zarrs hold very many chunk objects)
    _, lruns = list_all(s3, f"{rep}predictions/lasagna/", "/")
    rec["lasagna"] = []
    for lr in lruns:
        lo, lsub = list_all(s3, lr, "/")
        ent = dict(prefix=lr, same_volume=vid in lr, files={}, ome_zarrs=[p[len(lr):] for p in lsub])
        for k, sz, lm in lo:
            b, h = get_bytes(s3, k) if sz < 10_000_000 else (b"", None)
            ent["files"][k[len(lr):]] = dict(size=sz, sha256=h)
        rec["lasagna"].append(ent)
    umb, _ = list_all(s3, f"{rep}umbilicus/")
    rec["umbilicus"] = []
    for k, sz, lm in umb:
        if k.endswith(".json"):
            b, h = get_bytes(s3, k)
            d = json.loads(b)
            meta_vol = str(d.get("metadata", {}).get("volume", "")) if isinstance(d, dict) else ""
            fn = os.path.join(out, f"{scroll}_umbilicus_{k.rsplit('/', 1)[-1]}")
            open(fn, "wb").write(b)
            rec["umbilicus"].append(dict(key=k, size=sz, sha256=h, metadata_volume=meta_vol,
                                         same_volume=vid in meta_vol or vid in k,
                                         n_points=len(d.get("control_points", [])) if isinstance(d, dict) else None))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="data/catalogue/eligible_products.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vols", nargs="*", default=CENSUS)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cat = json.load(open(a.catalogue))
    s3 = s3client()
    res = {}
    pj = os.path.join(a.out, "products.json")
    if os.path.exists(pj):
        res = json.load(open(pj))
    for vol in a.vols:
        if vol in res:
            continue
        v = volume_entry(cat, vol)
        print(f"[{vol}] listing", flush=True)
        res[vol] = census_volume(s3, v, a.out)
        json.dump(res, open(pj, "w"), indent=1)
        print(f"[{vol}] ngrid {res[vol]['ngrid_bytes_total']} B m7 {res[vol]['m7_bytes_total']} B", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
