#!/usr/bin/env python
"""RULES R-INTERIOR: does either published product resolve individual wraps in the scroll INTERIOR?

R-RADIAL showed 89 % of inner-half traces failing at the geometry stage. The tracer runs on the surface prediction
(`predictions/surfaces/...-th0.2.zarr`); the seeds density gate already showed interior neighbourhoods are DENSE
there, which is what adjacent wraps look like when a model cannot separate them. The lasagna `cos` winding-phase field
is the alternative, a continuous field whose level sets are sheets.

Along radial rays from the published umbilicus, inside r/R in [lo, hi], this counts the wraps each product resolves and
compares both with the sheet spacing the CT itself shows (first autocorrelation peak of the CT profile along the same
ray). All three are sampled on the SAME rays at the SAME points, so the counts are comparable.

usage: interior_resolve.py --scroll PHerc0826 [--n-z 4] [--rays 24] [--lo 0.2] [--hi 0.5] [--out JSON]
"""
import argparse, json, os, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lasagna_normal as L          # BloscZarr, lasagna_base
import patch_qc                     # ChunkedCT (raw uint8 levels of the masked CT)
import radial_position as RP        # umbilicus, L4Mask
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BUCKET = L.BUCKET
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def surface_pred_url(scroll):
    q = {"list-type": "2", "prefix": f"{scroll}/representations/predictions/surfaces/", "delimiter": "/", "max-keys": "100"}
    with urllib.request.urlopen(f"{BUCKET}/?{urllib.parse.urlencode(q)}", timeout=120) as r:
        root = ET.fromstring(r.read())
    dirs = [c.findtext(NS + "Prefix") for c in root.findall(NS + "CommonPrefixes") if c.findtext(NS + "Prefix").rstrip("/").endswith(".zarr")]
    return f"{BUCKET}/{sorted(dirs)[-1].rstrip('/')}"


def runs_above(v, thr):
    """Number of connected runs of v >= thr separated by at least one sample below it."""
    a = v >= thr
    return int(np.sum(a[1:] & ~a[:-1]) + (1 if a.size and a[0] else 0))


