# Provenance: Project HERCULES | owner the owner | [id removed]
import pytest

from hercules.scorer.d3drive import d3_outcome, window_mean_c_net


def _arms(fa_a=6, fa_b=1, ctrl_a=2, ctrl_b=0, nulla=2, reva=2, fb_fa=0.5, fb_ctrl=0.0):
    a = {"FA-A": fa_a, "FA-B": fa_b, "CTRL-A": ctrl_a, "CTRL-B": ctrl_b,
         "NULLA-A": nulla, "NULLA-B": 0, "REVA-A": reva, "REVA-B": 0}
    out = {k: {"summed_mean_C_net": v, "F_B_mean_per_reader": 0.0} for k, v in a.items()}
    out["FA-A"]["F_B_mean_per_reader"] = fb_fa
    out["CTRL-A"]["F_B_mean_per_reader"] = fb_ctrl
    return out


PW = {"FA-A": {"J1": 1.0, "J2": 5.0}, "CTRL-A": {"J1": 1.5, "J2": 0.5},
      "FA-B": {"J1@B": 0.0, "J2@B": 1.0}, "CTRL-B": {"J1@B": 0.0, "J2@B": 0.0}}
BLOB = {"blank_1": 0.01, "blank_2": 0.02}


def test_pass_when_all_checks_hold():
    r = d3_outcome(_arms(), 0.004, PW, BLOB, 20)
    assert r["outcome"] == "PASS" and r["best_fa_state"] == "A" and r["margin"] == 3.0 and r["fa_minus_ctrl"] == 4.0


@pytest.mark.parametrize("kw,p,pw,blob,check", [
    ({"fa_a": 4.9}, 0.004, PW, BLOB, "fa_ge_ctrl_plus_margin"),
    ({}, 0.01, PW, BLOB, "p_max_lt_0.01"),
    ({"nulla": 3.5}, 0.004, PW, BLOB, "nulla_le_ctrl_plus_1"),
    ({"reva": 3.5}, 0.004, PW, BLOB, "reva_le_ctrl_plus_1"),
    ({"fb_fa": 1.5}, 0.004, PW, BLOB, "fb_fa_le_ctrl_plus_1"),
    ({}, 0.004, {**PW, "FA-A": {"J1": 0.4, "J2": 5.0}}, BLOB, "no_window_more_than_1_below_ctrl"),
    ({}, 0.004, PW, {"blank_1": 0.03}, "blob_f180_le_0.0272"),
])
def test_each_check_can_fail(kw, p, pw, blob, check):
    r = d3_outcome(_arms(**kw), p, pw, blob, 20)
    assert r["outcome"] == "NOT PASSED" and r["checks"][check] is False
    assert sum(1 for v in r["checks"].values() if not v) == 1


def test_margin_uses_tenth_of_large_seal_and_state_b_selection():
    r = d3_outcome(_arms(fa_a=1, fa_b=9, ctrl_b=4), 0.001, PW, BLOB, 50)
    assert r["best_fa_state"] == "B" and r["margin"] == 5.0 and r["outcome"] == "PASS"


def test_missing_inputs_raise():
    a = _arms()
    del a["REVA-B"]
    with pytest.raises(ValueError):
        d3_outcome(a, 0.001, PW, BLOB, 20)
    with pytest.raises(ValueError):
        d3_outcome(_arms(), 0.001, PW, {}, 20)


def test_window_mean_c_net_skips_blanks():
    res = {"arms": {"X": {"windows": ["J1", "B1"], "readers_scored": ["r1", "r2"]}},
           "windows": {"J1": {"blank": False, "readers": {"r1": {"C_net": 1.0}, "r2": {"C_net": 3.0}}},
                       "B1": {"blank": True, "readers": {"r1": {"C_net": 0.0}, "r2": {"C_net": 0.0}}}}}
    assert window_mean_c_net(res, "X") == {"J1": 2.0}
