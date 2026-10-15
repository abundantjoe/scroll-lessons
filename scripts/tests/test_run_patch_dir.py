"""Tests for scripts/run_patch_dir.py (MASTER_PROMPT_v4 5.11). Run: python -m pytest scripts/tests/test_run_patch_dir.py -q
Offline: subprocess.run is replaced by a fake that records argv and writes the files each stage would produce."""
import json, os, sys, tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import run_patch_dir as rpd  # noqa: E402

# never take the production inference lock from a test run: a real inference holds it for many minutes, and a test
# blocking on it would hang the suite (and, worse, look like a test failure)
rpd.INFER_LOCK = os.path.join(tempfile.gettempdir(), "hercules_test_infer.lock")

SCROLL, VOL, PITCH = "PHerc0306B", "20250521133212", "8.640um-1.2m-116keV"
META = {"scan": {"tomo": {"acquisition": {"detector": {"samplePixelSize": 0.00864}}}}}


@pytest.fixture
def catalogue(tmp_path):
    base = "%s/volumes/%s-%s-masked.zarr/" % (SCROLL, VOL, PITCH)
    cat = {"samples": {SCROLL: {"volumes": {VOL: {"properties": {"pixel_size_um": 8.64, "energy_keV": 116.0}, "data": [
        {"type": "surface-prediction-zarr", "origins": [{"path": "x/y.zarr/"}]}, {"type": "ome-zarr", "origins": [{"path": base}]}]}}}}}
    p = tmp_path / "cat.json"; p.write_text(json.dumps(cat)); return str(p)


def test_volume_info_from_metadata_and_catalogue(catalogue, tmp_path):
    urls = []
    info = rpd.volume_info(SCROLL, VOL, catalogue, fetch=lambda u: urls.append(u) or META, cache_dir=str(tmp_path / "vc_cache"))
    assert urls == ["https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/%s/volumes/%s-%s-masked.zarr/metadata.json" % (SCROLL, VOL, PITCH)]
    assert info["pitch"] == PITCH and info["um"] == pytest.approx(8.64) and info["catalogue_um"] == 8.64
    assert info["ct_url"].endswith("%s-%s-masked.zarr" % (VOL, PITCH))
    info2 = rpd.volume_info(SCROLL, VOL, catalogue, fetch=lambda u: pytest.fail("cached"), cache_dir=str(tmp_path / "vc_cache"))
    assert info2 == info
    bad = dict(META); bad["scan"] = {"tomo": {"acquisition": {"detector": {"samplePixelSize": 0.009362}}}}
    with pytest.raises(SystemExit, match="voxel size mismatch"):
        rpd.volume_info(SCROLL, VOL, catalogue, fetch=lambda u: bad)


def test_command_builders(tmp_path):
    info = dict(scroll=SCROLL, vol=VOL, pitch=PITCH, um=8.64, ct_url="https://x/y.zarr")
    patch = str(tmp_path / "auto_grown_1")
    assert rpd.infer_cmd("/r/render.zarr", "/m/step-075000.pth", "/o/map.tif") == [
        sys.executable, "-m", "vesuvius.ink_detection.inference.infer", "/r/render.zarr", "/m/step-075000.pth", "/o/map.tif",
        "--direction", "both", "--tta-mirror", "--batch-size", "4", "--no-compile", "--num-workers", rpd.INFER_WORKERS]
    assert rpd.render_cmd(info, patch) == [rpd.VC_TOOLS, "render", SCROLL, VOL, PITCH, "8.64", patch, os.path.join(patch, "render.zarr")]
    assert rpd.qc_cmd(patch, 8.64, "https://x/y.zarr", "/c", "/o.png") == [
        sys.executable, rpd.PATCH_QC, patch, "--um", "8.64", "--ct-url", "https://x/y.zarr", "--cache", "/c", "--overlay", "/o.png"]
    assert rpd.read_cmd("/r.zarr", "/f.tif", "/f_reverse.tif", 8.64, "/out", "k|a|0|t|both", "/L.md") == [
        sys.executable, rpd.READ_CHART, "/r.zarr", "/f.tif", "/f_reverse.tif", "--um", "8.64", "--out", "/out", "--key", "k|a|0|t|both", "--ledger", "/L.md"]
    assert rpd.ledger_key(SCROLL, patch + "/") == "PHerc0306B|auto_grown_1|0|ink9um_seed42+tta|both"
    fwd, rev = rpd.map_paths(patch, "ink9um_seed42+tta")
    assert fwd == os.path.join(patch, "read_ink9um_seed42_tta", "ink9um_seed42_tta.tif") and rev == fwd[:-4] + "_reverse.tif"
    assert rpd.read_dir(patch, "other+x") == os.path.join(patch, "read_other_x")


