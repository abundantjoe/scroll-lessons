# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for spec C: DisplayMap, the half-pixel convention and side/order assignment."""

import pytest

from hercules.scorer.display import DisplayMap, item_namings


def _dm(scale=1.0, y0=0.0, x0=0.0, side_order=("text", "nontext")):
    return DisplayMap(
        reader_id="r1", item_id="i1", window_id="w1", scale=scale, y0=y0, x0=x0, side_order=side_order
    )


def test_identity_mapping_at_scale_one_no_offset():
    dm = _dm()
    assert dm.to_canvas(0, 0) == (0.0, 0.0)
    assert dm.to_canvas(12.25, 7) == (12.25, 7.0)


def test_half_pixel_convention_scale_two():
    # Pixel centres sit at integer coordinates; pixel i spans [i-0.5, i+0.5).
    # Image pixel 0 (centre 0) covers canvas pixels 0 and 1, whose joint centre is 0.5.
    dm = _dm(scale=2.0)
    assert dm.to_canvas(0, 0) == (0.5, 0.5)
    assert dm.to_canvas(1, 0) == (2.5, 0.5)
    assert dm.to_canvas(0, 3) == (0.5, 6.5)
    # Image edges map to canvas edges.
    assert dm.to_canvas(-0.5, -0.5) == (-0.5, -0.5)
    width = 100
    assert dm.to_canvas(width - 0.5, 0)[0] == 2 * width - 0.5


def test_half_pixel_convention_downscale():
    dm = _dm(scale=0.5)
    # Two image pixels (centres -0.25 and 0.25 on canvas) share canvas pixel 0.
    a = dm.to_canvas(0, 0)[0]
    b = dm.to_canvas(1, 0)[0]
    assert a == -0.25 and b == 0.25
    assert (a + b) / 2 == 0.0


def test_offset_applies_x0_to_x_and_y0_to_y():
    dm = _dm(scale=1.0, y0=40.0, x0=100.0)
    assert dm.to_canvas(0, 0) == (100.0, 40.0)
    dm2 = _dm(scale=2.0, y0=1000.0, x0=3000.0)
    assert dm2.to_canvas(10, 20) == (3000.0 + 21.0 - 0.5, 1000.0 + 41.0 - 0.5)


@pytest.mark.parametrize("scale", [0.5, 1.0, 2.0, 3.0, 4.0])
def test_from_canvas_inverts_to_canvas(scale):
    dm = _dm(scale=scale, y0=17.0, x0=-3.0)
    for x, y in [(0, 0), (5.5, 9), (123.25, 77.75)]:
        X, Y = dm.to_canvas(x, y)
        xx, yy = dm.from_canvas(X, Y)
        assert xx == pytest.approx(x) and yy == pytest.approx(y)


def test_side_order_lookup():
    dm = _dm(side_order=("nontext", "text"))
    assert dm.order_of_side("left") == "nontext"
    assert dm.order_of_side("right") == "text"
    assert dm.side_of_order("text") == "right"
    assert dm.side_of_order("nontext") == "left"


@pytest.mark.parametrize(
    "bad", [("text", "text"), ("left", "right"), ("text",), ("text", "nontext", "text"), "text"]
)
def test_invalid_side_order_rejected(bad):
    with pytest.raises(ValueError):
        _dm(side_order=bad)


@pytest.mark.parametrize("scale", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_scale_rejected(scale):
    with pytest.raises(ValueError):
        _dm(scale=scale)


def test_dict_round_trip():
    dm = _dm(scale=2.0, y0=5.0, x0=6.0, side_order=("nontext", "text"))
    d = dm.to_dict()
    assert d["side_order"] == ["nontext", "text"]
    assert DisplayMap.from_dict(d) == dm


def test_item_namings_assigns_sides_to_orders():
    item = {
        "id": "i1",
        "left": {"rows": "N", "letters": [{"ch": "B", "x": 1, "y": 2, "box": [0, 0, 1, 1], "conf": "firm"}]},
        "right": {
            "rows": "Y",
            "letters": [
                {"ch": "\u03C3", "x": 10, "y": 20, "box": [0, 0, 1, 1], "conf": "tentative"},
                {"ch": "?", "x": 11, "y": 21, "box": [0, 0, 1, 1], "conf": "firm"},
            ],
        },
    }
    dm = _dm(scale=2.0, y0=100.0, x0=200.0, side_order=("nontext", "text"))
    out = item_namings(item, dm)
    assert out["text"]["rows"] == "Y"
    assert out["nontext"]["rows"] == "N"
    text = out["text"]["letters"]
    assert [n["kind"] for n in text] == ["\u03F9", None]
    assert text[0]["x"] == 200.0 + 21.0 - 0.5
    assert text[0]["y"] == 100.0 + 41.0 - 0.5
    assert text[0]["conf"] == "tentative"
    assert out["nontext"]["letters"][0]["kind"] == "\u0392"


def test_builder_style_side_order_mapping_and_extra_fields():
    key = {
        "window_id": "w9", "scale": 2.0, "y0": 10, "x0": 20,
        "side_order": {"left": "nontext", "right": "text"},
        "layout": "D2", "px_per_mm_image": 53.38, "left_sha256": "0" * 64, "right_sha256": "1" * 64,
    }
    dm = DisplayMap.from_dict(key, reader_id="r7", item_id="uuid-1")
    assert dm.side_order == ("nontext", "text")
    assert dm.order_of_side("right") == "text"
    assert (dm.reader_id, dm.item_id, dm.window_id) == ("r7", "uuid-1", "w9")
    assert dm.to_canvas(0, 0) == (20.5, 10.5)
    with pytest.raises(ValueError):
        _dm(side_order={"left": "text", "right": "text"})
    with pytest.raises(ValueError):
        _dm(side_order={"left": "text"})
