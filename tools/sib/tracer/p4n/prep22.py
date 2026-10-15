# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-22: local re-trace of the w010-027 low patch r5-r8 x c14-c19 (strip-a grid). Geometry only.

Operationalisation (fixed before any trace of this patch exists):
- Patch P = official grid rows [round(5T), end) x cols [round(14T), round(20T)), T = 8343/20; worked on every
  SUB-th vertex (SUB = 4, 0.192 mm), the same grid as P4-N.
- Defects (on the SUB-4 grid of the official mesh): vertices of transversely self-intersecting quads
  (vc_tifxyz_selfcross) and severe close approaches (neighbour-winding clearance < 0.3 x local spacing,
  p4-core's ratio_frac_lt_0p3 level). Holes = defects dilated by HOLE_DILATE grid steps (1.9 mm), inside P.
- The tracer (c5, L15 + gate_fix_resume_points) regrows the holes from the surrounding clean official vertices,
  which stay fixed. Growth stays short (holes <= a few mm across), the regime validated by the P4-N holdout
  (first 2 mm: 0.1 % of vertices > 20 vox off truth, against 5.6 % over 5.4 mm).
- The adoption gate compares the whole of P (official outside holes + re-trace inside) with the official
  mesh on P, with P4-N's metrics.

  prep22.py fetch     local m7-L2 crop covering P + margin (chunk copy, sha256 manifest)
  prep22.py official  official P (+ ring) in the local L2 frame -> /work/p422/official.tifxyz
  prep22.py holes     defects + holes -> /work/p422/resume.tifxyz (official with holes removed), holes.npy
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import prep  # noqa: E402

import os
CFG = os.environ.get("P4_CFG", "p422")
REPO = Path("/home/user/dominion")
SUB = 4
HOLE_DILATE = 10
T = prep.T_GRID
if CFG == "p422":           # DECL-P4-22: r5-r8 x c14-c19, rows to the mesh end, 25-step ring
    W = Path("/work/p422"); OUTLOG = REPO / "logs/sib/tracer/p4-22"
    RING = 25
    R0, R1, C0, C1 = round(5 * T), None, round(14 * T), round(20 * T)
elif CFG == "p424":         # DECL-P4-24 item 2: tile r2_c19 (p4-core tile frame: (k*8343)//20), 1-tile ring
    W = Path("/work/p424"); OUTLOG = REPO / "logs/sib/tracer/p4-24"
    RING = 104              # 104 steps x 4 = 416 official rows/cols = 1 tile
    R0, R1, C0, C1 = (2 * 8343) // 20, (3 * 8343) // 20, (19 * 8343) // 20, (20 * 8343) // 20
else:
    raise SystemExit(f"unknown P4_CFG {CFG}")


def official_crop():
    P = prep.load_official()
    r0 = R0 - RING * SUB
    r1 = P.shape[0] if R1 is None else min(P.shape[0], R1 + RING * SUB)
    c0, c1 = C0 - RING * SUB, min(P.shape[1], C1 + RING * SUB)
    crop = P[r0:r1:SUB, c0:c1:SUB]
    rows = np.arange(r0, r1, SUB)[: crop.shape[0]]
    cols = np.arange(c0, c1, SUB)[: crop.shape[1]]
    inP = (rows[:, None] >= R0) & (cols[None, :] >= C0) & (cols[None, :] < C1)
    if R1 is not None:
        inP &= rows[:, None] < R1
    return crop, inP, rows, cols


def origin():
    return np.array(json.loads((W / "frame.json").read_text())["origin_xyz"])


def to_local(p):
    o = p / 4.0 - origin(); o[p[..., 0] == -1] = -1; return o


def to_native(p):
    o = (p + origin()) * 4.0; o[p[..., 0] == -1] = -1; return o


def cmd_fetch():
    import fetch_m7l2 as F
    crop, inP, _, _ = official_crop()
    v = crop[..., 0] != -1
    lo = crop[v].min(0) / 4 - 40; hi = crop[v].max(0) / 4 + 40          # L2 xyz with 40-vox margin
    C = 192
    F.CX = (int(lo[0] // C), int(hi[0] // C) + 1)
    F.CY = (int(lo[1] // C), int(hi[1] // C) + 1)
    F.CZ = (int(max(lo[2], 0) // C), int(hi[2] // C) + 1)
    F.ORIGIN = (F.CZ[0] * C, F.CY[0] * C, F.CX[0] * C)
    F.OUT = W / "m7l2_local.zarr"
    F.MAN = OUTLOG / "m7l2_chunks_sha256.jsonl"
    W.mkdir(parents=True, exist_ok=True); OUTLOG.mkdir(parents=True, exist_ok=True)
    (W / "frame.json").write_text(json.dumps({"origin_xyz": [F.ORIGIN[2], F.ORIGIN[1], F.ORIGIN[0]],
        "chunks_zyx": [F.CZ, F.CY, F.CX]}, indent=1))
    F.main()


def cmd_official():
    crop, inP, rows, cols = official_crop()
    prep.write_tifxyz(W / "official.tifxyz", to_local(crop.copy()), "p422_official_L2")
    np.save(W / "inP.npy", inP)
    info = {"official_rows": [int(rows[0]), int(rows[-1])], "official_cols": [int(cols[0]), int(cols[-1])],
            "sub": SUB, "ring": RING, "shape": list(crop.shape[:2]), "n_valid": int((crop[..., 0] != -1).sum()),
            "n_valid_in_P": int(((crop[..., 0] != -1) & inP).sum()),
            "z_mm_in_P": [float(crop[inP & (crop[..., 0] != -1)][:, 2].min() * prep.VOX_MM),
                          float(crop[inP & (crop[..., 0] != -1)][:, 2].max() * prep.VOX_MM)]}
    (OUTLOG / "official_prep.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info))


def cmd_holes():
    import metrics as M
    import surfmetrics as SM
    g = M.read_grid(W / "official.tifxyz")
    inP = np.load(W / "inP.npy")
    v = g[..., 0] != -1
    rep = SM.selfcross(W / "official.tifxyz", W / "official_selfcross.json", REPO / "logs/sib/tracer/runs.jsonl",
                       "p422_official_selfcross")
    pairs = SM.crossing_pairs(rep)
    sx = np.zeros(g.shape[:2], bool)
    for qa, qb in pairs:
        for (r, c) in (qa, qb):
            sx[r:r + 2, c:c + 2] = True
    import metrics22 as M22
    _, _, rows, cols = official_crop()
    gn = to_native(g.copy())
    cl = M22.clearance_grid(gn)
    tr, tc = M22.tile_ids(g.shape[:2], rows, cols)
    sp = M22.spacing_by_tile(cl, inP, tr, tc)
    ratio = M22.ratio_from(cl, sp, tr, tc)
    np.save(W / "clearance_official.npy", cl)
    (OUTLOG / "spacing_by_tile.json").write_text(json.dumps({f"r{a}_c{b}": v for (a, b), v in sp.items()}, indent=1))
    close = v & np.isfinite(ratio) & (ratio < 0.3)
    defects = (sx | close) & inP & v
    holes = binary_dilation(defects, iterations=HOLE_DILATE) & inP & v
    np.save(W / "holes.npy", holes); np.save(W / "ratio_official.npy", ratio)
    res = np.where(holes[..., None], -1.0, g)
    prep.write_tifxyz(W / "resume.tifxyz", res, "p422_resume_L2")
    info = {"selfcross_pairs_official_patch": len(pairs), "selfcross_pairs_in_P": int(sum(
                1 for qa, qb in pairs if inP[qa] or inP[qb])),
            "n_selfcross_vertices_in_P": int((sx & inP).sum()), "n_close_lt0p3_in_P": int((close & inP).sum()),
            "n_defect_vertices": int(defects.sum()), "n_hole_vertices": int(holes.sum()),
            "hole_frac_of_P": float(holes.sum() / max((inP & v).sum(), 1)), "hole_dilate": HOLE_DILATE}
    (OUTLOG / "holes.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info))


P_MIN = 16.602701885666242   # p4-core holes.json p_min_prominence (627b42fc), test (d) of DECL-P4-24


def offsheet_flags(Pn: np.ndarray, mask: np.ndarray, Nn: np.ndarray, threads: int = 32,
                   checkpoint: str | None = None) -> np.ndarray:
    """p4-core DECL-P4-24 (d) test per vertex: +-60 um (+-25 vox) L0 normal profile, Gaussian sigma 1,
    no local maximum with prominence >= P_MIN -> off-sheet (True). CT read as numbers only (byte ranges)."""
    import concurrent.futures as cf
    sys.path.insert(0, str(HERE / "ext" / "p4core"))
    from mesh_audit import profile
    from holes import best_prom
    idx = np.argwhere(mask & np.isfinite(Nn).all(-1))
    def one(ij):
        return best_prom(profile(Pn[ij[0], ij[1]], Nn[ij[0], ij[1]])[1])[0]
    # resumable: results checkpointed every 500 vertices (container restarts are frequent)
    ck = W / f"prom_ckpt_{checkpoint}.npy" if checkpoint else None
    prom = np.full(len(idx), np.nan)
    if ck is not None and ck.exists():
        old = np.load(ck)
        if old.shape == prom.shape:
            prom = old
    todo = np.flatnonzero(~np.isfinite(prom))
    with cf.ThreadPoolExecutor(threads) as ex:
        for k in range(0, len(todo), 500):
            part = todo[k:k + 500]
            prom[part] = list(ex.map(one, [tuple(idx[i]) for i in part]))
            if ck is not None:
                np.save(ck, prom)
    out = np.full(mask.shape, np.nan)
    out[idx[:, 0], idx[:, 1]] = prom
    return out


def native_normals_sub():
    """Normals as p4-core computes them (central differences on the FULL-resolution official grid), sampled at
    the SUB-4 crop positions."""
    sys.path.insert(0, str(HERE / "ext" / "p4core"))
    from mesh_audit import normals
    P = prep.load_official()
    _, _, rows, cols = official_crop()
    r0, r1, c0, c1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
    blk = P[max(r0 - 1, 0):r1 + 1, max(c0 - 1, 0):c1 + 1].copy()
    blk[blk[..., 0] == -1] = np.nan
    N = normals(blk)
    return N[(rows - max(r0 - 1, 0))[:, None], (cols - max(c0 - 1, 0))[None, :]]


def cmd_offsheet():
    """DECL-P4-24 item 2 holes: off-sheet vertices inside P, dilated by HOLE_DILATE, inside P."""
    g = __import__("metrics").read_grid(W / "official.tifxyz")
    inP = np.load(W / "inP.npy")
    v = g[..., 0] != -1
    gn = to_native(g.copy())
    N = native_normals_sub()
    prom = offsheet_flags(gn, inP & v, N, checkpoint="official")
    np.save(W / "prom_official.npy", prom)
    off = inP & v & np.isfinite(prom) & (prom < P_MIN)
    holes = binary_dilation(off, iterations=HOLE_DILATE) & inP & v
    np.save(W / "holes.npy", holes)
    res = np.where(holes[..., None], -1.0, g)
    prep.write_tifxyz(W / "resume.tifxyz", res, f"{CFG}_resume_L2")
    tested = inP & v & np.isfinite(prom)
    info = {"cfg": CFG, "p_min": P_MIN, "n_tested_in_P": int(tested.sum()),
            "offsheet_frac_in_P": float(off.sum() / max(tested.sum(), 1)),
            "p4core_40_sample_estimate": 0.375, "n_offsheet": int(off.sum()), "n_hole_vertices": int(holes.sum()),
            "hole_frac_of_P": float(holes.sum() / max((inP & v).sum(), 1)), "hole_dilate": HOLE_DILATE}
    (OUTLOG / "holes.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info))


if __name__ == "__main__":
    {"fetch": cmd_fetch, "official": cmd_official, "holes": cmd_holes, "offsheet": cmd_offsheet}[sys.argv[1]]()
