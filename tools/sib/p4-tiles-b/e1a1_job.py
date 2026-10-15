"""P4-E E1 rebuild under RULES.md DECL-P4-5-A1, plus tile_points.npz for the E1 (= M2a) grid.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile or CT pixel is ever displayed or printed. PNG bytes are hashed and
written, never opened.

Changes vs e1_job.py (A1 only): the per-tile linear 1-99 % stretch is computed over mesh-valid px
whose slab mean is > 0, and px with slab mean 0 are written as 0. Slab, level, grid, eligibility
and output size are unchanged; the 60 tiles are those of logs/sib/p4-tiles-b/e1/manifest.json.
Every re-downloaded level-3 chunk is checked against the E1 chunk_manifest.jsonl sha256.

Usage: python e1a1_job.py <scratch_dir> <repo_dir>
"""
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time

import cv2
import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e1_job as E  # noqa: E402  (argv: <scratch_dir> <repo_dir>, same as here)
from hercules.display.builder import linear_window_ct, png_bytes  # noqa: E402

REPO = sys.argv[2]
SCR = sys.argv[1]
E1 = os.path.join(REPO, "logs/sib/p4-tiles-b/e1")
OUT = os.path.join(REPO, "logs/sib/p4-tiles-b/e1a1")
MESH24 = f"PHercParis4/segments/{E.SEG}/mesh/20260623141924-on-20260411134726-2.4um.tifxyz"
TOOLS = [os.path.join(REPO, "tools/sib/p4-tiles-b", f) for f in ("e1a1_job.py", "e1_job.py")]


