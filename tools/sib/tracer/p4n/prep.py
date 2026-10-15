# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-N (RULES.md DECL-P4-13): seed patches for resuming the gated tracer from the official
20260701183124-w010-027 2.4 um mesh, in the LOCAL m7-L2 frame of fetch_m7l2.py. Geometry only.

Frames:
  native  = 2.4 um voxels of volume 20260411134726 (official mesh coordinates, x,y,z)
  L2 loc  = native / 4 - ORIGIN_xyz, ORIGIN_xyz = (3648, 4800, 15552)   (fetch_m7l2.ORIGIN is zyx)
Grid: every SUB-th official row/col (SUB = 4): official step 20 native vox -> 20 L2 vox, so the
patch has tifxyz scale 0.05 in the L2 frame and matches the tracer step 20.

Modes:
  real     official rows from the top edge down to KEEP_MM below it, cols c9-c15 +- MARGIN_COLS.
  holdout  the same crop with the top HOLD_MM removed (rows whose z > top-edge z - HOLD_MM per column
           are dropped); the removed official vertices are the ground truth of the recovery test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import tifffile

MESH = Path("/work/s3/PHercParis4/segments/20260701183124-w010-027/mesh/"
            "20260701183124-on-20260411134726-2.4um.tifxyz")
ORIGIN_XYZ = np.array([3648.0, 4800.0, 15552.0])
L2 = 4.0
SUB = 4
T_GRID = 8343 / 20.0          # tile width in official grid steps (p4-tiles-a grid.json)
C_LO, C_HI = 9, 15            # window columns (inclusive)
MARGIN_COLS = 104             # official grid cols (about 5 mm) each side
KEEP_MM = 6.0
HOLD_MM = 5.0
VOX_MM = 0.0024


def load_official():
    return np.stack([tifffile.imread(MESH / f"{a}.tif") for a in "xyz"], axis=-1).astype(np.float64)


def col_range():
    a = int(round(C_LO * T_GRID)) - MARGIN_COLS
    b = int(round((C_HI + 1) * T_GRID)) + MARGIN_COLS
    return a, b


def to_local(p):
    out = p / L2 - ORIGIN_XYZ
    out[p[..., 0] == -1] = -1
    return out


def to_native(p):
    out = (p + ORIGIN_XYZ) * L2
    out[p[..., 0] == -1] = -1
    return out


def write_tifxyz(d: Path, pts: np.ndarray, uuid: str, gens: np.ndarray | None = None):
    d.mkdir(parents=True, exist_ok=True)
    for i, a in enumerate("xyz"):
        tifffile.imwrite(d / f"{a}.tif", pts[..., i].astype(np.float32), metadata=None, software=False)
    v = pts[..., 0] != -1
    if gens is None:
        gens = v.astype(np.uint16)
    tifffile.imwrite(d / "generations.tif", gens.astype(np.uint16), metadata=None, software=False)
    q = pts[v]
    (d / "meta.json").write_text(json.dumps({"format": "tifxyz", "type": "seg", "uuid": uuid,
        "scale": [1.0 / 20, 1.0 / 20], "bbox": [q.min(0).tolist(), q.max(0).tolist()]}, indent=1) + "\n")


def build(mode: str, out: Path) -> dict:
    P = load_official()
    a, b = col_range()
    top = np.argmax(P[:, a:b, 0] != -1, axis=0)                 # first valid row per col
    rows_keep = int(np.ceil(KEEP_MM / (20 * VOX_MM)))           # official rows kept below the edge
    r1 = int(top.max()) + rows_keep
    crop = P[: r1, a:b].copy()
    info = {"mode": mode, "official_cols": [a, b], "official_rows": [0, r1], "sub": SUB,
            "top_row_pct": np.percentile(top, [0, 50, 100]).tolist()}
    if mode == "holdout":
        zt = crop[top, np.arange(b - a), 2]                       # top-edge z per column (native)
        cut = zt - HOLD_MM / VOX_MM
        drop = crop[..., 2] > cut[None, :]
        truth = np.where(drop[..., None], crop, -1.0)
        crop[drop] = -1
        np.save(out.parent / f"{out.name}_truth_native.npy", truth.astype(np.float32))
        info["hold_mm"] = HOLD_MM
        info["n_truth"] = int((truth[..., 0] != -1).sum())
    sub = crop[::SUB, ::SUB]
    np.save(out.parent / f"{out.name}_official_native_sub.npy", sub.astype(np.float32))
    loc = to_local(sub)
    write_tifxyz(out, loc, f"p4n_{mode}")
    info["patch_shape"] = list(loc.shape[:2])
    info["n_valid"] = int((loc[..., 0] != -1).sum())
    v = loc[..., 0] != -1
    info["local_bbox"] = [loc[v].min(0).tolist(), loc[v].max(0).tolist()]
    (out.parent / f"{out.name}_prep.json").write_text(json.dumps(info, indent=1) + "\n")
    return info


if __name__ == "__main__":
    mode = sys.argv[1]
    print(json.dumps(build(mode, Path(sys.argv[2])), indent=1))
