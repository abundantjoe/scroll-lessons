# Provenance: Project HERCULES | owner the owner | [id removed]
"""Planted-sheet synthetic tests for the DECL-P4-7 crossing counter.

A synthetic CT slice holds a squashed Archimedean spiral: N_in planted
windings inward of a designated "w010", followed by windings w010..w022 at
the outer pitch. The labelled "mesh" given to the counter is only the
w010..w022 part (as for the real w010-027 mesh). The counter
(core_count.run_level, identical code and PARAMS) must recover N_in.

Nuisances: squash (aspect a/b), per-winding pitch jitter, sheet gaps,
multiplicative intensity modulation along the sheets, PSF blur, Gaussian
noise, umbilicus offset, touching sheets (thickness close to spacing), and
amorphous (non-sheet) texture filling the core as a false-positive control.
Numbers only; nothing is rendered to a file.
"""

from __future__ import annotations

import json
import math
import sys
import time
import concurrent.futures as cf
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_count as cc  # noqa: E402

VOX_MM = cc.VOX_UM * 1e-3


def spiral_polyline(n_in, pin_c_mm, pout_c_mm, n_out, r0_mm, a, b, rot, rng, jitter=0.1, ds_vox=0.5):
    """Circular-frame spiral r(phi) with piecewise pitch, squashed by (a, b),
    rotated. Returns (xy (n, 2) in vox relative to centre, s (turns from the
    start of w010; negative inward)). Pitch per winding jittered by +-jitter."""
    pitches = np.r_[pin_c_mm * (1 + jitter * rng.uniform(-1, 1, n_in)),
                    pout_c_mm * (1 + jitter * rng.uniform(-1, 1, n_out))]
    phis, rs = [], []
    r = r0_mm
    for k, p in enumerate(pitches):
        rmax = r + p
        L = 2 * math.pi * rmax / VOX_MM * max(a, b)
        n = int(L / ds_vox) + 8
        ph = np.linspace(0, 2 * math.pi, n, endpoint=False)
        phis.append(ph + 2 * math.pi * k)
        rs.append(r + p * ph / (2 * math.pi))
        r = rmax
    ph = np.concatenate(phis)
    rr = np.concatenate(rs) / VOX_MM
    u, v = a * rr * np.cos(ph), b * rr * np.sin(ph)
    c, s_ = math.cos(rot), math.sin(rot)
    xy = np.stack([c * u - s_ * v, s_ * u + c * v], 1)
    s = ph / (2 * math.pi) - n_in
    return xy, s


def render(xy, s, shape, center, thick_vox, gap_frac, mod_amp, psf_vox, snr, rng,
           amorph=0.0, amorph_len_vox=12.0, amorph_region=None):
    H, W = shape
    # sheet gaps: drop random runs of the polyline
    keep = np.ones(len(xy), bool)
    if gap_frac > 0:
        run = 400
        nruns = int(gap_frac * len(xy) / run)
        for st in rng.integers(0, len(xy), nruns):
            keep[st:st + run] = False
    P = xy[keep] + center
    ix = np.round(P[:, 0]).astype(int)
    iy = np.round(P[:, 1]).astype(int)
    ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    mask = np.ones((H, W), bool)
    mask[iy[ok], ix[ok]] = False
    d = ndimage.distance_transform_edt(mask)
    sheet = np.exp(-(d / (0.5 * thick_vox)) ** 4)
    # smooth multiplicative modulation
    m = ndimage.gaussian_filter(rng.standard_normal((H, W)), 40)
    m = 1 + mod_amp * m / (m.std() + 1e-12)
    img = sheet * np.clip(m, 0.2, None)
    if amorph > 0:
        t = ndimage.gaussian_filter(rng.standard_normal((H, W)), amorph_len_vox)
        t = (t - t.min()) / (t.max() - t.min())
        reg = amorph_region if amorph_region is not None else np.ones((H, W), bool)
        img = np.where(reg, np.maximum(img, amorph * t), img)
    img = ndimage.gaussian_filter(img, psf_vox)
    img = img + rng.standard_normal((H, W)) / snr
    return (100 + 60 * img).astype(np.float32)


