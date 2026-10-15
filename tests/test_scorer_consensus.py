# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for specs F, G, H, I: consensus, seal rule, identity-shuffle null, SG 1c, discovery."""

from fractions import Fraction

import numpy as np
import pytest

from hercules.scorer.consensus import (
    agreed_letters,
    discovery,
    identity_shuffle_null,
    make_seal,
    sg1c_evaluate,
    sg1c_pass,
)
from hercules.scorer.constants import CONSENSUS_RADIUS, SG1C_MIN_NULL_TILES
from hercules.scorer.synthetic import draw_kinds, grid_positions

ALPHA, BETA, SIGMA = "\u0391", "\u0392", "\u03F9"
UNIT_N_PERM = 500


def n(ch, x, y, conf="firm"):
    return {"ch": ch, "x": float(x), "y": float(y), "conf": conf}


# ---------------------------------------------------------------- agreed_letters


def test_three_readers_agree_group_at_mean():
    g = agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(ALPHA, 30, 0)], "r3": [n(ALPHA, 0, 60)]})
    assert len(g) == 1
    assert g[0]["ch"] == ALPHA
    assert g[0]["n_readers"] == 3
    assert g[0]["x"] == pytest.approx(10.0) and g[0]["y"] == pytest.approx(20.0)
    assert [m["reader"] for m in g[0]["members"]] == ["r1", "r2", "r3"]


def test_two_of_three():
    g = agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(ALPHA, 100, 0)], "r3": [n(ALPHA, 900, 0)]})
    assert len(g) == 1 and g[0]["n_readers"] == 2
    assert agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(ALPHA, 100, 0)], "r3": []}, min_readers=3) == []


def test_different_kind_or_far_does_not_agree():
    assert agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(BETA, 0, 0)], "r3": []}) == []
    assert agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(ALPHA, 151, 0)], "r3": []}) == []
    assert len(agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(ALPHA, 150, 0)], "r3": []})) == 1


def test_normalised_kinds_agree():
    g = agreed_letters({"r1": [n("\u03C3", 0, 0)], "r2": [n("C", 10, 0)], "r3": [n("\u03A3", 0, 10)]})
    assert len(g) == 1 and g[0]["ch"] == SIGMA and g[0]["n_readers"] == 3


def test_unknown_namings_ignored():
    assert agreed_letters({"r1": [n("?", 0, 0)], "r2": [n("?", 0, 0)], "r3": []}) == []


def test_same_reader_cannot_agree_with_itself():
    assert agreed_letters({"r1": [n(ALPHA, 0, 0), n(ALPHA, 5, 0)], "r2": [], "r3": []}) == []


def test_each_naming_used_once():
    g = agreed_letters({"r1": [n(ALPHA, 0, 0), n(ALPHA, 20, 0)], "r2": [n(ALPHA, 10, 0)], "r3": []})
    assert len(g) == 1
    # Closest pair wins; the tie at 10 px is broken by canonical rank (r1 index 0 first).
    assert [(m["reader"], m["index"]) for m in g[0]["members"]] == [("r1", 0), ("r2", 0)]


def test_complete_linkage():
    # a-b 100 px, b-c 100 px, a-c 200 px: c cannot join {a, b}.
    g = agreed_letters({"r1": [n(ALPHA, 0, 0)], "r2": [n(ALPHA, 100, 0)], "r3": [n(ALPHA, 200, 0)]})
    assert len(g) == 1 and g[0]["n_readers"] == 2
    assert [m["reader"] for m in g[0]["members"]] == ["r1", "r2"]


def test_multiple_groups_and_min_readers_one():
    by = {
        "r1": [n(ALPHA, 0, 0), n(BETA, 1000, 0)],
        "r2": [n(ALPHA, 10, 0), n(BETA, 1010, 0)],
        "r3": [n(SIGMA, 5000, 0)],
    }
    assert len(agreed_letters(by)) == 2
    singles = agreed_letters(by, min_readers=1)
    assert len(singles) == 3
    assert sum(g["n_readers"] for g in singles) == 5


