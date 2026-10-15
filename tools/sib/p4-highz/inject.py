"""p4-highz injection-recovery for the P4-F dense channel (orchestrator addendum under DECL-P4-12: turn "not seen"
into "ruled out down to X um"). Numbers only: synthetic letter-shaped pigment layers are added to REAL level-0
sheet-slab CT of the known-text control, and the screen's own criteria are re-run. Nothing is displayed.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python inject.py <scratch> <repo> <material C|C2> [n_regions]

Model:
- Letter: a Greek capital H-like glyph, 3.0 mm tall, 2.0 mm wide, stroke 0.4 mm (DECL-P4-10 item 3 range), centred in
  a 12 x 12 chunk region (1536 px) whose px are >= 95 % mesh-valid and whose chunks are all present.
- Layer of thickness t (um) whose lower face is on the mesh surface (centre slice), growing towards increasing slice
  index; per voxel the covered depth fraction f; grey increment f (g_pig - g_pap) with g_pig from pigments.json
  (linear grey model, papyrus density 0.8 g/cm3; see pigments.py for the caveats).
- Blur: the increment is convolved with a 3-D Gaussian of sigma 0 (ideal) or 1.0 voxel (~2.4 voxel FWHM), then added
  to the real uint8 voxels and clipped to [0, 255].
- Detected (pattern): the sheet-slab maximum > T_hi mask has an 8-connected component with bounding box 0.5-5 mm that
  overlaps the glyph (the screen's letter-scale criterion). Also reported: the n_hi increment vs the control's
  (tile p99 - tile median) gap, i.e. whether one such letter alone lifts a median tile over the hotspot bar.
- False-positive check: the same regions without injection (letter-scale components count).
"""
import concurrent.futures as cf
import json
import os
import sys
import time

import cv2
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

scr, repo, mat_name = sys.argv[1], sys.argv[2], sys.argv[3]
NREG = int(sys.argv[4]) if len(sys.argv) > 4 else 20
OFF_UM = int(sys.argv[5]) if len(sys.argv) > 5 else None  # PROTOCOL_dstar.md: layer at centre + offset
R = 12  # chunks per side
thf = "thresholds.json" if mat_name == "C" else "thresholds_2p4.json"
th = json.load(open(os.path.join(repo, "logs/sib/p4-highz", thf)))
T_hi = th["T_hi"]
PIGF = os.environ.get("HZ_PIGMENTS", "pigments.json")
pig = json.load(open(os.path.join(repo, "logs/sib/p4-highz", PIGF)))["materials"][mat_name]
M = C.load_material(mat_name, scr)
um = M["um"]
o_s = 0 if OFF_UM is None else int(round(OFF_UM / um))
s0, s1 = C.slabs_at(mat_name, o_s)[0]
cen = M["centre"] + o_s


