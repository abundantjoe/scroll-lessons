# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-FL-1 tiles: 2 x 2 cm non-overlapping grid on the render canvas, u8 ink map (invalid -> 0),
INTER_AREA to 1068 px, PNG, keep valid >= 50 %. Valid = render pixel nonzero in any of the slices.
Numbers only: nothing here displays an image.
Usage: make_tiles.py RENDER_ZARR FWD_TIF REV_TIF SEGMENT OUT_DIR VOXEL_UM EXTRA_JSON"""
import hashlib, json, sys
from pathlib import Path
import cv2, numpy as np, tifffile, zarr

rz, fwd, rev, seg, out, vox = sys.argv[1:7]
extra = json.loads(Path(sys.argv[7]).read_text()) if len(sys.argv) > 7 else {}
vox = float(vox)
TILE_MM, OUT_PX, MIN_VALID = 20.0, 1068, 0.5
T = int(round(TILE_MM * 1000.0 / vox))          # native px per tile side (2136 at 9.362 um)

g = zarr.open(rz, mode="r")
arr = g if isinstance(g, zarr.Array) else g["0"]
assert arr.ndim == 3, arr.shape
Z, H, W = arr.shape
valid = np.zeros((H, W), bool)
for y in range(0, H, 512):
    valid[y:y + 512] = (np.asarray(arr[:, y:y + 512, :]) > 0).any(axis=0)

maps = {"forward": tifffile.imread(fwd), "reverse": tifffile.imread(rev)}
for k, m in maps.items():
    assert m.shape == (H, W), (k, m.shape, (H, W))
    assert m.dtype == np.uint8, (k, m.dtype)

out = Path(out); out.mkdir(parents=True, exist_ok=True)
nr, nc = -(-H // T), -(-W // T)
tiles, n_grid = [], 0
for r in range(nr):
    for c in range(nc):
        n_grid += 1
        v = np.zeros((T, T), bool)
        vv = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
        v[:vv.shape[0], :vv.shape[1]] = vv
        vf = float(v.mean())
        if vf < MIN_VALID:
            continue
        for d, m in maps.items():
            t = np.zeros((T, T), np.uint8)
            mm = m[r * T:(r + 1) * T, c * T:(c + 1) * T]
            t[:mm.shape[0], :mm.shape[1]] = mm
            t[~v] = 0
            small = cv2.resize(t, (OUT_PX, OUT_PX), interpolation=cv2.INTER_AREA)
            name = f"{seg}_{d}_r{r:02d}_c{c:02d}.png"
            ok, buf = cv2.imencode(".png", small)
            assert ok
            (out / name).write_bytes(buf.tobytes())
            tiles.append({"segment": seg, "r": r, "c": c, "direction": d, "file": name,
                          "png_sha256": hashlib.sha256(buf.tobytes()).hexdigest(),
                          "valid_fraction": round(vf, 6), "px_per_mm": OUT_PX / TILE_MM,
                          "source": extra.get("source", "organizer"),
                          "canvas_origin_yx_native": [r * T, c * T]})
man = {"segment": seg, "canvas_hw": [H, W], "render_slices": Z, "voxel_um": vox, "tile_mm": TILE_MM,
       "tile_native_px": T, "tile_out_px": OUT_PX, "px_per_mm": OUT_PX / TILE_MM, "min_valid": MIN_VALID,
       "valid_def": "render nonzero in any slice; outside canvas counts invalid", "resize": "cv2.INTER_AREA",
       "canvas_valid_fraction": round(float(valid.mean()), 6), "n_grid_cells": n_grid,
       "n_kept_cells": len(tiles) // 2, **extra, "tiles": tiles}
(out / "manifest.json").write_text(json.dumps(man, indent=1))
print(json.dumps({"segment": seg, "canvas_hw": [H, W], "grid": n_grid, "kept_cells": len(tiles) // 2}))
