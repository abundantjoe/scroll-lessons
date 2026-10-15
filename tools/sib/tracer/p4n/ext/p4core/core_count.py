# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-7 items 1-2: sheet-crossing count inward of the w010 mesh of
PHerc. Paris 4 on the 2.4 um volume (20260411134726), numbers only.

No image is written, displayed or described. CT voxels are streamed as
numeric arrays (HTTP byte ranges into the uncompressed level-0 zarr chunks),
reduced to 1-D ray profiles and peak positions, and discarded. Only
aggregate statistics (counts, spacings, fractions) are logged.

Pipeline (parameters fixed in PARAMS before any CT value was fetched):
  1. z-level z0 (voxel index); the slab z0-4..z0+4 (9 slices, 21.6 um) is
     averaged (sheets run along the roll axis, so this averages noise, not
     sheets).
  2. 2-D Gaussian smoothing. DECL-P4-7 says "a 20 um smoothing"; primary
     interpretation: Gaussian FWHM 20 um (sigma 8.49 um = 3.54 vox);
     secondary: sigma 20 um (8.33 vox). Both are reported.
  3. Centre = official umbilicus (representations/umbilicus/
     20260411134726-umbilicus-20260524235033.json), linear in z.
  4. N_RAYS rays; each ray's crossings with the w010-027 mesh
     (20260701183124, triangle/plane intersection), labelled by the mesh's
     own winding coordinate s (unwrapped angle along the grid row, 0 at the
     inner end), so w0(10+k) is the crossing with floor(s) == k.
  5. Profile along the ray at 1 vox step (bilinear); peaks with
     scipy.signal.find_peaks, prominence >= PROM_FRAC * (p95 - p5 of the
     profile over the ray's own w010..w020 span), min distance MIN_DIST_UM.
  6. Inner count = peaks with r < r_w010 - 0.5 (r_w011 - r_w010).
     Calibration count = peaks in [r_w010 - h10, r_w020 - h19) (expect 10),
     where h_k is half the along-ray gap from w0k to the next winding.
"""

from __future__ import annotations

import json
import math
import concurrent.futures as cf
import urllib.request

import numpy as np
from scipy import ndimage, signal

VOX_UM = 2.4
PARAMS = {
    "n_rays": 128,
    "slab_half": 4,                   # slices each side -> 9 slices
    "smooth_primary": {"kind": "fwhm", "um": 20.0},
    "smooth_secondary": {"kind": "sigma", "um": 20.0},
    "prom_frac": 0.25,                # primary
    "prom_frac_sweep": [0.10, 0.15, 0.25, 0.35, 0.50],
    "min_dist_um": 12.0,
    "step_vox": 1.0,
}
VOL = ("https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/volumes/"
       "20260411134726-2.400um-0.2m-78keV-masked.zarr/0")
CH = 128
SHAPE = (75784, 32693, 32693)


def sigma_vox(spec: dict) -> float:
    s_um = spec["um"] / (2 * math.sqrt(2 * math.log(2))) if spec["kind"] == "fwhm" else spec["um"]
    return s_um / VOX_UM


# ---------------------------------------------------------------------------
# streamed CT slab (level 0, uncompressed chunks: byte ranges per z slice)
# ---------------------------------------------------------------------------

def _fetch(url: str, lo: int, hi: int, tries: int = 5) -> bytes | None:
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={lo}-{hi}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None      # absent chunk -> fill value 0
            last = e
        except Exception as e:  # network: retry with backoff
            last = e
        import time
        time.sleep(2 ** k)
    raise RuntimeError(f"fetch failed {url}: {last}")


def read_slab_mean(z0: int, y0: int, y1: int, x0: int, x1: int, half: int, workers: int = 48) -> tuple[np.ndarray, float]:
    """Mean over z0-half..z0+half of vol[z, y0:y1, x0:x1] (float32) and the
    fraction of absent chunks. All slices must lie in one z chunk."""
    cz = z0 // CH
    assert (z0 - half) // CH == cz and (z0 + half) // CH == cz, "slab crosses a z chunk"
    lz0 = z0 - half - cz * CH
    nz = 2 * half + 1
    out = np.zeros((y1 - y0, x1 - x0), np.float64)
    jobs = []
    for cy in range(y0 // CH, (y1 - 1) // CH + 1):
        for cx in range(x0 // CH, (x1 - 1) // CH + 1):
            jobs.append((cy, cx))
    absent = 0

    def work(j):
        cy, cx = j
        b = _fetch(f"{VOL}/{cz}/{cy}/{cx}", lz0 * CH * CH, (lz0 + nz) * CH * CH - 1)
        return j, b

    with cf.ThreadPoolExecutor(workers) as ex:
        for (cy, cx), b in ex.map(work, jobs):
            if b is None:
                absent += 1
                continue
            a = np.frombuffer(b, np.uint8).reshape(nz, CH, CH).mean(0)
            gy0, gx0 = cy * CH, cx * CH
            sy0, sy1 = max(y0, gy0), min(y1, gy0 + CH)
            sx0, sx1 = max(x0, gx0), min(x1, gx0 + CH)
            out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a[sy0 - gy0:sy1 - gy0, sx0 - gx0:sx1 - gx0]
    return out.astype(np.float32), absent / max(1, len(jobs))


# ---------------------------------------------------------------------------
# mesh / plane intersection and ray crossings
# ---------------------------------------------------------------------------

def plane_segments(X, Y, Z, S, z0: float):
    """Segments where the plane z = z0 cuts the triangulated tifxyz grid.
    Returns (P0, P1, s0, s1): endpoints (n, 2) in (x, y) and the winding
    coordinate s interpolated at each endpoint. Triangles as FLAT-1
    (p10, p00, p01) and (p10, p01, p11)."""
    valid = (X != -1) & np.isfinite(Z) & (Z > 0) & np.isfinite(S)
    rows = np.where(np.any(valid & (np.abs(Z - z0) < 2000), axis=1))[0]
    if rows.size == 0:
        return (np.zeros((0, 2)),) * 2 + (np.zeros(0),) * 2
    r0, r1 = max(rows.min() - 1, 0), min(rows.max() + 2, X.shape[0])
    sl = slice(r0, r1)
    x, y, z, s, v = X[sl].astype(np.float64), Y[sl].astype(np.float64), Z[sl].astype(np.float64), S[sl].astype(np.float64), valid[sl]
    P = np.stack([x, y, z - z0, s], -1)
    p00, p01, p10, p11 = P[:-1, :-1], P[:-1, 1:], P[1:, :-1], P[1:, 1:]
    qv = v[:-1, :-1] & v[:-1, 1:] & v[1:, :-1] & v[1:, 1:]
    segs0, segs1 = [], []
    for tri in ((p10, p00, p01), (p10, p01, p11)):
        A, B, C = (t[qv] for t in tri)
        # nudge exact zeros
        for T in (A, B, C):
            T[:, 2] = np.where(T[:, 2] == 0, 1e-6, T[:, 2])
        pts = []
        crossm = []
        for U, W in ((A, B), (B, C), (C, A)):
            c = (U[:, 2] > 0) != (W[:, 2] > 0)
            t = U[:, 2] / (U[:, 2] - W[:, 2])
            Q = U + (W - U) * t[:, None]
            pts.append(Q)
            crossm.append(c)
        crossm = np.stack(crossm, 1)
        ok = crossm.sum(1) == 2
        pts = np.stack(pts, 1)[ok]
        cm = crossm[ok]
        idx = np.argsort(~cm, axis=1, kind="stable")[:, :2]
        e0 = pts[np.arange(len(pts)), idx[:, 0]]
        e1 = pts[np.arange(len(pts)), idx[:, 1]]
        segs0.append(e0)
        segs1.append(e1)
    e0 = np.concatenate(segs0)
    e1 = np.concatenate(segs1)
    return e0[:, :2], e1[:, :2], e0[:, 3], e1[:, 3]


def ray_crossings(P0, P1, s0, s1, center, angles):
    """For each angle: list of (r, s) where the ray from center hits a segment."""
    c = np.asarray(center, float)
    res = []
    a = P0 - c
    b = P1 - c
    for th in angles:
        d = np.array([math.cos(th), math.sin(th)])
        n = np.array([-d[1], d[0]])
        fa, fb = a @ n, b @ n
        m = (fa > 0) != (fb > 0)
        t = fa[m] / (fa[m] - fb[m])
        q = a[m] + (b[m] - a[m]) * t[:, None]
        r = q @ d
        s = s0[m] + (s1[m] - s0[m]) * t
        keep = r > 0
        o = np.argsort(r[keep])
        res.append((r[keep][o], s[keep][o]))
    return res


def winding_radii(r, s, kmax: int = 11):
    """Along-ray radius of the innermost crossing with floor(s) == k, k = 0..kmax
    (NaN if absent), plus a sanity flag: consecutive crossings differ by ~1 turn."""
    out = np.full(kmax + 1, np.nan)
    k = np.floor(s + 1e-9).astype(int)
    for kk in range(kmax + 1):
        sel = np.where(k == kk)[0]
        if sel.size:
            out[kk] = r[sel[0]]
    ds = np.diff(s[: kmax + 2]) if s.size > 1 else np.zeros(0)
    ordered = bool(ds.size and np.all(np.abs(ds - 1) < 0.35))
    return out, ordered


# ---------------------------------------------------------------------------
# profile peaks
# ---------------------------------------------------------------------------

def ray_profile(img, origin_yx, center_xy, theta, rmax, step=1.0):
    r = np.arange(0.0, rmax, step)
    xs = center_xy[0] + r * math.cos(theta) - origin_yx[1]
    ys = center_xy[1] + r * math.sin(theta) - origin_yx[0]
    v = ndimage.map_coordinates(img, [ys, xs], order=1, mode="constant", cval=np.nan)
    return r, v


def count_on_ray(r, v, wr, prom_frac, min_dist_vox):
    """wr: along-ray radii of w010..w021 (index 0..11). Returns dict or None."""
    if not (np.isfinite(wr[0]) and np.isfinite(wr[1]) and np.isfinite(wr[10]) and np.isfinite(wr[9])):
        return None
    h0 = 0.5 * (wr[1] - wr[0])
    h9 = 0.5 * (wr[10] - wr[9])
    if not (h0 > 0 and h9 > 0):
        return None
    cal = (r >= wr[0] - h0) & (r < wr[10] - h9)
    vc = v[cal]
    if vc.size < 10 or not np.all(np.isfinite(vc)):
        return None
    lo, hi = np.percentile(vc, [5, 95])
    prom = prom_frac * (hi - lo)
    if not prom > 0:
        return None
    vv = np.where(np.isfinite(v), v, np.nanmin(v))
    pk, _ = signal.find_peaks(vv, prominence=prom, distance=max(1, int(round(min_dist_vox))))
    rp = r[pk]
    inner_lim = wr[0] - h0
    inner = rp[rp < inner_lim]
    ncal = int(np.sum((rp >= wr[0] - h0) & (rp < wr[10] - h9)))
    # expected crossing positions in calibration span vs peaks (matched within half gap)
    return {"n_inner": int(inner.size), "n_cal": ncal, "r_inner_lim": float(inner_lim),
            "inner_peaks_r": inner.tolist(), "cal_span": float(wr[10] - h9 - (wr[0] - h0)),
            "zero_frac_inner": float(np.mean(v[r < inner_lim] == 0)) if np.any(r < inner_lim) else math.nan}


def run_level(img, origin_yx, center_xy, angles, wradii, prom_frac, smooth_sigma_vox, min_dist_um=PARAMS["min_dist_um"]):
    """img: raw slab mean (float32). Returns per-ray result list."""
    sm = ndimage.gaussian_filter(img.astype(np.float32), smooth_sigma_vox)
    out = []
    for th, wr in zip(angles, wradii):
        if not np.isfinite(wr[10]):
            out.append(None)
            continue
        rmax = wr[10] + 0.5 * (wr[11] - wr[10] if np.isfinite(wr[11]) else wr[10] - wr[9]) + 5
        r, v = ray_profile(sm, origin_yx, center_xy, th, rmax)
        out.append(count_on_ray(r, v, wr, prom_frac, min_dist_um / VOX_UM))
    return out


# ---------------------------------------------------------------------------
# summaries
# ---------------------------------------------------------------------------

def step_rate(counts: np.ndarray, axis: int, circular: bool) -> dict:
    """Fraction of adjacent pairs (along axis) whose counts differ by >= 1 / >= 2."""
    c = np.asarray(counts, float)
    d = np.abs(np.diff(np.concatenate([c, np.take(c, [0], axis=axis)], axis=axis) if circular else c, axis=axis))
    d = d[np.isfinite(d)]
    if d.size == 0:
        return {"n_pairs": 0, "ge1": math.nan, "ge2": math.nan}
    return {"n_pairs": int(d.size), "ge1": float(np.mean(d >= 1)), "ge2": float(np.mean(d >= 2))}


def describe(a) -> dict:
    a = np.asarray([v for v in a if v is not None and np.isfinite(v)], float)
    if a.size == 0:
        return {"n": 0}
    q = np.percentile(a, [5, 25, 50, 75, 95])
    return {"n": int(a.size), "mean": float(a.mean()), "p5": float(q[0]), "p25": float(q[1]), "median": float(q[2]),
            "p75": float(q[3]), "p95": float(q[4]), "min": float(a.min()), "max": float(a.max())}


if __name__ == "__main__":
    print(json.dumps(PARAMS, indent=1))
