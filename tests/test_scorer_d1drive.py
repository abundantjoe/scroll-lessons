# Provenance: Project HERCULES | owner the owner | [id removed]
import pytest

from hercules.scorer.constants import NONTEXT, TEXT
from hercules.scorer.d1drive import (
    blank_namings_mean, d1_outcome, display_maps_for_job, filter_answer, max_mean_fb, mirror_letters,
    seals_by_state, sigma_crit, state_window_id, void_check,
)
from hercules.scorer.display import as_display_map, item_namings
from hercules.scorer.score import radius_key, score_decision

IMG = {
    "r0": {"kind": "REF0", "order": "single", "state": "A"},
    "bf": {"kind": "BASE", "order": "fwd", "state": "B"},
    "br": {"kind": "BASE", "order": "rev", "state": "B"},
    "rf": {"kind": "RAW", "order": "F", "state": "A"},
    "rb": {"kind": "RAW", "order": "B", "state": "A"},
}


def test_mirror_and_state_ids():
    assert state_window_id("J1", "A") == "J1" and state_window_id("J1", "B") == "J1@B"
    assert mirror_letters([{"ch": "Α", "x": 0.0, "y": 5.0}])[0]["x"] == 2135.0
    s = seals_by_state({"J1": {"blank": False, "letters": [{"ch": "Κ", "x": 100.0, "y": 7.0, "firm": True, "org_x": 1}]},
                        "B1": {"blank": True, "letters": []}})
    assert s["J1@B"]["letters"][0] == {"ch": "Κ", "x": 2035.0, "y": 7.0, "firm": True}
    assert s["B1@B"] == {"blank": True, "letters": []} and "org_x" not in s["J1"]["letters"][0]


def test_display_maps_sides_and_canary_skipped():
    items = {"i1": {"left": "r0", "right": None, "scored_window": "J1", "role": "window"},
             "i2": {"left": "bf", "right": "br", "scored_window": "J2", "role": "window"},
             "i3": {"left": "rb", "right": "rf", "scored_window": "B1", "role": "blank"},
             "i4": {"left": "r0", "right": None, "scored_window": "CAN", "role": "canary"}}
    dms = {d["item_id"]: d for d in display_maps_for_job("job", items, IMG, text_order="rev", raw_text_side="F")}
    assert set(dms) == {"i1", "i2", "i3"}
    assert dms["i1"]["side_order"] == [TEXT, NONTEXT] and dms["i1"]["window_id"] == "J1"
    assert dms["i2"]["side_order"] == [NONTEXT, TEXT] and dms["i2"]["window_id"] == "J2@B"
    assert dms["i3"]["side_order"] == [NONTEXT, TEXT]
    for d in dms.values():
        as_display_map(d)  # valid for the scorer


def test_display_maps_reject_bad_items():
    with pytest.raises(ValueError):
        display_maps_for_job("j", {"x": {"left": "bf", "right": "bf", "scored_window": "J1", "role": "window"}}, IMG, "fwd", "F")
    with pytest.raises(ValueError):
        display_maps_for_job("j", {"x": {"left": "bf", "right": None, "scored_window": "J1", "role": "window"}}, IMG, "fwd", "F")


def test_filter_answer_counts_canary_and_foreign():
    items = {"i1": {"role": "window"}, "i4": {"role": "canary"}}
    ans = {"items": [{"id": "i1", "left": {"rows": "Y", "letters": []}, "right": {"rows": "N", "letters": []}},
                     {"id": "i4", "left": {"rows": "Y", "letters": [{"ch": "Α"}, {"ch": "Ο"}]}, "right": {"rows": "N", "letters": []}},
                     {"id": "keysheet", "left": {"rows": "Y", "letters": []}, "right": {"rows": "N", "letters": []}}]}
    f, c = filter_answer(ans, items)
    assert [i["id"] for i in f["items"]] == ["i1"] and c == {"canary_namings": 2, "foreign_items": 1}


