# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for the factory verifier (tools/sib/factory): every check, with planted faults.
Synthetic packages only (no network, no real CT). Run: pytest tests/sib_factory_verify_test.py"""
import json
import os
import shutil
import struct
import sys
import zlib

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sib", "factory"))
import build_image as BI  # noqa: E402
import factory as F  # noqa: E402
import pngio  # noqa: E402
import verify as V  # noqa: E402

ELIG = json.load(open(os.path.join(ROOT, "data", "catalogue", "eligible_products.json")))["volumes"]
E0 = next(v for v in ELIG if v["protocol"] == "JULY")  # an eligible 9.362 um volume
URL_ELIG = E0["volume_zarr_s3"]
URL_0139 = "s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/"
RENDER = dict(app="vc_render_tifxyz", villa_commit="41701aa0eaa1aa765523db3f9f972b5830abf549", binary_sha256="0" * 64,
              deps_image="img", command=["vc_render_tifxyz"], utc_start="2026-09-25T00:00:00Z",
              utc_end="2026-09-25T00:00:01Z")


def metadata(tmp, scroll, pix_mm=0.009362):
    num = scroll.replace("PHerc", "")
    p = os.path.join(tmp, f"md_{scroll}.json")
    json.dump({"scan": {"tomo": {"acquisition": {"scanRadix": f"SCROLLS_HEL_4.681um_113keV_1.2m_binmean_2_PHerc_{num}_HA",
                                                 "detector": {"samplePixelSize": pix_mm}}}}}, open(p, "w"))
    return p


def raw_render(h=160, w=1200, seed=0):
    r = np.random.default_rng(seed)
    a = (np.linspace(20, 230, w)[None, :] + r.normal(0, 12, (h, w))).clip(1, 255).astype(np.uint8)
    a[:5, :40] = 0  # some invalid pixels
    return a


def mesh_points(n=10):
    g = np.mgrid[0:n, 0:n].astype(np.float32)
    return np.stack([100 + 20 * g[1], 200 + 20 * g[0], np.full((n, n), 500, np.float32)], -1)


def letters(ppm, n=10):
    rows = []
    for i in range(n):
        x, y, w, h = 20 + 60 * i, 30, 40, 50
        rows.append(dict(letter_id=f"L{i}", identity="A", bbox_x_px=x, bbox_y_px=y, bbox_w_px=w, bbox_h_px=h,
                         height_mm=round(h / ppm, 3), width_mm=round(w / ppm, 3), firm=True, evidence="test"))
    return rows


def make(tmp, dry=True, url=URL_0139, scale=1.0, name="PHerc0139_w035_test", rows=None, raw=None):
    scroll = url.split("/")[3]
    root = os.path.join(tmp, "packages", "dryrun" if dry else "real")
    os.makedirs(root, exist_ok=True)
    return F.make_package(raw if raw is not None else raw_render(), mesh_points=mesh_points(), mesh_scale=(0.05, 0.05),
                          mesh_name=name, volume_url=url, volume_metadata_path=metadata(tmp, scroll),
                          out_root=root, dry_run=dry, scale=scale, render_info=RENDER,
                          mesh_source=dict(url=f"s3://x/mesh/1-on-{url.split('/')[5][:14]}-9.362um.tifxyz"),
                          letter_rows=rows, created_utc="2026-09-25T00:00:02Z", repo=ROOT)


def real(tmp, **kw):
    ppm = 1000 / 9.362 * kw.get("scale", 1.0)
    kw.setdefault("rows", letters(ppm))
    return make(tmp, dry=False, url=kw.pop("url", URL_ELIG), name=kw.pop("name", "real_mesh_1"), **kw)


def check(res, name):
    return next(c for c in res["checks"] if c["check"] == name)


def failed(res):
    return [c["check"] for c in res["checks"] if not c["ok"]]


def pkgjson(d):
    return json.load(open(os.path.join(d, "package.json")))


def save_pkgjson(d, p):
    open(os.path.join(d, "package.json"), "w").write(json.dumps(p, indent=1, sort_keys=True) + "\n")


def reseal(d):
    """After a planted fault: refresh package.json hashes of the image and the manifest so that only the
    targeted check can catch the fault (an attacker who rewrites hashes)."""
    p = pkgjson(d)
    b = open(os.path.join(d, p["image"]["file"]), "rb").read()
    p["image"]["sha256"] = F.sha256_bytes(b)
    save_pkgjson(d, p)
    F.write_manifest(d)


def rewrite_png(d, img):
    p = pkgjson(d)
    open(os.path.join(d, p["image"]["file"]), "wb").write(pngio.encode_png_gray8(img))
    reseal(d)


def load_img(d):
    p = pkgjson(d)
    return pngio.decode_canonical_png(open(os.path.join(d, p["image"]["file"]), "rb").read())


@pytest.fixture
def tmp(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------- clean packages pass
def test_clean_dry_run_passes(tmp):
    r = V.verify(make(tmp))
    assert r["passed"], failed(r)
    assert "DRY RUN" in check(r, "volume_eligible")["detail"]


def test_clean_real_package_passes(tmp):
    r = V.verify(real(tmp))
    assert r["passed"], failed(r)


def test_clean_downscaled_package_passes(tmp):
    r = V.verify(make(tmp, scale=0.5, raw=raw_render(160, 2400)))
    assert r["passed"], failed(r)
    assert "INTER_AREA" in check(r, "linear_display")["detail"]


# ---------------------------------------------------------------- (a) metadata chunks, canonical PNG
@pytest.mark.parametrize("ctype", [b"tEXt", b"iTXt", b"zTXt", b"eXIf", b"pHYs", b"tIME"])
def test_hidden_png_chunk_rejected(tmp, ctype):
    d = make(tmp)
    p = pkgjson(d)
    f = os.path.join(d, p["image"]["file"])
    b = open(f, "rb").read()
    body = b"Comment\x00hidden" if ctype != b"pHYs" else struct.pack(">IIB", 3779, 3779, 1)
    ch = struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", zlib.crc32(ctype + body) & 0xFFFFFFFF)
    ihdr_end = 8 + 12 + 13
    open(f, "wb").write(b[:ihdr_end] + ch + b[ihdr_end:])
    reseal(d)
    r = V.verify(d)
    assert not r["passed"] and "png_no_metadata" in failed(r)
    assert ctype.decode() in check(r, "png_no_metadata")["detail"]


def test_trailing_bytes_after_iend_rejected(tmp):
    d = make(tmp)
    f = os.path.join(d, pkgjson(d)["image"]["file"])
    open(f, "ab").write(b"hidden payload")
    reseal(d)
    assert "png_no_metadata" in failed(V.verify(d))


def test_recompressed_png_rejected(tmp):
    """Same pixels, other encoder (zlib-compressed IDAT): not canonical, rejected."""
    d = make(tmp)
    f = os.path.join(d, pkgjson(d)["image"]["file"])
    img = load_img(d)
    raw = np.zeros((img.shape[0], img.shape[1] + 1), np.uint8)
    raw[:, 1:] = img
    ihdr = struct.pack(">IIBBBBB", img.shape[1], img.shape[0], 8, 0, 0, 0, 0)
    b = pngio.PNG_SIG + pngio._chunk(b"IHDR", ihdr) + pngio._chunk(b"IDAT", zlib.compress(raw.tobytes(), 9)) + pngio._chunk(b"IEND", b"")
    open(f, "wb").write(b)
    reseal(d)
    assert "png_no_metadata" in failed(V.verify(d))


def test_tiff_software_tag_rejected(tmp):
    import tifffile
    d = make(tmp)
    p = pkgjson(d)
    x = os.path.join(d, "mesh", p["mesh_name"], "x.tif")
    tifffile.imwrite(x, tifffile.imread(x), software="hidden", photometric="minisblack")
    p["mesh"]["files_sha256"]["x.tif"] = F.sha256_bytes(open(x, "rb").read())
    save_pkgjson(d, p)
    F.write_manifest(d)
    assert "mesh_no_metadata" in failed(V.verify(d))


def test_extra_json_key_rejected(tmp):
    d = make(tmp)
    p = pkgjson(d)
    p["image"]["comment"] = "x"
    save_pkgjson(d, p)
    F.write_manifest(d)
    assert "package_json_strict" in failed(V.verify(d))


def test_extra_mesh_meta_key_rejected(tmp):
    d = make(tmp)
    p = pkgjson(d)
    mp = os.path.join(d, "mesh", p["mesh_name"], "meta.json")
    m = json.load(open(mp))
    m["note"] = "x"
    json.dump(m, open(mp, "w"))
    F.write_manifest(d)
    assert "mesh_no_metadata" in failed(V.verify(d))


def test_extra_file_rejected(tmp):
    d = make(tmp)
    open(os.path.join(d, "notes.txt"), "w").write("x\n")
    F.write_manifest(d)
    assert "file_layout" in failed(V.verify(d))


# ---------------------------------------------------------------- names
def test_basename_must_equal_mesh_name(tmp):
    d = make(tmp)
    p = pkgjson(d)
    p["image"]["file"] = "other.png"
    save_pkgjson(d, p)
    F.write_manifest(d)
    r = V.verify(d)
    assert not r["passed"] and "names_ascii_basename" in failed(r)


@pytest.mark.parametrize("bad", ["w035\u00e9", "w035 x", "w035\u200b", "DRY_RUN_w035"])
def test_factory_refuses_bad_mesh_names(tmp, bad):
    with pytest.raises(ValueError):
        make(tmp, name=bad)


# ---------------------------------------------------------------- (b) scale bar
def test_wrong_scale_bar_rejected(tmp):
    d = make(tmp)
    img = load_img(d)
    p = pkgjson(d)
    y0, y1 = p["scale_bar"]["rows"]
    x0, L = p["scale_bar"]["x0"], p["scale_bar"]["length_px"]
    img[y0:y1, x0 + L - 6:x0 + L] = 0  # bar 6 px short
    rewrite_png(d, img)
    r = V.verify(d)
    assert "scale_bar_measured" in failed(r)
    assert str(L - 6) in check(r, "scale_bar_measured")["detail"]


def test_scale_bar_uses_metadata_voxel(tmp):
    """A package whose metadata voxel differs from the one used to draw the bar is rejected."""
    d = make(tmp)
    p = pkgjson(d)
    mp = os.path.join(d, p["volume_metadata"]["file"])
    m = json.load(open(mp))
    m["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"] = 0.00864
    json.dump(m, open(mp, "w"))
    p["volume_metadata"]["sha256"] = F.sha256_bytes(open(mp, "rb").read())
    save_pkgjson(d, p)
    F.write_manifest(d)
    assert "voxel_from_metadata" in failed(V.verify(d))


def test_bar_measurement_value(tmp):
    d = make(tmp)
    det = check(V.verify(d), "scale_bar_measured")["detail"]
    assert f"measured bar {round(10000 / 9.362)} px" in det


# ---------------------------------------------------------------- (e) Cf characters
def test_cf_in_readme_rejected(tmp):
    d = make(tmp)
    f = os.path.join(d, "README.txt")
    s = open(f).read()
    open(f, "w", encoding="utf-8").write(s.replace("Package:", "Pack\u200bage:"))
    F.write_manifest(d)
    assert "no_cf_characters" in failed(V.verify(d))


def test_cf_escaped_in_json_rejected(tmp):
    d = make(tmp)
    p = pkgjson(d)
    p["package_name"] = p["package_name"] + "\u2066"  # json.dumps writes it as an ASCII escape
    save_pkgjson(d, p)
    F.write_manifest(d)
    r = V.verify(d)
    assert "no_cf_characters" in failed(r)


def test_cf_in_file_name_rejected(tmp):
    d = make(tmp)
    open(os.path.join(d, "inputs", "a\u200d.json"), "w").write("{}")
    F.write_manifest(d)
    r = V.verify(d)
    assert "no_cf_characters" in failed(r) or "file_layout" in failed(r)
    assert not r["passed"]


# ---------------------------------------------------------------- (e) eligibility
def test_non_eligible_volume_rejected_in_real_package(tmp):
    r = V.verify(real(tmp, url=URL_0139, name="m0139"))
    assert "volume_eligible" in failed(r)


def test_wrong_volume_id_rejected(tmp):
    bad = URL_ELIG.replace(E0["volume_id"], "20990101000000")
    r = V.verify(real(tmp, url=bad, name="mbad"))
    assert "volume_eligible" in failed(r)


def test_volume_id_field_tamper_rejected(tmp):
    d = real(tmp)
    p = pkgjson(d)
    p["volume_id"] = "20250728140407"
    save_pkgjson(d, p)
    F.write_manifest(d)
    assert "volume_eligible" in failed(V.verify(d))


# ---------------------------------------------------------------- (e) DRY RUN marking
def test_dry_run_text_in_real_package_rejected(tmp):
    d = real(tmp)
    f = os.path.join(d, "README.txt")
    open(f, "a").write("DRY RUN\n")
    F.write_manifest(d)
    assert "dry_run_marking" in failed(V.verify(d))


def test_dry_run_stamp_in_real_image_rejected(tmp):
    d = real(tmp)
    img = load_img(d)
    img[:BI.HEADER] = BI.stamp_strip(img.shape[1])
    rewrite_png(d, img)
    assert "dry_run_marking" in failed(V.verify(d))


def test_dry_run_flag_flip_rejected(tmp):
    """A dry-run package relabelled as real still carries the stamp and the DRY_RUN_ dir name."""
    d = make(tmp)
    p = pkgjson(d)
    p["dry_run"] = False
    save_pkgjson(d, p)
    F.write_manifest(d)
    r = V.verify(d)
    assert not r["passed"] and "dry_run_marking" in failed(r)


def test_dry_run_without_stamp_rejected(tmp):
    d = make(tmp)
    img = load_img(d)
    img[:BI.HEADER] = 0
    rewrite_png(d, img)
    assert "dry_run_marking" in failed(V.verify(d))


# ---------------------------------------------------------------- display, manifest, tools, letters, provenance
def test_non_linear_display_rejected(tmp):
    d = make(tmp)
    img = load_img(d)
    p0, p1 = pkgjson(d)["image"]["panel_rows"]
    pan = img[p0:p1].astype(np.float64) / 255.0
    img[p0:p1] = np.rint(255 * pan ** 0.7).astype(np.uint8)  # gamma
    rewrite_png(d, img)
    assert "linear_display" in failed(V.verify(d))


def test_manifest_mismatch_rejected(tmp):
    d = make(tmp)
    open(os.path.join(d, "README.txt"), "a").write("x\n")
    assert "sha256_manifest" in failed(V.verify(d))


def test_tool_tamper_rejected(tmp):
    d = make(tmp)
    open(os.path.join(d, "tools", "build_image.py"), "a").write("# x\n")
    F.write_manifest(d)
    assert "tools_pinned" in failed(V.verify(d))


def test_letter_table_consistency(tmp):
    ppm = 1000 / 9.362
    rows = letters(ppm)
    rows[3]["height_mm"] = rows[3]["height_mm"] + 0.1
    assert "letter_table" in failed(V.verify(real(tmp, rows=rows)))


def test_real_package_needs_ten_letters(tmp):
    assert "letter_table" in failed(V.verify(real(tmp, rows=letters(1000 / 9.362, 9))))


def test_provenance_required(tmp):
    d = make(tmp)
    f = os.path.join(d, "README.txt")
    s = open(f).read()
    open(f, "w").write("\n".join(s.split("\n")[1:]))
    F.write_manifest(d)
    assert "provenance_visible" in failed(V.verify(d))


def test_bad_timestamp_rejected(tmp):
    d = make(tmp)
    p = pkgjson(d)
    p["timestamps"]["package_utc"] = "yesterday"
    save_pkgjson(d, p)
    F.write_manifest(d)
    assert "fields_wellformed" in failed(V.verify(d))


# ---------------------------------------------------------------- determinism
def test_png_encoding_is_deterministic_and_roundtrips():
    a = raw_render(50, 70)
    b1, b2 = pngio.encode_png_gray8(a), pngio.encode_png_gray8(a.copy())
    assert b1 == b2
    assert np.array_equal(pngio.decode_canonical_png(b1), a)
    big = np.random.default_rng(1).integers(0, 256, (400, 500), dtype=np.uint8)  # > 65535 bytes: several blocks
    assert np.array_equal(pngio.decode_canonical_png(pngio.encode_png_gray8(big)), big)


def test_png_readable_by_pil():
    from PIL import Image
    import io
    a = raw_render(30, 40)
    assert np.array_equal(np.asarray(Image.open(io.BytesIO(pngio.encode_png_gray8(a)))), a)


def test_tiff_readable_by_tifffile_and_structural():
    import tifffile
    import io
    a = np.arange(12, dtype=np.float32).reshape(3, 4)
    b = pngio.encode_tiff_f32(a)
    assert np.array_equal(tifffile.imread(io.BytesIO(b)), a)
    assert set(pngio.tiff_tags(b)) == set(pngio.TIFF_TAGS_ALLOWED)


def test_package_build_is_deterministic(tmp):
    d1 = make(os.path.join(tmp, "a"))
    d2 = make(os.path.join(tmp, "b"))
    for f in ("PHerc0139_w035_test.png", "render/PHerc0139_w035_test_raw.npy", "mesh/PHerc0139_w035_test/x.tif"):
        assert open(os.path.join(d1, f), "rb").read() == open(os.path.join(d2, f), "rb").read()


# ---------------------------------------------------------------- (f) reproduce path (renderer mocked)
def _repro(tmp, d, raw, md_path, monkeypatch):
    import reproduce_check as RC
    monkeypatch.setattr(RC.RB, "fetch_metadata", lambda url, dst: (shutil.copyfile(md_path, dst),
                                                                   F.sha256_file(dst))[1])
    monkeypatch.setattr(RC.RB, "render", lambda url, mesh, wd, vox: (raw, ["vc_render_tifxyz"], "t0", "t1"))
    p = pkgjson(d)
    with pytest.raises(SystemExit) as e:
        RC.main(["--package", d, "--volume-url", p["volume_url"], "--mesh", os.path.join(d, p["mesh"]["dir"]),
                 "--workdir", os.path.join(tmp, "repro_work")])
    return e.value.code


def test_reproduce_identical_render_passes(tmp, monkeypatch):
    raw = raw_render()
    d = make(tmp, raw=raw)
    md = os.path.join(d, "inputs", "volume_metadata.json")
    assert _repro(tmp, d, raw.copy(), md, monkeypatch) == 0


def test_reproduce_detects_one_grey_level(tmp, monkeypatch):
    raw = raw_render()
    d = make(tmp, raw=raw)
    md = os.path.join(d, "inputs", "volume_metadata.json")
    other = raw.copy()
    other[80, 600] = other[80, 600] ^ 1
    assert _repro(tmp, d, other, md, monkeypatch) == 1


def test_every_check_has_a_planted_fault_test():
    src = open(__file__).read()
    missing = [n for n, _ in V.CHECKS if f'"{n}" in failed' not in src]
    assert not missing, missing


def test_reproduce_script_writes_no_bytecode_into_package():
    assert "PYTHONDONTWRITEBYTECODE=1" in F.REPRODUCE_SH and " -B " in F.REPRODUCE_SH


def test_pycache_in_package_rejected(tmp):
    d = make(tmp)
    os.makedirs(os.path.join(d, "tools", "__pycache__"))
    open(os.path.join(d, "tools", "__pycache__", "x.pyc"), "wb").write(b"\x00")
    F.write_manifest(d)
    assert "file_layout" in failed(V.verify(d))
