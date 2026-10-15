"""p4-highz scan inventory (RULES.md DECL-P4-6-A1 item 2, DECL-P4-6-A2 item 2): every published PHerc. Paris 4
volume: energy, pixel size, date, registration to 20260411134726, and coverage of the w010-027 strip; K-edge
bracketing flags. Numbers only; no K-edge map is computed (that needs its own declaration).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python inventory.py <scratch> <repo>
"""
import hashlib
import json
import os
import re
import sys
import time

import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

scr, repo = sys.argv[1], sys.argv[2]
B = C.BUCKET
EDGES = {"Au": 80.7, "Hg": 83.1, "Pb": 88.0}
REF = "20260411134726-2.400um-0.2m-78keV-masked"
CANON = "20230205180739"


def fetch(key):
    b = C.get(f"{B}/{key}")
    return b, (None if b is None else {"key": key, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})


x = C.session().get(f"{B}/", params={"list-type": "2", "prefix": "PHercParis4/volumes/", "delimiter": "/"}).text
vols = [p.split("/")[-2][:-5] for p in re.findall(r"<Prefix>(PHercParis4/volumes/[^<]+/)</Prefix>", x)]
inv, inputs = {}, []
for v in vols:
    d = {"volume": v}
    base = f"PHercParis4/volumes/{v}.zarr"
    md, r1 = fetch(f"{base}/metadata.json")
    za, r2 = fetch(f"{base}/0/.zarray")
    tr, r3 = fetch(f"{base}/transform.json")
    inputs += [r for r in (r1, r2, r3) if r]
    m = json.loads(md)
    tomo = m.get("scan", m).get("tomo", m.get("tomo"))
    acq = tomo["acquisition"]
    d["energy_keV"] = acq["energy"]
    d["pixel_um"] = acq["detector"]["samplePixelSize"] * 1000
    d["date"] = acq.get("date") or acq.get("start_date")
    d["beamline"] = acq.get("beamline")
    d["mosaic_tiles"] = len(m.get("mosaic_tiles", {})) or None
    d["shape_zyx_level0"] = json.loads(za)["shape"]
    if tr is None:
        d["registration"] = {"transform_json": False, "registered_to_20260411134726": False,
                             "note": "no transform.json published; not registered to any frame in the bucket"}
    else:
        t = json.loads(tr)
        M = np.array(t["transformation_matrix"], float)
        Fl, Ml = np.array(t["fixed_landmarks"], float), np.array(t["moving_landmarks"], float)
        res = np.linalg.norm((M[:, :3] @ Ml.T).T + M[:, 3] - Fl, axis=1)
        d["registration"] = {"transform_json": True, "fixed_volume": t["fixed_volume"], "matrix_moving_to_fixed_xyz": M.tolist(),
                             "landmarks": len(Fl), "landmark_residual_fixed_vox_rms": float(np.sqrt((res ** 2).mean())),
                             "landmark_residual_fixed_vox_max": float(res.max()), "convention_check": "fixed = M [moving_xyz, 1]"}
        d["_M"] = M
    inv[v] = d

# composite transforms into the 20260411134726 (REF) frame: every published transform targets either the canonical
# 20230205180739 frame or the 2.4 um REF frame directly.
Mref = inv[REF]["_M"]
A = lambda M: np.vstack([M, [0, 0, 0, 1]])
for v, d in inv.items():
    if "_M" not in d:
        continue
    fv = d["registration"]["fixed_volume"]
    if v == REF:
        to_ref = np.eye(4)
        how = "identity (reference frame)"
    elif CANON in fv:
        to_ref = np.linalg.inv(A(Mref)) @ A(d["_M"])
        how = f"composed: own affine to canonical {CANON}, then inverse of the 20260411134726 affine"
    elif "2.4um" in fv:
        to_ref = A(d["_M"])
        how = "direct affine to the 2.4 um 78 keV volume (fixed_volume '2.4um_PHerc-Paris4_masked')"
    else:
        to_ref, how = None, f"unknown fixed volume {fv}"
    d["registration"]["registered_to_20260411134726"] = to_ref is not None
    d["registration"]["how"] = how
    d["_to_ref"] = to_ref
    if to_ref is not None:
        d["registration"]["scale_to_ref"] = float(abs(np.linalg.det(to_ref[:3, :3])) ** (1 / 3))

# strip coverage: w010-027 meshes in the 2.4 um REF frame, mapped into every registered volume
strips = {"E1_20260623141924": "PHercParis4/segments/20260623141924-w010-027/mesh/20260623141924-on-20260411134726-2.4um.tifxyz",
          "E2_20260701183124": "PHercParis4/segments/20260701183124-w010-027/mesh/20260701183124-on-20260411134726-2.4um.tifxyz"}
pts = {}
for s, k in strips.items():
    arr = []
    for a in "xyz":
        b, r = fetch(f"{k}/{a}.tif")
        inputs.append(r)
        p = os.path.join(scr, f"inv_{s}_{a}.tif")
        open(p, "wb").write(b)
        arr.append(tifffile.imread(p).astype(np.float64))
        os.remove(p)
    ok = (arr[0] != -1) & (arr[1] != -1) & (arr[2] != -1) & np.isfinite(arr[0]) & np.isfinite(arr[1]) & np.isfinite(arr[2])
    P = np.stack([a[ok] for a in arr], 1)
    rng = np.random.default_rng(20260926)
    pts[s] = P[rng.choice(len(P), min(200000, len(P)), replace=False)]
    del arr