def test_default_radius_is_150():
    assert CONSENSUS_RADIUS == 150.0


def test_order_invariance_of_input_mapping():
    a = {"r2": [n(ALPHA, 10, 0)], "r1": [n(ALPHA, 0, 0)], "r3": [n(ALPHA, 0, 10)]}
    b = {"r1": [n(ALPHA, 0, 0)], "r3": [n(ALPHA, 0, 10)], "r2": [n(ALPHA, 10, 0)]}
    assert agreed_letters(a) == agreed_letters(b)


# ---------------------------------------------------------------- make_seal


def test_seal_firm_rules():
    sealers = {
        "s1": [n(ALPHA, 0, 0, "tentative"), n(BETA, 1000, 0, "firm"), n(SIGMA, 2000, 0, "firm"), n(ALPHA, 3000, 0)],
        "s2": [n(ALPHA, 5, 0, "tentative"), n(BETA, 1005, 0, "firm"), n(SIGMA, 2005, 0, "tentative")],
        "s3": [n(ALPHA, 0, 5, "tentative"), n(ALPHA, 1000, 5, "firm")],
    }
    letters, stats = make_seal(sealers)
    by_kind = {(l["ch"], round(l["x"] / 1000)): l for l in letters}
    assert len(letters) == 3  # the lone s1 alpha at 3000 is not a seal letter
    assert by_kind[(ALPHA, 0)]["firm"] is True  # all 3 agree (conf irrelevant)
    assert by_kind[(ALPHA, 0)]["n_sealers"] == 3
    assert by_kind[(BETA, 1)]["firm"] is True  # exactly 2 agree, both firm
    assert by_kind[(SIGMA, 2)]["firm"] is False  # exactly 2 agree, one tentative
    assert stats["n_letters"] == 3
    assert stats["n_firm"] == 2
    assert stats["n_agree_3"] == 1 and stats["n_agree_2"] == 2
    assert stats["per_sealer"]["s1"]["n_named"] == 4
    assert stats["per_sealer"]["s1"]["n_in_seal"] == 3
    assert stats["per_sealer"]["s3"]["n_in_seal"] == 1


def test_seal_requires_three_sealers():
    with pytest.raises(ValueError):
        make_seal({"s1": [], "s2": []})
    with pytest.raises(ValueError):
        make_seal({"s1": [], "s2": [], "s3": [], "s4": []})


def test_seal_requires_conf():
    with pytest.raises(ValueError):
        make_seal({"s1": [{"ch": ALPHA, "x": 0.0, "y": 0.0}], "s2": [], "s3": []})


def test_seal_letters_are_json_ready():
    letters, _ = make_seal({"s1": [n(ALPHA, 0, 0)], "s2": [n(ALPHA, 1, 1)], "s3": []})
    assert set(letters[0]) >= {"ch", "x", "y", "firm", "n_sealers", "sealers"}
    assert isinstance(letters[0]["x"], float)


# ---------------------------------------------------------------- identity shuffle null (SG 1d)


def _grid_namings(rng, kinds, jitter):
    pos = grid_positions(len(kinds), spacing=110.0, per_row=10)
    return [n(k, x + rng.normal(0, jitter), y + rng.normal(0, jitter)) for k, (x, y) in zip(kinds, pos)]


def test_identity_shuffle_null_detects_true_agreement():
    rng = np.random.default_rng(1)
    kinds = draw_kinds(rng, 60)
    by = {r: _grid_namings(rng, kinds, 15.0) for r in ("r1", "r2", "r3")}
    res = identity_shuffle_null(by, n_perm=UNIT_N_PERM, seed=4)
    assert res["observed"] >= 55
    assert len(res["null"]) == UNIT_N_PERM
    assert max(res["null"]) < res["observed"]
    assert res["p"] == Fraction(1, UNIT_N_PERM + 1)


