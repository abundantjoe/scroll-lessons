"""Tests for the truncated-map audit (added 2026-09-19 after a one-quadrant reverse map produced a verdict).

Both tests matter equally: the checker must catch the real failure AND must not cry wolf on an auto-cropped
surface, because the first version of it did exactly that and flagged 19 sound corpus maps.
"""
import os
import sys

import numpy as np
import pytest
import tifffile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import map_integrity as mi


def _pair(tmp_path, fwd, rev, name="m"):
    f, r = str(tmp_path / (name + ".tif")), str(tmp_path / (name + "_reverse.tif"))
    tifffile.imwrite(f, fwd); tifffile.imwrite(r, rev)
    return f, r


def test_catches_the_one_quadrant_reverse_map(tmp_path):
    n = 128
    fwd = np.full((n, n), 100, np.uint8)
    rev = np.zeros((n, n), np.uint8); rev[: n // 2, : n // 2] = 100
    f, r = _pair(tmp_path, fwd, rev)
    out = mi.check_pair(f, r)
    assert out["problems"], "a quarter-written reverse map must be caught"
    assert "PAIR" in out["problems"][0]
    assert out["nonzero_forward"] == pytest.approx(1.0) and out["nonzero_reverse"] == pytest.approx(0.25)


def test_does_not_flag_an_auto_cropped_surface_whose_maps_are_partly_zero(tmp_path):
    """The bar is relative. Our renders are cropped around an irregular surface, so 0.60-0.84 non-zero is normal."""
    n = 128
    shape = np.zeros((n, n), bool); shape[10:100, 20:110] = True
    rng = np.random.default_rng(1)
    fwd = np.where(shape, rng.integers(50, 200, (n, n)), 0).astype(np.uint8)
    rev = np.where(shape, rng.integers(50, 200, (n, n)), 0).astype(np.uint8)
    f, r = _pair(tmp_path, fwd, rev)
    assert float((fwd > 0).mean()) < 0.7, "the fixture must actually be a partly-zero map"
    assert mi.check_pair(f, r)["problems"] == []


def test_a_small_footprint_difference_inside_the_tolerance_is_accepted(tmp_path):
    n = 200
    fwd = np.zeros((n, n), np.uint8); fwd[:100] = 100
    rev = np.zeros((n, n), np.uint8); rev[:99] = 100          # 0.005 apart, inside the 0.02 tolerance
    f, r = _pair(tmp_path, fwd, rev)
    assert mi.check_pair(f, r)["problems"] == []


def test_a_shape_mismatch_is_a_problem(tmp_path):
    f, r = _pair(tmp_path, np.full((64, 64), 100, np.uint8), np.full((64, 32), 100, np.uint8))
    assert any("shape mismatch" in p for p in mi.check_pair(f, r)["problems"])


def test_an_unreadable_map_is_a_problem(tmp_path):
    f = str(tmp_path / "bad.tif"); open(f, "w").write("not a tiff")
    r = str(tmp_path / "bad_reverse.tif"); tifffile.imwrite(r, np.zeros((8, 8), np.uint8))
    assert mi.check_pair(f, r)["problems"]


def test_the_rdepth_runner_verifies_before_it_scores():
    """A window whose maps fail the audit must be deleted and not scored, and must not get a completion marker."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rdepth.sh")).read()
    assert "map_integrity.py" in src
    i_check = src.index("map_integrity.py")
    i_score = src.index("score_auc.py")
    i_marker = src.index("touch .infer_complete_$w")
    assert i_check < i_score, "the audit must run before the scorer"
    assert i_check < i_marker, "the audit must run before the completion marker is written"
    assert 'rm -f "$out/$w.tif"' in src, "truncated maps must be deleted, not left to be picked up later"


def test_infer_slot_wrapper_blocks_past_the_cap(tmp_path):
    """Scripts that call `infer` directly bypassed run_patch_dir.py's cap; the wrapper closes that gap."""
    import subprocess, time, os
    R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ, HERCULES_DATA=str(tmp_path), HERCULES_INFER_SLOTS="2")
    w = os.path.join(R, "infer_slot.sh")
    holders = [subprocess.Popen(["bash", w, "sleep", "4"], env=env) for _ in range(2)]
    time.sleep(1.0)
    t0 = time.time()
    subprocess.run(["bash", w, "true"], env=env, check=True)
    waited = time.time() - t0
    for h in holders:
        h.wait()
    assert waited > 1.5, "a third inference ran immediately although both slots were held (waited %.1fs)" % waited


