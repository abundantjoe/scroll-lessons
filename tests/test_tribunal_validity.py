# Provenance: Project HERCULES | owner the owner | [id removed]
"""TRIBUNAL batch-validity scorer and I16 rule, tested with synthetic reader JSON."""

import copy

import numpy as np
import pytest

from hercules.scorer.display import DisplayMap
from hercules.scorer.letters import CANONICAL_KINDS
from hercules.tribunal import validity as V

READERS = ("r1", "r2", "r3")
SEAL = [{"ch": CANONICAL_KINDS[i % 24], "x": 2100.0 + 180.0 * (i % 5), "y": 1100.0 + 300.0 * (i // 5),
         "firm": i % 2 == 0} for i in range(10)]
MIRRORS = [("m1", True), ("m2", False), ("m3", True), ("m4", False)]


def _keys(seed=0):
    rng = np.random.default_rng(seed)
    keys = {}
    for rid in READERS:
        keys[rid] = {}
        for iid, (y0, x0) in {"c1": (1000, 2000), "b1": (5000, 5000), "x1": (8000, 1000)}.items():
            so = ["text", "nontext"] if rng.random() < 0.5 else ["nontext", "text"]
            keys[rid][iid] = {"window_id": f"w_{iid}", "scale": 2.0, "y0": y0, "x0": x0, "side_order": so}
    return keys


def _letter(ch, x, y, conf="tentative"):
    return {"ch": ch, "x": x, "y": y, "box": [x - 10, y - 10, x + 10, y + 10], "conf": conf}


def _reader(rid, keys, *, canary_letters=None, rows="Y", bait_letters=0, bait_conf="tentative", wrong_kind=False):
    canary_letters = SEAL if canary_letters is None else canary_letters
    items = []
    for iid, k in keys[rid].items():
        dm = DisplayMap.from_dict(k, reader_id=rid, item_id=iid)
        panels = {"text": {"rows": "N", "letters": []}, "nontext": {"rows": "N", "letters": []}}
        if iid == "c1":
            panels["text"]["rows"] = rows
            for s in canary_letters:
                x, y = dm.from_canvas(s["x"] + 7.0, s["y"] - 5.0)
                ch = CANONICAL_KINDS[23] if wrong_kind else s["ch"]  # a kind absent from the seal
                panels["text"]["letters"].append(_letter(ch, x, y))
        if iid == "b1":
            for j in range(bait_letters):
                panels["text"]["letters"].append(_letter("Ο", 100.0 + 50 * j, 100.0, bait_conf))
        items.append({"id": iid, "left": panels[dm.order_of_side("left")], "right": panels[dm.order_of_side("right")]})
    return {"items": items}


def _batch(ceiling=0.9, area=4.0):
    return {"batch_id": "B1", "controls": [
        {"type": "positive_canary", "control_id": "c1", "item_ids": ["c1"], "seal": SEAL,
         "ref_ceiling": {"recall": ceiling, "rows_found": 1.0}},
        {"type": "bait", "control_id": "b1", "kind": "blank", "item_ids": ["b1"], "area_cm2": area},
        *[{"type": "mirror_canary", "control_id": m, "item_id": m, "mirrored": mir} for m, mir in MIRRORS],
    ]}


def _mirror_answers(n_wrong=0, missing=0):
    ans = {rid: {m: ("mirrored" if mir else "normal") for m, mir in MIRRORS} for rid in READERS}
    flips = [(rid, m) for rid in READERS for m, _ in MIRRORS]
    for rid, m in flips[:n_wrong]:
        ans[rid][m] = "normal" if ans[rid][m] == "mirrored" else "mirrored"
    for rid, m in flips[n_wrong:n_wrong + missing]:
        del ans[rid][m]
    return ans


def _score(readers, keys, **kw):
    ma = kw.pop("mirror_answers", _mirror_answers())
    return V.score_batch(kw.pop("batch", _batch()), readers, keys, ma, **kw)


@pytest.fixture
def keys():
    return _keys()


def test_good_batch_is_valid(keys):
    rep = _score({r: _reader(r, keys) for r in READERS}, keys)
    assert not rep["void"], rep["reasons"]
    c = rep["controls"][0]
    assert c["recall"] == 1.0 and c["rows_found"] == 1.0


def test_canary_low_recall_voids(keys):
    rs = {r: _reader(r, keys, canary_letters=SEAL[:3]) for r in READERS}
    rep = _score(rs, keys)
    assert rep["void"] and any("recall" in s for s in rep["reasons"])


def test_canary_recall_exactly_at_bar_is_valid(keys):
    rs = {r: _reader(r, keys, canary_letters=SEAL[:4]) for r in READERS}  # 0.4 = 0.5 x 0.8
    assert not _score(rs, keys, batch=_batch(ceiling=0.8))["void"]
    rs = {r: _reader(r, keys, canary_letters=SEAL[:3]) for r in READERS}
    assert _score(rs, keys, batch=_batch(ceiling=0.8))["void"]


def test_canary_wrong_identities_do_not_count(keys):
    rs = {r: _reader(r, keys, wrong_kind=True) for r in READERS}
    rep = _score(rs, keys)
    assert rep["void"] and rep["controls"][0]["recall"] == 0.0


def test_canary_rows_not_found_voids(keys):
    rs = {r: _reader(r, keys, rows="N" if r == "r1" else "Y") for r in READERS}
    rep = _score(rs, keys)
    assert rep["void"] and any("rows found" in s for s in rep["reasons"])
    assert rep["controls"][0]["rows_found"] == pytest.approx(2 / 3)


def test_canary_letters_on_wrong_side_do_not_count(keys):
    """Namings are split by the scorer-held side order: letters on the non-text panel
    never count as canary recall."""
    bad = copy.deepcopy(keys)
    for rid in READERS:
        so = bad[rid]["c1"]["side_order"]
        bad[rid]["c1"]["side_order"] = so[::-1]
    rs = {r: _reader(r, keys) for r in READERS}
    rep = _score(rs, bad)
    assert rep["void"] and rep["controls"][0]["recall"] == 0.0


@pytest.mark.parametrize("counts,void", [((0, 0, 0), False), ((1, 1, 1), False), ((3, 0, 0), False), ((2, 1, 1), True), ((4, 0, 0), True)])
def test_bait_named_letters_per_4cm2(keys, counts, void):
    # area 4 cm^2 per panel, both panels count -> 8 cm^2 per reader -> rate = count / 2;
    # the bait rate is the mean over readers, so (1,1,1) and (3,0,0) sit exactly at 0.5 (not > 0.5)
    rs = {r: _reader(r, keys, bait_letters=c) for r, c in zip(READERS, counts)}
    rep = _score(rs, keys)
    b = next(c for c in rep["controls"] if c["type"] == "bait")
    assert b["named_per_4cm2"] == pytest.approx(sum(counts) / 2 / 3)
    assert rep["void"] is void


def test_bait_any_firm_naming_voids(keys):
    rs = {r: _reader(r, keys, bait_letters=1 if r == "r2" else 0, bait_conf="firm") for r in READERS}
    rep = _score(rs, keys)
    assert rep["void"] and any("firm" in s for s in rep["reasons"])


@pytest.mark.parametrize("n_wrong,missing,void", [(0, 0, False), (2, 0, False), (3, 0, True), (2, 1, True)])
def test_mirror_detection(keys, n_wrong, missing, void):
    rep = _score({r: _reader(r, keys) for r in READERS}, keys, mirror_answers=_mirror_answers(n_wrong, missing))
    m = next(c for c in rep["controls"] if c["type"] == "mirror")
    assert m["detection"] == pytest.approx((12 - n_wrong - missing) / 12)
    assert rep["void"] is void


def test_invalid_reader_excluded_and_too_few_readers_voids(keys):
    rs = {r: _reader(r, keys) for r in READERS}
    rs["r3"] = {"items": [{"id": "c1", "left": {"rows": "maybe", "letters": []}, "right": {"rows": "N", "letters": []}}]}
    rep = _score(rs, keys)
    assert "r3" in rep["invalid_readers"] and rep["n_valid_readers"] == 2 and rep["void"]
    assert not _score(rs, keys, min_valid_readers=2)["void"]


def test_batch_without_controls_is_void(keys):
    rep = V.score_batch({"batch_id": "B0", "controls": []}, {r: _reader(r, keys) for r in READERS}, keys, {})
    assert rep["void"] and len(rep["reasons"]) == 3


def test_panel_area():
    assert V.panel_area_cm2(2136, 2136, 9.366) == pytest.approx((2136 * 9.366e-4) ** 2)
    with pytest.raises(ValueError):
        V.panel_area_cm2(10, 10, 0)


@pytest.mark.parametrize("pattern,halt,after", [
    ([0, 0, 0], False, None),
    ([0, 0, 1], False, None),          # 1/3 is not > 1/3
    ([0, 0, 1, 1], True, 4),           # 2/4 > 1/3
    ([1], True, 1),                    # running fraction 1/1 > 1/3: halts at once
    ([0, 0, 0, 0, 0, 1, 1], False, None),  # 2/7 < 1/3
    ([0, 0, 0, 0, 1, 1, 1], True, 7),  # 3/7 > 1/3
])
def test_i16(pattern, halt, after):
    st = V.i16_status([{"void": bool(v)} for v in pattern])
    assert st["halt"] is halt and st["halt_after_batch"] == after


def test_mirror_answers_from_panels():
    readers = {"r1": {"items": [{"id": "i1", "left": {"rows": "N", "letters": [], "mirrored": "Y"},
                                 "right": {"rows": "N", "letters": [], "mirrored": "N"}}]},
               "r2": {"items": [{"id": "i1", "left": {"rows": "N", "letters": []},
                                 "right": {"rows": "N", "letters": [], "mirrored": "maybe"}}]}}
    panels = [{"control_id": "m1", "item_id": "i1", "side": "left"}, {"control_id": "m2", "item_id": "i1", "side": "right"}]
    ans = V.mirror_answers_from_panels(readers, panels)
    assert ans == {"r1": {"m1": "mirrored", "m2": "normal"}, "r2": {}}
    ctrls = [{"control_id": "m1", "item_id": "m1", "mirrored": True}, {"control_id": "m2", "item_id": "m2", "mirrored": False}]
    assert V.score_mirror(ctrls, ans, ["r1", "r2"])["detection"] == pytest.approx(0.5)
