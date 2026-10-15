"""P4-E E1 builder (RULES.md DECL-P4-5 items 1-3): raw-CT slab-mean tiles of
20260623141924-w010-027 from the official 1.129 um L1 surface volume, on the P4-D M2a tile grid.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile or CT pixel is ever displayed or printed. PNG bytes are hashed and
written, never opened. One background job: fetch, compute, tile, commit and push in batches.

Display (DECL-P4-5 item 2): per canvas pixel the mean over the central 47 slices (centre index
58 = n//2 of 116, slices 35..81 inclusive, +-23 x 2.258 um = +-51.9 um), computed on multiscale
level 3 (in-plane 18.064 um <= 18.7 um; depth unchanged at 2.258 um); per-tile linear 1-99 %
stretch over mesh-valid px (builder.linear_window_ct), 0 outside; cv2.INTER_AREA to 1068 x 1068;
builder.png_bytes (IHDR/IDAT/IEND only).

Usage: python e1_job.py <scratch_dir> <repo_dir>
"""
import concurrent.futures as cf
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

import cv2
import numpy as np
import requests
import tifffile

REPO = sys.argv[2]
sys.path.insert(0, os.path.join(REPO, "src"))
from hercules.display.builder import linear_window_ct, png_bytes  # noqa: E402

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
ATTR = open(os.path.join(sys.argv[1], "..", "attr.txt")).read().strip()  # session attribution lines, kept out of repo files
BR = "claude/gifted-bell-gavnl5-sib-p4-tiles-b"
SEG = "20260623141924-w010-027"
BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SV = f"PHercParis4/segments/{SEG}/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr"
MESH = f"PHercParis4/segments/{SEG}/mesh/20260623141924-on-20260608103018-1.129um.tifxyz"
VOL = "PHercParis4/volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr"
VOL_SHAPE_ZYX = (59969, 36006, 32354)
LEVEL = 3
LSCALE = 8  # level-3 px per L0 canvas px side
N_SLICES, CENTRE, HALF = 116, 58, 23
TILE_MM, OUT_SIDE, MIN_VALID, MAX_OUT = 20.0, 1068, 0.5, 0.5
MAX_PTS, PTS_SEED = 4096, 20260926

SCR = sys.argv[1]
OUT = os.path.join(REPO, "logs/sib/p4-tiles-b/e1")
RUNS = os.path.join(REPO, "logs/sib/p4-tiles-b/runs.jsonl")
S = requests.Session()


def log(**kw):
    kw = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    with open(RUNS, "a") as f:
        f.write(json.dumps(kw) + "\n")
    print(json.dumps(kw), flush=True)