def run_case(cfg: dict) -> dict:
    rng = np.random.default_rng(cfg["seed"])
    a, b = cfg["aspect"]
    rot = rng.uniform(0, math.pi)
    pin_c = cfg["pin_normal_mm"] / b
    pout_c = cfg["pout_normal_mm"] / b
    xy, s = spiral_polyline(cfg["n_in"], pin_c, pout_c, 13, cfg["r0_mm"], a, b, rot, rng)
    R = np.abs(xy).max() + 40
    H = W = int(2 * R)
    center = np.array([W / 2, H / 2])
    thick = cfg["thick_frac"] * min(cfg["pin_normal_mm"], cfg["pout_normal_mm"]) / VOX_MM
    thick = max(thick, 4.0)
    amorph_region = None
    if cfg.get("amorph", 0) > 0:
        # core region = inside the w010 loop (approx: points with s < 0 bound)
        inner = xy[(s >= 0) & (s < 1)] + center
        from matplotlib.path import Path as MPath  # geometry only
        yy, xx = np.mgrid[0:H, 0:W]
        amorph_region = MPath(inner).contains_points(np.c_[xx.ravel(), yy.ravel()]).reshape(H, W)
    img = render(xy, s, (H, W), center, thick, cfg["gap_frac"], cfg["mod_amp"], cfg["psf_vox"], cfg["snr"], rng,
                 amorph=cfg.get("amorph", 0.0), amorph_region=amorph_region)
    # labelled "mesh": polyline part s >= 0, as segments
    m = s >= 0
    P = xy[m] + center
    sm = s[m]
    P0, P1, s0, s1 = P[:-1], P[1:], sm[:-1], sm[1:]
    off = rng.uniform(0, 2 * math.pi)
    cen = center + cfg["umb_off_mm"] / VOX_MM * np.array([math.cos(off), math.sin(off)])
    angles = np.linspace(0, 2 * math.pi, cc.PARAMS["n_rays"], endpoint=False)
    cr = cc.ray_crossings(P0, P1, s0, s1, cen, angles)
    wr = [cc.winding_radii(r, ss)[0] for r, ss in cr]
    res = {}
    for key, spec in (("primary", cc.PARAMS["smooth_primary"]), ("secondary", cc.PARAMS["smooth_secondary"])):
        out = cc.run_level(img, (0, 0), cen, angles, wr, cc.PARAMS["prom_frac"], cc.sigma_vox(spec))
        n = np.array([o["n_inner"] if o else np.nan for o in out], float)
        ncal = np.array([o["n_cal"] if o else np.nan for o in out], float)
        err = n - cfg["n_in"]
        f = np.isfinite(err)
        half = len(n) // 2
        diam = (n[:half] + n[half:]) / 2
        res[key] = {"n_rays_valid": int(f.sum()),
                    "median_count": float(np.nanmedian(n)) if f.any() else None,
                    "median_err": float(np.nanmedian(err)) if f.any() else None,
                    "frac_rays_abs_err_le1": float(np.mean(np.abs(err[f]) <= 1)) if f.any() else None,
                    "mean_abs_err_rays": float(np.mean(np.abs(err[f]))) if f.any() else None,
                    "diam_median_err": float(np.nanmedian(diam) - cfg["n_in"]) if np.isfinite(diam).any() else None,
                    "cal_median": float(np.nanmedian(ncal)) if f.any() else None,
                    "cal_frac_eq10": float(np.mean(ncal[f] == 10)) if f.any() else None,
                    "step_rate_rays": cc.step_rate(n, 0, True)}
    return {"cfg": cfg, **res}


def grid(seed0=20260926):
    cases = []
    k = 0
    for n_in in (0, 4, 7, 10, 13):
        for pin in (0.04, 0.07, 0.12):
            for snr in (1.0, 2.0, 4.0):
                for off in (0.0, 0.15):
                    for tf in (0.5, 0.8):
                        cases.append(dict(n_in=n_in, pin_normal_mm=pin, pout_normal_mm=0.13, aspect=(1.6, 0.6),
                                          r0_mm=0.05, thick_frac=tf, gap_frac=0.15, mod_amp=0.25, psf_vox=1.5,
                                          snr=snr, umb_off_mm=off, seed=seed0 + k, group="main"))
                        k += 1
    # false-positive controls: no inner sheets, amorphous texture in the core
    for amorph in (0.3, 0.6, 1.0):
        for snr in (2.0, 4.0):
            for rep in range(2):
                cases.append(dict(n_in=0, pin_normal_mm=0.07, pout_normal_mm=0.13, aspect=(1.6, 0.6), r0_mm=0.6,
                                  thick_frac=0.5, gap_frac=0.15, mod_amp=0.25, psf_vox=1.5, snr=snr, umb_off_mm=0.0,
                                  amorph=amorph, seed=seed0 + 1000 + k, group="amorph_control"))
                k += 1
    return cases


if __name__ == "__main__":
    out_path = sys.argv[1]
    cases = grid()
    t0 = time.time()
    with cf.ProcessPoolExecutor(4) as ex:
        results = list(ex.map(run_case, cases, chunksize=1))
    json.dump({"provenance": "Project HERCULES | owner the owner | [id removed]",
               "params": cc.PARAMS, "n_cases": len(results), "wall_s": time.time() - t0, "results": results},
              open(out_path, "w"), indent=0)
    print("done", len(results), time.time() - t0)