class FakeRun:
    """Stands in for subprocess.run: records argv and produces the side effects of each stage."""
    def __init__(self, qc_verdict="PASS", read_rc=0):
        self.calls, self.qc_verdict, self.read_rc = [], qc_verdict, read_rc

    def __call__(self, cmd, **kw):
        self.calls.append(cmd); rc = 0
        if cmd[1] == rpd.PATCH_QC:
            open(os.path.join(cmd[2], ".qc_done"), "w").write(self.qc_verdict + "\n")
        elif cmd[0] == rpd.VC_TOOLS:
            os.makedirs(os.path.join(cmd[7], "0")); open(os.path.join(cmd[7], "0", "0.0.0"), "wb").write(b"\1" * 1_000_000)
        elif cmd[1:3] == ["-m", "vesuvius.ink_detection.inference.infer"]:
            open(cmd[5], "wb").write(b"f"); open(cmd[5][:-4] + "_reverse.tif", "wb").write(b"r")
        elif cmd[1] == rpd.READ_CHART:
            out = cmd[cmd.index("--out") + 1]; os.makedirs(out, exist_ok=True); rc = self.read_rc
            json.dump({"verdict": "BLANK" if rc == 0 else "UNREADABLE", "onsheet_cm2": 3.21}, open(os.path.join(out, "read_stats.json"), "w"))
            open(os.path.join(out, ".read_complete"), "w").write("x")
            with open(cmd[cmd.index("--ledger") + 1], "a") as fh:
                fh.write("| d | %s | ... |\n" % cmd[cmd.index("--key") + 1])
        return type("R", (), {"returncode": rc})()


@pytest.fixture
def setup(tmp_path, monkeypatch):
    fake = FakeRun(); monkeypatch.setattr(rpd.subprocess, "run", fake)
    # the fake render dirs hold no zarr: the R-CREST pre-check is stubbed to PASS here and exercised in test_crest_void
    monkeypatch.setattr(rpd, "crest_precheck", lambda render, um: ({"passed": True, "ratio": 1.8, "crest_slice": 13, "reason": None}, [1.0] * 28, 4.0))
    patches = tmp_path / "patches"; (patches / "auto_grown_a").mkdir(parents=True); (patches / "auto_grown_b").mkdir(); (patches / "other").mkdir()
    ledger = tmp_path / "LEDGER.md"; ledger.write_text("# LEDGER.md\n\n## Reads\n| date | key |\n|---|---|\n")
    info = dict(scroll=SCROLL, vol=VOL, pitch=PITCH, um=8.64, ct_url="https://x/y.zarr")
    # a unit test must never depend on how much free disk the machine happens to have: the render floor added on
    # 2026-09-18 made ten tests fail whenever the real disk dipped under 5 GB, which is exactly the situation the
    # floor exists for. Tests that want to exercise the floor set it themselves (monkeypatch).
    rpd.MIN_FREE_RENDER_GB = 0.0
    return dict(fake=fake, patches=patches, ledger=str(ledger), info=info, records=str(tmp_path / "records" / "throughput.jsonl"), cache=str(tmp_path / "cache"))


