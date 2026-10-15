"""Scan inventory and Au K-edge bracketing check for PHerc. Paris 4 (DECL-P4-6-A2 item 2, DECL-P4-10). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

For every published volume: energy, pixel size, Paganin delta/beta, filters, grey window, transform presence (sha256 of
metadata.json and transform.json recorded). For each pair bracketing 80.725 keV: whether both are registered to a
common frame, and the fraction of the w010-027 2.4 um mesh (every 16th vertex of 20260701183124-w010-027) that maps
inside the other volume and onto a non-zero (in-mask) voxel at a coarse level.
Usage: python kedge_inventory.py <scratch> <out.json>
"""
import hashlib
import json
import os
import sys

import numpy as np
import tifffile
import xraylib as X

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold as G  # noqa: E402

VOL = f"{G.BUCKET}/PHercParis4/volumes"
VOLS = ["20260310170716-45.532um-11.0m-74keV-masked.zarr", "20260310173927-45.532um-11.0m-110keV-masked.zarr",
        "20260323153942-2.400um-0.2m-137keV-masked.zarr", "20260411134726-2.400um-0.2m-78keV-masked.zarr",
        "20260608103018-1.129um-0.2m-78keV-masked.zarr"]
EDGES = {"Au": X.EdgeEnergy(79, X.K_SHELL), "Hg": X.EdgeEnergy(80, X.K_SHELL), "Pb": X.EdgeEnergy(82, X.K_SHELL)}
MESH = "PHercParis4/segments/20260701183124-w010-027/mesh/20260701183124-on-20260411134726-2.4um.tifxyz"


def acq(md):
    t = md.get("scan", md).get("tomo", md.get("tomo", {}))
    return t.get("acquisition", {}), t.get("processing", {})


def main():
    scr, outp = sys.argv[1], sys.argv[2]
    inv = {}
    for v in VOLS:
        b = G.get(f"{VOL}/{v}/metadata.json")
        md = json.loads(b)
        a, p = acq(md)
        tb = G.get(f"{VOL}/{v}/transform.json")
        za = json.loads(G.get(f"{VOL}/{v}/0/.zarray"))
        ph = p.get("preprocessing", {}).get("phase", {})
        inv[v] = {"metadata_sha256": hashlib.sha256(b).hexdigest(), "energy_keV": a.get("energy"),
                  "pixel_mm": a.get("detector", {}).get("samplePixelSize"),
                  "sample_detector_mm": a.get("sampleDetectorDistance"),
                  "filters": {k: f"{x.get('type')} {x.get('thickness')}" for k, x in a.get("attenuators", {}).items()
                              if x.get("thickness")},
                  "paganin_delta_beta": ph.get("delta_beta"), "unsharp": [ph.get("unsharp_coeff"), ph.get("unsharp_sigma")],
                  "window_f32": [md["zarr_export"]["target_window_f32_min"], md["zarr_export"]["target_window_f32_max"]],
                  "shape_zyx": za["shape"],
                  "transform": None if tb is None else {"sha256": hashlib.sha256(tb).hexdigest(),
                                                        "fixed_volume": json.loads(tb)["fixed_volume"]}}
        if tb is not None:
            inv[v]["_A"] = json.loads(tb)["transformation_matrix"]
    # mesh sample in 78 keV 2.4 um coords (x, y, z)
    arr = {}
    for a_ in "xyz":
        p = os.path.join(scr, f"e2mesh_{a_}.tif")
        if not os.path.exists(p):
            open(p, "wb").write(G.get(f"{G.BUCKET}/{MESH}/{a_}.tif"))
        arr[a_] = tifffile.imread(p)[::16, ::16].astype(np.float64)
    ok = (arr["x"] != -1) & np.isfinite(arr["x"])
    pts = np.stack([arr["x"][ok], arr["y"][ok], arr["z"][ok]], 1)
    A78 = np.vstack([np.array(inv[VOLS[3]]["_A"]), [0, 0, 0, 1]])
    fixed = (A78[:3, :3] @ pts.T).T + A78[:3, 3]
    pairs = []
    names = list(inv)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            e1, e2 = sorted([inv[names[i]]["energy_keV"], inv[names[j]]["energy_keV"]])
            br = {k: e1 < e < e2 for k, e in EDGES.items()}
            if not any(br.values()):
                continue
            rec = {"pair": [names[i], names[j]], "energies": [e1, e2], "brackets": br}
            # Au mono attenuation ratio high/low vs cellulose (tabulated, xraylib)
            rec["mu_ratio_Au_hi_over_lo"] = X.CS_Total(79, e2) / X.CS_Total(79, e1)
            rec["mu_ratio_cellulose_hi_over_lo"] = X.CS_Total_CP("C6H10O5", e2) / X.CS_Total_CP("C6H10O5", e1)
            rec["Au_specificity_factor"] = rec["mu_ratio_Au_hi_over_lo"] / rec["mu_ratio_cellulose_hi_over_lo"]
            ti, tj = inv[names[i]]["transform"], inv[names[j]]["transform"]
            reg = ti is not None and tj is not None and \
                ti["fixed_volume"].replace("PHerc4Paris", "PHercParis4") == tj["fixed_volume"].replace("PHerc4Paris", "PHercParis4")
            rec["both_registered_same_frame"] = bool(reg)
            if reg:
                cov = {}
                for n in (names[i], names[j]):
                    A = np.vstack([np.array(inv[n]["_A"]), [0, 0, 0, 1]])
                    q = (np.linalg.inv(A)[:3, :3] @ fixed.T).T + np.linalg.inv(A)[:3, 3]
                    zyx = inv[n]["shape_zyx"]
                    inside = (q[:, 0] >= 0) & (q[:, 0] < zyx[2]) & (q[:, 1] >= 0) & (q[:, 1] < zyx[1]) & \
                             (q[:, 2] >= 0) & (q[:, 2] < zyx[0])
                    cov[n] = {"frac_mesh_inside_volume_bbox": float(inside.mean()),
                              "z_range_mapped": [float(q[:, 2].min()), float(q[:, 2].max())]}
                rec["coverage_w010_027"] = cov
            pairs.append(rec)
    for v in inv.values():
        v.pop("_A", None)
    out = {"provenance": G.PROV, "serves": "DECL-P4-6-A1/A2 K-edge inventory; DECL-P4-10 GOLD", "edges_keV": EDGES,
           "volumes": inv, "bracketing_pairs": pairs, "mesh_sample": {"key": MESH, "every": 16, "n": int(ok.sum())},
           "note": "energies are nominal (mean) energies of filtered polychromatic BM18 beams; mono ratios are an idealisation"}
    json.dump(out, open(outp, "w"), indent=1)


if __name__ == "__main__":
    main()
