"""p4-pig-red: tabulated mass attenuation (xraylib 4.x, Schoonjans et al. 2011, Spectrochim. Acta B 66:776;
photon cross sections from the EPDL97/Scofield/Hubbell compilations that also underlie NIST XCOM).
Provenance: Project HERCULES | owner the owner | [id removed]. Numbers only."""
import json, sys
import xraylib as x
E = [74.0, 78.0, 83.0, 83.2, 87.9, 88.1, 110.0, 137.0]
MAT = {  # formula, density g/cm3 (handbook values; cited in MEMO.md)
 "HgS_cinnabar": ("HgS", 8.10), "HgS_metacinnabar": ("HgS", 7.71),
 "Pb3O4_red_lead": ("Pb3O4", 8.92), "PbO_litharge": ("PbO", 9.53), "Pb_metal": ("Pb", 11.34),
 "Hg_metal_liquid": ("Hg", 13.53), "Fe2O3_hematite_ref": ("Fe2O3", 5.26),
 "cellulose_C6H10O5": ("C6H10O5", 1.50), "char_C70O25H5_massfrac": (None, 1.0), "graphite_C": ("C", 2.0),
}
def mu_rho(key, e):
    f = MAT[key][0]
    if f is None:  # carbonised papyrus proxy, mass fractions C .70 O .25 H .05
        return .70 * x.CS_Total(6, e) + .25 * x.CS_Total(8, e) + .05 * x.CS_Total(1, e)
    return x.CS_Total_CP(f, e)
out = {"source": "xraylib %s CS_Total_CP (coherent+incoherent+photoelectric), cm2/g" % x.__version__,
       "edges_keV": {"Hg_K": x.EdgeEnergy(80, x.K_SHELL), "Pb_K": x.EdgeEnergy(82, x.K_SHELL), "Au_K": x.EdgeEnergy(79, x.K_SHELL)},
       "mu_rho_cm2_g": {k: {str(e): round(mu_rho(k, e), 5) for e in E} for k in MAT},
       "density_g_cm3": {k: v[1] for k, v in MAT.items()}}
out["mu_lin_per_cm_at_density"] = {k: {str(e): round(mu_rho(k, e) * MAT[k][1], 4) for e in E} for k in MAT if MAT[k][1]}
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k in MAT: print(k, {e: round(mu_rho(k, e), 3) for e in E})
print(out["edges_keV"])
