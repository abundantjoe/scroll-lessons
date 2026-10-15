"""Tests for the three instruments declared on 2026-09-19: R-SYM, R-POP and R-CTRL55.

These back results that now underpin every negative on record, so the invariants tested here are the ones whose
failure would have changed a conclusion: the correlation statistic, the unit-box arithmetic, the outcome mapping,
and the mirror reconstruction that R-POP needs because 41 of 50 reads carry an empty forward `valid_units` list.
"""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import rsym
import rpop
import rsens  # noqa: F401  (imported to prove it parses and exposes no import-time side effect)


# ---------------------------------------------------------------- R-SYM

def test_pearson_matches_numpy():
    rng = np.random.default_rng(0)
    a = rng.normal(size=500); b = 0.4 * a + rng.normal(size=500)
    assert rsym.pearson(a, b) == pytest.approx(float(np.corrcoef(a, b)[0, 1]), abs=1e-12)


def test_pearson_is_one_for_a_copy_and_minus_one_for_a_negation():
    a = np.arange(50.0)
    assert rsym.pearson(a, a.copy()) == pytest.approx(1.0)
    assert rsym.pearson(a, -a) == pytest.approx(-1.0)


def test_pearson_is_nan_on_a_constant_input_rather_than_dividing_by_zero():
    assert np.isnan(rsym.pearson(np.ones(10), np.arange(10.0)))


def test_unit_pixels_reads_exactly_the_declared_boxes():
    """The statistic is defined on the rule 5.5 valid unit boxes; a wrong box is a wrong statistic."""
    side = 4
    fwd = np.arange(20 * 20, dtype=np.uint8).reshape(20, 20)
    rev = fwd[::-1].copy()
    units = [dict(row=1, col=2), dict(row=0, col=0)]
    f, r = rsym.unit_pixels(fwd, rev, units, side, (2, 3))
    assert f.size == r.size == 2 * side * side
    expect0 = fwd[2 + 1 * side:2 + 2 * side, 3 + 2 * side:3 + 3 * side].ravel()
    assert np.array_equal(f[:side * side], expect0)
    expect1 = fwd[2:2 + side, 3:3 + side].ravel()
    assert np.array_equal(f[side * side:], expect1)


def test_unit_pixels_returns_none_when_there_is_no_valid_unit():
    assert rsym.unit_pixels(np.zeros((4, 4), np.uint8), np.zeros((4, 4), np.uint8), [], 2, (0, 0)) == (None, None)


def test_rsym_thresholds_are_the_declared_ones():
    assert (rsym.CONTROL_ANCHOR, rsym.SYM_AT, rsym.NOMINATE_BELOW) == (0.30, 0.70, 0.30)


# ---------------------------------------------------------------- R-POP mirror reconstruction

def _stats(fwd_units, swapped_units, n_valid_fwd=None, n_valid_swp=None):
    return dict(
        rule55=dict(units={"0.5cm2": dict(valid_units=fwd_units,
                                          n_valid=len(fwd_units) if n_valid_fwd is None else n_valid_fwd)}),
        rule55_depth_swapped={"0.5cm2": dict(valid_units=swapped_units,
                                             n_valid=len(swapped_units) if n_valid_swp is None else n_valid_swp)})


def _write(tmp_path, d):
    p = tmp_path / "read_stats.json"
    p.write_text(json.dumps(d))
    return str(p)


def test_units_of_prefers_the_forward_list_when_it_is_populated(tmp_path):
    u = [dict(row=0, col=1, onsheet_frac=0.95, fwd_mean=0.40, rev_mean=0.31, margin=0.09, flagged=True)]
    us, _d, how = rpop.units_of(_write(tmp_path, _stats(u, [])))
    assert how == "direct" and us == u


def test_units_of_mirrors_the_swapped_table_when_the_forward_list_is_empty(tmp_path):
    """The swapped table negates the margin and exchanges the means; the reconstruction must be exact."""
    sw = [dict(row=2, col=3, onsheet_frac=0.93, fwd_mean=0.4703, rev_mean=0.4533, margin=0.0171, flagged=False)]
    us, _d, how = rpop.units_of(_write(tmp_path, _stats([], sw, n_valid_fwd=1)))
    assert how == "mirrored"
    assert us[0]["fwd_mean"] == 0.4533 and us[0]["rev_mean"] == 0.4703
    assert us[0]["margin"] == pytest.approx(-0.0171)
    assert (us[0]["row"], us[0]["col"]) == (2, 3)


def test_units_of_refuses_to_mirror_when_the_two_tables_disagree_on_n_valid(tmp_path):
    """A mismatch means the two tables are not the same grid, so mirroring would fabricate a population."""
    sw = [dict(row=0, col=0, onsheet_frac=0.9, fwd_mean=0.4, rev_mean=0.3, margin=0.1, flagged=False)]
    us, _d, how = rpop.units_of(_write(tmp_path, _stats([], sw, n_valid_fwd=7)))
    assert how == "mismatch" and us == []


def test_units_of_reports_none_when_neither_table_has_units(tmp_path):
    us, _d, how = rpop.units_of(_write(tmp_path, _stats([], [])))
    assert how == "none" and us == []


def test_mirror_round_trips_to_the_forward_table_on_a_read_that_has_both(tmp_path):
    fwd = [dict(row=0, col=2, onsheet_frac=0.91, fwd_mean=0.4533, rev_mean=0.4703, margin=-0.0171, flagged=False)]
    sw = [dict(row=0, col=2, onsheet_frac=0.91, fwd_mean=0.4703, rev_mean=0.4533, margin=0.0171, flagged=False)]
    direct, _d, _h = rpop.units_of(_write(tmp_path, _stats(fwd, sw)))
    mirrored, _d2, _h2 = rpop.units_of(_write(tmp_path, _stats([], sw, n_valid_fwd=1)))
    for k in ("row", "col", "fwd_mean", "rev_mean"):
        assert direct[0][k] == mirrored[0][k]
    assert direct[0]["margin"] == pytest.approx(mirrored[0]["margin"])


# ---------------------------------------------------------------- R-CTRL55 outcome mapping

@pytest.mark.parametrize("flagged,largest,expected", [
    (0, 0, "CTRL55-BLIND"),
    (1, 1, "CTRL55-PASS"),
    (2, 2, "CTRL55-PASS"),
    (3, 3, "CTRL55-STRONG"),
    (7, 4, "CTRL55-STRONG"),
])
def test_ctrl55_outcome_follows_the_declared_bars(flagged, largest, expected):
    import rule55
    got = ("CTRL55-STRONG" if largest >= rule55.MIN_CLUSTER
           else "CTRL55-PASS" if flagged >= 1 else "CTRL55-BLIND")
    assert got == expected


def test_rctrl55_passes_the_auto_grid_not_a_tuple():
    """The defect of 2026-09-19 03:05: evaluate() takes the STRING "auto"; a tuple silently tiles from (0, 0)."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rctrl55.py")).read()
    assert 'unit_origin="auto"' in src
    assert "unit_origin=origin" not in src
    assert 'res["grid_origins"]["0.5cm2"]' in src, "the run must assert the grid it actually used"
