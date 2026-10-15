# Provenance: Project HERCULES | owner the owner | [id removed]
import numpy as np
import pytest

from hercules.scorer.consensus import agreed_letters, make_seal
from hercules.scorer.sealpos import label_positions, make_seal_with_labels, union_mask


def _n(ch, x, y, box=None, conf="firm"):
    d = {"ch": ch, "x": x, "y": y, "conf": conf}
    if box is not None:
        d["box"] = box
    return d


def _mask(shape=(400, 400)):
    return np.zeros(shape, dtype=np.uint8)


def test_union_mask_inclusive_and_clipped():
    m = union_mask([(1.0, 2.0, 3.0, 4.0), (-5, -5, 0.2, 0.2)], (6, 6))
    assert m[2:5, 1:4].all() and m.sum() == 9 + 1  # 3x3 block plus pixel (0, 0)
    assert m[0, 0]


def test_position_moves_to_label_centroid():
    lab = _mask()
    lab[100:111, 200:221] = 255  # centroid (row 105, col 210)
    s = {"a": [_n("Α", 190, 90, [180, 80, 230, 130])],
         "b": [_n("Α", 205, 100, [190, 95, 225, 120])],
         "c": [_n("Ο", 50, 50, [40, 40, 60, 60])]}
    letters, stats = make_seal_with_labels(s, lab)
    assert len(letters) == 1 and stats["n_label_positioned"] == 1
    l0 = letters[0]
    assert l0["pos_source"] == "labels" and l0["n_label_px"] == 11 * 21
    assert l0["x"] == pytest.approx(210.0) and l0["y"] == pytest.approx(105.0)
    assert l0["sealer_x"] == pytest.approx(197.5) and l0["sealer_y"] == pytest.approx(95.0)


def test_unchanged_without_label_ink_in_union():
    lab = _mask()
    lab[300:310, 300:310] = 1
    s = {"a": [_n("Ν", 100, 100, [90, 90, 110, 110])], "b": [_n("Ν", 110, 105, [95, 95, 120, 115])], "c": []}
    letters, _ = make_seal_with_labels(s, lab)
    assert letters[0]["pos_source"] == "sealers" and letters[0]["n_label_px"] == 0
    assert (letters[0]["x"], letters[0]["y"]) == (105.0, 102.5)


def test_invalid_or_missing_boxes_ignored():
    lab = _mask()
    lab[100, 100] = 1
    s = {"a": [_n("Τ", 100, 100, [120, 90, 80, 110])],   # x1 < x0: invalid
         "b": [_n("Τ", 101, 101)],                         # no box
         "c": [_n("Τ", 99, 99, [float("nan"), 0, 1, 1])]}
    letters, _ = make_seal_with_labels(s, lab)
    assert letters[0]["pos_source"] == "sealers"


def test_disjoint_boxes_union_centroid_of_all_labelled_px():
    lab = _mask()
    lab[100, 100] = 1
    lab[100, 200] = 1
    s = {"a": [_n("Ρ", 120, 100, [95, 95, 105, 105])], "b": [_n("Ρ", 180, 100, [195, 95, 205, 105])], "c": []}
    letters, _ = make_seal_with_labels(s, lab)
    assert letters[0]["x"] == pytest.approx(150.0) and letters[0]["y"] == pytest.approx(100.0)


def test_no_mask_keeps_positions_and_matches_make_seal():
    s = {"a": [_n("Α", 10, 10, [0, 0, 20, 20]), _n("Ο", 300, 300)],
         "b": [_n("Α", 20, 15), _n("Ο", 310, 290, conf="tentative")],
         "c": [_n("Α", 15, 5)]}
    plain, st = make_seal(s)
    new, st2 = make_seal_with_labels(s, None)
    assert [(l["ch"], l["x"], l["y"], l["firm"]) for l in plain] == [(l["ch"], l["x"], l["y"], l["firm"]) for l in new]
    assert st == st2


def test_group_letter_mismatch_raises():
    s = {"a": [_n("Α", 10, 10)], "b": [_n("Α", 12, 10)], "c": []}
    letters, _ = make_seal(s)
    groups = agreed_letters(s, radius=150, min_readers=2)
    bad = [dict(letters[0], x=999.0)]
    with pytest.raises(ValueError):
        label_positions(bad, groups, s, _mask())


def test_member_index_refers_to_original_list_with_unknown_first():
    lab = _mask()
    lab[50:53, 60:63] = 1  # centroid (51, 61)
    s = {"a": [_n("?", 5, 5, [0, 0, 10, 10]), _n("Ε", 60, 50, [55, 45, 66, 56])],
         "b": [_n("Ε", 62, 52, [300, 300, 310, 310])],
         "c": []}
    letters, _ = make_seal_with_labels(s, lab)
    assert len(letters) == 1 and letters[0]["pos_source"] == "labels"
    assert (letters[0]["x"], letters[0]["y"]) == (61.0, 51.0)
