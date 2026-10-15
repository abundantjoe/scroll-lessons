"""G-GP part 5b: the geometry bars decide whether a lower consensus threshold's extra area may be read."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _mod(tmp_path, monkeypatch):
    monkeypatch.setenv("HERCULES_DATA", str(tmp_path))
    for m in list(sys.modules):
        if m == "ggp5b_decide":
            del sys.modules[m]
    import ggp5b_decide as g
    monkeypatch.setattr(g, "D", str(tmp_path))
    return g


def _write(tmp_path, part, rows, reports):
    os.makedirs(tmp_path / "gates" / "ggp", exist_ok=True)
    (tmp_path / "gates" / "ggp" / ("part%s_consensus_mesh.json" % part)).write_text(json.dumps({"rows": rows}))
    d = tmp_path / "gates" / "rcross" / ("cons_part%s" % part)
    os.makedirs(d, exist_ok=True)
    for name, transverse in reports.items():
        (d / (name + ".json")).write_text(json.dumps(
            {"surface": "/data/patches/x/" + name, "census": [{"transverse": t} for t in transverse]}))


def test_the_bars_are_the_controls_own_rates(tmp_path, monkeypatch):
    g = _mod(tmp_path, monkeypatch)
    assert (g.MAX_CROSS_PER_CM2, g.MAX_P90_SAG_UM) == (1.42, 9.93)


def test_clean_geometry_is_admitted(tmp_path, monkeypatch):
    g = _mod(tmp_path, monkeypatch)
    _write(tmp_path, "5b", [{"patch": "s1", "area_cm2": 9.0, "sag_um_p90": 5.0}], {"s1": [0, 0]})
    sys.argv = ["x", "--part", "5b"]
    assert g.main() == 0


def test_too_many_crossings_is_refused_however_large_the_area(tmp_path, monkeypatch):
    g = _mod(tmp_path, monkeypatch)
    _write(tmp_path, "5b", [{"patch": "s1", "area_cm2": 40.0, "sag_um_p90": 5.0}], {"s1": [100, 90]})
    sys.argv = ["x", "--part", "5b"]
    assert g.main() == 1, "90 sites over 40 cm2 is 2.25/cm2, above the 1.42 bar"


def test_the_worst_surface_decides_not_the_pooled_average(tmp_path, monkeypatch):
    """Pooling a batch's areas would divide one surface's crossings by everyone's area and make the bar lenient."""
    g = _mod(tmp_path, monkeypatch)
    _write(tmp_path, "5b",
           [{"patch": "good", "area_cm2": 30.0, "sag_um_p90": 4.0}, {"patch": "bad", "area_cm2": 1.0, "sag_um_p90": 4.0}],
           {"good": [0, 0], "bad": [5, 5]})
    sys.argv = ["x", "--part", "5b"]
    assert g.main() == 1, "5 sites on a 1 cm2 surface is 5.0/cm2 and must fail even beside a clean 30 cm2 one"


def test_excess_sag_is_refused(tmp_path, monkeypatch):
    g = _mod(tmp_path, monkeypatch)
    _write(tmp_path, "5b", [{"patch": "s1", "area_cm2": 9.0, "sag_um_p90": 12.0}], {"s1": [0, 0]})
    sys.argv = ["x", "--part", "5b"]
    assert g.main() == 1


def test_an_unmeasurable_bar_is_not_a_pass(tmp_path, monkeypatch):
    g = _mod(tmp_path, monkeypatch)
    _write(tmp_path, "5b", [{"patch": "s1", "area_cm2": 9.0, "sag_um_p90": 4.0}], {})
    sys.argv = ["x", "--part", "5b"]
    assert g.main() == 1, "no rcross report means the crossing bar is unmeasured, which is not met"