def get(key, path=None, tries=6):
    for i in range(tries):
        try:
            r = S.get(f"{BUCKET}/{key}", timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            b = r.content
            if path:
                with open(path, "wb") as f:
                    f.write(b)
            return b
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def fetch_file(key):
    p = os.path.join(SCR, key.replace("/", "_"))
    t0 = time.time()
    b = get(key, p)
    rec = {"key": key, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "secs": round(time.time() - t0, 1)}
    return p, rec


def list_keys(prefix):
    out, tok = [], None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if tok:
            params["continuation-token"] = tok
        x = S.get(BUCKET + "/", params=params, timeout=120).text
        for blk in re.findall(r"<Contents>(.*?)</Contents>", x, re.S):
            k = re.search(r"<Key>(.*?)</Key>", blk).group(1)
            sz = int(re.search(r"<Size>(\d+)</Size>", blk).group(1))
            et = re.search(r"<ETag>(.*?)</ETag>", blk).group(1).replace("&quot;", "").strip('"')
            out.append((k, sz, et))
        m = re.search(r"<NextContinuationToken>(.*?)</NextContinuationToken>", x)
        if not m:
            return out
        tok = m.group(1)


def sh(*cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def clean_check(paths):
    for p in paths:
        if p.endswith((".json", ".jsonl", ".md", ".py")):
            s = open(p, encoding="utf-8").read()
            assert not any(unicodedata.category(c) == "Cf" for c in s), p
            if not p.endswith(".py"):  # data outputs must not carry tool paths or names
                assert "claude" not in s.lower(), p


def commit_push(paths, msg):
    clean_check(paths)
    sh("git", "add", *paths)
    r = sh("git", "commit", "-q", "-m", msg + "\n\n" + PROV + "\n\n" + ATTR)
    for i in range(5):
        p = sh("git", "push", "origin", BR)
        if p.returncode == 0:
            log(run="e1-push", msg=msg.splitlines()[0], commit=sh("git", "rev-parse", "--short", "HEAD").stdout.strip())
            return
        time.sleep(2 ** (i + 1))
    log(run="e1-push", status="FAILED", stderr=p.stderr[-500:], commit_rc=r.returncode)


def q(a):
    return {k: float(v) for k, v in zip(("p01", "p05", "p25", "median", "p75", "p95", "p99"),
                                        np.percentile(a, [1, 5, 25, 50, 75, 95, 99]))}


def edge_lengths(x, y, z, valid, axis, chunk=256):
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


def main():
    t_start = time.time()
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    log(run="e1-job", status="started", governed_by="DECL-P4-5 E1")
    # ---- 1. small inputs + mesh
    fetch = []
    paths = {}
    for k in [f"{SV}/.zattrs", f"{SV}/.zgroup", f"{SV}/0/.zarray", f"{SV}/{LEVEL}/.zarray", f"{VOL}/metadata.json",
              f"{MESH}/meta.json", f"{MESH}/x.tif", f"{MESH}/y.tif", f"{MESH}/z.tif"]:
        p, rec = fetch_file(k)
        paths[k] = p
        fetch.append(rec)
    log(run="e1-fetch-small", files=len(fetch))
    zattrs = json.load(open(paths[f"{SV}/.zattrs"]))
    za0 = json.load(open(paths[f"{SV}/0/.zarray"]))
    za3 = json.load(open(paths[f"{SV}/{LEVEL}/.zarray"]))
    ds = zattrs["multiscales"][0]["datasets"]
    l3scale = ds[LEVEL]["coordinateTransformations"][0]["scale"]
    assert za0["shape"][0] == N_SLICES and za3["shape"][0] == N_SLICES and za3["chunks"][0] == N_SLICES
    assert za3["dtype"] == "|u1" and za3["compressor"] is None and za3["dimension_separator"] == "/"
    assert abs(l3scale[1] / ds[0]["coordinateTransformations"][0]["scale"][1] - LSCALE) < 1e-9
    voxel_mm = float(json.load(open(paths[f"{VOL}/metadata.json"]))["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    mmeta = json.load(open(paths[f"{MESH}/meta.json"]))

    # ---- 2. grid geometry (M2b method)
    x, y, z = [tifffile.imread(paths[f"{MESH}/{a}.tif"]) for a in "xyz"]
    gh, gw = x.shape
    neg = [(a == -1) for a in (x, y, z)]
    valid = ~(neg[0] | neg[1] | neg[2]) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    negc = [int(n.sum()) for n in neg]
    agree = bool(np.array_equal(neg[0], neg[1]) and np.array_equal(neg[0], neg[2]))
    del neg
    ec, er = edge_lengths(x, y, z, valid, 1), edge_lengths(x, y, z, valid, 0)
    both = np.concatenate([ec, er])
    H, W = za0["shape"][1], za0["shape"][2]
    canvas_size_attr = zattrs.get("canvas_size")
    s = 10.0  # task + DECL-P4-4: canvas = grid x 10 (L1)
    assert (H, W) == (gh * 10, gw * 10) or (abs(H - gh * 10) <= 10 and abs(W - gw * 10) <= 10), (H, W, gh, gw)
    med = float(np.median(both))
    ppm = s / (med * voxel_mm)
    T = int(round(TILE_MM * ppm))
    nr, nc = -(-H // T), -(-W // T)
    # valid fractions exactly at canvas resolution
    gi_of_row = np.minimum(np.arange(H) // 10, gh - 1)
    gj_of_col = np.minimum(np.arange(W) // 10, gw - 1)
    vfm = valid.astype(np.float64)
    vf = np.zeros((nr, nc))
    for r in range(nr):
        wr = np.bincount(gi_of_row[r * T:min((r + 1) * T, H)], minlength=gh).astype(np.float64)
        cs = wr @ vfm
        for c in range(nc):
            wc = np.bincount(gj_of_col[c * T:min((c + 1) * T, W)], minlength=gw).astype(np.float64)
            vf[r, c] = float(cs @ wc) / float(T * T)
    del vfm
    # points outside the 1.129 um volume (4096 per tile, M2b rule)
    fout = np.full((nr, nc), np.nan)
    for r in range(nr):
        for c in range(nc):
            if vf[r, c] < MIN_VALID:
                continue
            i0, i1 = int(np.ceil(r * T / s)), min(int(np.ceil((r + 1) * T / s)), gh)
            j0, j1 = int(np.ceil(c * T / s)), min(int(np.ceil((c + 1) * T / s)), gw)
            vi, vj = np.nonzero(valid[i0:i1, j0:j1])
            if vi.size > MAX_PTS:
                sel = np.sort(np.random.default_rng(PTS_SEED + 1000 * r + c).choice(vi.size, MAX_PTS, replace=False))
                vi, vj = vi[sel], vj[sel]
            P = np.stack([x[vi + i0, vj + j0], y[vi + i0, vj + j0], z[vi + i0, vj + j0]], 1)
            fout[r, c] = float(((P[:, 0] < 0) | (P[:, 0] >= VOL_SHAPE_ZYX[2]) | (P[:, 1] < 0) | (P[:, 1] >= VOL_SHAPE_ZYX[1])
                                | (P[:, 2] < 0) | (P[:, 2] >= VOL_SHAPE_ZYX[0])).mean())
    del x, y, z
    elig = [(r, c) for r in range(nr) for c in range(nc) if vf[r, c] >= MIN_VALID and fout[r, c] < MAX_OUT]
    grid = {
        "provenance": PROV, "serves": "RULES.md DECL-P4-5 E1 (grid identical to P4-D M2a by construction)",
        "segment": SEG, "grid_shape": [gh, gw], "grid_vertices": int(gh * gw),
        "minus1_count_x_y_z": negc, "minus1_all_three_agree": agree,
        "mesh_valid_vertices": int(valid.sum()), "mesh_valid_fraction": float(valid.mean()),
        "canvas_shape_L0_surface_volume": [H, W], "canvas_size_attr_xy": canvas_size_attr,
        "canvas_per_grid_scale": s, "canvas_equals_grid_x10": (H, W) == (gh * 10, gw * 10),
        "edge_len_L0vx_along_cols": dict(n=int(ec.size), **q(ec)),
        "edge_len_L0vx_along_rows": dict(n=int(er.size), **q(er)),
        "edge_len_L0vx_both": dict(n=int(both.size), **q(both)),
        "voxel_mm": voxel_mm, "median_edge_mm": med * voxel_mm, "px_per_mm": ppm,
        "px_per_mm_cols_only": s / (float(np.median(ec)) * voxel_mm),
        "px_per_mm_rows_only": s / (float(np.median(er)) * voxel_mm),
        "px_per_mm_method": "same as P4-D M2b: (canvas px per grid step = 10) / (median 3-D edge of valid row+col "
                            "grid edges in L0 voxels x voxel_mm)",
        "T_px": T, "tile_grid_rows_cols": [nr, nc], "tiles_total": int(nr * nc),
        "tiles_ge50_valid": int((vf >= MIN_VALID).sum()), "tiles_eligible": len(elig),
        "eligibility": (">= 50 % mesh-valid AND frac_mesh_points_outside_1129_volume < 0.5 (4096-point subsample, "
                        f"default_rng(20260926 + 1000 r + c), volume L0 zyx {VOL_SHAPE_ZYX})"),
        "tile_valid_fraction_matrix": [[round(float(a), 6) for a in row] for row in vf],
        "tile_frac_outside_matrix": [[None if np.isnan(a) else round(float(a), 6) for a in row] for row in fout],
        "area_cm2_from_meta": mmeta["area_vx2"] * voxel_mm ** 2 / 100.0, "mesh_meta": mmeta,
        "surface_volume": {"key": SV, "levels_scale_zyx_um": [d["coordinateTransformations"][0]["scale"] for d in ds],
                           "zattrs_extra": {k: v for k, v in zattrs.items() if k != "multiscales"},
                           "level0_zarray": za0, "level_used": LEVEL, "level_zarray": za3},
        "slab": {"n_slices": N_SLICES, "centre_index": CENTRE, "centre_rule": "n//2 (builder.raw_slab_means convention)",
                 "slices": [CENTRE - HALF, CENTRE + HALF], "count": 2 * HALF + 1,
                 "half_width_um": HALF * 2.258, "depth_step_um": 2.258},
        "level_mapping": "canvas L0 px (i, j) <-> level-3 px (i // 8, j // 8); tile (r, c) uses level-3 rows "
                         "[round(r T / 8), round((r+1) T / 8)) and cols likewise (offset <= 4 canvas px); "
                         "level-3 mesh-valid mask: grid (floor((8a + 4) / 10), floor((8b + 4) / 10)) (nearest, centre)",
    }
    log(run="e1-grid", px_per_mm=ppm, T=T, tiles=int(nr * nc), ge50=grid["tiles_ge50_valid"], eligible=len(elig))

    # ---- 3. level-3 chunk listing, download, slab means
    keys = list_keys(f"{SV}/{LEVEL}/")
    chunk_keys = [(k, sz, et) for k, sz, et in keys if re.search(rf"/{LEVEL}/\d+/\d+/\d+$", k)]
    h3, w3 = za3["shape"][1], za3["shape"][2]
    ch, cw = za3["chunks"][1], za3["chunks"][2]
    # rows/cols of level-3 needed by eligible tiles
    need = np.zeros((-(-h3 // ch), -(-w3 // cw)), bool)
    for r, c in elig:
        a0, a1 = int(round(r * T / LSCALE)), min(int(round((r + 1) * T / LSCALE)), h3)
        b0, b1 = int(round(c * T / LSCALE)), min(int(round((c + 1) * T / LSCALE)), w3)
        need[a0 // ch:(a1 - 1) // ch + 1, b0 // cw:(b1 - 1) // cw + 1] = True
    slab = np.zeros((h3, w3), np.float32)
    have = np.zeros_like(need)
    todo = []
    for k, sz, et in chunk_keys:
        _, yc, xc = map(int, k.rsplit("/", 3)[1:])
        if need[yc, xc]:
            todo.append((k, sz, et, yc, xc))
    cman = []
    t0 = time.time()

    def dl(item):
        k, sz, et, yc, xc = item
        b = get(k)
        a = np.frombuffer(b, np.uint8).reshape(N_SLICES, ch, cw)
        m = a[CENTRE - HALF:CENTRE + HALF + 1].astype(np.float32).mean(0)
        return k, len(b), et, hashlib.sha256(b).hexdigest(), yc, xc, m

    with cf.ThreadPoolExecutor(8) as ex:
        for i, (k, n, et, h, yc, xc, m) in enumerate(ex.map(dl, todo)):
            assert n == N_SLICES * ch * cw
            y0, x0 = yc * ch, xc * cw
            hh, ww = min(ch, h3 - y0), min(cw, w3 - x0)
            slab[y0:y0 + hh, x0:x0 + ww] = m[:hh, :ww]
            have[yc, xc] = True
            cman.append({"key": k.split(SV + "/")[1], "bytes": n, "etag": et, "sha256": h})
            if i % 500 == 0:
                log(run="e1-chunks", done=i, of=len(todo), secs=round(time.time() - t0))
    cman.sort(key=lambda d: d["key"])
    with open(os.path.join(OUT, "chunk_manifest.jsonl"), "w") as f:
        for d in cman:
            f.write(json.dumps(d) + "\n")
    cm_sha = hashlib.sha256(open(os.path.join(OUT, "chunk_manifest.jsonl"), "rb").read()).hexdigest()
    grid["chunks"] = {"listed_level3": len(chunk_keys), "needed_grid_cells": int(need.sum()),
                      "needed_and_present": len(todo), "needed_but_absent_fill0": int(need.sum() - len(todo)),
                      "bytes_downloaded": int(sum(d["bytes"] for d in cman)), "secs": round(time.time() - t0, 1),
                      "chunk_manifest": "chunk_manifest.jsonl", "chunk_manifest_sha256": cm_sha}
    grid["fetch"] = fetch
    log(run="e1-chunks", status="done", n=len(cman), secs=round(time.time() - t0))

    # ---- 4. tiles
    vmask3 = valid[np.minimum((8 * np.arange(h3) + 4) // 10, gh - 1)][:, np.minimum((8 * np.arange(w3) + 4) // 10, gw - 1)]
    recs, batch = [], []
    tt = time.time()
    for idx, (r, c) in enumerate(elig):
        a0, a1 = int(round(r * T / LSCALE)), int(round((r + 1) * T / LSCALE))
        b0, b1 = int(round(c * T / LSCALE)), int(round((c + 1) * T / LSCALE))
        img = np.zeros((a1 - a0, b1 - b0), np.float32)
        vm = np.zeros((a1 - a0, b1 - b0), bool)
        e0, e1 = min(a1, h3), min(b1, w3)
        img[:e0 - a0, :e1 - b0] = slab[a0:e0, b0:e1]
        vm[:e0 - a0, :e1 - b0] = vmask3[a0:e0, b0:e1]
        absent = np.ones(img.shape, bool)
        absent[:e0 - a0, :e1 - b0] = ~have[np.arange(a0, e0)[:, None] // ch, np.arange(b0, e1)[None, :] // cw]
        vals = img[vm]
        u8, (lo, hi) = linear_window_ct(img, vm)
        u8[~vm] = 0
        disp = cv2.resize(u8, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
        assert disp.shape == (OUT_SIDE, OUT_SIDE) and disp.dtype == np.uint8
        b = png_bytes(disp)
        chunks, i = [], 8
        while i < len(b):
            n = int.from_bytes(b[i:i + 4], "big")
            chunks.append(b[i + 4:i + 8].decode("ascii"))
            i += 12 + n
        assert set(chunks) <= {"IHDR", "IDAT", "IEND"}, chunks
        name = f"{SEG}_r{r}_c{c}.png"
        with open(os.path.join(OUT, "tiles", name), "wb") as fo:
            fo.write(b)
        rec = {"r": r, "c": c, "file": f"tiles/{name}", "png_sha256": hashlib.sha256(b).hexdigest(),
               "png_bytes": len(b), "valid_fraction": float(vf[r, c]), "frac_outside": float(fout[r, c]),
               "canvas_rows": [r * T, (r + 1) * T], "canvas_cols": [c * T, (c + 1) * T],
               "level3_rows": [a0, a1], "level3_cols": [b0, b1], "level3_shape": list(img.shape),
               "stats": {"slab_mean_mean_valid": float(vals.mean()), "slab_mean_std_valid": float(vals.std()),
                         "stretch_p1": lo, "stretch_p99": hi,
                         "frac_valid_zero_slab": float((vals == 0).mean()),
                         "frac_valid_in_absent_chunk": float(absent[vm].mean())}}
        recs.append(rec)
        batch.append(os.path.join(OUT, "tiles", name))
        if len(recs) == 40:
            json.dump(grid, open(os.path.join(OUT, "grid.json"), "w"), indent=1)
            commit_push(batch + [os.path.join(OUT, "grid.json"), os.path.join(OUT, "chunk_manifest.jsonl"), RUNS,
                                 os.path.join(REPO, "tools/sib/p4-tiles-b/e1_job.py")],
                        f"p4-tiles-b E1 (DECL-P4-5): grid, chunk manifest, first 40 raw-CT tiles of {SEG}")
            batch = []
    # ---- 5. cross-check with p4-tiles-a M2a grid, if pushed
    xa = {"checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "found": False}
    sh("git", "fetch", "-q", "origin", "claude/gifted-bell-gavnl5-sib-p4-tiles-a")
    ls = sh("git", "ls-tree", "-r", "--name-only", "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-a").stdout.split()
    for f in ls:
        if f.endswith("grid.json") and "p4-tiles-a" in f:
            try:
                ga = json.loads(sh("git", "show", f"origin/claude/gifted-bell-gavnl5-sib-p4-tiles-a:{f}").stdout)
            except Exception:
                continue
            if ga.get("segment") == SEG or SEG in json.dumps(ga.get("segment", "")):
                xa = {**xa, "found": True, "file": f, "px_per_mm": ga.get("px_per_mm"),
                      "T": ga.get("T_px", ga.get("T_canvas_px")), "grid_shape": ga.get("grid_shape"),
                      "matches_T": ga.get("T_px", ga.get("T_canvas_px")) == T}
    grid["p4_tiles_a_m2a_grid_crosscheck"] = xa
    grid["secs_total"] = round(time.time() - t_start, 1)
    grid["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(grid, open(os.path.join(OUT, "grid.json"), "w"), indent=1)
    man = {"provenance": PROV, "serves": "RULES.md DECL-P4-5 E1; sibling task p4-tiles-b", "segment": SEG,
           "material": "official surface volume " + SV + " (raw CT, no model)",
           "level_used": LEVEL, "level_inplane_um": l3scale[1], "slab": grid["slab"],
           "px_per_mm": ppm, "T_px": T, "tile_grid_rows_cols": [nr, nc],
           "display": {"values": "per-tile linear 1-99 % stretch over mesh-valid px (builder.linear_window_ct), 0 outside",
                       "downscale": "cv2.resize INTER_AREA to 1068 x 1068 from the level-3 crop", "px_per_mm": OUT_SIDE / TILE_MM,
                       "encoder": "builder.png_bytes; chunks IHDR/IDAT/IEND only"},
           "eligibility": grid["eligibility"], "tiles_total": int(nr * nc), "tiles_eligible": len(recs),
           "ineligible_ge50_valid_but_outside": [f"r{r}_c{c}" for r in range(nr) for c in range(nc)
                                                 if vf[r, c] >= MIN_VALID and not fout[r, c] < MAX_OUT],
           "inputs": fetch, "chunk_manifest_sha256": cm_sha,
           "viewing": "no image, tile or CT pixel was opened, displayed or described by the builder",
           "naming_note": "files named per task notice; flat uuid naming and key are the orchestrator's step",
           "tiles": recs, "secs_total": grid["secs_total"], "utc": grid["utc"]}
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    zs = [t["stats"]["frac_valid_zero_slab"] for t in recs]
    rep = f"""{PROV}

# p4-tiles-b report: P4-E E1, raw-CT tiles of {SEG} (DECL-P4-5)

Builder role only. No tile, map or CT pixel was opened, viewed, displayed or described. Only numbers, shapes and hashes were computed. The PNG bytes were hashed and written, never read back. This report was generated by tools/sib/p4-tiles-b/e1_job.py.

## Material
- Official surface volume `{SV}`: {N_SLICES} slices, L0 canvas {H} x {W}, uint8, uncompressed, chunks {za3['chunks']}.
- The sha256 values of .zattrs, .zgroup, 0/.zarray, {LEVEL}/.zarray, the volume metadata.json and the mesh files are in manifest.json `inputs`.
- Chunk manifest: chunk_manifest.jsonl has {len(cman)} level-{LEVEL} chunks with key, bytes, ETag and sha256 each; the file's own sha256 is {cm_sha}.
- {grid['chunks']['needed_but_absent_fill0']} needed chunk positions are absent from the bucket and were treated as fill_value 0.

## Projection (as declared; one projection, no alternatives tried)
- Level used: {LEVEL}, with in-plane pixel {l3scale[1]} um (the limit is 18.7 um). Depth stays at 2.258 um per slice.
- Slab: slices {CENTRE - HALF}..{CENTRE + HALF} inclusive ({2 * HALF + 1} slices), centred on index {CENTRE} (n//2), +-{HALF * 2.258:.1f} um.
- Contrast: a per-tile linear 1-99 % stretch over mesh-valid pixels (builder.linear_window_ct), 0 outside.
- Downscale: cv2.INTER_AREA from the level-{LEVEL} crop (about {int(round(T / LSCALE))} px) to 1068 x 1068.
- PNG chunks: IHDR/IDAT/IEND only, asserted on every file.

## Grid (grid.json; identical to M2a by construction)
- 1.129 um mesh grid: {gh} x {gw}. Canvas = grid x 10: {grid['canvas_equals_grid_x10']}.
- Mesh-valid fraction: {valid.mean():.4f}.
- Voxel: {voxel_mm} mm. Median 3-D edge: {med:.4f} L0 vx.
- px_per_mm = {ppm:.4f}, giving **T = {T}**.
- Tile grid {nr} x {nc} ({nr * nc} tiles). {grid['tiles_ge50_valid']} tiles are >= 50 % valid, and **{len(recs)} are eligible** after the rule that < 50 % of mesh points may lie outside the 1.129 um volume.
  - Excluded by the coverage rule: {len(man['ineligible_ge50_valid_but_outside'])} tiles.
- p4-tiles-a M2a grid cross-check: {json.dumps(xa)}.

## Tile numbers
- Median fraction of each tile's valid pixels whose slab mean is exactly 0: {float(np.median(zs)) if zs else float('nan'):.4f}. The maximum is {max(zs) if zs else float('nan'):.4f}. These pixels have no CT data, from absent chunks or regions outside the scan.
- PNG total: {sum(t['png_bytes'] for t in recs) / 1e6:.1f} MB. Unique sha256: {len(set(t['png_sha256'] for t in recs))} of {len(recs)}.

## Timings
- Chunks: {grid['chunks']['bytes_downloaded'] / 1e9:.2f} GB in {grid['chunks']['secs']} s.
- Total job time: {grid['secs_total']} s.

## Notes
- File names follow the task notice. The flat uuid naming and the key are the orchestrator's step.
- The positive control for P4-E is prediction material (DECL-P4-5 item 4, disclosed there).
"""
    open(os.path.join(OUT, "REPORT.md"), "w").write(rep)
    log(run="e1-job", status="done", eligible=len(recs), secs=grid["secs_total"])
    commit_push(batch + [os.path.join(OUT, f) for f in ("grid.json", "manifest.json", "REPORT.md", "chunk_manifest.jsonl")]
                + [RUNS, os.path.join(REPO, "tools/sib/p4-tiles-b/e1_job.py")],
                f"p4-tiles-b E1 (DECL-P4-5): remaining raw-CT tiles, manifest, REPORT ({len(recs)} eligible)")
    for f in os.listdir(SCR):
        if f.endswith(".tif"):
            os.remove(os.path.join(SCR, f))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(run="e1-job", status="FAILED", error=repr(e)[:500])
        raise
