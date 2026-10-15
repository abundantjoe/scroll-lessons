"""p4-purple: predicted CT detectability of title colourants on carbonised papyrus (RULES.md DECL-P4-16 item 1).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python colourants.py <repo>        (writes logs/sib/p4-purple/colourants.json)

Numbers only. No CT voxel is read: the scan parameters come from the published metadata.json of the two volumes
(sha256 recorded below) and the noise from p4-highz's pushed control statistics (not re-measured).

Physics source: xraylib 4.3.0 (Schoonjans et al., Spectrochim. Acta B 66 (2011) 776; data: EPDL97 photoionisation,
Compton and Rayleigh cross sections; anomalous scattering factors for delta). mu = rho * CS_Total_CP (photo +
Compton + Rayleigh), delta = 1 - Refractive_Index_Re. Mixtures by the mixture rule (mu and delta are linear in the
partial densities).

Contrast model (1-D profile along the sheet normal; stated, approximate):
- A colourant layer of thickness t lies ON the papyrus surface (a deposit), displacing void. The with-minus-without
  difference is then a slab of (mu_L, delta_L) over [0, t]; the papyrus edge cancels in the difference (linear model).
- Layer = paint: pigment/dye volume fraction PHI = 0.5 in a binder; the binder is carbonised organic matter with the
  papyrus composition at 1.0 g/cm3. PHI = 1 (solid layer) is also reported.
- (i) Absorption value: slab * system PSF (Gaussian, sigma 1 voxel; 0.5 and 1.5 voxel as sensitivity) * voxel box.
- (ii) Paganin value, the published pipeline of each volume (metadata.json): single-material Paganin with
  delta/beta_a, propagation z, then a Gaussian unsharp mask on the projections, then GHBP. In the linear (weak
  object, TIE) regime and for an object much wider than its thickness, the reconstructed volume is
      mu_r(k) = [mu^(k) + z k^2 delta^(k)] / (1 + z c k^2) * U(k) * PSF(k),   c = (delta/beta)_a * lambda / (4 pi),
      U(k) = 1 + coeff * (1 - exp(-k^2 s^2 / 2)),
  with k the angular spatial frequency along the normal. For a material whose own delta/beta equals the assumed one,
  the bracket is exactly mu (no loss). Heavier materials (delta/beta << 1000) lose their high-frequency part and
  their peak is spread; lighter ones gain.
- The voxel value is the box average over 2.4 um; peak = mean over sub-voxel phases of the maximum voxel (typical),
  and the best phase.
- Grey scale: the uint8 export maps the float window [f_min, f_max] (metadata zarr_export) to 0..255. The float
  unit is taken as cm^-1. Check: the control void mode (grey 42) maps to 0.003 cm^-1 (~0, as void must) and the
  papyrus mode (grey 112) to 0.074 cm^-1, i.e. carbonised papyrus of about 0.43 g/cm3 with the assumed composition,
  inside the 0.3-1.0 range. No other unit gives a physical density.
- Noise: p4-highz C2 control (20260701183125-w028-037, 2.4 um, in-sheet slab +-15 um), percentiles p50 90, p99 158
  grey. Gaussian-equivalent sigma = (p99 - p50) / 2.326 = 29.2 grey. It includes papyrus texture and grains, not only
  photon noise, so the per-voxel CNR = contrast / 29.2 is conservative. p99.9 = 203 > the Gaussian 180: heavy tail.
- Not modelled: 3-D letter edges, beam hardening (monochromatic beam), scatter, non-linear Paganin at thick heavy
  layers (mu*t up to 0.09 for 20 um solid gold: still < 0.1, linear regime acceptable), chemical change of the
  colourant during carbonisation other than the stated Br-loss and binder cases.
"""
import hashlib
import json
import os
import sys
import time

import numpy as np
import xraylib as xr

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
repo = sys.argv[1] if len(sys.argv) > 1 else "."

