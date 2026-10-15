"""Tests for scripts/release_stats.py: the arithmetic must reproduce every statistic RULES.md printed by hand."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import release_stats as R  # noqa: E402


def test_every_recorded_value_is_reproduced():
    assert R.main([]) == 0


def test_clopper_pearson_known_values():
    lo, hi = R.clopper_pearson(0, 190)
    assert lo == 0.0 and math.isclose(hi, 1 - 0.025 ** (1 / 190), rel_tol=1e-9)   # exact form at k = 0
    lo, hi = R.clopper_pearson(5, 5)
    assert hi == 1.0 and math.isclose(lo, 0.025 ** (1 / 5), rel_tol=1e-9)


def test_intervals_are_never_narrowed_by_rounding():
    for k, n in ((7, 71), (1, 113), (2, 40), (60, 118)):
        cp, iv = R.clopper_pearson(k, n), R.interval(k, n)["cp95"]
        assert iv[0] <= cp[0] and iv[1] >= cp[1]


def test_collapsing_clusters_weakens_the_unit_level_evidence():
    assert R.fisher(1, 113, R.CONTROL_EVENTS, 71) > R.fisher(1, 113)
