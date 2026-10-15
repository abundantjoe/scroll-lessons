#!/usr/bin/env python
"""RULES G-GP part 3: how much surface do N of our patches agree on?

vc_grow_seg_from_segments accepts a point only where `consensus_default_th` source patches agree (the team publish 6;
the engine default is 10). That is a PRECONDITION on the patch library, and it is measurable with no download and no
tracing: voxelise every patch's valid points at a cell half the measured wrap spacing and count DISTINCT patches per
cell.

The cell is a deliberate over-count -- two patches in one 225 um cell could in principle sit on adjacent wraps where
the local spacing is tighter than the 449 um R-INTERIOR measured -- so the agreeing area reported here is an UPPER
BOUND. A conclusion that the library does not support a threshold is therefore stronger than the number looks.

usage: patch_agreement.py --scrolls PHerc0826 PHerc0358 [--cell 24] [--um 9.362] [--json out.json]
"""
import argparse, glob, json, os, sys
from collections import defaultdict
import numpy as np, tifffile
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA


def patch_points(d):
    P = np.stack([tifffile.imread(os.path.join(d, n + ".tif")).astype(np.float64) for n in "xyz"], -1)
    v = np.isfinite(P).all(-1) & (P > 0).all(-1)
    return P[v]


def identity(d):
    """What counts as ONE independent patch.

    Two traces grown from the SAME seed are the same observation twice: they would inflate the consensus count
    without adding any independent support, and duplicates do occur (a loop restarted over an in-flight trace on
    2026-09-18 produced two traces of one seed before it was stopped). So patches are keyed by their seed when they
    have a real one. The team's published segments all record seed [0, 0, 0], which is a placeholder rather than a
    shared origin, so a zero or missing seed falls back to the directory -- never collapsing distinct segments.
    """
    try:
        seed = json.load(open(os.path.join(d, "meta.json"))).get("seed")
    except Exception:
        seed = None
    if seed and any(float(v) != 0.0 for v in seed):
        return ("seed",) + tuple(round(float(v), 3) for v in seed)
    return ("dir", os.path.abspath(d).rstrip("/"))


def agreement(dirs, cell):
    occ = defaultdict(set)
    seen = {}
    for d in dirs:
        key = identity(d)
        if key in seen:
            continue                       # a duplicate trace of the same seed is one observation, not two
        try:
            Q = patch_points(d)
        except Exception:
            continue
        if not Q.size:
            continue
        seen[key] = d
        for c in set(map(tuple, np.floor(Q / cell).astype(np.int64))):
            occ[c].add(key)
    return occ, len(seen)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scrolls", nargs="*", default=[])
    ap.add_argument("--dirs", nargs="*", default=[],
                    help="explicit tifxyz dirs or parents of them, instead of (or as well as) --scrolls")
    ap.add_argument("--label", default="", help="name for an explicit --dirs population")
    ap.add_argument("--curve", action="store_true",
                    help="RULES G-GP part 4: agreeing area at each threshold as a function of how many patches are "
                         "included, in the order given. The deliverable whether the campaign passes or fails.")
    ap.add_argument("--patches", default=DATA + "/patches")
    ap.add_argument("--cell", type=float, default=24.0, help="level-0 voxels; default half the 449 um wrap spacing")
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--thresholds", nargs="+", type=int, default=[2, 3, 4, 6, 10])
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    out = {}
    cell_cm2 = (a.cell * a.um * 1e-4) ** 2
    # *_cons holds consensus surfaces GROWN FROM these patches, so counting them as sources would feed a surface's
    # own derivative back in as independent support for it. They are excluded by name, and the exclusion is listed.
    def sources(sc):
        out = []
        for m in sorted(glob.glob(os.path.join(a.patches, sc + "*", "auto_*", "meta.json"))):
            d = os.path.dirname(m)
            parent = os.path.basename(os.path.dirname(d))
            if parent.endswith("_cons") or not os.path.basename(d).startswith("auto_grown_"):
                continue
            out.append(d)
        return out
    populations = [(sc, sources(sc)) for sc in a.scrolls]
    if a.dirs:
        expanded = []
        for d in a.dirs:
            if os.path.exists(os.path.join(d, "x.tif")):
                expanded.append(d.rstrip("/"))
            else:
                expanded += sorted(os.path.join(d, c) for c in os.listdir(d)
                                   if os.path.exists(os.path.join(d, c, "x.tif")))
        populations.append((a.label or "dirs", expanded))
    for sc, dirs in populations:
        if a.curve:
            print("%s: agreeing area (cm2, upper bound) as patches are added, in order" % sc)
            print("   %-5s %s" % ("n", "  ".join(">=%d" % t for t in a.thresholds)))
            for k in range(1, len(dirs) + 1):
                occ_k, _ = agreement(dirs[:k], a.cell)
                c_k = np.array([len(v) for v in occ_k.values()]) if occ_k else np.array([0])
                print("   %-5d %s" % (k, "  ".join("%6.2f" % ((c_k >= t).sum() * cell_cm2) for t in a.thresholds)))
        occ, used = agreement(dirs, a.cell)
        if not occ:
            print("%s: no patches" % sc); continue
        counts = np.array([len(s) for s in occ.values()])
        rec = dict(scroll=sc, n_patches=used, n_cells=len(occ), cell_vx=a.cell,
                   cell_cm2=round(cell_cm2, 6), max_agreeing=int(counts.max()), by_threshold={})
        print("%s: %d patches, %d occupied %.0f-voxel cells, max agreeing in one cell %d"
              % (sc, used, len(occ), a.cell, counts.max()))
        for th in a.thresholds:
            n = int((counts >= th).sum())
            rec["by_threshold"][str(th)] = dict(cells=n, area_cm2=round(n * cell_cm2, 3))
            print("   >= %2d patches agree: %7d cells  (%5.2f %%)  upper-bound area %6.2f cm2"
                  % (th, n, 100 * n / len(occ), n * cell_cm2))
        out[sc] = rec
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
