"""Tests for scripts/review_folder.py (MASTER_PROMPT_v4 5.12). Run: python -m pytest scripts/tests/test_review_folder.py -q
Offline: a synthetic reads root with two fake reads (one eligible BLANK in the read_chart.py schema, one ineligible
control in the flat schema), 1200x1200 maps at 9.362 um.
"""
import json, os, sys, time
import numpy as np, pytest, tifffile, cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import review_folder as rf  # noqa: E402
import contact_sheet as cs  # noqa: E402

UM, N = 9.362, 1200
BAR = round(10000 / UM)   # 1068


def fake_read(d, key, scroll_flat=None, verdict="BLANK", fwd_level=0.30, margin=0.0, cluster=0, ink_block=False, marker=True,
              unreadable=False, rev_shape=None):
    """Write a read directory: render.zarr (3 slices), fwd/rev tifs, a contact sheet png, a stats file (+ .read_complete)."""
    import zarr
    os.makedirs(d, exist_ok=True)
    rng = np.random.default_rng(0)
    ct = rng.normal(120, 20, (N, N)).clip(1, 255).astype(np.uint8); ct[:, :100] = 0        # off-sheet strip
    g = zarr.open_group(os.path.join(d, "render.zarr"), mode="w", zarr_format=2)
    g.create_array("0", shape=(3, N, N), chunks=(1, 512, 512), dtype="uint8",
                   chunk_key_encoding={"name": "v2", "separator": "/"}, compressors=None)
    g["0"][:] = np.stack([ct, ct, ct])
    fwd = rng.normal(fwd_level, 0.02, (N, N)); rev = rng.normal(fwd_level - margin, 0.02, (N, N))
    if ink_block:
        fwd[200:400, 200:400] = 0.8; rev[200:400, 200:400] = 0.3                            # purple region (margin 0.5)
        fwd[600:800, 600:800] = 0.8; rev[600:800, 600:800] = 0.75                           # NOT purple (margin 0.05)
    tifffile.imwrite(os.path.join(d, "fwd.tif"), (fwd.clip(0, 1) * 255).astype(np.uint8))
    rev8 = (rev.clip(0, 1) * 255).astype(np.uint8)
    tifffile.imwrite(os.path.join(d, "fwd_reverse.tif"), rev8 if rev_shape is None else rev8[:rev_shape[0], :rev_shape[1]])
    sheet = np.zeros((50, 80, 3), np.uint8); cv2.imwrite(os.path.join(d, "contact_sheet.png"), sheet)
    if scroll_flat is None:      # read_chart.py schema
        stats = dict(key=key, um_per_px=UM, verdict=verdict, maps_only=False,
                     inputs=dict(render="render.zarr", forward="fwd.tif", reverse="fwd_reverse.tif"),
                     maps=dict(fwd_mean=fwd_level, rev_mean=fwd_level - margin, fwd_frac_gt_0p5=0.001, fwd_frac_gt_0p75=0.0),
                     rule55=dict(units={"0.5cm2": dict(n_flagged=cluster, n_valid=2, largest_cluster=cluster), "1cm2": dict(n_flagged=0)}),
                     contact_sheet=dict(path=os.path.join(d, "contact_sheet.png")))
        if unreadable:                                    # read_chart.py: key/um/verdict only, no maps/rule55/contact_sheet
            stats = dict(key=key, um_per_px=UM, verdict="UNREADABLE", maps_only=False, verdict_reason="on-sheet 0.1 cm^2 < 0.5",
                         inputs=dict(render="render.zarr", forward="fwd.tif", reverse="fwd_reverse.tif"))
        name = "read_stats.json"
        if marker:
            open(os.path.join(d, ".read_complete"), "w").write(stats["verdict"] + "\n")
    else:
        stats = dict(scroll=scroll_flat, surface=key, verdict=verdict, um=UM, fwd_mean=fwd_level, rev_mean=fwd_level - margin,
                     frac_gt_05=0.2, frac_gt_075=0.05, flagged_05=cluster, largest_cluster_05=cluster, flagged_1=1,
                     sheet_png="contact_sheet.png", forward_tif="fwd.tif", reverse_tif="fwd_reverse.tif", render_zarr="render.zarr", eligible=False)
        name = "stats.json"
    json.dump(stats, open(os.path.join(d, name), "w"))
    return d