def main():
    t_start = time.time()
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    E.log(run="e1a1-job", status="started", governed_by="DECL-P4-5-A1")
    man1 = json.load(open(os.path.join(E1, "manifest.json")))
    grid1 = json.load(open(os.path.join(E1, "grid.json")))
    cm1 = {d["key"]: d for d in map(json.loads, open(os.path.join(E1, "chunk_manifest.jsonl")))}
    T, s, LS = grid1["T_px"], 10.0, E.LSCALE
    za3 = grid1["surface_volume"]["level_zarray"]
    h3, w3 = za3["shape"][1], za3["shape"][2]
    ch, cw = za3["chunks"][1], za3["chunks"][2]

    # ---- inputs (mesh 1.129 + 2.4 + affine), sha256 compared to E1 where fetched before
    fetch, paths = [], {}
    for k in [f"{E.MESH}/meta.json", f"{E.MESH}/x.tif", f"{E.MESH}/y.tif", f"{E.MESH}/z.tif",
              f"{MESH24}/meta.json", f"{MESH24}/x.tif", f"{MESH24}/y.tif", f"{MESH24}/z.tif",
              f"{E.VOL}/transform.json"]:
        p, rec = E.fetch_file(k)
        paths[k] = p
        fetch.append(rec)
    prev = {d["key"]: d["sha256"] for d in man1["inputs"]}
    same = {r["key"]: prev[r["key"]] == r["sha256"] for r in fetch if r["key"] in prev}
    assert all(same.values()), same
    x, y, z = [tifffile.imread(paths[f"{E.MESH}/{a}.tif"]) for a in "xyz"]
    gh, gw = x.shape
    assert [gh, gw] == grid1["grid_shape"]
    valid = (x != -1) & (y != -1) & (z != -1) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    assert int(valid.sum()) == grid1["mesh_valid_vertices"]

    # ---- level-3 slab for the 60 tiles; verify chunk sha256 against E1
    tiles1 = man1["tiles"]
    need = np.zeros((-(-h3 // ch), -(-w3 // cw)), bool)
    for t in tiles1:
        a0, a1 = t["level3_rows"]
        b0, b1 = t["level3_cols"]
        need[a0 // ch:(min(a1, h3) - 1) // ch + 1, b0 // cw:(min(b1, w3) - 1) // cw + 1] = True
    todo = [k for k in cm1 if need[int(k.split("/")[2]), int(k.split("/")[3])]]
    slab = np.zeros((h3, w3), np.float32)
    t0 = time.time()

    def dl(key):
        b = E.get(f"{E.SV}/{key}")
        a = np.frombuffer(b, np.uint8).reshape(E.N_SLICES, ch, cw)
        return key, hashlib.sha256(b).hexdigest(), a[E.CENTRE - E.HALF:E.CENTRE + E.HALF + 1].astype(np.float32).mean(0)

    mism = []
    with cf.ThreadPoolExecutor(8) as ex:
        for key, h, m in ex.map(dl, todo):
            if h != cm1[key]["sha256"]:
                mism.append(key)
            yc, xc = int(key.split("/")[2]), int(key.split("/")[3])
            y0, x0 = yc * ch, xc * cw
            hh, ww = min(ch, h3 - y0), min(cw, w3 - x0)
            slab[y0:y0 + hh, x0:x0 + ww] = m[:hh, :ww]
    assert not mism, mism[:5]
    chunk_info = {"needed_and_present": len(todo), "sha256_all_match_e1_chunk_manifest": True,
                  "e1_chunk_manifest_sha256": grid1["chunks"]["chunk_manifest_sha256"],
                  "secs": round(time.time() - t0, 1)}
    E.log(run="e1a1-chunks", n=len(todo), sha_match=True, secs=chunk_info["secs"])

    # ---- tiles (A1 stretch)
    vmask3 = valid[np.minimum((8 * np.arange(h3) + 4) // 10, gh - 1)][:, np.minimum((8 * np.arange(w3) + 4) // 10, gw - 1)]
    recs = []
    for t in tiles1:
        r, c = t["r"], t["c"]
        a0, a1 = t["level3_rows"]
        b0, b1 = t["level3_cols"]
        img = np.zeros((a1 - a0, b1 - b0), np.float32)
        vm = np.zeros(img.shape, bool)
        e0, e1 = min(a1, h3), min(b1, w3)
        img[:e0 - a0, :e1 - b0] = slab[a0:e0, b0:e1]
        vm[:e0 - a0, :e1 - b0] = vmask3[a0:e0, b0:e1]
        # reproduce the E1 stats exactly (guards the rebuild against drift)
        vals = img[vm]
        old_lo, old_hi = np.percentile(vals.astype(np.float64), [1.0, 99.0])
        assert abs(old_lo - t["stats"]["stretch_p1"]) < 1e-3 and abs(old_hi - t["stats"]["stretch_p99"]) < 1e-3, (r, c)
        pos = vm & (img > 0)
        u8, (lo, hi) = linear_window_ct(img, pos)
        u8[~pos] = 0
        disp = cv2.resize(u8, (E.OUT_SIDE, E.OUT_SIDE), interpolation=cv2.INTER_AREA)
        assert disp.shape == (E.OUT_SIDE, E.OUT_SIDE) and disp.dtype == np.uint8
        b = png_bytes(disp)
        chunks, i = [], 8
        while i < len(b):
            n = int.from_bytes(b[i:i + 4], "big")
            chunks.append(b[i + 4:i + 8].decode("ascii"))
            i += 12 + n
        assert set(chunks) <= {"IHDR", "IDAT", "IEND"}, chunks
        name = f"{E.SEG}_r{r}_c{c}.png"
        with open(os.path.join(OUT, "tiles", name), "wb") as fo:
            fo.write(b)
        pv = img[pos]
        rec = {k: t[k] for k in ("r", "c", "valid_fraction", "frac_outside", "canvas_rows", "canvas_cols",
                                 "level3_rows", "level3_cols", "level3_shape")}
        rec.update({"file": f"tiles/{name}", "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                    "superseded_e1_png_sha256": t["png_sha256"],
                    "stats": {"frac_mesh_points_outside_1129_volume": t["frac_outside"],
                              "frac_valid_zero_slab": float((vals == 0).mean()),
                              "frac_valid_in_absent_chunk": t["stats"]["frac_valid_in_absent_chunk"],
                              "old_stretch_p1": float(old_lo), "old_stretch_p99": float(old_hi),
                              "new_stretch_p1": lo, "new_stretch_p99": hi,
                              "slab_mean_mean_valid_pos": float(pv.mean()), "slab_mean_std_valid_pos": float(pv.std()),
                              "n_valid_px_level3": int(vm.sum()), "n_valid_pos_px_level3": int(pos.sum())}})
        recs.append(rec)
    man = {"provenance": E.PROV,
           "serves": "RULES.md DECL-P4-5 E1 as amended by DECL-P4-5-A1; sibling task p4-tiles-b",
           "segment": E.SEG, "material": man1["material"], "level_used": man1["level_used"],
           "level_inplane_um": man1["level_inplane_um"], "slab": man1["slab"], "px_per_mm": man1["px_per_mm"],
           "T_px": T, "tile_grid_rows_cols": man1["tile_grid_rows_cols"],
           "display": {"values": "per-tile linear 1-99 % stretch over mesh-valid px with slab mean > 0 "
                                 "(builder.linear_window_ct); px with slab mean 0 and px outside mesh-valid written as 0",
                       "downscale": man1["display"]["downscale"], "px_per_mm": man1["display"]["px_per_mm"],
                       "encoder": man1["display"]["encoder"], "amendment": "DECL-P4-5-A1"},
           "eligibility": man1["eligibility"], "tiles_total": man1["tiles_total"], "tiles_eligible": len(recs),
           "ineligible_ge50_valid_but_outside": man1["ineligible_ge50_valid_but_outside"],
           "inputs": man1["inputs"], "chunk_manifest_sha256": man1["chunk_manifest_sha256"], "chunk_check": chunk_info,
           "supersedes": "logs/sib/p4-tiles-b/e1/manifest.json tiles (never to be read)",
           "viewing": "no image, tile or CT pixel was opened, displayed or described by the builder",
           "tiles": recs, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    rows = "\n".join(
        f"| r{t['r']}_c{t['c']} | {t['stats']['frac_valid_zero_slab']:.4f} | {t['stats']['old_stretch_p1']:.2f} | "
        f"{t['stats']['old_stretch_p99']:.2f} | {t['stats']['new_stretch_p1']:.2f} | {t['stats']['new_stretch_p99']:.2f} |"
        for t in recs)
    changed = sum(t["png_sha256"] != t["superseded_e1_png_sha256"] for t in recs)
    rep = f"""{E.PROV}

# p4-tiles-b report: P4-E E1 rebuild under DECL-P4-5-A1 ({E.SEG})

Builder role only. No tile, map or CT pixel was opened, viewed, displayed or described. Only numbers and hashes were computed. This report was generated by tools/sib/p4-tiles-b/e1a1_job.py.

## What changed
- The per-tile linear 1-99 % stretch is now computed over mesh-valid pixels whose slab mean is > 0. Pixels with a slab mean of 0, and pixels outside mesh-valid, are written as 0.
- Nothing else changed:
  - slab: slices {E.CENTRE - E.HALF}..{E.CENTRE + E.HALF}, level {man1['level_used']};
  - grid: T = {T}, {man1['tile_grid_rows_cols'][0]} x {man1['tile_grid_rows_cols'][1]};
  - eligibility: the same {len(recs)} tiles;
  - output: 1068 x 1068 via INTER_AREA, IHDR/IDAT/IEND only (asserted per file).
- The same rule is applied to all {len(recs)} tiles. {changed} PNGs differ from E1. The rest are byte-identical, because they contain no zero-slab pixel and the stretch is unchanged.
- Reproducibility checks:
  - all {len(todo)} re-downloaded level-3 chunks match the E1 chunk_manifest.jsonl sha256;
  - the mesh inputs match E1's sha256;
  - every tile's old p1/p99, recomputed here, equals the E1 manifest value to within 1e-3.
- The superseded E1 tiles (logs/sib/p4-tiles-b/e1/) stay on the branch unchanged and are not to be read.

## Per tile: zero fraction, old and new stretch
- zero_frac = fraction of mesh-valid pixels with a slab mean of 0.
- Old p1/p99 are from DECL-P4-5; new p1/p99 are from A1.

| tile | zero_frac | old p1 | old p99 | new p1 | new p99 |
|---|---|---|---|---|---|
{rows}

## Timings
- Chunks: {chunk_info['secs']} s.
- Total to the tile push: {round(time.time() - t_start, 1)} s.

## Sub-siblings
- None were created. The rebuild is a single job of a few minutes on this machine, and splitting it would add coordination cost without saving time.
"""
    open(os.path.join(OUT, "REPORT.md"), "w").write(rep)
    E.log(run="e1a1-tiles", status="done", n=len(recs), changed=changed)
    E.commit_push([os.path.join(OUT, "tiles", f"{E.SEG}_r{t['r']}_c{t['c']}.png") for t in recs]
                  + [os.path.join(OUT, f) for f in ("manifest.json", "REPORT.md")] + [E.RUNS] + TOOLS,
                  f"p4-tiles-b E1-A1 (DECL-P4-5-A1): rebuilt 60 raw-CT tiles, manifest, REPORT ({changed} changed)")

    # ---- tile_points.npz for the E1 grid (both frames, M2b method)
    tr = json.load(open(paths[f"{E.VOL}/transform.json"]))
    Maff = np.array(tr["transformation_matrix"], dtype=np.float64)
    B = np.stack([tifffile.imread(paths[f"{MESH24}/{a}.tif"]) for a in "xyz"], -1)
    vB = (B != -1).all(-1)
    hB, wB = vB.shape
    ai, bi = hB / gh, 0.5 * hB / gh - 0.5
    aj, bj = wB / gw, 0.5 * wB / gw - 0.5
    pts, dall, n_aff = {}, [], 0
    for t in recs:
        r, c = t["r"], t["c"]
        i0, i1 = int(np.ceil(r * T / s)), min(int(np.ceil((r + 1) * T / s)), gh)
        j0, j1 = int(np.ceil(c * T / s)), min(int(np.ceil((c + 1) * T / s)), gw)
        vi, vj = np.nonzero(valid[i0:i1, j0:j1])
        n = vi.size
        if n > E.MAX_PTS:
            sel = np.sort(np.random.default_rng(E.PTS_SEED + 1000 * r + c).choice(n, E.MAX_PTS, replace=False))
            vi, vj = vi[sel], vj[sel]
        gi_, gj_ = vi + i0, vj + j0
        P = np.stack([x[gi_, gj_], y[gi_, gj_], z[gi_, gj_]], 1).astype(np.float32)
        fi, fj = gi_ * ai + bi, gj_ * aj + bj
        ii0, jj0 = np.floor(fi).astype(np.int64), np.floor(fj).astype(np.int64)
        ok = (ii0 >= 0) & (jj0 >= 0) & (ii0 + 1 < hB) & (jj0 + 1 < wB)
        ic, jc = np.clip(ii0, 0, hB - 2), np.clip(jj0, 0, wB - 2)
        ok &= vB[ic, jc] & vB[ic + 1, jc] & vB[ic, jc + 1] & vB[ic + 1, jc + 1]
        di, dj = (fi - ic)[:, None], (fj - jc)[:, None]
        Q = (B[ic, jc] * (1 - di) * (1 - dj) + B[ic + 1, jc] * di * (1 - dj)
             + B[ic, jc + 1] * (1 - di) * dj + B[ic + 1, jc + 1] * di * dj).astype(np.float64)
        Aff = P.astype(np.float64) @ Maff[:, :3].T + Maff[:, 3]
        dall.append(np.linalg.norm(Q - Aff, axis=1)[ok])
        n_aff += int((~ok).sum())
        k = f"r{r}_c{c}"
        pts[k] = P
        pts[k + "__f20260411134726"] = np.where(ok[:, None], Q, Aff).astype(np.float32)
        pts[k + "__f20260411134726_src"] = (~ok).astype(np.uint8)
        pts[k + "__grid_ij"] = np.stack([gi_, gj_], 1).astype(np.int32)
        pts[k + "__n_valid_vertices"] = np.array([n], np.int64)
        frac_out = float(((P[:, 0] < 0) | (P[:, 0] >= E.VOL_SHAPE_ZYX[2]) | (P[:, 1] < 0) | (P[:, 1] >= E.VOL_SHAPE_ZYX[1])
                          | (P[:, 2] < 0) | (P[:, 2] >= E.VOL_SHAPE_ZYX[0])).mean())
        assert abs(frac_out - t["frac_outside"]) < 1e-12, (r, c)
    dall = np.concatenate(dall)
    np.savez_compressed(os.path.join(OUT, "tile_points.npz"), **pts)
    pinfo = {"provenance": E.PROV, "segment": E.SEG, "grid": "E1 = P4-D M2a grid (logs/sib/p4-tiles-b/e1/grid.json)",
             "file": "tile_points.npz", "tiles": len(recs),
             "keys": {"r<r>_c<c>": "float32 (n,3) xyz, 20260608103018 L0 voxels (mesh own frame)",
                      "r<r>_c<c>__f20260411134726": "float32 (n,3) xyz, 20260411134726 voxels",
                      "r<r>_c<c>__f20260411134726_src": "uint8 (n,) 0 = same-UV 2.4 um mesh, 1 = affine fallback",
                      "r<r>_c<c>__grid_ij": "int32 (n,2) 1.129 um grid row, col",
                      "r<r>_c<c>__n_valid_vertices": "int64 (1,) valid vertices in the tile before subsampling"},
             "selection": "valid 1.129 um grid vertices whose canvas position (gi*10, gj*10) lies in the tile; if > 4096, "
                          "4096 drawn by numpy default_rng(20260926 + 1000 r + c), sorted (same draw as frac_outside)",
             "frame_20260411134726": {"method": "same UV on the segment's official 20260411134726 tifxyz (bilinear), "
                                                "pixel-centre map i24 = (i + 0.5) * h24 / h1129 - 0.5 (same for j); affine "
                                                "fallback (transform.json) where a bilinear corner is invalid",
                                      "uv_map": {"a_i": ai, "b_i": bi, "a_j": aj, "b_j": bj, "grid_24": [hB, wB]},
                                      "points_via_affine_fallback": n_aff,
                                      "same_uv_vs_affine_dist_vx24": dict(n=int(dall.size), **E.q(dall), max=float(dall.max()))},
             "frac_outside_reproduced": True,
             "inputs": fetch, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(pinfo, open(os.path.join(OUT, "tile_points.json"), "w"), indent=1)
    E.log(run="e1a1-points", status="done", n_aff=n_aff, med_dist=float(np.median(dall)), p95=float(np.percentile(dall, 95)))
    E.commit_push([os.path.join(OUT, f) for f in ("tile_points.npz", "tile_points.json")] + [E.RUNS],
                  "p4-tiles-b E1-A1: tile_points.npz for the E1 (= M2a) grid, both frames")
    for f in os.listdir(SCR):
        if f.endswith(".tif"):
            os.remove(os.path.join(SCR, f))
    E.log(run="e1a1-job", status="done", secs=round(time.time() - t_start, 1))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        E.log(run="e1a1-job", status="FAILED", error=repr(e)[:500])
        raise
