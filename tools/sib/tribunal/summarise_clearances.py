# Provenance: Project HERCULES | owner the owner | [id removed]
"""Add the flag summary to recheck_clearances.json (numbers only).

    python tools/sib/tribunal/summarise_clearances.py logs/sib/tribunal/recheck_clearances.json
"""
import json
import sys

p = sys.argv[1]
d = json.load(open(p))
J = d["part_j"]["segments"]
B = d["part_b"]
flags = []
for s, v in J.items():
    if v["retained_px_surface_lt128"]:
        flags.append({"where": f"D3-FEAS pixel exclusion, segment {s}", "declared_margin_vox": 128,
                      "finding": f"{v['retained_px_surface_lt128']} retained canvas pixel(s) at surface distance "
                                 f"{v['min_surface_dist_retained_px']:.4f} vox (point distance >= 128)",
                      "shortfall_vox": 128 - v["min_surface_dist_retained_px"], "severity": "negligible (< 0.001 vox)",
                      "tiles_affected": len(v["flag_eligible_but_surface_lt128"])})
    if v["flag_point_ge144_but_surface_lt144"]:
        flags.append({"where": f"DECL-D3-A2 144 vox pool rule, segment {s}", "tiles": v["flag_point_ge144_but_surface_lt144"]})
w047 = B["bank"]["20260206000001-w047_2026020613"]["vs_base"]
flags.append({"where": "RCBANK-1 w047", "declared": "same-papyrus pixels vs base training excluded (+64 px halo)",
              "finding": "corrected rule: w047 SAME as base-training w045 (vertex form alone: NOT SAME); w046 misses SAME "
                         "by the ratio test (c0 4964 < 2 x 2490); area within 2 vox: w045 %.4f cm^2, w046 %.4f cm^2 "
                         "(RCBANK-1 recorded ~0.12 cm^2 strip, excluded)" % (w047["20260126000000-w045_2026012619"]["area_lt2_cm2"],
                                                                             w047["20260325000000-w046_20260325"]["area_lt2_cm2"]),
              "severity": "consistent with RCBANK-1 (already excluded); only the literal form would have missed it"})
bl = B["blanks"]["blank_w053_y256_x7168"]["vs_base"]["20260302000000-w039_2026030210"]
flags.append({"where": "SEAL-J-D1 blank_w053_y256_x7168 vs base-training w039",
              "finding": "not SAME (%d points within 2 vox < 1000) but %.5f cm^2 of the blank lies within 2 vox of base-training "
                         "w039 (min surface distance %.3f vox): a crossing/contact sliver, ~0.03 %% of the blank" %
                         (bl["surface_counts"][0] + bl["surface_counts"][1], bl["area_lt2_cm2"], bl["min_surface_dist_vox"]),
              "declared_margin": "none declared for blanks vs base training (DECL-D1-A1: outside READ-CAL windows + 128 vox)",
              "severity": "informational; relevant only to the w053 blob-f180 bar if it is meant to be base-clean"})
d["summary"] = {
    "recorded_method_answer": "D3-FEAS counts A and B computed point-to-point distances on DENSE canvas points (1 px = 1 vox, "
                              "every mesh-valid pixel of J), not on 20-vox vertices; this re-check reproduces the recorded minimum "
                              "retained distance (w00 128.00015 vox) and shows point minus surface <= 0.0025 vox at that density",
    "tiles_checked": "every PRIMARY-grid tile (128 px, stride 64, >= 90 % mesh-valid, outside own J window): a superset of the "
                     "306 PRIMARY text tiles and 288 pool tiles (text status not recomputed: it needs the 0841 reference ink map)",
    "tiles_below_128_by_surface_form": sum(len(v["flag_eligible_but_surface_lt128"]) for v in J.values()),
    "tiles_crossing_144_by_surface_form": sum(len(v["flag_point_ge144_but_surface_lt144"]) for v in J.values()),
    "seal_j_d1_blanks_distance_to_J": "not defined: the blanks are on PHerc0139 w053, J is on PHerc0841 (different volumes)",
    "flags": flags,
}
json.dump(d, open(p, "w"), indent=1, sort_keys=True, default=float)
print(json.dumps(d["summary"], indent=1)[:3000])