def glyph(n):
    g = np.zeros((n, n), bool)
    h, w, sw = int(3.0e3 / um), int(2.0e3 / um), int(0.4e3 / um)
    y0, x0 = (n - h) // 2, (n - w) // 2
    g[y0:y0 + h, x0:x0 + sw] = True
    g[y0:y0 + h, x0 + w - sw:x0 + w] = True
    g[y0 + h // 2 - sw // 2:y0 + h // 2 + sw // 2, x0:x0 + w] = True
    return g


def fetch(yc, xc):
    b = C.get(f"{M['url0']}/{yc}/{xc}", (s0 * C.PLANE, s1 * C.PLANE - 1))
    return None if b is None else np.frombuffer(b, np.uint8).reshape(-1, C.CH, C.CH)


rng = np.random.default_rng(20260928)
regions, tries = [], 0
tiles = M["tiles"]
while len(regions) < NREG and tries < 400:
    tries += 1
    t = tiles[rng.integers(len(tiles))]
    ch = C.tile_chunks(M, t["r"], t["c"])
    ys = sorted({a for a, _ in ch})
    xs = sorted({b for _, b in ch})
    if len(ys) < R or len(xs) < R:
        continue
    y0 = ys[rng.integers(len(ys) - R + 1)]
    x0 = xs[rng.integers(len(xs) - R + 1)]
    yy, xx = y0 * C.CH + np.arange(R * C.CH), x0 * C.CH + np.arange(R * C.CH)
    dv = M["div"]
    v = M["valid"][np.minimum(yy // dv, M["valid"].shape[0] - 1)][:, np.minimum(xx // dv, M["valid"].shape[1] - 1)]
    v &= (yy < M["H"])[:, None] & (xx < M["W"])[None, :]
    if v.mean() < 0.95:
        continue
    with cf.ThreadPoolExecutor(48) as ex:
        blocks = list(ex.map(lambda k: fetch(y0 + k // R, x0 + k % R), range(R * R)))
    if any(b is None for b in blocks):
        continue
    vol = np.zeros((s1 - s0, R * C.CH, R * C.CH), np.uint8)
    for k, b in enumerate(blocks):
        a, c = divmod(k, R)
        vol[:, a * C.CH:(a + 1) * C.CH, c * C.CH:(c + 1) * C.CH] = b
    regions.append({"tile": f"r{t['r']}_c{t['c']}", "chunk0": [int(y0), int(x0)], "vol": vol, "valid": v})
n = R * C.CH
G = glyph(n)


def letter_components(vol, valid, gl=None):
    hi = ((vol.max(0) > T_hi) & valid).astype(np.uint8)
    ncc, lab, st, _ = cv2.connectedComponentsWithStats(hi, connectivity=8)
    ext = np.maximum(st[1:, 2], st[1:, 3]) * um / 1000.0
    ok = (ext >= 0.5) & (ext <= 5)
    if gl is not None and ok.any():
        ids = np.nonzero(ok)[0] + 1
        hit = np.unique(lab[gl & (hi > 0)])
        ok_ids = set(ids) & set(hit.tolist())
        return len(ok_ids), int(((vol > T_hi) & valid[None]).sum())
    return int(ok.sum()), int(((vol > T_hi) & valid[None]).sum())


fp = [letter_components(r["vol"], r["valid"])[0] for r in regions]
base_nhi = [letter_components(r["vol"], r["valid"])[1] for r in regions]
nslab = s1 - s0
kc = cen - s0  # index of the surface slice inside the slab
THK = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]
out = {"provenance": C.PROV, "material": mat_name, "segment": M["seg"], "voxel_um": um, "T_hi": T_hi,
       "regions": [{"tile": r["tile"], "chunk0": r["chunk0"]} for r in regions], "n_regions": len(regions),
       "region_side_mm": n * um / 1000, "glyph": "H-like, 3.0 x 2.0 mm, stroke 0.4 mm", "glyph_px": int(G.sum()),
       "false_positive_letter_components_no_injection": fp, "model": __doc__.split("Model:")[1].strip(),
       "papyrus_density_g_cm3": 0.8, "results": {}}
dgs = {}
for pname, prow in pig["pigments"].items():
    dg = prow["by_papyrus_density"]["0.8"]["grey_full_voxel_unclipped"] - pig["g_papyrus_mode"]
    if dg > 0:
        dgs[pname] = dg
curves = {p: {} for p in dgs}
for sig in (0.0, 1.0):
    for t in THK:
        # depth fractions of each slab slice covered by [surface, surface + t)
        f = np.zeros(nslab)
        rem, k = t / um, kc
        while rem > 0 and k < nslab:
            f[k] = min(1.0, rem)
            rem -= 1.0
            k += 1
        unit = f[:, None, None] * G[None].astype(np.float32)
        if sig > 0:
            unit = ndimage.gaussian_filter(unit, sig, mode="constant")
        for pname, dg in dgs.items():
            det, dn = 0, []
            for r, nb in zip(regions, base_nhi):
                v2 = np.clip(r["vol"].astype(np.float32) + unit * dg, 0, 255).astype(np.uint8)
                c, nh = letter_components(v2, r["valid"], G)
                det += int(c > 0)
                dn.append(nh - nb)
            curves[pname].setdefault(f"sigma_{sig}", []).append(
                {"t_um": t, "recovery": det / len(regions), "n_hi_increment_median": float(np.median(dn))})
for pname, cs in curves.items():
    res = {k: {"curve": rec, "detection_limit_um_recovery_ge_0p8": next((x["t_um"] for x in rec if x["recovery"] >= 0.8), None)}
           for k, rec in cs.items()}
    out["results"][pname] = res
    print(pname, {k: v["detection_limit_um_recovery_ge_0p8"] for k, v in res.items()}, flush=True)
out["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
out["offset_um"], out["offset_slices"], out["pigment_table"] = OFF_UM, o_s, PIGF
json.dump(out, open(os.path.join(repo, f"logs/sib/p4-highz/inject_{mat_name}" + ("" if OFF_UM is None else f"_o{OFF_UM}") + ("_ext" if PIGF != "pigments.json" else "") + ".json"), "w"), indent=1)
print("FP", fp)
