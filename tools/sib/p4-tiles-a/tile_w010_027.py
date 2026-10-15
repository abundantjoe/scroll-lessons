"""P4-B material M1 tiling for 20260701183124-w010-027 (RULES.md DECL-P4-2 item 2).

Provenance: Project HERCULES | owner the owner | [id removed]

Builder only: never opens, views or prints image pixels. Writes numbers, hashes and
PNG bytes (builder.png_bytes) only.

Usage: python tile_w010_027.py <download_dir> <out_dir> [--phase grid|tiles] [--first N]
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from hercules.display import builder  # noqa: E402

PROV = "Project HERCULES | owner the owner | [id removed]"
SEG = "20260701183124-w010-027"
OUT_SIDE = 1068
TILE_MM = 20.0
ELIGIBLE_FRAC = 0.5
MAX_POINTS = 4096
POINT_SEED = 20260926
INK_THR = 150


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


class TiledReader:
    """Region reader for a single-page tiled TIFF, decoding only the tiles needed."""

    def __init__(self, path):
        self.tf = tifffile.TiffFile(path)
        self.p = self.tf.pages[0]
        assert self.p.is_tiled and len(self.tf.pages) == 1
        self.H, self.W = self.p.shape
        self.th, self.tw = self.p.tilelength, self.p.tilewidth
        self.ntx = -(-self.W // self.tw)
        self.fh = self.tf.filehandle

    def read(self, y0, y1, x0, x1):
        """Rows [y0,y1), cols [x0,x1), clipped to the canvas; outside the canvas = 0."""
        out = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, self.H), max(x0, 0), min(x1, self.W)
        if cy0 >= cy1 or cx0 >= cx1:
            return out
        for ty in range(cy0 // self.th, (cy1 - 1) // self.th + 1):
            for tx in range(cx0 // self.tw, (cx1 - 1) // self.tw + 1):
                idx = ty * self.ntx + tx
                self.fh.seek(self.p.dataoffsets[idx])
                data = self.fh.read(self.p.databytecounts[idx])
                seg, _, _ = self.p.decode(data, idx)
                seg = np.asarray(seg).reshape(self.th, self.tw)
                gy, gx = ty * self.th, tx * self.tw
                sy0, sy1 = max(cy0, gy), min(cy1, gy + self.th)
                sx0, sx1 = max(cx0, gx), min(cx1, gx + self.tw)
                out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = seg[sy0 - gy:sy1 - gy, sx0 - gx:sx1 - gx]
        return out


def find(dl, suffix):
    m = glob.glob(os.path.join(dl, "*" + suffix))
    assert len(m) == 1, (suffix, m)
    return m[0]


def load_grid(dl):
    base = "mesh_20260701183124-on-20260411134726-2.4um.tifxyz_"
    xyz = [tifffile.imread(find(dl, base + a + ".tif")).astype(np.float32) for a in "xyz"]
    return np.stack(xyz, axis=-1)  # (gh, gw, 3) volume voxels, order x, y, z


def geometry(dl, pred_path):
    t0 = time.time()
    meta_vol = json.load(open(find(dl, "masked.zarr_metadata.json")))
    acq = meta_vol["scan"]["tomo"]["acquisition"]["detector"]
    voxel_mm = float(acq["samplePixelSize"])  # mm (0.0024 mm = 2.4 um; volume name 2.400um)
    meta_mesh = json.load(open(find(dl, "tifxyz_meta.json")))
    P = load_grid(dl)
    gh, gw, _ = P.shape
    invalid_each = [(P[..., k] == -1) for k in range(3)]
    valid = ~(invalid_each[0] | invalid_each[1] | invalid_each[2])
    nonfinite = int((~np.isfinite(P)).any(-1).sum())
    valid &= np.isfinite(P).all(-1)
    rd = TiledReader(pred_path)
    H, W = rd.H, rd.W
    sy, sx = H / gh, W / gw
    # 3-D edge lengths between 4-neighbour valid vertices
    ev = valid[:, 1:] & valid[:, :-1]
    eh = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[ev]
    vv = valid[1:, :] & valid[:-1, :]
    evl = np.linalg.norm(P[1:, :] - P[:-1, :], axis=-1)[vv]
    all_e = np.concatenate([eh, evl])
    med = float(np.median(all_e))
    med_h, med_v = float(np.median(eh)), float(np.median(evl))
    scale_c = float(np.sqrt(sy * sx)) if sy != sx else float(sy)
    px_per_mm = scale_c / (med * voxel_mm)
    T = int(round(TILE_MM * px_per_mm))
    q = lambda a: [float(v) for v in np.percentile(a, [1, 5, 25, 50, 75, 95, 99])]
    g = {
        "provenance": PROV,
        "segment": SEG,
        "voxel_size_mm": voxel_mm,
        "voxel_size_source": "volume metadata.json scan.tomo.acquisition.detector.samplePixelSize (mm); consistent with volume name 2.400um",
        "mesh_meta": meta_mesh,
        "grid_shape": [gh, gw],
        "canvas_shape": [H, W],
        "canvas_tiff": {"tile": [rd.th, rd.tw], "compression": int(rd.p.compression), "dtype": str(rd.p.dtype), "n_tiles": len(rd.p.dataoffsets)},
        "scale_canvas_per_grid": {"rows": sy, "cols": sx, "integer_exact": bool(H == 20 * gh and W == 20 * gw)},
        "mesh_scale_meta_inverse": [1.0 / meta_mesh["scale"][0], 1.0 / meta_mesh["scale"][1]],
        "mesh_valid": {"rule": "vertex valid iff none of x,y,z == -1 and all finite",
                       "n_valid": int(valid.sum()), "n_total": int(gh * gw),
                       "fraction": float(valid.mean()), "n_nonfinite": nonfinite,
                       "n_minus1_per_axis": [int(a.sum()) for a in invalid_each]},
        "edge_length_vox": {"n_edges": int(all_e.size), "median": med,
                            "median_along_cols": med_h, "median_along_rows": med_v,
                            "pct_1_5_25_50_75_95_99": q(all_e)},
        "grid_step_mm_median": med * voxel_mm,
        "px_per_mm": px_per_mm,
        "px_per_mm_formula": "canvas_px_per_grid_step / (median 3-D edge length [vox] * voxel_size_mm)",
        "px_per_mm_by_axis": {"cols": sx / (med_h * voxel_mm), "rows": sy / (med_v * voxel_mm)},
        "nominal_px_per_mm_one_px_per_voxel": 1.0 / voxel_mm,
        "tile_mm": TILE_MM,
        "T_canvas_px": T,
        "tile_grid": {"n_rows": -(-H // T), "n_cols": -(-W // T),
                      "rule": "tile (r,c) = rows [r*T,(r+1)*T), cols [c*T,(c+1)*T) from (0,0); pixels beyond the canvas count as not mesh-valid and are 0"},
        "canvas_mask_rule": "canvas px (i,j) -> grid (floor(i*gh/H), floor(j*gw/W)) nearest neighbour (= i//20, j//20 here)",
        "area_valid_cm2_grid": float(valid.sum() * (med * voxel_mm / 10) ** 2),
        "mesh_meta_area_cm2": float(meta_mesh.get("area_vx2", 0) * (voxel_mm / 10) ** 2),
        "seconds": round(time.time() - t0, 1),
    }
    return g, P, valid, rd


def canvas_mask(valid, H, W, y0, y1, x0, x1):
    gh, gw = valid.shape
    ys = np.arange(y0, y1)
    xs = np.arange(x0, x1)
    iny = (ys >= 0) & (ys < H)
    inx = (xs >= 0) & (xs < W)
    gy = np.clip((ys * gh) // H, 0, gh - 1)
    gx = np.clip((xs * gw) // W, 0, gw - 1)
    m = valid[np.ix_(gy, gx)]
    m &= iny[:, None] & inx[None, :]
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dl")
    ap.add_argument("out")
    ap.add_argument("--first", type=int, default=0, help="stop after N eligible tiles (0 = all)")
    ap.add_argument("--skip-existing", action="store_true")
    a = ap.parse_args()
    t_start = time.time()
    pred_path = find(a.dl, "new_canon_autoresearch_recipe-tile256-stride128.tif")
    g, P, valid, rd = geometry(a.dl, pred_path)
    json.dump(g, open(os.path.join(a.out, "grid.json"), "w"), indent=1)
    print(json.dumps({k: g[k] for k in ("grid_shape", "canvas_shape", "px_per_mm", "T_canvas_px", "tile_grid")}), flush=True)
    H, W, T = rd.H, rd.W, g["T_canvas_px"]
    gh, gw = valid.shape
    nr, nc = g["tile_grid"]["n_rows"], g["tile_grid"]["n_cols"]
    tiles_dir = os.path.join(a.out, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    census_path = os.path.join(a.out, "tile_census.jsonl")
    done = {}
    if a.skip_existing and os.path.exists(census_path):
        for l in open(census_path):
            d = json.loads(l)
            done[(d["r"], d["c"])] = d
    cf = open(census_path, "a")
    pts_path = os.path.join(a.out, "tile_points.npz")
    pts = dict(np.load(pts_path)) if (a.skip_existing and os.path.exists(pts_path)) else {}
    n_elig = 0
    for r in range(nr):
        for c in range(nc):
            y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
            key = "r%d_c%d" % (r, c)
            if (r, c) in done:
                n_elig += int(done[(r, c)]["eligible"])
                continue
            t0 = time.time()
            m = canvas_mask(valid, H, W, y0, y1, x0, x1)
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
                assert b[:8] == b"\x89PNG\r\n\x1a\n"
                fn = "w010-027_%s.png" % key
                with open(os.path.join(tiles_dir, fn), "wb") as f:
                    f.write(b)
                rec.update({
                    "file": "tiles/" + fn, "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                    "valid_px": int(raw_valid.size),
                    "mean": float(raw_valid.mean()), "std": float(raw_valid.std()),
                    "frac_ge_150": float((raw_valid >= INK_THR).mean()),
                    "stats_domain": "raw uint8 canvas pixels inside mesh-valid, before downscale",
                })
                # 3-D mesh points: grid vertices whose canvas cell origin lies in the tile
                gy0, gy1 = -(-y0 * gh // H), min(-(-y1 * gh // H), gh)
                gx0, gx1 = -(-x0 * gw // W), min(-(-x1 * gw // W), gw)
                sub = P[gy0:gy1, gx0:gx1][valid[gy0:gy1, gx0:gx1]]
                rng = np.random.default_rng([POINT_SEED, r, c])
                if sub.shape[0] > MAX_POINTS:
                    sub = sub[np.sort(rng.choice(sub.shape[0], MAX_POINTS, replace=False))]
                pts[key] = sub.astype(np.float32)
                rec.update({"n_mesh_vertices_in_tile": int(valid[gy0:gy1, gx0:gx1].sum()),
                            "n_points_saved": int(sub.shape[0]),
                            "grid_rows": [gy0, gy1], "grid_cols": [gx0, gx1]})
                n_elig += 1
            rec["seconds"] = round(time.time() - t0, 2)
            cf.write(json.dumps(rec) + "\n")
            cf.flush()
            if rec["eligible"]:
                np.savez(pts_path + ".tmp.npz", **pts)
                os.replace(pts_path + ".tmp.npz", pts_path)
                print("tile", key, "vf=%.3f" % vf, "n_elig=%d" % n_elig, "%.1fs" % rec["seconds"], flush=True)
            if a.first and n_elig >= a.first:
                print("FIRST_BATCH_DONE", n_elig, flush=True)
                return
    print("ALL_DONE", n_elig, "total_s=%.0f" % (time.time() - t_start), flush=True)


if __name__ == "__main__":
    main()
