# Provenance: Project HERCULES | [id removed]
"""DECL-FL-2-E2 item 2 (SUPPLEMENTARY, not used for the gate criterion): tile the title segment's prediction as
2 cm-wide cells spanning its full canvas height (1.67 cm), zero-padded at the bottom to 2 x 2 cm, then INTER_AREA to
1068 px (53.4 px/mm), exactly as the template cmd_tiles does otherwise (u8 conversion, valid = mesh vertex validity
resampled nearest, invalid px set to 0, ink_score_ge128 over valid px). Kept if the strip cell's valid fraction >= 0.5.
Usage: fl2_supp_tiles.py SEGNAME SEGDIR PRED_TIF DIRECTION OUTDIR MANIFEST"""
import json, os, sys, hashlib
import numpy as np, cv2, tifffile
VOX_UM, TILE_MM, OUT_PX = 9.362, 20.0, 1068
def sha256(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
seg, segdir, pred, direction, outdir, manifest = sys.argv[1:7]
p = tifffile.imread(pred)
if p.ndim == 3: p = p[0] if p.shape[0] < p.shape[-1] else p[..., 0]
if p.dtype != np.uint8:
    pf = p.astype(np.float32); p = np.clip(pf * (255.0 if pf.max() <= 1.0 else 1.0), 0, 255).round().astype(np.uint8)
P = np.stack([tifffile.imread(os.path.join(segdir, f"{a}.tif")).astype(np.float64) for a in "xyz"], -1)
V = (P[..., 0] != -1) & np.isfinite(P).all(-1) & (P[..., 2] > 0)
valid = cv2.resize(V.astype(np.uint8), (p.shape[1], p.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
T = int(round(TILE_MM * 1000 / VOX_UM)); ppm = OUT_PX / (T * VOX_UM / 1000.0); H = p.shape[0]
assert H < T, (H, T)
os.makedirs(outdir, exist_ok=True)
man = json.load(open(manifest)) if os.path.exists(manifest) else {"tiles": []}
man.update({"scroll": "PHerc0139", "decl": "DECL-FL-2-E2 item 2 (supplementary)", "tile_src_px": T, "tile_out_px": OUT_PX,
            "px_per_mm": round(ppm, 4), "voxel_um": VOX_UM, "canvas_hw": list(p.shape), "strip_height_px": H,
            "strip_height_cm": round(H * VOX_UM / 1e4, 4), "padding": f"rows {H}..{T - 1} of each 2 x 2 cm cell are zero (bottom padding)",
            "keep_rule": "strip valid fraction >= 0.5", "tool": "tools/sib/pairs0139c/fl2_supp_tiles.py",
            "tool_sha256": sha256(__file__)})
man["tiles"] = [t for t in man["tiles"] if t.get("direction") != direction]
nk = nt = 0
for c in range(p.shape[1] // T):
    nt += 1
    vm = valid[:, c * T:(c + 1) * T]; vf = float(vm.mean())
    if vf < 0.5: continue
    t = np.zeros((T, T), np.uint8); s = p[:, c * T:(c + 1) * T].copy(); s[~vm] = 0; t[:H] = s
    vfull = np.zeros((T, T), bool); vfull[:H] = vm
    t = cv2.resize(t, (OUT_PX, OUT_PX), interpolation=cv2.INTER_AREA)
    fn = os.path.join(outdir, f"{seg}_{direction}_strip_c{c:02d}.png"); cv2.imwrite(fn, t)
    vv = cv2.resize(vfull.astype(np.uint8), (OUT_PX, OUT_PX), interpolation=cv2.INTER_NEAREST) > 0
    man["tiles"].append({"segment": seg, "r": 0, "c": c, "direction": direction, "file": os.path.basename(fn),
                         "png_sha256": sha256(fn), "valid_fraction_strip": round(vf, 4),
                         "valid_fraction_cell": round(float(vfull.mean()), 4), "px_per_mm": round(ppm, 4), "source": "organizer",
                         "ink_score_ge128": round(float((t[vv] >= 128).mean()) if vv.any() else 0.0, 5)})
    nk += 1
json.dump(man, open(manifest, "w"), indent=1)
print(f"supp tiles {seg} {direction}: kept {nk} of {nt} strip cells (T={T} px, strip H={H} px)")
