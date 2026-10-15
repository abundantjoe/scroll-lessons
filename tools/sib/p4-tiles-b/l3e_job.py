"""P4-L3 at 1.129 um (RULES.md DECL-P4-12-A4, method DECL-P4-12-A3): calibration on the known-text
control 20260623142658-w028-037, then (only on PASS) L3 tiles of the E1/M2a grid of
20260623141924-w010-027.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile or CT pixel is ever displayed or printed; PNG bytes are hashed and
written, never opened. Order of pushes: (1) calibration selection, before any f(o) number;
(2) calib_1129.json with the verdict and frozen d*, before any title-strip number; (3) tiles.

Usage: python l3e_job.py <scratch_dir> <repo_dir>
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
import e1_job as E  # noqa: E402  (same argv convention)
import l3e_lib as L  # noqa: E402
from hercules.display.builder import linear_window_ct, png_bytes  # noqa: E402

REPO, SCR = sys.argv[2], sys.argv[1]
OUT = os.path.join(REPO, "logs/sib/p4-tiles-b/l3e")
M2B = os.path.join(REPO, "logs/sib/p4-tiles-b/m2b")
E1A1 = os.path.join(REPO, "logs/sib/p4-tiles-b/e1a1")
CSEG = "20260623142658-w028-037"
CSV = f"PHercParis4/segments/{CSEG}/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr"
CMESH = f"PHercParis4/segments/{CSEG}/mesh/20260623142658-on-20260608103018-1.129um.tifxyz"
T_HI = 233
T_HI_SOURCE = ("p4-highz sibling branch, logs/sib/p4-highz/thresholds.json (T_hi 233 = p99.9, "
               "control 1.129 um L1 surface volume level 0, voxels > 0; frozen 2026-09-26T17:50:05Z)")
SEED = 20260926
N_CTRL_TILES, N_CHUNKS_PER_TILE = 24, 40
CAL_LEVEL, TILE_LEVEL = 0, 1
STEP_UM = 2.258
THREADS = 16
TOOLS = [os.path.join(REPO, "tools/sib/p4-tiles-b", f) for f in ("l3e_job.py", "l3e_lib.py", "test_l3e.py", "e1_job.py")]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
    t0 = time.time()
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    E.log(run="l3e-job", status="started", governed_by="DECL-P4-12-A4 (A3 method)")
    # ---------------- control mesh + selection (pushed before any f(o) number)
    m2b_man = json.load(open(os.path.join(M2B, "manifest.json")))
    m2b_grid = json.load(open(os.path.join(M2B, "grid.json")))
    m2b_sha = {f["key"]: f["sha256"] for f in m2b_man["inputs"]}
    px, rx = E.fetch_file(f"{CMESH}/x.tif")
    assert rx["sha256"] == m2b_sha[f"{CMESH}/x.tif"], "control mesh x.tif sha256 differs from M2b record"
    cx = tifffile.imread(px)
    cvalid = cx != -1  # all three coords agree on -1 (M2b grid.json minus1_all_three_agree)
    del cx
    os.remove(px)
    cgh, cgw = cvalid.shape
    CT = m2b_grid["T_px"]
    pool = [t for t in m2b_man["tiles"] if t["stats"]["frac_mesh_points_outside_1129_volume"] < 0.5]
    rng = np.random.default_rng(SEED)
    pick = sorted(rng.choice(len(pool), N_CTRL_TILES, replace=False).tolist())
    sel_tiles = [pool[i] for i in pick]
    sel = []
    for t in sel_tiles:
        r, c = t["r"], t["c"]
        y0, y1 = r * CT, min((r + 1) * CT, cgh * 10)
        x0, x1 = c * CT, min((c + 1) * CT, cgw * 10)
        ys = np.arange(-(-y0 // 128), y1 // 128)
        xs = np.arange(-(-x0 // 128), x1 // 128)
        yy, xx = np.meshgrid(ys, xs, indexing="ij")
        cy, cxx = (yy * 128 + 64) // 10, (xx * 128 + 64) // 10
        good = cvalid[np.minimum(cy, cgh - 1), np.minimum(cxx, cgw - 1)] & (cy < cgh) & (cxx < cgw)
        cand = np.stack([yy[good], xx[good]], 1)
        k = np.random.default_rng(SEED + 1000 * r + c).choice(len(cand), min(N_CHUNKS_PER_TILE, len(cand)), replace=False)
        for yc, xc in sorted(cand[k].tolist()):
            sel.append({"tile": f"r{r}_c{c}", "key": f"{CAL_LEVEL}/0/{yc}/{xc}"})
    selection = {
        "provenance": E.PROV, "serves": "DECL-P4-12-A4 item 1 calibration; recorded before any f(o) number",
        "control_segment": CSEG, "control_surface_volume": CSV, "level": CAL_LEVEL,
        "level_reason": "T_hi 233 was frozen on level 0 of this volume; same level keeps the threshold meaningful",
        "control_tile_grid": "P4-D M2b grid (logs/sib/p4-tiles-b/m2b, T %d)" % CT,
        "tile_pool": "M2b read-eligible tiles with frac_mesh_points_outside_1129_volume < 0.5 (n = %d)" % len(pool),
        "seed": SEED, "tiles_drawn": N_CTRL_TILES, "tile_draw": "numpy default_rng(20260926).choice(pool, 24, no replacement), sorted",
        "chunk_draw": "per tile: level-0 chunks fully inside the tile whose centre px maps to a mesh-valid vertex; "
                      "40 drawn by default_rng(20260926 + 1000 r + c) without replacement",
        "voxel_mask": "voxels at canvas px whose grid vertex (i // 10, j // 10) is mesh-valid",
        "f_definition": "f(o) = (# mask voxels in slice o with value > T_hi) / (# mask voxels in slice o with value > 0); "
                        "alternative denominator (all mask voxels) also reported",
        "T_hi": T_HI, "T_hi_source": T_HI_SOURCE,
        "offsets": "o = (slice - 58) x 2.258 um, slice 0..115 (centre 58 = n//2, E1 convention)",
        "tiles_level_for_L3_if_PASS": TILE_LEVEL,
        "tiles_level_reason": "level 1 (4.516 um in-plane, depth 2.258 um unchanged) of the E1 surface volume: finer than "
                              "the 18.7 um display, and 1/4 of the level-0 transfer; chosen before any number",
        "tiles": [f"r{t['r']}_c{t['c']}" for t in sel_tiles], "chunks": sel, "utc": now()}
    json.dump(selection, open(os.path.join(OUT, "calib_selection.json"), "w"), indent=1)
    E.commit_push([os.path.join(OUT, "calib_selection.json"), E.RUNS] + TOOLS,
                  "p4-tiles-b L3E (DECL-P4-12-A4): calibration selection (seed, 24 control tiles, 960 chunks), "
                  "recorded before any number")

    # ---------------- calibration counts
    n_hi = np.zeros(E.N_SLICES, np.int64)
    n_pos = np.zeros(E.N_SLICES, np.int64)
    n_all = np.zeros(E.N_SLICES, np.int64)
    per_tile = {}
    absent, rot_ok, cman = [], None, []

    def cal(item):
        b = E.get(f"{CSV}/{item['key']}")
        if b is None:
            return item, None, None
        a = np.frombuffer(b, np.uint8).reshape(E.N_SLICES, 128, 128)
        _, yc, xc = map(int, item["key"].split("/")[1:])
        gi = np.minimum((yc * 128 + np.arange(128)) // 10, cgh - 1)
        gj = np.minimum((xc * 128 + np.arange(128)) // 10, cgw - 1)
        m = cvalid[np.ix_(gi, gj)]
        cnt = L.slice_counts(a, m, T_HI)
        rc = None
        if item is sel[0]:
            cr = L.slice_counts(np.rot90(a, 1, axes=(1, 2)), np.rot90(m), T_HI)
            rc = all((x == y).all() for x, y in zip(cnt, cr))
        return item, cnt, (hashlib.sha256(b).hexdigest(), len(b), rc)

    tc = time.time()
    with cf.ThreadPoolExecutor(THREADS) as ex:
        for item, cnt, meta in ex.map(cal, sel):
            if cnt is None:
                absent.append(item["key"])
                continue
            n_hi += cnt[0]
            n_pos += cnt[1]
            n_all += cnt[2]
            pt = per_tile.setdefault(item["tile"], [np.zeros(E.N_SLICES, np.int64), np.zeros(E.N_SLICES, np.int64)])
            pt[0] += cnt[0]
            pt[1] += cnt[1]
            cman.append({"key": item["key"], "sha256": meta[0], "bytes": meta[1]})
            if meta[2] is not None:
                rot_ok = meta[2]
    res = L.calibrate(n_hi, n_pos, STEP_UM, E.CENTRE)
    res_alt = L.calibrate(n_hi, n_all, STEP_UM, E.CENTRE)
    o = (np.arange(E.N_SLICES) - E.CENTRE) * STEP_UM
    f = np.where(n_pos > 0, n_hi / np.maximum(n_pos, 1), np.nan)
    gap = {"offsets_abs_gt_100um": int((np.abs(o) > 100).sum()),
           "f_median_gap": float(np.nanmedian(f[np.abs(o) > 100])), "f_median_within_100um": float(np.nanmedian(f[np.abs(o) <= 100]))}
    per_tile_peaks = {}
    for k, (h, p) in per_tile.items():
        rr = L.calibrate(h, p, STEP_UM, E.CENTRE)
        per_tile_peaks[k] = {"peak_offset_um": rr["global_peak"]["offset_um"], "z": rr["global_peak"]["z"], "verdict": rr["verdict"]}
    offs = [v["peak_offset_um"] for v in per_tile_peaks.values()]
    sl = L.slab_slices(res["d_star_um"], STEP_UM, E.CENTRE, E.N_SLICES) if res["verdict"] == "PASS" else None
    calib = {
        "provenance": E.PROV, "serves": "DECL-P4-12-A4 item 1; frozen before any title-strip number",
        "verdict": res["verdict"], "reasons": res["reasons"], "d_star_um": res["d_star_um"],
        "d_star_slice": res["global_peak"]["slice"] if res["verdict"] == "PASS" else None,
        "L3_slices_if_pass": sl, "L3_window_um": "[d* - 10, d* + 10]",
        "primary": res, "alt_denominator_all_mask_voxels": {k: v for k, v in res_alt.items() if k != "profile"},
        "sides": {"negative": res["side_negative"], "positive": res["side_positive"],
                  "sign_note": "positive o = higher slice index; which side is recto is not established by this builder"},
        "gap_depths": gap, "rot90_sanity_first_chunk_identical": rot_ok,
        "per_tile_peaks": per_tile_peaks,
        "per_tile_peak_offset_um_summary": {"median": float(np.median(offs)), "p10": float(np.percentile(offs, 10)),
                                            "p90": float(np.percentile(offs, 90))},
        "chunks_used": len(cman), "chunks_absent": absent, "voxels_pos_total": int(n_pos.sum()),
        "chunk_sha256": cman, "T_hi": T_HI, "T_hi_source": T_HI_SOURCE,
        "limitations": [
            "The declared rule cannot tell sheet density from an ink layer: T_hi is p99.9 of the sheet slab, so a peak "
            "near o = 0 can be the dense sheet itself (tools/sib/p4-tiles-b/test_l3e.py::test_sheet_bump_without_ink).",
            "On a flat layer-free profile with iid noise, the max-over-116-offsets rule passes falsely at a measured "
            "rate of 0.17 (test_flat_no_layer_false_pass_rate_measured).",
            "For a flat-topped 10-20 um deposit the declared argmax is defined only to within the half thickness; the "
            "half-max centroid is reported as a diagnostic (primary.halfmax_centroid_um), not used as d*."],
        "secs": round(time.time() - tc, 1), "utc": now()}
    json.dump(calib, open(os.path.join(OUT, "calib_1129.json"), "w"), indent=1)
    E.log(run="l3e-calib", verdict=res["verdict"], d_star_um=res["d_star_um"], z=res["global_peak"]["z"],
          centroid=res["halfmax_centroid_um"], chunks=len(cman))
    E.commit_push([os.path.join(OUT, "calib_1129.json"), E.RUNS],
                  f"p4-tiles-b L3E: calib_1129.json, verdict {res['verdict']}"
                  + (f", d* = {res['d_star_um']:.3f} um (frozen before any title-strip number)" if res["d_star_um"] is not None else ""))
    if res["verdict"] != "PASS":
        E.log(run="l3e-job", status="stopped", reason="calibration STOP")
        return

    # ---------------- L3 tiles on the E1 grid (only after the push above)
    e1_man = json.load(open(os.path.join(E1A1, "manifest.json")))
    e1_grid = json.load(open(os.path.join(REPO, "logs/sib/p4-tiles-b/e1/grid.json")))
    e1_sha = {f["key"]: f["sha256"] for f in e1_man["inputs"]}
    px, rx = E.fetch_file(f"{E.MESH}/x.tif")
    assert rx["sha256"] == e1_sha[f"{E.MESH}/x.tif"]
    ex_ = tifffile.imread(px)
    valid = ex_ != -1
    del ex_
    os.remove(px)
    gh, gw = valid.shape
    T = e1_grid["T_px"]
    za1 = json.loads(E.get(f"{E.SV}/{TILE_LEVEL}/.zarray"))
    assert za1["dtype"] == "|u1" and za1["compressor"] is None and za1["chunks"] == [116, 128, 128]
    h1, w1 = za1["shape"][1], za1["shape"][2]
    tiles = e1_man["tiles"]
    rows = sorted({t["r"] for t in tiles})
    R0, R1 = rows[0] * T // 2, min((rows[-1] + 1) * T // 2, h1)
    mx = np.zeros((R1 - R0, w1), np.uint8)
    need = set()
    for t in tiles:
        a0, a1 = t["r"] * T // 2, min((t["r"] + 1) * T // 2, h1)
        b0, b1 = t["c"] * T // 2, min((t["c"] + 1) * T // 2, w1)
        for yc in range(a0 // 128, (a1 - 1) // 128 + 1):
            for xc in range(b0 // 128, (b1 - 1) // 128 + 1):
                need.add((yc, xc))
    need = sorted(need)
    K = np.array(sl)

    def tl(pos):
        yc, xc = pos
        b = E.get(f"{E.SV}/{TILE_LEVEL}/0/{yc}/{xc}")
        if b is None:
            return pos, None, None
        a = np.frombuffer(b, np.uint8).reshape(E.N_SLICES, 128, 128)
        return pos, a[K].max(0), hashlib.sha256(b).hexdigest()

    tman, n_abs, tt = [], 0, time.time()
    with cf.ThreadPoolExecutor(THREADS) as ex:
        for i, (pos, m, h) in enumerate(ex.map(tl, need)):
            if m is None:
                n_abs += 1
                continue
            y0, x0 = pos[0] * 128, pos[1] * 128
            ya, yb = max(y0, R0), min(y0 + 128, R1, h1)
            xb = min(x0 + 128, w1)
            if yb > ya:
                mx[ya - R0:yb - R0, x0:xb] = m[ya - y0:yb - y0, :xb - x0]
            tman.append(f"{TILE_LEVEL}/0/{pos[0]}/{pos[1]} {h}")
            if i % 5000 == 0:
                E.log(run="l3e-chunks", done=i, of=len(need), secs=round(time.time() - tt))
    with open(os.path.join(OUT, "chunk_manifest_L3.txt"), "w") as fo:
        fo.write("\n".join(sorted(tman)) + "\n")
    cm_sha = hashlib.sha256(open(os.path.join(OUT, "chunk_manifest_L3.txt"), "rb").read()).hexdigest()
    E.log(run="l3e-chunks", status="done", n=len(tman), absent=n_abs, secs=round(time.time() - tt))
    recs, batch = [], []
    for t in tiles:
        r, c = t["r"], t["c"]
        a0, a1 = r * T // 2, (r + 1) * T // 2
        b0, b1 = c * T // 2, (c + 1) * T // 2
        img = np.zeros((a1 - a0, b1 - b0), np.float32)
        vm = np.zeros(img.shape, bool)
        e0, e1 = min(a1, h1, R1), min(b1, w1)
        img[:e0 - a0, :e1 - b0] = mx[a0 - R0:e0 - R0, b0:e1]
        gi = np.minimum((2 * np.arange(a0, e0) + 1) // 10, gh - 1)
        gj = np.minimum((2 * np.arange(b0, e1) + 1) // 10, gw - 1)
        vm[:e0 - a0, :e1 - b0] = valid[np.ix_(gi, gj)]
        pos_ = vm & (img > 0)
        u8, (lo, hi) = linear_window_ct(img, pos_)
        u8[~pos_] = 0
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
        vals = img[vm]
        pv = img[pos_]
        recs.append({"r": r, "c": c, "file": f"tiles/{name}", "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                     "valid_fraction": t["valid_fraction"], "frac_outside": t["frac_outside"],
                     "canvas_rows": t["canvas_rows"], "canvas_cols": t["canvas_cols"],
                     "level1_rows": [a0, a1], "level1_cols": [b0, b1],
                     "stats": {"frac_mesh_points_outside_1129_volume": t["frac_outside"],
                               "frac_valid_zero": float((vals == 0).mean()), "stretch_p1": lo, "stretch_p99": hi,
                               "max_mean_valid_pos": float(pv.mean()), "max_std_valid_pos": float(pv.std()),
                               "frac_valid_pos_gt_T_hi": float((pv > T_HI).mean())}})
        batch.append(os.path.join(OUT, "tiles", name))
        if len(recs) == 40:
            E.commit_push(batch + [E.RUNS], f"p4-tiles-b L3E: first 40 L3 tiles (d* = {res['d_star_um']:.3f} um)")
            batch = []
    man = {"provenance": E.PROV, "serves": "RULES.md DECL-P4-12-A4 item 2 (L3 at 1.129 um); sibling task p4-tiles-b",
           "segment": E.SEG, "material": f"official surface volume {E.SV} (raw CT, no model)",
           "channel": {"d_star_um": res["d_star_um"], "slices": sl, "offsets_um": [float((k - E.CENTRE) * STEP_UM) for k in sl],
                       "rule": "per pixel max over slices with offset in [d* - 10, d* + 10] um",
                       "calibration": "calib_1129.json (pushed before this channel was computed)"},
           "level_used": TILE_LEVEL, "level_inplane_um": 4.516, "px_per_mm": e1_man["px_per_mm"], "T_px": T,
           "tile_grid_rows_cols": e1_man["tile_grid_rows_cols"],
           "display": {"values": "per-tile linear 1-99 % stretch over mesh-valid px with max > 0 (builder.linear_window_ct); "
                                 "px with max 0 and px outside mesh-valid written as 0 (DECL-P4-5-A1 rule)",
                       "downscale": "cv2.resize INTER_AREA to 1068 x 1068 from the level-1 crop (4436 px)",
                       "px_per_mm": 53.4, "encoder": "builder.png_bytes; chunks IHDR/IDAT/IEND only"},
           "eligibility": e1_man["eligibility"], "tiles_eligible": len(recs),
           "chunks": {"needed": len(need), "present": len(tman), "absent_fill0": n_abs,
                      "chunk_manifest": "chunk_manifest_L3.txt", "chunk_manifest_sha256": cm_sha},
           "viewing": "no image, tile or CT pixel was opened, displayed or described by the builder",
           "tiles": recs, "secs_total": round(time.time() - t0, 1), "utc": now()}
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    p1 = [x["stats"]["stretch_p1"] for x in recs]
    rep = f"""{E.PROV}

