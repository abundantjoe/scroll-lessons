# Provenance: Project HERCULES | owner the owner | [id removed]
"""Winding sense from CT alone (no mesh): the pitch angle of the sheets.

In an axial slice, a spiral sheet r(phi) is tilted from the circumferential
direction phi_hat by psi = atan(dr / (r dphi)). The local sheet direction t
normal is the major-eigenvalue direction of the 2-D structure tensor
(unsigned). Relative to the centre curve (umbilicus, else CT-mask centroid),
psi = angle(sheet normal, r_hat) folded into (-90, 90] deg is averaged over
coherent scroll pixels (coherence weighted); the estimator used is the
constant a0 of a harmonic fit (orders 0-3 in phi) of psi * r, which removes
the first-order bias of a centre error and the second-order bias of a
crushed (elliptic) section. Calibrated on synthetic spirals
(tests/sib_handed_spiral.py): a0 > 0 <=> r decreases with phi (inward =
counter-clockwise about +z) <=> w = +1. By F5 (rolls read inward),
text-top is at low z iff w * parity = +1.

The expected magnitude is small (sheet spacing / (2 pi r), a fraction of a
degree); the method is therefore validated on the volumes whose
z_direction_is_top_to_bottom flag is known before it is used on the others.
Numbers only; slices are read by byte range, held in memory and discarded.

Usage: python spiral_sense.py SCROLL VOLUME_PREFIX OUT_JSON [--level 2] [--n-slices 12] [--avoid-z LO HI]
"""

from __future__ import annotations

import argparse
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
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "src"))
import analyze_meshes as A  # noqa: E402

B = "vesuvius-challenge-open-data"


def slice_psi(img: np.ndarray, mask: np.ndarray, cx: float, cy: float, f: int, s_grad=1.0, s_int=3.0,
              min_coh=0.5, r_min_frac=0.15) -> dict:
    I = img.astype(np.float32)
    gx = gaussian_filter(I, s_grad, order=(0, 1))
    gy = gaussian_filter(I, s_grad, order=(1, 0))
    Jxx = gaussian_filter(gx * gx, s_int)
    Jxy = gaussian_filter(gx * gy, s_int)
    Jyy = gaussian_filter(gy * gy, s_int)
    tr = Jxx + Jyy
    disc = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2)
    coh = np.where(tr > 0, disc / np.maximum(tr, 1e-9), 0)
    # orientation of the dominant gradient (normal to the sheet): theta_n
    theta_n = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    H, W = I.shape
    yy, xx = np.mgrid[0:H, 0:W]
    X = xx * f + (f - 1) / 2 - cx
    Y = yy * f + (f - 1) / 2 - cy
    r = np.hypot(X, Y)
    phi = np.arctan2(Y, X)
    R = np.sqrt(mask.sum() / np.pi) * f
    sel = mask & (coh > min_coh) & (r > r_min_frac * R)
    # sheet NORMAL should be ~ radial; psi = angle(normal, r_hat) folded to (-90, 90]
    d = theta_n - phi
    psi = (d + np.pi / 2) % np.pi - np.pi / 2
    w = coh[sel]
    ps = psi[sel]
    if not sel.any():
        return dict(n=0, psi_mean_deg=math.nan, frac_pos=math.nan, a0_vox=math.nan, R_vox=float(R))
    # harmonic fit of psi * r (level-0 vox): centre error -> 1st harmonic, crushing -> 2nd;
    # the constant a0 = +- sheet spacing / (2 pi) is the pitch (winding) term
    y = 0.5 * np.sin(2 * ps) * r[sel]
    ph = phi[sel]
    Amat = np.stack([np.ones_like(ph), np.cos(ph), np.sin(ph), np.cos(2 * ph), np.sin(2 * ph),
                     np.cos(3 * ph), np.sin(3 * ph)], 1)
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(Amat * sw[:, None], y * sw, rcond=None)
    return dict(n=int(sel.sum()), psi_mean_deg=float(np.degrees(np.sum(w * np.sin(2 * ps)) / (2 * np.sum(w)))),
                frac_pos=float((ps > 0).mean()), a0_vox=float(coef[0]), R_vox=float(R))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scroll")
    ap.add_argument("prefix")
    ap.add_argument("out")
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--n-slices", type=int, default=12)
    ap.add_argument("--avoid-z", type=float, nargs=2)
    a = ap.parse_args()
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=24,
                                          retries={"max_attempts": 8, "mode": "standard"}))
    pre = a.prefix.rstrip("/")
    za = json.loads(s3.get_object(Bucket=B, Key=f"{pre}/{a.level}/.zarray")["Body"].read())
    Z, Y, X = za["shape"]
    cz, cy, cx = za["chunks"]
    assert za.get("compressor") is None
    sep = za.get("dimension_separator", ".")
    f = 2 ** a.level
    vol = pre.split("/")[-1].split("-")[0]
    uc, _ = A.umbilicus_curve(a.scroll, vol)
    cc, ci = A.centroid_curve(a.scroll)
    centre = uc if uc is not None else cc
    src = "umbilicus" if uc is not None else "centroid"
    zlo, zhi = ci["z_range"]
    zs = np.linspace(zlo + 0.1 * (zhi - zlo), zhi - 0.1 * (zhi - zlo), a.n_slices)
    if a.avoid_z:
        zs = np.array([z for z in zs if not (a.avoid_z[0] <= z <= a.avoid_z[1])])
    pb = cy * cx
    rows = []
    t0 = time.time()

    def fetch(args):
        zl, iy, ix = args
        iz, zz = divmod(zl, cz)
        key = f"{pre}/{a.level}/" + sep.join(map(str, (iz, iy, ix)))
        for i in range(5):
            try:
                b = s3.get_object(Bucket=B, Key=key, Range=f"bytes={zz * pb}-{(zz + 1) * pb - 1}")["Body"].read()
                return iy, ix, np.frombuffer(b, np.uint8).reshape(cy, cx)
            except s3.exceptions.NoSuchKey:
                return iy, ix, None
            except Exception:
                time.sleep(2 ** (i + 1))
        raise RuntimeError(key)

    with ThreadPoolExecutor(20) as ex:
        for z0 in zs:
            zl = int(round((z0 - (f - 1) / 2) / f))
            plane = np.zeros((-(-Y // cy) * cy, -(-X // cx) * cx), np.uint8)
            for iy, ix, arr in ex.map(fetch, [(zl, iy, ix) for iy in range(-(-Y // cy)) for ix in range(-(-X // cx))]):
                if arr is not None:
                    plane[iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = arr
            img = plane[:Y, :X]
            m = img > 0
            ccx, ccy = centre(np.array([zl * f + (f - 1) / 2]))
            r = slice_psi(img, m, float(ccx[0]), float(ccy[0]), f)
            r["z"] = zl * f + (f - 1) / 2
            rows.append(r)
            del plane, img, m
    ps = np.array([r["a0_vox"] for r in rows if r["n"] > 1000])
    res = dict(scroll=a.scroll, volume=pre, level=a.level, centre_source=src, slices=rows, seconds=round(time.time() - t0, 1),
               a0_median_vox=float(np.median(ps)) if ps.size else math.nan,
               n_slices_neg=int((ps < 0).sum()), n_slices_pos=int((ps > 0).sum()),
               w=(1 if np.median(ps) > 0 else -1) if ps.size else 0)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "slices"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
