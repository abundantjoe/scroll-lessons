"""P4-D M2b tiler: 20260623142658-w028-037, official 1 um model prediction on 20260608103018 L1
(RULES.md DECL-P4-4 items 1-2, as DECL-P4-2 items 1-2).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile, map or CT pixel is ever displayed or printed. PNG bytes are
hashed and written, never opened. Display chain (I2): raw uint8 prediction, 0 outside
mesh-valid, builder.area_downscale (cv2.INTER_AREA) to 1068 x 1068, builder.png_bytes.

Usage: python tile_m2b.py <download_dir> <out_dir> <uv_check.json> [workers]
"""
import glob
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
SEG = "20260623142658-w028-037"
TILE_MM = 20.0
OUT_SIDE = 1068
MIN_VALID = 0.5
MAX_PTS = 4096
PTS_SEED = 20260926
INK_THR = 150

OUT = None
G = {}


def find(dl, pat):
    m = sorted(glob.glob(os.path.join(dl, pat)))
    assert len(m) == 1, (pat, m)
    return m[0]


def load_xyz(dl, tag):
    return [tifffile.imread(find(dl, f"*{tag}.tifxyz_{a}.tif")) for a in "xyz"]


def edge_lengths(x, y, z, valid, axis, chunk=256):
    """Valid 3-D edge lengths along an axis, computed in row chunks (float64)."""
    out = []
    h = x.shape[0]
    for i0 in range(0, h, chunk):
        i1 = min(h, i0 + chunk + (1 if axis == 0 else 0))
        P = np.stack([x[i0:i1], y[i0:i1], z[i0:i1]], -1).astype(np.float64)
        v = valid[i0:i1]
        if axis == 1:
            d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[v[:, 1:] & v[:, :-1]]
        else:
            d = np.linalg.norm(P[1:] - P[:-1], axis=-1)[v[1:] & v[:-1]]
        out.append(d.astype(np.float32))
    return np.concatenate(out)


def q(a):
    return {k: float(v) for k, v in zip(("p01", "p05", "p25", "median", "p75", "p95", "p99"),
                                        np.percentile(a, [1, 5, 25, 50, 75, 95, 99]))}


