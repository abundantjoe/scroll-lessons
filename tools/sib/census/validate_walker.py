# Provenance: Project HERCULES | owner the owner | [id removed]
"""Validation of the duplicate-sheet walker against official traced sheets.

Positive pairs: two vertices of the same official PHerc1203 team segment
(dev set only; the five T0 test-set segments are never opened), surface
distance 400-1800 vox, both on m7==255 (nearest-run snap along the radial).
Negative pairs: the same pairs with vertex j moved radially to the adjacent
m7 run (the neighbouring sheet), which must not be called "same".
Reports sensitivity (same | positive), false-same rate (same | negative) and
undetermined shares. Numbers only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import plan_seeds as P  # noqa: E402
from centre import centroid_curve, load_shape  # noqa: E402

T0 = {"auto_grown_20250923163217042", "auto_grown_20250923163219195", "auto_grown_20250923163223390",
      "auto_grown_20250923163227956", "auto_grown_20250923163230146"}


def load_seg(s3, name):
    import tifffile

    arr, sha = {}, {}
    for c in "xyz":
        b = s3.get_object(Bucket=P.BUCKET, Key=f"PHerc1203/segments/raw/{name}/{c}.tif")["Body"].read()
        sha[c] = hashlib.sha256(b).hexdigest()
        arr[c] = tifffile.imread(io.BytesIO(b)).astype(float)
    return np.stack([arr["x"], arr["y"], arr["z"]], -1), sha


def adjacent_run(m7, curve, q, direction, max_off=80):
    cx, cy = P.centre_at(curve, q[2])
    th = math.atan2(q[1] - cy, q[0] - cx)
    r = math.hypot(q[0] - cx, q[1] - cy)
    rr = r + direction * np.arange(0, max_off + 1, 1.0)
    pts = np.c_[cx + rr * math.cos(th), cy + rr * math.sin(th), np.full(rr.size, q[2])]
    v = m7.points(pts) == 255
    # leave the current band, cross a gap, take the next band's centre
    i = 0
    while i < v.size and v[i]:
        i += 1
    while i < v.size and not v[i]:
        i += 1
    if i >= v.size:
        return None
    j = i
    while j < v.size and v[j]:
        j += 1
    rc = 0.5 * (rr[i] + rr[j - 1])
    return (cx + rc * math.cos(th), cy + rc * math.sin(th), q[2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="data/catalogue/eligible_products.json")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--mask", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pairs-per-seg", type=int, default=8)
    ap.add_argument("--track-half", type=int, default=4)
    ap.add_argument("--max-gap", type=float, default=48.0)
    ap.add_argument("--walker", choices=["v1", "v2"], default="v2")
    ap.add_argument("--step", type=float, default=4.0)
    ap.add_argument("--max-shift", type=float, default=3.0)
    a = ap.parse_args()
    cat = json.load(open(a.catalogue))
    v = next(v for v in cat["volumes"] if v["scroll"] == "PHerc1203")
    arc = json.load(open(a.archive))
    segs = [s for s, d in arc.items() if s not in T0 and d["meta"].get("vc_gsfs_mode") == "explicit_seed"]
    sh = load_shape(a.mask, "PHerc1203")
    zc, xc, yc, _ = centroid_curve(sh)
    curve = (zc, xc, yc)
    m7 = P.M7Volume("PHerc1203", v["volume_id"], max_chunks=300)
    rng = np.random.default_rng(20260925)
    if a.walker == "v1":
        walk = lambda u, w: P.sheet_walk(m7, curve, u, w, max_gap=a.max_gap, track_half=a.track_half)
    else:
        walk = lambda u, w: P.sheet_walk_v2(m7, u, w, step=a.step, max_gap=a.max_gap, max_shift=a.max_shift)
    res, hashes = [], {}
    for name in segs:
        pts, sha = load_seg(m7.s3, name)
        hashes[name] = sha
        ok = np.isfinite(pts).all(-1) & (pts[..., 2] > 0)
        idx = np.argwhere(ok)
        n = 0
        tries = 0
        while n < a.pairs_per_seg and tries < 400:
            tries += 1
            i, j = idx[rng.integers(len(idx))], idx[rng.integers(len(idx))]
            pi, pj = pts[tuple(i)], pts[tuple(j)]
            sd = P.surface_distance(curve, pi, pj)
            if not (400 <= sd <= 1800):
                continue
            # vertices to nearest m7 run centre on their radial line
            snapped = []
            for p in (pi, pj):
                cx, cy = P.centre_at(curve, p[2])
                th = math.atan2(p[1] - cy, p[0] - cx)
                r = math.hypot(p[0] - cx, p[1] - cy)
                rc, _ = P.radial_run(m7, cx, cy, p[2], th, r, half=6)
                snapped.append(None if rc is None else (cx + rc * math.cos(th), cy + rc * math.sin(th), float(p[2])))
            if None in snapped:
                continue
            n += 1
            wp = walk(snapped[0], snapped[1])
            neg = adjacent_run(m7, curve, snapped[1], +1 if rng.random() < 0.5 else -1)
            wn = walk(snapped[0], neg) if neg else None
            res.append(dict(seg=name, surface_dist=round(sd, 1), pos=wp["verdict"], pos_dr=wp["dr"],
                            neg=wn["verdict"] if wn else "no-adjacent", neg_dr=wn["dr"] if wn else None))
            print(json.dumps(res[-1]), flush=True)
    pos = [r["pos"] for r in res]
    neg = [r["neg"] for r in res if r["neg"] != "no-adjacent"]
    summ = dict(n_pos=len(pos), pos_same=pos.count("same"), pos_different=pos.count("different"),
                pos_undetermined=pos.count("undetermined"), n_neg=len(neg), neg_same=neg.count("same"),
                neg_different=neg.count("different"), neg_undetermined=neg.count("undetermined"),
                sensitivity_determined=pos.count("same") / max(1, pos.count("same") + pos.count("different")),
                false_same_determined=neg.count("same") / max(1, neg.count("same") + neg.count("different")),
                params=dict(walker=a.walker, step=a.step, max_shift=a.max_shift, track_half=a.track_half, max_gap=a.max_gap, tol=P.DUP_TOL), segment_tif_sha256=hashes,
                centre="PHerc1203 CT-mask centroid (no official umbilicus)")
    json.dump(dict(summary=summ, pairs=res), open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "segment_tif_sha256"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
