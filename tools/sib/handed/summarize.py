# Provenance: Project HERCULES | owner the owner | [id removed]
"""Summary numbers for REPORT.md -> logs/sib/handed/handed_summary.json."""
import json
from collections import Counter
from pathlib import Path

D = Path(__file__).resolve().parents[3] / "logs/sib/handed"
mp = json.loads((D / "mesh_predictions.json").read_text())
aff = json.loads((D / "affine_determinants.json").read_text())
syn = json.loads((D / "synthetic_scores.json").read_text())["summary"]
tab = json.loads((D / "volume_table.json").read_text())
cov = json.loads((D / "maas_labels_0139_coverage.json").read_text())


def grp(scroll, frame=None):
    return [m for m in mp if m["scroll"] == scroll and (frame is None or frame in m["tifxyz"])]


def stats(ms):
    out = dict(n=len(ms), confidence=dict(Counter(m.get("confidence") for m in ms)),
               native_legible=dict(Counter(str(m.get("prediction", {}).get("native_legible")) for m in ms)),
               mirror_u_needed=dict(Counter(str(m.get("prediction", {}).get("mirror_u_needed")) for m in ms)),
               flip_v_needed=dict(Counter(str(m.get("prediction", {}).get("flip_v_needed")) for m in ms)))
    src = {}
    for m in ms:
        for k, v in m.get("chirality", {}).items():
            if k not in m.get("voting_sources", []):
                continue
            s = src.setdefault(k, dict(signs=Counter(), min_agreement=1.0))
            s["signs"][str(v["sign"])] += 1
            if v["agreement"] == v["agreement"]:
                s["min_agreement"] = min(s["min_agreement"], v["agreement"])
    out["sources"] = {k: dict(signs=dict(v["signs"]), min_agreement=round(v["min_agreement"], 4)) for k, v in src.items()}
    pair = {}
    for m in ms:
        for k, v in m.get("source_agreement", {}).items():
            if v.get("n"):
                pair.setdefault(k, []).append(v["agree"])
    out["pairwise_sign_agreement_min"] = {k: round(min(v), 4) for k, v in pair.items()}
    out["pairwise_sign_agreement_median"] = {k: round(sorted(v)[len(v) // 2], 4) for k, v in pair.items()}
    w = [m["winding"] for m in ms if m.get("winding", {}).get("w")]
    out["winding"] = dict(n_measured=len(w), w=dict(Counter(x["w"] for x in w)),
                          consistent_with_top_flag=sum(x.get("predicts_top_at_low_z") == x.get("metadata_top_at_low_z") for x in w))
    j = [m["j_exclusion"]["frac_kept"] for m in ms if "j_exclusion" in m]
    if j:
        out["j_exclusion_frac_kept"] = [round(x, 4) for x in j]
    return out


same = [a for a in aff if a["lh_from"] == a["lh_to"]]
diff = [a for a in aff if a["lh_from"] != a["lh_to"]]
opp = [a for a in aff if a.get("acq_from") and a.get("acq_to") and a["acq_from"] != a["acq_to"]]
S = dict(
    synthetic=syn,
    parity_flag_vs_affines=dict(n=len(aff), same_flag=len(same), same_flag_det_pos=sum(a["det"] > 0 for a in same),
                                diff_flag=len(diff), diff_flag_det_neg=sum(a["det"] < 0 for a in diff)),
    opposite_acquisition_z_affines=[dict(sample=a["sample"], frm=a["from_volume"], acq_from=a["acq_from"], to=a["to_volume"],
                                         acq_to=a["acq_to"], det=round(a["det"], 4)) for a in opp],
    PHerc0139_9um=stats(grp("PHerc0139", "9.362um")), PHerc0139_2p4um=stats(grp("PHerc0139", "2.399um")),
    PHerc0009B=stats(grp("PHerc0009B")), PHerc0841=stats(grp("PHerc0841")),
    PHerc0800=stats(grp("PHerc0800")), PHerc1447=stats(grp("PHerc1447")),
    label_check=dict(letter_identities=False,
                     label_arrays=["inklabels.zarr", "supervision.zarr", "validation.zarr (0841 only)"],
                     dtype="uint8 single channel, OME-Zarr 0.5 multiscales y,x; no class table",
                     layout_slant=dict(segments=len(cov["segments"]), measurable_columns=0,
                                       widest_ink_run_mm=max(max([w for _, w in s["ink_x_occupancy_runs_mm"]] or [0]) for s in cov["segments"]),
                                       supervised_extent_mm_max=max(max(s["supervised_extent_mm_rows"], s["supervised_extent_mm_cols"]) for s in cov["segments"]))),
    volumes=len(tab), rule_confidence=dict(Counter(r["rule_confidence"].split(" ")[0] for r in tab)),
)
(D / "handed_summary.json").write_text(json.dumps(S, indent=1))
print(json.dumps(S, indent=1)[:6000])
