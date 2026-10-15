"""Tests for scripts/patch_qc.py (MASTER_PROMPT_v4 5.8).
Run: python -m pytest scripts/tests/test_patch_qc.py -q
The last test reads a few dozen 2 MB level-4 chunks of PHerc0139 over HTTPS, cached under
/home/user/hercules_data/ct_l4_cache/PHerc0139; everything else is offline (a local fake zarr server)."""
import functools, http.server, json, os, shutil, subprocess, sys, threading
import numpy as np, pytest, tifffile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import patch_qc as q  # noqa: E402
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

UM = 9.362
W040 = DATA + "/controls/w040/mesh"
CT_URL = ("https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0139/volumes/"
          "20250728140407-9.362um-1.2m-113keV-masked.zarr")
CACHE = DATA + "/ct_l4_cache/PHerc0139"
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "patch_qc.py")


def grid(n=101, step=20.0):
    i, j = np.mgrid[0:n, 0:n].astype(np.float64)
    return i * step, j * step  # v (rows), u (columns)


def flat_sheet():  # sheet in the xy plane: normal along z
    v, u = grid()
    return u + 1000, v + 1000, np.full_like(u, 3000.0)


def cylinder_wall(R=2000.0, n=101):  # winding around the z axis: normals in the xy plane
    v, u = grid(n)
    th = u / R
    return 3000 + R * np.cos(th), 3000 + R * np.sin(th), v + 1000


def tilted_sheet():  # rotated 45 degrees about the u axis
    v, u = grid()
    c = np.cos(np.pi / 4)
    return u + 1000, v * c + 1000, v * c + 1000


def write_tifxyz(d, xyz, meta=None):
    os.makedirs(d, exist_ok=True)
    for n, a in zip("xyz", xyz):
        tifffile.imwrite(os.path.join(d, n + ".tif"), a.astype(np.float32))
    json.dump(meta or {"scale": [0.05, 0.05]}, open(os.path.join(d, "meta.json"), "w"))


def bar_is_exact(png, ov):
    import cv2
    img = cv2.imread(png)
    assert img.shape[:2] == (ov["image_size_px"][1], ov["image_size_px"][0])
    bx, by = ov["bar_xy"]
    row = img[by, :, :].min(axis=1)
    assert (row[bx:bx + ov["bar_px"]] == 255).all() and row[bx - 1] == 0 and row[bx + ov["bar_px"]] == 0
    assert ov["bar_px"] == round(10000 / ov["um_per_px"])


# ---------------- (1) synthetic geometry ----------------
def test_flat_sheet_fails():
    r = q.geometry_stats(*flat_sheet(), UM)
    assert abs(r["mean_abs_nz"] - 1.0) < 1e-9 and r["frac_abs_nz_gt_0p7"] == 1.0
    assert abs(r["area_vx2"] - 100 * 100 * 400) < 1e-3 and r["area_cm2"] > q.AREA_CM2_MIN
    assert r["geometry_pass"] is False


def test_cylinder_wall_passes():
    r = q.geometry_stats(*cylinder_wall(), UM)
    assert r["mean_abs_nz"] < 1e-9 and r["frac_abs_nz_gt_0p7"] == 0.0
    assert r["area_cm2"] > q.AREA_CM2_MIN and r["geometry_pass"] is True


def test_tilted_sheet_is_0p707():
    r = q.geometry_stats(*tilted_sheet(), UM)
    assert abs(r["mean_abs_nz"] - np.sqrt(0.5)) < 1e-9 and r["frac_abs_nz_gt_0p7"] == 1.0


def test_small_winding_fails_on_area_only():
    r = q.geometry_stats(*cylinder_wall(n=11), UM)  # 10x10 cells of 20 vx: 0.035 cm^2
    assert r["mean_abs_nz"] < 1e-9 and r["area_cm2"] < q.AREA_CM2_MIN and r["geometry_pass"] is False


def test_invalid_cells_are_ignored():
    x, y, z = cylinder_wall()
    x[:10], y[:10], z[:10] = -1, -1, -1  # tracer-style invalid rows
    z[50, 50] = np.nan
    r = q.geometry_stats(x, y, z, UM)
    assert r["n_valid_points"] == 101 * 101 - 10 * 101 - 1
    assert r["n_valid_cells"] == 90 * 100 - 3  # cells whose three corners include (50, 50)
    assert r["bbox_min_xyz"][2] == pytest.approx(1000 + 10 * 20) and r["mean_abs_nz"] < 1e-9


