#!/usr/bin/env python
"""RULES G-GP part 5b: decide from the MEASUREMENTS, never from the area, whether the threshold-4 consensus is read.

Bars, copied from the declaration and not tunable here:
  transverse self-intersections <= 1.42 per cm^2   (the w040 known-text control's own measured rate)
  p90 sag                       <= 9.93 um         (the w040 known-text control's own, at matched baseline)
Exit 0 = ADMITTED for reading. Exit 1 = area bought at the cost of geometry; recorded, not read.
"""
import argparse, glob, json, os, sys

MAX_CROSS_PER_CM2, MAX_P90_SAG_UM = 1.42, 9.93
D = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")


def crossings(pop, areas):
    """Worst PER-SURFACE transverse rate in the population, in sites per cm^2.

    Per surface, not pooled: a consensus build's mesh record also holds its companion patches, and pooling their
    areas would divide one surface's crossings by the whole batch's area and make the bar six times more lenient
    than it reads. The sag bar already takes the worst surface; this matches it.

    A report's `census` holds one entry per quad triangulation; the count that counts is the MINIMUM over the two,
    which is what R-CROSS used throughout. `areas` maps patch basename -> cm^2.
    """
    worst, worst_name, per = None, None, []
    for f in sorted(glob.glob(os.path.join(D, "gates", "rcross", pop, "*.json"))):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        cen = r.get("census") or []
        if not cen:
            continue
        name = os.path.basename(r.get("surface", f)).replace(".json", "")
        a = areas.get(name)
        sites = min(int(c.get("transverse", 0)) for c in cen)
        if not a:
            per.append((name, sites, None, None)); continue
        rate = sites / float(a)
        per.append((name, sites, a, rate))
        if worst is None or rate > worst:
            worst, worst_name = rate, name
    return worst, worst_name, per


def mesh_areas(part):
    """patch basename -> cm^2, from mesh_distortion's own rows (nodes x spacing^2). Available immediately after the
    build, before any render exists, which is when this gate has to decide."""
    f = os.path.join(D, "gates", "ggp", "part%s_consensus_mesh.json" % part)
    if not os.path.exists(f):
        return {}
    return {r["patch"]: float(r["area_cm2"]) for r in (json.load(open(f)).get("rows") or [])
            if r.get("patch") and r.get("area_cm2")}


def sag(part):
    f = os.path.join(D, "gates", "ggp", "part%s_consensus_mesh.json" % part)
    if not os.path.exists(f):
        return None
    m = json.load(open(f))
    # mesh_distortion.py writes one row per surface with sag_um_p90, plus a pooled p90-of-p90 over the batch.
    # The bar is on the surface, so the worst surface in the batch decides; the pooled value is the fallback.
    vals = [r["sag_um_p90"] for r in (m.get("rows") or []) if r.get("sag_um_p90") is not None]
    if vals:
        return max(vals)
    return None if m.get("pooled_sag_um_p90") is None else float(m["pooled_sag_um_p90"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="5b")
    ap.add_argument("--pop", default=None, help="rcross population name (default cons_part<part>)")
    a = ap.parse_args()
    pop = a.pop or ("cons_part%s" % a.part)
    areas = mesh_areas(a.part)
    x, worst_name, per = crossings(pop, areas)
    s = sag(a.part)
    print("G-GP part %s geometry, against the w040 known-text control's own rates (worst surface decides):" % a.part)
    for name, sites, ar, rate in per:
        print("    %-52s %3d sites over %s cm2 -> %s per cm2"
              % (name[:52], sites, "   n/a" if ar is None else "%6.2f" % ar,
                 "  n/a" if rate is None else "%5.2f" % rate))
    print("  worst transverse rate %s per cm2 (%s)   (bar <= %.2f)"
          % ("unmeasured" if x is None else "%.2f" % x, worst_name or "-", MAX_CROSS_PER_CM2))
    print("  p90 sag                       %s um        (bar <= %.2f)"
          % ("unmeasured" if s is None else "%.2f" % s, MAX_P90_SAG_UM))
    if x is None or s is None:
        print("VERDICT: NOT ADMITTED - a bar could not be measured, so it is not met."); return 1
    ok = (x <= MAX_CROSS_PER_CM2) and (s <= MAX_P90_SAG_UM)
    print("VERDICT: %s" % ("ADMITTED for reading - the area is earned" if ok else
                           "NOT ADMITTED - area bought at the cost of geometry; recorded, not read"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
