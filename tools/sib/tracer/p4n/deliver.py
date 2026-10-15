# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-N delivery: trim the raw trace to the declared extension and write deliverables. Geometry only.

  deliver.py <run_dir> <mode> [max_rows]

Trim rule (fixed before the real output was looked at): keep the official patch plus the new vertices that
lie ABOVE an official column (1..max_rows grid rows above that column's official top vertex) and inside the
window columns c9-c15 (official grid cols [round(9*T), round(16*T)), T = 8343/20). Growth sideways past the
window and downward below the patch is dropped.

Writes, inside <run_dir>/trimmed/:
  surface_L2.tifxyz/               official patch + kept new vertices, local L2 frame (for metrics.py)
  <run_dir>/deliver/extension_native.tifxyz          kept new vertices only, native 2.4 um frame, scale 1/80
  <run_dir>/deliver/extension_with_seam_native.tifxyz official patch + kept new vertices, native frame, scale 1/80
  <run_dir>/organizer_check.json    point-to-surface distance to the organizers' 20231016151002 2.4 um mesh
                                    (new vertices) vs the same for official top-band vertices (baseline).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import metrics as M  # noqa: E402
import prep  # noqa: E402

ORG = Path("/work/s3/PHercParis4/segments/20231016151002/mesh/20231016151002-on-20260411134726-2.4um.tifxyz")


def surf_dist(q: np.ndarray, grid: np.ndarray, k: int = 8) -> np.ndarray:
    tris, _ = M.tri_mesh(grid, np.zeros(grid.shape[:2] + (2,)))
    tt = cKDTree(tris.mean(1))
    _, it = tt.query(q, k=k)
    dt = np.min(np.stack([M.point_tri_dist(q, tris[it[:, j]]) for j in range(k)], 1), 1)
    dv, _ = cKDTree(grid[grid[..., 0] != -1]).query(q)
    return np.minimum(dt, dv)                      # fail-closed (CORR-RETRACE-RULE form)


def main(run: Path, mode: str, max_rows: int):
    out_dir = M.find_output(run)
    out = M.read_grid(out_dir)
    pat = M.read_grid(Path(f"/work/p4n/patches/{mode}.tifxyz"))
    info = json.loads(Path(f"/work/p4n/patches/{mode}.tifxyz_prep.json").read_text())
    dy, dx, _ = M.locate_resume(out, pat)
    H, W = pat.shape[:2]
    off = np.zeros(out.shape[:2], bool)
    off[dy:dy + H, dx:dx + W] = pat[..., 0] != -1
    new = (out[..., 0] != -1) & ~off
    a0 = info["official_cols"][0]
    ocol = a0 + (np.arange(out.shape[1]) - dx) * prep.SUB          # official native col of each output col
    inwin = (ocol >= round(9 * prep.T_GRID)) & (ocol < round(16 * prep.T_GRID))
    top = np.array([np.flatnonzero(off[:, c]).min() if off[:, c].any() else -1 for c in range(out.shape[1])])
    rows = np.arange(out.shape[0])[:, None]
    h = np.where(top[None, :] >= 0, top[None, :] - rows, -1)
    keep = new & inwin[None, :] & (h >= 1) & (h <= max_rows)
    trimmed = np.where((off | keep)[..., None], out, -1.0)
    rr = np.flatnonzero((off | keep).any(1)); cc = np.flatnonzero((off | keep).any(0))
    # the crop always contains the whole resume-patch rectangle (metrics.locate_resume needs it)
    sl = (slice(min(rr.min(), dy), max(rr.max() + 1, dy + H)), slice(min(cc.min(), dx), max(cc.max() + 1, dx + W)))
    td = run / "trimmed"
    if td.exists():
        shutil.rmtree(td)
    prep.write_tifxyz(td / "surface_L2.tifxyz", trimmed[sl], f"p4n_{mode}_trimmed_L2")
    shutil.copy(run / "params.json", td / "params.json")
    nat_all = prep.to_native(trimmed[sl].copy())
    nat_ext = np.where(keep[sl][..., None], nat_all, -1.0)
    for name, g in (("extension_native.tifxyz", nat_ext), ("extension_with_seam_native.tifxyz", nat_all)):
        d = run / "deliver" / name
        if d.exists():
            shutil.rmtree(d)
        prep.write_tifxyz(d, g, f"p4n_{mode}_{name.split('.')[0]}")
        m = json.loads((d / "meta.json").read_text()); m["scale"] = [1.0 / 80, 1.0 / 80]
        m["hrc_frame"] = "native 2.4 um voxels of 20260411134726; grid step 80 vox (0.192 mm)"
        (d / "meta.json").write_text(json.dumps(m, indent=1) + "\n")
    # organizer-mesh check
    org = np.stack([__import__("tifffile").imread(ORG / f"{a}.tif") for a in "xyz"], -1).astype(np.float64)
    qn = nat_all[keep[sl]]
    dn = surf_dist(qn, org)
    # baseline per output column: official vertices of that column in the top 1 mm of the patch
    offm = off[sl]
    Rn, Cn = np.nonzero(offm)
    offn = nat_all[Rn, Cn]
    zt = np.percentile(offn[:, 2], 99)
    bsel = offn[:, 2] >= zt - 1.0 / prep.VOX_MM
    db = surf_dist(offn[bsel], org)
    colbase = np.full(offm.shape[1], np.nan)
    for c in np.unique(Cn[bsel]):
        colbase[c] = np.median(db[Cn[bsel] == c])
    overlap_cols = colbase <= 4.0                   # organizer mesh coincides with the official mesh here
    Rk, Ck = np.nonzero(keep[sl])
    ov = overlap_cols[Ck]
    hk = h[sl][keep[sl]]
    tile = ((ocol[sl[1]][None, :].repeat(keep[sl].shape[0], 0))[keep[sl]] / prep.T_GRID).astype(int)

    def st(x):
        x = x[np.isfinite(x)]
        return {"n": int(x.size), "median": float(np.median(x)), "p90": float(np.percentile(x, 90)),
                "frac_le_4": float(np.mean(x <= 4)), "frac_le_8": float(np.mean(x <= 8)),
                "frac_gt_20": float(np.mean(x > 20)), "frac_gt_40": float(np.mean(x > 40))} if x.size else {"n": 0}
    chk = {"organizer_mesh": str(ORG), "form": "min(nearest vertex, point-to-triangle), native vox",
           "overlap_rule": "output columns whose official top-1mm vertices have median distance <= 4 vox to the organizer mesh",
           "n_overlap_cols": int(overlap_cols.sum()), "n_cols": int(np.isfinite(colbase).sum()),
           "new_vertices_all": st(dn), "new_vertices_overlap_cols": st(dn[ov]),
           "official_top_1mm_baseline_overlap_cols": st(db[overlap_cols[Cn[bsel]]]),
           "new_overlap_by_tile": {f"c{t}": st(dn[ov & (tile == t)]) for t in range(9, 16)},
           "new_overlap_by_height_rows": {f"{lo}-{hi}": st(dn[ov & (hk >= lo) & (hk <= hi)]) for lo, hi in ((1, 4), (5, 8), (9, 11))},
           "n_kept_new": int(keep.sum()), "n_dropped_new": int((new & ~keep).sum()), "max_rows": max_rows}
    (run / "organizer_check.json").write_text(json.dumps(chk, indent=1) + "\n")
    print(json.dumps({k: chk[k] for k in ("n_overlap_cols", "n_cols", "new_vertices_overlap_cols", "official_top_1mm_baseline_overlap_cols", "n_kept_new")}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 11)
