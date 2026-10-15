"""p4-highz pigment physics (orchestrator addenda to DECL-P4-6-A1/A2, DECL-P4-12): expected CT contrast of
mineral pigments vs carbonised papyrus at the Paris 4 scan energies, and the minimum layer thickness that would
push a sheet-slab voxel above T_hi. Tabulated data only (NIST X-ray mass attenuation coefficients, Hubbell &
Seltzer, NISTIR 5632, element tables z01-z82 fetched from physics.nist.gov and stored in data/sib/p4-highz/).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python pigments.py <scratch> <repo>

Model (stated, approximate):
- grey g is linear in the linear attenuation coefficient mu: g = g_void + (g_pap - g_void) * mu / mu_pap, with
  g_void and g_pap the two modes of the control's sheet+gap voxel histogram (voids between/inside sheets, papyrus).
- A pigment layer of thickness t on the recto fills a fraction f = t / voxel of a voxel otherwise papyrus:
  g = g_pap + f (g_pig - g_pap), g_pig unclipped. Voxel > T_hi requires f > (T_hi - g_pap) / (g_pig - g_pap).
- No point-spread blur and no phase-contrast edge enhancement are modelled: blur of FWHM ~2 voxels roughly doubles
  the needed t for layers thinner than the blur; phase contrast (22 cm propagation) adds edge overshoot. So t_min is
  a lower bound for an ideal system, uncertain to about a factor 2-3.
- Carbonised papyrus composition and density are not measured here: C 0.70, O 0.25, H 0.05 by mass, density
  0.4 / 0.8 / 1.2 g/cm3 bracket the plausible range; all results are given for the three densities.
"""
import json
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

scr, repo = sys.argv[1], sys.argv[2]
DATA = os.path.join(repo, "data/sib/p4-highz")
Z = {"H": 1, "C": 6, "N": 7, "O": 8, "Al": 13, "As": 33, "Br": 35, "Si": 14, "S": 16, "Ca": 20, "Fe": 26, "Cu": 29, "Au": 79, "Hg": 80, "Pb": 82}
AW = {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999, "Al": 26.982, "As": 74.922, "Br": 79.904, "Si": 28.085, "S": 32.06, "Ca": 40.078, "Fe": 55.845, "Cu": 63.546,
      "Au": 196.967, "Hg": 200.59, "Pb": 207.2}


def table(el):
    t = open(os.path.join(DATA, f"nist_z{Z[el]:02d}.html"), errors="ignore").read()
    rows = re.findall(r"(\d\.\d+E[-+]\d+)\s+(\d\.\d+E[-+]\d+)\s+(\d\.\d+E[-+]\d+)", t)
    return np.array([[float(a), float(b)] for a, b, _ in rows])  # MeV, mu/rho cm2/g


def mu_rho(el, keV):
    a = table(el)
    e = keV / 1000.0
    # interpolate log-log on the side of any absorption edge that contains e
    i = np.searchsorted(a[:, 0], e)
    lo, hi = a[i - 1], a[i]
    if lo[0] == e:
        return float(lo[1])
    return float(np.exp(np.interp(np.log(e), [np.log(lo[0]), np.log(hi[0])], [np.log(lo[1]), np.log(hi[1])])))


def formula_mass(f):
    tot = sum(AW[e] * n for e, n in f.items())
    return {e: AW[e] * n / tot for e, n in f.items()}


PIG = {  # name: (mass fractions, density g/cm3, note)
    "Au (gold leaf / shell gold)": (formula_mass({"Au": 1}), 19.3, "inert; leaf is sub-micron"),
    "HgS (cinnabar / vermilion)": (formula_mass({"Hg": 1, "S": 1}), 8.1, "stable at 300-400 C"),
    "Pb3O4 (red lead / minium)": (formula_mass({"Pb": 3, "O": 4}), 8.9, "-> PbO above ~500 C"),
    "PbO (litharge / massicot)": (formula_mass({"Pb": 1, "O": 1}), 9.5, ""),
    "CuO (from azurite / malachite)": (formula_mass({"Cu": 1, "O": 1}), 6.3, "decomposition product"),
    "CaCuSi4O10 (Egyptian blue)": (formula_mass({"Ca": 1, "Cu": 1, "Si": 4, "O": 10}), 3.07, "stable to ~1000 C"),
    "Fe2O3 (red ochre / hematite)": (formula_mass({"Fe": 2, "O": 3}), 5.24, "weak"),
    "carbon ink (soot)": (formula_mass({"C": 1}), 1.8, "reference: black ink"),
}


def mix(parts):
    """mass-weighted mixture of mass-fraction dicts: [(weight, fracs), ...]"""
    out = {}
    for w, f in parts:
        for e, v in f.items():
            out[e] = out.get(e, 0) + w * v
    return out


