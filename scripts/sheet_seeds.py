#!/usr/bin/env python
"""RULES G-GP part 4: seeds sampled from ONE patch's own surface points, so every trace starts on the same sheet.

The existing seeder (seeds.py) places seeds >= 320 level-0 voxels apart on a 3D grid. The wrap spacing R-INTERIOR
measured is 48 voxels, so two such seeds can be six wraps apart and their traces never agree on a sheet. Seeding from
a patch's own valid grid points removes that failure by construction: every seed is a point the source surface passes
through.

Spread is enforced in GRID INDEX, not in 3D, because grid index is the sheet's own coordinate -- a minimum 3D
separation would again allow two seeds on different wraps that happen to be far apart in space.

usage: sheet_seeds.py <tifxyz dir> --count 25 [--json out.json]
"""
import argparse, json, os, sys
import numpy as np, tifffile


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patch")
    ap.add_argument("--count", type=int, default=25)
    ap.add_argument("--edge-margin", type=int, default=6,
                    help="grid nodes to stay clear of the patch border, where the surface is least supported")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    P = np.stack([tifffile.imread(os.path.join(a.patch, n + ".tif")).astype(np.float64) for n in "xyz"], -1)
    valid = np.isfinite(P).all(-1) & (P > 0).all(-1)
    m = a.edge_margin
    if m:
        inner = np.zeros_like(valid)
        inner[m:-m or None, m:-m or None] = True
        valid = valid & inner
    rc = np.argwhere(valid)
    if rc.size == 0:
        sys.exit("no valid interior grid points in " + a.patch)
    # A farthest-point pass in GRID INDEX: deterministic (starts at the valid node nearest the grid centre),
    # and it spreads the seeds over the patch instead of clustering them where the grid is dense.
    centre = rc.mean(0)
    order = [int(np.argmin(((rc - centre) ** 2).sum(1)))]
    d = ((rc - rc[order[0]]) ** 2).sum(1).astype(float)
    while len(order) < min(a.count, len(rc)):
        j = int(np.argmax(d))
        order.append(j)
        d = np.minimum(d, ((rc - rc[j]) ** 2).sum(1))
    seeds = []
    for j in order:
        r, c = rc[j]
        x, y, z = P[r, c]
        seeds.append(dict(row=int(r), col=int(c), x=int(round(x)), y=int(round(y)), z=int(round(z))))
    sep = float(np.sqrt(min(((np.array([[s["row"], s["col"]] for s in seeds])[:, None]
                             - np.array([[s["row"], s["col"]] for s in seeds])[None]) ** 2).sum(-1)
                           [np.triu_indices(len(seeds), 1)]))) if len(seeds) > 1 else float("nan")
    out = dict(source_patch=a.patch, grid_shape=[int(P.shape[0]), int(P.shape[1])],
               n_valid_interior=int(len(rc)), count=len(seeds), min_grid_separation=round(sep, 1), seeds=seeds)
    print("%d seeds from %s (grid %dx%d, %d valid interior nodes, min grid separation %.1f)"
          % (len(seeds), os.path.basename(a.patch.rstrip("/")), P.shape[0], P.shape[1], len(rc), sep))
    for s in seeds:
        print("  %5d %5d   %6d %6d %6d" % (s["row"], s["col"], s["x"], s["y"], s["z"]))
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
