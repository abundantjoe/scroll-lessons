"""fl-pherc0125 helpers (RULES.md DECL-FL-1). Numbers only: no image is viewed or described.
Provenance: Project HERCULES | owner the owner | [id removed]
  python fl_tools.py area <tifxyz_dir> <voxel_um>        -> prints area_cm2 (sum of valid quad areas)
  python fl_tools.py tiles <seg> <pred.tif> <render.zarr> <out_dir> <voxel_um> <source_json>
"""
import hashlib, json, os, sys
import numpy as np


def area(d, vox):
    import tifffile
    x, y, z = (tifffile.imread(os.path.join(d, f"{a}.tif")).astype(np.float64) for a in "xyz")
    P = np.stack([x, y, z], -1)
    ok = (x != -1) & (y != -1) & (z != -1)
    q = ok[:-1, :-1] & ok[1:, :-1] & ok[:-1, 1:] & ok[1:, 1:]
    a, b, c, e = P[:-1, :-1], P[1:, :-1], P[:-1, 1:], P[1:, 1:]
    t1 = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1)
    t2 = 0.5 * np.linalg.norm(np.cross(b - e, c - e), axis=-1)
    return float(((t1 + t2) * q).sum() * (vox * 1e-4) ** 2)


def tiles(seg, pred, render, out, vox, source):
    import cv2, tifffile, zarr
    os.makedirs(os.path.join(out, "tiles"), exist_ok=True)
    p = tifffile.imread(pred)
    if p.ndim == 3:
        p = p[0]
    if p.dtype != np.uint8:
        p = np.clip(p.astype(np.float64) * (255.0 if float(np.nanmax(p)) <= 1.0 else 1.0), 0, 255).astype(np.uint8)
    r = zarr.open(os.path.join(render, "0"), mode="r")
    valid = np.asarray(r[15]) > 0                      # middle render slice: zero outside the mesh
    H, W = min(p.shape[0], valid.shape[0]), min(p.shape[1], valid.shape[1])
    p, valid = p[:H, :W], valid[:H, :W]
    px_mm = 1000.0 / vox
    T = int(round(20 * px_mm))                          # 2 cm
    man = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "serves": "RULES.md DECL-FL-1 items 1-2", "segment": seg, "tile_px_source": T,
           "px_per_mm": 1068 / 20.0, "source": json.loads(source), "tiles": []}
    for i in range(H // T):
        for j in range(W // T):
            v = valid[i*T:(i+1)*T, j*T:(j+1)*T]
            vf = float(v.mean())
            if vf < 0.5:
                continue
            t = p[i*T:(i+1)*T, j*T:(j+1)*T].copy()
            t[~v] = 0
            img = cv2.resize(t, (1068, 1068), interpolation=cv2.INTER_AREA)
            fn = os.path.join(out, "tiles", f"{seg}_r{i}_c{j}.png")
            cv2.imwrite(fn, img)
            ink = float((t[v] >= 128).mean()) if v.any() else 0.0
            man["tiles"].append({"segment": seg, "r": i, "c": j, "png": os.path.basename(fn),
                                 "png_sha256": hashlib.sha256(open(fn, "rb").read()).hexdigest(),
                                 "valid_fraction": vf, "px_per_mm": 1068 / 20.0, "ink_score_ge128": ink})
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(len(man["tiles"]), "tiles")


if __name__ == "__main__":
    if sys.argv[1] == "area":
        print(area(sys.argv[2], float(sys.argv[3])))
    else:
        tiles(*sys.argv[2:6], float(sys.argv[6]), sys.argv[7])
