# Provenance: Project HERCULES | owner the owner | [id removed]
"""Paris 4 P4-B tile checks (DECL-P4-2 item 2; REAL-TRIB-2 iv).

Manifest checks (numbers only) on the tile builders' grid.json / manifest.json / tiles.jsonl:
T == round(20 mm x px_per_mm); px_per_mm recomputed from the recorded median edge length; the
mesh-derived px_per_mm within 3 % of 1 / voxel_mm; canvas == grid x 20; tile grid dims ==
ceil(canvas / T); every tile's canvas range == [r T, (r+1) T) from origin (0, 0); in-canvas range ==
clip; valid_fraction == valid_px / T^2 (edge tiles zero-padded, T^2 denominator); read-eligible iff
>= 0.5; counts; PNG chunks IHDR/IDAT/IEND; display 1068 px (53.4 px/mm).

Pixel check (``verify_tile``), for pipelines that hold the source canvas: the expected display tile
is recomputed bit-exactly with the display builder's own functions (mask to mesh-valid, zero-pad,
cv2.INTER_AREA via ``area_downscale``, then the keyed rotation) and compared with the delivered tile.
On a mismatch ``diagnose`` names the most likely fault (dihedral transform, shift, or scale).
Exercised on synthetic arrays only: no real tile is opened by this module's tests.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from hercules.display.builder import area_downscale

TILE_MM = 20.0
DISPLAY_SIDE = 1068
READ_MIN_VALID = 0.5
PPM_REL_BOUND = 0.03
PIX_MAX_ABS = 1        # tolerated per-pixel difference (grey levels) for a PASS
PIX_MEAN_ABS = 0.05    # tolerated mean absolute difference
ALLOWED_CHUNKS = {"IHDR", "IDAT", "IEND"}


# ----------------------------------------------------------------------------- manifest checks

def normalize_grid(g: Mapping[str, Any]) -> dict:
    """Common view of the two builders' grid.json schemas (field names differ)."""
    ppm = float(g["px_per_mm"])
    T = int(g.get("T_canvas_px", g.get("T_px")))
    scale = g.get("scale_canvas_per_grid", g.get("canvas_per_grid_scale_rows_cols"))
    if isinstance(scale, Mapping):
        scale = [scale["rows"], scale["cols"]]
    tg = g.get("tile_grid", g.get("tile_grid_rows_cols"))
    if isinstance(tg, Mapping):
        tg = [tg["n_rows"], tg["n_cols"]]
    edge = g.get("edge_length_vox", g.get("edge_len_vx_both")) or {}
    return {"px_per_mm": ppm, "T": T, "canvas": list(g["canvas_shape"]), "grid": list(g["grid_shape"]),
            "scale": [float(scale[0]), float(scale[1])], "voxel_mm": float(g.get("voxel_size_mm", g.get("voxel_mm"))),
            "tile_grid": [int(tg[0]), int(tg[1])], "median_edge_vox": edge.get("median"),
            "tile_mm": float(g.get("tile_mm", TILE_MM)), "valid_matrix": g.get("tile_valid_fraction_matrix"),
            "tiles_total": g.get("tiles_total"), "tiles_read_eligible": g.get("tiles_read_eligible")}


