"""p4-highz step 1 output: physics.json (strip-level numbers) and thresholds.json (T_mid, T_hi frozen from the
control's in-sheet voxels > 0, PROTOCOL.md). Uses strip-level aggregates only; no per-tile number is computed.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python freeze.py <scratch> <repo>
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

scr, repo = sys.argv[1], sys.argv[2]
CTRL, TGT, SUF = (sys.argv[3:6] if len(sys.argv) > 5 else ("C", "E1", ""))
MD = C.MATERIALS[CTRL]
out = os.path.join(repo, "logs/sib/p4-highz")
phys = {"provenance": C.PROV, "serves": "RULES.md DECL-P4-6 item 2 (physics sanity, before any tile)",
        "slabs": {"sheet": [MD["sheet"][0], MD["sheet"][1] - 1], "gap_lo": [MD["gap_lo"][0], MD["gap_lo"][1] - 1],
                  "gap_hi": [MD["gap_hi"][0], MD["gap_hi"][1] - 1], "centre": MD["centre"], "um_per_slice": MD["um"]},
        "level": 0, "dtype": "uint8 (max 255)", "percentile_rule": "smallest v with CDF(v) >= q",
        "materials": {}}
agg = {}
for name in (CTRL, TGT):
    z = np.load(os.path.join(scr, f"stage_a_{name}.npz"))
    info = json.load(open(os.path.join(scr, f"stage_a_{name}.json")))
    H = z["H"].sum(0)  # (4, 256): sheet, gap_lo, gap_hi, sheet max per px
    agg[name] = H
    prof = z["prof"].sum(0) / max(1, z["npx"].sum())
    profnz = z["profnz_s"].sum(0) / np.maximum(1, z["profnz_n"].sum(0))
    gaps = H[1] + H[2]
    phys["materials"][name] = {
        **{k: v for k, v in info.items()},
        "valid_px_columns_sampled": int(z["npx"].sum()),
        "sheet_slab": C.pct_block(H[0]), "gap_slabs_both": C.pct_block(gaps),
        "gap_lo": C.pct_block(H[1]), "gap_hi": C.pct_block(H[2]), "sheet_max_per_px": C.pct_block(H[3]),
        "depth_profile_mean_incl_zero": [round(float(a), 3) for a in prof],
        "depth_profile_mean_excl_zero": [round(float(a), 3) for a in profnz],
        "depth_profile_note": f"index 0..{MD['n_slices'] - 1}; slabs as above",
    }
Hc = agg[CTRL][0].copy()
Hc[0] = 0
T_mid, T_hi = C.hist_pct(Hc, 0.5), C.hist_pct(Hc, 0.999)


def ks(h1, h2):
    a, b = np.cumsum(h1) / h1.sum(), np.cumsum(h2) / h2.sum()
    return float(np.max(np.abs(a - b)))


hz = lambda h: np.concatenate([[0], h[1:]])
phys[f"ks_control_vs_{TGT}"] = {
    "sheet_slab_excl_zero": ks(hz(agg[CTRL][0]), hz(agg[TGT][0])),
    "gap_slabs_excl_zero": ks(hz(agg[CTRL][1] + agg[CTRL][2]), hz(agg[TGT][1] + agg[TGT][2])),
    "sheet_max_per_px_excl_zero": ks(hz(agg[CTRL][3]), hz(agg[TGT][3])),
    "note": "two-sample KS D between voxel histograms; voxels are spatially correlated, so no p-value is claimed"}
for name in (CTRL, TGT):
    H = agg[name]
    ns, ng = int(H[0][T_hi + 1:].sum()), int(H[1][T_hi + 1:].sum() + H[2][T_hi + 1:].sum())
    phys["materials"][name]["gt_T_hi"] = {"n_sheet": ns, "n_gaps": ng, "f_in_raw": ns / max(1, ns + ng),
                                          "density_sheet": ns / max(1, H[0].sum()),
                                          "density_gaps": ng / max(1, H[1].sum() + H[2].sum())}
phys["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
th = {"provenance": C.PROV, "serves": "RULES.md DECL-P4-6 item 2; frozen before any P4-F tile or per-tile number",
      "T_mid": T_mid, "T_hi": T_hi,
      "source": (f"control {MD['seg']} {MD['sv'].split('/')[-1]}, level 0, sheet slab slices {MD['sheet'][0]}.."
                 f"{MD['sheet'][1] - 1}, mesh-valid px of the eligible control tiles, 6 % whole-chunk random sample, voxels > 0"),
      "T_mid_rule": "p50 (median)", "T_hi_rule": "p99.9", "applies_to": [TGT, CTRL],
      "control_sheet_voxels_nonzero": int(Hc.sum()),
      "tile_value": "clip(255 * (max_sheet - T_mid) / (T_hi - T_mid), 0, 255); 0 outside mesh-valid",
      "n_hi_rule": "sheet-slab voxels > T_hi", "utc": phys["utc"]}
json.dump(phys, open(os.path.join(out, f"physics{SUF}.json"), "w"), indent=1)
json.dump(th, open(os.path.join(out, f"thresholds{SUF}.json"), "w"), indent=1)
print(json.dumps({"T_mid": T_mid, "T_hi": T_hi}))
