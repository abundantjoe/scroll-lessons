"""p4-pig-cu memo physics (RULES.md DECL-P4-10 item 1): mass/linear attenuation of Cu pigments, natural inclusions,
carbonised papyrus and carbon ink at the PHerc. Paris 4 scan energies (74, 78, 110, 137 keV).

Provenance: Project HERCULES | owner the owner | [id removed]

Source: NIST SRD 126 (Hubbell & Seltzer), elemental tables physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/zNN.html,
total mu/rho with coherent scattering, log-log interpolated between tabulated energies (no absorption edge lies between
50 and 150 keV for Z <= 29). Mixture rule: mu/rho = sum_i w_i (mu/rho)_i. Densities are literature/handbook values
(ranges given where uncertain). Usage: python physics.py <nist_html_dir> <out.json>
"""
import json
import re
import sys

import numpy as np

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
EN = [74, 78, 110, 137]
AW = {1: 1.008, 6: 12.011, 7: 14.007, 8: 15.999, 11: 22.99, 12: 24.305, 13: 26.982, 14: 28.085, 19: 39.098,
      20: 40.078, 26: 55.845, 29: 63.546}
SYM = {"H": 1, "C": 6, "N": 7, "O": 8, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "K": 19, "Ca": 20, "Fe": 26, "Cu": 29}

# (formula as atom counts or mass fractions, density g/cm3 [lo, nominal, hi], note)
MATS = {
    "egyptian_blue_CaCuSi4O10": ({"Ca": 1, "Cu": 1, "Si": 4, "O": 10}, [3.0, 3.07, 3.1], "cuprorivaite, X-ray density ~3.07"),
    "azurite_Cu3(CO3)2(OH)2": ({"Cu": 3, "C": 2, "O": 8, "H": 2}, [3.7, 3.77, 3.9], ""),
    "malachite_Cu2CO3(OH)2": ({"Cu": 2, "C": 1, "O": 5, "H": 2}, [3.6, 3.9, 4.05], ""),
    "tenorite_CuO": ({"Cu": 1, "O": 1}, [6.3, 6.4, 6.5], "decomposition product of azurite/malachite/verdigris"),
    "cuprite_Cu2O": ({"Cu": 2, "O": 1}, [6.0, 6.1, 6.2], "possible product in a reducing setting"),
    "verdigris_Cu(CH3COO)2.H2O": ({"Cu": 1, "C": 4, "H": 8, "O": 5}, [1.8, 1.88, 1.95], "neutral verdigris; converts to Cu oxides on heating"),
    "quartz_SiO2": ({"Si": 1, "O": 2}, [2.65, 2.65, 2.65], "sand"),
    "calcite_CaCO3": ({"Ca": 1, "C": 1, "O": 3}, [2.71, 2.71, 2.71], ""),
    "volcanic_glass_trachytic": ({"Si": 0.285, "Al": 0.098, "Fe": 0.030, "Ca": 0.025, "Na": 0.030, "K": 0.065, "Mg": 0.005, "O": 0.462}, [2.3, 2.45, 2.6],
                                 "approx. Vesuvian phonolite/tephriphonolite glass by mass; pumice is porous (bulk 0.5-1.2)"),
    "augite_pyroxene": ({"Ca": 0.15, "Mg": 0.07, "Fe": 0.08, "Al": 0.03, "Si": 0.23, "O": 0.44}, [3.2, 3.35, 3.5], "mafic phenocryst in Vesuvian ash"),
    "leucite_KAlSi2O6": ({"K": 1, "Al": 1, "Si": 2, "O": 6}, [2.45, 2.47, 2.5], "typical Vesuvian phenocryst"),
    "magnetite_Fe3O4": ({"Fe": 3, "O": 4}, [5.1, 5.18, 5.2], ""),
    "hematite_Fe2O3": ({"Fe": 2, "O": 3}, [5.2, 5.26, 5.3], "for reference (FE family)"),
    "carbonised_papyrus": ({"C": 0.78, "O": 0.15, "H": 0.03, "N": 0.01, "K": 0.01, "Ca": 0.01, "Si": 0.01}, [0.3, 0.5, 0.8],
                           "char composition approximate; bulk density of carbonised Herculaneum papyrus uncertain"),
    "carbon_ink_dry": ({"C": 0.90, "O": 0.07, "H": 0.02, "N": 0.01}, [0.8, 1.2, 1.6], "soot + gum; layer density uncertain"),
    "air": ({"N": 0.755, "O": 0.232, "C": 0.0001}, [0.0012, 0.0012, 0.0012], ""),
}


def load_tab(d):
    tab = {}
    for z in AW:
        t = open(f"{d}/z{z:02d}.html").read()
        rows = re.findall(r"([0-9.]+E[-+][0-9]+)\s+([0-9.]+E[-+][0-9]+)\s+([0-9.]+E[-+][0-9]+)", t)
        tab[z] = (np.array([float(a) for a, b, c in rows]), np.array([float(b) for a, b, c in rows]))
    return tab


def mu_el(tab, z, kev):
    E, m = tab[z]
    e = kev / 1000.0
    lo = max(k for k in range(len(E)) if E[k] <= e)
    hi = lo + 1
    return float(np.exp(np.interp(np.log(e), [np.log(E[lo]), np.log(E[hi])], [np.log(m[lo]), np.log(m[hi])])))


def main():
    tab = load_tab(sys.argv[1])
    out = {"provenance": PROV, "serves": "DECL-P4-10 item 1 (CU family memo)", "energies_keV": EN,
           "source": "NIST SRD 126 X-Ray Mass Attenuation Coefficients (Hubbell & Seltzer), elemental Table 3; log-log interpolation",
           "elements_mu_rho_cm2_g": {k: {str(e): mu_el(tab, z, e) for e in EN} for k, z in SYM.items()}, "materials": {}}
    for name, (f, rho, note) in MATS.items():
        if all(isinstance(v, int) for v in f.values()):
            m = {k: v * AW[SYM[k]] for k, v in f.items()}
            s = sum(m.values())
            w = {k: v / s for k, v in m.items()}
        else:
            s = sum(f.values())
            w = {k: v / s for k, v in f.items()}
        mr = {str(e): sum(wi * mu_el(tab, SYM[k], e) for k, wi in w.items()) for e in EN}
        out["materials"][name] = {"mass_fractions": w, "density_g_cm3_lo_nom_hi": rho, "note": note, "mu_rho_cm2_g": mr,
                                  "mu_lin_per_cm_nominal": {e: mr[e] * rho[1] for e in mr},
                                  "mu_lin_per_cm_range": {e: [mr[e] * rho[0], mr[e] * rho[2]] for e in mr}}
    pap = out["materials"]["carbonised_papyrus"]["mu_lin_per_cm_nominal"]
    for name, d in out["materials"].items():
        d["ratio_to_papyrus_nominal"] = {e: d["mu_lin_per_cm_nominal"][e] / pap[e] for e in pap}
    json.dump(out, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