@pytest.fixture(scope="module")
def root(tmp_path_factory):
    r = tmp_path_factory.mktemp("reads")
    fake_read(str(r / "PHerc0175A" / "seg_a"), "PHerc0175A|seg_a|0|ink9um_seed42+tta|both", verdict="BLANK", ink_block=True)
    fake_read(str(r / "controls" / "w040"), "w040_crop", scroll_flat="PHerc0139", verdict="NOT ESTABLISHED", fwd_level=0.40, margin=0.12, cluster=3)
    return r


def test_build_and_index(root, tmp_path):
    out = str(tmp_path / "review_sheets")
    s = rf.run_once(str(root), out)
    assert s["n_reads"] == 2 and s["n_eligible"] == 1 and s["sheets_copied"] == 2 and s["overlays_built"] == 1
    assert os.path.exists(os.path.join(out, "eligible", "PHerc0175A__seg_a__BLANK.png"))
    assert os.path.exists(os.path.join(out, "ineligible", "PHerc0139__w040_crop__NOT_ESTABLISHED.png"))
    assert not os.path.exists(os.path.join(out, "eligible", "overlays", "PHerc0139__w040_crop_overlay.png"))
    assert os.path.exists(os.path.join(out, ".review_complete"))
    idx = open(os.path.join(out, "INDEX.md")).read().splitlines()
    rows = [l for l in idx if l.startswith("| PHerc")]
    assert len(rows) == 2 and rows[0].startswith("| PHerc0139 | w040_crop | NOT ESTABLISHED | no |")   # cluster 3 sorts first
    assert rows[1].startswith("| PHerc0175A | seg_a | BLANK | yes |")
    assert "| 3/-" in rows[0] and "| 3 |" in rows[0] and "| 0.1200 |" in rows[0]
    assert "eligible/overlays/PHerc0175A__seg_a_overlay.png" in rows[1]
    # overlay: bar length exactly round(10000/um) on every panel, thresholds and fractions recorded
    opng = os.path.join(out, "eligible", "overlays", "PHerc0175A__seg_a_overlay.png")
    nums = json.load(open(opng[:-4] + ".json"))
    assert nums["bar_px_at_map_scale"] == BAR == 1068 and nums["shown_1_to"] == 1
    assert set(nums["bar_px_in_png"].values()) == {BAR}
    runs = cs.bar_run_lengths(opng)
    assert len(runs) == 8 and set(runs) == {BAR}          # bars are 8 rows tall, all three on the same rows, every run exactly 1068 px
    assert nums["overlay_thresholds"] == dict(forward_gt=0.5, margin_gt=0.10) and nums["diverging_limit"] == 0.3
    assert 0.02 < nums["purple_frac_of_onsheet"] < 0.04 and nums["purple_px"] == 200 * 200 and nums["n_slices"] == 3
    img = cv2.imread(opng)
    assert img.shape[1] >= 3 * N and "eyes only" in open(opng[:-4] + ".json").read()
    # purple applied where fwd>0.5 & fwd-rev>0.10 (block 200:400), NOT where margin is 0.05 (block 600:800), NOT in the background
    import zarr
    ct = np.asarray(zarr.open_group(str(root / "PHerc0175A" / "seg_a" / "render.zarr"), mode="r")["0"][1])
    grey = cs.gray_to_bgr(ct)
    purple = (grey.astype(np.float32) * (1 - rf.PURPLE_ALPHA) + np.array(rf.PURPLE_BGR, np.float32) * rf.PURPLE_ALPHA).astype(np.uint8)
    y = cs.TITLE_H + cs.HEADER_H
    px = lambda r, c: tuple(int(v) for v in img[y + r, c])
    assert px(300, 300) == tuple(int(v) for v in purple[300, 300]) and px(300, 300) != tuple(int(v) for v in grey[300, 300])
    assert px(700, 700) == tuple(int(v) for v in grey[700, 700])
    assert px(1000, 300) == tuple(int(v) for v in grey[1000, 300])
    assert px(300, 300) != px(700, 700)


