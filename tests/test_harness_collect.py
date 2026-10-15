# Provenance: Project HERCULES | owner the owner | [id removed]
from hercules.harness.collect import picker_counts, select_windows, validate_picker


def _pick(n, firm=0):
    return {"rows": "Y", "letters": [{"ch": "Α", "x": 1, "y": 1, "conf": "firm" if i < firm else "tentative"} for i in range(n)]}


def test_validate_picker():
    assert validate_picker({"windows": {"u": _pick(3)}})
    assert not validate_picker({"windows": {"u": {"rows": "maybe", "letters": []}}})
    assert not validate_picker({"w": {}})


def test_select_rules():
    ans = {"windows": {"a": _pick(9, 2), "b": _pick(9, 5), "c": _pick(4), "d": _pick(6), "e": _pick(7), "f": _pick(8)}}
    key = {"a": {"segment": "S1", "y0": 0, "x0": 0, "h": 100, "w": 100},
           "b": {"segment": "S1", "y0": 50, "x0": 50, "h": 100, "w": 100},   # overlaps a
           "c": {"segment": "S2", "y0": 0, "x0": 0, "h": 100, "w": 100},     # < 5 letters
           "d": {"segment": "S1", "y0": 500, "x0": 0, "h": 100, "w": 100},
           "e": {"segment": "S1", "y0": 900, "x0": 0, "h": 100, "w": 100},
           "f": {"segment": "S1", "y0": 300, "x0": 0, "h": 100, "w": 100}}
    ch = select_windows(picker_counts(ans), key, target=8, max_per_segment=3)
    assert ch == ["b", "f", "e"]  # b beats a on firm count; a overlaps b; cap 3 per segment
