# Provenance: Project HERCULES | owner the owner | [id removed]
"""Known-answer tests for hercules.sg.refcal (SG 11 REF calibration; synthetic reads only)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from hercules.sg import constants as C
from hercules.sg import refcal as RC
from hercules.sg import synth as S

ROOT = Path(__file__).resolve().parents[1]


def window(wid, **kw):
    L = S.text_letters(**kw)
    return {"window_id": wid, "readers": S.read(L, ("a", "b", "c"), seed=len(wid))}


def data(windows):
    return {"voxel_size_um": S.VOXEL_UM, "canvas_px_per_voxel": 1.0, "windows": windows}


def test_all_regular_windows_pass():
    r = RC.calibrate(data([window("w1"), window("w2"), window("w3")]))
    assert r["n_evaluated"] == 3 and r["pass_rate_sg11"] == 1.0 and r["pass_rate_pitch_cv"] == 1.0
    assert r["pass_rate_at_fraction_bar"]["0.8"] == 1.0
    assert r["pitch_over_height_p5_p25_p50_p75_p95"][2] == pytest.approx(5.0 / 3.0, rel=0.02)


def test_known_mixture_gives_known_rates():
    ws = [window("ok1"), window("ok2"), window("two", n_rows=2), window("tall", height_mm=5.0, pitch_mm=9.0)]
    r = RC.calibrate(data(ws))
    # ok1, ok2 pass; the 2-row window fails rows (B9); the 5 mm window fails the median bar
    assert r["pass_rate_sg11"] == pytest.approx(0.5) and r["pass_rate_rows"] == pytest.approx(0.75)
    assert r["pass_rate_heights_median"] == pytest.approx(0.5)  # SG semantics: the 2-row window is not evaluated
    assert r["pass_rate_heights_median_ge2_rows"] == pytest.approx(0.75)  # height alone: only "tall" fails
    assert r["per_window"]["two"]["two_row_window"] is True
    assert r["per_window"]["two"]["pitch_over_height"] == pytest.approx(5.0 / 3.0, rel=0.02)
    assert r["n_two_row_windows"] == 1


def test_fraction_bar_grid_is_reported_not_applied():
    L = S.text_letters()
    for l in L[:5]:  # 16/21 = 0.76 in band
        l["h"] = 4.5 * S.PPM
    r = RC.calibrate(data([{"window_id": "w", "readers": S.read(L, ("a", "b", "c"), seed=1)}]))
    assert r["pass_rate_sg11"] == 1.0  # B8 revised: no fraction bar
    grid = r["pass_rate_at_fraction_bar"]
    assert grid["0.75"] == 1.0 and grid["0.8"] == 0.0
    assert tuple(float(k) for k in grid) == RC.FRACTION_BAR_GRID


def test_unevaluable_windows_are_counted_apart():
    one = {"window_id": "solo", "readers": {"a": []}}
    nobox = window("nobox")
    for ns in nobox["readers"].values():
        for n in ns:
            n.pop("box")
    r = RC.calibrate(data([window("w1"), one, nobox]))
    assert r["n_windows"] == 3 and r["n_evaluated"] == 1
    assert r["per_window"]["solo"]["status"] == "NOT_EVALUATED" and r["per_window"]["nobox"]["reason"] == "letter_box_missing"


def test_cli(tmp_path):
    f = tmp_path / "in.json"
    f.write_text(json.dumps(data([window("w1")])))
    out = tmp_path / "out.json"
    env = {"PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run([sys.executable, "-m", "hercules.sg.refcal", str(f), "--out", str(out)], capture_output=True,
                       text=True, cwd=ROOT, env=env)
    assert p.returncode == 0, p.stderr
    assert json.loads(out.read_text())["pass_rate_sg11"] == 1.0