# --- published scan / reconstruction parameters (metadata.json of each volume; fetched 2026-09-26) ---
SCANS = {
    "78": {"volume": "20260411134726-2.400um-0.2m-78keV-masked", "E_keV": 78.0, "voxel_um": 2.4, "z_m": 0.220,
           "delta_beta": 1000.0, "unsharp_coeff": 4.0, "unsharp_sigma_px": 1.2, "f32_window": [-0.04, 0.22],
           "metadata_sha256": "881bf77fc0f02a91040755da25d54ad958e290a528ec61489e411937112fba4d"},
    "137": {"volume": "20260323153942-2.400um-0.2m-137keV-masked", "E_keV": 137.0, "voxel_um": 2.4, "z_m": 0.220,
            "delta_beta": 2000.0, "unsharp_coeff": 5.0, "unsharp_sigma_px": 2.5, "f32_window": [0.01, 0.16],
            "metadata_sha256": "26792eb8a448ed37e0835effd920552ffd3a182b584b20e8a88a5c1d37981740"},
}
NOISE = {"source": "origin/claude/gifted-bell-gavnl5-sib-p4-highz logs/sib/p4-highz/physics_2p4.json, "
                   "materials.C2.sheet_slab.excl_zero (control 20260701183125-w028-037, 2.4 um, 78 keV)",
         "p50": 90, "p99": 158, "p99.9": 203, "void_mode": 42, "papyrus_mode": 112,
         "modes_source": "logs/sib/p4-highz/pigments.json materials.C2 / REPORT.md section 5"}
NOISE["sigma_grey"] = (NOISE["p99"] - NOISE["p50"]) / 2.326

PAP = [("C", 0.70), ("O", 0.25), ("H", 0.05)]           # carbonised papyrus (p4-highz model), by mass
PAP_RHO = [0.3, 0.43, 0.5, 0.7, 1.0]                    # 0.43 = implied by the grey calibration (see docstring)
BINDER = (PAP, 1.0)                                     # carbonised gum binder proxy
PHI = 0.5
THICK = [5.0, 10.0, 20.0]


def f(formula):
    return [(formula, 1.0)]


def mix(*parts):
    return list(parts)


def tyrian(loss):
    br, h = 2 * (1 - loss), 8 + 2 * loss                # debromination replaces Br by H
    m0 = xr.CompoundParser("C16H8Br2N2O2")["molarMass"]
    fm = f"C16H{h:g}Br{br:g}N2O2" if br > 0 else "C16H10N2O2"
    m1 = xr.CompoundParser(fm)["molarMass"]
    return f(fm), 2.0 * m1 / m0                          # constant molar volume


# name: (class, components [(formula, mass fraction)], solid density g/cm3, density note, chemistry note)
MAT = {}
for loss in (0.0, 0.5, 0.9):
    comp, rho = tyrian(loss)
    MAT[f"Tyrian purple, {int(loss*100)} % Br loss"] = (
        "purple (Br)", comp, rho,
        "6,6'-dibromoindigo 2.0 g/cm3 estimated (indigo 1.35 scaled by molar mass at constant molar volume = 2.16, "
        "less for the larger Br); Br-loss variants at constant molar volume",
        "38.0 wt% Br intact; sublimes/decomposes near 390 C; carbonisation fate of Br unknown")
MAT["purpurissum (5 wt% Tyrian dye on CaCO3)"] = (
    "purple lake (Ca)", mix(("CaCO3", 0.95), ("C16H8Br2N2O2", 0.05)), 2.65,
    "calcite 2.71 and dye 2.0 by volume mixing", "Pliny NH 35.44-45 (dye on creta argentaria); dye fraction assumed 5 wt%; CaCO3 stable < ~600 C")
MAT["purpurissum, dye fully lost (CaCO3 carrier only)"] = (
    "purple lake (Ca)", f("CaCO3"), 2.71, "calcite", "worst case for the dye, carrier survives")
MAT["alumina lake (10 wt% alizarin on Al(OH)3)"] = (
    "lake (Al)", mix(("AlO3H3", 0.90), ("C14H8O4", 0.10)), 2.33, "gibbsite 2.42, alizarin 1.54",
    "Al(OH)3 dehydrates towards boehmite/Al2O3 above ~250-300 C (denser); not modelled")
MAT["gypsum lake (10 wt% alizarin on CaSO4.2H2O)"] = (
    "lake (Ca,S)", mix(("CaSO6H4", 0.90), ("C14H8O4", 0.10)), 2.23, "gypsum 2.32, alizarin 1.54",
    "gypsum -> bassanite/anhydrite above ~150 C (denser); not modelled")
