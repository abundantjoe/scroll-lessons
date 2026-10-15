"""p4-highz DECL-P4-6-A3 aggregator: screen at offsets (sweep, Bonferroni) or at d* (single offset, unchanged bar).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python screen_off.py <scratch> <repo> <control> <target> <o_um,...> [candidates]
With several offsets the n_hi bar per offset is percentile(control n_hi at that offset, 100 (1 - 0.01/9)); with one
offset (d*) it is the unchanged p99. f_in: full-coverage value where computed (offgap_<m>.jsonl), else the 6 % sample.
"""
import json
import os
import sys
import time

import numpy as np

scr, repo, CT, TG, offs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
O = [int(x) for x in offs.split(",")]
q_bar = 100 * (1 - 0.01 / 9) if len(O) > 1 else 99.0
recs = {m: {(d["r"], d["c"]): d for d in map(json.loads, open(os.path.join(scr, f"off_{m}_{'_'.join(map(str, O))}.jsonl")))}
        for m in (CT, TG)}
if "candidates" in sys.argv:
    out = {}
    for o in O:
        bar = float(np.percentile([d["offsets"][str(o)]["n_hi"] for d in recs[CT].values()], q_bar))
        out[o] = {m: [f"{r},{c}" for (r, c), d in recs[m].items() if d["offsets"][str(o)]["n_hi"] > bar] for m in (CT, TG)}
    print(json.dumps(out))
    sys.exit()
fin = {m: json.load(open(os.path.join(scr, f"fin_{m}_{'_'.join(map(str, O))}.json"))) for m in (CT, TG)}
full = {}
for m in (CT, TG):
    p = os.path.join(scr, f"offgap_{m}.jsonl")
    if os.path.exists(p):
        for d in map(json.loads, open(p)):
            full[(m, d["r"], d["c"], d["o_um"])] = d


def q(a):
    a = np.array([x for x in a if x is not None], float)
    return None if not a.size else {k: float(v) for k, v in zip(("min", "median", "p90", "max"), np.percentile(a, [0, 50, 90, 100]))}


per = {}
rot_ok = True
for o in O:
    bar = float(np.percentile([d["offsets"][str(o)]["n_hi"] for d in recs[CT].values()], q_bar))
    blk = {"n_hi_bar": bar, "bar_percentile": q_bar}
    for m in (CT, TG):
        rows = []
        for (r, c), d in sorted(recs[m].items()):
            x = d["offsets"][str(o)]
            fu = full.get((m, r, c, o))
            fs = fin[m][f"r{r}_c{c}"][str(o)]
            f_in = fu["f_in_full"] if fu else fs["f_in_sample"]
            a, a9, s = x["acf"] or {}, x["acf_rot90"] or {}, x["stroke"]
            rot_ok &= abs((a.get("radial_peak_2_4mm") or 0) - (a9.get("radial_peak_2_4mm") or 0)) < 1e-6
            rows.append({"tile": f"r{r}_c{c}", "n_hi": x["n_hi"], "gt_bar": x["n_hi"] > bar, "f_in": f_in,
                         "f_in_source": "full" if fu else "6 % sample", "gap_slices_available": fs["gap_slices_available"],
                         "DENSE_HOTSPOT": bool(x["n_hi"] > bar and f_in >= 0.8),
                         "letter_scale_components": s.get("components_letter_scale_0p5_5mm", 0),
                         "comp_extent_mm_max": s.get("comp_extent_mm_max"), "width_um_median": s.get("width_um_median"),
                         "acf_radial_peak_2_4mm": a.get("radial_peak_2_4mm"), "c10_c17": 10 <= c <= 17})
        def summ(L):
            return {"tiles": len(L), "gt_bar": [x["tile"] for x in L if x["gt_bar"]],
                    "DENSE_HOTSPOT": [x["tile"] for x in L if x["DENSE_HOTSPOT"]],
                    "f_in": q([x["f_in"] for x in L]), "letter_scale_tiles": sum(x["letter_scale_components"] > 0 for x in L),
                    "comp_extent_mm_max": q([x["comp_extent_mm_max"] for x in L]),
                    "acf_radial_peak_2_4mm": q([x["acf_radial_peak_2_4mm"] for x in L]),
                    "n_hi": q([x["n_hi"] for x in L])}
        blk[m] = {"all": summ(rows), "c10_c17": summ([x for x in rows if x["c10_c17"]]), "tiles": rows}
    per[str(o)] = blk
out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
       "serves": "RULES.md DECL-P4-6-A3 (" + ("offset sweep, STOP branch" if len(O) > 1 else "d* re-run") + "); PROTOCOL_dstar.md",
       "control": CT, "target": TG, "offsets_um": O, "rule": "DENSE-HOTSPOT = n_hi > bar AND f_in >= 0.8",
       "rot90_radial_identical_all": rot_ok,
       "any_hotspot_target": sorted({t for o in per.values() for t in o[TG]["all"]["DENSE_HOTSPOT"]}),
       "note_c10_c17": ("c10-c17 is the title zone on the E2 (strip a) grid; on the E1 grid (a different trace of the same "
                        "strip, 6 x 21 tiles) the same column indices do not map to the same papyrus and are reported only because asked"
                        if TG == "E1" else "title zone on the strip-a grid (DECL-P4-12)"),
       "per_offset": per, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
fn = f"screen_dstar_{TG}.json"
json.dump(out, open(os.path.join(repo, "logs/sib/p4-highz", fn), "w"), indent=1)
for o in O:
    b = per[str(o)]
    print(o, round(b["n_hi_bar"]), "gt", b[TG]["all"]["gt_bar"], "hot", b[TG]["all"]["DENSE_HOTSPOT"], "ctl_hot", b[CT]["all"]["DENSE_HOTSPOT"],
          "letter", b[TG]["all"]["letter_scale_tiles"], "/", b[CT]["all"]["letter_scale_tiles"], "fin_max", round(b[TG]["all"]["f_in"]["max"], 3))
print("rot_ok", rot_ok)
