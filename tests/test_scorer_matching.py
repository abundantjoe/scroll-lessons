# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for spec D: one-to-one same-kind Hungarian matching within radius R."""

import numpy as np
import pytest

from hercules.scorer.constants import R_PRIMARY, R_SECONDARY
from hercules.scorer.matching import match_letters, max_matching, max_matching_size

ALPHA, BETA, SIGMA = "\u0391", "\u0392", "\u03F9"


def seal(*letters):
    return [{"ch": ch, "x": float(x), "y": float(y), "firm": firm} for ch, x, y, firm in letters]


def named(*letters):
    return [{"ch": ch, "x": float(x), "y": float(y)} for ch, x, y in letters]


def test_radii_constants():
    assert R_PRIMARY == 250.0
    assert R_SECONDARY == 150.0


def test_exact_positions_match():
    s = seal((ALPHA, 0, 0, True), (BETA, 1000, 0, False))
    n = named((ALPHA, 0, 0), (BETA, 1000, 0))
    m = match_letters(n, s, R_PRIMARY)
    assert m["count"] == 2
    assert m["firm"] == 1
    assert m["pairs"] == [(0, 0), (1, 1)]


def test_shift_260_does_not_match_at_250():
    s = seal((ALPHA, 0, 0, True))
    assert match_letters(named((ALPHA, 260, 0)), s, R_PRIMARY)["count"] == 0
    assert match_letters(named((ALPHA, 0, 260)), s, R_PRIMARY)["count"] == 0


def test_shift_200_matches_at_250_not_150():
    s = seal((ALPHA, 0, 0, True))
    n = named((ALPHA, 120, 160))  # distance exactly 200
    assert match_letters(n, s, R_PRIMARY)["count"] == 1
    assert match_letters(n, s, R_SECONDARY)["count"] == 0


def test_radius_is_inclusive():
    s = seal((ALPHA, 0, 0, True))
    assert match_letters(named((ALPHA, 150, 200)), s, R_PRIMARY)["count"] == 1  # distance 250


def test_one_to_one_two_namings_one_seal_letter():
    s = seal((ALPHA, 0, 0, True))
    n = named((ALPHA, 5, 0), (ALPHA, -5, 0))
    m = match_letters(n, s, R_PRIMARY)
    assert m["count"] == 1
    assert len(m["pairs"]) == 1


def test_one_to_one_one_naming_two_seal_letters():
    s = seal((ALPHA, 0, 0, True), (ALPHA, 10, 0, True))
    assert match_letters(named((ALPHA, 5, 0)), s, R_PRIMARY)["count"] == 1


def test_wrong_kind_never_matches():
    s = seal((ALPHA, 0, 0, True))
    for ch in (BETA, SIGMA, "D", "?"):
        assert match_letters(named((ch, 0, 0)), s, R_PRIMARY)["count"] == 0


def test_normalisation_applied_to_namings():
    s = seal((SIGMA, 0, 0, True), (ALPHA, 1000, 0, False))
    n = named(("\u03A3", 0, 0), ("A", 1000, 0))  # capital sigma and Latin A
    assert match_letters(n, s, R_PRIMARY)["count"] == 2


def test_maximum_cardinality_beats_nearest_greedy():
    # Greedy-by-distance would pair n0-s0 (100 px) and leave n1 unmatched.
    s = seal((ALPHA, 0, 0, True), (ALPHA, 300, 0, False))
    n = named((ALPHA, 100, 0), (ALPHA, -200, 0))
    m = match_letters(n, s, R_PRIMARY)
    assert m["count"] == 2
    assert sorted(m["pairs"]) == [(0, 1), (1, 0)]


def test_min_distance_tie_break_among_maximum_matchings():
    s = seal((ALPHA, 0, 0, True), (ALPHA, 100, 0, False))
    n = named((ALPHA, 99, 0))
    m = match_letters(n, s, R_PRIMARY)
    assert m["pairs"] == [(0, 1)]
    assert m["firm"] == 0


def test_c_firm_counts_only_firm_seal_letters():
    s = seal((ALPHA, 0, 0, True), (BETA, 1000, 0, False), (SIGMA, 2000, 0, True))
    n = named((ALPHA, 0, 0), (BETA, 1000, 0))
    m = match_letters(n, s, R_PRIMARY)
    assert m["count"] == 2 and m["firm"] == 1


def test_empty_inputs():
    assert match_letters([], seal((ALPHA, 0, 0, True)), R_PRIMARY)["count"] == 0
    assert match_letters(named((ALPHA, 0, 0)), [], R_PRIMARY)["count"] == 0


def test_invalid_seal_letter_rejected():
    with pytest.raises(ValueError):
        match_letters(named((ALPHA, 0, 0)), [{"ch": "?", "x": 0.0, "y": 0.0, "firm": True}], R_PRIMARY)
    with pytest.raises(ValueError):
        match_letters(named((ALPHA, 0, 0)), [{"ch": ALPHA, "x": 0.0, "y": 0.0}], R_PRIMARY)


def test_max_matching_bruteforce_agreement():
    rng = np.random.default_rng(7)
    from itertools import permutations

    for _ in range(60):
        n, m = int(rng.integers(1, 5)), int(rng.integers(1, 5))
        allowed = rng.random((n, m)) < 0.45
        dist = rng.random((n, m)) * 250
        rows, cols = max_matching(allowed, dist)
        assert len(set(rows)) == len(rows) and len(set(cols)) == len(cols)
        assert all(allowed[r, c] for r, c in zip(rows, cols))
        best = 0
        big = max(n, m)
        for perm in permutations(range(big), min(n, m)):
            if n <= m:
                cnt = sum(allowed[i, perm[i]] for i in range(n))
            else:
                cnt = sum(allowed[perm[j], j] for j in range(m))
            best = max(best, cnt)
        assert len(rows) == best
        assert max_matching_size(allowed) == best