MAT["orchil / orcein (lichen purple)"] = ("organic dye", f("C28H24N2O7"), 1.4, "assumed 1.4 (no crystal density)",
                                           "representative orcein formula; carbonises")
MAT["kermes (kermesic acid)"] = ("organic dye", f("C16H10O8"), 1.6, "assumed 1.6", "carbonises")
MAT["madder (alizarin)"] = ("organic dye", f("C14H8O4"), 1.54, "alizarin", "carbonises")
MAT["indigo"] = ("organic dye", f("C16H10N2O2"), 1.35, "indigo (reported 1.2-1.35)", "carbonises")
MAT["orpiment As2S3"] = ("mineral (As)", f("As2S3"), 3.49, "mineral", "volatile/oxidises > ~300 C in air; reducing burial unknown")
MAT["realgar As4S4"] = ("mineral (As)", f("As4S4"), 3.56, "mineral", "as orpiment")
MAT["lead white (hydrocerussite)"] = ("mineral (Pb)", f("Pb3C2O8H2"), 6.8, "mineral", "-> PbO above ~300-400 C (denser)")
MAT["verdigris (neutral, Cu acetate hydrate)"] = ("mineral (Cu)", f("CuC4H8O5"), 1.88, "", "decomposes ~240 C to Cu/Cu2O/CuO + carbon")
MAT["malachite"] = ("mineral (Cu)", f("Cu2CO5H2"), 4.0, "mineral", "-> CuO above ~350 C")
MAT["cinnabar HgS"] = ("mineral (Hg)", f("HgS"), 8.1, "mineral", "stable at 300-400 C")
MAT["minium Pb3O4"] = ("mineral (Pb)", f("Pb3O4"), 8.9, "mineral", "-> PbO above ~500 C")
MAT["red ochre (hematite Fe2O3)"] = ("mineral (Fe)", f("Fe2O3"), 5.26, "mineral", "stable")
MAT["yellow ochre (goethite FeOOH)"] = ("mineral (Fe)", f("FeO2H"), 4.27, "mineral", "-> hematite above ~300 C")
MAT["Egyptian blue CaCuSi4O10"] = ("mineral (Cu,Ca)", f("CaCuSi4O10"), 3.07, "mineral", "stable to ~1000 C")
MAT["gold"] = ("metal (Au)", f("Au"), 19.3, "metal", "inert; leaf is sub-micron (use t << 5 um)")
MAT["carbon ink (soot)"] = ("carbon ink", f("C"), 1.8, "carbon black 1.8-2.1", "reference: the body-text ink")
MAT["carbon ink + 2 wt% Pb (as PbO)"] = ("carbon ink (Pb)", mix(("C", 0.9785), ("PbO", 0.0215)), 1.83, "", "Pb in Herculaneum ink reported (Brun et al., PNAS 2016); fraction assumed")
MAT["carbon ink + 10 wt% Pb (as PbO)"] = ("carbon ink (Pb)", mix(("C", 0.8923), ("PbO", 0.1077)), 1.97, "", "upper scenario")


def optics(comp, rho, E):
    """mu (cm^-1), delta, beta of a mixture at density rho."""
    mu = delta = beta = 0.0
    for fm, w in comp:
        mu += rho * w * xr.CS_Total_CP(fm, E)
        delta += 1 - xr.Refractive_Index_Re(fm, E, rho * w)
        beta += xr.Refractive_Index_Im(fm, E, rho * w)
    return mu, delta, beta


def layer_optics(comp, rho, E, phi):
    a = optics(comp, rho, E)
    b = optics(*BINDER, E)
    return tuple(phi * p + (1 - phi) * q for p, q in zip(a, b))


