"""Tests for scripts/seeds.py (master prompt 5.6).
(1) synthetic level-3 prediction (concentric rings) in a local zarr v2 store -> seeds on rings,
    three radius classes, min pairwise distance >= 40, counts about n-per-band.
(2) real smoke run on PHerc0306B (20250521133212, 8.64 um), one mid-z band, --n-per-band 12,
    only the needed chunks, cached under /home/user/hercules_data/pred_l3_cache/PHerc0306B.
"""
import json, os, sys, itertools
import numpy as np, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import seeds as S
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

CACHE = DATA + "/pred_l3_cache/PHerc0306B"


def make_rings(shape=(64, 400, 400), radii=(60, 110, 160), width=2):
    z, h, w = shape
    yy, xx = np.mgrid[:h, :w]
    d = np.hypot(yy - h / 2, xx - w / 2)
    sl = np.zeros((h, w), np.uint8)
    for r in radii:
        sl[np.abs(d - r) <= width] = 255
    return np.broadcast_to(sl, shape).copy(), d


@pytest.fixture(scope="module")
def synth_store(tmp_path_factory):
    import zarr
    vol, d = make_rings()
    root = tmp_path_factory.mktemp("pred") / "synthetic.zarr"
    g = zarr.open_group(str(root), mode="w", zarr_format=2)
    a = g.create_array("3", shape=vol.shape, chunks=(32, 128, 128), dtype="uint8",
                       chunk_key_encoding={"name": "v2", "separator": "/"})
    a[:] = vol
    return str(root), vol, d


