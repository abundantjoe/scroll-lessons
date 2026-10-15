#!/usr/bin/env python
"""RULES R-SMALL: pick the INTERIOR seeds of a scroll's seed file, by the same radial measure as R-RADIAL.

A seed is interior when its radial position between the scroll axis and the outer edge of the scanned material at the
same z lies in [--lo, --hi]. Axis and edge are taken exactly as radial_position.py takes them: the published umbilicus
where the volume has one, otherwise the level-4 CT mask centroid; edge = the 99th percentile mask radius at that z.

usage: interior_seeds.py --scroll PHerc0826 [--seeds seeds/PHerc0826.json] [--lo 0.20] [--hi 0.55] [--out FILE]
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import radial_position as RP
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scroll", required=True)
    ap.add_argument("--seeds"); ap.add_argument("--lo", type=float, default=0.20); ap.add_argument("--hi", type=float, default=0.55)
    ap.add_argument("--out"); ap.add_argument("--cache")
    a = ap.parse_args(argv)
    seeds_path = a.seeds or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seeds", f"{a.scroll}.json")
    d = json.load(open(seeds_path))
    um = RP.umbilicus(a.scroll)
    mask = RP.L4Mask(a.scroll, a.cache or f"{DATA}/ct_l4_cache/{a.scroll}")
    out = []
    for s in d["seeds"]:
        if s.get("skip"):
            continue
        zi = int(round(s["z"] / RP.CT_SCALE))
        st = mask.at(zi)
        if st is None:
            continue
        if um is not None:
            cx, cy = RP.axis_at(um, np.array([float(s["z"])]))[0] / RP.CT_SCALE
        else:
            cx, cy = st[0], st[1]
        r = float(np.hypot(s["x"] / RP.CT_SCALE - cx, s["y"] / RP.CT_SCALE - cy) / st[2])
        if a.lo <= r <= a.hi:
            out.append(dict(x=s["x"], y=s["y"], z=s["z"], r_over_R=round(r, 4)))
    out.sort(key=lambda s: s["r_over_R"])
    print(f"{a.scroll}: {len(out)} of {len(d['seeds'])} seeds are interior (r/R in [{a.lo}, {a.hi}])", file=sys.stderr)
    if a.out:
        json.dump(dict(scroll=a.scroll, source=seeds_path, band=[a.lo, a.hi],
                       note="RULES R-SMALL: interior seeds, to be traced at a reduced growth budget", seeds=out),
                  open(a.out, "w"), indent=1)
    for s in out:
        print(s["x"], s["y"], s["z"], s["r_over_R"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