# DECL-P4-16 item 2 extension classes (panel_ext). Densities are assumptions where marked; dye loadings 10 % by mass.
DBI = lambda br: formula_mass({"C": 16, "H": 10 - br, "Br": br, "N": 2, "O": 2})  # 6,6'-dibromoindigo, Br atoms 2 -> br
INDIGO = formula_mass({"C": 16, "H": 10, "N": 2, "O": 2})
PIG_EXT = {
    "Br: Tyrian purple, 0 % Br loss": (DBI(2), 1.7, "density assumed 1.7 (indigo 1.35-1.5; no measured value used)"),
    "Br: Tyrian purple, 50 % Br loss": (DBI(1), 1.55, "Br 2 -> 1 atom (H substituted); density assumed"),
    "Br: Tyrian purple, 90 % Br loss": (DBI(0.2), 1.4, "Br 2 -> 0.2 atom; density assumed"),
    "Ca: purpurissum (10 % dibromoindigo on CaCO3)": (mix([(0.9, formula_mass({"Ca": 1, "C": 1, "O": 3})), (0.1, DBI(2))]), 2.5, "chalk carrier; density assumed 2.5 (calcite 2.71)"),
    "Al: alumina lake (10 % dye on Al(OH)3)": (mix([(0.9, formula_mass({"Al": 1, "O": 3, "H": 3})), (0.1, INDIGO)]), 2.2, "gibbsite 2.42; density assumed 2.2"),
    "S: gypsum lake (10 % dye on CaSO4.2H2O)": (mix([(0.9, formula_mass({"Ca": 1, "S": 1, "O": 6, "H": 4})), (0.1, INDIGO)]), 2.1, "gypsum 2.32; density assumed 2.1"),
    "As: orpiment As2S3": (formula_mass({"As": 2, "S": 3}), 3.49, ""),
    "As: realgar As4S4": (formula_mass({"As": 4, "S": 4}), 3.56, ""),
}
if os.environ.get("HZ_PANEL_EXT"):
    PIG.update(PIG_EXT)
PAP = {"C": 0.70, "O": 0.25, "H": 0.05}


def mu_lin(frac, rho, keV):
    return rho * sum(w * mu_rho(e, keV) for e, w in frac.items())


def modes(h):
    hs = np.convolve(h.astype(float), np.ones(9) / 9, "same")
    hs[0] = 0
    gv = int(np.argmax(hs[1:75])) + 1
    gp = int(np.argmax(hs[80:220])) + 80
    return gv, gp


out = {"provenance": C.PROV, "serves": "orchestrator addenda to DECL-P4-6-A1/A2 and DECL-P4-12 (pigment physics; numbers only)",
       "source": "NIST XCOM / X-ray mass attenuation coefficients (Hubbell & Seltzer, NISTIR 5632), element tables stored "
                 "as data/sib/p4-highz/nist_zNN.html; compounds by the mixture rule",
       "papyrus_model": {"mass_fractions": PAP, "densities_g_cm3": [0.4, 0.8, 1.2]},
       "model": __doc__.split("Model (stated, approximate):")[1].strip(), "materials": {}}
for mat, thf, keV in (("C", "thresholds.json", 78.0), ("C2", "thresholds_2p4.json", 78.0)):
    p = os.path.join(scr, f"stage_a_{mat}.npz")
    tp = os.path.join(repo, "logs/sib/p4-highz", thf)
    if not (os.path.exists(p) and os.path.exists(tp)):
        continue
    H = np.load(p)["H"].sum(0)
    gv, gp = modes(H[0] + H[1] + H[2])
    T_hi = json.load(open(tp))["T_hi"]
    vox = C.MATERIALS[mat]["um"]
    res = {"voxel_um": vox, "energy_keV": keV, "g_void_mode": gv, "g_papyrus_mode": gp, "T_hi": T_hi, "pigments": {}}
    for name, (frac, rho, note) in PIG.items():
        mp = mu_lin(frac, rho, keV)
        row = {"mu_cm-1": mp, "density": rho, "note": note, "by_papyrus_density": {}}
        for rp in (0.4, 0.8, 1.2):
            mpap = mu_lin(PAP, rp, keV)
            ratio = mp / mpap
            g = gv + (gp - gv) * ratio
            f = (T_hi - gp) / (g - gp) if g > gp else None
            row["by_papyrus_density"][str(rp)] = {
                "mu_pap_cm-1": mpap, "mu_ratio_pigment_over_papyrus": ratio, "grey_full_voxel_unclipped": g,
                "full_voxel_exceeds_T_hi": bool(g > T_hi),
                "min_fill_fraction": (f if f is not None and f <= 1 else None),
                "t_min_um_ideal": (f * vox if f is not None and f <= 1 else None),
                "t_min_um_with_2vox_blur_x2": (2 * f * vox if f is not None and f <= 1 else None)}
        res["pigments"][name] = row
    out["materials"][mat] = res
# K-edge context: mu/rho just below/above the edges and at the other scan energies
out["mu_rho_cm2_g"] = {el: {str(k): mu_rho(el, k) for k in (74.0, 78.0, 110.0, 137.0)} for el in ("Au", "Hg", "Pb", "Cu", "Fe", "C") + (("Br", "As", "Ca", "Al", "S") if os.environ.get("HZ_PANEL_EXT") else ())}
out["k_edges"] = {"Au": 80.7, "Hg": 83.1, "Pb": 88.0}
out["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(out, open(os.path.join(repo, "logs/sib/p4-highz/" + ("pigments_ext.json" if os.environ.get("HZ_PANEL_EXT") else "pigments.json")), "w"), indent=1)
for mat, r in out["materials"].items():
    print(mat, r["voxel_um"], "modes", r["g_void_mode"], r["g_papyrus_mode"], "T_hi", r["T_hi"])
    for n, row in r["pigments"].items():
        b = row["by_papyrus_density"]
        print(f"  {n:34s} mu {row['mu_cm-1']:8.2f} ratio(0.8) {b['0.8']['mu_ratio_pigment_over_papyrus']:7.1f} "
              f"tmin um (0.4/0.8/1.2): " + " / ".join(str(None if b[k]['t_min_um_ideal'] is None else round(b[k]['t_min_um_ideal'], 3)) for k in ('0.4', '0.8', '1.2')))
print(json.dumps(out["mu_rho_cm2_g"]))
