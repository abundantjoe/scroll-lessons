"""Tests for scripts/read_chart.py (MASTER_PROMPT_v4 5.10). Run: python -m pytest scripts/tests/test_read_chart.py -q
Offline: a synthetic 5x3000x3000 render zarr (v2) + forward/reverse TIFFs at 9.362 um in a temp dir.
"""
import json, os, sys
import numpy as np, pytest, tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import read_chart as rc  # noqa: E402
import contact_sheet as cs  # noqa: E402
from test_rule55 import make_synthetic, to_u8, UM, SIDE, TEXT_UNITS  # noqa: E402
import rule55  # noqa: E402

KEY = "PHercTEST|synthetic_patch|0|ink9um_seed42+tta|both"


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    import zarr
    d = tmp_path_factory.mktemp("read")
    ct, fwd, rev = make_synthetic(seed=1)
    rng = np.random.default_rng(3)
    stack = np.stack([np.where(ct > 0, rng.normal(40 + 40 * k, 10, ct.shape).clip(1, 255), 0).astype(np.uint8)
                      for k in (0, 1, 2, 1, 0)])                     # crest at slice 2 = the mid slice
    stack[2] = ct
    g = zarr.open_group(str(d / "render.zarr"), mode="w", zarr_format=2)
    g.create_array("0", shape=stack.shape, chunks=(1, 1024, 1024), dtype="uint8",
                   chunk_key_encoding={"name": "v2", "separator": "/"}, compressors=None)
    g["0"][:] = stack
    tifffile.imwrite(str(d / "fwd.tif"), fwd); tifffile.imwrite(str(d / "fwd_reverse.tif"), rev)
    tifffile.imwrite(str(d / "mask.tif"), (ct > 0).astype(np.uint8) * 255)
    ledger = d / "LEDGER.md"
    ledger.write_text("# LEDGER.md\n\n## Reads (test)\n%s\n|%s\n\n## Throughput (daily)\n| date | x |\n|---|---|\n" % (rc.LEDGER_HEADER, "---|" * 10))
    return dict(dir=d, ct=ct, fwd=fwd, rev=rev, ledger=str(ledger))


def run(data, out, key=KEY, extra=()):
    argv = [str(data["dir"] / "render.zarr"), str(data["dir"] / "fwd.tif"), str(data["dir"] / "fwd_reverse.tif"),
            "--um", str(UM), "--out", str(out), "--key", key, "--ledger", data["ledger"], "--max-panel-px", "600"] + list(extra)
    return rc.main(argv)


def test_full_read_and_sheet(data):
    out = data["dir"] / "out1"
    assert run(data, out) == 0
    s = json.load(open(out / rc.STATS))
    assert s["assertions_failed"] == [] and s["onsheet_ct_std"] > 5 and s["onsheet_cm2"] > 0.5
    assert s["n_slices"] == 5 and s["crest_slice"] == 2 and len(s["slice_mean_profile"]) == 5
    assert s["verdict"] == "PROMISING CANDIDATE"                        # 6-unit cluster; rows are report-only
    h = s["rule55"]["units"]["0.5cm2"]
    assert h["n_flagged"] == 6 and h["largest_cluster"] == 6
    assert {(d["row"], d["col"]) for d in h["flagged"]} == TEXT_UNITS
    m = s["maps"]
    assert 0.33 < m["fwd_mean"] < 0.40 and 0.27 < m["rev_mean"] < 0.31 and m["fwd_minus_rev_mean"] > 0.05
    assert 0 <= m["fwd_frac_gt_0p75"] <= m["fwd_frac_gt_0p5"] <= 1
    assert "frac_in_elongated_marks" in s["bright_ink_in_render"] and s["bright_ink_in_render"]["flag_for_human_look"] is False
    # contact sheet: exists, bar length recorded and measurable in the PNG on every panel
    png = s["contact_sheet"]["path"]
    assert os.path.exists(png) and png.endswith(rc.SHEET)
    f = s["contact_sheet"]["shown_1_to"]
    assert f == 5 and s["contact_sheet"]["bar_px_at_map_scale"] == round(10000 / UM) == 1068
    bars = s["contact_sheet"]["bar_px_at_shown_scale"]
    assert len(bars) == 4 and all(b == round(10000 / (UM * f)) for b in bars.values())
    runs = cs.bar_run_lengths(png)
    assert runs and all(x == round(10000 / (UM * f)) for x in runs)
    # ledger line, marker, idempotent skip
    text = open(data["ledger"]).read()
    ekey = rc.escape_key(KEY)
    assert text.count("| %s |" % ekey) == 1 and "## Throughput" in text.split(ekey)[1]
    row = next(l for l in text.splitlines() if ekey in l)
    assert row.replace("\\|", "").count("|") == 11                    # 10 cells: the key's pipes are escaped
    assert os.path.exists(out / rc.MARKER)
    assert run(data, out) == 0 and open(data["ledger"]).read().count("| %s |" % ekey) == 1