def tile_valid_fractions(valid, s, T, H, W):
    nr, nc = -(-H // T), -(-W // T)
    gi_of_row = (np.arange(H) // s).astype(np.int64)
    gj_of_col = (np.arange(W) // s).astype(np.int64)
    gh, gw = valid.shape
    vf = valid.astype(np.float64)
    out = np.zeros((nr, nc))
    for r in range(nr):
        wr = np.bincount(gi_of_row[r * T:min((r + 1) * T, H)], minlength=gh).astype(np.float64)
        colsum = wr @ vf
        for c in range(nc):
            wc = np.bincount(gj_of_col[c * T:min((c + 1) * T, W)], minlength=gw).astype(np.float64)
            out[r, c] = float(colsum @ wc) / float(T * T)
    return out


def _init(pred_path, grid_valid, s, T):
    with tifffile.TiffFile(pred_path) as t:
        p = t.pages[0]
        G.update(offs=np.asarray(p.dataoffsets), cnts=np.asarray(p.databytecounts), tw=p.tilewidth,
                 tl=p.tilelength, H=p.shape[0], W=p.shape[1])
    G.update(valid=grid_valid, s=s, T=T, ntx=-(-G["W"] // G["tw"]), f=open(pred_path, "rb"))


def read_region(y0, y1, x0, x1):
    tl, tw, f = G["tl"], G["tw"], G["f"]
    out = np.zeros((y1 - y0, x1 - x0), np.uint8)
    for ty in range(y0 // tl, (y1 - 1) // tl + 1):
        for tx in range(x0 // tw, (x1 - 1) // tw + 1):
            k = ty * G["ntx"] + tx
            f.seek(int(G["offs"][k]))
            a = np.frombuffer(zlib.decompress(f.read(int(G["cnts"][k]))), np.uint8).reshape(tl, tw)
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
    del m
    v = np.arange(256, dtype=np.float64)
    mean = float((hist * v).sum() / nval)
    std = float(np.sqrt((hist * (v - mean) ** 2).sum() / nval))
    fge = float(hist[INK_THR:].sum() / nval)
    disp = area_downscale(crop, OUT_SIDE / T)
    del crop
    assert disp.shape == (OUT_SIDE, OUT_SIDE) and disp.dtype == np.uint8, disp.shape
    b = png_bytes(disp)
    assert b[:8] == b"\x89PNG\r\n\x1a\n"
    chunks, i = [], 8
    while i < len(b):
        n = int.from_bytes(b[i:i + 4], "big")
        chunks.append(b[i + 4:i + 8].decode("ascii"))
        i += 12 + n
    assert set(chunks) <= {"IHDR", "IDAT", "IEND"}, chunks
    name = f"{SEG}_r{r}_c{c}.png"
    with open(os.path.join(OUT, "tiles", name), "wb") as fo:
        fo.write(b)
    return {"r": r, "c": c, "file": f"tiles/{name}", "canvas_rows": [y0, y0 + T], "canvas_cols": [x0, x0 + T],
            "in_canvas_rows": [y0, y1], "in_canvas_cols": [x0, x1], "valid_fraction": vfrac,
            "valid_px": nval, "valid_fraction_check": nval / float(T * T),
            "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b), "png_chunks": sorted(set(chunks)),
            "stats": {"mean": mean, "std": std, "frac_ge_150": fge},
            "secs": round(time.time() - t0, 2)}


def main():
    global OUT
    dl, OUT, uvp = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    t_start = time.time()
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    fetch = [{k: v for k, v in json.loads(l).items() if k != "local"}
             for l in open(os.path.join(dl, "fetch.jsonl"))]
    vmeta = json.load(open(find(dl, "*masked.zarr_metadata.json")))
    voxel_mm = float(vmeta["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    zattrs = json.load(open(find(dl, "*masked.zarr_.zattrs")))
    l1_scale = zattrs["multiscales"][0]["datasets"][1]["coordinateTransformations"][0]["scale"]
    tr = json.load(open(find(dl, "*masked.zarr_transform.json")))
    Maff = np.array(tr["transformation_matrix"], dtype=np.float64)
    mmeta = json.load(open(find(dl, "*1.129um.tifxyz_meta.json")))
    mmeta24 = json.load(open(find(dl, "*2.4um.tifxyz_meta.json")))
    uv = json.load(open(uvp))
    pred_path = find(dl, "*tile256-stride128.tif")
    with tifffile.TiffFile(pred_path) as t:
        p = t.pages[0]
        pinfo = {"shape": list(p.shape), "dtype": str(p.dtype), "compression": int(p.compression),
                 "predictor": int(getattr(p, "predictor", 1)), "tiled": bool(p.is_tiled),
                 "tile": [p.tilelength, p.tilewidth], "n_tiles": len(p.dataoffsets),
                 "image_description": p.description}
        assert p.dtype == np.uint8 and int(p.compression) == 32946 and int(getattr(p, "predictor", 1)) == 1
        fh, checks = t.filehandle, []
        for k in (0, len(p.dataoffsets) // 2, len(p.dataoffsets) - 1):
            fh.seek(p.dataoffsets[k])
            raw = fh.read(p.databytecounts[k])
            ref = np.asarray(p.decode(raw, k)[0])
            mine = np.frombuffer(zlib.decompress(raw), np.uint8).reshape(p.tilelength, p.tilewidth)
            checks.append(bool(np.array_equal(ref.reshape(mine.shape), mine)))
        assert all(checks), checks
        pinfo["zlib_decode_matches_tifffile_on_tiles"] = checks

    x, y, z = load_xyz(dl, "1.129um")
    gh, gw = x.shape
    neg = [(a == -1) for a in (x, y, z)]
    nonfin = int(sum((~np.isfinite(a)).sum() for a in (x, y, z)))
    valid = ~(neg[0] | neg[1] | neg[2]) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    agree = bool(np.array_equal(neg[0], neg[1]) and np.array_equal(neg[0], neg[2]))
    negc = [int(n.sum()) for n in neg]
    del neg
    ec = edge_lengths(x, y, z, valid, 1)
    er = edge_lengths(x, y, z, valid, 0)
    both = np.concatenate([ec, er])
    H, W = pinfo["shape"]
    sy, sx = H / gh, W / gw
    assert sy == sx, (sy, sx)
    s = float(sy)
    med = float(np.median(both))
    ppm = s / (med * voxel_mm)
    T = int(round(TILE_MM * ppm))
    info = {
        "provenance": PROV,
        "serves": "RULES.md DECL-P4-4 item 1 M2b and item 2; sibling task p4-tiles-b (P4-D)",
        "segment": SEG,
        "mesh_frame": "20260608103018 (1.129 um) L0 voxels, xyz",
        "grid_shape": [gh, gw], "grid_vertices": int(gh * gw),
        "minus1_count_x_y_z": negc, "minus1_all_three_agree": agree, "nonfinite_count": nonfin,
        "mesh_valid_vertices": int(valid.sum()), "mesh_valid_fraction": float(valid.mean()),
        "canvas_shape": [H, W], "canvas_per_grid_scale_rows_cols": [sy, sx],
        "canvas_level": "L1 (x2 of L0; .zattrs dataset 1 scale %s)" % l1_scale,
        "canvas_level_check": "mesh scale 0.05 => 20 L0 voxels per grid step = 10 L1 px; canvas/grid "
                              "measured = %.6f" % s,
        "edge_len_L0vx_along_cols": dict(n=int(ec.size), **q(ec)),
        "edge_len_L0vx_along_rows": dict(n=int(er.size), **q(er)),
        "edge_len_L0vx_both": dict(n=int(both.size), **q(both)),
        "voxel_mm": voxel_mm,
        "voxel_mm_source": "volume 20260608103018 metadata.json tomo.acquisition.detector.samplePixelSize (mm)",
        "median_edge_mm": med * voxel_mm,
        "px_per_mm": ppm,
        "px_per_mm_cols_only": s / (float(np.median(ec)) * voxel_mm),
        "px_per_mm_rows_only": s / (float(np.median(er)) * voxel_mm),
        "px_per_mm_nominal_L1": 1.0 / (2.0 * voxel_mm),
        "formula": "px_per_mm = (canvas px per grid step) / (median 3-D edge length of valid row+col grid "
                   "edges in L0 voxels x voxel_mm)",
        "T_px": T, "T_formula": "T = round(20 mm x px_per_mm)",
        "display_scale": OUT_SIDE / T, "display_px_per_mm": OUT_SIDE / TILE_MM,
        "canvas_mask_rule": "canvas px (i, j) -> grid (floor(i / s), floor(j / s)) (nearest neighbour); canvas "
                            "px outside the canvas extent count as not mesh-valid",
        "area_cm2_from_meta": mmeta["area_vx2"] * voxel_mm ** 2 / 100.0,
        "mesh_meta_1129": mmeta, "mesh_meta_24": mmeta24,
        "prediction_tiff": pinfo,
    }
    del ec, er, both
    vf = tile_valid_fractions(valid, s, T, H, W)
    nr, nc = vf.shape
    info.update({"tile_grid_rows_cols": [nr, nc], "tiles_total": int(nr * nc),
                 "tiles_read_eligible": int((vf >= MIN_VALID).sum()),
                 "tile_valid_fraction_matrix": [[round(float(a), 6) for a in row] for row in vf],
                 "edge_tile_rule": "tiles extending past the canvas are zero-padded to T x T; padded px are not "
                                   "mesh-valid and count in the T^2 denominator"})
    print("grid", json.dumps({k: info[k] for k in ("grid_shape", "canvas_shape", "px_per_mm", "T_px",
                                                   "tile_grid_rows_cols", "tiles_read_eligible")}), flush=True)

    # ---- mesh points, both frames
    x24, y24, z24 = load_xyz(dl, "2.4um")
    B = np.stack([x24, y24, z24], -1)
    del x24, y24, z24
    vB = (B != -1).all(-1)
    hB, wB = vB.shape
    ai, bi = hB / gh, 0.5 * hB / gh - 0.5
    aj, bj = wB / gw, 0.5 * wB / gw - 0.5

    def to24(ii, jj, P):
        fi, fj = ii * ai + bi, jj * aj + bj
        i0, j0 = np.floor(fi).astype(np.int64), np.floor(fj).astype(np.int64)
        ok = (i0 >= 0) & (j0 >= 0) & (i0 + 1 < hB) & (j0 + 1 < wB)
        i0c, j0c = np.clip(i0, 0, hB - 2), np.clip(j0, 0, wB - 2)
        ok &= vB[i0c, j0c] & vB[i0c + 1, j0c] & vB[i0c, j0c + 1] & vB[i0c + 1, j0c + 1]
        di, dj = (fi - i0c)[:, None], (fj - j0c)[:, None]
        Q = (B[i0c, j0c] * (1 - di) * (1 - dj) + B[i0c + 1, j0c] * di * (1 - dj)
             + B[i0c, j0c + 1] * (1 - di) * dj + B[i0c + 1, j0c + 1] * di * dj).astype(np.float64)
        Aff = P.astype(np.float64) @ Maff[:, :3].T + Maff[:, 3]
        d = np.linalg.norm(Q - Aff, axis=1)
        out = np.where(ok[:, None], Q, Aff)
        return out.astype(np.float32), ok, d[ok]

    elig = [(r, c, float(vf[r, c])) for r in range(nr) for c in range(nc) if vf[r, c] >= MIN_VALID]
    pts, dall, n_aff = {}, [], 0
    for r, c, _ in elig:
        i0, i1 = int(np.ceil(r * T / s)), min(int(np.ceil((r + 1) * T / s)), gh)
        j0, j1 = int(np.ceil(c * T / s)), min(int(np.ceil((c + 1) * T / s)), gw)
        vi, vj = np.nonzero(valid[i0:i1, j0:j1])
        n = vi.size
        if n > MAX_PTS:
            sel = np.sort(np.random.default_rng(PTS_SEED + 1000 * r + c).choice(n, MAX_PTS, replace=False))
            vi, vj = vi[sel], vj[sel]
        gi_, gj_ = vi + i0, vj + j0
        P = np.stack([x[gi_, gj_], y[gi_, gj_], z[gi_, gj_]], 1).astype(np.float32)
        P24, ok, d = to24(gi_.astype(np.float64), gj_.astype(np.float64), P)
        dall.append(d)
        n_aff += int((~ok).sum())
        k = f"r{r}_c{c}"
        pts[k] = P
        pts[k + "__f20260411134726"] = P24
        pts[k + "__f20260411134726_src"] = (~ok).astype(np.uint8)
        pts[k + "__grid_ij"] = np.stack([gi_, gj_], 1).astype(np.int32)
        pts[k + "__n_valid_vertices"] = np.array([n], np.int64)
    dall = np.concatenate(dall)
    np.savez_compressed(os.path.join(OUT, "tile_points.npz"), **pts)
    info["frame_20260411134726"] = {
        "method": "same UV on the segment's official 20260411134726 tifxyz (bilinear), pixel-centre-aligned map "
                  "i24 = (i + 0.5) * h24 / h1129 - 0.5 (same for j), verified in uv_check.json; falls back to the "
                  "published affine transform.json (1.129 um L0 xyz -> 2.4 um xyz) where a bilinear corner is invalid",
        "uv_map": {"a_i": ai, "b_i": bi, "a_j": aj, "b_j": bj, "grid_24": [hB, wB]},
        "points_total": int(sum(v.shape[0] for k, v in pts.items() if k.count("__") == 0)),
        "points_via_affine_fallback": n_aff,
        "same_uv_vs_affine_dist_vx24_all_saved_points": dict(n=int(dall.size), **q(dall), max=float(dall.max())),
        "affine_matrix": Maff.tolist(),
    }
    info["all_vertices_note"] = ("not saved: all valid 1.129 um vertices are %d (x 12 B = %.2f GB float32 xyz per "
                                 "frame), over the 90 MB per-file limit; p4-excl can read them from the official "
                                 "tifxyz (sha256 in fetch)" % (int(valid.sum()), valid.sum() * 12 / 1e9))
    del B, vB, x, y, z
    info["fetch"] = fetch
    info["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(info, open(os.path.join(OUT, "grid.json"), "w"), indent=1)
    print("points", len(elig), n_aff, flush=True)

    recs = []
    jl = open(os.path.join(OUT, "tiles.jsonl"), "w")
    with Pool(workers, initializer=_init, initargs=(pred_path, valid, s, T)) as pool:
        for rec in pool.imap(do_tile, elig):
            k = f"r{rec['r']}_c{rec['c']}"
            rec["mesh_points_key"] = k
            rec["mesh_valid_vertices_in_tile"] = int(pts[k + "__n_valid_vertices"][0])
            rec["mesh_points_saved"] = int(pts[k].shape[0])
            recs.append(rec)
            jl.write(json.dumps(rec) + "\n")
            jl.flush()
            print("tile", k, rec["secs"], len(recs), "/", len(elig), flush=True)
    jl.close()

    pf = [f for f in fetch if f["key"].endswith("tile256-stride128.tif")][0]
    man = {
        "provenance": PROV,
        "serves": "RULES.md DECL-P4-4 item 1 (material M2b) and item 2; sibling task p4-tiles-b",
        "segment": SEG,
        "volume": "20260608103018 (1.129 um), canvas rendered at L1",
        "model": "20260709123958-mrg20736-1um-s1z2",
        "prediction": {"key": pf["key"], "bytes": pf["bytes"], "sha256": pf["sha256"]},
        "inputs": [{"key": f["key"], "bytes": f["bytes"], "sha256": f["sha256"]} for f in fetch],
        "voxel_mm": voxel_mm, "canvas_shape": [H, W], "grid_shape": [gh, gw], "canvas_per_grid_scale": s,
        "px_per_mm": ppm, "T_px": T, "tile_mm": TILE_MM,
        "display": {"side_px": OUT_SIDE, "px_per_mm": OUT_SIDE / TILE_MM,
                    "downscale": "builder.area_downscale (cv2.INTER_AREA), scale 1068/T",
                    "values": "raw uint8 prediction (builder.model_map_u8), 0 outside mesh-valid; no contrast change",
                    "encoder": "builder.png_bytes; chunks IHDR/IDAT/IEND only"},
        "read_eligible_rule": "valid fraction >= 0.5 of T^2",
        "tile_grid_rows_cols": [nr, nc], "tiles_total": int(nr * nc), "tiles_read_eligible": len(recs),
        "stats_note": "stats over mesh-valid raw full-resolution (L1 canvas) px of the tile, before downscale",
        "mesh_points": {
            "file": "tile_points.npz",
            "keys": {"r<r>_c<c>": "float32 (n,3) xyz, 20260608103018 L0 voxels (mesh own frame)",
                     "r<r>_c<c>__f20260411134726": "float32 (n,3) xyz, 20260411134726 voxels",
                     "r<r>_c<c>__f20260411134726_src": "uint8 (n,) 0 = same-UV 2.4 um mesh, 1 = affine fallback",
                     "r<r>_c<c>__grid_ij": "int32 (n,2) 1.129 um grid row, col",
                     "r<r>_c<c>__n_valid_vertices": "int64 (1,) valid vertices in the tile before subsampling"},
            "selection": "valid 1.129 um grid vertices whose canvas position (gi*s, gj*s) lies in the tile; if > "
                         "4096, 4096 drawn without replacement by numpy default_rng(20260926 + 1000 r + c), sorted",
            "frame_20260411134726": info["frame_20260411134726"]["method"]},
        "viewing": "no image, tile, map or CT pixel was opened, displayed or described by the builder",
        "tiles": recs,
        "secs_total": round(time.time() - t_start, 1),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print("DONE", len(recs), round(time.time() - t_start, 1), flush=True)


if __name__ == "__main__":
    main()