for v, d in inv.items():
    cov = {}
    to_ref = d.get("_to_ref")
    if to_ref is None:
        d["coverage_w010_027"] = None
        continue
    inv_m = np.linalg.inv(to_ref)
    Z, Y, X = d["shape_zyx_level0"]
    for s, P in pts.items():
        Q = (inv_m[:3, :3] @ P.T).T + inv_m[:3, 3]
        inside = (Q[:, 0] >= 0) & (Q[:, 0] < X) & (Q[:, 1] >= 0) & (Q[:, 1] < Y) & (Q[:, 2] >= 0) & (Q[:, 2] < Z)
        # data presence: sample 3000 inside points at a coarse level (non-zero voxel = scanned and not masked)
        lvl = 5 if d["pixel_um"] < 10 else 0
        f = 2 ** lvl
        sel = np.nonzero(inside)[0]
        sel = sel[np.random.default_rng(1).choice(len(sel), min(1000, len(sel)), replace=False)] if len(sel) else sel
        nz = 0
        cache = {}
        for i in sel:
            xi, yi, zi = (Q[i] / f).astype(int)
            key = (zi // 128, yi // 128, xi // 128)
            if key not in cache:
                b = C.get(f"{B}/PHercParis4/volumes/{v}.zarr/{lvl}/{key[0]}/{key[1]}/{key[2]}")
                cache[key] = None if b is None else np.frombuffer(b, np.uint8).reshape(128, 128, 128)
            c = cache[key]
            nz += int(c is not None and c[zi % 128, yi % 128, xi % 128] > 0)
        cov[s] = {"points": len(P), "frac_inside_volume_extent": float(inside.mean()),
                  "frac_nonzero_data_at_inside_points": (nz / len(sel)) if len(sel) else None,
                  "nonzero_check": f"{len(sel)} points at level {lvl}",
                  "z_range_in_volume_vox": [float(Q[inside, 2].min()), float(Q[inside, 2].max())] if inside.any() else None,
                  "xy_range_in_volume_vox": ([float(Q[inside, 0].min()), float(Q[inside, 0].max()),
                                              float(Q[inside, 1].min()), float(Q[inside, 1].max())] if inside.any() else None),
                  "strip_z_range_ref_vox": [float(P[:, 2].min()), float(P[:, 2].max())]}
    d["coverage_w010_027"] = cov

# K-edge bracketing pairs (both scans registered to REF and both covering some of the strip)
pairs = []
vl = list(inv)
for i in range(len(vl)):
    for j in range(i + 1, len(vl)):
        a, b = inv[vl[i]], inv[vl[j]]
        lo, hi = sorted([a["energy_keV"], b["energy_keV"]])
        br = [e for e, k in EDGES.items() if lo < k < hi]
        if not br:
            continue
        reg = a["registration"].get("registered_to_20260411134726") and b["registration"].get("registered_to_20260411134726")
        def covf(d):
            c = d.get("coverage_w010_027") or {}
            return {s: (x["frac_inside_volume_extent"], x["frac_nonzero_data_at_inside_points"]) for s, x in c.items()}
        pairs.append({"scans": [vl[i], vl[j]], "energies_keV": [a["energy_keV"], b["energy_keV"]],
                      "pixel_um": [a["pixel_um"], b["pixel_um"]], "brackets_K_edges": br,
                      "both_registered_to_20260411134726": bool(reg),
                      "coverage_w010_027_(frac_inside, frac_nonzero)": [covf(a), covf(b)],
                      "FLAG": bool(reg)})
for d in inv.values():
    d.pop("_M", None)
    d.pop("_to_ref", None)
out = {"provenance": C.PROV, "serves": "RULES.md DECL-P4-6-A1 item 2 and DECL-P4-6-A2 item 2 (inventory; numbers only; no K-edge map)",
       "K_edges_keV": EDGES, "reference_frame": REF, "volumes": inv, "kedge_pairs": pairs, "inputs": inputs,
       "coverage_method": "valid vertices of the two w010-027 meshes in the 20260411134726 frame (200k random each), mapped "
                          "by the published affines into each volume's level-0 voxel frame; 'inside' = within the zarr "
                          "extent; 'nonzero' = voxel > 0 at a coarse level (scanned, not masked)",
       "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump(out, open(os.path.join(repo, "logs/sib/p4-highz/scans.json"), "w"), indent=1)
print(json.dumps([{k: p[k] for k in ("energies_keV", "pixel_um", "brackets_K_edges", "FLAG", "coverage_w010_027_(frac_inside, frac_nonzero)")} for p in pairs], indent=0))
for v, d in inv.items():
    print(v, d["energy_keV"], d["pixel_um"], d["registration"].get("registered_to_20260411134726"),
          {s: (round(x["frac_inside_volume_extent"], 3), x["frac_nonzero_data_at_inside_points"]) for s, x in (d["coverage_w010_027"] or {}).items()})
