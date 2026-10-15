# Provenance: Project HERCULES | owner the owner | [id removed]
from hercules.scorer.probe1 import dedup, map_namings, score_arm

KEY = {"t1": {"window": "W", "image_to_levelled_window_px": [[2, 0, 0.5], [0, 2, 0.5]]},
       "t2": {"window": "W", "image_to_levelled_window_px": [[1, 0, 1000], [0, 1, 1000]]}}


def _ans(items):
    return {"items": [{"id": i, "left": {"rows": "Y", "letters": L}, "right": {"rows": "N", "letters": []}}
                      for i, L in items]}


def test_mapping_and_dedup():
    a = _ans([("t1", [{"ch": "Α", "x": 500, "y": 500, "conf": "firm"}]),
              ("t2", [{"ch": "Α", "x": 1, "y": 1, "conf": "firm"}, {"ch": "Β", "x": 50, "y": 50, "conf": "tentative"}])])
    m = map_namings(a, KEY)["W"]
    # t1 (500,500) -> (1000.5, 1000.5); t2 (1,1) -> (1001, 1001): duplicate Alpha merged
    assert [n["ch"] for n in m] == ["Α", "Β"]
    assert abs(m[0]["x"] - 1000.5) < 1e-9


def test_agreement_counts():
    L = [{"ch": "Α", "x": 100, "y": 100, "conf": "firm"}, {"ch": "Κ", "x": 400, "y": 100, "conf": "tentative"}]
    per = {"r1": {"W": L}, "r2": {"W": [dict(L[0], x=120)]}, "r3": {"W": []}}
    s = score_arm(per, ["W"])
    assert s["total"]["agreed"] == 1 and s["total"]["agreed_firm"] == 1 and s["total"]["named"] == 3
    empty = score_arm({"r1": {}, "r2": {}, "r3": {}}, ["W"])
    assert empty["total"]["agreed"] == 0 and empty["per_window"]["W"]["shuffle_p"] is None