def _item(iid, letters, right=None):
    return {"id": iid, "left": {"rows": "Y", "letters": letters}, "right": {"rows": "N", "letters": right or []}}


def _l(ch, x, y, conf="firm"):
    return {"ch": ch, "x": x, "y": y, "box": [x - 10, y - 10, x + 10, y + 10], "conf": conf}


def test_end_to_end_state_b_scores_against_mirrored_seal():
    seal = {"J1": {"blank": False, "letters": [{"ch": "Κ", "x": 200.0, "y": 400.0, "firm": True}]},
            "B1": {"blank": True, "letters": []}}
    seals = seals_by_state(seal)
    key = {"a": {"kind": "BASE", "order": "fwd", "state": "B"}, "b": {"kind": "BASE", "order": "rev", "state": "B"},
           "c": {"kind": "BASE", "order": "fwd", "state": "B"}, "d": {"kind": "BASE", "order": "rev", "state": "B"}}
    items = {"it1": {"left": "a", "right": "b", "scored_window": "J1", "role": "window"},
             "it2": {"left": "d", "right": "c", "scored_window": "B1", "role": "blank"}}
    # state-B image px x for canvas x_B = 2135 - 200 = 1935 -> image x = (1935 + 0.5) / 2 - 0.5 = 967.25
    ans = {"items": [_item("it1", [_l("Κ", 967.25, 199.75)]), _item("it2", [], right=[_l("Ο", 500, 500)])]}
    dms = display_maps_for_job("r1", items, key, text_order="fwd", raw_text_side="F")
    decl = {"decision_id": "t", "arms": [{"arm_id": "BASE-B", "readers": ["r1"], "windows": ["J1@B", "B1@B"]}]}
    res = score_decision(decl, seals, {"r1": ans}, dms, n_perm=50)
    rec = res["windows"]["J1@B"]["readers"]["r1"]
    assert rec["C_all"][radius_key(250.0)] == 1
    assert blank_namings_mean(res, "BASE-B") == 1  # the O is on the text panel (right = c = fwd)
    assert max_mean_fb(res, "BASE-B") == 0.0


def test_outcome_table():
    assert d1_outcome(7, 12, 2, 0.001, 1, 0.3, 20)["outcome"] == "PASS_PENDING_CONFIRMATION"
    assert d1_outcome(7, 12, 2, 0.006, 1, 0.3, 20)["outcome"] == "BETWEEN"   # small seal needs p < 0.005
    assert d1_outcome(7, 12, 2, 0.006, 1, 0.3, 30)["outcome"] == "BETWEEN"   # 7 < 0.30 x 30
    assert d1_outcome(10, 16, 2, 0.006, 1, 0.3, 30)["outcome"] == "PASS_PENDING_CONFIRMATION"
    assert d1_outcome(2, 12, 2, 0.001, 1, 0.3, 20)["outcome"] == "FAIL"      # C_net <= 0.10 S'
    assert d1_outcome(7, 12, 2, 0.05, 1, 0.3, 20)["outcome"] == "FAIL"       # p >= 0.05
    assert d1_outcome(7, 12, 9, 0.001, 1, 0.3, 20)["outcome"] == "BETWEEN"   # chance margin fails
    assert d1_outcome(7, 12, 2, 0.001, 3, 0.3, 20)["outcome"] == "BETWEEN"   # F_B
    assert d1_outcome(7, 12, 2, 0.001, 1, 1.5, 20)["outcome"] == "BETWEEN"   # blanks
    assert d1_outcome(7, 12, 2, 0.001, 1, 0.3, 19)["outcome"] == "VOID"


def test_void_check_and_sigma_crit():
    assert void_check(9.9, 20) is True and void_check(10, 20) is False
    assert sigma_crit({0.0: 8, 0.15: 5, 0.30: 4, 0.45: 1}) == 0.30
    assert sigma_crit({0.0: 0, 0.15: 1}) is None
