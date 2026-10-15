#!/usr/bin/env python
"""RULES G-GP scorer: apply the declared parameterisation bar to our auto-grown traces.

Reference B is the team's own published segments. "Reference B's pooled 90th percentile" is the 90th percentile
OF the per-surface 90th percentiles -- the same quantity mesh_distortion.py prints as pooled_*_p90.
A trace is PARAMETERISATION-DEGRADED if its own anisotropy_p90 >= 2x Reference B's pooled anisotropy_p90,
OR its own sag_um_p90 >= 2x Reference B's pooled sag_um_p90.
"""
import json, os, sys
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

G = DATA + "/gates/ggp"
FACTOR = 2.0            # RULES G-GP: ">= 2x Reference B's pooled 90th percentile"
SHEET_UM = 150.0        # papyrus thickness, order of magnitude; reported, gates nothing
WRAP_UM = 449.0         # R-INTERIOR's measured wrap spacing; reported, gates nothing


def main():
    refA = json.load(open(os.path.join(G, "refA_w040.json")))
    refB = json.load(open(os.path.join(G, "refB_team.json")))
    ours = json.load(open(os.path.join(G, "ours_autogrown.json")))
    a_bar = refB["pooled_anisotropy_p90"] * FACTOR
    s_bar = refB["pooled_sag_um_p90"] * FACTOR
    deg = []
    for r in ours["rows"]:
        by_a = r["anisotropy_p90"] >= a_bar
        by_s = r["sag_um_p90"] is not None and r["sag_um_p90"] >= s_bar
        if by_a or by_s:
            deg.append(dict(patch=r["patch"], dir=r["dir"], anisotropy_p90=r["anisotropy_p90"],
                            sag_um_p90=r["sag_um_p90"], area_cm2=r["area_cm2"], max_gen=r["max_gen"],
                            by_anisotropy=bool(by_a), by_sag=bool(by_s)))
    ctl = refA["rows"][0]
    print("RULES G-GP: mesh parameterisation quality (no inference, no render)")
    print("  Reference A, w040 control mesh (known text, FLAT FRAGMENT -- scale only, not the bar):")
    print("      stretch median %.3f  anisotropy p90 %.3f  sag median %.1f um  p90 %.1f um"
          % (ctl["stretch_median"], ctl["anisotropy_p90"], ctl["sag_um_median"], ctl["sag_um_p90"]))
    print("  Reference B, the team's %d published segments (THE BAR):" % refB["n"])
    print("      pooled p90 anisotropy %.3f  pooled p90 sag %.1f um   (median-of-p90: %.3f / %.1f um)"
          % (refB["pooled_anisotropy_p90"], refB["pooled_sag_um_p90"],
             refB["median_anisotropy_p90"], refB["median_sag_um_p90"]))
    print("  Ours, %d auto-grown traces:" % ours["n"])
    print("      pooled p90 anisotropy %.3f  pooled p90 sag %.1f um   (median-of-p90: %.3f / %.1f um)"
          % (ours["pooled_anisotropy_p90"], ours["pooled_sag_um_p90"],
             ours["median_anisotropy_p90"], ours["median_sag_um_p90"]))
    print("      ratio to Reference B: anisotropy %.2fx   sag %.2fx"
          % (ours["pooled_anisotropy_p90"] / refB["pooled_anisotropy_p90"],
             ours["pooled_sag_um_p90"] / refB["pooled_sag_um_p90"]))
    print("  BAR: degraded if anisotropy p90 >= %.3f OR sag p90 >= %.1f um" % (a_bar, s_bar))
    print("  PARAMETERISATION-DEGRADED: %d of %d traces" % (len(deg), ours["n"]))
    for d in sorted(deg, key=lambda d: -(d["sag_um_p90"] or 0)):
        print("      %-32s ani %5.3f %s  sag %6.2f um %s  %s cm2"
              % (d["patch"][:32], d["anisotropy_p90"], "*" if d["by_anisotropy"] else " ",
                 d["sag_um_p90"], "*" if d["by_sag"] else " ",
                 "-" if d["area_cm2"] is None else "%.2f" % d["area_cm2"]))
    verdict = "DEGRADED SURFACES FOUND" if deg else "NO SURFACE DEGRADED: parameterisation is not the gap"
    print("  G-GP: %s" % verdict)
    # reported, gates nothing
    over_sheet = [r for r in ours["rows"] if (r["sag_um_p90"] or 0) >= SHEET_UM]
    print("  reported separately, gating nothing: %d of %d traces have p90 sag >= the ~%d um papyrus thickness;"
          % (len(over_sheet), ours["n"], SHEET_UM))
    print("      the worst p90 sag anywhere in our corpus is %.1f um, against the %.0f um wrap spacing (R-INTERIOR)."
          % (max((r["sag_um_p90"] or 0) for r in ours["rows"]), WRAP_UM))
    res = dict(bar=dict(factor=FACTOR, anisotropy_p90_bar=round(a_bar, 4), sag_um_p90_bar=round(s_bar, 2),
                        reference="team published segments (Reference B)"),
               refA=ctl, refB={k: refB[k] for k in refB if k != "rows" and k != "skipped"},
               ours={k: ours[k] for k in ours if k != "rows" and k != "skipped"},
               degraded=deg, n_degraded=len(deg), n_ours=ours["n"], verdict=verdict)
    json.dump(res, open(os.path.join(G, "ggp.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