def test_full_chain_markers_and_throughput(setup):
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    msg = rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], delete_renders=True, cache=s["cache"])
    assert msg == "done: BLANK 3.21 cm^2"
    kinds = [(c[1] if c[0] == sys.executable else c[0]) for c in s["fake"].calls]
    assert kinds == [rpd.PATCH_QC, rpd.VC_TOOLS, "-m", rpd.READ_CHART]
    assert s["fake"].calls[2] == rpd.infer_cmd(os.path.join(p, "render.zarr"), "/ck.pth", os.path.join(p, "read_ink9um_seed42_tta", "ink9um_seed42_tta.tif"))
    for m in (".qc_done", ".infer_complete_ink9um_seed42+tta", "read_ink9um_seed42_tta/.read_complete"):
        assert os.path.exists(os.path.join(p, m)), m
    assert not os.path.exists(os.path.join(p, "render.zarr"))           # --delete-renders after a successful read
    # ... and BOTH completion markers of that render go with it (ours and the one vc_tools.sh writes). A marker left
    # behind by --delete-renders made vc_tools report "complete" and render nothing on a re-read, and the read then
    # died on a missing render.zarr.
    assert not os.path.exists(os.path.join(p, ".render_complete"))
    assert not os.path.exists(os.path.join(p, "render.zarr.complete"))
    rec = [json.loads(l) for l in open(s["records"])]
    assert len(rec) == 1 and rec[0]["cm2_read"] == 3.21 and rec[0]["charts"] == 1 and rec[0]["render_mb"] == 1.0 and rec[0]["render_deleted"]
    assert rec[0]["key"] == "PHerc0306B|auto_grown_a|0|ink9um_seed42+tta|both" and rec[0]["mb_per_s"] is not None
    # rerun: everything is skipped from the read marker / ledger, nothing is run
    n = len(s["fake"].calls)
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]).startswith("skip: already read / ledgered")
    assert len(s["fake"].calls) == n and len(open(s["records"]).read().splitlines()) == 1


def test_partial_markers_resume_at_the_right_stage(setup):
    s, p = setup, str(setup["patches"] / "auto_grown_b")
    open(os.path.join(p, ".qc_done"), "w").write("PASS\n"); open(os.path.join(p, ".render_complete"), "w").write("x\n")
    os.makedirs(os.path.join(p, "render.zarr", "0"))
    msg = rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"])
    # QC is always re-invoked (patch_qc is idempotent and upgrades a stale geometry-only PASS); render is skipped by its marker
    assert msg.startswith("done") and [c[2] if c[0] == sys.executable and c[1] == "-m" else c[1] for c in s["fake"].calls] == [
        rpd.PATCH_QC, "vesuvius.ink_detection.inference.infer", rpd.READ_CHART]
    assert os.path.isdir(os.path.join(p, "render.zarr"))                # kept without --delete-renders


def test_stale_geometry_only_qc_is_rerun_and_can_turn_unreadable(setup):
    s, p = setup, str(setup["patches"] / "auto_grown_b")
    open(os.path.join(p, ".qc_done"), "w").write("PASS\n"); s["fake"].qc_verdict = "UNREADABLE"
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]) == "stop: qc UNREADABLE"
    assert len(s["fake"].calls) == 1 and not os.path.exists(os.path.join(p, ".render_complete"))


def test_second_tag_is_skipped_by_the_screening_loop_unless_reread(setup, monkeypatch):
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]).startswith("done")
    n = len(s["fake"].calls)
    msg = rpd.process_patch(p, s["info"], "/ck2.pth", "ink9um_seed7+tta", s["ledger"], s["records"], cache=s["cache"])
    assert msg.startswith("skip: already read under read_ink9um_seed42_tta") and len(s["fake"].calls) == n


def test_plain_inference_drops_tta_mirror():
    assert "--tta-mirror" in rpd.infer_cmd("r", "c", "o", tta=True) and "--tta-mirror" not in rpd.infer_cmd("r", "c", "o", tta=False)


def test_second_tag_is_a_fresh_read_of_the_same_render_with_reread(setup, monkeypatch):
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]).startswith("done")
    n = len(s["fake"].calls)
    monkeypatch.setattr(rpd, "REREAD", True)
    msg = rpd.process_patch(p, s["info"], "/ck2.pth", "ink9um_seed7+tta", s["ledger"], s["records"], cache=s["cache"])
    assert msg.startswith("done")
    kinds = [(c[1] if c[0] == sys.executable else c[0]) for c in s["fake"].calls[n:]]
    assert kinds == [rpd.PATCH_QC, "-m", rpd.READ_CHART]                # render reused, inference + read redone under the new tag
    assert os.path.exists(os.path.join(p, "read_ink9um_seed7_tta", ".read_complete")) and os.path.exists(os.path.join(p, ".infer_complete_ink9um_seed7+tta"))
    keys = [json.loads(l)["key"] for l in open(s["records"])]
    assert keys == ["PHerc0306B|auto_grown_a|0|ink9um_seed42+tta|both", "PHerc0306B|auto_grown_a|0|ink9um_seed7+tta|both"]