def test_duplicate_key_refused_without_reason(data):
    with pytest.raises(SystemExit, match="REFUSED"):
        run(data, data["dir"] / "out2")
    assert run(data, data["dir"] / "out2", extra=["--reason", "re-read to check idempotence"]) == 0
    text = open(data["ledger"]).read()
    assert text.count("| %s |" % rc.escape_key(KEY)) == 2 and "reason: re-read to check idempotence" in text


def test_ledger_has_key_accepts_raw_older_lines(tmp_path):
    L = tmp_path / "L.md"
    L.write_text("## Reads\n%s\n|%s\n| 2026-01-01 | %s | - | - | - | - | - | - | BLANK | - |\n" % (rc.LEDGER_HEADER, "---|" * 10, KEY))
    assert rc.ledger_has_key(str(L), KEY) and not rc.ledger_has_key(str(L), KEY + "x")


def test_maps_only_mode(data):
    out = data["dir"] / "out3"
    argv = [str(data["dir"] / "mask.tif"), str(data["dir"] / "fwd.tif"), str(data["dir"] / "fwd_reverse.tif"), "--um", str(UM),
            "--out", str(out), "--key", KEY + "-mask", "--ledger", data["ledger"], "--maps-only", "--max-panel-px", "600"]
    assert rc.main(argv) == 0
    s = json.load(open(out / rc.STATS))
    assert s["maps_only"] and s["onsheet_ct_std"] is None and "bright_ink_in_render" not in s
    assert s["rule55"]["units"]["0.5cm2"]["n_flagged"] == 6 and os.path.exists(out / rc.SHEET)


def test_unreadable_when_too_little_sheet(data):
    d = data["dir"]
    tiny = np.zeros_like(data["ct"]); tiny[:300, :300] = 200                       # 0.08 cm^2
    tifffile.imwrite(str(d / "tiny_mask.tif"), tiny)
    argv = [str(d / "tiny_mask.tif"), str(d / "fwd.tif"), str(d / "fwd_reverse.tif"), "--um", str(UM), "--out", str(d / "out4"),
            "--key", KEY + "-tiny", "--ledger", data["ledger"], "--maps-only"]
    with pytest.raises(SystemExit) as e:
        rc.main(argv)
    assert e.value.code == 2
    s = json.load(open(d / "out4" / rc.STATS))
    assert s["verdict"] == "UNREADABLE" and "| UNREADABLE |" in open(data["ledger"]).read()
    import subprocess
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(rc.__file__), "read_chart.py")] + argv + ["--force", "--reason", "exit code check"],
                       capture_output=True, text=True)
    assert p.returncode == 2 and "UNREADABLE" in p.stderr


@pytest.mark.parametrize("len_mm,counted", [(2.2, True), (3.0, True), (3.9, True), (4.5, False), (1.5, False)])
def test_bright_ink_mark_length(len_mm, counted):
    """A one-pixel bright line of len_mm on a flat sheet is counted iff 2 <= len <= 4 mm (segment-length estimator)."""
    ct = np.full((1200, 1200), 100, np.uint8)
    n = int(round(len_mm * 1000.0 / UM))
    ct[600, 100:100 + n] = 255
    res = rc.bright_ink_check(ct, ct > 0, UM)
    assert (res["n_elongated_marks"] == 1) is counted
    if counted:
        assert abs(res["marks"][0]["length_mm"] - len_mm) < 0.1


def test_blank_only_map_gives_blank(data, tmp_path):
    ct, fwd, rev = make_synthetic(seed=2, blank_only=True)
    tifffile.imwrite(str(tmp_path / "f.tif"), fwd); tifffile.imwrite(str(tmp_path / "r.tif"), rev)
    tifffile.imwrite(str(tmp_path / "m.tif"), ct)
    argv = [str(tmp_path / "m.tif"), str(tmp_path / "f.tif"), str(tmp_path / "r.tif"), "--um", str(UM), "--out", str(tmp_path / "o"),
            "--key", KEY + "-blank", "--ledger", str(tmp_path / "L.md"), "--maps-only", "--max-panel-px", "400"]
    assert rc.main(argv) == 0
    s = json.load(open(tmp_path / "o" / rc.STATS))
    assert s["verdict"] == "BLANK" and "| BLANK |" in open(tmp_path / "L.md").read()


def test_cli_help():
    import subprocess
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(rc.__file__), "read_chart.py"), "-h"], capture_output=True, text=True)
    assert p.returncode == 0 and "--maps-only" in p.stdout


