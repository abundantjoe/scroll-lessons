"""Draw a tifxyz surface on raw CT slices at several heights, so a person can see whether it stays on one sheet.
usage: python -m xsec.xsections <tifxyz_dir> <volume> <out_prefix> [--level L] [--n 4] [--scale S]
  volume: a local zarr path or an s3:// URL of an OME-zarr; --level picks the pyramid level (default 1), --scale its
  downsampling factor relative to the tifxyz coordinates (default 2 for level 1). Writes <out_prefix>_xsec.png and .json."""
import argparse, json, numpy as np, cv2, zarr
from .tifxyz import read, valid_mask

def open_volume(url, level):
    if url.startswith("s3://"):
        import s3fs; fs = s3fs.S3FileSystem(anon=True)
        return zarr.open(zarr.storage.FSStore(url.rstrip("/") + f"/{level}", fs=fs, mode="r"), mode="r")
    g = zarr.open(url, mode="r")
    return g[str(level)] if isinstance(g, zarr.Group) and str(level) in g else g

def on_bright_fraction(vol, X, Y, Z, scale, thr=100, n=400, seed=0):
    """Fraction of sampled valid surface points whose voxel (at this level) is >= thr. Discriminates on synthetic
    data; on real crushed scrolls it did NOT (see README)."""
    v = valid_mask(X); idx = np.argwhere(v); rng = np.random.default_rng(seed); sel = idx[rng.choice(len(idx), min(n, len(idx)), replace=False)]
    hits = 0
    for r, c in sel:
        z, y, x = int(round(Z[r, c] / scale)), int(round(Y[r, c] / scale)), int(round(X[r, c] / scale))
        if 0 <= z < vol.shape[0] and 0 <= y < vol.shape[1] and 0 <= x < vol.shape[2] and vol[z, y, x] >= thr: hits += 1
    return hits / len(sel)

def draw(vol, X, Y, Z, scale, n_slices=4, band=12, pad=120):
    v = valid_mask(X); zs = np.percentile(Z[v], np.linspace(12, 88, n_slices)).round().astype(int)
    cols = [(0, 0, 255), (0, 200, 255), (0, 255, 0), (255, 0, 255), (255, 200, 0), (255, 255, 255)]; panels = []
    for k, zi in enumerate(zs):
        m = v & (np.abs(Z - zi) < band)
        if m.sum() < 5: continue
        P = np.stack([X[m], Y[m]], 1) / scale
        x0, x1 = max(int(P[:, 0].min()) - pad, 0), int(P[:, 0].max()) + pad; y0, y1 = max(int(P[:, 1].min()) - pad, 0), int(P[:, 1].max()) + pad
        sl = np.asarray(vol[int(zi / scale), y0:y1, x0:x1]).astype(np.float32); nz = sl[sl > 0]
        if nz.size < 10: continue
        lo, hi = np.percentile(nz, [1, 99]); g = np.clip((sl - lo) / max(hi - lo, 1) * 255, 0, 255).astype(np.uint8); im = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
        col = cols[k % len(cols)]
        for x, y in P: cv2.circle(im, (int(x - x0), int(y - y0)), 2, col, -1)
        cv2.putText(im, f"z={int(zi)}  surface within +-{band} vox", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2); panels.append(im)
    if not panels: return None, zs
    W = max(p.shape[1] for p in panels)
    return np.concatenate([cv2.copyMakeBorder(p, 0, 6, 0, W - p.shape[1], cv2.BORDER_CONSTANT, value=(40, 40, 40)) for p in panels], 0), zs

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("tifxyz"); ap.add_argument("volume"); ap.add_argument("out")
    ap.add_argument("--level", type=int, default=1); ap.add_argument("--scale", type=float, default=None); ap.add_argument("--n", type=int, default=4)
    a = ap.parse_args(argv); scale = a.scale if a.scale is not None else 2.0 ** a.level
    X, Y, Z = read(a.tifxyz); vol = open_volume(a.volume, a.level); img, zs = draw(vol, X, Y, Z, scale, a.n)
    if img is not None: cv2.imwrite(a.out + "_xsec.png", img)
    res = {"z_levels": [int(z) for z in zs], "on_bright_fraction": on_bright_fraction(vol, X, Y, Z, scale), "panels": 0 if img is None else int(len(zs))}
    json.dump(res, open(a.out + "_xsec.json", "w"), indent=1); print(json.dumps(res)); return res

if __name__ == "__main__": main()
