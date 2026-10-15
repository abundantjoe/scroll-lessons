# Provenance: Project HERCULES | owner the owner | [id removed]
"""Census step 5: local normal-grid sync per seed and time per seed.

The official NormalGridVolume (villa 41701aa core/src/NormalGridVolume.cpp)
reads whole files xy/<z>.grid, xz/<y>.grid, yz/<x>.grid (one file per slice
index, sparse-volume 1, query interpolates slices s and s+1); the *_img
directories are previews it never opens. A seed traced to `g` generations with
step 20 vox reaches at most R = 20 g vox along the sheet (archive: the six
75-generation 1203 team traces fill exactly the L1 ball of radius 1500 vox,
area 4,438,400 vox^2 each, and every bbox side lies within 1471 vox of its
seed). Per seed the sync is therefore:
  upper bound : xy z in [z-R-1, z+R+1], xz y in [y-R-1, y+R+1], yz x in [x-R-1, x+R+1]
  typical     : as upper, but the horizontal axis closest to the local radial
                (sheet-normal) direction shrunk to +-0.41 R (archive: normal-axis
                half extent <= 603 vox at R = 1500).
Time per seed: archive median elapsed at 75 generations (thread_limit 1,
organizer hardware), scaled by (g/75)^2.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

NORMAL_SHRINK = 603.0 / 1500.0


def seed_ranges(seed, centre_xy, R, shape_zyx, typical):
    x, y, z = seed
    Z, Y, X = shape_zyx
    rx = ry = R + 1
    if typical:
        dx, dy = x - centre_xy[0], y - centre_xy[1]
        if abs(dx) >= abs(dy):
            rx = NORMAL_SHRINK * R + 1
        else:
            ry = NORMAL_SHRINK * R + 1
    clip = lambda a, b, n: (max(0, int(math.floor(a))), min(n - 1, int(math.ceil(b))))
    return dict(xy=clip(z - R - 1, z + R + 1, Z), xz=clip(y - ry, y + ry, Y), yz=clip(x - rx, x + rx, X))


def bytes_in(sizes, rng):
    lo, hi = rng
    return int(sizes[lo:hi + 1].sum()), int((sizes[lo:hi + 1] > 0).sum())


def plan(seeds_json, sizes_npz, archive_json, gens=(45, 75)):
    sj = json.load(open(seeds_json))
    sz = dict(np.load(sizes_npz))
    shape = [len(sz["xy"]), len(sz["xz"]), len(sz["yz"])]
    arc = json.load(open(archive_json))
    t75 = [v["meta"]["elapsed_time_s"] for v in arc.values()
           if v["meta"].get("max_gen") == 75 and v["meta"].get("vc_gsfs_mode") == "explicit_seed"]
    t75_med = float(np.median(t75))
    out = dict(scroll=sj["scroll"], archive_t75_s=sorted(t75), archive_t75_median_s=t75_med, per_gen={})
    seeds = [s for s in sj["seeds"] if s.get("seed_xyz")]
    for g in gens:
        R = 20.0 * g
        per = []
        union = {p: np.zeros(n, bool) for p, n in zip(("xy", "xz", "yz"), shape)}
        for s in seeds:
            e = dict(id=s["id"])
            for mode in ("upper", "typical"):
                rr = seed_ranges(s["seed_xyz"], s["centre_xy"], R, shape, mode == "typical")
                tot, nf = 0, 0
                for p in ("xy", "xz", "yz"):
                    b, n = bytes_in(sz[p], rr[p])
                    tot += b
                    nf += n
                    if mode == "upper":
                        union[p][rr[p][0]:rr[p][1] + 1] = True
                e[f"{mode}_bytes"] = tot
                e[f"{mode}_files"] = nf
            per.append(e)
        ub = np.array([e["upper_bytes"] for e in per])
        tb = np.array([e["typical_bytes"] for e in per])
        uni = int(sum(sz[p][union[p]].sum() for p in union))
        full = int(sum(sz[p].sum() for p in ("xy", "xz", "yz")))
        t = t75_med * (g / 75.0) ** 2
        out["per_gen"][str(g)] = dict(reach_vox=R, per_seed_upper_bytes=dict(median=float(np.median(ub)), max=int(ub.max()), min=int(ub.min())),
                                      per_seed_typical_bytes=dict(median=float(np.median(tb)), max=int(tb.max())),
                                      union_60_seeds_bytes=uni, full_planes_bytes=full, union_share_of_full=uni / full if full else None,
                                      time_per_seed_s_archive_scaled=t, time_60_seeds_1thread_h=60 * t / 3600,
                                      time_60_seeds_4parallel_h=60 * t / 3600 / 4, per_seed=per)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--sizes", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    o = plan(a.seeds, a.sizes, a.archive)
    json.dump(o, open(a.out, "w"), indent=1)
    print(json.dumps({g: {k: v for k, v in d.items() if k != "per_seed"} for g, d in o["per_gen"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