def test_synthetic_rings(synth_store):
    base, vol, d = synth_store
    meta = S.read_zarray(base)
    assert meta["shape"] == list(vol.shape) and meta["dtype"] == "|u1"
    z0, z1 = 8 * 8, 56 * 8                       # level-0 band inside the 64 level-3 slices
    idx = S.band_slices(z0, z1)
    assert len(idx) == 5 and all(8 <= z < 56 for z in idx)
    slices = []
    for z in idx:
        m = S.read_slice(base, meta, z)
        assert np.array_equal(m, vol[z])            # chunk assembly is exact
        slices.append((z, m >= S.THRESH))
    seeds, per = S.select_band(slices, 30, np.random.default_rng(1))
    assert 24 <= len(seeds) <= 30, len(seeds)
    # seeds lie on the rings (predicted voxels) and coordinates are level-0 = level-3 * 8
    for s in seeds:
        assert vol[s["z"] // 8, s["y"] // 8, s["x"] // 8] >= 128
        assert s["x"] % 8 == 0 and s["y"] % 8 == 0 and s["z"] % 8 == 0
    # three radius classes, each present and balanced within a few
    cnt = {c: sum(s["radius"] == c for s in seeds) for c in S.CLASSES}
    assert all(cnt[c] >= 6 for c in S.CLASSES), cnt
    # radius classes are ordered by distance from the centroid (thirds by distance rank)
    rad = {c: [d[s["y"] // 8, s["x"] // 8] for s in seeds if s["radius"] == c] for c in S.CLASSES}
    assert max(rad["inner"]) <= min(rad["outer"]) and np.mean(rad["inner"]) < np.mean(rad["middle"]) < np.mean(rad["outer"])
    assert min(rad["outer"]) >= 100 and max(rad["inner"]) <= 120, rad
    # min pairwise distance >= 40 within each slice
    for z in idx:
        pts = [(s["row_l3"], s["col_l3"]) for s in seeds if s["slice_l3"] == z]
        for p, q in itertools.combinations(pts, 2):
            assert np.hypot(p[0] - q[0], p[1] - q[1]) >= S.MIN_DIST


def test_ct_ok_mask_and_filters_assert(tmp_path):
    # level-4 CT slice 3x3 with the right column zero -> level-3 mask 6x6 (repeat x2), cropped to shape
    ct4 = np.array([[5, 7, 0], [1, 9, 0], [3, 2, 0]], np.uint8)
    m = S.ct_ok_mask(ct4, (5, 5))
    assert m.shape == (5, 5) and m[:, :4].all() and not m[:, 4].any()
    m = S.ct_ok_mask(ct4, (8, 8))                  # padding beyond the CT is False
    assert m[:6, :4].all() and not m[6:].any() and not m[:, 4:].any()
    # a zarr v2 store with filters must be refused (read_slice applies only the Blosc codec)
    d = tmp_path / "f.zarr" / "3"; d.mkdir(parents=True)
    (d / ".zarray").write_text(json.dumps({"zarr_format": 2, "dtype": "|u1", "order": "C", "shape": [1, 1, 1],
        "chunks": [1, 1, 1], "compressor": None, "fill_value": 0, "dimension_separator": "/",
        "filters": [{"id": "delta", "dtype": "|u1"}]}))
    with pytest.raises(AssertionError):
        S.read_zarray(str(tmp_path / "f.zarr"))


def test_auto_bands():
    b = S.auto_bands(12748)
    assert len(b) == 3 and all(z1 - z0 == 1000 for z0, z1 in b)
    assert b[1] == (6374 - 500, 6374 + 500)


def test_cli_idempotent(synth_store, tmp_path):
    base, vol, d = synth_store
    out = tmp_path / "s.json"
    assert S.main(["--pred-url", base, "--um", "8.64", "--zband", "64:448", "--n-per-band", "12",
                   "--out", str(out)]) == 0
    j = json.load(open(out))
    assert 9 <= len(j["seeds"]) <= 12 and j["bar_px_l3"] == round(10000 / (8.64 * 8))
    assert os.path.exists(tmp_path / "s_band_64_448.png")
    mtime = out.stat().st_mtime
    S.main(["--pred-url", base, "--um", "8.64", "--zband", "64:448", "--out", str(out)])
    assert out.stat().st_mtime == mtime          # skipped


@pytest.mark.skipif(not os.path.exists(S.CATALOGUE), reason="needs the bucket catalogue at $HERCULES_DATA/cat/metadata.min.json and network (docs/REPRODUCE.md)")
def test_real_phherc0306b_smoke(tmp_path, capsys):
    base = S.pred_url_from_catalogue("PHerc0306B", "20250521133212")
    assert base.endswith("20250521133212-surface-20260413222639-surface-m7-L0-th0.2.zarr")
    meta = S.read_zarray(base, CACHE)
    assert meta["zarr_format"] == 2 and meta["dtype"] == "|u1" and meta["chunks"] == [192, 192, 192]
    assert meta["compressor"]["id"] == "blosc" and meta["compressor"]["cname"] == "zstd"
    assert meta["dimension_separator"] == "/"
    Z3 = meta["shape"][0]
    zc = Z3 * 8 // 2
    z0, z1 = zc - 500, zc + 500
    out = tmp_path / "PHerc0306B.json"
    rc = S.main(["--scroll", "PHerc0306B", "--vol", "20250521133212", "--um", "8.64",
                 "--zband", f"{z0}:{z1}", "--n-per-band", "12", "--cache", CACHE, "--out", str(out)])
    assert rc == 0
    j = json.load(open(out))
    band = j["bands"][0]
    print("PHerc0306B level-3 shape", meta["shape"])
    for s in band["slices"]:
        print(f"  slice {s['slice_l3']}: predicted voxels {s['n_pred']}, seeds {s['n_seeds']}")
    for s in j["seeds"]:
        print("  seed", s["x"], s["y"], s["z"], s["radius"])
    assert all(s["n_pred"] > 0 for s in band["slices"])
    assert 8 <= len(j["seeds"]) <= 12
    assert set(s["radius"] for s in j["seeds"]) == set(S.CLASSES)
    for s in j["seeds"]:
        assert 0 <= s["x"] < meta["shape"][2] * 8 and 0 <= s["y"] < meta["shape"][1] * 8
        assert z0 <= s["z"] < z1
    assert j["bar_px_l3"] == round(10000 / (8.64 * 8))
    # voxel pitch cross-checked: metadata.json samplePixelSize*1000 == --um == catalogue
    assert abs(j["um_metadata_json"] - 8.64) < 1e-3 and abs(j["um_catalogue"] - 8.64) < 1e-3
    # 5.8 gate: every seed sits on masked CT (level 4 at z//16, y//16, x//16 > 0), and the gate removed some
    ct_meta = S.read_zarray(j["ct_url"], os.path.join(CACHE, "ct"), S.CT_LEVEL)
    assert ct_meta["shape"] == [994, 554, 554] and ct_meta["compressor"] is None
    for s in band["slices"]:
        assert 0 < s["n_pred_on_ct"] < s["n_pred_total"] and s["n_pred"] == s["n_pred_on_ct"]
        print(f"  slice {s['slice_l3']}: predicted total {s['n_pred_total']}, on CT {s['n_pred_on_ct']}")
    ct_planes = {}
    for s in j["seeds"]:
        z4 = s["z"] // 16
        if z4 not in ct_planes:
            ct_planes[z4] = S.read_slice(j["ct_url"], ct_meta, z4, os.path.join(CACHE, "ct"))
        v = int(ct_planes[z4][s["y"] // 16, s["x"] // 16])
        print(f"  seed {s['x']} {s['y']} {s['z']} {s['radius']} CT L4 = {v}")
        assert v > 0, s
