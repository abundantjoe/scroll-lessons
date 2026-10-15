#!/usr/bin/env python
"""RULES R-FLIP, applied RETROSPECTIVELY to reads made before the tripwire existed.

Rule 5.5 flags on a signed margin, and "forward" is a property of the SURFACE's normal. A mirrored surface carrying
ink puts its whole signal in the map we label "reverse", with a large negative margin, and the signed rule never sees
it. Every read from 2026-09-18 14:30 UTC on records the swapped evaluation itself; the reads before that do not.

Their stored maps and on-sheet mask are enough to compute it with NO inference: forward TIFF, reverse TIFF and
onsheet_mask.png are all kept beside read_stats.json. This adds `rule55_depth_swapped` and `depth_swap_tripwire` to
those stats files. It changes no verdict, no ledger line and no threshold: the ledger keeps the signed rule exactly as
frozen, and a firing tripwire obliges an orientation check in the geometry, not a new candidate.

usage: reflip_scan.py [--patches DIR] [--dry-run]
"""
import argparse, glob, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55, read_chart  # noqa: E402
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA


def maps_of(read_dir):
    """(forward, reverse, onsheet) for a finished read, or None if anything is missing."""
    fwd = [f for f in glob.glob(os.path.join(read_dir, "*.tif")) if not f.endswith("_reverse.tif")]
    rev = glob.glob(os.path.join(read_dir, "*_reverse.tif"))
    mask = os.path.join(read_dir, "onsheet_mask.png")
    if not (fwd and rev and os.path.exists(mask)):
        return None
    f, r = read_chart.load_map(fwd[0]), read_chart.load_map(rev[0])
    on = read_chart.load_mask(mask)
    if not (f.shape == r.shape == on.shape):
        return None
    return f, r, on


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patches", default=DATA + "/patches")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    done = skipped = fired = 0
    rows = []
    for sp in sorted(glob.glob(os.path.join(a.patches, "*", "*", "read_*", "read_stats.json"))):
        s = json.load(open(sp))
        if "rule55_depth_swapped" in s:
            skipped += 1; continue
        m = maps_of(os.path.dirname(sp))
        if m is None:
            skipped += 1; continue
        f, r, on = m
        um = s.get("um_per_px")
        swapped = rule55.evaluate(r, f, on, um, row_check=False,
                                  unit_origin=(s.get("rule55") or {}).get("unit_origin", "auto"))[0]
        n_flag = swapped["units"]["0.5cm2"]["n_flagged"]
        s["rule55_depth_swapped"] = swapped["units"]
        s["depth_swap_tripwire"] = bool(n_flag)
        s["depth_swap_note"] = ("RULES R-FLIP, computed retrospectively from the stored maps; the ledger verdict is the "
                                "signed rule and is unchanged")
        if not a.dry_run:
            json.dump(s, open(sp, "w"), indent=1)
        done += 1
        if n_flag:
            fired += 1
            rows.append((s["key"], n_flag, swapped["units"]["0.5cm2"]["largest_cluster"], swapped["verdict"]))
    print(f"retrospective R-FLIP: {done} reads evaluated, {skipped} skipped (no maps on disk or already done), "
          f"{fired} tripwire firing(s)")
    for k, n, c, v in rows:
        print(f"  TRIPWIRE {k}: {n} flagged unit(s), largest cluster {c}, swapped verdict {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
