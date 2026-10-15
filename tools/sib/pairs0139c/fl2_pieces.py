# Provenance: Project HERCULES | [id removed]
"""DECL-FL-2-E3 gate pieces (pairs0139c). Numbers only.
plan SEGDIR OUT_JSON [--single]: full canvas H = rows*20, W = cols*20 (scale 0.05, render 'WxH from (0,0)');
  2 x 2 cm grid T = 2136 px from the canvas origin (as fl-pherc0257 cmd_tiles); valid = mesh vertex validity resampled
  nearest to the canvas; kept cells valid >= 0.5. Pieces = vertical pairs of kept cells in one column (else single
  cells; --single: always single). Crop origin = floor((cell0 - 256) / 64) * 64 (clipped to 0): a margin of 256-319 px
  (<= 0.3 cm), on the infer stride grid (64) of the full canvas, so the official sliding-window positions inside the
  piece coincide with the full-canvas ones. Crop end = cell end + 256 (clipped to the canvas).
tile SEGNAME SEGDIR PIECE_JSON PIECE_ID PRED_TIF DIRECTION OUTDIR MANIFEST VOLID MEASURE_JSON: crop the margin off and
  tile exactly as cmd_tiles does (u8, invalid px = 0, INTER_AREA to 1068 px, ink_score_ge128 over valid px);
  r, c are full-grid indices; rows get piece bounds and BRIEF_FL2 item 5 fields."""
import json, os, sys, hashlib
import numpy as np, cv2, tifffile
VOX_UM, TILE_MM, OUT_PX, MARG, STRIDE = 9.362, 20.0, 1068, 256, 64
CKSHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
T = int(round(TILE_MM * 1000 / VOX_UM)); PPM = OUT_PX / (T * VOX_UM / 1000.0)
def sha256(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def full_valid(segdir):
    P = np.stack([tifffile.imread(os.path.join(segdir, f"{a}.tif")).astype(np.float64) for a in "xyz"], -1)
    V = (P[..., 0] != -1) & np.isfinite(P).all(-1) & (P[..., 2] > 0)
    H, W = V.shape[0] * 20, V.shape[1] * 20
    return cv2.resize(V.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
def plan(segdir, out, single):
    v = full_valid(segdir); H, W = v.shape
    kept = {(r, c): float(v[r*T:(r+1)*T, c*T:(c+1)*T].mean()) for r in range(H // T) for c in range(W // T)}
    kept = {k: f for k, f in kept.items() if f >= 0.5}
    pieces, used = [], set()
    for (r, c) in sorted(kept, key=lambda k: (k[1], k[0])):
        if (r, c) in used: continue
        cells = [(r, c)] + ([(r + 1, c)] if not single and (r + 1, c) in kept and (r + 1, c) not in used else [])
        used.update(cells)
        y0, y1 = min(a for a, _ in cells) * T, (max(a for a, _ in cells) + 1) * T; x0, x1 = c * T, (c + 1) * T
        cy = max(0, (y0 - MARG) // STRIDE * STRIDE); cx = max(0, (x0 - MARG) // STRIDE * STRIDE)
        ey = min(H, y1 + MARG); ex = min(W, x1 + MARG)
        pieces.append(dict(id=len(pieces), cells=[list(k) for k in cells], crop_x=cx, crop_y=cy, crop_w=ex - cx, crop_h=ey - cy,
                           cells_y0=y0, cells_y1=y1, cells_x0=x0, cells_x1=x1,
                           area_cm2=round((ex - cx) * (ey - cy) * (VOX_UM / 1e4) ** 2, 3),
                           margins_px=[y0 - cy, ey - y1, x0 - cx, ex - x1]))
    json.dump(dict(canvas_hw=[H, W], tile_px=T, n_cells=len(kept), cells_valid={f"{r},{c}": f for (r, c), f in kept.items()},
                   pieces=pieces), open(out, "w"), indent=1)
    print(f"plan: canvas {H}x{W}, {len(kept)} cells, {len(pieces)} pieces, max area {max([p['area_cm2'] for p in pieces] or [0])} cm2")
def tile(seg, segdir, pjson, pid, pred, direction, outdir, manifest, volid, measure):
    pl = json.load(open(pjson)); pc = pl["pieces"][int(pid)]
    p = tifffile.imread(pred)
    if p.ndim == 3: p = p[0] if p.shape[0] < p.shape[-1] else p[..., 0]
    if p.dtype != np.uint8:
        pf = p.astype(np.float32); p = np.clip(pf * (255.0 if pf.max() <= 1.0 else 1.0), 0, 255).round().astype(np.uint8)
    assert p.shape == (pc["crop_h"], pc["crop_w"]), (p.shape, pc)
    v = full_valid(segdir); me = json.load(open(measure))
    os.makedirs(outdir, exist_ok=True)
    man = json.load(open(manifest)) if os.path.exists(manifest) else {"tiles": []}
    man.update({"scroll": "PHerc0139", "decl": "DECL-FL-2-E2/E3 gate (pieces)", "tile_src_px": T, "tile_out_px": OUT_PX,
                "px_per_mm": round(PPM, 4), "voxel_um": VOX_UM, "canvas_hw": pl["canvas_hw"],
                "chain": "C2-NT: vc_render_tifxyz -n 31 --flip-normals --crop-*, ink_9um step-075000, both directions, no TTA",
                "tool": "tools/sib/pairs0139c/fl2_pieces.py", "tool_sha256": sha256(__file__)})
    nk = 0
    for (r, c) in pc["cells"]:
        names = f"{seg}_{direction}_r{r:02d}_c{c:02d}.png"
        man["tiles"] = [t for t in man["tiles"] if t.get("file") != names]
        vm = v[r*T:(r+1)*T, c*T:(c+1)*T]; vf = float(vm.mean())
        if vf < 0.5: continue
        oy, ox = r*T - pc["crop_y"], c*T - pc["crop_x"]
        t = p[oy:oy + T, ox:ox + T].copy(); assert t.shape == (T, T); t[~vm] = 0
        t = cv2.resize(t, (OUT_PX, OUT_PX), interpolation=cv2.INTER_AREA)
        fn = os.path.join(outdir, names); cv2.imwrite(fn, t)
        vv = cv2.resize(vm.astype(np.uint8), (OUT_PX, OUT_PX), interpolation=cv2.INTER_NEAREST) > 0
        man["tiles"].append({"file": names, "png_sha256": sha256(fn), "scroll": "PHerc0139", "volume": volid, "segment": seg,
                             "model": "official", "model_sha256": CKSHA, "direction": direction, "r": r, "c": c,
                             "piece": {k: pc[k] for k in ("id", "crop_x", "crop_y", "crop_w", "crop_h", "area_cm2", "margins_px")},
                             "valid_fraction": round(vf, 4), "px_per_mm": round(PPM, 4), "source": "organizer",
                             "segment_area_cm2": round(me["area_cm2"], 4),
                             "ink_score_ge128": round(float((t[vv] >= 128).mean()) if vv.any() else 0.0, 5)})
        nk += 1
    man["tiles"].sort(key=lambda t: (t["r"], t["c"], t["direction"]))
    json.dump(man, open(manifest, "w"), indent=1)
    print(f"piece tiles {seg} piece {pid} {direction}: {nk}")
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "plan": plan(a[1], a[2], "--single" in a)
    else: tile(*a[1:11])
