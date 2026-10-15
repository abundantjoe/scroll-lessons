# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-2 (A): distortion of the OFFICIAL flattening of two PHercParis4
segments (RULES.md DECL-P4-2 item 7 support). Geometry only: mesh
coordinates and metadata; no prediction, render or CT pixel is read.

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/p4_flat.py [seg ...]

What is measured
* The official flattened product is the organizer tifxyz
  ``<ts>-on-20260411134726-2.4um.tifxyz``: its regular grid IS the flat
  parameterisation (the prediction canvas is that grid x 20 px, see the
  p4-tiles builders' grid.json). The flat length of every grid edge is the
  nominal step 1/scale = 20 vox, so the FLAT-1 metric is % of valid quads
  whose four 3-D edges lie within +-5 % of 20 vox ("raw", the scale the
  canvas assumes: 1 px per voxel) and within +-5 % of 20 vox x s with one
  global s = sqrt(A3 / A2) per segment ("norm", FLAT-1 convention).
* Flips: a regular grid cannot flip in (u, v); the equivalent defect is a
  fold of the 3-D surface relative to the parameterisation: a triangle whose
  normal has a negative dot product with the area-weighted mean normal of
  the 9 x 9 quad neighbourhood. Reported as fold counts.
* Tiles: the DECL-P4-2 grid (tile (r, c) = canvas rows [r T, (r+1) T),
  cols [c T, (c+1) T) from (0, 0), T from the builders' grid.json). Quad
  (i, j) belongs to the tile containing canvas point 20 (i + 0.5),
  20 (j + 0.5). A tile's mesh-valid fraction is the valid-vertex fraction of
  its canvas block (nearest-neighbour rule of grid.json); tiles >= 50 % are
  "read-eligible".
* Our flattening: one 4.00 cm^2 rectangle per segment chosen by the FLAT-1
  rule (flatlib.choose_rectangle, rng [20260926, crc32(segment)]) on the
  official grid (no re-levelling: the official canvas orientation is the one
  tiles use), flattened by vc_flatten (official ABF++ via abf_uv_dump), SLIM
  and ARAP; plus the official flattening's own numbers on that rectangle.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
import zlib
from pathlib import Path

import numpy as np
from scipy import ndimage

import flat1_run as RUN
import flatlib as FL
from hercules.geometry import tifxyz as T
from hercules.pipeline.window import voxel_size_from_metadata

SCROLL = "PHercParis4"
VOL = "20260411134726"
VOL_ZARR_PREFIX = f"{SCROLL}/volumes/"
SEGS = {  # T_px from the p4 tile builders' grid.json (branches sib-p4-tiles-a / -b)
    "20260701183124-w010-027": 8343,
    "20260701183125-w028-037": 8301,
}
CANVAS_PER_GRID = 20
FOLD_WIN = 9
WORK = Path("/work/flat1/p4")
OUT = RUN.OUT / "p4_flat.json"
TOL = 0.05


def vol_voxel(c) -> tuple[float, str, str]:
    r = c.list_objects_v2(Bucket=RUN.BUCKET, Prefix=VOL_ZARR_PREFIX, Delimiter="/")
    zarr = [p["Prefix"] for p in r.get("CommonPrefixes", []) if p["Prefix"].split("/")[-2].startswith(VOL)]
    assert len(zarr) == 1, zarr
    key = zarr[0] + "metadata.json"
    p = WORK / "vol_metadata.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(c.get_object(Bucket=RUN.BUCKET, Key=key)["Body"].read())
    return voxel_size_from_metadata(p), RUN.sha256_file(p), key


def fetch(c, seg: str) -> tuple[Path, list]:
    ts = seg.split("-")[0]
    name = f"{ts}-on-{VOL}-2.4um.tifxyz"
    key = f"{SCROLL}/segments/{seg}/mesh/{name}/"
    d = WORK / seg / name
    d.mkdir(parents=True, exist_ok=True)
    dl = []
    for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
        p = d / f
        if not p.exists():
            for i in range(5):
                try:
                    c.download_file(RUN.BUCKET, key + f, str(p))
                    break
                except Exception:
                    time.sleep(2 ** i)
        dl.append({"key": key + f, "size": p.stat().st_size, "sha256": RUN.sha256_file(p)})
    return d, dl


def grid_stats(p: np.ndarray, T_px: int) -> dict:
    """Whole-segment and per-tile statistics of the official grid flattening."""
    H, W = p.shape[:2]
    v = FL.valid_mask(p)
    qv = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    Lh = np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)  # (H, W-1) float32
    Lv = np.linalg.norm(p[1:] - p[:-1], axis=-1)  # (H-1, W)
    step = 1.0 / 0.05
    # 3-D triangle areas and normals per quad (T1 = p10,p00,p01 ; T2 = p10,p01,p11)
    p00, p01, p10, p11 = p[:-1, :-1], p[:-1, 1:], p[1:, :-1], p[1:, 1:]
    n1 = np.cross(p00 - p10, p01 - p10)
    n2 = np.cross(p01 - p10, p11 - p10)
    a1 = 0.5 * np.linalg.norm(n1, axis=-1)
    a2 = 0.5 * np.linalg.norm(n2, axis=-1)
    A3 = float(np.where(qv, a1 + a2, 0).sum(dtype=np.float64))
    nq = int(qv.sum())
    s = math.sqrt(A3 / (nq * step * step))
    nq_sum = np.where(qv[..., None], n1 + n2, 0).astype(np.float32)
    mean_n = np.stack([ndimage.uniform_filter(nq_sum[..., k], FOLD_WIN, mode="constant") for k in range(3)], -1)
    fold1 = qv & ((n1 * mean_n).sum(-1) < 0)
    fold2 = qv & ((n2 * mean_n).sum(-1) < 0)
    degen = qv & ((a1 <= 1e-6) | (a2 <= 1e-6))
    del n1, n2, mean_n, nq_sum, p00, p01, p10, p11

    def ok_quads(ref: float) -> np.ndarray:
        okh = np.abs(Lh / ref - 1.0) <= TOL
        okv = np.abs(Lv / ref - 1.0) <= TOL
        return okh[:-1] & okh[1:] & okv[:, :-1] & okv[:, 1:] & qv

    ok_raw = ok_quads(step)
    ok_norm = ok_quads(step * s)
    eh = np.abs(Lh / step - 1.0)
    ev = np.abs(Lv / step - 1.0)
    # quad-level worst edge deviation (raw), for distribution
    worst = np.maximum.reduce([eh[:-1], eh[1:], ev[:, :-1], ev[:, 1:]])
    wq = worst[qv]
    whole = {
        "grid_shape": [H, W], "n_valid_vertices": int(v.sum()), "n_valid_quads": nq,
        "area_3d_cm2": A3 * (RUN.VOX_P4 * 1e-4) ** 2, "area_scale_factor_s": s,
        "pct_quads_within_5pct_raw": 100.0 * ok_raw.sum() / nq,
        "pct_quads_within_5pct_norm": 100.0 * ok_norm.sum() / nq,
        "pct_quads_within_1pct_raw": 100.0 * ok_quads_tol(Lh, Lv, qv, step, 0.01).sum() / nq,
        "pct_quads_within_10pct_raw": 100.0 * ok_quads_tol(Lh, Lv, qv, step, 0.10).sum() / nq,
        "quad_worst_edge_dev_raw_pctl": {str(k): float(np.percentile(wq, k)) for k in (50, 90, 95, 99, 99.9)},
        "fold_triangles": int(fold1.sum() + fold2.sum()), "degenerate_triangles": int(degen.sum()),
        "fold_rule": "normal . (9x9 area-weighted mean normal) < 0",
    }
    # tiles
    Tq = T_px / CANVAS_PER_GRID  # tile side in grid units
    qi = np.floor((np.arange(H - 1) + 0.5) / Tq).astype(np.int64)
    qj = np.floor((np.arange(W - 1) + 0.5) / Tq).astype(np.int64)
    nr = int(math.ceil(H * CANVAS_PER_GRID / T_px))
    nc = int(math.ceil(W * CANVAS_PER_GRID / T_px))
    tid = qi[:, None] * nc + qj[None, :]

    def per_tile(mask: np.ndarray) -> np.ndarray:
        return np.bincount(tid[mask], minlength=nr * nc)

    n_q = per_tile(qv)
    n_raw = per_tile(ok_raw)
    n_norm = per_tile(ok_norm)
    n_fold = per_tile(fold1) + per_tile(fold2)
    # vertex validity per tile (canvas px -> grid floor(i/20); vertex i covers canvas [20 i, 20 i + 20))
    # vertex blocks may straddle tile borders: count valid canvas px exactly per axis
    rows_px = _block_split(H, T_px, nr)  # (H, nr) px of vertex row i in tile row r
    cols_px = _block_split(W, T_px, nc)
    valid_px = rows_px.T @ v.astype(np.float64) @ cols_px  # (nr, nc)
    tiles = []
    for r in range(nr):
        for c in range(nc):
            k = r * nc + c
            frac = float(valid_px[r, c] / (T_px * T_px))
            tiles.append({"row": r, "col": c, "mesh_valid_fraction": frac, "read_eligible": frac >= 0.5,
                          "n_quads": int(n_q[k]),
                          "pct_within_5pct_raw": (100.0 * n_raw[k] / n_q[k]) if n_q[k] else None,
                          "pct_within_5pct_norm": (100.0 * n_norm[k] / n_q[k]) if n_q[k] else None,
                          "fold_triangles": int(n_fold[k])})
    el = [t for t in tiles if t["read_eligible"] and t["n_quads"]]
    whole["tiles_summary"] = {
        "T_px": T_px, "n_rows": nr, "n_cols": nc, "n_read_eligible": len(el),
        "n_read_eligible_ge_93p1_raw": int(sum(t["pct_within_5pct_raw"] >= 93.1 for t in el)),
        "n_read_eligible_ge_93p1_norm": int(sum(t["pct_within_5pct_norm"] >= 93.1 for t in el)),
        "read_eligible_raw_min_median_max": [float(np.min([t["pct_within_5pct_raw"] for t in el])),
                                             float(np.median([t["pct_within_5pct_raw"] for t in el])),
                                             float(np.max([t["pct_within_5pct_raw"] for t in el]))] if el else None,
        "n_read_eligible_with_folds": int(sum(t["fold_triangles"] > 0 for t in el)),
    }
    return {"whole": whole, "tiles": tiles, "ok_norm_mask": ok_norm, "qv": qv, "s": s, "fold": fold1 | fold2}


def ok_quads_tol(Lh, Lv, qv, ref, tol):
    okh = np.abs(Lh / ref - 1.0) <= tol
    okv = np.abs(Lv / ref - 1.0) <= tol
    return okh[:-1] & okh[1:] & okv[:, :-1] & okv[:, 1:] & qv


def _block_split(n: int, T_px: int, nt: int) -> np.ndarray:
    """(n, nt): canvas px of grid index i (canvas [20 i, 20 i + 20)) inside tile t."""
    out = np.zeros((n, nt))
    a = np.arange(n) * CANVAS_PER_GRID
    b = a + CANVAS_PER_GRID
    for t in range(nt):
        lo, hi = t * T_px, (t + 1) * T_px
        out[:, t] = np.clip(np.minimum(b, hi) - np.maximum(a, lo), 0, None)
    return out


def own_flattening(p: np.ndarray, seg: str, vox: float, stats: dict) -> dict:
    rng = np.random.default_rng([20260926, zlib.crc32(seg.encode())])
    rect = FL.choose_rectangle(p, vox, 20.0, rng, target_cm2=4.0)
    if rect is None:
        return {"rect": None}
    r0, c0, h, w = rect["r0"], rect["c0"], rect["h_quads"], rect["w_quads"]
    patch = p[r0:r0 + h + 1, c0:c0 + w + 1].astype(np.float64)
    qe = FL.quad_mask(patch)
    # official flattening on the same rectangle: grid with nominal step
    m = FL.grid_to_mesh(patch)
    uv_off = FL.uv_to_grid(m, FL.grid_init_uv(m, 20.0), patch.shape[:2])
    res = {"rect": rect, "rect_tile_rc": [int((r0 + h / 2) * CANVAS_PER_GRID // SEGS[seg]),
                                          int((c0 + w / 2) * CANVAS_PER_GRID // SEGS[seg])],
           "official_on_rect": FL.evaluate(patch, uv_off, qe),
           "geometry": RUN.geometry_diagnostics(patch)}
    meth = RUN.flatten_all(patch, "p4_" + seg, vox, qe, sensitivity=False)
    res["methods"] = {k: {"metrics": v["metrics"], "info": {kk: vv for kk, vv in v["info"].items() if kk != "energy_history"}}
                      for k, v in meth.items() if k != "grid_baseline"}
    ab = res["methods"]["vc_flatten"]["info"]
    if ab.get("exit_code", 0) != 0:
        raise RuntimeError(f"ABF++ did not run: {ab}")
    ms = ab.get("stdout_tail", "")
    i = ms.find("Scaling UVs by ")
    res["methods"]["vc_flatten"]["abf_rescale_factor"] = float(ms[i + 15:].split()[0]) if i >= 0 else None
    return res


def main() -> None:
    c = RUN.s3()
    vox, vsha, vkey = vol_voxel(c)
    RUN.VOX_P4 = vox
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    out.update({"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
                "viewing": "geometry only; no prediction, render or CT pixel read", "volume_metadata_key": vkey,
                "volume_metadata_sha256": vsha, "voxel_um": vox, "tol": TOL})
    out.setdefault("segments", {})
    todo = sys.argv[1:] or list(SEGS)
    for seg in todo:
        if seg in out["segments"] and "own_flattening" in out["segments"][seg]:
            continue
        t0 = time.time()
        d, dl = fetch(c, seg)
        mesh = T.read_tifxyz(d)
        assert abs(mesh.step_vox[0] - 20.0) < 1e-3
        p = mesh.points
        st = grid_stats(p, SEGS[seg])
        rec = {"mesh": dl, "grid_shape": list(p.shape[:2]), "whole_official": st["whole"], "tiles_official": st["tiles"],
               "seconds_grid": time.time() - t0}
        out["segments"][seg] = rec
        OUT.write_text(json.dumps(out, indent=1, default=float))
        print(seg, json.dumps({k: v for k, v in st["whole"].items() if k != "tiles_summary"}, default=float),
              json.dumps(st["whole"]["tiles_summary"]), flush=True)
        del st
        t0 = time.time()
        rec["own_flattening"] = own_flattening(p, seg, vox, None)
        rec["seconds_own"] = time.time() - t0
        OUT.write_text(json.dumps(out, indent=1, default=float))
        of = rec["own_flattening"]
        print(seg, "rect", of["rect"], "official", round(of["official_on_rect"]["pct_quads_within_5pct"], 3),
              {k: round(v["metrics"]["pct_quads_within_5pct"], 3) for k, v in of["methods"].items()}, flush=True)
        for f in d.glob("*.tif"):  # keep disk bounded
            f.unlink()


if __name__ == "__main__":
    main()