def test_unreadable_read_parsed(tmp_path):
    r = tmp_path / "reads"
    fake_read(str(r / "PHerc0800" / "segX"), "PHerc0800|segX|0|ink9um_seed42|both", unreadable=True)
    out = str(tmp_path / "rs"); s = rf.run_once(str(r), out)
    assert s["n_reads"] == 1 and s["n_eligible"] == 1
    rows = [l for l in open(os.path.join(out, "INDEX.md")).read().splitlines() if l.startswith("| PHerc")]
    assert rows[0].startswith("| PHerc0800 | segX | UNREADABLE | yes | 9.3620 | - | - | - |")
    assert "None" not in rows[0]


def test_bad_read_does_not_kill_pass(tmp_path):
    r = tmp_path / "reads"
    fake_read(str(r / "PHerc0800" / "bad"), "PHerc0800|bad|0|ink9um_seed42|both", rev_shape=(600, 600))      # shape mismatch
    fake_read(str(r / "PHerc0800" / "inprogress"), "PHerc0800|inprogress|0|ink9um_seed42|both", marker=False)  # no marker yet
    fake_read(str(r / "PHerc0800" / "good"), "PHerc0800|good|0|ink9um_seed42|both")
    out = str(tmp_path / "rs"); s = rf.run_once(str(r), out)
    assert s["n_reads"] == 2 and s["overlays_built"] == 1 and os.path.exists(os.path.join(out, "INDEX.md"))
    rows = [l for l in open(os.path.join(out, "INDEX.md")).read().splitlines() if l.startswith("| PHerc")]
    assert any("| bad |" in l and l.rstrip().endswith("| - |") for l in rows) and not any("inprogress" in l for l in rows)


def test_same_segment_two_reads_do_not_collide(tmp_path):
    r = tmp_path / "reads"
    fake_read(str(r / "PHerc0800" / "seg1_a"), "PHerc0800|seg1|0|ink9um_seed42|both")
    fake_read(str(r / "PHerc0800" / "seg1_b"), "PHerc0800|seg1|8|ink9um_seed43+tta|both")
    out = str(tmp_path / "rs"); s = rf.run_once(str(r), out)
    assert s["overlays_built"] == 2 and s["sheets_copied"] == 2
    ov = sorted(os.listdir(os.path.join(out, "eligible", "overlays")))
    assert ov == ["PHerc0800__seg1__0_ink9um_seed42_both_overlay.json", "PHerc0800__seg1__0_ink9um_seed42_both_overlay.png",
                  "PHerc0800__seg1__8_ink9um_seed43_tta_both_overlay.json", "PHerc0800__seg1__8_ink9um_seed43_tta_both_overlay.png"]
    assert len([f for f in os.listdir(os.path.join(out, "eligible")) if f.endswith(".png")]) == 2


def test_idempotent_by_mtime(root, tmp_path):
    out = str(tmp_path / "rs")
    rf.run_once(str(root), out)
    s2 = rf.run_once(str(root), out)
    assert s2["sheets_copied"] == 0 and s2["overlays_built"] == 0
    f = str(root / "PHerc0175A" / "seg_a" / "fwd.tif")
    time.sleep(0.05); os.utime(f, None)
    s3 = rf.run_once(str(root), out)
    assert s3["overlays_built"] == 1 and s3["sheets_copied"] == 0


def test_cli_help():
    with pytest.raises(SystemExit) as e:
        rf.main(["-h"])
    assert e.value.code == 0