def test_ledgered_key_is_skipped_before_any_work(setup):
    s, p = setup, str(setup["patches"] / "auto_grown_b")
    with open(s["ledger"], "a") as fh:
        fh.write("| 2026-09-16 | %s | 0.3 |\n" % rpd.ledger_key(SCROLL, p))
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]).startswith("skip")
    assert s["fake"].calls == [] and not os.path.exists(os.path.join(p, ".qc_done"))


@pytest.mark.parametrize("verdict", ["FAIL", "UNREADABLE"])
def test_qc_fail_or_unreadable_stops_before_render(setup, verdict):
    s, p = setup, str(setup["patches"] / "auto_grown_a"); s["fake"].qc_verdict = verdict
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]) == "stop: qc " + verdict
    assert len(s["fake"].calls) == 1 and not os.path.exists(os.path.join(p, ".render_complete")) and not os.path.exists(s["records"])


@pytest.mark.parametrize("rc", [1, 2])
def test_read_unreadable_nonzero_exit_is_recorded(setup, rc):
    """read_chart signals UNREADABLE with a non-zero exit but has written stats + marker + ledger line: that is a completed read."""
    s, p = setup, str(setup["patches"] / "auto_grown_a"); s["fake"].read_rc = rc
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]) == "done: UNREADABLE 3.21 cm^2"
    assert json.loads(open(s["records"]).read())["verdict"] == "UNREADABLE"


def test_read_crash_without_stats_is_an_error(setup, monkeypatch):
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    orig = s["fake"].__call__
    def crash(cmd, **kw):
        if cmd[1] == rpd.READ_CHART:
            return type("R", (), {"returncode": 1})()
        return orig(cmd, **kw)
    monkeypatch.setattr(rpd.subprocess, "run", crash)
    assert rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], cache=s["cache"]).startswith("ERROR: read failed rc=1")
    assert not os.path.exists(s["records"])


def test_main_cli(setup, catalogue, tmp_path, monkeypatch):
    monkeypatch.setattr(rpd.requests, "get", lambda u, timeout=0: type("R", (), {"json": lambda self: META})())
    rc = rpd.main([str(setup["patches"]), "--scroll", SCROLL, "--vol", VOL, "--catalogue", catalogue, "--ledger", setup["ledger"],
                   "--records", setup["records"], "--data-root", str(tmp_path / "data"), "--only", "auto_grown_b"])
    assert rc == 0 and len(setup["fake"].calls) == 4 and os.path.exists(tmp_path / "data" / "vc_cache" / SCROLL / (VOL + "-metadata.json"))
    with pytest.raises(SystemExit) as e:
        rpd.main(["-h"])
    assert e.value.code == 0


def test_crest_void_skips_inference(setup, monkeypatch):
    """RULES R-CREST pre-check: a flat-profile render is VOID, ledgered, marked, and the 5.1 call never runs."""
    st, p = setup, str(setup["patches"] / "auto_grown_a")
    flat = ({"passed": False, "ratio": 1.01, "crest_slice": 27, "reason": "render not centred on a sheet: crest ratio 1.01"}, [107.0] * 28, 4.7)
    monkeypatch.setattr(rpd, "crest_precheck", lambda render, um: flat)
    out = rpd.process_patch(p, st["info"], "/ck.pth", rpd.TAG, st["ledger"], st["records"], delete_renders=True, cache=st["cache"])
    assert out.startswith("VOID")
    assert not any("inference.infer" in " ".join(c) for c in st["fake"].calls), "inference must not run on a VOID render"
    rd = rpd.read_dir(p, rpd.TAG)
    stats = json.load(open(os.path.join(rd, rpd.read_chart.STATS)))
    assert stats["verdict"] == "VOID" and os.path.exists(os.path.join(rd, rpd.read_chart.MARKER))
    assert "VOID" in open(st["ledger"]).read() and rpd.read_chart.ledger_has_key(st["ledger"], rpd.ledger_key(st["info"]["scroll"], p, rpd.TAG))
    rec = [json.loads(l) for l in open(st["records"])]
    assert rec[-1]["verdict"] == "VOID" and rec[-1]["charts"] == 0 and rec[-1]["cm2_read"] == 0.0
    # rerun is a skip
    assert rpd.process_patch(p, st["info"], "/ck.pth", rpd.TAG, st["ledger"], st["records"], cache=st["cache"]).startswith("skip")


