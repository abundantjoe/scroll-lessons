"""Render logs/sib/p4-purple/colourants.json as tables (numbers copied, not recomputed).
Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python colourants_md.py <repo>   (prints markdown tables to stdout)"""
import json
import os
import sys

d = json.load(open(os.path.join(sys.argv[1], "logs/sib/p4-purple/colourants.json")))
M = d["materials"]
f = lambda v, p=2: "-" if v is None else f"{v:.{p}f}"
print("### Table A. Optics of the paint layer (pigment volume fraction 0.5 in carbonised binder)\n")
print("| colourant | class | layer rho g/cm3 | mu78 cm-1 | mu137 cm-1 | R = mu137/mu78 | delta78 (1e-8) | delta/beta 78 | mu78 / papyrus (rho 0.3 / 1.0) |")
print("|---|---|---|---|---|---|---|---|---|")
for n, r in M.items():
    p = r["phi"]["0.5"]
    print(f"| {n} | {r['class']} | {f(p['layer_density_g_cm3'])} | {f(p['78']['mu_cm-1'],3)} | {f(p['137']['mu_cm-1'],3)} | "
          f"{f(p['R_mu137_over_mu78'],3)} | {f(p['78']['delta']*1e8)} | {p['78']['delta_over_beta']:.0f} | "
          f"{f(p['78']['mu_ratio_to_papyrus']['0.3'],1)} / {f(p['78']['mu_ratio_to_papyrus']['1.0'],1)} |")
pp = d["papyrus"]["mu_cm-1"]
print(f"\nCarbonised papyrus (C 0.70 / O 0.25 / H 0.05): mu78 = {pp['0.3']['78']:.4f} / {pp['0.43']['78']:.4f} / {pp['1.0']['78']:.4f} cm-1 "
      f"at 0.3 / 0.43 / 1.0 g/cm3; R = {pp['1.0']['137']/pp['1.0']['78']:.3f} at any density.\n")
print("### Table B. Predicted peak voxel contrast of a deposit at 78 keV, 2.4 um (grey levels over void; noise sigma 29.2 grey)\n")
print("| colourant | (i) absorption 5 / 10 / 20 um | (ii) Paganin 5 / 10 / 20 um | CNR (ii) 5 / 10 / 20 um | (ii) vs carbon ink, 10 um | t for CNR 3: (ii) / (i) um | saturates uint8 at 5 um |")
print("|---|---|---|---|---|---|---|")
for n, r in M.items():
    p = r["phi"]["0.5"]; t = p["thickness_um"]
    a = " / ".join(f"{t[k]['78']['absorption_grey']:.0f}" for k in ("5", "10", "20"))
    g = " / ".join(f"{t[k]['78']['paganin_grey']:.0f}" for k in ("5", "10", "20"))
    c = " / ".join(f"{t[k]['78']['CNR_vox_paganin']:.1f}" for k in ("5", "10", "20"))
    print(f"| {n} | {a} | {g} | {c} | {t['10']['78']['paganin_contrast_ratio_to_carbon_ink_same_t']:.2f} | "
          f"{f(p['t_um_CNR3_paganin_78'])} / {f(p['t_um_CNR3_absorption_78'])} | {'yes' if t['5']['78']['saturates_uint8_over_void'] else 'no'} |")
print("\n### Table C. Dual-energy signature, 10 um deposit on a 100 um carbonised papyrus column (rho 0.43)\n")
print("| colourant | R (true) | Paganin peak ratio 137/78 | column ratio shift dR | CNR_DE per 0.2 mm patch (correlated-noise estimate; upper bound) | dR at 5 / 20 um |")
print("|---|---|---|---|---|---|")
for n, r in M.items():
    p = r["phi"]["0.5"]; t = p["thickness_um"]
    dc = t["10"]["dual_energy_column"]["100"]
    print(f"| {n} | {f(p['R_mu137_over_mu78'],3)} | {f(t['10']['paganin_peak_ratio_137_over_78'])} | {dc['delta_R']:+.3f} | "
          f"{dc['CNR_DE_patch_correlated']:+.1f} | {t['5']['dual_energy_column']['100']['delta_R']:+.3f} / {t['20']['dual_energy_column']['100']['delta_R']:+.3f} |")
