# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for spec E: identity-permutation null, arm statistics, p-values, max-T."""

from fractions import Fraction

import numpy as np
import pytest

from hercules.scorer.constants import N_PERM_DEFAULT, R_PRIMARY, SEED_DEFAULT
from hercules.scorer.letters import CANONICAL_KINDS, KIND_INDEX
from hercules.scorer.matching import match_letters
from hercules.scorer.null import (
    arm_summed_mean_cnet,
    max_t_p,
    null_match_counts,
    permutation_p,
    window_permutations,
)
from hercules.scorer.synthetic import draw_kinds, synthetic_seal

UNIT_N_PERM = 500  # small permutation count for unit tests (production default is 5000)


def test_production_defaults():
    assert N_PERM_DEFAULT == 5000
    assert isinstance(SEED_DEFAULT, int)


def test_window_permutations_are_permutations_and_deterministic():
    p1 = window_permutations(30, 200, 11, "w-A")
    p2 = window_permutations(30, 200, 11, "w-A")
    assert p1.shape == (200, 30)
    assert np.array_equal(p1, p2)
    assert all(np.array_equal(np.sort(row), np.arange(30)) for row in p1)
    # Not all identity.
    assert (p1 != np.arange(30)).any()


def test_window_permutations_depend_on_window_and_seed_only():
    a = window_permutations(30, 50, 11, "w-A")
    b = window_permutations(30, 50, 11, "w-B")
    c = window_permutations(30, 50, 12, "w-A")
    assert not np.array_equal(a, b)
    assert not np.array_equal(a, c)
    # Prefix property: the first 50 of 100 perms equal the 50-perm draw.
    d = window_permutations(30, 100, 11, "w-A")
    assert np.array_equal(d[:50], a)


def test_window_permutations_empty_seal():
    p = window_permutations(0, 10, 1, "w")
    assert p.shape == (10, 0)


def test_permutation_p_formula():
    null = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert permutation_p(7, null) == Fraction(1 + 3, 11)
    assert permutation_p(100, null) == Fraction(1, 11)
    assert permutation_p(-1, null) == Fraction(11, 11)
    assert permutation_p(5, np.array([5, 5, 5])) == 1


def _seal_arrays(seal):
    xy = np.array([[l["x"], l["y"]] for l in seal["letters"]], dtype=float)
    kinds = np.array([KIND_INDEX[l["ch"]] for l in seal["letters"]], dtype=np.int64)
    return xy, kinds


def test_null_counts_identity_permutation_equals_observed():
    rng = np.random.default_rng(3)
    seal = synthetic_seal(rng, 40, spacing=90.0, per_row=8)
    xy, kinds = _seal_arrays(seal)
    reader = [
        {"ch": ch, "x": l["x"] + rng.normal(0, 60), "y": l["y"] + rng.normal(0, 60)}
        for ch, l in zip(draw_kinds(rng, 40), seal["letters"])
    ]
    nxy = np.array([[n["x"], n["y"]] for n in reader])
    nk = np.array([KIND_INDEX[n["ch"]] for n in reader], dtype=np.int64)
    perms = np.vstack([np.arange(40), window_permutations(40, 99, 5, "w")])
    counts = null_match_counts(nxy, nk, xy, kinds, perms, R_PRIMARY)
    assert counts.dtype.kind == "i"
    assert counts[0] == match_letters(reader, seal["letters"], R_PRIMARY)["count"]
    # Every permuted count also equals a direct matching against the permuted seal.
    for j in range(1, 8):
        permuted = [dict(l, ch=seal["letters"][perms[j, i]]["ch"]) for i, l in enumerate(seal["letters"])]
        assert counts[j] == match_letters(reader, permuted, R_PRIMARY)["count"]


def test_null_counts_empty_inputs():
    perms = window_permutations(3, 5, 1, "w")
    xy = np.zeros((3, 2))
    k = np.zeros(3, dtype=np.int64)
    out = null_match_counts(np.zeros((0, 2)), np.zeros(0, dtype=np.int64), xy, k, perms, R_PRIMARY)
    assert np.array_equal(out, np.zeros(5, dtype=np.int64))


def test_arm_summed_mean_cnet():
    cnet = {"w1": {"r1": 2.0, "r2": 4.0, "r3": 0.0}, "w2": {"r1": -1.0, "r2": 1.0, "r3": 3.0}}
    assert arm_summed_mean_cnet(cnet) == pytest.approx(2.0 + 1.0)
    assert arm_summed_mean_cnet({}) == 0.0


def test_max_t_single_arm_equals_single_p():
    null = np.array([3, 5, 7, 2, 9, 4, 4, 6])
    res = max_t_p({"a": (6, null, 1)})
    assert res["p_max"] == permutation_p(6, null)
    assert res["argmax_arm"] == "a"


def test_max_t_hand_example():
    # Two arms, 4 permutations, 1 reader each.  E_null: a -> 2.0, b -> 5.0.
    a_null = np.array([1, 2, 3, 2])
    b_null = np.array([5, 4, 8, 3])
    res = max_t_p({"a": (4, a_null, 1), "b": (6, b_null, 1)})
    # observed C_net: a = 2, b = 1 -> max 2.  Permuted centred: a = [-1,0,1,0], b = [0,-1,3,-2]
    # permuted max = [0, 0, 3, 0] -> #>=2 is 1 -> p = 2/5
    assert res["p_max"] == Fraction(2, 5)
    assert res["argmax_arm"] == "a"
    assert res["observed_max_c_net"] == Fraction(2)
    assert permutation_p(4, a_null) == Fraction(1, 5)


def test_max_t_uses_mean_over_readers():
    # Arm with 3 readers: totals are sums over readers; statistic is total/3.
    a_null = np.array([3, 3, 6, 0])  # E = 3 -> centred mean [0,0,1,-1]
    b_null = np.array([1, 1, 1, 1])  # E = 1 -> centred [0,0,0,0]
    res = max_t_p({"a": (6, a_null, 3), "b": (2, b_null, 1)})
    # observed: a = (6-3)/3 = 1, b = 1 -> max 1; permuted max = [0,0,1,0] -> count 1
    assert res["observed_max_c_net"] == Fraction(1)
    assert res["p_max"] == Fraction(2, 5)


def test_max_t_zero_reader_arm_is_constant_zero():
    res = max_t_p({"a": (0, np.zeros(4, dtype=np.int64), 0), "b": (2, np.array([0, 1, 2, 3]), 1)})
    assert res["observed_max_c_net"] == Fraction(1, 2)


def test_p_max_at_least_best_single_arm_p_random():
    rng = np.random.default_rng(99)
    for _ in range(40):
        n_arms = int(rng.integers(2, 6))
        n_perm = 60
        arms = {}
        for a in range(n_arms):
            n_r = int(rng.integers(1, 4))
            null = rng.binomial(20 * n_r, 0.3, size=n_perm)
            obs = int(rng.binomial(20 * n_r, rng.uniform(0.2, 0.6)))
            arms[f"arm{a}"] = (obs, null, n_r)
        res = max_t_p(arms)
        best = min(permutation_p(o, nl) for o, nl, _ in arms.values())
        assert res["p_max"] >= best


def test_max_t_rejects_mismatched_perm_counts():
    with pytest.raises(ValueError):
        max_t_p({"a": (1, np.zeros(3, dtype=np.int64), 1), "b": (1, np.zeros(4, dtype=np.int64), 1)})


def test_kind_index_covers_canonical_kinds():
    assert sorted(KIND_INDEX.values()) == list(range(len(CANONICAL_KINDS)))