def test_stale_render_markers_are_dropped_before_a_reread(setup, monkeypatch):
    """A re-read of a patch whose render was deleted must render again, not trust a leftover marker."""
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    for m in (".render_complete", "render.zarr.complete"):
        open(os.path.join(p, m), "w").write("stale\n")
    assert not os.path.isdir(os.path.join(p, "render.zarr"))
    monkeypatch.setattr(rpd, "REREAD", True)
    rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], delete_renders=False, cache=s["cache"])
    assert rpd.VC_TOOLS in [(c[1] if c[0] == sys.executable else c[0]) for c in s["fake"].calls]


def test_a_published_render_is_refetched_not_rerendered(setup, monkeypatch):
    """Where the team published the render, provenance belongs to them: a missing render stops the patch with a
    pointer to the fetcher instead of quietly substituting one of ours under the same ledger key."""
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    open(os.path.join(p, "render_source.json"), "w").write('{"bucket_prefix": "x/"}')
    monkeypatch.setattr(rpd, "REREAD", True)
    msg = rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], delete_renders=False, cache=s["cache"])
    assert "published render deleted" in msg and rpd.VC_TOOLS not in [(c[1] if c[0] == sys.executable else c[0]) for c in s["fake"].calls]


def test_a_render_does_not_start_below_the_disk_floor(setup, monkeypatch):
    """A render is the largest write in the pipeline; starting one on a nearly full disk wedges the box. The patch is
    skipped and the loop comes back, rather than the disk guard cleaning up after a half-written stack."""
    s, p = setup, str(setup["patches"] / "auto_grown_a")
    monkeypatch.setattr(rpd, "MIN_FREE_RENDER_GB", 1e9)
    msg = rpd.process_patch(p, s["info"], "/ck.pth", rpd.TAG, s["ledger"], s["records"], delete_renders=False, cache=s["cache"])
    assert "render floor" in msg
    assert rpd.VC_TOOLS not in [(c[1] if c[0] == sys.executable else c[0]) for c in s["fake"].calls]