def oscillations(c, min_amp=0.2):
    """Complete oscillations of c about its median: zero crossings counted in pairs, excursions below min_amp ignored."""
    d = c - np.median(c)
    keep = np.abs(d) >= min_amp
    if keep.sum() < 4:
        return 0
    s = np.sign(d[keep])
    return int(np.sum(s[1:] != s[:-1]) // 2)


def first_acf_peak(v, lo=2, hi=None):
    """Lag of the first autocorrelation peak of v (the sheet spacing the data itself shows), in samples."""
    v = v - v.mean()
    if v.std() < 1e-6:
        return None
    a = np.correlate(v, v, "full")[len(v) - 1:]
    a = a / a[0]
    hi = hi or len(a) - 1
    seg = a[lo:hi]
    if seg.size < 3:
        return None
    i = int(np.argmax(seg[1:-1] * (seg[1:-1] > seg[:-2]) * (seg[1:-1] > seg[2:]))) + 1
    return lo + i if seg[i] > 0.1 else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scroll", required=True)
    ap.add_argument("--n-z", type=int, default=4); ap.add_argument("--rays", type=int, default=24)
    ap.add_argument("--lo", type=float, default=0.20); ap.add_argument("--hi", type=float, default=0.50)
    ap.add_argument("--step", type=float, default=1.0, help="sample step along the ray, in voxels of the phase level")
    ap.add_argument("--out")
    a = ap.parse_args(argv)

    um = RP.umbilicus(a.scroll)
    if um is None:
        raise SystemExit(f"{a.scroll}: no published umbilicus; R-INTERIOR needs the axis")
    base, man = L.lasagna_base(a.scroll)
    cos = L.BloscZarr(f"{BUCKET}/{urllib.parse.quote(base + man['groups']['cos']['zarr'])}",
                      f"{DATA}/lasagna_cache/{a.scroll}/cos")
    dcos = man["base_shape_zyx"][0] / cos.shape[0]                      # level-0 voxels per phase voxel
    # all three products are read at the SAME physical scale (level 1 = half the CT level-0 pitch, which is where the
    # phase field is published), with one reader that handles both the blosc-compressed predictions and the raw CT
    pred = L.BloscZarr(surface_pred_url(a.scroll) + "/1", f"{DATA}/pred_l1_cache/{a.scroll}")
    dpred = man["base_shape_zyx"][0] / pred.shape[0]
    ct = L.BloscZarr(RP.L4Mask._url(a.scroll) + "/1", f"{DATA}/ct_l1_cache/{a.scroll}")
    dct = man["base_shape_zyx"][0] / ct.shape[0]
    l4 = RP.L4Mask(a.scroll, f"{DATA}/ct_l4_cache/{a.scroll}")

    z0, z1 = float(um[0].min()), float(um[0].max())
    zs = np.linspace(z0 + 0.15 * (z1 - z0), z0 - 0.15 * (z1 - z0) + (z1 - z0), a.n_z)
    rows = []
    for z in zs:
        st = l4.at(int(round(z / 16)))
        if st is None:
            continue
        R = st[2] * 16.0                                                # outer edge radius in level-0 voxels
        cx, cy = RP.axis_at(um, np.array([z]))[0]
        for k in range(a.rays):
            th = 2 * np.pi * k / a.rays
            rr = np.arange(a.lo * R, a.hi * R, a.step * dcos)
            px, py = cx + rr * np.cos(th), cy + rr * np.sin(th)
            pz = np.full_like(rr, z)
            ci = np.rint(np.stack([pz / dcos, py / dcos, px / dcos], 1)).astype(np.int64)
            cv = cos.sample(ci).astype(np.float64)
            if (cv == 0).mean() > 0.5:
                continue                                                # ray mostly outside the published field
            c = cv / 127.5 - 1.0
            pi = np.rint(np.stack([pz / dpred, py / dpred, px / dpred], 1)).astype(np.int64)
            pv = pred.sample(pi).astype(np.float64)
            ti = np.rint(np.stack([pz / dct, py / dct, px / dct], 1)).astype(np.int64)
            tv = ct.sample(ti).astype(np.float64)
            lag = first_acf_peak(tv)
            rows.append(dict(z=float(z), ray=k, n_samples=int(rr.size),
                             phase_wraps=oscillations(c), pred_runs=runs_above(pv, 0.2 * 255),
                             ct_acf_lag_vx=None if lag is None else float(lag * a.step * dcos),
                             span_vx=float(rr[-1] - rr[0])))
    res = dict(scroll=a.scroll, band=[a.lo, a.hi], n_rays=len(rows), phase_level_div=dcos,
               pred_level_div=dpred, ct_level_div=dct)
    if rows:
        ph = np.array([r["phase_wraps"] for r in rows], float)
        pr = np.array([r["pred_runs"] for r in rows], float)
        span = np.array([r["span_vx"] for r in rows], float)
        lags = np.array([r["ct_acf_lag_vx"] for r in rows if r["ct_acf_lag_vx"]], float)
        ph_sp = np.divide(span, np.maximum(ph, 1e-9), out=np.full_like(span, np.nan), where=ph > 0)
        pr_sp = np.divide(span, np.maximum(pr, 1e-9), out=np.full_like(span, np.nan), where=pr > 0)
        res.update(phase_wraps_median=float(np.median(ph)), pred_runs_median=float(np.median(pr)),
                   ratio=float(np.median(ph) / max(np.median(pr), 1e-9)),
                   phase_spacing_vx=float(np.nanmedian(ph_sp)), pred_spacing_vx=float(np.nanmedian(pr_sp)),
                   ct_acf_spacing_vx=float(np.median(lags)) if lags.size else None,
                   span_vx_median=float(np.median(span)))
        if res["ct_acf_spacing_vx"]:
            res["phase_vs_ct_spacing_err"] = round(abs(res["phase_spacing_vx"] / res["ct_acf_spacing_vx"] - 1), 4)
            res["pred_vs_ct_spacing_err"] = round(abs(res["pred_spacing_vx"] / res["ct_acf_spacing_vx"] - 1), 4)
        res["criterion_ratio_ge_1p5"] = bool(res["ratio"] >= 1.5)
        res["criterion_spacing_within_30pct"] = bool(res.get("phase_vs_ct_spacing_err") is not None
                                                     and res["phase_vs_ct_spacing_err"] <= 0.30)
        res["passed"] = bool(len(rows) >= 20 and res["criterion_ratio_ge_1p5"] and res["criterion_spacing_within_30pct"])
    res["rays"] = rows
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rays"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
