# Provenance: Project HERCULES | owner the owner | [id removed]
"""Driver for the P4-TAG search (rules in tag_search.py). Numbers only.

usage: tag_run.py <outer_dir> <umb.json> <out tag.json>
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tag_search as ts  # noqa: E402

F = ts.F
MM_L0 = 1 / 2.4e-3


def xy_window(outline):
    P = outline.P
    m = 5.0 * MM_L0
    x0 = int(max(0, (P[:, 0].min() - m) // F))
    x1 = int(min(2044, (P[:, 0].max() + m) // F + 1))
    y0 = int(max(0, (P[:, 1].min() - m) // F))
    y1 = int(min(2044, (P[:, 1].max() + m) // F + 1))
    return y0, y1, x0, x1


def bands(outline):
    b = BAND = ts.BAND_MM * MM_L0
    return {"bottom": (ts.Z_FIRST, outline.zmin + BAND), "top": (outline.zmax - BAND, ts.Z_LAST + 1)}


def threshold(outline, bnds, n=3000, seed=20260926):
    rng = np.random.default_rng(seed)
    P = outline.P
    sel = np.zeros(len(P), bool)
    for lo, hi in bnds.values():
        sel |= (P[:, 2] >= lo) & (P[:, 2] < hi)
    idx = np.where(sel)[0]
    idx = rng.choice(idx, min(n, len(idx)), replace=False)
    Q = (P[idx] // F).astype(int)          # x, y, z at L4
    vals = []
    chunks = {}
    for q in Q:
        chunks.setdefault((q[2] // ts.CH, q[1] // ts.CH, q[0] // ts.CH), []).append(q)
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(32) as ex:
        for key, a in zip(chunks, ex.map(lambda k: ts.fetch_chunk(ts.LEVEL, *k), list(chunks))):
            for q in chunks[key]:
                if a is None:
                    vals.append(0)
                    continue
                vals.append(int(a[q[2] % ts.CH, q[1] % ts.CH, q[0] % ts.CH]))
    v = np.array(vals)
    # max over a +-1 voxel neighbourhood is not taken: the mesh lies on the sheet
    return {"n_vertices": int(len(v)), "n_chunks": len(chunks), "median_at_mesh": float(np.median(v)),
            "p10_p90_at_mesh": [float(np.percentile(v, 10)), float(np.percentile(v, 90))],
            "zero_frac_at_mesh": float(np.mean(v == 0))}


def process_band(outline, name, zr, win, thr_list, plant=None):
    """Returns per-slice stats and sparse candidate coords per threshold."""
    y0, y1, x0, x1 = win
    z0 = int(zr[0] // F)
    z1 = int(math.ceil(zr[1] / F))
    z1 = min(z1, 4737)
    H, W = y1 - y0, x1 - x0
    stats = []
    cands = {t: [] for t in thr_list}
    absent_tot = jobs_tot = 0
    cache = {}
    for cz in range(z0 // ts.CH, (z1 - 1) // ts.CH + 1):
        za, zb = max(z0, cz * ts.CH), min(z1, (cz + 1) * ts.CH)
        blk, absent, nj = ts.read_block(ts.LEVEL, za, zb, y0, y1, x0, x1)
        absent_tot += absent
        jobs_tot += nj
        if plant is not None:
            plant(blk, za, (y0, x0))
        for k in range(zb - za):
            z = za + k
            zl0 = (z + 0.5) * F
            zbin = int(zl0 // MM_L0)
            if zbin not in cache:
                cache = {zbin: ts.excess_map(outline, zl0, (H, W), (y0, x0))}
            ex = cache[zbin]
            I = blk[k]
            inside = ex < 0
            shell = (ex > ts.EXCESS_MM) & (ex < 5.0)
            st = {"z_l4": z, "n_inside": int(inside.sum()),
                  "occ_inside": float(np.mean(I[inside] > thr_list[0])) if inside.any() else 0.0,
                  "shell_px": int(shell.sum()), "shell_nonzero_frac": float(np.mean(I[shell] > 0)) if shell.any() else 0.0}
            for t in thr_list:
                m = (I > t) & (ex > ts.EXCESS_MM)
                yy, xx = np.nonzero(m)
                if yy.size:
                    cands[t].append(np.stack([np.full(yy.size, z), yy + y0, xx + x0, ], 1).astype(np.int32))
                    cands[t].append(None)
                    cands[t][-1] = ex[yy, xx].astype(np.float32)
                st[f"n_cand_{t:g}"] = int(yy.size)
            # everything above threshold anywhere in the slice (for beyond-end detection)
            st["n_above_thr_all"] = int((I > thr_list[0]).sum())
            stats.append(st)
        del blk
    out = {}
    for t in thr_list:
        L = cands[t]
        C = np.concatenate(L[0::2]) if L else np.zeros((0, 3), np.int32)
        E = np.concatenate(L[1::2]) if L else np.zeros(0, np.float32)
        out[t] = (C, E)
    return stats, out, absent_tot, jobs_tot


def physical_end(stats, side):
    occ = np.array([s["occ_inside"] for s in stats])
    z = np.array([s["z_l4"] for s in stats])
    med = np.median(occ[occ > 0]) if (occ > 0).any() else 0
    ok = occ >= 0.05 * med
    if not ok.any():
        return None
    return int(z[ok].min()) if side == "bottom" else int(z[ok].max())


def beyond_end_candidates(outline, name, zr, win, thr, zend):
    """Voxels above thr in slices more than 0.5 mm beyond the physical end."""
    y0, y1, x0, x1 = win
    g = int(math.ceil(0.5 * MM_L0 / F))
    if name == "bottom":
        za, zb = max(int(zr[0] // F), 0), zend - g
    else:
        za, zb = zend + g + 1, min(int(math.ceil(zr[1] / F)), 4737)
    if zb <= za:
        return np.zeros((0, 3), np.int32), np.zeros(0, np.float32), [za, zb]
    C, E = [], []
    for cz in range(za // ts.CH, (zb - 1) // ts.CH + 1):
        a, b = max(za, cz * ts.CH), min(zb, (cz + 1) * ts.CH)
        blk, _, _ = ts.read_block(ts.LEVEL, a, b, y0, y1, x0, x1)
        zz, yy, xx = np.nonzero(blk > thr)
        C.append(np.stack([zz + a, yy + y0, xx + x0], 1).astype(np.int32))
        E.append((np.abs(zz + a - zend) * F / MM_L0).astype(np.float32))
    return np.concatenate(C), np.concatenate(E), [za, zb]


def main(outer_dir, umb, out_path):
    t0 = time.time()
    ol = ts.Outline(Path(outer_dir), Path(umb))
    win = xy_window(ol)
    bnds = bands(ol)
    thr_info = threshold(ol, bnds)
    thr = 0.5 * thr_info["median_at_mesh"]
    thr_lo = 0.35 * thr_info["median_at_mesh"]
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "entry": "DECL-P4-15 (c) P4-TAG, numbers only; no render",
           "viewing": "No image, tile or CT pixel was viewed or described; L4 chunks were streamed as numbers into masks and component statistics, then discarded.",
           "volume": ts.VOL, "level": ts.LEVEL, "voxel_mm": ts.VOX_MM, "outer_meshes": list(ts.OUTER),
           "outer_mesh_z_mm": [ol.zmin * 2.4e-3, ol.zmax * 2.4e-3],
           "outline_empty_bin_frac_p50_p95": [float(np.median(ol.empty_frac)), float(np.percentile(ol.empty_frac, 95))],
           "xy_window_l4_yx": list(win), "bands_l0_z": {k: [float(a), float(b)] for k, (a, b) in bnds.items()},
           "threshold": {**thr_info, "thr": thr, "thr_sensitivity": thr_lo}, "bands": {}}
    for name, zr in bnds.items():
        stats, cands, absent, nj = process_band(ol, name, zr, win, [thr, thr_lo])
        zend = physical_end(stats, name)
        C, E = cands[thr]
        bC, bE, brange = beyond_end_candidates(ol, name, zr, win, thr, zend) if zend is not None else (np.zeros((0, 3), np.int32), np.zeros(0, np.float32), None)
        CC = np.concatenate([C, bC])
        EE = np.concatenate([E, bE])
        lab, k = ts.components(CC)
        comps = ts.component_stats(CC, EE, lab, k)
        comps.sort(key=lambda c: -c["n_vox"])
        Cl, El = cands[thr_lo]
        lab2, k2 = ts.components(Cl)
        comps_lo = ts.component_stats(Cl, El, lab2, k2)
        shell_nz = [s["shell_nonzero_frac"] for s in stats if s["shell_px"] > 0]
        res["bands"][name] = {
            "z_l4": [stats[0]["z_l4"], stats[-1]["z_l4"]], "chunks_read": nj, "chunks_absent": absent,
            "physical_end_z_l4": zend, "physical_end_z_mm": None if zend is None else zend * ts.VOX_MM,
            "outer_mesh_edge_z_mm": (ol.zmin if name == "bottom" else ol.zmax) * 2.4e-3,
            "beyond_end_slices_l4": brange,
            "shell_0p5_5mm_inside_mask_frac": {"median": float(np.median(shell_nz)) if shell_nz else None,
                                               "p5": float(np.percentile(shell_nz, 5)) if shell_nz else None,
                                               "p95": float(np.percentile(shell_nz, 95)) if shell_nz else None},
            "n_candidate_voxels": int(len(CC)), "n_candidate_voxels_beyond_end": int(len(bC)),
            "n_components_ge8vox": len(comps), "n_sheet_like": sum(c["sheet_like"] for c in comps),
            "n_sheet_like_attached": sum(c["sheet_like"] and c["attached"] for c in comps),
            "components_top50": comps[:50],
            "sensitivity_thr035": {"n_candidate_voxels": int(len(Cl)), "n_components_ge8vox": len(comps_lo),
                                   "n_sheet_like": sum(c["sheet_like"] for c in comps_lo),
                                   "n_sheet_like_attached": sum(c["sheet_like"] and c["attached"] for c in comps_lo)},
            "slice_stats_every10": stats[::10]}
        json.dump(res, open(out_path, "w"), indent=1)
        print(name, json.dumps({k: v for k, v in res["bands"][name].items() if k not in ("components_top50", "slice_stats_every10")}), flush=True)
    res["wall_s"] = time.time() - t0
    json.dump(res, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