def test_flat_profile_render_is_void(data, tmp_path):
    """RULES R-CREST: a render whose per-slice on-sheet mean is flat (no crest) is VOID even if rule 5.5 says BLANK."""
    import zarr
    d = tmp_path / "flat"; d.mkdir()
    ct = data["ct"]
    stack = np.stack([ct] * 5)                                   # identical slices: crest ratio 1.00
    g = zarr.open_group(str(d / "render.zarr"), mode="w", zarr_format=2)
    g.create_array("0", shape=stack.shape, chunks=(1, 1024, 1024), dtype="uint8",
                   chunk_key_encoding={"name": "v2", "separator": "/"}, compressors=None)
    g["0"][:] = stack
    ledger = d / "LEDGER.md"; ledger.write_text(open(data["ledger"]).read())
    out = d / "out"
    rc.main([str(d / "render.zarr"), str(data["dir"] / "fwd.tif"), str(data["dir"] / "fwd_reverse.tif"), "--um", str(UM),
             "--out", str(out), "--key", "T|flat|0|k|both", "--ledger", str(ledger), "--max-panel-px", "400"])
    st = json.load(open(out / "read_stats.json"))
    assert st["verdict"] == "VOID" and st["crest_check"]["passed"] is False and st["crest_check"]["ratio"] < 1.01
    assert "VOID" in ledger.read_text()


def test_crest_check_controls():
    w040 = [73, 74, 74, 75, 75, 75, 76, 78, 82, 87, 93, 97, 99, 96, 88, 79, 70, 63, 58, 56, 56, 58, 59, 60, 61, 61, 61, 61]
    w028 = [62, 62, 63, 65, 67, 70, 74, 78, 81, 84, 84, 82, 78, 73, 69, 66, 64, 62, 62, 62, 62]
    flat = [107] * 10 + [108] * 18
    assert rc.crest_check(w040)["passed"] and rc.crest_check(w028)["passed"] and not rc.crest_check(flat)["passed"]
    edge = [50] * 27 + [120]                                     # crest on the last slice: not central
    assert not rc.crest_check(edge)["passed"]


def test_flag_on_either_grid_rules_out_blank(monkeypatch, tmp_path):
    """A unit flagged on the (0, 0) grid keeps a blank-looking chart out of BLANK even when the mask-origin grid flags nothing."""
    ct, fwd, rev = make_synthetic(seed=2, blank_only=True)
    tifffile.imwrite(str(tmp_path / "f.tif"), fwd); tifffile.imwrite(str(tmp_path / "r.tif"), rev); tifffile.imwrite(str(tmp_path / "m.tif"), ct)
    real, calls = rc.rule55.evaluate, {}
    def fake(f, r, on, um, row_check=True, unit_origin="fixed"):
        res, tables = real(f, r, on, um, row_check, unit_origin)
        if unit_origin == "fixed":
            res = json.loads(json.dumps(res)); u = res["units"]["0.5cm2"]
            u["n_flagged"] = 1; u["flagged"] = [dict(row=0, col=0, y0=0, x0=0, onsheet_frac=1.0, fwd_mean=0.41, rev_mean=0.30, margin=0.11, cluster=1)]
            res["verdict"], res["verdict_reason"] = "NOT ESTABLISHED", "1 flagged unit, largest cluster 1 (< 3)"
        calls[unit_origin] = res["verdict"]
        return res, tables
    monkeypatch.setattr(rc.rule55, "evaluate", fake)
    argv = [str(tmp_path / "m.tif"), str(tmp_path / "f.tif"), str(tmp_path / "r.tif"), "--um", str(UM), "--out", str(tmp_path / "o"),
            "--key", KEY + "-either", "--ledger", str(tmp_path / "L.md"), "--maps-only", "--max-panel-px", "400"]
    assert rc.main(argv) == 0
    st = json.load(open(tmp_path / "o" / rc.STATS))
    assert calls["auto"] == "BLANK" and calls["fixed"] == "NOT ESTABLISHED"
    assert st["verdict"] == "NOT ESTABLISHED" and "(0, 0)" in st["verdict_reason"] and st["rule55"]["flagged_any_grid"] == 1


