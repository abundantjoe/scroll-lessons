#!/usr/bin/env python
"""Where in the scroll are the surfaces we have actually read?

The seeds are ordered outer -> middle -> inner and the density gate (RULES, seeds density gate) prefers sparse
prediction neighbourhoods, which sit nearer the scroll edge. Both push coverage OUTWARD, and the outer wraps of a
Herculaneum scroll are the most damaged and the least likely to carry legible text. This measures the bias instead of
assuming it: for every read surface, the radial position of its points between the scroll axis and the outer edge of
the scanned material at the same z.

Axis: the published `representations/umbilicus/*.json` control points when the volume has one (linear interpolation in
z), otherwise the centroid of the level-4 CT mask at that z. Outer edge: the 99th percentile radius of that mask's
pixels at the same z, so one stray voxel cannot set the scale. Reported as r/R in [0, 1]: 0 at the axis, 1 at the edge.

usage: radial_position.py --scroll PHerc0826 [--patches DIR] [--out JSON]
"""
import argparse, glob, json, os, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import numpy as np, tifffile
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
CT_LEVEL, CT_SCALE = 4, 16


def umbilicus(scroll):
    """{z: (x, y)} control points of the published scroll axis, or None."""
    q = {"list-type": "2", "prefix": f"{scroll}/representations/umbilicus/", "max-keys": "100"}
    with urllib.request.urlopen(f"{BUCKET}/?{urllib.parse.urlencode(q)}", timeout=120) as r:
        root = ET.fromstring(r.read())
    keys = [c.findtext(NS + "Key") for c in root.findall(NS + "Contents") if c.findtext(NS + "Key").endswith(".json")]
    if not keys:
        return None
    with urllib.request.urlopen(f"{BUCKET}/{urllib.parse.quote(sorted(keys)[-1])}", timeout=120) as r:
        j = json.load(r)
    pts = sorted(((p["z"], p["x"], p["y"]) for p in j["control_points"]))
    return np.array([p[0] for p in pts], float), np.array([[p[1], p[2]] for p in pts], float)


def axis_at(um, z):
    """Linear interpolation of the axis at level-0 z."""
    zs, xy = um
    return np.stack([np.interp(z, zs, xy[:, 0]), np.interp(z, zs, xy[:, 1])], -1)


class L4Mask:
    """Level-4 CT mask slices, cached: centroid and 99th-percentile radius per z."""

    def __init__(self, scroll, cache):
        self.cache = cache
        import patch_qc
        self.ct = patch_qc.ChunkedCT(self._url(scroll), CT_LEVEL, cache)
        self.stats = {}

    @staticmethod
    def _url(scroll):
        q = {"list-type": "2", "prefix": f"{scroll}/volumes/", "delimiter": "/", "max-keys": "100"}
        with urllib.request.urlopen(f"{BUCKET}/?{urllib.parse.urlencode(q)}", timeout=120) as r:
            root = ET.fromstring(r.read())
        dirs = [c.findtext(NS + "Prefix") for c in root.findall(NS + "CommonPrefixes") if "masked.zarr" in c.findtext(NS + "Prefix")]
        return f"{BUCKET}/{sorted(dirs)[-1].rstrip('/')}"

    def at(self, zi):
        if zi not in self.stats:
            s = self.ct.slice(int(zi))
            yy, xx = np.nonzero(s > 0)
            if len(xx) < 100:
                self.stats[zi] = None
            else:
                cx, cy = xx.mean(), yy.mean()
                r = np.hypot(xx - cx, yy - cy)
                self.stats[zi] = (cx, cy, float(np.percentile(r, 99)))
        return self.stats[zi]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scroll", required=True)
    ap.add_argument("--patches", default=DATA + "/patches")
    ap.add_argument("--cache", default=None); ap.add_argument("--out")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    cache = a.cache or f"{DATA}/ct_l4_cache/{a.scroll}"
    um = umbilicus(a.scroll)
    mask = L4Mask(a.scroll, cache)
    rows = []
    for sp in sorted(glob.glob(os.path.join(a.patches, a.scroll, "*", "read_*", "read_stats.json"))):
        d = os.path.dirname(os.path.dirname(sp))
        s = json.load(open(sp))
        try:
            x, y, z = [tifffile.imread(os.path.join(d, f"{c}.tif")).astype(np.float64) for c in "xyz"]
        except Exception:
            continue
        v = (x > -1) & (y > -1) & (z > -1)
        if v.sum() < 100:
            continue
        px, py, pz = x[v][::17], y[v][::17], z[v][::17]
        zi = np.rint(pz / CT_SCALE).astype(int)
        rr = []
        for zz in np.unique(zi):
            st = mask.at(zz)
            if st is None:
                continue
            sel = zi == zz
            if um is not None:
                c = axis_at(um, pz[sel]) / CT_SCALE
                cx, cy = c[:, 0], c[:, 1]
            else:
                cx, cy = st[0], st[1]
            r = np.hypot(px[sel] / CT_SCALE - cx, py[sel] / CT_SCALE - cy)
            rr.append(r / st[2])
        if not rr:
            continue
        rr = np.concatenate(rr)
        cc = s.get("crest_check") or {}
        rows.append(dict(key=s["key"], patch=os.path.basename(d), verdict=s.get("verdict"),
                         crest=cc.get("ratio"), onsheet_cm2=s.get("onsheet_cm2"),
                         r_over_R_median=round(float(np.median(rr)), 4),
                         r_over_R_p05=round(float(np.percentile(rr, 5)), 4),
                         r_over_R_p95=round(float(np.percentile(rr, 95)), 4)))
    out = dict(scroll=a.scroll, axis="published umbilicus" if um is not None else "level-4 CT mask centroid",
               n_reads=len(rows), reads=rows)
    if rows:
        med = [r["r_over_R_median"] for r in rows]
        out["summary"] = dict(median_of_medians=round(float(np.median(med)), 4),
                              min=round(min(med), 4), max=round(max(med), 4),
                              frac_outer_half=round(float(np.mean([m > 0.5 for m in med])), 4),
                              frac_outer_quarter=round(float(np.mean([m > 0.75 for m in med])), 4))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out.get("summary", {}), indent=1))
    for r in sorted(rows, key=lambda r: r["r_over_R_median"]):
        print(f"  {r['r_over_R_median']:.3f} [{r['r_over_R_p05']:.2f}-{r['r_over_R_p95']:.2f}]  "
              f"{r['patch'][:34]:34} crest {r['crest'] if r['crest'] is not None else float('nan'):5.2f}  {str(r['verdict'])[:18]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
