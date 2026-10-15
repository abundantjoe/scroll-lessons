"""Unroll patches (tifxyz + a per-patch 2-D map rendered on it) around one winding into a single strip.
Every map pixel gets its 3-D position by bilinear interpolation of the patch tifxyz; it lands at
(u, v) = (azimuth about the axis x R_ref, z) in voxel units. Overlaps are averaged; 1-3 px holes are closed.
usage: python -m ringstrip.unroll <out.png> <axis_x> <axis_y> <R_ref> <map_name> <patch_dir>...
  patch_dir holds tifxyz/ (x.tif, y.tif, z.tif) and <map_name> (png, same aspect as the tifxyz grid)."""
import sys, os, json, numpy as np, cv2, tifffile

def read_tifxyz(d):
    return [tifffile.imread(os.path.join(d, c + ".tif")).astype(np.float32) for c in "xyz"]

def unroll(patches, ux, uy, Rr, map_name="map.png", scale_px_per_cell=None):
    pts = []
    for d in patches:
        T = os.path.join(d, "tifxyz") if os.path.isdir(os.path.join(d, "tifxyz")) else d
        f = os.path.join(d, map_name)
        if not os.path.exists(f): continue
        X, Y, Z = read_tifxyz(T); im = cv2.imread(f, cv2.IMREAD_GRAYSCALE); h, w = im.shape
        v = ((X > 0) & (X != -1)).astype(np.float32); up = lambda a: cv2.resize(a, (w, h), interpolation=cv2.INTER_LINEAR)
        Xu, Yu, Zu, Vu = up(X), up(Y), up(Z), up(v); ok = (Vu > 0.999) & (im > 0)
        th = np.arctan2(Yu[ok] - uy, Xu[ok] - ux); pts.append((th, Zu[ok], im[ok].astype(np.float32), d))
    if not pts: raise SystemExit("no maps")
    th_all = np.concatenate([p[0] for p in pts]); ref = np.angle(np.mean(np.exp(1j * th_all))) + np.pi
    zs = np.concatenate([p[1] for p in pts]); z0 = np.floor(zs.min())
    U = [np.mod(p[0] - ref, 2 * np.pi) * Rr for p in pts]; u0 = np.floor(min(u.min() for u in U))
    W = int(max(u.max() for u in U) - u0) + 2; H = int(zs.max() - z0) + 2
    acc = np.zeros((H, W), np.float32); cnt = np.zeros((H, W), np.float32)
    for (th, z, val, d), u in zip(pts, U):
        xi = np.round(u - u0).astype(int); yi = np.round(z - z0).astype(int); np.add.at(acc, (yi, xi), val); np.add.at(cnt, (yi, xi), 1)
    img = np.where(cnt > 0, acc / np.maximum(cnt, 1), 0).astype(np.uint8); m = (cnt > 0).astype(np.uint8)
    mc = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    fill = cv2.inpaint(img, ((mc > 0) & (m == 0)).astype(np.uint8), 3, cv2.INPAINT_TELEA); img = np.where(mc > 0, fill, 0).astype(np.uint8)[::-1]
    meta = {"axis": [ux, uy], "R_ref": Rr, "cut_azimuth_rad": float(ref), "z0": float(z0), "u0": float(u0), "size": [H, W], "patches": [p[3] for p in pts], "coverage_px": int((mc > 0).sum())}
    return img, meta

def main(argv=None):
    a = argv or sys.argv[1:]; out, ux, uy, Rr, name = a[0], float(a[1]), float(a[2]), float(a[3]), a[4]; img, meta = unroll(a[5:], ux, uy, Rr, name)
    cv2.imwrite(out, img, [cv2.IMWRITE_PNG_COMPRESSION, 9]); json.dump(meta, open(os.path.splitext(out)[0] + ".json", "w"), indent=1); print("strip", img.shape, "->", out); return img, meta

if __name__ == "__main__": main()
