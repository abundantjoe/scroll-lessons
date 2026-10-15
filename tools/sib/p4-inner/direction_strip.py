[line withheld: prize-candidate detail under review]
Per z-level, the mesh columns give a polyline; along each of 64 rays from the umbilicus the polyline is crossed
once per winding. For consecutive crossings (ordered by mesh column) we record whether radius increases with
column. Same-angle comparison removes the scroll's out-of-roundness, which dominates per-tile radius here.
Provenance: Project HERCULES | owner the owner | [id removed]
[line withheld: prize-candidate detail under review]
"""
import glob, json, sys, urllib.request
import numpy as np, tifffile
dl, outp = sys.argv[1:3]
U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in json.loads(urllib.request.urlopen(
    "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/representations/umbilicus/20260411134726-umbilicus-20260524235033.json").read())["control_points"]]), float)
G = np.stack([tifffile.imread(glob.glob(f"{dl}/*{sys.argv[3]}*tifxyz_{c}.tif")[0]).astype(np.float64) for c in "xyz"], -1)
G[(G == -1).any(-1)] = np.nan
Z = G[..., 2]
inc = []; per_z = []
for z0 in np.linspace(np.nanpercentile(Z, 5), np.nanpercentile(Z, 95), 40):
    s = Z - z0
    # z may increase or decrease along rows: take first sign change per column
    c = ((s[:-1] >= 0) & (s[1:] < 0)) | ((s[:-1] < 0) & (s[1:] >= 0))
    i = np.argmax(c, 0); j = np.arange(Z.shape[1]); ok = c[i, j]
    f = (Z[i, j] - z0) / (Z[i, j] - Z[i + 1, j] + 1e-9)
    xy = G[i, j, :2] * (1 - f)[:, None] + G[i + 1, j, :2] * f[:, None]
    idx = np.where(ok & np.isfinite(xy[:, 0]))[0]
    if len(idx) < 0.5 * Z.shape[1]: continue
    cx, cy = np.interp(z0, U[:, 0], U[:, 1]), np.interp(z0, U[:, 0], U[:, 2])
    p = xy[idx]; r = np.hypot(p[:, 0] - cx, p[:, 1] - cy); tu = np.unwrap(np.arctan2(p[:, 1] - cy, p[:, 0] - cx))
    zi = []
    for k in range(64):
        a = 2 * np.pi * k / 64; q = (tu - a) / (2 * np.pi); n = np.floor(q); w = np.where(np.diff(n) != 0)[0]
        w = [m for m in w if idx[m + 1] - idx[m] < 40]
        rr = [r[m] + (np.round(max(n[m], n[m + 1])) - q[m]) / (q[m + 1] - q[m]) * (r[m + 1] - r[m]) for m in w]
        for a1, a2 in zip(rr[:-1], rr[1:]): zi.append(a2 > a1)
    inc += zi; per_z.append({"z_mm": round(z0 * 0.0024, 1), "n_pairs": len(zi), "frac_r_increases_with_col": round(float(np.mean(zi)), 3) if zi else None,
                             "total_turn_deg": round(float(abs(tu[-1] - tu[0])) * 180 / np.pi, 1)})
res = {"provenance": "Project HERCULES | owner the owner | [id removed]", "method": __doc__.split("usage")[0].strip(),
       "n_pairs": len(inc), "frac_r_increases_with_col": round(float(np.mean(inc)), 4),
       "outward_direction": "increasing column" if np.mean(inc) > 0.5 else "decreasing column", "per_z": per_z}
json.dump(res, open(outp, "w"), indent=1)
print(res["n_pairs"], res["frac_r_increases_with_col"], res["outward_direction"], [d["total_turn_deg"] for d in per_z[:5]])