def test_fixed_grid_area_shortfall_does_not_override_blank(monkeypatch, tmp_path):
    """A (0, 0)-grid NOT ESTABLISHED caused only by too few valid units must not override a BLANK on the mask grid."""
    ct, fwd, rev = make_synthetic(seed=2, blank_only=True)
    tifffile.imwrite(str(tmp_path / "f.tif"), fwd); tifffile.imwrite(str(tmp_path / "r.tif"), rev); tifffile.imwrite(str(tmp_path / "m.tif"), ct)
    real = rc.rule55.evaluate
    def fake(f, r, on, um, row_check=True, unit_origin="fixed"):
        res, tables = real(f, r, on, um, row_check, unit_origin)
        if unit_origin == "fixed":
            res = json.loads(json.dumps(res)); res["units"]["0.5cm2"]["n_valid"] = 2; res["units"]["0.5cm2"]["n_flagged"] = 0; res["units"]["0.5cm2"]["flagged"] = []
            res["verdict"], res["verdict_reason"] = "NOT ESTABLISHED", "no flagged unit but only 2 valid units"
        return res, tables
    monkeypatch.setattr(rc.rule55, "evaluate", fake)
    argv = [str(tmp_path / "m.tif"), str(tmp_path / "f.tif"), str(tmp_path / "r.tif"), "--um", str(UM), "--out", str(tmp_path / "o"),
            "--key", KEY + "-area", "--ledger", str(tmp_path / "L.md"), "--maps-only", "--max-panel-px", "400"]
    assert rc.main(argv) == 0
    st = json.load(open(tmp_path / "o" / rc.STATS))
    assert st["verdict"] == "BLANK" and st["rule55"]["flagged_any_grid"] == 0


def test_depth_swap_tripwire_is_recorded_and_changes_no_verdict(tmp_path):
    """RULES R-FLIP. A mirrored surface carrying ink would put its signal in the map we call 'reverse'. The swapped
    evaluation is recorded so that case cannot pass unnoticed; the ledger verdict stays the signed rule."""
    um = UM
    side = rule55.unit_side(um)
    n = side * 2
    fwd = np.full((n, n), 0.30, np.float32)
    rev = np.full((n, n), 0.30, np.float32)
    rev[:side, :side] = 0.50; fwd[:side, :side] = 0.20        # a MIRRORED inked unit: all the signal in 'reverse'
    onsheet = np.ones((n, n), bool)
    signed = rule55.evaluate(to_u8(fwd), to_u8(rev), onsheet, um, row_check=False, unit_origin="fixed")[0]
    swapped = rule55.evaluate(to_u8(rev), to_u8(fwd), onsheet, um, row_check=False, unit_origin="fixed")[0]
    assert signed["units"]["0.5cm2"]["n_flagged"] == 0        # the frozen signed rule sees nothing, as it must
    assert swapped["units"]["0.5cm2"]["n_flagged"] == 1       # the tripwire sees it
    assert signed["verdict"] != "PROMISING CANDIDATE"


# ------------------------------------------------- truncated-map guard (added 2026-09-19)

def test_truncated_reverse_map_is_refused(tmp_path, monkeypatch):
    """An inference that exits 0 with an incomplete map must not be scored. The real case left a reverse map non-zero on exactly
    one quadrant; the zeros where it had no prediction became a +0.60594 margin and an ADMITTED verdict out of nothing."""
    import subprocess, sys, os
    import numpy as np, tifffile
    n = 256
    fwd = np.full((n, n), 100, np.uint8)
    rev = np.zeros((n, n), np.uint8); rev[: n // 2, : n // 2] = 100      # one quadrant, as it happened
    mask = np.full((n, n), 255, np.uint8)
    f, r, m = (str(tmp_path / x) for x in ("f.tif", "r.tif", "mask.tif"))
    for p, arr in ((f, fwd), (r, rev), (m, mask)):
        tifffile.imwrite(p, arr)
    out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "read_chart.py"),
                          m, f, r, "--maps-only", "--um", "9.362", "--out", str(tmp_path / "out"),
                          "--key", "w|s|0|t|both", "--ledger", str(tmp_path / "L.md")],
                         capture_output=True, text=True)
    assert out.returncode != 0
    assert "truncated map" in (out.stdout + out.stderr).lower()


def test_a_complete_pair_is_not_refused_by_the_guard(tmp_path):
    """The guard is relative, so an auto-cropped surface whose maps are only partly non-zero must still pass."""
    import subprocess, sys, os
    import numpy as np, tifffile
    n = 256
    rng = np.random.default_rng(0)
    shape = np.zeros((n, n), bool); shape[40:200, 30:210] = True          # an irregular-ish footprint
    fwd = np.where(shape, rng.integers(60, 200, (n, n)), 0).astype(np.uint8)
    rev = np.where(shape, rng.integers(60, 200, (n, n)), 0).astype(np.uint8)
    mask = (shape * 255).astype(np.uint8)
    f, r, m = (str(tmp_path / x) for x in ("f.tif", "r.tif", "mask.tif"))
    for p, arr in ((f, fwd), (r, rev), (m, mask)):
        tifffile.imwrite(p, arr)
    out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "read_chart.py"),
                          m, f, r, "--maps-only", "--um", "9.362", "--out", str(tmp_path / "out"),
                          "--key", "w|s|0|t|both", "--ledger", str(tmp_path / "L.md")],
                         capture_output=True, text=True)
    assert "truncated map" not in (out.stdout + out.stderr).lower(), out.stdout + out.stderr
