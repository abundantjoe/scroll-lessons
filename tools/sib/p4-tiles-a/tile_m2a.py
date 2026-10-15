"""P4-D material M2a tiling for 20260623141924-w010-027 (RULES.md DECL-P4-4, via DECL-P4-2 item 2).

Provenance: Project HERCULES | owner the owner | [id removed]

Builder only: never opens, views or prints image pixels. Writes numbers, hashes and
PNG bytes (builder.png_bytes) only.

Frames:
- native: 20260608103018 (1.129 um) voxels, from the segment's 1.129 um tifxyz;
- 2p4: 20260411134726 (2.4 um) voxels. The segment's 2.4 um tifxyz is used at the same UV
  only if the grids correspond (rule CORR below, fixed before the run); otherwise the
  published affine 20260608103018 -> 20260411134726 (volume transform.json) is used.
  Both variants are saved when available; key suffix '__2p4' is the chosen one.

CORR: sample 20000 valid native vertices (seed 20260926). For each, map it through the
affine, and read the 2.4 um tifxyz bilinearly at the corresponding UV (grid index scaled
by gh2/gh1, gw2/gw1). The grids correspond iff the median 3-D residual <= 2.0 vox
(2.4 um frame) and the 95th percentile <= 5.0 vox.

Usage: python tile_m2a.py <download_dir> <out_dir>
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import time

import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from hercules.display import builder  # noqa: E402
from tile_w010_027 import TiledReader, canvas_mask  # noqa: E402

PROV = "Project HERCULES | owner the owner | [id removed]"
SEG = "20260623141924-w010-027"
OUT_SIDE = 1068
TILE_MM = 20.0
ELIGIBLE_FRAC = 0.5
MAX_POINTS = 4096
SEED = 20260926
INK_THR = 150
CORR_MED, CORR_P95 = 2.0, 5.0


def find(dl, suffix):
    m = glob.glob(os.path.join(dl, "*" + suffix))
    assert len(m) == 1, (suffix, m)
    return m[0]


def load_xyz(dl, tag):
    base = "mesh_20260623141924-on-%s.tifxyz_" % tag
    return np.stack([tifffile.imread(find(dl, base + a + ".tif")).astype(np.float32) for a in "xyz"], axis=-1)


def valid_of(P):
    return ~(P == -1).any(-1) & np.isfinite(P).all(-1)


def edge_lengths(P, valid, axis, block=256):
    """3-D lengths of 4-neighbour edges along one grid axis, both endpoints valid (row blocks)."""
    out = []
    gh = P.shape[0]
    if axis == 1:
        for y0 in range(0, gh, block):
            p, v = P[y0:y0 + block], valid[y0:y0 + block]
            m = v[:, 1:] & v[:, :-1]
            out.append(np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)[m])
    else:
        for y0 in range(0, gh - 1, block):
            p, v = P[y0:y0 + block + 1], valid[y0:y0 + block + 1]
            m = v[1:] & v[:-1]
            out.append(np.linalg.norm(p[1:] - p[:-1], axis=-1)[m])
    return np.concatenate(out)


def affine_apply(A, pts):
    A = np.asarray(A, np.float64)
    return (pts.astype(np.float64) @ A[:, :3].T + A[:, 3]).astype(np.float32)


def bilinear(P2, V2, fy, fx):
    """Bilinear read of grid P2 at fractional indices; NaN where any corner is invalid."""
    gh, gw = V2.shape
    y0 = np.clip(np.floor(fy).astype(np.int64), 0, gh - 2)
    x0 = np.clip(np.floor(fx).astype(np.int64), 0, gw - 2)
    ty, tx = (fy - y0)[:, None], (fx - x0)[:, None]
    ok = V2[y0, x0] & V2[y0 + 1, x0] & V2[y0, x0 + 1] & V2[y0 + 1, x0 + 1]
    ok &= (fy >= 0) & (fy <= gh - 1) & (fx >= 0) & (fx <= gw - 1)
    q = (P2[y0, x0] * (1 - ty) * (1 - tx) + P2[y0 + 1, x0] * ty * (1 - tx)
         + P2[y0, x0 + 1] * (1 - ty) * tx + P2[y0 + 1, x0 + 1] * ty * tx)
    q[~ok] = np.nan
    return q.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dl")
    ap.add_argument("out")
    a = ap.parse_args()
    t_start = time.time()
    dl = a.dl
    pred_path = find(dl, "mrg20736-1um-s1z2-tile256-stride128.tif")
    vmeta = json.load(open(find(dl, "20260608103018-1.129um-0.2m-78keV-masked.zarr_metadata.json")))
    vs = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "samplePixelSize":
                    vs.add(float(v))
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(vmeta)
    assert len(vs) == 1, vs
    voxel_mm = vs.pop()
    tr = json.load(open(find(dl, "20260608103018-1.129um-0.2m-78keV-masked.zarr_transform.json")))
    A = tr["transformation_matrix"]
    mmeta1 = json.load(open(find(dl, "on-20260608103018-1.129um.tifxyz_meta.json")))
    mmeta2 = json.load(open(find(dl, "on-20260411134726-2.4um.tifxyz_meta.json")))

    t0 = time.time()
    P = load_xyz(dl, "20260608103018-1.129um")
    V = valid_of(P)
    gh, gw = V.shape
    rd = TiledReader(pred_path)
    H, W = rd.H, rd.W
    sy, sx = H / gh, W / gw
    eh = edge_lengths(P, V, 1)
    ev = edge_lengths(P, V, 0)
    med_h, med_v = float(np.median(eh)), float(np.median(ev))
    allm = float(np.median(np.concatenate([eh, ev])))
    q = [float(v) for v in np.percentile(np.concatenate([eh, ev]), [1, 5, 25, 50, 75, 95, 99])]
    n_edges = int(eh.size + ev.size)
    del eh, ev
    scale_c = float(np.sqrt(sy * sx))
    px_per_mm = scale_c / (allm * voxel_mm)
    T = int(round(TILE_MM * px_per_mm))
    nr, nc = -(-H // T), -(-W // T)

    # affine sanity: native bbox through the affine vs the 2.4 um mesh bbox
    vp = P[V]
    bb1 = [vp.min(0).tolist(), vp.max(0).tolist()]
    bb1_aff = affine_apply(A, np.array(bb1, np.float32))
    del vp

    # CORR check against the 2.4 um tifxyz at the same UV
    P2 = load_xyz(dl, "20260411134726-2.4um")
    V2 = valid_of(P2)
    gh2, gw2 = V2.shape
    rng = np.random.default_rng(SEED)
    iv = np.flatnonzero(V.ravel())
    pick = np.sort(rng.choice(iv.size, min(20000, iv.size), replace=False))
    yy, xx = np.unravel_index(iv[pick], V.shape)
    del iv
    aff = affine_apply(A, P[yy, xx])
    corr = {"rule": "median <= %.1f and p95 <= %.1f vox (2.4 um frame) over 20000 valid native vertices, seed %d" % (CORR_MED, CORR_P95, SEED),
            "grid_native": [gh, gw], "grid_2p4": [gh2, gw2]}
    maps = {
        "scaled_index": (yy * (gh2 / gh), xx * (gw2 / gw)),
        "scaled_corner": (yy * ((gh2 - 1) / (gh - 1)), xx * ((gw2 - 1) / (gw - 1))),
    }
    best = None
    for name, (fy, fx) in maps.items():
        uvp = bilinear(P2, V2, fy.astype(np.float64), fx.astype(np.float64))
        d = np.linalg.norm(uvp - aff, axis=-1)
        ok = np.isfinite(d)
        st = {"n_compared": int(ok.sum())}
        if ok.any():
            st.update({"median_vox": float(np.median(d[ok])), "p95_vox": float(np.percentile(d[ok], 95)),
                       "max_vox": float(d[ok].max())})
        corr[name] = st
        if ok.sum() > 1000 and (best is None or st["median_vox"] < corr[best]["median_vox"]):
            best = name
    corresponds = bool(best is not None and corr[best]["median_vox"] <= CORR_MED and corr[best]["p95_vox"] <= CORR_P95)
    corr.update({"best_mapping": best, "grids_correspond": corresponds,
                 "chosen_2p4_frame_method": ("tifxyz 20260411134726 at same UV (%s, bilinear)" % best) if corresponds else "published affine 20260608103018 -> 20260411134726 (transform.json)"})
    del aff

    g = {
        "provenance": PROV, "segment": SEG, "declaration": "RULES.md DECL-P4-4 item 1 (M2a), item 2",
        "voxel_size_mm": voxel_mm,
        "voxel_size_source": "20260608103018 metadata.json samplePixelSize (all 20 entries equal, mm); consistent with volume name 1.129um",
        "mesh_meta_native": mmeta1, "mesh_meta_2p4": mmeta2,
        "grid_shape": [gh, gw], "canvas_shape": [H, W],
        "canvas_tiff": {"tile": [rd.th, rd.tw], "compression": int(rd.p.compression), "dtype": str(rd.p.dtype), "n_tiles": len(rd.p.dataoffsets)},
        "scale_canvas_per_grid": {"rows": sy, "cols": sx, "integer_exact": bool(H % gh == 0 and W % gw == 0 and sy == sx)},
        "canvas_note": "prediction rendered at L1 (x2): one canvas px = 2 native voxels at mesh scale; grid step 1/0.05 = 20 native vox = 10 canvas px expected",
        "mesh_valid": {"rule": "vertex valid iff none of x,y,z == -1 and all finite", "n_valid": int(V.sum()),
                       "n_total": int(gh * gw), "fraction": float(V.mean())},
        "edge_length_vox": {"n_edges": n_edges, "median": allm, "median_along_cols": med_h, "median_along_rows": med_v,
                            "pct_1_5_25_50_75_95_99": q},
        "px_per_mm": px_per_mm,
        "px_per_mm_formula": "canvas_px_per_grid_step / (median 3-D edge length [native vox] * voxel_size_mm)",
        "px_per_mm_by_axis": {"cols": sx / (med_h * voxel_mm), "rows": sy / (med_v * voxel_mm)},
        "nominal_px_per_mm_L1": 1.0 / (2 * voxel_mm),
        "tile_mm": TILE_MM, "T_canvas_px": T,
        "tile_grid": {"n_rows": nr, "n_cols": nc,
                      "rule": "tile (r,c) = rows [r*T,(r+1)*T), cols [c*T,(c+1)*T) from (0,0); pixels beyond the canvas count as not mesh-valid and are 0"},
        "canvas_mask_rule": "canvas px (i,j) -> grid (floor(i*gh/H), floor(j*gw/W)) nearest neighbour",
        "area_valid_cm2_grid": float(V.sum() * (allm * voxel_mm / 10) ** 2),
        "mesh_meta_area_cm2": float(mmeta1.get("area_vx2", 0) * (voxel_mm / 10) ** 2),
        "affine": {"matrix": A, "fixed_volume": tr.get("fixed_volume"), "native_bbox": bb1,
                   "native_bbox_through_affine": bb1_aff.tolist(), "mesh_2p4_bbox": mmeta2.get("bbox")},
        "frame_2p4_check": corr,
        "seconds": round(time.time() - t0, 1),
    }
    json.dump(g, open(os.path.join(a.out, "grid.json"), "w"), indent=1)
    print(json.dumps({k: g[k] for k in ("grid_shape", "canvas_shape", "scale_canvas_per_grid", "px_per_mm", "T_canvas_px", "tile_grid")}), flush=True)
    print(json.dumps(corr), flush=True)

    tiles_dir = os.path.join(a.out, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    cf = open(os.path.join(a.out, "tile_census.jsonl"), "w")
    pts = {}
    pts_path = os.path.join(a.out, "tile_points.npz")
    n_elig = 0
    for r in range(nr):
        for c in range(nc):
            y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
            key = "r%d_c%d" % (r, c)
            t1 = time.time()
            m = canvas_mask(V, H, W, y0, y1, x0, x1)
            vf = float(m.mean())
            rec = {"r": r, "c": c, "valid_fraction": vf, "eligible": vf >= ELIGIBLE_FRAC,
                   "canvas_rows": [y0, y1], "canvas_cols": [x0, x1]}
            if rec["eligible"]:
                crop = builder.model_map_u8(rd.read(y0, y1, x0, x1))
                raw_valid = crop[m]
                rec["raw_nonzero_outside_valid_frac"] = float((crop[~m] > 0).mean()) if (~m).any() else 0.0
                crop[~m] = 0
                disp = builder.area_downscale(crop, OUT_SIDE / T)
                assert disp.shape == (OUT_SIDE, OUT_SIDE) and disp.dtype == np.uint8, disp.shape
                b = builder.png_bytes(disp)
                fn = "%s_%s.png" % (SEG, key)
                with open(os.path.join(tiles_dir, fn), "wb") as f:
                    f.write(b)
                rec.update({"file": "tiles/" + fn, "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                            "valid_px": int(raw_valid.size), "mean": float(raw_valid.mean()), "std": float(raw_valid.std()),
                            "frac_ge_150": float((raw_valid >= INK_THR).mean()),
                            "stats_domain": "raw uint8 canvas pixels inside mesh-valid, before downscale"})
                gy0, gy1 = -(-y0 * gh // H), min(-(-y1 * gh // H), gh)
                gx0, gx1 = -(-x0 * gw // W), min(-(-x1 * gw // W), gw)
                vsub = V[gy0:gy1, gx0:gx1]
                ly, lx = np.nonzero(vsub)
                trng = np.random.default_rng([SEED, r, c])
                if ly.size > MAX_POINTS:
                    s = np.sort(trng.choice(ly.size, MAX_POINTS, replace=False))
                    ly, lx = ly[s], lx[s]
                gyy, gxx = ly + gy0, lx + gx0
                nat = P[gyy, gxx]
                pts[key] = nat.astype(np.float32)
                pts[key + "__2p4_affine"] = affine_apply(A, nat)
                if corresponds:
                    sc ={"scaled_index": (gh2 / gh, gw2 / gw), "scaled_corner": ((gh2 - 1) / (gh - 1), (gw2 - 1) / (gw - 1))}[best]
                    pts[key + "__2p4_uv"] = bilinear(P2, V2, gyy * sc[0], gxx * sc[1])
                    pts[key + "__2p4"] = pts[key + "__2p4_uv"]
                else:
                    pts[key + "__2p4"] = pts[key + "__2p4_affine"]
                pts[key + "__grid_rc"] = np.stack([gyy, gxx], 1).astype(np.int32)
                rec.update({"n_mesh_vertices_in_tile": int(vsub.sum()), "n_points_saved": int(gyy.size),
                            "grid_rows": [gy0, gy1], "grid_cols": [gx0, gx1]})
                n_elig += 1
            rec["seconds"] = round(time.time() - t1, 2)
            cf.write(json.dumps(rec) + "\n")
            cf.flush()
            if rec["eligible"]:
                print("tile", key, "vf=%.3f" % vf, "n_elig=%d" % n_elig, "%.1fs" % rec["seconds"], flush=True)
                if n_elig % 20 == 0:
                    np.savez(pts_path + ".tmp.npz", **pts)
                    os.replace(pts_path + ".tmp.npz", pts_path)
    np.savez(pts_path + ".tmp.npz", **pts)
    os.replace(pts_path + ".tmp.npz", pts_path)
    print("ALL_DONE", n_elig, "total_s=%.0f" % (time.time() - t_start), flush=True)


if __name__ == "__main__":
    main()
