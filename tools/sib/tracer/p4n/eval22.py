# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-22 evaluation and delivery. Adoption rule: metrics22.py docstring (fixed before the trace).

  eval22.py <run_dir>

Hybrid H = official vertices outside the holes (fixed, bit-identical) + traced vertices INSIDE the holes only.
Official O = the official mesh on the same grid. Each metric is computed by the same code on H and O over P.
Seam baseline: the same quadratic-continuation residual evaluated on O's own vertices at the hole positions.
Writes logs/sib/tracer/p4-22/{metrics.json, patch_native.tifxyz, patch_native_flat_uv/, REPORT inputs}.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import tifffile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "ext")); sys.path.insert(0, str(HERE.parent))
import metrics as M  # noqa: E402
import metrics22 as M22  # noqa: E402
import prep  # noqa: E402
import prep22 as P22  # noqa: E402

W = P22.W
OUT = P22.OUTLOG


def main(run: Path):
    import surfmetrics as SM
    off_loc = M.read_grid(W / "official.tifxyz")
    res_loc = M.read_grid(W / "resume.tifxyz")
    holes = np.load(W / "holes.npy"); inP = np.load(W / "inP.npy")
    out_loc = M.read_grid(M.find_output(run))
    dy, dx, _ = M.locate_resume(out_loc, res_loc)
    Hh, Ww = res_loc.shape[:2]
    o = out_loc[dy:dy + Hh, dx:dx + Ww]
    ov = o[..., 0] != -1
    fixed = res_loc[..., 0] != -1
    unchanged = bool(np.all(ov[fixed]) and np.abs(o[fixed] - res_loc[fixed]).max() <= 1e-3)
    filled = holes & ov
    hyb_loc = np.where(fixed[..., None], res_loc, np.where(filled[..., None], o, -1.0))
    # write hybrid (L2) for selfcross
    hd = run / "hybrid_L2.tifxyz"
    if hd.exists():
        shutil.rmtree(hd)
    prep.write_tifxyz(hd, hyb_loc, "p422_hybrid_L2")

    def sx_in_P(tif: Path, js: Path, lab: str):
        rep = SM.selfcross(tif, js, P22.REPO / "logs/sib/tracer/runs.jsonl", lab)
        pairs = SM.crossing_pairs(rep)
        return sum(1 for qa, qb in pairs if inP[qa] or inP[qb]), len(pairs)
    sxH = sx_in_P(hd, run / "hybrid_selfcross.json", f"{P22.CFG}_hybrid_selfcross")
    sxO = sx_in_P(W / "official.tifxyz", W / "official_selfcross.json", f"{P22.CFG}_official_selfcross_eval")

    Hn = P22.to_native(hyb_loc.copy()); On = P22.to_native(off_loc.copy())
    seamH = M22.seam_general(Hn, filled, fixed)
    ovalid = On[..., 0] != -1
    seamO = M22.seam_general(On, holes & ovalid, fixed)
    _, _, rows, cols = P22.official_crop()
    tr, tc = M22.tile_ids(off_loc.shape[:2], rows, cols)
    if not (W / "clearance_official.npy").exists():
        np.save(W / "clearance_official.npy", M22.clearance_grid(On))
    clO = np.load(W / "clearance_official.npy")
    sp = M22.spacing_by_tile(clO, inP, tr, tc)
    rO = M22.ratio_from(clO, sp, tr, tc)
    clH = M22.clearance_grid(Hn)
    rH = M22.ratio_from(clH, sp, tr, tc)

    def nw(r, valid):
        x = r[inP & valid & np.isfinite(r)]
        return {"n": int(x.size), "frac_ge_0p6": float(np.mean(x >= 0.6)), "frac_lt_0p3": float(np.mean(x < 0.3)),
                "min": float(x.min()), "p1": float(np.percentile(x, 1))}
    nwH = nw(rH, hyb_loc[..., 0] != -1); nwO = nw(rO, ovalid)
    flH, uvH = M22.flat(Hn, inP); flO, _ = M22.flat(On, inP)

    seam_ok = M22.st(seamH)["median"] is not None and M22.st(seamH)["median"] <= M22.st(seamO)["median"]
    adopt = {"selfcross_zero": sxH[0] == 0,
             "seam_no_worse": bool(seam_ok),
             "neighbour_winding_no_worse": nwH["frac_ge_0p6"] >= nwO["frac_ge_0p6"],
             "flattening_no_worse": flH["pct_quads_within_5pct"] >= flO["pct_quads_within_5pct"]
                                    and flH["angle_err_mean_deg"] <= flO["angle_err_mean_deg"]}
    adopt["ADOPT"] = all(adopt.values())
    offsheet = None
    if P22.CFG == "p424":       # DECL-P4-24 item 2: off-sheet fraction of the re-traced vertices, same profile test
        Nh = M.normals(Hn)
        prom = P22.offsheet_flags(Hn, filled, Nh, checkpoint="retrace")
        t = filled & np.isfinite(prom)
        offsheet = {"n_tested": int(t.sum()), "offsheet_frac_retraced": float(np.mean(prom[t] < P22.P_MIN)) if t.any() else None,
                    "offsheet_frac_official_in_P": json.loads((OUT / "holes.json").read_text())["offsheet_frac_in_P"],
                    "normals_note": "re-traced vertices: central-difference normals of the hybrid SUB-4 grid"}
    m = {"run": str(run), "official_fixed_vertices_unchanged": unchanged,
         "n_P_valid_official": int((inP & ovalid).sum()), "n_hole_vertices": int(holes.sum()),
         "n_hole_filled": int(filled.sum()), "hole_fill_frac": float(filled.sum() / max(holes.sum(), 1)),
         "selfcross_pairs_touching_P": {"retrace": sxH[0], "official": sxO[0]},
         "selfcross_pairs_total_crop": {"retrace": sxH[1], "official": sxO[1]},
         "seam_normal_residual_vox": {"retrace_hole_borders": M22.st(seamH), "official_same_positions": M22.st(seamO)},
         "neighbour_winding": {"excl_grid": M22.EXCL, "retrace": nwH, "official": nwO,
                               "spacing_by_tile_vox": {f"r{a}_c{b}": v for (a, b), v in sp.items()}},
         "flattening_SLIM_on_P": {"retrace": flH, "official": flO},
         "offsheet": offsheet, "adoption": adopt}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps(m, indent=1, default=float) + "\n")
    # deliverables: P only, native frame; flattening uv of the hybrid
    rr = np.flatnonzero(inP.any(1)); cc = np.flatnonzero(inP.any(0))
    sl = (slice(rr.min(), rr.max() + 1), slice(cc.min(), cc.max() + 1))
    for name, g in (("patch_native.tifxyz", np.where(inP[..., None], Hn, -1.0)[sl]),):
        d = OUT / name
        if d.exists():
            shutil.rmtree(d)
        prep.write_tifxyz(d, g, "p422_patch_native")
        mm = json.loads((d / "meta.json").read_text()); mm["scale"] = [1 / 80, 1 / 80]
        mm["hrc_frame"] = "native 2.4 um voxels of 20260411134726; official grid rows/cols = every 4th"
        mm["hrc_official_row0_col0"] = [int(rows[rr.min()]), int(cols[cc.min()])]
        (d / "meta.json").write_text(json.dumps(mm, indent=1) + "\n")
        np.save(d / "retraced_mask.npy", filled[sl])
    fd = OUT / "patch_native_flat_uv"
    fd.mkdir(exist_ok=True)
    for i, a in enumerate("uv"):
        tifffile.imwrite(fd / f"{a}.tif", np.nan_to_num(uvH[sl][..., i], nan=-1).astype(np.float32),
                         metadata=None, software=False)
    print(json.dumps(m["adoption"]), json.dumps({k: m[k] for k in ("hole_fill_frac", "selfcross_pairs_touching_P")}))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
