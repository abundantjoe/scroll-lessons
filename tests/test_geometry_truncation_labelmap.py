# Provenance: Project HERCULES | owner the owner | [id removed]
"""v2 truncation and 2.4 um <-> 9 um label-map tests."""

import numpy as np
import pytest

from hercules.geometry import labelmap as LM
from hercules.geometry import truncation as TR


@pytest.fixture
def g():
    # generation grows with distance from the seed at (4, 4)
    vv, uu = np.mgrid[0:9, 0:9]
    return (np.abs(vv - 4) + np.abs(uu - 4)).astype(np.uint16)


def flat(shape, *rc):
    return int(np.ravel_multi_index(rc, shape))


def test_no_contacts_keeps_all(g):
    res = TR.v2_truncation(g, [])
    assert res.cutoff is None and res.keep.all() and res.n_removed == 0
    assert TR.v2_cutoff(g, np.zeros((0, 2), int)) is None


def test_single_contact_uses_max_generation(g):
    i = flat(g.shape, 4, 1)  # g = 3
    j = flat(g.shape, 0, 0)  # g = 8
    res = TR.v2_truncation(g, [(i, j)])
    assert res.cutoff == 8
    np.testing.assert_array_equal(res.keep, g < 8)
    assert not res.keep[0, 0] and res.keep[4, 4]


def test_multiple_contacts_min_over_max(g):
    c = [
        (flat(g.shape, 4, 1), flat(g.shape, 0, 0)),  # max(3, 8) = 8
        (flat(g.shape, 2, 4), flat(g.shape, 7, 5)),  # max(2, 4) = 4
        (flat(g.shape, 8, 8), flat(g.shape, 8, 7)),  # max(8, 7) = 8
    ]
    res = TR.v2_truncation(g, c)
    assert res.cutoff == 4
    np.testing.assert_array_equal(res.keep, g < 4)
    assert res.n_contacts == 3 and res.n_removed == int((g >= 4).sum())


def test_same_generation_contact_and_order_invariance(g):
    a, b = flat(g.shape, 4, 6), flat(g.shape, 6, 4)  # both g = 2
    r1 = TR.v2_truncation(g, [(a, b)])
    r2 = TR.v2_truncation(g, np.array([[b, a]]))
    assert r1.cutoff == r2.cutoff == 2
    assert r1.keep.sum() == 5  # g in {0, 1}


def test_out_of_range_contact_raises(g):
    with pytest.raises(IndexError):
        TR.v2_truncation(g, [(0, g.size)])


def test_truncate_points_with_validity(g):
    pts = np.random.default_rng(0).random((9, 9, 3)).astype(np.float32) * 100 + 1
    pts[4, 4] = -1.0
    out, res = TR.truncate_mesh_points(pts, g, [(flat(g.shape, 4, 2), flat(g.shape, 4, 7))])
    assert res.cutoff == 3
    keep = (g < 3)
    keep[4, 4] = False
    np.testing.assert_array_equal(res.keep, keep)
    assert np.all(out[~keep] == -1.0)
    np.testing.assert_array_equal(out[keep], pts[keep])


# --------------------------------------------------------------------------
# label map
# --------------------------------------------------------------------------

def test_labelmap_known_example():
    # N2 = 1000, N9 = 266: c9 = (490 + 10) * 266 / 1000 - 10 = 123
    assert LM.map_2p4_to_9(490.0, 1000, 266) == pytest.approx(123.0)
    assert LM.map_9_to_2p4(123.0, 1000, 266) == pytest.approx(490.0)
    # per-axis extents (x, y)
    c9 = LM.map_2p4_to_9(np.array([490.0, 990.0]), (1000, 2000), (266, 533))
    np.testing.assert_allclose(c9, [123.0, 1000 * 533 / 2000 - 10])  # y: 256.5
    # the offset: c2 = -10 is a fixed point
    assert LM.map_2p4_to_9(-10.0, 1000, 266) == pytest.approx(-10.0)


def test_labelmap_round_trip():
    rng = np.random.default_rng(3)
    c2 = rng.uniform(0, 4000, (500, 2))
    n2, n9 = (4000, 3500), (1067, 933)
    np.testing.assert_allclose(LM.map_9_to_2p4(LM.map_2p4_to_9(c2, n2, n9), n2, n9), c2, atol=1e-9)
    c9 = rng.uniform(0, 1000, (500, 2))
    np.testing.assert_allclose(LM.map_2p4_to_9(LM.map_9_to_2p4(c9, n2, n9), n2, n9), c9, atol=1e-9)


def test_window_extents():
    n2, n9 = (1000, 2000), (266, 533)
    w = LM.map_window_2p4_to_9(100, 200, 300, 400, n2, n9)
    # x: 110*0.266-10 = 19.26 -> 19 ; 310*0.266-10 = 72.46 -> 73
    # y: 210*0.2665-10 = 45.965 -> 45 ; 410*0.2665-10 = 99.265 -> 100
    assert (w.x0, w.y0, w.x1, w.y1) == (19, 45, 73, 100)
    assert (w.width, w.height) == (54, 55)
    # enclosing: mapped window corners lie inside
    lo = LM.map_2p4_to_9(np.array([100.0, 200.0]), n2, n9)
    hi = LM.map_2p4_to_9(np.array([300.0, 400.0]), n2, n9)
    assert w.x0 <= lo[0] and w.y0 <= lo[1] and w.x1 >= hi[0] and w.y1 >= hi[1]
    # clamped to the canvas
    full = LM.map_window_2p4_to_9(0, 0, 1000, 2000, n2, n9)
    assert full.x0 == 0 and full.y0 == 0 and full.x1 <= 266 and full.y1 <= 533
    back = LM.map_window_9_to_2p4(w.x0, w.y0, w.x1, w.y1, n2, n9)
    assert back.x0 <= 100 and back.y0 <= 200 and back.x1 >= 300 and back.y1 >= 400
