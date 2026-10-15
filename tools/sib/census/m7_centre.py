# Provenance: Project HERCULES | owner the owner | [id removed]
"""Census step 2c: geometry-only centre from the m7 surface prediction (no CT).

Per sampled slice of the m7 prediction at pyramid level L (default 3), the
2-D structure tensor gives the local sheet normal (dominant gradient
direction) and its coherence. The centre is the weighted least-squares point
closest to all normal lines inside the CT mask (hercules.pipeline.centre.
normal_line_centre generalised with weights). Sheets wrap around the
umbilicus, so normal lines meet near it. Scored against the official
umbilicus where one exists. Numbers only; no image is written.
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

BUCKET = "vesuvius-challenge-open-data"
M7 = "surface-20260413222639-surface-m7-L0-th0.2"


def s3client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16,
                                            retries={"max_attempts": 8, "mode": "adaptive"}))


def weighted_line_centre(p, d, w):
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    P = np.eye(2)[None] - d[:, :, None] * d[:, None, :]
    A = np.einsum("n,nij->ij", w, P)
    b = np.einsum("n,nij,nj->i", w, P, p)
    c = np.linalg.solve(A, b)
    return c, float(np.linalg.cond(A))


def slice_centre(img, mask, f, sig_g=1.0, sig_t=4.0, stride=2, min_coh=0.5, irls=3):
    """img: m7 slice (float), mask: bool (same shape) where to use normals."""
    g = ndimage.gaussian_filter(img.astype(np.float32), sig_g)
    gy = ndimage.sobel(g, 0)
    gx = ndimage.sobel(g, 1)
    Jxx = ndimage.gaussian_filter(gx * gx, sig_t)
    Jyy = ndimage.gaussian_filter(gy * gy, sig_t)
    Jxy = ndimage.gaussian_filter(gx * gy, sig_t)
    tr = Jxx + Jyy
    disc = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2)
    coh = np.where(tr > 1e-6, disc / np.maximum(tr, 1e-6), 0)
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)  # dominant gradient direction = sheet normal
    sel = mask & (coh >= min_coh) & (tr > np.percentile(tr[mask], 25) if mask.any() else False)
    sel[::stride, :] &= True
    sub = np.zeros_like(sel)
    sub[::stride, ::stride] = True
    sel &= sub
    yy, xx = np.nonzero(sel)
    if yy.size < 200:
        return None
    p = np.c_[xx, yy].astype(float) * f + (f - 1) / 2.0
    d = np.c_[np.cos(th[yy, xx]), np.sin(th[yy, xx])]
    w = coh[yy, xx] * tr[yy, xx] / tr[yy, xx].mean()
    c, cond = weighted_line_centre(p, d, w)
    for _ in range(irls):  # down-weight lines far from the current centre (robust to off-centre texture)
        v = c[None] - p
        dist = np.abs(v[:, 0] * d[:, 1] - v[:, 1] * d[:, 0])
        s = np.median(dist) * 1.4826 + 1e-6
        ww = w / (1.0 + (dist / (2 * s)) ** 2)
        c, cond = weighted_line_centre(p, d, ww)
    return dict(cx=float(c[0]), cy=float(c[1]), cond=cond, n=int(yy.size), coh_med=float(np.median(coh[yy, xx])))


def run(scroll, vid, mask_npz, level=3, z_step_l0=256, workers=8):
    s3 = s3client()
    import numcodecs

    pre = f"{scroll}/representations/predictions/surfaces/{vid}-{M7}.zarr/{level}"
    za = json.loads(s3.get_object(Bucket=BUCKET, Key=pre + "/.zarray")["Body"].read())
    Z, Y, X = za["shape"]
    cz, cy, cx = za["chunks"]
    codec = numcodecs.get_codec(za["compressor"])
    sep = za.get("dimension_separator", ".")
    f = 2 ** level
    mk = np.load(mask_npz)
    P, (MZ, MY, MX) = mk["packed"], mk["shape"]
    fm = 2 ** int(mk["level"])
    ny, nx = -(-Y // cy), -(-X // cx)
    out = []
    t0 = time.time()

    def fetch(a):
        iz, iy, ix = a
        try:
            raw = s3.get_object(Bucket=BUCKET, Key=pre + "/" + sep.join(map(str, a)))["Body"].read()
            return iy, ix, np.frombuffer(codec.decode(raw), np.uint8).reshape(cz, cy, cx)
        except s3.exceptions.NoSuchKey:
            return iy, ix, None

    zl_all = np.arange(0, Z, max(1, z_step_l0 // f))
    with ThreadPoolExecutor(workers) as ex:
        for iz in range(-(-Z // cz)):
            zl = zl_all[(zl_all >= iz * cz) & (zl_all < (iz + 1) * cz)]
            if zl.size == 0:
                continue
            blk = np.zeros((zl.size, ny * cy, nx * cx), np.uint8)
            for iy, ix, a in ex.map(fetch, [(iz, iy, ix) for iy in range(ny) for ix in range(nx)]):
                if a is not None:
                    blk[:, iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = a[zl - iz * cz]
            for k, z in enumerate(zl):
                z0 = z * f + (f - 1) / 2.0
                mi = int(np.clip(round((z0 - (fm - 1) / 2.0) / fm), 0, MZ - 1))
                m = np.unpackbits(P[mi])[: MY * MX].reshape(MY, MX).astype(bool)
                m = ndimage.binary_erosion(m, iterations=3)
                # mask to level L grid
                yy = np.clip(((np.arange(Y) * f + (f - 1) / 2.0) / fm).astype(int), 0, MY - 1)
                xx = np.clip(((np.arange(X) * f + (f - 1) / 2.0) / fm).astype(int), 0, MX - 1)
                mL = m[np.ix_(yy, xx)]
                r = slice_centre(blk[k, :Y, :X], mL, f)
                if r:
                    r["z"] = z0
                    out.append(r)
            print(f"{scroll} L{level} chunk-row {iz} {time.time() - t0:.0f}s", flush=True)
    keys = ["z", "cx", "cy", "cond", "n", "coh_med"]
    return {k: np.array([o[k] for o in out], float) for k in keys}, dict(level=level, shape=[Z, Y, X],
                                                                         seconds=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="data/catalogue/eligible_products.json")
    ap.add_argument("--mask", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--level", type=int, default=3)
    ap.add_argument("--vols", nargs="+", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cat = json.load(open(a.catalogue))
    for vol in a.vols:
        v = next(v for v in cat["volumes"] if v["scroll"] == "PHerc" + vol)
        fn = os.path.join(a.out, f"{v['scroll']}_m7centre_L{a.level}.npz")
        if os.path.exists(fn):
            continue
        arr, info = run(v["scroll"], v["volume_id"], os.path.join(a.mask, f"{v['scroll']}_mask_L4.npz"), a.level)
        np.savez_compressed(fn, **arr)
        print(json.dumps(dict(scroll=v["scroll"], **info)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
