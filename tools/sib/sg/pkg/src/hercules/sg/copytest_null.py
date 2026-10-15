# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic null of the DECL-SG 7 copy statistic (no real data, no images viewed).

For independent Gaussian-smoothed white-noise fields (correlation scale sigma px), measure
the maximum masked NCC of a crop over 24 rotation steps x every placement x n_patches
unrelated patches of side 2d.  Any value >= 0.8 is a FALSE copy flag, because crop and
patches are independent by construction.  Output: JSON per (sigma, d) with the max-NCC of
each crop and the false-flag fraction.  Resumable: finished cells are skipped.

  python -m hercules.sg.copytest_null --out logs/sib/sg/copytest_null.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from . import copytest as T

SIGMAS = (1.0, 2.0, 4.0, 8.0)
DISCS = (32, 64, 128)
N_CROPS = 8
N_PATCHES = 100
SEED = 20260925


def field(rng, shape, sigma):
    return cv2.GaussianBlur(rng.standard_normal(shape), (0, 0), sigma)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    res = json.loads(out.read_text()) if out.exists() else {"seed": SEED, "n_crops": N_CROPS, "n_patches": N_PATCHES,
                                                             "rotations": len(T.SG7_ROTATIONS_DEG), "cells": {}}
    for d in DISCS:
        for s in SIGMAS:
            key = f"d{d}_s{s:g}"
            if key in res["cells"]:
                continue
            rng = np.random.default_rng([SEED, d, int(s * 10)])
            patches = [field(rng, (2 * d, 2 * d), s) for _ in range(N_PATCHES)]
            crops = [field(rng, (d, d), s) for _ in range(N_CROPS)]
            t = time.perf_counter()
            r = T.copy_test(crops, patches, enforce_neff=False)
            mx = [p["max_abs_ncc"] for p in r["per_letter"]]
            n_eff = float(np.median([p["n_eff"] for p in r["per_letter"]]))  # measured by coherence_area_px
            res["cells"][key] = {"d": d, "sigma": s, "n_eff_approx": n_eff, "max_ncc_per_crop": mx,
                                 "median_max_ncc": float(np.median(mx)), "false_flag_fraction": float(np.mean(np.array(mx) >= 0.8)),
                                 "placements_per_patch": (d + 1) ** 2, "seconds": time.perf_counter() - t}
            out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
            print(key, round(float(np.median(mx)), 3), res["cells"][key]["false_flag_fraction"], flush=True)
    # extreme-value growth with the number of label patches (fixed d, sigma)
    for d, s, n_p in ((64, 2.0, 1000), (64, 4.0, 1000)):
        key = f"d{d}_s{s:g}_p{n_p}"
        if key in res["cells"]:
            continue
        rng = np.random.default_rng([SEED, d, int(s * 10), n_p])
        patches = [field(rng, (2 * d, 2 * d), s) for _ in range(n_p)]
        crops = [field(rng, (d, d), s) for _ in range(N_CROPS)]
        t = time.perf_counter()
        r = T.copy_test(crops, patches, enforce_neff=False)
        mx = [p["max_abs_ncc"] for p in r["per_letter"]]
        res["cells"][key] = {"d": d, "sigma": s, "n_patches": n_p, "n_eff_approx": float(np.median([p["n_eff"] for p in r["per_letter"]])),
                             "max_ncc_per_crop": mx, "median_max_ncc": float(np.median(mx)),
                             "false_flag_fraction": float(np.mean(np.array(mx) >= 0.8)), "seconds": time.perf_counter() - t}
        out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        print(key, round(float(np.median(mx)), 3), flush=True)


if __name__ == "__main__":
    main()
