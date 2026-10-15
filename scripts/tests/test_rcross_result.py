"""RULES R-CROSS: the scorer must see every census report, compressed or not.

Compressing the reports to keep this box above its disk floor silently shrank the populations from 66 and 107 to
55 and 17, and the scorer then OVERWROTE rcross.json with that partial result. It was caught only by re-running the
scorer afterwards and reading its output. These tests pin the behaviour so a cleanup can never quietly do it again.
"""
import gzip, importlib.util, json, os, sys
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("rcross_result", os.path.join(HERE, "rcross_result.py"))
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)


def report(transverse):
    return {"tool": "vc_tifxyz_selfcross", "report_only": True,
            "clean_of_transverse_self_intersection": transverse == 0,
            "census": [{"diagonal": d, "transverse": transverse, "coplanar": 0, "grazing": 0,
                        "triangles": 1000, "quads_dropped_for_edge_length": 0, "pairs_tested": 10,
                        "transverse_contacts": []} for d in (0, 1)]}


@pytest.fixture
def pop(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "G", str(tmp_path))
    d = tmp_path / "ours"
    d.mkdir()
    json.dump(report(4), open(d / "S__auto_grown_plain.json", "w"))
    with gzip.open(d / "S__auto_grown_gz.json.gz", "wt") as fh:
        json.dump(report(8), fh)
    return str(tmp_path)


def test_compressed_reports_are_read(pop):
    rows = rr.load_pop("ours", {})
    assert len(rows) == 2, "a compressed report was skipped, which silently shrinks the population"
    assert sorted(r["transverse_min"] for r in rows) == [4, 8]


def test_the_patch_name_survives_compression(pop):
    names = {r["patch"] for r in rr.load_pop("ours", {})}
    assert names == {"auto_grown_plain", "auto_grown_gz"}, "the .gz suffix leaked into the patch key"


def test_area_rates_are_computed_for_compressed_reports(pop):
    rows = rr.load_pop("ours", {"auto_grown_gz": 2.0})
    by = {r["patch"]: r for r in rows}
    assert by["auto_grown_gz"]["per_cm2"] == pytest.approx(4.0)
    assert by["auto_grown_plain"]["per_cm2"] is None
