"""P4-B tiler for segment 20260701183125-w028-037 (RULES.md DECL-P4-2 items 1-2, material M1).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile, map or CT pixel is ever displayed or printed. PNG bytes are
hashed and written, never opened. Display chain (I2): raw uint8 prediction, 0 outside
mesh-valid, builder.area_downscale (cv2.INTER_AREA) to 1068 x 1068, builder.png_bytes.

Usage: python tile_w028_037.py <download_dir> <out_dir> [workers]
"""
import hashlib
import json
import os
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np
import tifffile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from hercules.display.builder import area_downscale, model_map_u8, png_bytes  # noqa: E402

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
SEG = "20260701183125-w028-037"
TILE_MM = 20.0
OUT_SIDE = 1068
MIN_VALID = 0.5
MAX_PTS = 4096
PTS_SEED = 20260926
INK_THR = 150

DL = OUT = None
G = {}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def find(dl, needle):
    m = [os.path.join(dl, f) for f in sorted(os.listdir(dl)) if needle in f]
    assert len(m) == 1, (needle, m)
    return m[0]


def load_grid(dl):
    xyz = []
    for a in "xyz":
        xyz.append(tifffile.imread(find(dl, f"2.4um.tifxyz_{a}.tif")).astype(np.float32))
    return xyz


def grid_geometry(dl, pred_shape, voxel_mm):
    x, y, z = load_grid(dl)
    gh, gw = x.shape
    neg = [(a == -1) for a in (x, y, z)]
    fin = [np.isfinite(a) for a in (x, y, z)]
    valid = ~(neg[0] | neg[1] | neg[2]) & fin[0] & fin[1] & fin[2]
    info = {
        "grid_shape": [gh, gw],
        "grid_vertices": int(gh * gw),
        "minus1_count_x_y_z": [int(n.sum()) for n in neg],
        "minus1_all_three_agree": bool(np.array_equal(neg[0], neg[1]) and np.array_equal(neg[0], neg[2])),
        "nonfinite_count": int(sum((~f).sum() for f in fin)),
        "mesh_valid_vertices": int(valid.sum()),
        "mesh_valid_fraction": float(valid.mean()),
    }
    P = np.stack([x, y, z], axis=-1).astype(np.float64)
    ec = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[valid[:, 1:] & valid[:, :-1]]
    er = np.linalg.norm(P[1:, :] - P[:-1, :], axis=-1)[valid[1:, :] & valid[:-1, :]]
    del P
    both = np.concatenate([ec, er])
    q = lambda a: {k: float(v) for k, v in zip(("p01", "p05", "p25", "median", "p75", "p95", "p99"),
                                                np.percentile(a, [1, 5, 25, 50, 75, 95, 99]))}
    sy, sx = pred_shape[0] / gh, pred_shape[1] / gw
    assert sy == sx, (sy, sx)
    s = float(sy)
    med = float(np.median(both))
    ppm = s / (med * voxel_mm)
    T = int(round(TILE_MM * ppm))
    info.update({
        "canvas_shape": list(pred_shape),
        "canvas_per_grid_scale_rows_cols": [sy, sx],
        "edge_len_vx_along_cols": dict(n=int(ec.size), **q(ec)),
        "edge_len_vx_along_rows": dict(n=int(er.size), **q(er)),
        "edge_len_vx_both": dict(n=int(both.size), **q(both)),
        "voxel_mm": voxel_mm,
        "median_edge_mm": med * voxel_mm,
        "px_per_mm": ppm,
        "px_per_mm_cols_only": s / (float(np.median(ec)) * voxel_mm),
        "px_per_mm_rows_only": s / (float(np.median(er)) * voxel_mm),
        "px_per_mm_nominal_one_px_per_voxel": 1.0 / voxel_mm,
        "formula": "px_per_mm = (canvas px per grid step) / (median 3-D edge length of valid "
                   "row+col grid edges in voxels x voxel_mm)",
        "T_px": T,
        "T_formula": "T = round(20 mm x px_per_mm)",
        "display_scale": OUT_SIDE / T,
        "display_px_per_mm": OUT_SIDE / TILE_MM,
        "canvas_mask_rule": "canvas px (i, j) -> grid (floor(i / s), floor(j / s)), s = canvas/grid "
                            "scale (nearest neighbour; identical to centre-aligned nearest for integer s); "
                            "canvas px outside the canvas extent count as not mesh-valid",
    })
    return info, valid, (x, y, z), s, T


