# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for hercules.sg.gate: DECL-SG items 1-6, 9, 11 (via runner), 13, 14,
the discovery rule and its calibration (DECL-EMPNULL), and the sg_check runner.
Synthetic reader JSON only (hercules.sg.synth)."""

import copy
from pathlib import Path

import pytest


from hercules.sg import constants as C
from hercules.sg import gate as G
from hercules.sg import synth as S

OMICRON = "Ο"


@pytest.fixture(scope="module")
def base():
    inp = S.passing_inputs()
    inp.pop("_sealers_for_band")
    return inp


@pytest.fixture(scope="module")
def base_result(base):
    return G.sg_check(base)


def run(base, mutate):
    inp = copy.deepcopy(base)
    mutate(inp)
    return G.sg_check(inp)


# ------------------------------------------------------------------ passing scenario


def test_passing_scenario_passes_every_item(base_result):
    r = base_result
    assert r["overall"] == "PASS", r["not_passed"]
    assert r["not_passed"] == []
    for i in C.SG_ITEMS:
        assert r["items"][i]["status"] in G.OK_STATES, (i, r["items"][i])
    assert r["items"]["1"]["a"]["agreed"] == 21
    assert r["discovery"]["status"] == "PASS" and r["discovery_calibration"]["k"] == 5
    assert r["R"]["n_inside"] == r["R"]["n_agreed_discovery"]
    assert len(r["inputs_sha256"]) == 64 and len(r["R"]["rect_sha256"]) == 64


def test_computed_items_really_computed(base_result):
    for i in ("1", "2", "3", "4", "5", "6", "7", "11"):
        assert base_result["items"][i]["status"] == "PASS"
    assert base_result["items"]["14"]["rotation"]["status"] == "PASS"


def test_result_is_deterministic(base):
    assert G.sg_check(copy.deepcopy(base)) == G.sg_check(copy.deepcopy(base))


def test_voxel_size_never_assumed(base):
    inp = copy.deepcopy(base)
    del inp["volume_metadata"]
    with pytest.raises(KeyError):
        G.sg_check(inp)
    assert G.voxel_size_um_from_metadata(S.METADATA) == pytest.approx(9.366)
    assert G.px_per_mm(9.366, 0.5) == pytest.approx(1000 / 9.366 / 2)


# ------------------------------------------------------------------ discovery + calibration


def test_discovery_nontext_agreed_two_fails(base):
    def m(inp):
        extra = [{"ch": OMICRON, "x": 100.0, "y": 100.0}, {"ch": "Α", "x": 900.0, "y": 900.0}]
        inp["discovery"]["readers"]["d1"]["nontext"] = copy.deepcopy(extra)
        inp["discovery"]["readers"]["d2"]["nontext"] = copy.deepcopy(extra)
    r = run(base, m)
    assert r["discovery"]["status"] == "FAIL" and r["discovery"]["agreed_nontext"] == 2
    assert r["overall"] == "FAIL" and "discovery" in r["not_passed"]


def test_discovery_nontext_single_agreed_allowed(base):
    def m(inp):
        one = [{"ch": OMICRON, "x": 100.0, "y": 100.0}]
        inp["discovery"]["readers"]["d1"]["nontext"] = copy.deepcopy(one)
        inp["discovery"]["readers"]["d2"]["nontext"] = copy.deepcopy(one)
    r = run(base, m)
    assert r["discovery"]["status"] == "PASS" and r["discovery"]["F_B_max"] == 1


def test_discovery_below_k_fails():
    readers = {rid: {"text": [{"ch": S.CANONICAL_KINDS[i], "x": 400.0 * i, "y": 0.0} for i in range(4)],
                     "nontext": []} for rid in ("a", "b", "c")}
    assert G.discovery_rule(readers, 5)["status"] == "FAIL"
    readers = {rid: {"text": [{"ch": S.CANONICAL_KINDS[i], "x": 400.0 * i, "y": 0.0} for i in range(5)],
                     "nontext": []} for rid in ("a", "b", "c")}
    assert G.discovery_rule(readers, 5)["status"] == "PASS"
    with pytest.raises(ValueError):
        G.discovery_rule(readers, 4)  # k never below 5


def _cal_tiles(n_total, counts):
    tiles = []
    for i in range(n_total):
        t = S.agreed_tile(counts[i], seed=i) if i < len(counts) else S.agreed_tile(0, seed=i)
        tiles.append({"tile_id": f"t{i}", "readers": {rid: {"text": v, "nontext": []} for rid, v in t.items()}})
    return tiles


def test_calibration_keeps_k_at_one_percent():
    cal = G.calibrate_discovery_k(_cal_tiles(200, [5, 5]))  # 2/200 = 1.0 % <= 1 %
    assert cal["k"] == 5 and cal["trail"][0]["fdr"] == pytest.approx(0.01)


def test_calibration_raises_k_until_fdr_ok():
    cal = G.calibrate_discovery_k(_cal_tiles(200, [5, 6, 6, 7, 7, 7]))
    # k=5: 6/200, k=6: 5/200, k=7: 3/200, k=8: 0
    assert [t["null_passes"] for t in cal["trail"]] == [6, 5, 3, 0]
    assert cal["k"] == 8


def test_calibration_nontext_agreement_is_not_a_discovery():
    tiles = _cal_tiles(200, [9, 9, 9])
    for t in tiles[:3]:
        for rid in ("n1", "n2"):
            t["readers"][rid]["nontext"] = [{"ch": OMICRON, "x": 0.0, "y": 0.0}, {"ch": "Α", "x": 900.0, "y": 0.0}]
    assert G.calibrate_discovery_k(tiles)["k"] == 5


def test_calibration_needs_200_tiles(base):
    assert G.calibrate_discovery_k(_cal_tiles(199, []))["status"] == "FAIL"
    r = run(base, lambda inp: inp["discovery_calibration"].update(null_tiles=inp["discovery_calibration"]["null_tiles"][:199]))
    assert r["overall"] == "FAIL" and "discovery_calibration" in r["not_passed"]


def test_uncalibrated_discovery_is_not_evaluated(base):
    r = run(base, lambda inp: inp.pop("discovery_calibration"))
    assert r["discovery"]["status"] == "NOT_EVALUATED" and r["overall"] == "FAIL"


# ------------------------------------------------------------------ R


def test_declared_R_must_match(base, base_result):
    good = base_result["R"]["rect"]
    assert base_result["R"]["declared_matches"] is True and base_result["R"]["declared_record"] == "SYNTH-R"
    bad = dict(good, x0=good["x0"] + 1.0)
    r = run(base, lambda inp: inp["R_declared"].update(rect=bad))
    assert r["R"]["status"] == "FAIL" and r["R"]["reason"] == "declared_R_differs_from_recomputed"
    assert r["overall"] == "FAIL" and "R" in r["not_passed"]


def test_undeclared_R_fails_closed(base):
    r = run(base, lambda inp: inp.pop("R_declared"))
    assert r["R"]["status"] == "FAIL" and r["R"]["reason"] == "R_not_declared" and r["overall"] == "FAIL"
    r = run(base, lambda inp: inp["R_declared"].pop("record"))
    assert r["R"]["status"] == "FAIL"


def test_sg7_arrays_must_cover_every_sg_letter(base):
    import numpy as np
    rng = np.random.default_rng(0)
    crops = [rng.random((30, 30)) for _ in range(21)]
    patches = [rng.random((40, 40)) for _ in range(3)]
    r = G.sg_check(copy.deepcopy(base), copy_crops=crops, copy_patches=patches)
    assert r["items"]["7"]["status"] == "PASS" and r["items"]["7"]["n_letters"] == 21
    r = G.sg_check(copy.deepcopy(base), copy_crops=crops[:20], copy_patches=patches)
    assert r["items"]["7"]["status"] == "FAIL" and r["items"]["7"]["reason"] == "crop_count_differs_from_sg_letters"
    planted = list(crops)
    planted[5] = patches[1][5:35, 5:35].copy()
    r = G.sg_check(copy.deepcopy(base), copy_crops=planted, copy_patches=patches)
    assert r["items"]["7"]["status"] == "FAIL" and r["items"]["7"]["copies"] == [5]


# ------------------------------------------------------------------ SG 1


def _conf(inp, **kw):
    inp["confirmation"]["readers"] = S.read(S.text_letters(), S.CONF_READERS, seed=2, **kw)


def test_sg1a_fails_below_12(base):
    r = run(base, lambda inp: _conf(inp, drop=set(range(11, 21))))  # 11 letters
    assert r["items"]["1"]["a"]["status"] == "FAIL" and r["items"]["1"]["a"]["agreed"] == 11
    assert r["items"]["1"]["status"] == "FAIL"


def test_sg1a_passes_at_12(base):
    r = run(base, lambda inp: _conf(inp, drop=set(range(12, 21))))
    assert r["items"]["1"]["a"]["status"] == "PASS" and r["items"]["1"]["a"]["agreed"] == 12


def test_sg1b_firm_needs_two_readers(base):
    r = run(base, lambda inp: _conf(inp, firm_readers=("c1",)))
    assert r["items"]["1"]["a"]["status"] == "PASS"
    assert r["items"]["1"]["b"]["status"] == "FAIL" and r["items"]["1"]["b"]["firm_2readers"] == 0


def test_sg1c_margin_and_null_max(base):
    def m(inp):
        inp["empirical_null"]["tiles"] = [{"tile_id": f"z{i}", "readers": S.agreed_tile(12 if i == 0 else 0, i)}
                                          for i in range(40)]
    r = run(base, m)  # p99 (higher) of 39 zeros + one 12 = 12 -> margin 9
    c = r["items"]["1"]["c"]
    assert c["p99"] == 12 and c["margin"] == 9 and c["status"] == "FAIL"

    def m2(inp):
        inp["empirical_null"]["tiles"] = [{"tile_id": f"z{i}", "readers": S.agreed_tile(11 if i == 0 else 0, i)}
                                          for i in range(40)]
    assert run(base, m2)["items"]["1"]["c"]["status"] == "PASS"  # margin 10, 21 > 11


def test_sg1c_needs_40_tiles(base):
    r = run(base, lambda inp: inp["empirical_null"].update(tiles=inp["empirical_null"]["tiles"][:39]))
    assert r["items"]["1"]["c"]["status"] == "FAIL" and r["items"]["1"]["c"]["reason"] == "insufficient_null_tiles"


def test_sg1d_identity_shuffle_fails_when_identities_carry_no_information():
    letters = [dict(l, ch=OMICRON) for l in S.text_letters()]
    readers = S.read(letters, S.CONF_READERS, seed=2)
    rect = {"x0": 0.0, "y0": 0.0, "x1": 8000.0, "y1": 8000.0}
    null = [{"tile_id": str(i), "readers": S.agreed_tile(0, i)} for i in range(40)]
    r = G.sg1(readers, rect, null, m=1, n_perm=200)
    assert r["a"]["status"] == "PASS" and r["c"]["status"] == "PASS"
    assert r["d"]["status"] == "FAIL" and r["d"]["p"]["float"] == 1.0


def test_sg1d_alpha_scales_with_m_and_permutations_must_resolve(base):
    rect = {"x0": 0.0, "y0": 0.0, "x1": 8000.0, "y1": 8000.0}
    null = [{"tile_id": str(i), "readers": S.agreed_tile(0, i)} for i in range(40)]
    readers = base["confirmation"]["readers"]
    r = G.sg1(readers, rect, null, m=1, n_perm=99)  # p_min = 1/100 is not < 1/100
    assert r["d"]["status"] == "FAIL" and r["d"]["reason"] == "too_few_permutations_to_resolve_alpha"
    r = G.sg1(readers, rect, null, m=3, n_perm=400)
    assert r["d"]["alpha"]["exact"] == "1/300" and r["d"]["status"] == "PASS"


def test_sg1_readers_must_be_fresh(base):
    def m(inp):
        inp["confirmation"]["readers"] = {"d1" if k == "c1" else k: v for k, v in inp["confirmation"]["readers"].items()}
    r = run(base, m)
    assert r["items"]["1"]["fresh_readers"]["stale_reader_ids"] == ["d1"] and r["items"]["1"]["status"] == "FAIL"


def test_sg1_needs_exactly_three_readers(base):
    r = run(base, lambda inp: inp["confirmation"]["readers"].pop("c3"))
    assert r["items"]["1"]["status"] == "FAIL" and r["items"]["1"]["reason"] == "invalid_input"


def _all_reader_ids(inp):
    return sorted({rid for ids in G.collect_reads(inp).values() for rid in ids})


def _alone(r, name):
    """The overall result fails and ``name`` is the only thing that did not pass."""
    assert r["overall"] == "FAIL" and r["not_passed"] == [name], r["not_passed"]


def test_B14_model_mix_every_read(base):
    ids = _all_reader_ids(base)
    # alternate two versions inside every read (each read has 3 readers -> both versions)
    models = {}
    for read, rids in G.collect_reads(base).items():
        for k, rid in enumerate(rids):
            models[rid] = "mA" if k % 2 == 0 else "mB"
    assert sorted(models) == ids

    def ok(inp):
        inp["available_reader_models"] = ["mA", "mB"]
        inp["reader_models"] = dict(models)
    r = run(base, ok)
    assert r["overall"] == "PASS" and r["model_mix"]["status"] == "PASS"

    def rotation_one_model(inp):
        ok(inp)
        for rid in ("o1", "o2", "o3"):
            inp["reader_models"][rid] = "mA"
    r = run(base, rotation_one_model)
    assert r["model_mix"]["failed_reads"] == ["rotation"]
    _alone(r, "model_mix")

    def unrecorded(inp):
        ok(inp)
        del inp["reader_models"]["t2"]
    r = run(base, unrecorded)
    assert r["model_mix"]["failed_reads"] == ["retrace"]
    _alone(r, "model_mix")


def test_B14_single_version_not_applicable(base, base_result):
    assert base_result["model_mix"]["status"] == "NOT_APPLICABLE"
    r = run(base, lambda inp: inp.update(available_reader_models=["mA"]))
    assert r["model_mix"]["status"] == "NOT_APPLICABLE"


@pytest.mark.parametrize("read,key", [
    ("slice_+1", lambda inp: inp["slice_rereads"].update({"+1": {("c1" if k == "p1" else k): v for k, v in inp["slice_rereads"]["+1"].items()}})),
    ("second_lineage", lambda inp: inp["second_lineage"].update(readers={("m2" if k == "l2" else k): v for k, v in inp["second_lineage"]["readers"].items()})),
    ("rotation", lambda inp: inp["rotation"].update(readers={("t3" if k == "o3" else k): v for k, v in inp["rotation"]["readers"].items()})),
])
def test_B13_reader_reused_across_reads_fails_alone(base, read, key):
    r = run(base, key)
    assert r["readers_fresh"]["status"] == "FAIL"
    assert any(read in reads for reads in r["readers_fresh"]["reused"].values())
    _alone(r, "readers_fresh")


def test_B13_arms_and_sealers_count(base):
    L = S.text_letters()
    def m(inp):
        inp["trained_on_this_scroll"] = True
        inp["arms"] = {"NULL": {"c1": []}, "REV": {"x2": []}, "CTRL": {"x3": []}}  # c1 also confirms
    r = run(base, m)
    assert r["readers_fresh"]["reused"] == {"c1": ["confirmation", "arm_NULL"]}
    sealers = S.read(L, ("s1", "s2", "d3"), seed=9, jitter=60.0)  # d3 is a discovery reader
    r = run(base, lambda inp: inp.update(band_1203_0846A={"in_band": True, "sealers": sealers}))
    assert r["readers_fresh"]["reused"] == {"d3": ["discovery", "band_sealers"]}
    _alone(r, "readers_fresh")


def test_B13_opposite_order_and_blank_share_readers_by_design(base, base_result):
    # SG 3 and SG 2 namings come from the confirmation readers (paired display): not separate reads
    assert "c1" in base["opposite_order"]["readers"] and base_result["readers_fresh"]["status"] == "PASS"


# ------------------------------------------------------------------ B1 (discovery F_B)


def test_B1_per_reader_FB_fails_alone(base):
    def m(inp):  # reader d1 names 2 known letters in the non-text order; no agreement there
        inp["discovery"]["readers"]["d1"]["nontext"] = [{"ch": OMICRON, "x": 100.0, "y": 100.0},
                                                        {"ch": "\u0391", "x": 900.0, "y": 900.0}]
    r = run(base, m)
    d = r["discovery"]
    assert d["agreed_nontext"] == 0 and d["F_B_max"] == 2 and d["status"] == "FAIL"
    _alone(r, "discovery")


def test_B1_unknown_nontext_namings_are_not_FB(base):
    r = run(base, lambda inp: inp["discovery"]["readers"]["d1"].update(nontext=[{"ch": "?", "x": 0.0, "y": 0.0}] * 3))
    assert r["discovery"]["F_B_max"] == 0 and r["discovery"]["status"] == "PASS"


def test_B1_calibration_uses_full_rule():
    tiles = _cal_tiles(200, [9, 9, 9])
    for t in tiles[:3]:  # agreed text 9 but reader n1 has F_B = 2 -> not a discovery
        t["readers"]["n1"]["nontext"] = [{"ch": OMICRON, "x": 0.0, "y": 0.0}, {"ch": "\u0391", "x": 900.0, "y": 0.0}]
    assert G.calibrate_discovery_k(tiles)["trail"][0]["null_passes"] == 0


# ------------------------------------------------------------------ B7 via runner


def test_B7_copy_test_null_required(base):
    r = run(base, lambda inp: inp.pop("copy_test_null"))
    assert r["items"]["7"]["reason"] == "copy_test_null_missing"
    _alone(r, "7")
    for change in ({"false_flags": 1}, {"n_null_tiles": 39}, {"status": "UNINFORMATIVE"}, {"record": ""}):
        r = run(base, lambda inp: inp["copy_test_null"].update(change))
        _alone(r, "7")


def test_B7_precomputed_neff_floor(base):
    r = run(base, lambda inp: inp["copy_test"]["result"].update(n_eff_min=29.9))
    _alone(r, "7")
    r = run(base, lambda inp: inp["copy_test"]["result"].update(neff_floor_enforced=False))
    _alone(r, "7")


def test_B6_precomputed_abs(base):
    r = run(base, lambda inp: inp["copy_test"]["result"].update(max_abs_ncc=0.8, min_signed_ncc=-0.8))
    _alone(r, "7")


# ------------------------------------------------------------------ SG 2-4


def test_sg2_canary_and_blank(base):
    r = run(base, lambda inp: inp["batches"][0]["canary"].update(score=0.699))
    assert r["items"]["2"]["status"] == "FAIL" and r["items"]["2"]["consequence"] == "VOID_AND_REREAD"
    r = run(base, lambda inp: inp["batches"][0]["canary"].update(score=0.70))
    assert r["items"]["2"]["status"] == "PASS"
    one = [{"ch": "?", "x": 0.0, "y": 0.0}]
    r = run(base, lambda inp: inp["batches"][0]["blank"]["readers"].update(c1=one))
    assert r["items"]["2"]["status"] == "PASS"
    r = run(base, lambda inp: inp["batches"][0]["blank"]["readers"].update(c1=one, c2=one))
    assert r["items"]["2"]["status"] == "FAIL" and r["items"]["2"]["batches"][0]["blank_namings"] == 2
    r = run(base, lambda inp: inp["batches"][0]["canary"].update(ref_ceiling=0.0))
    assert r["items"]["2"]["status"] == "FAIL"


def test_sg2_every_batch_counts(base):
    def m(inp):
        b2 = copy.deepcopy(inp["batches"][0])
        b2["batch_id"] = "b2"
        b2["canary"]["score"] = 0.1
        inp["batches"].append(b2)
    r = run(base, m)
    assert r["items"]["2"]["void_batches"] == ["b2"]


def test_sg3_opposite_order(base, base_result):
    rect = base_result["R"]["rect"]
    inside = [{"ch": OMICRON, "x": rect["x0"] + 10, "y": rect["y0"] + 10}]
    outside = [{"ch": OMICRON, "x": rect["x0"] - 10, "y": rect["y0"] - 10}]
    r = run(base, lambda inp: inp["opposite_order"].update(readers={"c1": inside * 2, "c2": inside, "c3": outside * 5}))
    assert r["items"]["3"]["status"] == "FAIL" and r["items"]["3"]["namings_in_R"] == 3
    r = run(base, lambda inp: inp["opposite_order"].update(readers={"c1": inside * 2, "c2": [], "c3": outside * 5}))
    assert r["items"]["3"]["status"] == "PASS"


def test_sg4_slice_80_percent(base):
    L = S.text_letters()
    r = run(base, lambda inp: inp["slice_rereads"].update({"-1": S.read(L, S.CONF_READERS, 3, drop={0, 1, 2, 3})}))
    assert r["items"]["4"]["status"] == "PASS"  # 17/21 = 0.81
    r = run(base, lambda inp: inp["slice_rereads"].update({"+1": S.read(L, S.CONF_READERS, 3, drop={0, 1, 2, 3, 4})}))
    assert r["items"]["4"]["status"] == "FAIL"  # 16/21 = 0.76
    r = run(base, lambda inp: inp["slice_rereads"].pop("+1"))
    assert r["items"]["4"]["status"] == "FAIL"


def test_sg4_wrong_identity_does_not_reconfirm(base):
    L = S.text_letters()
    wrong = [dict(l, ch=S.CANONICAL_KINDS[(S.CANONICAL_KINDS.index(l["ch"]) + 1) % 24]) for l in L]
    r = run(base, lambda inp: inp["slice_rereads"].update({"-1": S.read(wrong, S.CONF_READERS, 3)}))
    assert r["items"]["4"]["per_offset"]["-1"]["reproduced"] == 0 and r["items"]["4"]["status"] == "FAIL"


# ------------------------------------------------------------------ SG 5-6


@pytest.mark.parametrize("change", [
    {"seed": 1}, {"fold": "A"}, {"trained_on_this_scroll": True}, {"trained_on_this_scroll": None},
    {"is_base": True, "base_usable": False}, {"is_base": True},
])
def test_sg5_lineage_conditions(base, change):
    r = run(base, lambda inp: inp["second_lineage"]["meta"].update(change))
    assert r["items"]["5"]["status"] == "FAIL"


def test_sg5_base_counts_if_usable(base):
    r = run(base, lambda inp: inp["second_lineage"]["meta"].update(is_base=True, base_usable=True))
    assert r["items"]["5"]["status"] == "PASS"


def test_sg5_fraction(base):
    L = S.text_letters()
    r = run(base, lambda inp: inp["second_lineage"].update(readers=S.read(L, ("l1", "l2", "l3"), 5, drop=set(range(11)))))
    assert r["items"]["5"]["status"] == "FAIL" and r["items"]["5"]["reproduced"] == 10  # 10/21 < 0.5
    r = run(base, lambda inp: inp["second_lineage"].update(readers=S.read(L, ("l1", "l2", "l3"), 5, drop=set(range(10)))))
    assert r["items"]["5"]["status"] == "PASS"  # 11/21


def test_sg6_retrace(base):
    assert run(base, lambda inp: inp["retrace"].update(overlap_fraction=0.59))["items"]["6"]["status"] == "FAIL"
    assert run(base, lambda inp: inp["retrace"].update(overlap_fraction=0.60))["items"]["6"]["status"] == "PASS"
    assert run(base, lambda inp: inp["retrace"].update(neighbour_contradiction=True))["items"]["6"]["status"] == "FAIL"
    assert run(base, lambda inp: inp["retrace"].pop("neighbour_contradiction"))["items"]["6"]["status"] == "FAIL"
    L = S.text_letters()
    r = run(base, lambda inp: inp["retrace"].update(readers=S.read(L, ("t1", "t2", "t3"), 6, drop=set(range(11)))))
    assert r["items"]["6"]["status"] == "FAIL"


def test_overlap_fraction():
    import numpy as np
    a = np.zeros((10, 10), bool)
    a[:, :5] = True
    b = np.zeros((10, 10), bool)
    b[:, 2:] = True
    assert G.overlap_fraction(a, b) == pytest.approx(0.6)


# ------------------------------------------------------------------ SG 7 via runner


def test_sg7_precomputed_result_checked(base):
    for change in ({"max_abs_ncc": 0.8}, {"status": "FAIL"}, {"n_rotations": 12}, {"n_letters": 5}):
        r = run(base, lambda inp: inp["copy_test"]["result"].update(change))
        assert r["items"]["7"]["status"] == "FAIL", change
    assert run(base, lambda inp: inp.pop("copy_test"))["items"]["7"]["status"] == "NOT_EVALUATED"


# ------------------------------------------------------------------ SG 9, 11, 13, 14 via runner


def test_sg9_arms(base, base_result):
    r = run(base, lambda inp: inp.update(trained_on_this_scroll=True))
    assert r["items"]["9"]["status"] == "FAIL"
    rect = base_result["R"]["rect"]
    x, y = rect["x0"] + 50, rect["y0"] + 50
    one = {"a": [{"ch": OMICRON, "x": x, "y": y}], "b": [{"ch": OMICRON, "x": x, "y": y}], "c": []}
    two = {"a": [{"ch": OMICRON, "x": x, "y": y}, {"ch": "Α", "x": x + 400, "y": y}],
           "b": [{"ch": OMICRON, "x": x, "y": y}, {"ch": "Α", "x": x + 400, "y": y}], "c": []}
    r = run(base, lambda inp: inp.update(trained_on_this_scroll=True, arms={"NULL": one, "REV": one, "CTRL": one}))
    assert r["items"]["9"]["status"] == "PASS"
    r = run(base, lambda inp: inp.update(trained_on_this_scroll=True, arms={"NULL": one, "REV": two, "CTRL": one}))
    assert r["items"]["9"]["status"] == "FAIL" and r["items"]["9"]["per_arm"]["REV"]["agreed_in_R"] == 2


def test_sg11_through_runner(base):
    L = S.text_letters(height_mm=5.0)
    r = run(base, lambda inp: inp["confirmation"].update(readers=S.read(L, S.CONF_READERS, seed=2)))
    assert r["items"]["11"]["status"] == "FAIL" and not r["items"]["11"]["heights_ok"]
    L = S.text_letters(n_rows=1, per_row=21)
    r = G.sg11_layout(G._agreed(S.read(L, S.CONF_READERS, 2)), S.read(L, S.CONF_READERS, 2),
                      {"x0": 0, "y0": 0, "x1": 1e5, "y1": 1e5}, S.PPM)
    assert r["status"] == "FAIL" and not r["rows_ok"]


def test_sg11_missing_boxes_fail(base):
    def m(inp):
        for ns in inp["confirmation"]["readers"].values():
            for n in ns:
                n.pop("box")
    assert run(base, m)["items"]["11"]["status"] == "FAIL"


def test_sg13_band():
    L = S.text_letters()
    sg_letters = G._agreed(S.read(L, S.CONF_READERS, 2))
    sealers = S.read(L, ("s1", "s2", "s3"), seed=9, jitter=60.0)
    assert G.sg13_band(sg_letters, {"in_band": True, "sealers": sealers})["status"] == "PASS"
    few = S.read(L, ("s1", "s2", "s3"), seed=9, drop=set(range(11)))
    r = G.sg13_band(sg_letters, {"in_band": True, "sealers": few})
    assert r["status"] == "FAIL" and r["alarm"] is True
    assert G.sg13_band(sg_letters, {"in_band": False})["status"] == "NOT_APPLICABLE"
    # 250 px radius: a 200 px shift still confirms, 300 px does not
    shifted = {k: [dict(n, x=n["x"] + 200) for n in v] for k, v in S.read(L, ("s1", "s2", "s3"), 9, jitter=0).items()}
    assert G.sg13_band(G._agreed(S.read(L, S.CONF_READERS, 2, jitter=0)), {"in_band": True, "sealers": shifted})["status"] == "PASS"
    far = {k: [dict(n, x=n["x"] + 300) for n in v] for k, v in S.read(L, ("s1", "s2", "s3"), 9, jitter=0).items()}
    assert G.sg13_band(G._agreed(S.read(L, S.CONF_READERS, 2, jitter=0)), {"in_band": True, "sealers": far})["status"] == "FAIL"


def test_sg13_runner_in_band(base):
    sealers = S.passing_inputs(n_null_disc=0, n_null_sg=0)["_sealers_for_band"]
    r = run(base, lambda inp: inp.update(band_1203_0846A={"in_band": True, "sealers": sealers}))
    assert r["items"]["13"]["status"] == "PASS"
    assert run(base, lambda inp: inp.pop("band_1203_0846A"))["items"]["13"]["status"] == "NOT_EVALUATED"


def test_sg14_rotation(base):
    L = S.text_letters()
    c = (4000.0, 3500.0)
    m10 = S.rotation_matrix(c, 10.0)
    r = run(base, lambda inp: inp.update(rotation={"canvas_to_display": m10,
                                                   "readers": S.apply_affine(S.read(L, ("o1", "o2", "o3"), 8), m10)}))
    assert r["items"]["14"]["rotation"]["angle_ok"] is False and r["items"]["14"]["status"] == "FAIL"
    m15 = S.rotation_matrix(c, -15.0)
    r = run(base, lambda inp: inp.update(rotation={"canvas_to_display": m15,
                                                   "readers": S.apply_affine(S.read(L, ("o1", "o2", "o3"), 8), m15)}))
    assert r["items"]["14"]["status"] == "PASS"
    few = S.read(L, ("o1", "o2", "o3"), 8, drop=set(range(11)))
    r = run(base, lambda inp: inp.update(rotation={"canvas_to_display": m15, "readers": S.apply_affine(few, m15)}))
    assert r["items"]["14"]["rotation"]["status"] == "FAIL"
    # namings left in the rotated frame (not mapped back) must not pass
    r = run(base, lambda inp: inp["rotation"].update(canvas_to_display=[[1, 0, 0], [0, 1, 0]]))
    assert r["items"]["14"]["status"] == "FAIL"


def test_sg14_needs_attested_parts(base):
    r = run(base, lambda inp: inp["attestations"].pop("14_profile"))
    assert r["items"]["14"]["status"] == "NOT_EVALUATED" and r["overall"] == "FAIL"
    r = run(base, lambda inp: inp["attestations"].update({"14_tests": {"status": "FAIL", "record": "X"}}))
    assert r["items"]["14"]["status"] == "FAIL"


# ------------------------------------------------------------------ attestations / overall


@pytest.mark.parametrize("key", ["0", "8", "10", "12"])
def test_attested_items(base, key):
    r = run(base, lambda inp: inp["attestations"].pop(key))
    assert r["items"][key]["status"] == "NOT_EVALUATED" and key in r["not_passed"] and r["overall"] == "FAIL"
    r = run(base, lambda inp: inp["attestations"].update({key: {"status": "PASS"}}))  # no record
    assert r["items"][key]["status"] == "NOT_EVALUATED"
    r = run(base, lambda inp: inp["attestations"].update({key: {"status": "FAIL", "record": "R"}}))
    assert r["items"][key]["status"] == "ATTESTED_FAIL" and r["overall"] == "FAIL"


@pytest.mark.parametrize("key,item", [("batches", "2"), ("opposite_order", "3"), ("slice_rereads", "4"),
                                      ("second_lineage", "5"), ("retrace", "6"), ("rotation", "14"),
                                      ("trained_on_this_scroll", "9")])
def test_missing_input_is_not_a_pass(base, key, item):
    r = run(base, lambda inp: inp.pop(key))
    assert r["items"][item]["status"] == "NOT_EVALUATED" and r["overall"] == "FAIL"


def test_output_is_canonical_json(base_result):
    from hercules.scorer.canon import canonical_json
    canonical_json(G._hashable(base_result))  # finite numbers, no Cf characters


# ------------------------------------------------------------------ B8, B9 alone via runner


def _conf_letters(inp, L):
    inp["confirmation"]["readers"] = S.read(L, S.CONF_READERS, seed=2)
    inp["copy_test"]["result"]["n_letters"] = len(L)


def test_B8_median_fails_alone_via_runner(base):
    L = S.text_letters()
    for l in L[:11]:  # median 4.5 mm
        l["h"] = 4.5 * S.PPM
    r = run(base, lambda inp: _conf_letters(inp, L))
    assert r["items"]["11"]["heights_ok"] is False
    _alone(r, "11")


def test_B8_fraction_under_80_percent_passes_via_runner(base):
    L = S.text_letters()
    for l in L[:5]:  # 76 % in band, median 3.0 mm: reported, not barred (B8 revised)
        l["h"] = 4.5 * S.PPM
    r = run(base, lambda inp: _conf_letters(inp, L))
    assert r["overall"] == "PASS" and r["items"]["11"]["letter_height_mm_frac_in_band"] == pytest.approx(16 / 21)


def test_B9_fails_alone_via_runner(base):
    L = S.text_letters()[:14]  # two rows of 7
    r = run(base, lambda inp: _conf_letters(inp, L))
    assert r["items"]["1"]["status"] == "PASS" and r["items"]["11"]["pitch_cv_status"] == "NOT_EVALUATED"
    _alone(r, "11")
