"""AUDIT step 5: turn the measurements into the two upper bounds the hypothesis asks for.

BOUND 1 (label-noise attenuation).  If a fraction alpha of the "text" class is really blank and a
fraction beta of the "blank" class is really ink, and that mislabelling is independent of the score,
then for ANY score s exactly

        AUC_obs(s) - 1/2 = (1 - alpha - beta) * (AUC_true(s) - 1/2)        [derivation in the notes]

The attenuation kappa = 1 - alpha - beta is a property of the REFERENCE, shared by every score.  The
team model is scored against the same pixels, and AUC_true <= 1, so
        kappa >= 2 * (AUC_obs(team) - 1/2)
and therefore our own de-noised AUC is bounded by
        AUC_true(ours) <= 1/2 + (AUC_obs(ours) - 1/2) / (2*(AUC_obs(team) - 1/2)).
No model of the label noise is needed -- only that it does not depend on which score is being judged.

BOUND 2 (registration).  From step 3: the AUC an ORACLE detector achieves when displaced by the
measured within-crop registration residual.  That is the highest AUC any perfect detector could
score against these labels.  Also the displacement delta* that would be needed to pull the oracle
down to our measured AUC.
"""
import os, sys, json, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import au_lib as A

TAGS = ["v0.1b", "v1b", "v2", "v3"]
rows = []
for seg, crop in A.TRAIN + A.HELD:
    p2 = os.path.join(A.ROOT, f"stats/explore/au_step2_{seg}_{crop}.json")
    p3 = os.path.join(A.ROOT, f"stats/explore/au_step3_{seg}_{crop}.json")
    if not (os.path.exists(p2) and os.path.exists(p3)):
        continue
    r2, r3 = json.load(open(p2)), json.load(open(p3))
    lad = r2["erosion_ladder"]["0"]
    team = lad["team"]
    kappa_min = 2 * (team - 0.5)
    best_tag = max(TAGS, key=lambda t: lad.get(t, 0))
    ours = lad[best_tag]
    bound1 = 0.5 + (ours - 0.5) / kappa_min

    cur = r3["oracle_vs_displacement_mm"]
    dd = np.array([float(k) for k in cur], float)
    ot = np.array([cur[k]["oracle_team"] for k in cur], float)
    ol = np.array([cur[k]["oracle_label"] for k in cur], float)
    resid = r3.get("residual_um_rms_about_tile_mean", None)
    ceil_t = float(np.interp(resid / 1000.0, dd, ot)) if resid else None
    ceil_l = float(np.interp(resid / 1000.0, dd, ol)) if resid else None
    # displacement that would pull the oracle down to our measured AUC (monotone decreasing curve)
    dstar_t = float(np.interp(-ours, -ot, dd)) if ours < ot[0] else 0.0
    dstar_l = float(np.interp(-ours, -ol, dd)) if ours < ol[0] else 0.0

    rows.append({
        "seg": seg, "crop": crop, "held_out": (seg, crop) in A.HELD,
        "best_tag": best_tag, "auc_ours_obs": round(ours, 4), "auc_team_obs": round(team, 4),
        "kappa_min_from_team": round(kappa_min, 4),
        "bound1_perfect_reference_ceiling_for_ours": round(bound1, 4),
        "auc_ours_erode0.3": round(max(r2["erosion_ladder"]["0.3"].get(t, 0) for t in TAGS), 4),
        "auc_team_erode0.3": round(r2["erosion_ladder"]["0.3"]["team"], 4),
        "auc_ours_clean_both": round(max(r2["reference_cleaning"]["clean_both"].get(t, 0) for t in TAGS), 4),
        "global_residual_um": round(float(np.hypot(*r3["global_shift_um"])), 1),
        "tile_residual_um_rms": resid, "tile_residual_um_max": r3.get("residual_um_max"),
        "bound2_oracle_team_at_residual": round(ceil_t, 4) if ceil_t else None,
        "bound2_oracle_label_at_residual": round(ceil_l, 4) if ceil_l else None,
        "displacement_mm_to_explain_our_auc_teamoracle": round(dstar_t, 3),
        "displacement_mm_to_explain_our_auc_labeloracle": round(dstar_l, 3),
    })

held = [r for r in rows if r["held_out"]]
summary = {}
for k in ("auc_ours_obs", "auc_team_obs", "bound1_perfect_reference_ceiling_for_ours",
          "auc_ours_erode0.3", "auc_team_erode0.3", "auc_ours_clean_both",
          "tile_residual_um_rms", "bound2_oracle_team_at_residual", "bound2_oracle_label_at_residual",
          "displacement_mm_to_explain_our_auc_teamoracle", "displacement_mm_to_explain_our_auc_labeloracle"):
    summary["held_out_mean_" + k] = round(float(np.mean([r[k] for r in held if r[k] is not None])), 4)
A.jwrite(os.path.join(A.ROOT, "stats/explore/au_step5_bound.json"), {"per_crop": rows, "held_out_summary": summary})
for r in rows:
    print(("HELD " if r["held_out"] else "TRAIN"), r["seg"], r["crop"], r["best_tag"],
          "| ours %.3f team %.3f | kappa>=%.3f -> perfect-ref ceiling %.3f | erode0.3 ours %.3f team %.3f"
          " | resid %s um -> oracle ceiling %.3f/%.3f | delta* %.2f/%.2f mm"
          % (r["auc_ours_obs"], r["auc_team_obs"], r["kappa_min_from_team"],
             r["bound1_perfect_reference_ceiling_for_ours"], r["auc_ours_erode0.3"], r["auc_team_erode0.3"],
             r["tile_residual_um_rms"], r["bound2_oracle_team_at_residual"] or -1,
             r["bound2_oracle_label_at_residual"] or -1,
             r["displacement_mm_to_explain_our_auc_teamoracle"],
             r["displacement_mm_to_explain_our_auc_labeloracle"]))
print()
for k, v in summary.items():
    print(" ", k, v)
