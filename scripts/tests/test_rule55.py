"""Tests for scripts/rule55.py (MASTER_PROMPT_v4 5.5, RULES.md R-5.5). Run: python -m pytest scripts/tests/test_rule55.py -q
Synthetic 3000x3000 maps at 9.362 um (unit side 755 -> 3x3 full units; 1 cm^2 side 1068 -> 2x2):
  text  = unit rows 0-1, all 3 columns (6 units): forward ~ N(0.42, 0.05), reverse ~ N(0.28, 0.05)
  blank = unit row 2, columns 0-1 (2 units): 0.30 / 0.30
  hole  = unit row 2, column 2: CT 0 (off-sheet)
"""
import os, sys
import numpy as np, pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rule55 as r  # noqa: E402

UM, N = 9.362, 3000
SIDE = 755
TEXT_UNITS = {(i, j) for i in (0, 1) for j in (0, 1, 2)}
BLANK_UNITS = {(2, 0), (2, 1)}
HOLE_UNIT = (2, 2)


def to_u8(p):
    return np.clip(np.round(p * 255.0), 0, 255).astype(np.uint8)


def make_synthetic(seed=0, blank_only=False, row_pitch_mm=None):
    """(ct_mid uint8, forward uint8, reverse uint8). Optional horizontal rows at row_pitch_mm inside the text block."""
    rng = np.random.default_rng(seed)
    fwd = rng.normal(0.30, 0.02, (N, N)); rev = rng.normal(0.30, 0.02, (N, N))
    ct = rng.normal(120, 20, (N, N)).clip(1, 255)
    if not blank_only:
        t = slice(0, 2 * SIDE)
        fwd[t, :] = rng.normal(0.42, 0.05, (2 * SIDE, N)); rev[t, :] = rng.normal(0.28, 0.05, (2 * SIDE, N))
        if row_pitch_mm:
            yy = np.arange(2 * SIDE)[:, None] * UM / 1000.0
            fwd[t, :] += 0.15 * (np.sin(2 * np.pi * yy / row_pitch_mm) > 0.3)
        y0, x0 = HOLE_UNIT[0] * SIDE, HOLE_UNIT[1] * SIDE
        ct[y0:y0 + SIDE, x0:x0 + SIDE] = 0
    return ct.astype(np.uint8), to_u8(fwd), to_u8(rev)


@pytest.mark.parametrize("um,side", [(9.596, 737), (8.64, 818), (9.362, 755)])
def test_unit_side(um, side):
    # 8.64 -> 818: RULES.md arithmetic note (sqrt(0.5)*10000/8.64 = 818.41; the prose's 819 is a transcription slip)
    assert r.unit_side(um) == side
    assert r.unit_side(um, 1.0) == round(10000 / um)


def test_thresholds_are_the_frozen_ones():
    assert (r.FWD_MIN, r.MARGIN_MIN, r.VALID_ONSHEET_FRAC, r.MIN_CLUSTER, r.BLANK_MIN_VALID_CM2) == (0.36, 0.08, 0.90, 3, 1.5)


def test_text_flagged_blank_and_hole_not():
    ct, fwd, rev = make_synthetic()
    res, tables = r.evaluate(fwd, rev, ct > 0, UM)
    t = tables["0.5cm2"]
    assert t["flagged"].shape == (3, 3)
    flagged = {(int(i), int(j)) for i, j in zip(*np.nonzero(t["flagged"]))}
    assert flagged == TEXT_UNITS
    assert not t["valid"][HOLE_UNIT]
    for u in BLANK_UNITS:
        assert t["valid"][u] and not t["flagged"][u]
        assert abs(t["margin"][u]) < 0.02
    half = res["units"]["0.5cm2"]
    assert half["n_flagged"] == 6 and half["largest_cluster"] == 6 and half["cluster_sizes"] == [6]
    assert half["n_valid"] == 8 and abs(half["valid_area_cm2"] - 8 * 0.4996) < 0.01
    b = half["brightest_flagged"]
    assert (b["row"], b["col"]) in TEXT_UNITS and 0.38 < b["fwd_mean"] < 0.46 and b["margin"] > 0.08
    for d in half["flagged"]:
        assert set(d) >= {"row", "col", "fwd_mean", "rev_mean", "margin"}
    one = res["units"]["1cm2"]                       # 1 cm^2 grid: 2x2, top row (0-1068 px) is all text
    assert one["side_px"] == 1068 and one["grid_rows"] == one["grid_cols"] == 2
    assert {(d["row"], d["col"]) for d in one["flagged"]} == {(0, 0), (0, 1)}