def test_identity_shuffle_null_random_readers_not_significant():
    rng = np.random.default_rng(2)
    by = {r: _grid_namings(rng, draw_kinds(rng, 60), 15.0) for r in ("r1", "r2", "r3")}
    res = identity_shuffle_null(by, n_perm=UNIT_N_PERM, seed=4)
    assert res["p"] > Fraction(1, 20)
    assert res["p"] == Fraction(1 + sum(v >= res["observed"] for v in res["null"]), UNIT_N_PERM + 1)


def test_identity_shuffle_null_deterministic():
    rng = np.random.default_rng(5)
    by = {r: _grid_namings(rng, draw_kinds(rng, 30), 20.0) for r in ("r1", "r2", "r3")}
    a = identity_shuffle_null(by, n_perm=100, seed=9)
    b = identity_shuffle_null(by, n_perm=100, seed=9)
    c = identity_shuffle_null(by, n_perm=100, seed=10)
    assert a == b
    assert a["null"] != c["null"]


def test_identity_shuffle_preserves_observed_count():
    rng = np.random.default_rng(6)
    by = {r: _grid_namings(rng, draw_kinds(rng, 30), 20.0) for r in ("r1", "r2", "r3")}
    res = identity_shuffle_null(by, n_perm=20, seed=1)
    assert res["observed"] == len(agreed_letters(by))


# ---------------------------------------------------------------- SG 1c empirical null threshold


def test_sg1c_requires_40_null_tiles():
    assert SG1C_MIN_NULL_TILES == 40
    assert sg1c_pass(100, [0] * 39) is False
    assert sg1c_evaluate(100, [0] * 39)["reason"] == "insufficient_null_tiles"
    assert sg1c_pass(100, [0] * 40) is True


def test_sg1c_exact_threshold():
    null = [5] * 40
    assert sg1c_pass(15, null) is True  # 15 - 5 == 10 exactly
    assert sg1c_pass(14, null) is False
    ev = sg1c_evaluate(15, null)
    assert ev["p99"] == 5 and ev["margin"] == 10 and ev["pass"] is True


def test_sg1c_percentile_higher_method():
    # n = 200: the 99th percentile with method="higher" is the 2nd-largest value.
    null = list(range(200))
    ev = sg1c_evaluate(208, null)
    assert ev["p99"] == 198
    assert ev["pass"] is True
    assert sg1c_pass(207, null) is False


def test_sg1c_must_exceed_null_max():
    null = [0] * 199 + [100]  # p99 (higher) is 0, max is 100
    assert sg1c_evaluate(50, null)["margin"] >= 10
    assert sg1c_pass(50, null) is False
    assert sg1c_pass(100, null) is False  # equal to max is not greater
    assert sg1c_pass(101, null) is True


def test_sg1c_rejects_bad_null_values():
    with pytest.raises(ValueError):
        sg1c_pass(10, [float("nan")] * 40)


# ---------------------------------------------------------------- discovery rule


def _agreeing(kinds_positions):
    return {r: [n(k, x + i, y) for k, x, y in kinds_positions] for i, r in enumerate(("r1", "r2", "r3"))}


def test_discovery_pass_and_fail():
    five = [(ALPHA, i * 1000, 0) for i in range(5)]
    one = [(BETA, 0, 0)]
    two = [(BETA, 0, 0), (BETA, 1000, 0)]
    none = {"r1": [], "r2": [], "r3": []}
    assert discovery(_agreeing(five), none)["pass"] is True
    assert discovery(_agreeing(five), _agreeing(one))["pass"] is True
    assert discovery(_agreeing(five), _agreeing(two))["pass"] is False
    assert discovery(_agreeing(five[:4]), none)["pass"] is False
    res = discovery(_agreeing(five[:4]), none, k=4)
    assert res["pass"] is True and res["agreed_text"] == 4 and res["agreed_nontext"] == 0 and res["k"] == 4


def test_discovery_requires_same_three_readers():
    with pytest.raises(ValueError):
        discovery({"r1": [], "r2": []}, {"r1": [], "r2": []})
    with pytest.raises(ValueError):
        discovery({"r1": [], "r2": [], "r3": []}, {"r1": [], "r2": [], "r4": []})
