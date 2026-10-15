#!/usr/bin/env python
"""cluster_power.py -- could our canvas form a rule-5.5 candidate at all, even if it were as inked as the control?

Rule 5.5 needs THREE 4-connected flagged 0.5 cm2 units.  R-DEFICIT's cluster arithmetic used the control's cluster
DENSITY (one per 71 valid units), which silently assumes our units are laid out like the control's single large
contiguous grid.  They are not: our surfaces are small and their valid units are scattered.  This computes the
expectation from the ACTUAL per-surface layouts instead.

Method (no threshold is chosen here, so there is nothing to pre-register): reconstruct each surface's valid-unit
occupancy grid from its recorded rule 5.5 table, flag each valid unit independently with the control's own measured
rate p = 7/71, and count 4-connected flagged triples.  Monte Carlo, fixed seed (the --read-stats mode prints the
binomial standard error of each estimate; the corpus mode records trials and seed, from which it follows).

usage: cluster_power.py --read-stats <read_stats.json> [...] [--p 0.0986] [--trials 20000]   (score given reads)
       cluster_power.py [--out cluster_power.json]          (every read under $HERCULES_DATA/patches)
"""
import argparse, glob, json, os, sys
import numpy as np
from scipy import ndimage
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

P_CONTROL = 7.0 / 71.0
TRIALS = 20000
SEED = 20260919


def dedupe_consensus(out):
    """Drop a consensus build's SECOND output: auto_grown_* and auto_trace_* of one vc_grow_seg_from_segments run are
    ONE surface written twice (same grid, same valid-node count, identical read statistics), and counting both
    inflates the canvas.  Only collapses within a single *_cons_part* directory and only when the unit layouts are
    identical, so two genuinely different surfaces are never merged."""
    seen, keep = {}, {}
    for (sc, su), g in sorted(out.items()):
        if "_cons_part" not in sc:
            keep[(sc, su)] = g
            continue
        fp = (sc, g.shape, int(g.sum()), g.tobytes())
        if fp in seen:
            continue                      # same build, same layout: already counted
        seen[fp] = (sc, su)
        keep[(sc, su)] = g
    return keep


def layouts(root=DATA + "/patches", recipe="plain"):
    """(scroll, surface, occupancy grid of VALID units) for every unique surface read on the screening recipe.

    A consensus build's two outputs are collapsed to one (see dedupe_consensus)."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "*/*/read_*/read_stats.json"))):
        if f.split("/")[-2].replace("read_ink9um_seed42_", "") != recipe:
            continue
        g = grid_from_read_stats(json.load(open(f)))
        if g is None:
            continue
        out[(f.split("/")[-4], f.split("/")[-3])] = g
    return dedupe_consensus(out)


def grid_from_read_stats(j):
    """Occupancy grid of the VALID 0.5 cm2 units recorded in one read_stats.json (read_chart.py output), or None.

    The forward table's per-unit rows are used; where they are empty (41 of 50 older reads) the depth-swapped table's
    rows are used, which tile the same grid.  If neither survived, a contiguous block of n_valid units stands in."""
    r = j.get("rule55"); sw = j.get("rule55_depth_swapped")
    if not r:
        return None
    t = (r.get("units") or r)["0.5cm2"]
    if not t.get("n_valid"):
        return None
    units = t.get("valid_units") or ((sw or {}).get("0.5cm2", {}).get("valid_units") or [])
    g = np.zeros((int(t["grid_rows"]), int(t["grid_cols"])), bool)
    if units:
        for u in units:
            g[int(u["row"]), int(u["col"])] = True
    else:                       # no per-unit rows survived: fall back to a contiguous block of n_valid units
        g.flat[:int(t["n_valid"])] = True
    if int(g.sum()) != int(t["n_valid"]):
        g = np.zeros_like(g); g.flat[:int(t["n_valid"])] = True
    return g


def p_triple(grid, p=P_CONTROL, trials=TRIALS, rng=None):
    """P(the surface yields at least one 4-connected flagged triple) under independent per-unit flagging."""
    rng = rng or np.random.default_rng(SEED)
    n = int(grid.sum())
    if n < 3:
        return 0.0                              # cannot hold three units, whatever the rate
    hits = 0
    idx = np.nonzero(grid)
    for _ in range(trials):
        f = np.zeros(grid.shape, bool)
        f[idx] = rng.random(n) < p
        if f.sum() < 3:
            continue
        lab, k = ndimage.label(f)
        if k and np.bincount(lab.ravel())[1:].max() >= 3:
            hits += 1
    return hits / float(trials)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, default=P_CONTROL)
    ap.add_argument("--trials", type=int, default=TRIALS)
    ap.add_argument("--out", default=DATA + "/gates/cluster_power.json")
    ap.add_argument("--read-stats", nargs="+", metavar="READ_STATS_JSON",
                    help="score these read_stats.json files only (prints P(>= 1 triple) per read; writes nothing)")
    a = ap.parse_args(argv)
    if a.read_stats:
        total = 0.0
        for f in a.read_stats:
            g = grid_from_read_stats(json.load(open(f)))
            pt = 0.0 if g is None else p_triple(g, a.p, a.trials, np.random.default_rng(SEED))
            total += pt
            se = (pt * (1 - pt) / a.trials) ** 0.5
            print("%s  grid %s  valid units %d  P(>= 1 4-connected flagged triple at p=%.4f) = %.4f (Monte Carlo, %d trials, SE %.4f)"
                  % (f, "-" if g is None else "%dx%d" % g.shape, 0 if g is None else int(g.sum()), a.p, pt, a.trials, se))
        print("expected candidates over %d read(s): %.4f" % (len(a.read_stats), total))
        return 0
    L = layouts(); rng = np.random.default_rng(SEED)
    rows = []
    for (sc, su), g in L.items():
        rows.append(dict(scroll=sc, surface=su, grid=list(g.shape), n_valid=int(g.sum()),
                         p_triple=p_triple(g, a.p, a.trials, rng)))
    exp = sum(r["p_triple"] for r in rows)
    nv = sum(r["n_valid"] for r in rows)
    small = sum(1 for r in rows if r["n_valid"] < 3)
    out = dict(p_flag=a.p, trials=a.trials, seed=SEED, n_surfaces=len(rows), n_valid_units=nv,
               expected_candidates=exp, n_surfaces_too_small_to_hold_a_triple=small, rows=rows)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
    print("surfaces %d ; valid units %d (%.2f cm2) ; per-unit flag rate used %.4f (the control's own 7/71)"
          % (len(rows), nv, nv * 0.5, a.p))
    print("surfaces that cannot hold a 4-connected triple at all (fewer than 3 valid units): %d" % small)
    print("EXPECTED candidates from this canvas if it were as inked as the control: %.3f" % exp)
    print("  (R-DEFICIT's density-based figure, which assumed one large contiguous grid, was 1.59)")
    for r in sorted(rows, key=lambda z: -z["p_triple"])[:8]:
        print("   %-22s %-38s grid %sx%s  valid %2d  P(triple) %.4f"
              % (r["scroll"], r["surface"][:38], r["grid"][0], r["grid"][1], r["n_valid"], r["p_triple"]))
    print("wrote", a.out)


if __name__ == "__main__":
    sys.exit(main())