# --- 1-D response ---
DX = 0.05                                   # um
N = 1 << 16                                 # 3.3 mm domain
xg = (np.arange(N) - N // 2) * DX
kk = 2 * np.pi * np.fft.fftfreq(N, d=DX)    # rad/um


def response(mu_cm, delta, t_um, scan, psf_px=1.0, paganin=True):
    """Peak voxel value (cm^-1) of the reconstructed difference profile. Returns (typical, best)."""
    s = SCANS[scan]
    vox = s["voxel_um"]
    lam_um = 12.398419843 / s["E_keV"] * 1e-4          # Angstrom -> um
    mu = mu_cm * 1e-4                                   # 1/um
    slab = ((xg >= 0) & (xg < t_um)).astype(float)
    F = np.fft.fft(np.fft.ifftshift(slab))
    H = np.exp(-0.5 * (kk * psf_px * vox) ** 2)
    if paganin:
        z = s["z_m"] * 1e6
        c = s["delta_beta"] * lam_um / (4 * np.pi)
        sg = s["unsharp_sigma_px"] * vox
        U = 1 + s["unsharp_coeff"] * (1 - np.exp(-0.5 * (kk * sg) ** 2))
        G = (mu + z * kk ** 2 * delta) / (1 + z * c * kk ** 2) * U * H
    else:
        G = mu * H
    prof = np.real(np.fft.fftshift(np.fft.ifft(F * G)))          # 1/um
    nb = int(round(vox / DX))
    box = np.convolve(prof, np.ones(nb) / nb, mode="same")       # voxel average at every phase
    peaks = []
    for ph in range(nb):                                         # sample grid phase
        v = box[ph::nb]
        peaks.append(v.max())
    peaks = np.array(peaks) * 1e4                                # cm^-1
    return float(peaks.mean()), float(peaks.max()), float(box.min() * 1e4)


def grey_per_cm(scan):
    lo, hi = SCANS[scan]["f32_window"]
    return 255.0 / (hi - lo)


DE = {"papyrus_rho": 0.43, "papyrus_column_um": [50.0, 100.0], "depth_window_um": 100.0, "patch_mm": 0.2,
      "sigma_vox_cm-1": {"78": None, "137": None},
      "note": "The Paganin/unsharp/PSF chain has unit gain at k = 0, so the depth-integrated retrieved value equals "
              "mu*t at both energies and the column ratio carries the true mu ratio; peak values do not (thin layers "
              "are dominated by delta, whose 137/78 ratio is ~(78/137)^2 for every material). Noise: 78 keV sigma "
              "29.2 grey = 0.0298 cm^-1 (p4-highz control); 137 keV sigma NOT MEASURED, assumed the same 29.2 grey "
              "= 0.0172 cm^-1 (window 0.15 cm^-1); voxel noise assumed independent (optimistic; papyrus texture is "
              "common to both energies and cancels in the ratio, photon noise does not). CNR_DE is an upper bound."}


def column_ratio(pr, t):
    out = {}
    for E in ("78", "137"):
        lo, hi = SCANS[E]["f32_window"]
        DE["sigma_vox_cm-1"][E] = NOISE["sigma_grey"] * (hi - lo) / 255.0
    vox = SCANS["78"]["voxel_um"]
    nd = DE["depth_window_um"] / vox
    na = (DE["patch_mm"] * 1000 / vox) ** 2
    for tp in DE["papyrus_column_um"]:
        mp = {E: optics(PAP, DE["papyrus_rho"], float(E))[0] for E in ("78", "137")}
        col = {E: (mp[E] * tp + pr[E]["mu_cm-1"] * t) * 1e-4 for E in ("78", "137")}        # dimensionless mu*L
        R0 = mp["137"] / mp["78"]
        R = col["137"] / col["78"]
        sc = {E: DE["sigma_vox_cm-1"][E] * 1e-4 * vox * np.sqrt(nd) / np.sqrt(na) for E in ("78", "137")}
        sR = R * np.sqrt((sc["78"] / col["78"]) ** 2 + (sc["137"] / col["137"]) ** 2)
        # Paganin smoothing length sqrt(z c) at 78 keV correlates voxel noise; N_eff reduced by (L/vox)^3
        lam = 12.398419843 / 78.0 * 1e-4
        L = np.sqrt(SCANS["78"]["z_m"] * 1e6 * SCANS["78"]["delta_beta"] * lam / (4 * np.pi))
        corr = max(1.0, L / vox) ** 1.5
        out[str(int(tp))] = {"R_papyrus": R0, "R_column": R, "delta_R": R - R0, "sigma_R_patch": sR,
                             "CNR_DE_patch_upper": (R - R0) / sR,
                             "paganin_length_um": L, "CNR_DE_patch_correlated": (R - R0) / sR / corr}
    return out


def self_test():
    """Checks: (1) matched delta/beta and no unsharp/PSF -> Paganin returns the absorption slab exactly;
    (2) thick layer (200 um) plateau equals mu; (3) grey calibration of the control modes."""
    out = {}
    s = SCANS["78"]
    lam_um = 12.398419843 / 78 * 1e-4
    mu = 1.0
    delta = s["delta_beta"] * mu * 1e-4 * lam_um / (4 * np.pi)
    saved = s["unsharp_coeff"]
    s["unsharp_coeff"] = 0.0
    a = response(mu, delta, 10.0, "78", psf_px=1e-6, paganin=True)
    b = response(mu, 0.0, 10.0, "78", psf_px=1e-6, paganin=False)
    s["unsharp_coeff"] = saved
    out["matched_paganin_equals_absorption"] = {"paganin": a[0], "absorption": b[0], "ok": abs(a[0] - b[0]) < 1e-6}
    c = response(1.0, 0.0, 200.0, "78", psf_px=1.0, paganin=False)
    out["thick_plateau_mu1"] = {"value": c[0], "ok": abs(c[0] - 1.0) < 1e-3}
    lo, hi = s["f32_window"]
    fv = lo + NOISE["void_mode"] / 255 * (hi - lo)
    fp = lo + NOISE["papyrus_mode"] / 255 * (hi - lo)
    mup = optics(PAP, 1.0, 78.0)[0]
    out["grey_calibration"] = {"void_mode_cm-1": fv, "papyrus_mode_cm-1": fp,
                               "papyrus_mu_rho_78keV_cm2_g": mup, "implied_papyrus_density_g_cm3": fp / mup}
    return out


def main():
    st = self_test()
    assert st["matched_paganin_equals_absorption"]["ok"] and st["thick_plateau_mu1"]["ok"], st
    sig = NOISE["sigma_grey"]
    pap = {r: {E: optics(PAP, float(r), float(E))[0] for E in ("78", "137")} for r in map(str, PAP_RHO)}
    rows = {}
    for name, (cls, comp, rho, dn, cn) in MAT.items():
        row = {"class": cls, "components_mass_fraction": comp, "solid_density_g_cm3": round(rho, 4),
               "density_note": dn, "chemistry_note": cn, "phi": {}}
        for phi in (PHI, 1.0):
            pr = {}
            for E in ("78", "137"):
                mu, de, be = layer_optics(comp, rho, float(E), phi)
                pr[E] = {"mu_cm-1": mu, "delta": de, "beta": be, "delta_over_beta": de / be,
                         "mu_ratio_to_papyrus": {r: mu / pap[r][E] for r in pap}}
            b = BINDER[1] * (1 - phi)
            pr["layer_density_g_cm3"] = phi * rho + b
            pr["areal_density_mg_cm2_per_um"] = (phi * rho + b) * 1e-4 * 1e3
            pr["R_mu137_over_mu78"] = pr["137"]["mu_cm-1"] / pr["78"]["mu_cm-1"]
            th = {}
            for t in THICK:
                d = {}
                for E in ("78", "137"):
                    mu, de = pr[E]["mu_cm-1"], pr[E]["delta"]
                    ab = response(mu, de, t, E, paganin=False)
                    pg = response(mu, de, t, E, paganin=True)
                    gpc = grey_per_cm(E)
                    e = {"absorption_peak_cm-1": ab[0], "paganin_peak_cm-1": pg[0], "paganin_peak_best_phase_cm-1": pg[1],
                         "paganin_undershoot_cm-1": pg[2],
                         "absorption_grey": ab[0] * gpc, "paganin_grey": pg[0] * gpc,
                         "mu_t": mu * t * 1e-4,
                         "paganin_peak_over_papyrus_mu": {r: pg[0] / pap[r][E] for r in pap}}
                    e["saturates_uint8_over_void"] = bool(NOISE["void_mode"] + pg[0] * gpc > 255)
                    if E == "78":
                        e["CNR_vox_absorption"] = ab[0] * gpc / sig
                        e["CNR_vox_paganin"] = pg[0] * gpc / sig
                        e["psf_sensitivity_paganin_grey"] = {str(p): response(mu, de, t, E, psf_px=p)[0] * gpc for p in (0.5, 1.5)}
                    d[E] = e
                th[str(int(t))] = d
            for t in th:
                th[t]["paganin_peak_ratio_137_over_78"] = th[t]["137"]["paganin_peak_cm-1"] / th[t]["78"]["paganin_peak_cm-1"]
                th[t]["dual_energy_column"] = column_ratio(pr, float(t))
            pr["thickness_um"] = th
            # detection limit: thinnest deposit giving per-voxel CNR 3 at 78 keV (Paganin chain), and absorption-only
            for key, pg in (("t_um_CNR3_paganin_78", True), ("t_um_CNR3_absorption_78", False)):
                mu, de = pr["78"]["mu_cm-1"], pr["78"]["delta"]
                g = lambda t: response(mu, de, t, "78", paganin=pg)[0] * grey_per_cm("78") / NOISE["sigma_grey"] - 3.0
                lo_t, hi_t = 0.01, 40.0
                if g(hi_t) < 0:
                    pr[key] = None
                elif g(lo_t) > 0:
                    pr[key] = lo_t
                else:
                    for _ in range(40):
                        m_t = 0.5 * (lo_t + hi_t)
                        lo_t, hi_t = (lo_t, m_t) if g(m_t) > 0 else (m_t, hi_t)
                    pr[key] = hi_t
            row["phi"][str(phi)] = pr
        rows[name] = row
    # detectability vs carbon ink (the body-text ink that the organizers see as deposits in this volume)
    ref = rows["carbon ink (soot)"]["phi"][str(PHI)]["thickness_um"]
    for name, row in rows.items():
        for t in map(lambda v: str(int(v)), THICK):
            e = row["phi"][str(PHI)]["thickness_um"][t]["78"]
            e["paganin_contrast_ratio_to_carbon_ink_same_t"] = e["paganin_peak_cm-1"] / ref[t]["78"]["paganin_peak_cm-1"]
    srcs = {}
    for p in [__file__]:
        srcs[os.path.relpath(p, repo)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    out = {"provenance": PROV,
           "serves": "RULES.md DECL-P4-16 item 1 (predicted detectability table; numbers only)",
           "physics_source": f"xraylib {xr.__version__} (Schoonjans et al. 2011; EPDL97 cross sections, anomalous "
                             "scattering factors). mu = rho*CS_Total_CP; delta = 1 - Refractive_Index_Re.",
           "model": __doc__.split("Contrast model")[1].strip(),
           "scans": SCANS, "noise": NOISE, "phi_primary": PHI, "binder": {"composition": PAP, "density": 1.0},
           "papyrus": {"composition": PAP, "mu_cm-1": pap}, "dual_energy_model": DE, "self_test": st, "materials": rows,
           "tool_sha256": srcs, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    p = os.path.join(repo, "logs/sib/p4-purple/colourants.json")
    json.dump(out, open(p, "w"), indent=1, default=float)
    print(json.dumps(st, indent=1))
    print(f"{'material':48s} {'Rpk10':>5s} {'dRcol':>6s} {'CNRde':>6s} {'R137/78':>7s} {'d/b78':>6s} | 10um: {'abs g':>6s} {'pag g':>6s} {'CNRpag':>6s} {'xCink':>5s} | 5um CNR 20um CNR")
    for name, row in rows.items():
        pr = row["phi"][str(PHI)]
        e = {t: pr["thickness_um"][t]["78"] for t in ("5", "10", "20")}
        dc = pr["thickness_um"]["10"]["dual_energy_column"]["100"]
        print(f"{name:48s} {pr['thickness_um']['10']['paganin_peak_ratio_137_over_78']:5.2f} {dc['delta_R']:6.3f} {dc['CNR_DE_patch_correlated']:6.1f} {pr['R_mu137_over_mu78']:7.3f} {pr['78']['delta_over_beta']:6.0f} | "
              f"{e['10']['absorption_grey']:6.1f} {e['10']['paganin_grey']:6.1f} {e['10']['CNR_vox_paganin']:6.2f} "
              f"{e['10']['paganin_contrast_ratio_to_carbon_ink_same_t']:5.1f} | {e['5']['CNR_vox_paganin']:6.2f} {e['20']['CNR_vox_paganin']:6.2f}")


if __name__ == "__main__":
    main()
