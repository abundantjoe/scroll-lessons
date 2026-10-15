"""Freeze the GOLD detector parameters from the CONTROL strips only (DECL-P4-10 item 2). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

tau_M     = 99.99th percentile of Z over all scored work px of control M (C1 for E1, C2 for E2), from the
            per-tile histograms (bin 0.25 grey; upper bin edge).
A_hot     = area (mm^2) of work px with Z > tau_M, per control tile (from the stored Z maps).
A_p99_M   = numpy.percentile(A_hot over control tiles, 99) (linear); the hotspot area bar.
Usage: python freeze.py <outdir> <params.json>
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold as G  # noqa: E402
import run_tiles as R  # noqa: E402
import xraylib as X  # noqa: E402

outdir, pp = sys.argv[1], sys.argv[2]
core = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "detector_core.json")))
LAM = 12.39842 / 78.0 * 1e-10
params = {"provenance": G.PROV,
          "serves": "RULES.md DECL-P4-10 items 2-4 (GOLD); frozen from control strips before any title-strip detector number",
          "core": core, "materials": {}, "control_of": {"E1": "C1", "E2": "C2"},
          "thicknesses_um": [0.01, 0.02, 0.05, 0.1, 0.3, 1.0], "plausible_thickness_um": 0.3,
          "rho_pap": [1.5, 0.5], "rho_pap_primary": 1.5,
          "mu_ratio_78keV": {str(r): X.CS_Total(79, 78.0) * 19.32 / (X.CS_Total_CP("C6H10O5", 78.0) * r) for r in (1.5, 0.5)},
          "injection_seed": 20260926,
          "recovery_rule": "new hot area (hot after injection and not before) within glyph mask dilated by radius_mm >= 0.5 x glyph area AND > A_p99 of the control",
          "sensitivity_bar": 0.8,
          "hotspot_rule": "tile not labelled-adjacent (E1: excl_d_a union; E2: excl_a union) AND A_hot > A_p99(control) AND f_in >= 0.8, f_in = A_sheet / (A_sheet + A_gap_lo + A_gap_hi) with gap windows of the same half-width centred 88-90 um off-sheet (E1/C1 slices 9..27 and 89..107; E2/C2 9..25 and 83..99), same tau",
          "rot90_note": "Z (isotropic disc mean of a per-column statistic) and A_hot are rotation-invariant; the rot-90 null equals the unrotated control by construction and is reported as such; the injection FP also evaluates a 90-degree-rotated patch against a fixed virtual glyph",
          "gap_windows": {"E1": [[9, 27], [89, 107]], "C1": [[9, 27], [89, 107]], "E2": [[9, 25], [83, 99]], "C2": [[9, 25], [83, 99]]}}
tf1 = {"z_det_m": 0.225, "g_rec": 500.0, "unsharp_c": 4.0, "unsharp_sigma_m": 2.5 * 1.129e-6,
       "g_au": 1 / ((X.CS_Total(79, 78.0) * 19.32 * 100 * LAM / (4 * np.pi)) / (1 - X.Refractive_Index_Re("Au", 78.0, 19.32)))}
tf2 = dict(tf1, z_det_m=0.22, g_rec=1000.0, unsharp_sigma_m=1.2 * 2.4e-6)
GPAP = {"C1": 82, "C2": 89}   # gpap.py medians of the controls over the +-20 um slab (numbers in STATUS/params)
GAIR = {"C1": 255 * 0.03 / 0.175, "C2": 255 * 0.04 / 0.26}
for M, C, tf, nch, rdz, sub in (("E1", "C1", tf1, 23, 1.129, 2), ("E2", "C2", tf2, 11, 2.4, 1)):
    recs = [json.loads(l) for l in open(os.path.join(outdir, C, "tiles.jsonl"))]
    h = np.zeros(R.NB, np.int64)
    for r in recs:
        for k, v in r["hist_nonzero"].items():
            h[int(k)] += v
    cdf = np.cumsum(h) / h.sum()
    ib = int(np.searchsorted(cdf, 0.9999))
    tau = R.HIST_LO + (ib + 1) * R.HIST_BIN
    m = G.MATERIALS[C]
    px_mm = m["px_um"] * m["B"] / 1000.0
    areas = []
    for r in recs:
        Z = np.load(os.path.join(outdir, C, f"r{r['r']}_c{r['c']}.npz"))["Z"].astype(np.float32)
        areas.append(float((np.isfinite(Z) & (Z > tau)).sum() * px_mm ** 2))
    a99 = float(np.percentile(areas, 99))
    entry = {"control": C, "tau": tau, "A_p99_mm2": a99, "control_tiles": len(recs),
             "control_work_px": int(h.sum()), "control_A_hot_mm2": {f"r{r['r']}_c{r['c']}": a for r, a in zip(recs, areas)},
             "dG_pap": GPAP[C] - GAIR[C], "G_pap_control_median": GPAP[C], "G_air_f32_zero": GAIR[C],
             "tf": tf, "patch_chunks": nch, "recon_dz_um": rdz, "subslices": sub,
             "control_tiles_rows_json": os.path.join(C, "tiles.jsonl")}
    params["materials"][M] = entry
    params["materials"][C] = entry
params["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(params, open(pp, "w"), indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("tau", "A_p99_mm2", "control_tiles", "dG_pap")}
                  for k, v in params["materials"].items()}))