# p4-tiles-b report: P4-L3 at 1.129 um (DECL-P4-12-A4)

Builder role only. No tile, map or CT pixel was opened, viewed, displayed or described. Only numbers and hashes were computed. This report was generated by tools/sib/p4-tiles-b/l3e_job.py.

## Calibration (calib_1129.json, pushed before any title-strip number)
- Control: {CSEG}, 1.129 um L1 surface volume, level {CAL_LEVEL}.
  - Sample: {N_CTRL_TILES} M2b-grid tiles with coverage < 0.5, drawn by seed {SEED}. {len(cman)} chunks were used and {len(absent)} were absent.
  - T_hi = {T_HI}, the frozen value from p4-highz.
- Verdict: **{res['verdict']}**.
  - d* = {res['d_star_um']} um (slice {res['global_peak']['slice']}), with z = {res['global_peak']['z']:.2f} robust SD.
  - Half-max centroid: {res['halfmax_centroid_um']:.2f} um; width {res['halfmax_width_um']:.1f} um.
- Mesh sides (peak offset / z):
  - negative side: {res['side_negative']['offset_um']:.2f} um / {res['side_negative']['z']:.2f};
  - positive side: {res['side_positive']['offset_um']:.2f} um / {res['side_positive']['z']:.2f}.
- Per-tile peak offsets: median {calib['per_tile_peak_offset_um_summary']['median']:.2f} um, p10-p90 {calib['per_tile_peak_offset_um_summary']['p10']:.2f} to {calib['per_tile_peak_offset_um_summary']['p90']:.2f} um.
- Limitations (see calib_1129.json `limitations` and the unit tests):
  - The rule cannot separate sheet density from ink at o ~ 0.
  - On a flat layer-free profile the rule falsely passes at a measured rate of 0.17.
  - For a flat-topped deposit, the argmax is defined only to within the half thickness.

