"""p4-pig-gold memo numbers (RULES.md DECL-P4-10 item 1). Tabulated physics only; no CT pixel is used.

Provenance: Project HERCULES | owner the owner | [id removed]

Sources: xraylib (Schoonjans et al. 2011, Spectrochim. Acta B 66:776) cross sections (EPDL/Scofield photo,
equivalent to NIST XCOM within a few %), refractive index decrement delta from xraylib Refractive_Index_Re.
Grey calibration: the published zarr metadata.json 'zarr_export.target_window_f32_{min,max}' of each volume.
"""
import json
import math
import sys

import xraylib as X

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
RHO_AU = 19.32
ENERGIES = [74.0, 78.0, 110.0, 137.0]
PAPYRUS = "C6H10O5"          # cellulose proxy for carbonised papyrus (carbon: see mu_rho_C)
RHO_PAP = [0.3, 0.5, 1.0, 1.5]  # g/cm3 bracket (1.5 = crystalline cellulose, an upper bound)
out = {"provenance": PROV, "xraylib": X.__version__, "au_K_edge_keV": X.EdgeEnergy(79, X.K_SHELL),
       "hg_K_edge_keV": X.EdgeEnergy(80, X.K_SHELL), "pb_K_edge_keV": X.EdgeEnergy(82, X.K_SHELL), "per_energy": {}}
for E in ENERGIES:
    lam_m = 12.39842 / E * 1e-10
    mu_au = X.CS_Total(79, E) * RHO_AU  # 1/cm
    d_au = 1 - X.Refractive_Index_Re("Au", E, RHO_AU)
    beta_au = mu_au * 100 * lam_m / (4 * math.pi)
    row = {"mu_rho_Au_cm2_g": X.CS_Total(79, E), "mu_rho_Au_photo": X.CS_Photo(79, E),
           "mu_Au_per_cm": mu_au, "delta_Au": d_au, "beta_Au": beta_au, "delta_over_beta_Au": d_au / beta_au,
           "mu_rho_C": X.CS_Total(6, E), "mu_rho_cellulose": X.CS_Total_CP(PAPYRUS, E), "papyrus": {}}
    for rho in RHO_PAP:
        mu_p = X.CS_Total_CP(PAPYRUS, E) * rho
        d_p = 1 - X.Refractive_Index_Re(PAPYRUS, E, rho)
        row["papyrus"][str(rho)] = {"mu_per_cm": mu_p, "mu_ratio_Au_over_pap": mu_au / mu_p,
                                    "delta": d_p, "delta_ratio_Au_over_pap": d_au / d_p,
                                    "delta_over_beta": d_p / (mu_p * 100 * lam_m / (4 * math.pi))}
    out["per_energy"][str(E)] = row

# Partial-volume contrast in uint8 grey (linear reconstruction, DC-preserving Paganin; see MEMO.md 2).
# dG_pap = G_papyrus - G_air, with G_air = grey of f32 = 0 from the published window.
WIN = {"1.129um_78keV": (-0.03, 0.145), "2.4um_78keV": (-0.04, 0.22), "2.4um_137keV": (0.01, 0.16),
       "45.5um_74keV": (-0.058, 0.27), "45.5um_110keV": (-0.04, 0.2)}
out["grey_of_f32_zero"] = {k: 255 * (0 - a) / (b - a) for k, (a, b) in WIN.items()}
G_PAP = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0   # measured sheet median (p4-highz physics.json: 80 / 77)
pv = {}
for vox_name, vox_um, g_air in (("1.129um", 1.129, out["grey_of_f32_zero"]["1.129um_78keV"]),
                                ("2.258um (L1 surface volume)", 2.258, out["grey_of_f32_zero"]["1.129um_78keV"]),
                                ("2.4um", 2.4, out["grey_of_f32_zero"]["2.4um_78keV"])):
    dg = G_PAP - g_air
    for t in (0.1, 0.5, 2.0):
        for rho in RHO_PAP:
            ratio = out["per_energy"]["78.0"]["papyrus"][str(rho)]["mu_ratio_Au_over_pap"]
            phi = min(1.0, t / vox_um)
            dG = dg * phi * ratio               # un-blurred single-voxel increment, grey levels
            integ = dg * (t / vox_um) * ratio   # depth integral, grey x slices (conserved by Paganin DC gain 1)
            pv[f"{vox_name}|t={t}um|rho_pap={rho}"] = {
                "fill_fraction": phi, "dG_pap_grey": dg, "mu_ratio": ratio,
                "dG_unblurred_grey": dG, "saturates_unblurred": G_PAP + dG >= 255,
                "depth_integral_grey_slices": integ,
                "mean_increment_over_19_slices": integ / 19.0}
out["partial_volume"] = {"G_pap_assumed": G_PAP, "rows": pv}
# Pliny NH 33.61: one uncia beaten into >= 750 leaves 4 digits square
uncia_g, digit_cm = 27.3, 1.85
area = 750 * (4 * digit_cm) ** 2
out["pliny_leaf_thickness_um"] = uncia_g / (RHO_AU * area) * 1e4
json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else "memo_numbers.json", "w"), indent=1)
