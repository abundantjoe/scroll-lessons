"""p4-highz DECL-P4-16 item 2: aggregate the extended injection-recovery panel (control only) into panel_ext.json.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python panel_ext.py <repo> <material> (reads logs/sib/p4-highz/inject_<material>_o<o>_ext.json)
"""
import json
import os
import sys
import time

repo, mat = sys.argv[1], sys.argv[2]
d = os.path.join(repo, "logs/sib/p4-highz")
OFFS = [-60, -45, -30, -15, 0, 15, 30, 45, 60]
runs = {o: json.load(open(os.path.join(d, f"inject_{mat}_o{o}_ext.json"))) for o in OFFS
        if os.path.exists(os.path.join(d, f"inject_{mat}_o{o}_ext.json"))}
pig = json.load(open(os.path.join(d, "pigments_ext.json")))["materials"][mat]
table = {}
for o, r in runs.items():
    for p, res in r["results"].items():
        table.setdefault(p, {})[str(o)] = {s: res[s]["detection_limit_um_recovery_ge_0p8"] for s in ("sigma_0.0", "sigma_1.0")}
out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
       "serves": "RULES.md DECL-P4-16 item 2 (control strip only; no title-strip number)",
       "material": mat, "segment": next(iter(runs.values()))["segment"] if runs else None,
       "attenuation_source": "NIST X-ray mass attenuation tables (Hubbell & Seltzer) via pigments.py (pigments_ext.json); "
                             "p4-purple colourants.json not available when computed; densities marked 'assumed' are assumptions",
       "method": "inject.py unchanged (DECL-P4-6 panel): 20 real control regions per offset, H glyph 3 x 2 mm stroke 0.4 mm, "
                 "layer lower face at centre + offset, linear grey model (papyrus 0.8 g/cm3), letter-scale criterion, recovery >= 0.8; "
                 "offset 0 = the +-15 um slab; thickness grid 0.01-20 um (None = not detected at 20 um)",
       "offsets_um": sorted(runs), "false_positives_no_injection": {str(o): sum(r["false_positive_letter_components_no_injection"]) for o, r in runs.items()},
       "mu_cm-1_78keV": {p: v["mu_cm-1"] for p, v in pig["pigments"].items()},
       "mu_ratio_to_papyrus_0p8": {p: v["by_papyrus_density"]["0.8"]["mu_ratio_pigment_over_papyrus"] for p, v in pig["pigments"].items()},
       "detection_limit_um": table,
       "caveat": "linear-grey model is optimistic: the control's real carbon ink (10-20 um per Angelotti et al.) is not detected by this "
                 "criterion, so real limits may be higher by up to ~(mu_ink x 20 um)/(mu_class) (REPORT.md section 5)",
       "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump(out, open(os.path.join(d, "panel_ext.json"), "w"), indent=1)
for p, v in table.items():
    print(f"{p:48s}", " ".join(f"{o}:{v[o]['sigma_1.0']}" for o in sorted(v, key=int)))