def test_cluster_sizes_four_connected():
    ct, fwd, rev = make_synthetic()
    fwd = fwd.copy(); fwd[SIDE:2 * SIDE, SIDE:2 * SIDE] = 77            # unit (1,1) -> 0.30: breaks the block
    res = r.rule55(fwd, rev, ct > 0, UM)
    h = res["units"]["0.5cm2"]
    assert h["n_flagged"] == 5 and h["largest_cluster"] == 5           # (0,0)(0,1)(0,2)(1,0)(1,2) still one 4-path via row 0
    fwd[0:SIDE, SIDE:2 * SIDE] = 77                                     # unit (0,1) too: {(0,0),(1,0)} vs {(0,2),(1,2)}
    h = r.rule55(fwd, rev, ct > 0, UM)["units"]["0.5cm2"]
    assert h["cluster_sizes"] == [2, 2] and h["largest_cluster"] == 2
    assert r.rule55(fwd, rev, ct > 0, UM)["verdict"] == "NOT ESTABLISHED"


def test_blank_verdict_on_blank_only_map():
    ct, fwd, rev = make_synthetic(blank_only=True)
    res = r.rule55(fwd, rev, ct > 0, UM)
    assert res["verdict"] == "BLANK"
    assert res["units"]["0.5cm2"]["n_flagged"] == 0 and res["units"]["0.5cm2"]["valid_area_cm2"] >= 1.5
    assert res["candidate_rule_geometry"] is False


def test_blank_needs_1p5_cm2_valid():
    ct, fwd, rev = make_synthetic(blank_only=True)
    small = np.zeros_like(ct); small[:SIDE, :2 * SIDE] = ct[:SIDE, :2 * SIDE]          # 2 valid units = 1.0 cm^2
    assert r.rule55(fwd, rev, small > 0, UM)["verdict"] == "NOT ESTABLISHED"
    assert r.rule55(fwd, rev, np.zeros_like(ct) > 0, UM)["verdict"] == "UNREADABLE"


@pytest.mark.parametrize("um", [9.362, 8.64])
def test_blank_with_exactly_three_units_nominal_area(um):
    """3 valid units = 1.5 cm^2 nominally although 3 * round(side)^2 px is 1.4988 / 1.4985 cm^2: BLANK, 2 units not."""
    ct, fwd, rev = make_synthetic(blank_only=True)
    side = r.unit_side(um)
    three = np.zeros_like(ct); three[:side, :3 * side] = 1
    res = r.rule55(fwd, rev, three > 0, um)
    h = res["units"]["0.5cm2"]
    assert h["n_valid"] == 3 and h["valid_area_nominal_cm2"] == 1.5 and res["verdict"] == "BLANK"
    two = np.zeros_like(ct); two[:side, :2 * side] = 1
    assert r.rule55(fwd, rev, two > 0, um)["verdict"] == "NOT ESTABLISHED"


def test_row_pitch_is_report_only_and_cluster_gives_candidate():
    """>= 3 adjacent flagged units -> PROMISING CANDIDATE whatever the row check says; rows are reported extras."""
    ct, fwd, rev = make_synthetic(row_pitch_mm=3.0)
    res = r.rule55(fwd, rev, ct > 0, UM)
    assert res["rows"]["in_band"] and 2.5 < res["rows"]["pitch_mm"] < 3.5
    assert res["verdict"] == "PROMISING CANDIDATE" and res["candidate_rule_geometry"] is True
    ct, fwd, rev = make_synthetic(row_pitch_mm=1.0)
    res = r.rule55(fwd, rev, ct > 0, UM)
    assert not res["rows"]["in_band"] and res["verdict"] == "PROMISING CANDIDATE" and not res["candidate_rule_geometry"]
    ct, fwd, rev = make_synthetic(row_pitch_mm=6.0)                      # 6 mm baseline: still a candidate
    assert r.rule55(fwd, rev, ct > 0, UM)["verdict"] == "PROMISING CANDIDATE"
    for seed in range(4):                                                # no rows: verdict must not depend on noise
        ct, fwd, rev = make_synthetic(seed=seed)
        res = r.rule55(fwd, rev, ct > 0, UM)
        assert res["rows"] is not None and res["verdict"] == "PROMISING CANDIDATE"
        assert res["rows_check_gates_verdict"] is False
    ct, fwd, rev = make_synthetic()
    assert r.rule55(fwd, rev, ct > 0, UM, row_check=False)["verdict"] == "PROMISING CANDIDATE"


