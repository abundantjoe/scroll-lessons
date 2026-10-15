"""RULES R-DEPTH: the scorer must answer the declared bar and must refuse to answer while a window is missing."""
import importlib.util, json, os, sys
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("rdepth_result", os.path.join(HERE, "rdepth_result.py"))
rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)


def write(path, ink, blank=0.25, auc=0.9):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(dict(auc=auc, mean_on_ink=ink, mean_on_blank=blank, n_ink=100, n_blank=100), open(path, "w"))


@pytest.fixture
def lay(tmp_path, monkeypatch):
    out, gb = str(tmp_path / "rdepth"), str(tmp_path / "gateB")
    monkeypatch.setattr(rd, "OUT", out); monkeypatch.setattr(rd, "GATEB", gb)
    monkeypatch.setattr(rd, "WINDOWS", [
        ("low", os.path.join(out, "auc_low.json"), os.path.join(out, "auc_low_reverse.json"), 8, -6),
        ("centre", os.path.join(gb, "auc_render_plain.json"), os.path.join(gb, "auc_render_plain_reverse.json"), 14, 0),
        ("high", os.path.join(out, "auc_high.json"), os.path.join(out, "auc_high_reverse.json"), 19, 5)])
    os.makedirs(out, exist_ok=True)
    return out, gb


def build(out, gb, low, centre, high):
    write(os.path.join(gb, "auc_render_plain.json"), 0.30 + centre)
    write(os.path.join(gb, "auc_render_plain_reverse.json"), 0.30)
    for name, m in (("low", low), ("high", high)):
        write(os.path.join(out, "auc_%s.json" % name), 0.30 + m)
        write(os.path.join(out, "auc_%s_reverse.json" % name), 0.30)


def verdict(out):
    return json.load(open(os.path.join(out, "rdepth.json")))


def test_pending_while_a_window_is_missing(lay, capsys):
    out, gb = lay
    write(os.path.join(gb, "auc_render_plain.json"), 0.76)
    write(os.path.join(gb, "auc_render_plain_reverse.json"), 0.29)
    rd.main()
    v = verdict(out)
    assert v["verdict"] == "PENDING" and set(v["pending_windows"]) == {"low", "high"}
    assert "NOT YET DECIDABLE" in capsys.readouterr().out


def test_a_better_off_centre_window_admits(lay):
    out, gb = lay
    build(out, gb, low=0.40, centre=0.30, high=0.20)      # low beats centre by 0.10 >= 0.05
    rd.main()
    v = verdict(out)
    assert v["admitted_by_gain"] and v["verdict"] == "ADMITTED"


def test_a_narrow_depth_response_admits_even_when_centre_is_best(lay):
    out, gb = lay
    build(out, gb, low=0.10, centre=0.50, high=0.40)      # worst/centre = 0.20 <= 0.50
    rd.main()
    v = verdict(out)
    assert not v["admitted_by_gain"] and v["admitted_by_selectivity"] and v["verdict"] == "ADMITTED"


def test_a_centred_broad_response_closes_depth_offset(lay, capsys):
    out, gb = lay
    build(out, gb, low=0.40, centre=0.50, high=0.45)      # centre best, worst/centre = 0.80 > 0.50
    rd.main()
    v = verdict(out)
    assert v["verdict"] == "FAILED" and v["retained_ratio"] == pytest.approx(0.80, rel=1e-6)
    assert "depth offset is CLOSED" in capsys.readouterr().out