## Unit tests (tools/sib/p4-tiles-b/test_l3e.py, 27 pass)
- A synthetic peaked layer at 5 offsets, with and without a sheet bump, is recovered within 5 um.
- For a flat-topped 15.8 um layer, the argmax falls within the half thickness and the centroid within 5 um.
- No bright voxels gives STOP. A layer outside +-100 um gives STOP.
- Documented limitations: the flat-noise false-PASS rate, measured at 0.17, and a PASS at d* ~ 0 for a pure sheet bump.

## L3 tiles (logs/sib/p4-tiles-b/l3e/)
- Grid: {len(recs)} tiles on the E1/M2a grid (T {T}), using the e1a1 tile list and its DECL-P4-4-A1 coverage values.
- Channel: per-pixel max over slices {sl} of the E1 surface volume, level {TILE_LEVEL} (4.516 um in-plane).
- Display: per-tile 1-99 % stretch over mesh-valid pixels with max > 0; everything else is 0. INTER_AREA to 1068 px.
- Chunks: {len(tman)} present and {n_abs} absent; chunk_manifest_L3.txt has sha256 {cm_sha}.
- stretch p1: min {min(p1):.1f}, median {float(np.median(p1)):.1f}. Unique PNG sha256: {len(set(x['png_sha256'] for x in recs))} of {len(recs)}.
- Total time: {round(time.time() - t0)} s.

## Sub-siblings
- None were created. The job is transfer-bound on one machine, and splitting it would not change the calibration-first order.
"""
    open(os.path.join(OUT, "REPORT.md"), "w").write(rep)
    E.log(run="l3e-job", status="done", tiles=len(recs), secs=round(time.time() - t0, 1))
    E.commit_push(batch + [os.path.join(OUT, f) for f in ("manifest.json", "REPORT.md", "chunk_manifest_L3.txt")] + [E.RUNS],
                  f"p4-tiles-b L3E: remaining L3 tiles, manifest, REPORT ({len(recs)} tiles)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        E.log(run="l3e-job", status="FAILED", error=repr(e)[:500])
        raise