def test_row_pitch_pure_profile():
    y = np.arange(2000) * UM / 1000.0
    assert r.row_pitch(np.sin(2 * np.pi * y / 2.5), UM)["in_band"]
    assert not r.row_pitch(np.sin(2 * np.pi * y / 6.0), UM)["in_band"]
    assert r.row_pitch(np.ones(50), UM)["pitch_mm"] is None


def test_best_origin_is_mask_only_and_raises_valid_units():
    """A sheet band offset from (0, 0): the fixed grid finds few valid units, the mask-chosen origin finds more; the
    origin must not depend on the maps."""
    um = 9.362; side = r.unit_side(um, 0.5)                       # 755
    H = W = 4 * side
    on = np.zeros((H, W), bool); on[side // 2: side // 2 + 2 * side, side // 3: side // 3 + 3 * side] = True   # 2 x 3 units, offset
    t_fixed = r.unit_table(np.zeros((H, W), np.uint8), np.zeros((H, W), np.uint8), on, side)
    origin, n = r.best_origin(on, side)
    t_auto = r.unit_table(np.zeros((H, W), np.uint8), np.zeros((H, W), np.uint8), on, side, origin=origin)
    assert int(t_fixed["valid"].sum()) < 6 and n == 6 == int(t_auto["valid"].sum())
    rng = np.random.default_rng(0)
    f1 = (rng.random((H, W)) * 255).astype(np.uint8); f2 = (rng.random((H, W)) * 255).astype(np.uint8)
    assert r.best_origin(on, side) == r.best_origin(on, side)          # deterministic
    r1 = r.evaluate(f1, f1, on, um, row_check=False, unit_origin="auto")[0]
    r2 = r.evaluate(f2, f2, on, um, row_check=False, unit_origin="auto")[0]
    assert r1["grid_origins"] == r2["grid_origins"] == {"0.5cm2": list(origin), "1cm2": r1["grid_origins"]["1cm2"]}
    on0 = np.ones((H, W), bool)                                       # full mask: (0, 0) wins ties
    assert r.best_origin(on0, side)[0] == (0, 0)


def test_valid_units_table_is_recorded_without_changing_the_verdict():
    """Every valid unit's levels go on record, so a near-miss can be told from an isolated spike afterwards.
    The flagged list, the cluster rule and the verdict are untouched by it."""
    um = UM
    side = r.unit_side(um)
    fwd = np.zeros((side * 2, side * 2), np.float32)
    rev = np.zeros_like(fwd)
    onsheet = np.ones_like(fwd, bool)
    fwd[:side, :side] = 0.50; rev[:side, :side] = 0.30          # one unit over both bars
    fwd[:side, side:] = 0.50; rev[:side, side:] = 0.47          # level high, margin far below the bar
    res, _ = r.evaluate(to_u8(fwd), to_u8(rev), onsheet, um, row_check=False, unit_origin="fixed")
    u = res["units"]["0.5cm2"]
    assert u["n_flagged"] == 1 and u["largest_cluster"] == 1
    vu = u["valid_units"]
    assert len(vu) == u["n_valid"] == 4
    assert sum(1 for d in vu if d["flagged"]) == 1
    near = [d for d in vu if not d["flagged"] and d["fwd_mean"] > 0.4]
    assert near and all(0.0 <= d["margin"] < r.MARGIN_MIN for d in near)   # the near-miss is on record too