def check_grid(n: Mapping[str, Any], *, voxel_mm_metadata: float) -> list[dict]:
    out = []

    def rec(name, ok, **det):
        out.append({"check": name, "passed": bool(ok), **det})

    rec("T_rule", n["T"] == int(round(TILE_MM * n["px_per_mm"])), T=n["T"], expected=int(round(TILE_MM * n["px_per_mm"])))
    if n["median_edge_vox"] is not None:
        re = n["scale"][0] / (float(n["median_edge_vox"]) * n["voxel_mm"])
        rec("ppm_recomputed", abs(re - n["px_per_mm"]) <= 1e-9 * re, recorded=n["px_per_mm"], recomputed=re)
    else:
        rec("ppm_recomputed", False, reason="no median edge length recorded")
    nominal = 1.0 / n["voxel_mm"]
    rec("ppm_vs_nominal", abs(n["px_per_mm"] / nominal - 1) <= PPM_REL_BOUND, ratio=n["px_per_mm"] / nominal)
    rec("voxel_from_metadata", abs(n["voxel_mm"] - voxel_mm_metadata) <= 1e-12, recorded=n["voxel_mm"],
        metadata=voxel_mm_metadata)
    rec("canvas_eq_grid_x_scale", n["canvas"] == [n["grid"][0] * n["scale"][0], n["grid"][1] * n["scale"][1]]
        and n["scale"] == [20.0, 20.0], canvas=n["canvas"], grid=n["grid"], scale=n["scale"])
    dims = [math.ceil(n["canvas"][0] / n["T"]), math.ceil(n["canvas"][1] / n["T"])]
    rec("tile_grid_dims", n["tile_grid"] == dims, recorded=n["tile_grid"], expected=dims)
    rec("display_px_per_mm", abs(DISPLAY_SIDE / TILE_MM - 53.4) < 1e-12, value=DISPLAY_SIDE / TILE_MM)
    return out


def check_tiles(n: Mapping[str, Any], tiles: Sequence[Mapping[str, Any]]) -> list[dict]:
    """Per-tile checks; returns one record per tile with the list of failing conditions."""
    T, (Hc, Wc) = n["T"], n["canvas"]
    res = []
    for t in tiles:
        r, c = int(t["r"]), int(t["c"])
        bad = []
        if not (0 <= r < n["tile_grid"][0] and 0 <= c < n["tile_grid"][1]):
            res.append({"r": r, "c": c, "failed": ["rc_outside_tile_grid", "origin_or_extent"]})
            continue
        if list(t["canvas_rows"]) != [r * T, (r + 1) * T] or list(t["canvas_cols"]) != [c * T, (c + 1) * T]:
            bad.append("origin_or_extent")
        if list(t["in_canvas_rows"]) != [r * T, min((r + 1) * T, Hc)] or \
                list(t["in_canvas_cols"]) != [c * T, min((c + 1) * T, Wc)]:
            bad.append("in_canvas_clip")
        vf = t["valid_px"] / float(T * T)
        if abs(vf - t["valid_fraction"]) > 1e-12:
            bad.append("valid_fraction_vs_valid_px")
        if "valid_fraction_check" in t and abs(t["valid_fraction_check"] - t["valid_fraction"]) > 1e-12:
            bad.append("valid_fraction_check")
        if n.get("valid_matrix") is not None and abs(round(t["valid_fraction"], 6) - n["valid_matrix"][r][c]) > 1e-9:
            bad.append("valid_fraction_vs_grid_matrix")
        if t["valid_fraction"] < READ_MIN_VALID:
            bad.append("listed_but_not_read_eligible")
        if set(t.get("png_chunks", [])) != ALLOWED_CHUNKS:
            bad.append("png_chunks")
        if "file" in t and not str(t["file"]).endswith(f"_r{r}_c{c}.png"):
            bad.append("file_name_rc")
        res.append({"r": r, "c": c, "failed": bad})
    return res


def check_counts(n: Mapping[str, Any], tiles: Sequence[Mapping[str, Any]]) -> list[dict]:
    out = []
    if n.get("valid_matrix") is not None:
        vm = np.asarray(n["valid_matrix"], float)
        out.append({"check": "valid_matrix_shape", "passed": list(vm.shape) == n["tile_grid"], "shape": list(vm.shape)})
        # the matrix is rounded to 6 decimals, so tiles within 1e-6 of the bar are reported, not decided
        elig = int((vm >= READ_MIN_VALID).sum())
        out.append({"check": "eligible_count_vs_matrix", "passed": elig == len(tiles) == n.get("tiles_read_eligible", elig),
                    "matrix_eligible": elig, "listed": len(tiles), "recorded": n.get("tiles_read_eligible"),
                    "near_bar": int((np.abs(vm - READ_MIN_VALID) < 1e-6).sum())})
        out.append({"check": "tiles_total", "passed": n.get("tiles_total", vm.size) == vm.size, "total": int(vm.size)})
    return out


# ----------------------------------------------------------------------------- pixel checks

