#!/usr/bin/env python
"""coverage_proxy.py -- can a trace's PAPYRUS COVERAGE be predicted from the CT without rendering it?

R-COVER9 measured that our surfaces spend two fifths of their area off the papyrus, and that the consensus surfaces
that buy us canvas size are the worst.  Selecting consensus sources on coverage would fix that - but coverage is only
known after a render, which costs more than the selection saves.

This builds a cheap proxy (level-4 CT intensity sampled at the trace's own grid points) and VALIDATES IT against the
31 surfaces whose true rendered coverage is already recorded.  The proxy is used for nothing unless it predicts.
"""
import argparse, glob, json, os, sys
import numpy as np, tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55
from patch_qc import ChunkedCT, CT_LEVEL, CT_SCALE
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
AIR_MAX = 40.0          # RULES R-COVER: air reads 30-40 on the 8-bit scale, papyrus 80-130
EVERY = 7               # sample every Nth grid node; the grids are ~120x120 so this is ~300 points


def sample_ct(patch_dir, ct, every=EVERY):
    x = tifffile.imread(os.path.join(patch_dir, "x.tif"))
    y = tifffile.imread(os.path.join(patch_dir, "y.tif"))
    z = tifffile.imread(os.path.join(patch_dir, "z.tif"))
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (x > 0) & (y > 0) & (z > 0)
    sel = np.zeros_like(ok); sel[::every, ::every] = True
    ok &= sel
    if not ok.any():
        return None
    pz = (z[ok] / CT_SCALE).round().astype(int)
    py = (y[ok] / CT_SCALE).round().astype(int)
    px = (x[ok] / CT_SCALE).round().astype(int)
    v = np.asarray(ct.sample(np.stack([pz, py, px], axis=1)), float)
    return dict(n=int(v.size), median=float(np.median(v)), mean=float(v.mean()),
                frac_above_air=float((v > AIR_MAX).mean()), frac_zero=float((v == 0).mean()))


def recorded_coverage():
    """{(scroll, surface): measured papyrus coverage} from the screening reads."""
    out = {}
    for f in sorted(glob.glob(os.path.join(D, "patches", "*/*/read_*/read_stats.json"))):
        if f.split("/")[-2].replace("read_ink9um_seed42_", "") != "plain":
            continue
        j = json.load(open(f))
        ms, oc = j.get("map_shape"), j.get("onsheet_cm2")
        if not ms or not oc or not j.get("rule55"):
            continue
        um = j.get("um_per_px") or 9.362
        out[(f.split("/")[-4], f.split("/")[-3])] = oc / rule55.px_to_cm2(ms[0] * ms[1], um)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scroll", default="PHerc0826")
    ap.add_argument("--vol", default="20250821151701-9.362um-1.2m-113keV-masked.zarr")
    ap.add_argument("--every", type=int, default=EVERY)
    ap.add_argument("--out", default=os.path.join(D, "gates", "ggp", "coverage_proxy.json"))
    a = ap.parse_args()
    cov = recorded_coverage()
    ct = ChunkedCT("%s/%s/volumes/%s" % (BUCKET, a.scroll, a.vol), CT_LEVEL,
                   os.path.join(D, "ct_l4_cache", a.scroll))
    rows = []
    for (sc, su), c in sorted(cov.items()):
        if not sc.startswith(a.scroll):
            continue
        d = os.path.join(D, "patches", sc, su)
        if not os.path.isdir(d):
            continue
        s = sample_ct(d, ct, a.every)
        if s:
            s.update(scroll=sc, surface=su, measured_coverage=c)
            rows.append(s)
            print("%-22s %-38s ct_med %6.1f  frac>air %.3f  measured cover %.3f"
                  % (sc, su[:38], s["median"], s["frac_above_air"], c))
    if len(rows) >= 4:
        m = np.array([r["measured_coverage"] for r in rows])
        for k in ("median", "mean", "frac_above_air", "frac_zero"):
            v = np.array([r[k] for r in rows])
            print("  proxy %-16s vs measured coverage: Pearson r = %+.3f" % (k, np.corrcoef(v, m)[0, 1]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rows, open(a.out, "w"), indent=1, sort_keys=True)
    print("wrote %s (%d surfaces)" % (a.out, len(rows)))


if __name__ == "__main__":
    main()
