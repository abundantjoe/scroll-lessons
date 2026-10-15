import os, sys, json, tempfile, numpy as np, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import gown_result as G


def write_grid(d, pts_grid):
    os.makedirs(d, exist_ok=True)
    for i, n in enumerate("xyz"):
        tifffile.imwrite(os.path.join(d, n + ".tif"), pts_grid[..., i].astype(np.float32))
    json.dump({"scale": [0.05, 0.05]}, open(os.path.join(d, "meta.json"), "w"))
    return d


def flat_sheet(n=20, x0=0.0, spacing=20.0):
    u, v = np.meshgrid(np.arange(n) * spacing, np.arange(n) * spacing, indexing="ij")
    return np.stack([np.full_like(u, 100.0 + x0), u + 100.0, v + 100.0], axis=-1)


def maps(dirpath, fwd, rev, shape=(64, 64)):
    os.makedirs(dirpath, exist_ok=True)
    tifffile.imwrite(os.path.join(dirpath, "m.tif"), np.full(shape, int(round(fwd*255)), np.uint8))
    tifffile.imwrite(os.path.join(dirpath, "m_reverse.tif"), np.full(shape, int(round(rev*255)), np.uint8))
    return dirpath


def test_bars_are_the_declared_ones_and_are_not_computed():
    assert G.MIN_ON_SHEET_FRAC == 0.50
    assert abs(G.PASS_BAR - 0.0128) < 1e-12 and abs(G.COLLAPSE_BAR - 0.0042) < 1e-12
    assert abs(G.TEAM_MESH_MARGIN - 0.0255) < 1e-12 and G.WRAP_UM == 449.0


def test_a_trace_on_the_known_text_sheet_is_admissible():
    d = tempfile.mkdtemp()
    mesh = write_grid(os.path.join(d, "mesh"), flat_sheet())
    patch = write_grid(os.path.join(d, "patch"), flat_sheet(n=10, x0=1.0))   # 1 voxel off the sheet
    f, dist = G.on_sheet_fraction(G.grid_points(patch), G.grid_points(mesh))
    assert f == 1.0 and dist.max() < G.WRAP_UM


def test_a_trace_a_wrap_away_is_VOID_OFF_SHEET_not_a_result():
    d = tempfile.mkdtemp()
    mesh = write_grid(os.path.join(d, "mesh"), flat_sheet())
    patch = write_grid(os.path.join(d, "patch"), flat_sheet(n=10, x0=200.0))  # ~4 wraps away
    f, _ = G.on_sheet_fraction(G.grid_points(patch), G.grid_points(mesh))
    assert f == 0.0
    v, why = G.verdict(f, 0.05)                       # even a huge margin cannot rescue it
    assert v == "VOID-OFF-SHEET" and "re-seeded" in why


def test_the_three_margin_outcomes():
    assert G.verdict(0.9, 0.0300)[0] == "PASS"
    assert G.verdict(0.9, 0.0128)[0] == "PASS"        # the bar is inclusive
    assert G.verdict(0.9, 0.0042)[0] == "COLLAPSE"    # so is the collapse bar
    assert G.verdict(0.9, 0.0010)[0] == "COLLAPSE"
    assert G.verdict(0.9, 0.0080)[0] == "PARTIAL"


def test_an_admissible_trace_with_no_read_yet_is_PENDING():
    assert G.verdict(0.9, None)[0] == "PENDING"


def test_the_statistic_is_the_absolute_margin_so_orientation_cannot_decide_it():
    d = tempfile.mkdtemp()
    pos = G.whole_map_margin(maps(os.path.join(d, "p"), 0.40, 0.37))
    neg = G.whole_map_margin(maps(os.path.join(d, "n"), 0.37, 0.40))
    assert pos["margin"] > 0 > neg["margin"]
    assert G.verdict(0.9, abs(pos["margin"]))[0] == G.verdict(0.9, abs(neg["margin"]))[0] == "PASS"


def test_off_sheet_pixels_are_excluded_from_the_margin():
    d = tempfile.mkdtemp(); p = os.path.join(d, "p"); os.makedirs(p)
    f = np.zeros((64, 64), np.uint8); r = np.zeros((64, 64), np.uint8)
    f[:8, :8] = int(0.40*255); r[:8, :8] = int(0.35*255)     # only 1/64 of the canvas is on-sheet
    tifffile.imwrite(os.path.join(p, "m.tif"), f); tifffile.imwrite(os.path.join(p, "m_reverse.tif"), r)
    mm = G.whole_map_margin(p)
    assert mm["onsheet_px"] == 64
    assert abs(mm["margin"] - (int(0.40*255) - int(0.35*255)) / 255.0) < 1e-6


def test_a_read_dir_with_no_maps_returns_None_rather_than_a_number():
    assert G.whole_map_margin(tempfile.mkdtemp()) is None


def test_matched_region_selects_only_the_blocks_the_trace_actually_covers():
    d = tempfile.mkdtemp()
    mesh = write_grid(os.path.join(d, "mesh"), flat_sheet(n=20))          # 20x20 nodes, 20 vx apart
    patch = write_grid(os.path.join(d, "patch"), flat_sheet(n=3, x0=1.0))  # covers the 3x3 corner only
    rows, cols, step, n_near = G.matched_region(G.grid_points(patch), mesh)
    assert step == 20
    assert len(rows) == 9 and n_near == 9
    assert rows.max() <= 2 and cols.max() <= 2


def test_matched_region_ignores_trace_points_that_are_off_the_sheet():
    d = tempfile.mkdtemp()
    mesh = write_grid(os.path.join(d, "mesh"), flat_sheet(n=20))
    patch = write_grid(os.path.join(d, "patch"), flat_sheet(n=3, x0=500.0))  # far off the sheet
    rows, cols, step, n_near = G.matched_region(G.grid_points(patch), mesh)
    assert n_near == 0 and len(rows) == 0


def test_team_margin_on_region_uses_only_the_selected_blocks():
    d = tempfile.mkdtemp()
    f = np.zeros((60, 60), np.uint8); r = np.zeros((60, 60), np.uint8)
    f[:20, :20] = int(0.50 * 255); r[:20, :20] = int(0.40 * 255)   # block (0,0): margin ~ +0.10
    f[20:40, :20] = int(0.30 * 255); r[20:40, :20] = int(0.30 * 255)  # block (1,0): margin 0
    ft = os.path.join(d, "f.tif"); rt = os.path.join(d, "r.tif")
    tifffile.imwrite(ft, f); tifffile.imwrite(rt, r)
    only00 = G.team_margin_on_region(np.array([0]), np.array([0]), 20, ft, rt)
    both = G.team_margin_on_region(np.array([0, 1]), np.array([0, 0]), 20, ft, rt)
    assert abs(only00["margin"] - 0.1) < 0.005 and only00["px"] == 400
    assert abs(both["margin"] - 0.05) < 0.005 and both["px"] == 800


def test_the_matched_figure_cannot_change_the_declared_verdict():
    # whatever the matched control says, verdict() only ever sees on_frac and |margin|
    import inspect
    sig = inspect.signature(G.verdict)
    assert list(sig.parameters) == ["on_frac", "margin_abs"]
