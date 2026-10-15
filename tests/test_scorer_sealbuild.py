# Provenance: Project HERCULES | owner the owner | [id removed]
import numpy as np
import pytest

from hercules.scorer.sealbuild import build_seal, map_answer

# image px -> window px: scale 2 (D2) plus offset (row +10, col +20); [y, x] = M [iy, ix, 1]
M = [[2.0, 0.0, 10.0], [0.0, 2.0, 20.0]]
KEY = {"img1": {"window": "J1", "image_to_levelled_window_px": M},
       "img2": {"window": "J2", "image_to_levelled_window_px": [[2.0, 0, 0], [0, 2.0, 0], [0, 0, 1]]}}


def _item(iid, letters):
    return {"id": iid, "left": {"rows": "Y", "letters": letters}, "right": {"rows": "N", "letters": []}}


def _l(ch, x, y, conf="firm", box=None):
    d = {"ch": ch, "x": x, "y": y, "conf": conf}
    if box is not None:
        d["box"] = box
    return d


def test_map_answer_maps_centres_and_boxes_and_skips_keysheet():
    ans = {"items": [_item("keysheet_5da96bde", [_l("Α", 1, 1)]),
                     _item("img1", [_l("Α", 100, 50, box=[90, 40, 110, 60])])]}
    m = map_answer(ans, KEY)
    assert list(m) == ["J1"]
    n = m["J1"][0]
    assert (n["x"], n["y"]) == (220.0, 110.0)
    assert n["box"] == [200.0, 90.0, 240.0, 130.0]


def test_build_seal_counts_labels_blanks_and_organizer():
    a = {"items": [_item("img1", [_l("Α", 100, 50, box=[90, 40, 110, 60]), _l("Ο", 300, 300)]), _item("img2", [])]}
    b = {"items": [_item("img1", [_l("Α", 105, 52, box=[95, 45, 112, 62]), _l("Ο", 305, 302, conf="tentative")])]}
    c = {"items": [_item("img1", [_l("Α", 102, 48, conf="tentative")])]}
    lab = np.zeros((1000, 1000), np.uint8)
    lab[108:113, 218:223] = 1  # centroid (110, 220)
    org = {"J1": [[1.0, 0.0, 1000.0], [0.0, 1.0, 2000.0]]}
    seal, summ = build_seal({"s1": a, "s2": b, "s3": c}, KEY, ["J1", "J2"], labels={"J1": lab},
                            blank_windows=["B1"], organizer_affines=org)
    j1 = seal["windows"]["J1"]["letters"]
    assert summ["windows"]["J1"]["n_letters"] == 2 and summ["S_prime"] == 2
    alpha = next(l for l in j1 if l["ch"] == "Α")
    assert alpha["firm"] is True and alpha["n_sealers"] == 3  # 3/3 agree -> firm
    assert alpha["pos_source"] == "labels" and (alpha["x"], alpha["y"]) == (220.0, 110.0)
    assert (alpha["org_x"], alpha["org_y"]) == (2220.0, 1110.0)
    omicron = next(l for l in j1 if l["ch"] == "Ο")
    assert omicron["firm"] is False  # 2/3 with one tentative
    assert seal["windows"]["J2"] == {"blank": False, "letters": []}
    assert seal["windows"]["B1"] == {"blank": True, "letters": []}
    assert summ["n_firm_total"] == 1


def test_build_seal_requires_three_sealers():
    with pytest.raises(ValueError):
        build_seal({"s1": {"items": []}, "s2": {"items": []}}, KEY, ["J1"])


def test_invalid_conf_namings_are_dropped_not_fatal():
    a = {"items": [_item("img1", [_l("Α", 100, 50, conf="maybe")])]}
    seal, summ = build_seal({"s1": a, "s2": {"items": []}, "s3": {"items": []}}, KEY, ["J1"])
    assert summ["S_prime"] == 0
