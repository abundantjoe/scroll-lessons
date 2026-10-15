#!/usr/bin/env python
"""RULES R-CROSS scorer: pool vc_tifxyz_selfcross reports per population and answer the declared bar.

The tool censuses both quad triangulations ("diagonals"). The triangulation is arbitrary, so the HEADLINE count
here is the MINIMUM over the two -- the conservative reading, a contact that survives either way of cutting the
quads. Both are reported. That is a stricter choice than taking the max and is stated rather than assumed.
"""
import argparse, glob, gzip, json, os, sys
import numpy as np
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

G = DATA + "/gates/rcross"
AREA_SRC = [DATA + "/gates/ggp/ours_autogrown.json",
            DATA + "/gates/ggp/refB_team.json",
            DATA + "/gates/ggp/refA_w040.json"]


def areas():
    out = {}
    for p in AREA_SRC:
        try:
            for r in json.load(open(p))["rows"]:
                if r.get("area_cm2"):
                    out[r["patch"]] = r["area_cm2"]
        except Exception:
            pass
    return out


def read_report(f):
    """A census report, plain or gzipped. The reports are bulky (533 MB over the corpus) and get compressed to keep
    this box's disk above its floor; a scorer that silently skipped the compressed ones would shrink the population
    without saying so -- which is exactly what happened once on 2026-09-18 and overwrote rcross.json with a partial
    result."""
    if f.endswith(".gz"):
        with gzip.open(f, "rt") as fh:
            return json.load(fh)
    return json.load(open(f))


def load_pop(pop, area_by_patch):
    rows = []
    files = sorted(glob.glob(os.path.join(G, pop, "*.json")) + glob.glob(os.path.join(G, pop, "*.json.gz")))
    for f in files:
        if os.path.basename(f).split(".json")[0] == "summary":
            continue
        try:
            d = read_report(f)
        except Exception as e:
            print("  unreadable report %s: %s" % (os.path.basename(f), e)); continue
        cen = d.get("census") or []
        tv = [int(c.get("transverse", 0)) for c in cen] or [0]
        patch = os.path.basename(f).split(".json")[0].split("__")[-1]
        a = area_by_patch.get(patch)
        rows.append(dict(name=os.path.basename(f).split(".json")[0], patch=patch, area_cm2=a,
                         transverse_min=min(tv), transverse_max=max(tv),
                         clean=bool(d.get("clean_of_transverse_self_intersection")),
                         per_cm2=(min(tv) / a) if a else None,
                         triangles=int(cen[0].get("triangles", 0)) if cen else 0,
                         quads_dropped=int(cen[0].get("quads_dropped_for_edge_length", 0)) if cen else 0))
    return rows


def describe(pop, rows):
    if not rows:
        print("  %-10s no reports" % pop); return {}
    tv = np.array([r["transverse_min"] for r in rows], float)
    pc = np.array([r["per_cm2"] for r in rows if r["per_cm2"] is not None], float)
    frac = float((tv > 0).mean())
    s = dict(population=pop, n=len(rows), frac_with_contact=round(frac, 4),
             median_transverse_min=float(np.median(tv)), max_transverse_min=float(tv.max()),
             median_per_cm2=round(float(np.median(pc)), 3) if pc.size else None,
             p90_per_cm2=round(float(np.percentile(pc, 90)), 3) if pc.size else None)
    print("  %-10s n=%-4d  with a transverse contact: %5.1f %%   median sites %6.0f   median /cm2 %s   p90 /cm2 %s"
          % (pop, len(rows), 100 * frac, np.median(tv),
             "-" if s["median_per_cm2"] is None else "%8.2f" % s["median_per_cm2"],
             "-" if s["p90_per_cm2"] is None else "%8.2f" % s["p90_per_cm2"]))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--populations", nargs="+", default=["control", "team", "ours"])
    a = ap.parse_args()
    abp = areas()
    print("RULES R-CROSS: transverse self-intersection census (vc_tifxyz_selfcross, report-only)")
    print("  headline count = MINIMUM over the two quad triangulations (the conservative reading)")
    out, pops = {}, {}
    for p in a.populations:
        rows = load_pop(p, abp)
        pops[p] = rows
        out[p] = describe(p, rows)
    ctl = pops.get("control") or []
    if ctl:
        print("  CONTROL FIRST, as declared: the w040 known-text mesh has %d transverse sites (min over diagonals), "
              "%d (max)." % (ctl[0]["transverse_min"], ctl[0]["transverse_max"]))
        print("      %s" % ("A known-good, known-text sheet DOES self-cross, so a contact is tolerable in a readable "
                            "surface and the physical argument for this measure is weaker than it looks."
                            if ctl[0]["transverse_min"] > 0 else
                            "The known-good sheet is clean, so a contact is not something a readable surface carries."))
    json.dump(dict(summary=out, rows={p: pops[p] for p in pops}), open(os.path.join(G, "rcross.json"), "w"), indent=1)
    print("  written %s (the outcome split against the declared 2x bar is scored separately once every population is in)"
          % os.path.join(G, "rcross.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