def expected_tile(canvas: np.ndarray, valid: np.ndarray, r: int, c: int, T: int, side: int = DISPLAY_SIDE,
                  rotation: int = 0) -> np.ndarray:
    """The display tile the P4-B rule prescribes: canvas rows/cols [rT, (r+1)T) from (0, 0), 0 outside
    mesh-valid and beyond the canvas, INTER_AREA to side x side, then rotated ``rotation`` degrees
    clockwise (90 for N0 null tiles)."""
    src = np.zeros((T, T), dtype=np.uint8)
    H, W = canvas.shape
    y1, x1 = min((r + 1) * T, H), min((c + 1) * T, W)
    blk = np.where(valid[r * T:y1, c * T:x1], canvas[r * T:y1, c * T:x1], 0)
    src[:blk.shape[0], :blk.shape[1]] = blk
    out = area_downscale(src, side / T)
    if out.shape != (side, side):
        out = cv2.resize(src, (side, side), interpolation=cv2.INTER_AREA)
    k = {0: 0, 90: -1, 180: 2, 270: 1}[int(rotation) % 360]
    return np.ascontiguousarray(np.rot90(out, k))


def verify_tile(tile: np.ndarray, canvas: np.ndarray, valid: np.ndarray, r: int, c: int, T: int, *,
                side: int = DISPLAY_SIDE, rotation: int = 0) -> dict:
    """PASS iff the delivered tile equals the prescribed one (max |diff| <= 1, mean <= 0.05)."""
    exp = expected_tile(canvas, valid, r, c, T, side, rotation)
    if tile.shape != exp.shape:
        return {"passed": False, "reason": "shape", "shape": list(tile.shape), "expected": list(exp.shape)}
    d = np.abs(tile.astype(np.int16) - exp.astype(np.int16))
    ok = int(d.max()) <= PIX_MAX_ABS and float(d.mean()) <= PIX_MEAN_ABS
    res = {"passed": ok, "max_abs": int(d.max()), "mean_abs": float(d.mean())}
    if not ok:
        res["diagnosis"] = diagnose(tile, canvas, valid, r, c, T, side, rotation)
    return res


def _ncc(a, b):
    a = a.astype(np.float64).ravel() - a.mean()
    b = b.astype(np.float64).ravel() - b.mean()
    den = math.sqrt(float(a @ a) * float(b @ b))
    return float(a @ b) / den if den > 0 else math.nan


def diagnose(tile, canvas, valid, r, c, T, side=DISPLAY_SIDE, rotation=0, max_shift_canvas=16) -> dict:
    """Most likely fault: best of rotations/mirrors (at the keyed origin), canvas-px origin shifts, and
    tile-size (px_per_mm) errors of up to 6 %."""
    exp = expected_tile(canvas, valid, r, c, T, side, rotation)
    cands = {}
    for k in (1, 2, 3):
        cands[f"rot{90 * k}cw_extra"] = _ncc(tile, np.rot90(exp, -k))
    cands["mirror_lr"] = _ncc(tile, exp[:, ::-1])
    cands["mirror_ud"] = _ncc(tile, exp[::-1, :])
    for dy in range(-max_shift_canvas, max_shift_canvas + 1, 4):
        for dx in range(-max_shift_canvas, max_shift_canvas + 1, 4):
            if dy == dx == 0:
                continue
            sub = np.roll(np.roll(canvas, -dy, 0), -dx, 1)
            vsub = np.roll(np.roll(valid, -dy, 0), -dx, 1)
            cands[f"shift_{dy}_{dx}"] = _ncc(tile, expected_tile(sub, vsub, r, c, T, side, rotation))
    for f in (0.94, 0.96, 0.98, 0.99, 1.01, 1.02, 1.04, 1.06):
        T2 = int(round(T * f))
        cands[f"T_x{f}"] = _ncc(tile, expected_tile(canvas, valid, r, c, T2, side, rotation))
    fin = {k: v for k, v in cands.items() if math.isfinite(v)}
    best = max(fin, key=fin.get) if fin else None
    return {"best": best, "best_ncc": fin.get(best), "keyed_ncc": _ncc(tile, exp)}