def test_rdepth_takes_a_global_slot():
    import os
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rdepth.sh")).read()
    assert "infer_slot.sh" in src
    i = src.index("infer_slot.sh")
    j = src.index("inference.infer")
    assert i < j, "the slot must be taken before the inference starts"


def _mtime_pair(tmp, skew_s=0.0, shape=(32, 32)):
    import numpy as np, tifffile, os
    f = os.path.join(tmp, "m.tif"); r = os.path.join(tmp, "m_reverse.tif")
    a = np.full(shape, 200, np.uint8)
    tifffile.imwrite(f, a); tifffile.imwrite(r, a)
    st = os.stat(f)
    os.utime(f, (st.st_atime - skew_s, st.st_mtime - skew_s))
    return f, r


def test_sequential_writes_on_a_slow_read_are_NOT_stale():
    """The four real false positives: skew is about half the read's own inference time."""
    import tempfile, map_integrity as M
    for skew, infer in ((4620, 9222), (3705, 7985), (4209, 8141), (6806, 13108)):
        f, r = _mtime_pair(tempfile.mkdtemp(), skew_s=skew)
        out = M.check_pair(f, r, infer_s=infer)
        assert not [p for p in out["problems"] if p.startswith("STALE")], (skew, infer, out)


def test_a_leftover_map_from_an_earlier_run_is_flagged_STALE():
    import tempfile, map_integrity as M
    f, r = _mtime_pair(tempfile.mkdtemp(), skew_s=60 * 60 * 16)   # 16 h, the R-CREST-POWER case
    out = M.check_pair(f, r, infer_s=900.0)                       # on a read whose inference took 15 min
    stale = [p for p in out["problems"] if p.startswith("STALE")]
    assert stale, out
    assert "left over" in stale[0]


def test_a_read_with_no_recorded_inference_time_is_SKIPPED_not_guessed():
    import tempfile, map_integrity as M
    f, r = _mtime_pair(tempfile.mkdtemp(), skew_s=60 * 60 * 16)
    out = M.check_pair(f, r)          # no read_stats.json in that dir, so no key, so no s_infer
    assert out["infer_s"] is None
    assert not [p for p in out["problems"] if p.startswith("STALE")]


def test_the_bar_is_the_reads_own_cost_not_a_constant():
    import tempfile, map_integrity as M
    assert not hasattr(M, "MAX_MTIME_SKEW_S"), "the absolute bar was withdrawn; it was the wrong shape"
    assert M.SKEW_SLACK_S == 600.0
    f, r = _mtime_pair(tempfile.mkdtemp(), skew_s=5000)
    assert not [p for p in M.check_pair(f, r, infer_s=9000)["problems"] if p.startswith("STALE")]
    assert [p for p in M.check_pair(f, r, infer_s=1000)["problems"] if p.startswith("STALE")]


def test_stale_is_an_audit_flag_only_and_read_chart_does_not_refuse_on_it():
    import os
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "read_chart.py")).read()
    assert "mtime" not in src, "read_chart must not refuse a read on mtime skew; STALE is an audit flag"


def test_single_pair_cli_refuses_a_truncated_pair_and_passes_a_sound_one(tmp_path, capsys):
    """`map_integrity.py --pair FWD REV` is the release entry point for anyone's own maps: exit 1 + PAIR on the
    one-quadrant failure, exit 0 on a sound pair."""
    n = 128
    fwd = np.full((n, n), 100, np.uint8)
    rev = np.zeros((n, n), np.uint8); rev[: n // 2, : n // 2] = 100
    f, r = _pair(tmp_path, fwd, rev, "bad")
    assert mi.main(["--pair", f, r]) == 1
    out = capsys.readouterr().out
    assert "SUSPECT" in out and "PAIR" in out
    f, r = _pair(tmp_path, fwd, np.full((n, n), 90, np.uint8), "good")
    assert mi.main(["--pair", f, r]) == 0
    assert "SOUND" in capsys.readouterr().out


def test_json_to_a_bare_file_name_in_the_working_directory(tmp_path, monkeypatch):
    """`--json audit.json` (no directory part) used to crash in os.makedirs(''); the audit must write the file."""
    import json
    monkeypatch.chdir(tmp_path); monkeypatch.setenv("HERCULES_DATA", str(tmp_path / "empty"))
    assert mi.main(["--json", "audit.json"]) == 0
    assert json.load(open(tmp_path / "audit.json"))["pairs"] == []
