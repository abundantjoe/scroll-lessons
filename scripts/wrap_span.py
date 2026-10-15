#!/usr/bin/env python
"""RULES R-WRAP: how many wraps does a trace span radially?

R-CREST measures sheet-holding through a papyrus-to-gap density contrast, which a fully compressed interior does not
have — a trace there can hold to one sheet perfectly and still render flat. This measures sheet-holding directly.

For every valid grid point, the radial coordinate about the scroll axis (the published umbilicus where the volume has
one, otherwise the level-4 CT mask centroid at that z — the same axis radial_position.py uses). The 5th-to-95th
percentile spread of that radius, divided by the wrap spacing the CT's own autocorrelation shows, is `wrap_span`:
below about 1 means the surface stays inside one wrap, several means it steps across wraps.

usage: wrap_span.py PATCH_DIR --scroll PHerc0826 [--spacing-vx 48] [--out JSON]
  spacing-vx: wrap spacing in LEVEL-0 voxels; 48 for PHerc0826 (R-INTERIOR: 24 level-1 voxels = 449 um at 9.362 um).
"""
import argparse, json, os, sys
import numpy as np, tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import radial_position as RP
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA


def wrap_span(patch_dir, scroll, spacing_vx, cache=None, every=7):
    x, y, z = [tifffile.imread(os.path.join(patch_dir, f"{c}.tif")).astype(np.float64) for c in "xyz"]
    v = (x > -1) & (y > -1) & (z > -1)
    if v.sum() < 100:
        return dict(patch=os.path.abspath(patch_dir), scroll=scroll, n_points=int(v.sum()), wrap_span=None,
                    note="fewer than 100 valid grid points")
    px, py, pz = x[v][::every], y[v][::every], z[v][::every]
    um = RP.umbilicus(scroll)
    mask = RP.L4Mask(scroll, cache or f"{DATA}/ct_l4_cache/{scroll}")
    r = np.full(px.shape, np.nan)
    zi = np.rint(pz / RP.CT_SCALE).astype(int)
    for zz in np.unique(zi):
        sel = zi == zz
        if um is not None:
            c = RP.axis_at(um, pz[sel])
            cx, cy = c[:, 0], c[:, 1]
        else:
            st = mask.at(int(zz))
            if st is None:
                continue
            cx, cy = st[0] * RP.CT_SCALE, st[1] * RP.CT_SCALE
        r[sel] = np.hypot(px[sel] - cx, py[sel] - cy)
    r = r[np.isfinite(r)]
    if r.size < 100:
        return dict(patch=os.path.abspath(patch_dir), scroll=scroll, n_points=int(r.size), wrap_span=None,
                    note="fewer than 100 points with a usable axis")
    lo, hi = np.percentile(r, 5), np.percentile(r, 95)
    return dict(patch=os.path.abspath(patch_dir), scroll=scroll, n_points=int(r.size),
                axis="published umbilicus" if um is not None else "level-4 CT mask centroid",
                spacing_vx=spacing_vx, r_p05_vx=round(float(lo), 2), r_p95_vx=round(float(hi), 2),
                r_median_vx=round(float(np.median(r)), 2),
                span_vx=round(float(hi - lo), 2), wrap_span=round(float((hi - lo) / spacing_vx), 3))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patch_dir"); ap.add_argument("--scroll", required=True)
    ap.add_argument("--spacing-vx", type=float, default=48.0)
    ap.add_argument("--every", type=int, default=7); ap.add_argument("--cache"); ap.add_argument("--out")
    a = ap.parse_args(argv)
    r = wrap_span(a.patch_dir, a.scroll, a.spacing_vx, a.cache, a.every)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(r, open(a.out, "w"), indent=1)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