def test_consensus_surfaces_are_enumerated(tmp_path):
    """vc_grow_seg_from_segments names its result auto_trace_*; enumerating only auto_grown_/team_ skipped every
    consensus surface silently, including the one that met G-GP part 4's milestone 2."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_patch_dir.py")).read()
    block = src.split("dirs = sorted(", 1)[1].split("if a.only:", 1)[0]
    for prefix in ("auto_grown_", "auto_trace_", "team_"):
        assert prefix in block, "%s is not enumerated by the reader" % prefix


def test_only_that_names_a_missing_patch_fails_loudly():
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_patch_dir.py")).read()
    tail = src.split("if a.only:", 1)[1][:600]
    assert "sys.exit" in tail, "--only naming nothing must fail, not read zero patches silently"
    assert "not present in" in tail


# ---------------------------------------------------------------- RULES R-DEPTH windows (ADMITTED 2026-09-19)

def test_depth_windows_lock_the_layer_args_to_the_ledger_offset():
    """The whole point of the table: a read can never be filed under an offset it did not use."""
    assert rpd.DEPTH_WINDOWS["centre"]["layers"] == () and rpd.DEPTH_WINDOWS["centre"]["offset"] == "0"
    assert rpd.DEPTH_WINDOWS["low"]["layers"] == ("--layer-start", "0", "--layer-end", "17")
    assert rpd.DEPTH_WINDOWS["low"]["offset"] == "-6"
    assert rpd.DEPTH_WINDOWS["high"]["layers"] == ("--layer-start", "11", "--layer-end", "28")
    assert rpd.DEPTH_WINDOWS["high"]["offset"] == "+5"


def test_ledger_key_carries_the_window_offset():
    patch = "/d/PHerc0306B/auto_grown_1"
    assert rpd.ledger_key(SCROLL, patch) == "PHerc0306B|auto_grown_1|0|ink9um_seed42+tta|both"
    assert rpd.ledger_key(SCROLL, patch, window="high") == "PHerc0306B|auto_grown_1|+5|ink9um_seed42+tta|both"
    assert rpd.ledger_key(SCROLL, patch, window="low") == "PHerc0306B|auto_grown_1|-6|ink9um_seed42+tta|both"


def test_infer_cmd_appends_the_window_layer_args_and_keeps_the_rest_of_the_5_1_call():
    base = rpd.infer_cmd("/r/render.zarr", "/m/c.pth", "/o/m.tif", tta=False)
    hi = rpd.infer_cmd("/r/render.zarr", "/m/c.pth", "/o/m.tif", tta=False, window="high")
    assert "--layer-start" not in base
    assert hi[hi.index("--layer-start") + 1] == "11" and hi[hi.index("--layer-end") + 1] == "28"
    for flag in ("--direction", "--batch-size", "--no-compile", "--num-workers"):
        assert flag in hi
    assert [x for x in hi if x not in ("--layer-start", "11", "--layer-end", "28")] == base


def test_dir_tag_keeps_the_centre_name_and_separates_the_off_centre_windows():
    """CENTRE must keep the historical directory so no read already on disk is orphaned or re-run."""
    assert rpd.dir_tag("ink9um_seed42+plain") == "ink9um_seed42+plain"
    assert rpd.dir_tag("ink9um_seed42+plain", "high") == "ink9um_seed42+plain+dp5"
    assert rpd.dir_tag("ink9um_seed42+plain", "low") == "ink9um_seed42+plain+dm6"
    for w in ("centre", "low", "high"):
        assert len({rpd.dir_tag("t", x) for x in ("centre", "low", "high")}) == 3


def test_off_centre_read_dirs_and_maps_cannot_collide_with_the_centre_read():
    p = "/d/PHerc0306B/auto_grown_1"
    dirs = {rpd.read_dir(p, rpd.dir_tag("ink9um_seed42+plain", w)) for w in ("centre", "low", "high")}
    maps = {rpd.map_paths(p, rpd.dir_tag("ink9um_seed42+plain", w))[0] for w in ("centre", "low", "high")}
    assert len(dirs) == 3 and len(maps) == 3


# ---------- global inference slot cap (added 2026-09-19 after two truncated reverse passes under load)

def test_a_global_slot_cap_exists_and_defaults_to_two():
    assert rpd.INFER_SLOTS == 2
    assert rpd.SLOT_DIR.endswith(os.path.join("logs", "infer_slots"))


def test_slots_are_exclusive_and_block_beyond_the_cap(tmp_path, monkeypatch):
    """Seven scripts pass seven different named locks, so only a global cap actually bounds concurrency."""
    monkeypatch.setattr(rpd, "SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setattr(rpd, "INFER_SLOTS", 2)
    a = rpd.acquire_slot()
    b = rpd.acquire_slot()
    assert a.name != b.name, "two holders must occupy two different slots"
    import threading
    got = []
    t = threading.Thread(target=lambda: got.append(rpd.acquire_slot()), daemon=True)
    t.start(); t.join(timeout=1.0)
    assert not got, "a third inference must wait while both slots are held"
    a.close()
    t.join(timeout=15.0)
    assert got, "the waiter must proceed once a slot is released"
    for fh in [b] + got:
        fh.close()


def test_the_stage_helper_takes_a_slot_before_the_named_lock():
    import inspect
    src = inspect.getsource(rpd.stage)
    assert "acquire_slot()" in src
    assert src.index("acquire_slot()") < src.index("fcntl.flock(fh"), "the global cap comes first"
    assert "slot.close()" in src, "the slot must be released even when the command fails"


def test_worker_count_is_configurable_and_defaults_to_two():
    """Dataloader workers change throughput only - the maps are identical - but each is a process, and an inference
    died on 2026-09-19 leaving leaked semaphores, the signature of workers killed under pressure."""
    assert rpd.INFER_WORKERS == "2"
    assert "--num-workers" in rpd.infer_cmd("r", "c", "o")
