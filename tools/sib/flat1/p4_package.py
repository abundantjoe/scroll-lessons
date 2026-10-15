# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-2 item 7 geometry path: crop the official Paris 4 tifxyz to a
candidate tile +- 1 cm, flatten with vc_flatten (FLAT-1), report quads within
+-5 % against the 93.1 % bar, write a verified flat package. Geometry only:
no prediction, render or CT pixel is read; no image is produced here.

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/p4_package.py \
        <tifxyz_dir> <T_px> <px_per_mm> <tile_row> <tile_col> <out_dir> [--voxel-um 2.4]

Crop rule (fixed): tile (r, c) = canvas rows [r T, (r+1) T), cols [c T, (c+1) T)
(DECL-P4-2 item 2, canvas = grid x 20). Margin m = 10 mm x px_per_mm canvas px.
Grid crop rows [floor((r T - m) / 20), ceil(((r+1) T + m) / 20)] clipped to the
grid, same for columns (inclusive vertex range). Metrics are reported over (a)
all valid quads of the crop and (b) the quads whose centre lies in the tile
itself ("tile" rows/cols, the part a reader saw). The bar (93.1 %) is applied to
(b) and (a) is reported alongside. SLIM is run as a secondary flattening.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

import flatlib as FL
import flatpkg as P
from hercules.geometry import tifxyz as T

CANVAS_PER_GRID = 20
MARGIN_MM = 10.0
BAR = 93.1


def crop_indices(T_px: int, px_per_mm: float, r: int, c: int, shape: tuple[int, int]) -> dict:
    m = MARGIN_MM * px_per_mm
    H, W = shape
    r0 = max(int(math.floor((r * T_px - m) / CANVAS_PER_GRID)), 0)
    r1 = min(int(math.ceil(((r + 1) * T_px + m) / CANVAS_PER_GRID)), H - 1)
    c0 = max(int(math.floor((c * T_px - m) / CANVAS_PER_GRID)), 0)
    c1 = min(int(math.ceil(((c + 1) * T_px + m) / CANVAS_PER_GRID)), W - 1)
    return {"r0": r0, "r1": r1, "c0": c0, "c1": c1, "margin_canvas_px": m}


def tile_quad_mask(crop: dict, T_px: int, r: int, c: int, qshape: tuple[int, int]) -> np.ndarray:
    ii = crop["r0"] + np.arange(qshape[0]) + 0.5
    jj = crop["c0"] + np.arange(qshape[1]) + 0.5
    inr = np.floor(ii * CANVAS_PER_GRID / T_px) == r
    inc = np.floor(jj * CANVAS_PER_GRID / T_px) == c
    return inr[:, None] & inc[None, :]


def largest_component(q: np.ndarray, seed: np.ndarray) -> np.ndarray:
    from scipy import ndimage

    lab, n = ndimage.label(q)
    if n == 0:
        return q
    ids, counts = np.unique(lab[q & seed] if (q & seed).any() else lab[q], return_counts=True)
    ids, counts = ids[ids > 0], counts[ids > 0]
    return lab == ids[np.argmax(counts)]


def package(mesh_dir: str | Path, T_px: int, px_per_mm: float, r: int, c: int, out: str | Path,
            voxel_um: float | None = None, methods=("vc_flatten", "slim")) -> dict:
    t0 = time.time()
    mesh = T.read_tifxyz(mesh_dir)
    step = mesh.step_vox[0]
    crop = crop_indices(T_px, px_per_mm, r, c, mesh.points.shape[:2])
    p = mesh.points[crop["r0"]:crop["r1"] + 1, crop["c0"]:crop["c1"] + 1].astype(np.float64)
    q_all = FL.quad_mask(p)
    q_tile = tile_quad_mask(crop, T_px, r, c, q_all.shape)
    q_keep = largest_component(q_all, q_tile)  # one connected sheet for the flattener
    p = np.where(_used(q_keep)[..., None], p, -1.0)
    out = Path(out)
    rec = {"mesh_dir": str(mesh_dir), "tile": [r, c], "T_px": T_px, "px_per_mm": px_per_mm, "crop": crop,
           "crop_shape": list(p.shape[:2]), "n_quads_crop": int(q_keep.sum()),
           "n_quads_tile": int((q_keep & q_tile).sum()), "n_quads_tile_dropped_not_connected": int((q_all & q_tile & ~q_keep).sum()),
           "voxel_um": voxel_um, "bar": BAR}
    if voxel_um:
        rec["crop_area_cm2"] = T.area_cm2(p.astype(np.float32), voxel_um)
    # the official flattening on the same crop (grid with nominal step)
    m = FL.grid_to_mesh(p)
    uv_off = FL.uv_to_grid(m, FL.grid_init_uv(m, step), p.shape[:2])
    rec["official"] = {"crop": P.metrics(p, uv_off, q_keep), "tile": P.metrics(p, uv_off, q_keep & q_tile)}
    rec["methods"] = {}
    for meth in methods:
        res = P.flatten(p, meth, workdir=out / f"work_{meth}" if str(out).startswith("/work/") else None,
                        voxel_um=voxel_um, step=step)
        mc, mt = P.metrics(p, res.uv, q_keep), P.metrics(p, res.uv, q_keep & q_tile)
        pk = P.write_package(out / f"package_{meth}", p, res.uv, method=meth, step=step, voxel_um=voxel_um,
                             quads=q_keep, info=res.info, source=f"{mesh_dir} tile {r},{c}")
        ok, vrep = P.verify_package(out / f"package_{meth}")
        rec["methods"][meth] = {"crop": mc, "tile": mt, "seconds": res.seconds, "collapse": P.collapse_flags(mc, res.info),
                                "abf_rescale_factor": res.info.get("abf_rescale_factor"),
                                "pct_tile_within_5pct": mt["pct_quads_within_5pct"],
                                "passes_bar_tile": mt["pct_quads_within_5pct"] >= BAR,
                                "package_verified": ok, "package_record_pct": pk["metrics"]["pct_quads_within_5pct"]}
    rec["seconds_total"] = time.time() - t0
    out.mkdir(parents=True, exist_ok=True)
    (out / "p4_package_record.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")
    return rec


def _used(q: np.ndarray) -> np.ndarray:
    u = np.zeros((q.shape[0] + 1, q.shape[1] + 1), bool)
    u[:-1, :-1] |= q
    u[1:, :-1] |= q
    u[:-1, 1:] |= q
    u[1:, 1:] |= q
    return u


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("mesh_dir")
    a.add_argument("T_px", type=int)
    a.add_argument("px_per_mm", type=float)
    a.add_argument("row", type=int)
    a.add_argument("col", type=int)
    a.add_argument("out")
    a.add_argument("--voxel-um", type=float, default=None)
    x = a.parse_args()
    rec = package(x.mesh_dir, x.T_px, x.px_per_mm, x.row, x.col, x.out, x.voxel_um)
    print(json.dumps({k: rec[k] for k in ("tile", "crop", "n_quads_crop", "n_quads_tile", "seconds_total")}, default=float))
    for k, v in rec["methods"].items():
        print(k, "tile %.3f crop %.3f bar %s collapse %s verified %s" % (v["tile"]["pct_quads_within_5pct"],
              v["crop"]["pct_quads_within_5pct"], v["passes_bar_tile"], v["collapse"]["collapsed"], v["package_verified"]))


if __name__ == "__main__":
    main()