def tile_valid_fractions(valid, s, T, H, W):
    nr, nc = -(-H // T), -(-W // T)
    gi_of_row = (np.arange(H) // s).astype(np.int64)
    gj_of_col = (np.arange(W) // s).astype(np.int64)
    gh, gw = valid.shape
    out = np.zeros((nr, nc))
    for r in range(nr):
        rows = gi_of_row[r * T:min((r + 1) * T, H)]
        wr = np.bincount(rows, minlength=gh).astype(np.float64)
        colsum = wr @ valid.astype(np.float64)  # (gw,)
        for c in range(nc):
            cols = gj_of_col[c * T:min((c + 1) * T, W)]
            wc = np.bincount(cols, minlength=gw).astype(np.float64)
            out[r, c] = float(colsum @ wc) / float(T * T)
    return out


def _init(pred_path, grid_valid, s, T):
    t = tifffile.TiffFile(pred_path)
    p = t.pages[0]
    G.update(path=pred_path, offs=np.asarray(p.dataoffsets), cnts=np.asarray(p.databytecounts),
             tw=p.tilewidth, tl=p.tilelength, H=p.shape[0], W=p.shape[1], valid=grid_valid, s=s, T=T,
             pred_mod=p.predictor if hasattr(p, "predictor") else None)
    t.close()
    G["ntx"] = -(-G["W"] // G["tw"])
    G["f"] = open(pred_path, "rb")


def read_region(y0, y1, x0, x1):
    """Decode canvas rows [y0,y1), cols [x0,x1) (clipped to the canvas) from the deflate tiles."""
    tl, tw, f = G["tl"], G["tw"], G["f"]
    out = np.zeros((y1 - y0, x1 - x0), np.uint8)
    for ty in range(y0 // tl, (y1 - 1) // tl + 1):
        for tx in range(x0 // tw, (x1 - 1) // tw + 1):
            k = ty * G["ntx"] + tx
            f.seek(int(G["offs"][k]))
            buf = zlib.decompress(f.read(int(G["cnts"][k])))
            a = np.frombuffer(buf, np.uint8).reshape(tl, tw)
            ay0, ax0 = ty * tl, tx * tw
            sy0, sy1 = max(y0, ay0), min(y1, ay0 + tl)
            sx0, sx1 = max(x0, ax0), min(x1, ax0 + tw)
            out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a[sy0 - ay0:sy1 - ay0, sx0 - ax0:sx1 - ax0]
    return out


def do_tile(rc):
    r, c, vfrac = rc
    t0 = time.time()
    T, s, H, W = G["T"], G["s"], G["H"], G["W"]
    y0, x0 = r * T, c * T
    y1, x1 = min(y0 + T, H), min(x0 + T, W)
    crop = np.zeros((T, T), np.uint8)
    crop[:y1 - y0, :x1 - x0] = read_region(y0, y1, x0, x1)
    crop = model_map_u8(crop)
    gi = (np.arange(y0, y1) // s).astype(np.int64)
    gj = (np.arange(x0, x1) // s).astype(np.int64)
    m = np.zeros((T, T), bool)
    m[:y1 - y0, :x1 - x0] = G["valid"][np.ix_(gi, gj)]
    crop[~m] = 0
    nval = int(m.sum())
    hist = np.bincount(crop[m], minlength=256).astype(np.float64)
    v = np.arange(256, dtype=np.float64)
    mean = float((hist * v).sum() / nval)
    std = float(np.sqrt((hist * (v - mean) ** 2).sum() / nval))
    fge = float(hist[INK_THR:].sum() / nval)
    del m
    disp = area_downscale(crop, OUT_SIDE / T)
    assert disp.shape == (OUT_SIDE, OUT_SIDE) and disp.dtype == np.uint8, disp.shape
    del crop
    b = png_bytes(disp)
    assert b[:8] == b"\x89PNG\r\n\x1a\n"
    chunks, i = [], 8
    while i < len(b):
        n = int.from_bytes(b[i:i + 4], "big")
        chunks.append(b[i + 4:i + 8].decode("ascii"))
        i += 12 + n
    assert set(chunks) <= {"IHDR", "IDAT", "IEND"}, chunks
    name = f"{SEG[15:]}_r{r}_c{c}.png"
    with open(os.path.join(OUT, "tiles", name), "wb") as fo:
        fo.write(b)
    return {"r": r, "c": c, "file": f"tiles/{name}", "canvas_rows": [y0, y0 + T], "canvas_cols": [x0, x0 + T],
            "in_canvas_rows": [y0, y1], "in_canvas_cols": [x0, x1], "valid_fraction": vfrac,
            "valid_px": nval, "valid_fraction_check": nval / float(T * T),
            "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b), "png_chunks": sorted(set(chunks)),
            "stats_valid_raw": {"mean": mean, "std": std, "frac_ge_150": fge},
            "secs": round(time.time() - t0, 2)}


def main():
    global DL, OUT
    DL, OUT = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    t_start = time.time()
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    fetch = [{k: v for k, v in json.loads(l).items() if k != "local"}
             for l in open(os.path.join(DL, "fetch.jsonl"))]
    vmeta = json.load(open(find(DL, "masked.zarr_metadata.json")))
    voxel_mm = float(vmeta["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    mmeta = json.load(open(find(DL, "2.4um.tifxyz_meta.json")))
    pred_path = find(DL, "tile256-stride128.tif")
    with tifffile.TiffFile(pred_path) as t:
        p = t.pages[0]
        pinfo = {"shape": list(p.shape), "dtype": str(p.dtype), "compression": int(p.compression),
                 "predictor": int(getattr(p, "predictor", 1)), "tiled": bool(p.is_tiled),
                 "tile": [p.tilelength, p.tilewidth], "n_tiles": len(p.dataoffsets),
                 "image_description": p.description}
        assert p.dtype == np.uint8 and int(p.compression) == 32946 and int(getattr(p, "predictor", 1)) == 1
        # self-check of the zlib path against tifffile's own decoder on 3 TIFF tiles (hashes only)
        fh = t.filehandle
        checks = []
        for k in (0, len(p.dataoffsets) // 2, len(p.dataoffsets) - 1):
            fh.seek(p.dataoffsets[k])
            raw = fh.read(p.databytecounts[k])
            ref = p.decode(raw, k)[0]
            mine = np.frombuffer(zlib.decompress(raw), np.uint8).reshape(p.tilelength, p.tilewidth)
            checks.append(bool(np.array_equal(np.asarray(ref).reshape(mine.shape), mine)))
        assert all(checks), checks
        pinfo["zlib_decode_matches_tifffile_on_tiles"] = checks
    info, valid, (x, y, z), s, T = grid_geometry(DL, pinfo["shape"], voxel_mm)
    H, W = pinfo["shape"]
    vf = tile_valid_fractions(valid, s, T, H, W)
    nr, nc = vf.shape
    info.update({"voxel_mm_source": "volume metadata.json scan.tomo.acquisition.detector.samplePixelSize (mm)",
                 "mesh_meta": mmeta, "area_cm2_from_meta": mmeta["area_vx2"] * voxel_mm ** 2 / 100.0,
                 "prediction_tiff": pinfo, "tile_grid_rows_cols": [nr, nc],
                 "tiles_total": int(nr * nc), "tiles_read_eligible": int((vf >= MIN_VALID).sum()),
                 "tile_valid_fraction_matrix": [[round(float(a), 6) for a in row] for row in vf],
                 "edge_tile_rule": "tiles extending past the canvas are zero-padded to T x T; padded px are "
                                   "not mesh-valid and count in the T^2 denominator",
                 "fetch": fetch, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    info = {"provenance": PROV, **info}
    json.dump(info, open(os.path.join(OUT, "grid.json"), "w"), indent=1)
    print("grid", json.dumps({k: info[k] for k in ("grid_shape", "canvas_shape", "px_per_mm", "T_px",
                                                   "tile_grid_rows_cols", "tiles_read_eligible")}), flush=True)

    elig = [(r, c, float(vf[r, c])) for r in range(nr) for c in range(nc) if vf[r, c] >= MIN_VALID]
    # mesh points per tile: vertex (gi, gj) sits at canvas (gi*s, gj*s)
    pts = {}
    gh, gw = valid.shape
    for r, c, _ in elig:
        i0, i1 = int(np.ceil(r * T / s)), min(int(np.ceil((r + 1) * T / s)), gh)
        j0, j1 = int(np.ceil(c * T / s)), min(int(np.ceil((c + 1) * T / s)), gw)
        vi, vj = np.nonzero(valid[i0:i1, j0:j1])
        n = vi.size
        if n > MAX_PTS:
            sel = np.sort(np.random.default_rng(PTS_SEED + 1000 * r + c).choice(n, MAX_PTS, replace=False))
            vi, vj = vi[sel], vj[sel]
        gi_, gj_ = vi + i0, vj + j0
        pts[f"r{r}_c{c}"] = (np.stack([x[gi_, gj_], y[gi_, gj_], z[gi_, gj_]], 1).astype(np.float32), n)
    np.savez_compressed(os.path.join(OUT, "tile_points.npz"), **{k: v[0] for k, v in pts.items()})
    del x, y, z

    recs = []
    jl = open(os.path.join(OUT, "tiles.jsonl"), "w")
    with Pool(workers, initializer=_init, initargs=(pred_path, valid, s, T)) as pool:
        for rec in pool.imap(do_tile, elig):
            k = f"r{rec['r']}_c{rec['c']}"
            rec["mesh_points_key"] = k
            rec["mesh_valid_vertices_in_tile"] = int(pts[k][1])
            rec["mesh_points_saved"] = int(pts[k][0].shape[0])
            recs.append(rec)
            jl.write(json.dumps(rec) + "\n")
            jl.flush()
            print("tile", k, rec["secs"], len(recs), "/", len(elig), flush=True)
    jl.close()

    pred_fetch = [f for f in fetch if f["key"].endswith("tile256-stride128.tif")][0]
    mesh_fetch = {os.path.basename(f["key"]): {"key": f["key"], "bytes": f["bytes"], "sha256": f["sha256"]}
                  for f in fetch if "2.4um.tifxyz/" in f["key"]}
    vol_fetch = [f for f in fetch if f["key"].endswith("masked.zarr/metadata.json")][0]
    man = {
        "provenance": PROV,
        "serves": "RULES.md DECL-P4-2 items 1-2 (material M1); sibling task p4-tiles-b",
        "segment": SEG,
        "volume": "20260411134726",
        "model": "20260417190342-new_canon_autoresearch_recipe",
        "prediction": {"key": pred_fetch["key"], "bytes": pred_fetch["bytes"], "sha256": pred_fetch["sha256"]},
        "mesh": mesh_fetch,
        "volume_metadata": {"key": vol_fetch["key"], "bytes": vol_fetch["bytes"], "sha256": vol_fetch["sha256"]},
        "voxel_mm": voxel_mm,
        "canvas_shape": [H, W],
        "grid_shape": list(valid.shape),
        "canvas_per_grid_scale": s,
        "px_per_mm": info["px_per_mm"],
        "T_px": T,
        "tile_mm": TILE_MM,
        "display": {"side_px": OUT_SIDE, "px_per_mm": OUT_SIDE / TILE_MM, "downscale": "builder.area_downscale "
                    "(cv2.INTER_AREA), scale 1068/T", "values": "raw uint8 prediction (builder.model_map_u8), "
                    "0 outside mesh-valid; no contrast change", "encoder": "builder.png_bytes; chunks "
                    "IHDR/IDAT/IEND only"},
        "read_eligible_rule": "valid fraction >= 0.5 of T^2",
        "tile_grid_rows_cols": [nr, nc],
        "tiles_total": int(nr * nc),
        "tiles_read_eligible": len(recs),
        "stats_note": "stats over mesh-valid raw full-resolution px of the tile, before downscale",
        "mesh_points": {"file": "tile_points.npz", "keys": "r<r>_c<c>", "dtype": "float32", "columns":
                        "x, y, z from x.tif, y.tif, z.tif (volume 20260411134726 voxels)",
                        "selection": "valid grid vertices whose canvas position (gi*s, gj*s) lies in the "
                        "tile; if > 4096, 4096 drawn without replacement by numpy default_rng(20260926 + "
                        "1000 r + c), sorted"},
        "viewing": "no image, tile, map or CT pixel was opened, displayed or described by the builder",
        "naming_note": "files are named w028-037_r<r>_c<c>.png as the task brief requires; the uuid "
                       "renaming and key of DECL-P4-2 item 2 are the orchestrator's step",
        "tiles": recs,
        "secs_total": round(time.time() - t_start, 1),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print("DONE", len(recs), round(time.time() - t_start, 1), flush=True)


if __name__ == "__main__":
    main()
