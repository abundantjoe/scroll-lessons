# Provenance: Project HERCULES | owner the owner | [id removed]
"""Paris 4 tile checks (REAL-TRIB-2 iv) on synthetic manifests and arrays only."""

import copy

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from hercules.tribunal import tiles as TL

VOX = 0.0024


def _grid(ppm=415.0389822320533, median_edge=20.078435255688987, canvas=(71600, 174640)):
    T = int(round(20 * ppm))
    return {"px_per_mm": ppm, "T_px": T, "canvas_shape": list(canvas), "grid_shape": [canvas[0] // 20, canvas[1] // 20],
            "canvas_per_grid_scale_rows_cols": [20.0, 20.0], "voxel_mm": VOX,
            "tile_grid_rows_cols": [-(-canvas[0] // T), -(-canvas[1] // T)], "edge_len_vx_both": {"median": median_edge},
            "tile_mm": 20.0}


def _tile(n, r, c, vf=0.9):
    T, (H, W) = n["T"], n["canvas"]
    return {"r": r, "c": c, "file": f"tiles/x_r{r}_c{c}.png", "canvas_rows": [r * T, (r + 1) * T],
            "canvas_cols": [c * T, (c + 1) * T], "in_canvas_rows": [r * T, min((r + 1) * T, H)],
            "in_canvas_cols": [c * T, min((c + 1) * T, W)], "valid_px": int(round(vf * T * T)),
            "valid_fraction": int(round(vf * T * T)) / float(T * T), "png_chunks": ["IDAT", "IEND", "IHDR"]}


def test_grid_checks_pass_on_consistent_grid():
    n = TL.normalize_grid(_grid())
    assert all(x["passed"] for x in TL.check_grid(n, voxel_mm_metadata=VOX))


@pytest.mark.parametrize("fault,check", [("T", "T_rule"), ("ppm", "ppm_recomputed"), ("vox", "voxel_from_metadata"),
                                         ("dims", "tile_grid_dims")])
def test_grid_faults_caught(fault, check):
    n = TL.normalize_grid(_grid())
    if fault == "T":
        n["T"] += 1
    elif fault == "ppm":
        n["px_per_mm"] *= 1.02
        n["T"] = int(round(20 * n["px_per_mm"]))
    elif fault == "vox":
        n["voxel_mm"] = 0.002399
    else:
        n["tile_grid"] = [n["tile_grid"][0] + 1, n["tile_grid"][1]]
    failed = {x["check"] for x in TL.check_grid(n, voxel_mm_metadata=VOX) if not x["passed"]}
    assert check in failed


def test_tile_checks_and_faults():
    n = TL.normalize_grid(_grid())
    tiles = [_tile(n, 0, 0), _tile(n, 8, 21, 0.6)]
    assert all(not x["failed"] for x in TL.check_tiles(n, tiles))
    bad = copy.deepcopy(tiles)
    bad[0]["canvas_rows"] = [8, n["T"] + 8]
    bad[1]["valid_fraction"] += 0.01
    res = TL.check_tiles(n, bad)
    assert "origin_or_extent" in res[0]["failed"] and "valid_fraction_vs_valid_px" in res[1]["failed"]
    sw = copy.deepcopy(tiles)
    sw[1]["r"], sw[1]["c"] = 21, 8
    assert "rc_outside_tile_grid" in TL.check_tiles(n, sw)[1]["failed"]


def _canvas(rng, T):
    H, W = 2 * T + 300, 3 * T + 500
    tex = gaussian_filter(rng.standard_normal((H, W)), 6.0)
    canvas = np.clip((tex - tex.mean()) / tex.std() * 50 + 90, 0, 255).astype(np.uint8)
    valid = np.ones((H, W), bool)
    valid[:, : T // 3] = False
    return canvas, valid


def test_verify_tile_clean_and_faults():
    rng = np.random.default_rng(1)
    T, side = 800, 128
    canvas, valid = _canvas(rng, T)
    good = TL.expected_tile(canvas, valid, 1, 2, T, side)
    assert TL.verify_tile(good, canvas, valid, 1, 2, T, side=side)["passed"]
    assert not TL.verify_tile(np.rot90(good, -1).copy(), canvas, valid, 1, 2, T, side=side)["passed"]
    assert not TL.verify_tile(good[:, ::-1].copy(), canvas, valid, 1, 2, T, side=side)["passed"]
    off = TL.expected_tile(np.roll(canvas, -8, 1), np.roll(valid, -8, 1), 1, 2, T, side)
    assert not TL.verify_tile(off, canvas, valid, 1, 2, T, side=side)["passed"]
    wrongT = TL.expected_tile(canvas, valid, 1, 2, int(round(T * 1.02)), side)
    assert not TL.verify_tile(wrongT, canvas, valid, 1, 2, T, side=side)["passed"]
    # N0 null tiles are keyed rotated 90 deg clockwise
    n0 = TL.expected_tile(canvas, valid, 1, 2, T, side, rotation=90)
    assert TL.verify_tile(n0, canvas, valid, 1, 2, T, side=side, rotation=90)["passed"]
    assert not TL.verify_tile(good, canvas, valid, 1, 2, T, side=side, rotation=90)["passed"]
    np.testing.assert_array_equal(n0, np.rot90(good, -1))


def test_expected_tile_masks_and_pads():
    canvas = np.full((100, 100), 200, np.uint8)
    valid = np.zeros((100, 100), bool)
    valid[:50] = True
    t = TL.expected_tile(canvas, valid, 0, 0, 100, side=50)
    assert t[:25].min() == 200 and t[25:].max() == 0
    t2 = TL.expected_tile(canvas, np.ones((100, 100), bool), 0, 0, 200, side=100)  # beyond canvas -> 0
    assert t2[:50, :50].min() == 200 and t2[50:, :].max() == 0