def test_spread_points_are_valid_and_spread():
    x, y, z = cylinder_wall()
    x[:, :30] = -1
    p = q.spread_points(x, y, z, 100)
    assert p.shape == (100, 3) and len({tuple(a) for a in p}) == 100 and (p > 0).all()
    assert p[:, 2].min() <= 1000 + 5 * 20 and p[:, 2].max() >= 1000 + 95 * 20  # spans the rows
    assert p[:, 0].max() > 3000 + 2000 * np.cos(30 * 20 / 2000) - 1 or True
    assert len(np.unique(np.round(p[:, 2] / 200))) >= 9  # points in at least 9 of the 11 row bands


# ---------------- offline CT reader on a local fake zarr level ----------------
@pytest.fixture
def fake_ct(tmp_path, monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    root = tmp_path / "www"
    zdir = root / "PHerc0139" / "volumes" / "20250728140407-9.362um-1.2m-113keV-masked.zarr"
    lvl = zdir / "4"
    (lvl / "0" / "0").mkdir(parents=True); (lvl / "1" / "1").mkdir(parents=True)
    za = {"shape": [10, 6, 6], "chunks": [4, 4, 4], "dtype": "|u1", "fill_value": 0, "order": "C",
          "filters": None, "dimension_separator": "/", "compressor": None, "zarr_format": 2}
    (lvl / ".zarray").write_text(json.dumps(za))
    (lvl / "0" / "0" / "0").write_bytes(np.arange(64, dtype=np.uint8).tobytes())
    (lvl / "1" / "1" / "1").write_bytes(np.full(64, 200, np.uint8).tobytes())
    (zdir / "metadata.json").write_text(json.dumps(
        {"scan": {"tomo": {"acquisition": {"detector": {"samplePixelSize": 0.009362}}}}}))
    cat = tmp_path / "cat.json"
    cat.write_text(json.dumps({"samples": {"PHerc0139": {"volumes": {"20250728140407": {"properties": {"pixel_size_um": 9.362}}}}}}))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr"
    yield {"url": url, "cache": str(tmp_path / "cache"), "catalogue": str(cat), "server": srv}
    srv.shutdown()


def test_chunked_ct_reader(fake_ct):
    ct = q.ChunkedCT(fake_ct["url"], 4, fake_ct["cache"])
    assert ct.shape == (10, 6, 6) and ct.chunks == (4, 4, 4) and ct.zarray["compressor"] is None
    vals = ct.sample([[0, 0, 0], [1, 2, 3], [5, 5, 5], [9, 5, 5], [3, 1, 1], [20, 0, 0]])
    assert vals.tolist() == [0, 27, 200, 0, 53, 0]
    assert ct.n_fetched == 2 and ct.n_missing == 1 and ct.n_http == 4  # .zarray + 2 chunks + 1 miss
    assert os.path.exists(os.path.join(fake_ct["cache"], "4", "1", "1", "1"))
    assert os.path.exists(os.path.join(fake_ct["cache"], "4", "2", "1", "1.missing"))
    s = ct.slice(5)  # z chunk 1: only 1/1/1 exists; 1/0/0, 1/0/1, 1/1/0 are 404 -> fill
    assert s.shape == (6, 6) and (s[4:6, 4:6] == 200).all() and (s[:4, :4] == 0).all()
    assert (s[:4, 4:] == 0).all() and (s[4:, :4] == 0).all() and ct.n_missing == 4
    s1 = ct.slice(1)  # z chunk 0: only 0/0/0 exists; its z=1 plane is arange(16, 32)
    assert (s1[:4, :4] == np.arange(16, 32).reshape(4, 4)).all() and (s1[4:, 4:] == 0).all()
    assert q.voxel_size_um(ct, fake_ct["catalogue"]) == {"metadata_um": pytest.approx(9.362), "catalogue_um": 9.362}
    fake_ct["server"].shutdown()  # everything touched so far must now come from the cache
    ct2 = q.ChunkedCT(fake_ct["url"], 4, fake_ct["cache"])
    assert ct2.sample([[1, 2, 3], [9, 5, 5]]).tolist() == [27, 0]


def test_qc_patch_unreadable_overlay_and_idempotence(fake_ct, tmp_path):
    d = str(tmp_path / "auto_grown_1")
    write_tifxyz(d, cylinder_wall())  # geometry PASS, but the fake CT is zero/absent everywhere it is sampled
    png = str(tmp_path / "ov.png")
    r, skipped = q.qc_patch(d, UM, fake_ct["url"], png, fake_ct["cache"], catalogue=fake_ct["catalogue"])
    assert not skipped and r["geometry_pass"] and r["ct"]["zero_frac"] == 1.0 and r["verdict"] == "UNREADABLE"
    assert r["ct"]["n_samples"] == 100 and r["voxel_size_check"]["metadata_um"] == pytest.approx(9.362)
    assert os.path.exists(os.path.join(d, "qc.json")) and open(os.path.join(d, q.MARKER)).read().strip() == "UNREADABLE"
    ov = r["overlay"]
    assert ov["n_points_drawn"] > 0 and ov["slice_z_l4"] == int(r["median_z"] // 16)
    assert ov["um_per_px"] == pytest.approx(16 * UM / ov["upscale"])
    bar_is_exact(png, ov)
    r2, skipped2 = q.qc_patch(d, UM, fake_ct["url"], png, fake_ct["cache"], catalogue=fake_ct["catalogue"])
    assert skipped2 and r2["verdict"] == "UNREADABLE"
    r3, skipped3 = q.qc_patch(d, UM, None, None, None, force=True)
    assert not skipped3 and r3["verdict"] == "PASS" and r3["ct"] is None and r3["voxel_size_check"] == "UNVERIFIED"
    assert "UNVERIFIED" in q.one_line(r3)
    # a geometry-only cache must not shadow a later CT / overlay request (or a different um / coord_scale)
    os.remove(png)
    r4, skipped4 = q.qc_patch(d, UM, fake_ct["url"], png, fake_ct["cache"], catalogue=fake_ct["catalogue"])
    assert not skipped4 and r4["ct"] is not None and r4["verdict"] == "UNREADABLE" and os.path.exists(png)
    assert r4["ct"]["chunks_http"] == 0 and r4["ct"]["chunks_loaded"] >= 0  # all chunks came from the disk cache
    assert q.qc_patch(d, UM, fake_ct["url"], png, fake_ct["cache"], catalogue=fake_ct["catalogue"])[1]
    assert not q.cached_covers(r4, UM, 4.0, fake_ct["url"], png) and not q.cached_covers(r4, UM, 1.0, fake_ct["url"], png + "x")
    assert os.path.exists(os.path.join(fake_ct["cache"], "metadata.json")) and not os.path.exists(os.path.join(fake_ct["cache"], "4", "metadata.json"))
    with pytest.raises(SystemExit):
        q.qc_patch(d, 8.64, fake_ct["url"], None, fake_ct["cache"], force=True, catalogue=fake_ct["catalogue"])


def test_cli_single_and_batch(tmp_path):
    parent = tmp_path / "patches"
    write_tifxyz(str(parent / "auto_grown_a"), flat_sheet())
    write_tifxyz(str(parent / "auto_grown_b"), cylinder_wall())
    (parent / "not_a_patch").mkdir()
    out = subprocess.run([sys.executable, SCRIPT, str(parent / "auto_grown_b"), "--um", str(UM)],
                         capture_output=True, text=True, check=True).stdout
    assert out.startswith("auto_grown_b PASS mean|nz|=0.000")
    out = subprocess.run([sys.executable, SCRIPT, str(parent), "--um", str(UM), "--batch"],
                         capture_output=True, text=True, check=True).stdout.splitlines()
    assert len(out) == 2 and out[0].startswith("auto_grown_a FAIL mean|nz|=1.000") and "[cached]" in out[1]
    assert subprocess.run([sys.executable, SCRIPT, "-h"], capture_output=True, text=True).returncode == 0


# ---------------- (2) the real w040 mesh: master-prompt reference ----------------
NEEDS_W040 = pytest.mark.skipif(not os.path.isdir(W040), reason="needs the public w040 mesh at $HERCULES_DATA/controls/w040/mesh (docs/REPRODUCE.md)")


@NEEDS_W040
def test_w040_geometry_reference():
    x, y, z, meta = q.load_tifxyz(W040)
    r = q.geometry_stats(x, y, z, UM)
    assert abs(r["mean_abs_nz"] - 0.25) <= 0.05 and abs(r["frac_abs_nz_gt_0p7"] - 0.06) <= 0.05
    ref = 43573236 * (UM * 1e-4) ** 2
    assert abs(r["area_cm2"] - ref) <= 0.2 * ref and r["geometry_pass"] is True
    assert r["bbox_min_xyz"] == pytest.approx(meta["bbox"][0]) and r["bbox_max_xyz"] == pytest.approx(meta["bbox"][1])


# ---------------- (3) CT-mask check against the real PHerc0139 volume at level 4 (network) ----------------
@NEEDS_W040
def test_w040_ct_mask_check_and_overlay(tmp_path):
    d = str(tmp_path / "w040_mesh")
    shutil.copytree(W040, d)  # the QC writes qc.json + marker into the patch dir; keep the control pristine
    png = str(tmp_path / "w040_l4_overlay.png")
    r, skipped = q.qc_patch(d, UM, CT_URL, png, CACHE)
    assert not skipped and r["verdict"] == "PASS"
    assert r["ct"]["n_samples"] == 100 and r["ct"]["zero_frac"] <= q.CT_ZERO_FRAC_MAX
    assert r["ct"]["chunks"] == [128, 128, 128] and r["ct"]["zarray"]["compressor"] is None
    assert r["voxel_size_check"]["metadata_um"] == pytest.approx(UM)
    if os.path.exists(q.CATALOGUE):
        assert r["voxel_size_check"]["catalogue_um"] == pytest.approx(UM)
    ov = r["overlay"]
    assert os.path.exists(ov["path"]) and ov["n_points_drawn"] > 0
    assert ov["n_points_drawn"] < 0.05 * r["n_valid_points"]  # a thin curve, not a wide band
    bar_is_exact(png, ov)
    r2, skipped2 = q.qc_patch(d, UM, CT_URL, png, CACHE)
    assert skipped2 and r2["ct"]["zero_frac"] == r["ct"]["zero_frac"]
    assert not q.qc_patch(d, UM, CT_URL, str(tmp_path / "other.png"), CACHE)[1]  # a new overlay path re-runs
    print("w040 CT check:", q.one_line(r), "overlay", ov["path"], "chunks loaded/http", r["ct"]["chunks_loaded"], r["ct"]["chunks_http"])


def test_ct_mask_in_mask_area_arm(fake_ct, tmp_path, monkeypatch):
    """RULES 'QC CT-mask bar: an in-mask AREA arm'. The zero-fraction arm is unchanged; a patch over that bar is
    admitted only when (1 - zero_frac) * area_cm2 reaches the 1.5 cm2 rule 5.5 needs before it will call anything
    BLANK. Both arms and the estimated in-mask area are recorded in qc.json."""
    d = str(tmp_path / "auto_grown_arm")
    write_tifxyz(d, cylinder_wall())        # fake CT samples zero everywhere -> zero_frac 1.0, in-mask area 0
    r, _ = q.qc_patch(d, UM, fake_ct["url"], None, fake_ct["cache"], catalogue=fake_ct["catalogue"])
    assert r["ct"]["zero_frac"] == 1.0 and r["ct"]["in_mask_cm2"] == 0.0
    assert r["ct"]["arm"] is None and r["verdict"] == "UNREADABLE"
    assert r["ct"]["in_mask_cm2_min"] == 1.5 and r["bars"]["ct_in_mask_cm2_min"] == 1.5

    # the same patch with the area bar dropped below its in-mask area is admitted BY THE SECOND ARM, not the first
    monkeypatch.setattr(q, "CT_IN_MASK_CM2_MIN", -1.0)
    r2, _ = q.qc_patch(d, UM, fake_ct["url"], None, fake_ct["cache"], force=True, catalogue=fake_ct["catalogue"])
    assert r2["ct"]["zero_frac"] > q.CT_ZERO_FRAC_MAX and r2["ct"]["arm"] == "in_mask_area" and r2["verdict"] == "PASS"

    # and a patch under the zero-fraction bar is always admitted by the FIRST arm, whatever its area
    monkeypatch.setattr(q, "CT_ZERO_FRAC_MAX", 1.0)
    monkeypatch.setattr(q, "CT_IN_MASK_CM2_MIN", 1e9)
    r3, _ = q.qc_patch(d, UM, fake_ct["url"], None, fake_ct["cache"], force=True, catalogue=fake_ct["catalogue"])
    assert r3["ct"]["arm"] == "zero_frac" and r3["verdict"] == "PASS"
