"""Tests for package_submission.py + verify_package.py (5.14 dry-run semantics) on synthetic 9.362 um data."""
import json, os, sys
import numpy as np, cv2, tifffile, zarr, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import package_submission as ps  # noqa: E402
import verify_package as vp  # noqa: E402

UM = 9.362
SIDE = int(round(20000 / UM))   # 2136
BAR = int(round(10000 / UM))    # 1068
X0, Y0 = 200, 150


def make_read_dir(d):
    rng = np.random.default_rng(0)
    fwd = rng.integers(0, 256, (2500, 2500), dtype=np.uint8)
    rev = rng.integers(0, 256, (2500, 2500), dtype=np.uint8)
    tifffile.imwrite(os.path.join(d, "forward.tif"), fwd)
    tifffile.imwrite(os.path.join(d, "reverse.tif"), rev)
    g = zarr.open_group(os.path.join(d, "render.zarr"), mode="w", zarr_format=2)
    a = g.create_array("0", shape=(3, 2500, 2500), chunks=(3, 512, 512), dtype="uint8", compressors=None,
                       chunk_key_encoding={"name": "v2", "separator": "/"})
    a[:] = rng.integers(0, 256, (3, 2500, 2500), dtype=np.uint8)
    return fwd


def make_mesh(d):
    os.makedirs(d)
    for n in "xyz":
        tifffile.imwrite(os.path.join(d, n + ".tif"), np.zeros((20, 20), np.float32))
    json.dump({"format": "tifxyz", "scale": [0.05, 0.05], "flattened": {"tool": "vc_flatten ABF++"}},
              open(os.path.join(d, "meta.json"), "w"))


def letters12():
    # 3 rows x 4 letters, ~3 mm tall (320 px), inside the window (source coords)
    out = []
    for r in range(3):
        for c in range(4):
            out.append({"x": X0 + 300 + c * 400, "y": Y0 + 300 + r * 500, "w_px": 250, "h_px": 320, "reading": "ΑΒΓΔ"[c]})
    return out


def build(tmp_path, scroll, volume, letters, name="pkg"):
    rd = tmp_path / "read"; rd.mkdir()
    make_read_dir(str(rd))
    mesh = tmp_path / "seg_flat"; make_mesh(str(mesh))
    lp = tmp_path / "letters.json"; json.dump(letters, open(lp, "w"))
    (tmp_path / "heldout.md").write_text("Held-out window 2 cm away shows different plausible letters.\n")
    (tmp_path / "method.md").write_text("Method: villa infer, public 9um checkpoint, 28 slices, both orders.\n")
    out = tmp_path / name
    argv = ["--read-dir", str(rd), "--mesh", str(mesh), "--window-x", str(X0), "--window-y", str(Y0),
            "--scroll", scroll, "--volume", volume, "--um", str(UM), "--letters", str(lp),
            "--heldout", str(tmp_path / "heldout.md"), "--method", str(tmp_path / "method.md"),
            "--checkpoint", "ink_9um.ckpt", "--call", "python infer.py --ckpt ink_9um.ckpt", "--docker-image", "img:tag",
            "--out", str(out)]
    ps.main(argv)
    return str(out)


def fails(checks):
    return [c[0] + ": " + c[2] for c in checks if c[1] is False]


def nas(checks):
    return [c[0] for c in checks if c[1] is None]


def test_w040_dry_run_fails_exactly_not_eligible(tmp_path):
    out = build(tmp_path, "PHerc0139", "20231117161658", letters12())
    checks = vp.verify(out)
    f = fails(checks)
    assert len(f) == 1 and "not eligible" in f[0], f
    assert os.path.exists(os.path.join(out, "seg_flat.png"))
    assert os.path.exists(os.path.join(out, ".complete"))
    assert vp.main([out]) == 1
    # window TIFF is the untouched crop; bar measured exactly
    fw = tifffile.imread(os.path.join(out, "forward_window.tif"))
    src = tifffile.imread(os.path.join(tmp_path, "read", "forward.tif"))
    assert fw.shape == (SIDE, SIDE) and np.array_equal(fw, src[Y0:Y0 + SIDE, X0:X0 + SIDE])
    L, top = vp.measure_bar(os.path.join(out, "seg_flat.png"))
    assert L == BAR and top >= SIDE
    pkg = json.load(open(os.path.join(out, "package.json")))
    assert abs(pkg["window"]["area_cm2"] - 4.0) < 0.04 and pkg["n_letters_in_window"] == 12 and len(pkg["rows"]) == 3
    assert pkg["letters"][0]["h_mm"] == round(320 * UM / 1000, 3)


def test_empty_letters_adds_fewer_than_10(tmp_path):
    out = build(tmp_path, "PHerc0139", "20231117161658", [])
    f = fails(vp.verify(out))
    assert len(f) == 2 and any("not eligible" in s for s in f) and any("fewer than 10 letters" in s for s in f), f


def test_eligible_all_pass(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    checks = vp.verify(out)
    assert fails(checks) == []
    assert vp.main([out]) == 0
    # idempotent: second call skips
    assert ps.main(["--read-dir", "x", "--mesh", "x", "--window-x", "0", "--window-y", "0", "--scroll", "a", "--volume", "b",
                    "--um", "9.362", "--letters", "x", "--heldout", "x", "--method", "x", "--checkpoint", "c", "--call", "c",
                    "--docker-image", "d", "--out", out]) == 0


def test_tampered_forward_window_fails(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    p = os.path.join(out, "forward_window.tif")
    a = tifffile.imread(p); a[10, 10] ^= 0xFF; tifffile.imwrite(p, a)
    f = fails(vp.verify(out))
    # the byte-identity check fails, and the PNGs (still showing the original crop) no longer match the TIFF
    assert len(f) == 3 and any("byte-identical" in s for s in f) and sum("map pixels" in s for s in f) == 2, f


def test_wrong_bar_length_fails(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    p = os.path.join(out, "seg_flat.png")
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    m = np.all(img == np.array(ps.BAR_BGR, np.uint8), axis=2)
    ys, xs = np.nonzero(m)
    img[ys.min():ys.max() + 1, xs.max() - 2:xs.max() + 1] = ps.BG   # shorten the bar by 3 px
    cv2.imwrite(p, img)
    f = fails(vp.verify(out))
    assert len(f) == 1 and "1 cm bar in seg_flat.png" in f[0] and "measured %d" % (BAR - 3) in f[0], f


def test_wrong_volume_not_eligible(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521125822", letters12())
    f = fails(vp.verify(out))
    assert len(f) == 1 and "not eligible" in f[0]


def test_tampered_png_map_fails(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    for name in ("seg_flat.png", "reverse_window.png", "rows.png", "ct_window.png"):
        p = os.path.join(out, name)
        img = cv2.imread(p, cv2.IMREAD_COLOR); orig = img.copy()
        img[:SIDE, :SIDE] = np.clip(img[:SIDE, :SIDE].astype(np.int16) * 2 - 60, 0, 255).astype(np.uint8)   # "enhanced"
        cv2.imwrite(p, img)
        f = fails(vp.verify(out))
        # ct_window.png is now cross-checked TWICE - against the crop the package carries and against the live
        # render - so tampering with it must fail both, not one. Every other image has a single source of truth.
        want = 2 if name == "ct_window.png" else 1
        assert len(f) == want and all(x.startswith(name + " map pixels") for x in f), f
        cv2.imwrite(p, orig)
    assert fails(vp.verify(out)) == []


def test_source_inside_package_or_self_compare_fails(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    pj = os.path.join(out, "package.json"); pkg = json.load(open(pj))
    src_fw = os.path.join(out, "forward_window.tif")
    tifffile.imwrite(src_fw, np.full((SIDE, SIDE), 7, np.uint8))
    pkg["source"]["forward_tif"] = src_fw; pkg["window"]["x"] = pkg["window"]["y"] = 0
    pkg["source"]["forward_tif_sha256"] = ps.sha256_file(src_fw)
    json.dump(pkg, open(pj, "w"))
    f = fails(vp.verify(out))
    assert any("byte-identical" in s and "inside the package" in s for s in f), f
    # a source outside the package that is the window file itself, and a modified source, both fail
    import shutil
    ext = str(tmp_path / "copy.tif"); shutil.copyfile(src_fw, ext)
    pkg["source"]["forward_tif"] = ext; json.dump(pkg, open(pj, "w"))
    f = fails(vp.verify(out))
    assert any("byte-identical" in s and "IS the window file" in s for s in f), f


def test_modified_source_fails_sha(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    src = os.path.join(tmp_path, "read", "forward.tif")
    a = tifffile.imread(src); a[0, 0] ^= 0xFF; tifffile.imwrite(src, a)   # outside the window: crop still identical
    f = fails(vp.verify(out))
    assert len(f) == 1 and "byte-identical" in f[0] and "differs from recorded" in f[0], f


def test_flattened_false_fails(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12(), name="seg_x")
    pj = os.path.join(out, "package.json"); pkg = json.load(open(pj))
    mp = os.path.join(out, "mesh", "seg_flat", "meta.json")
    # the dir is named seg_flat; rename the copy to drop the _flat hint and set flattened=false
    import shutil
    shutil.move(os.path.join(out, "mesh", "seg_flat"), os.path.join(out, "mesh", "seg"))
    shutil.move(os.path.join(out, "seg_flat.png"), os.path.join(out, "seg.png"))
    mp = os.path.join(out, "mesh", "seg", "meta.json")
    meta = json.load(open(mp)); meta["flattened"] = False; json.dump(meta, open(mp, "w"))
    pkg["mesh"]["dir"] = "mesh/seg"; pkg["mesh"]["sha256"]["meta.json"] = ps.sha256_file(mp)
    json.dump(pkg, open(pj, "w"))
    f = fails(vp.verify(out))
    assert len(f) == 1 and "flattened" in f[0], f


def test_inconsistent_letter_coords_fail(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    pj = os.path.join(out, "package.json"); pkg = json.load(open(pj))
    for l in pkg["letters"]:
        l["x_px"] = 999999
    json.dump(pkg, open(pj, "w"))
    f = fails(vp.verify(out))
    assert len(f) == 1 and "fewer than 10 letters" in f[0], f


def _row_pixels_outside_letters(rows_png, letters, x0, y0):
    img = cv2.imread(rows_png, cv2.IMREAD_COLOR)
    m = np.all(img[:SIDE, :SIDE] == np.array(vp.ROW_BGR, np.uint8), axis=2)
    assert m.any()
    for l in letters:
        xw, yw = l["x"] - x0, l["y"] - y0
        assert not m[yw:yw + l["h_px"], xw:xw + l["w_px"]].any(), l


def test_baseline_moves_into_gap_when_next_row_is_close(tmp_path):
    # row 1 has a tall letter; row 2 starts 2 px below it -> bottom+2 would cross row 2
    L = [{"x": X0 + 300 + c * 400, "y": Y0 + 300, "w_px": 250, "h_px": 320 if c else 500, "reading": "ΑΒΓΔ"[c]} for c in range(4)]
    L += [{"x": X0 + 300 + c * 400, "y": Y0 + 300 + 502, "w_px": 250, "h_px": 320, "reading": "ΑΒΓΔ"[c]} for c in range(4)]
    L += [{"x": X0 + 300 + c * 400, "y": Y0 + 1300, "w_px": 250, "h_px": 320, "reading": "ΑΒΓΔ"[c]} for c in range(4)]
    out = build(tmp_path, "PHerc0175A", "20250521115057", L)
    _row_pixels_outside_letters(os.path.join(out, "rows.png"), L, X0, Y0)
    pkg = json.load(open(os.path.join(out, "package.json")))
    assert len(pkg["rows"]) == 3 and pkg["rows"][0]["baseline_px"] == 300 + 500 + 0   # midpoint of the 2 px gap
    assert fails(vp.verify(out)) == []


def test_baseline_at_window_edge(tmp_path):
    # last row's bottom is 1 px above the window edge: baseline must be that free line, never clamped onto letters
    L = letters12()[:8] + [{"x": X0 + 300 + c * 400, "y": Y0 + SIDE - 336, "w_px": 250, "h_px": 335, "reading": "Ε"} for c in range(4)]
    out = build(tmp_path, "PHerc0175A", "20250521115057", L)
    _row_pixels_outside_letters(os.path.join(out, "rows.png"), L, X0, Y0)
    pkg = json.load(open(os.path.join(out, "package.json")))
    assert pkg["rows"][-1]["baseline_px"] == SIDE - 1
    # bottom == side: no free line -> packager fails loudly
    L2 = letters12()[:8] + [{"x": X0 + 300 + c * 400, "y": Y0 + SIDE - 335, "w_px": 250, "h_px": 335, "reading": "Ε"} for c in range(4)]
    (tmp_path / "b").mkdir()
    with pytest.raises(SystemExit):
        build(tmp_path / "b", "PHerc0175A", "20250521115057", L2)


def test_complete_marker_absent_on_file_failure(tmp_path):
    out = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    assert os.path.exists(os.path.join(out, ".complete"))
    os.remove(os.path.join(out, ".complete")); os.remove(os.path.join(out, "rows.png"))
    # rebuild with an unreadable mesh copy step? simplest: verify FAIL on a file-derived check must not write .complete
    checks = vp.verify(out)
    assert any(not c[1] for c in checks)
    assert not os.path.exists(os.path.join(out, ".complete"))


# ---------- the package must stay verifiable after the source render is pruned (2026-09-19)

def test_package_carries_its_own_ct_crop_and_verifies_without_the_render(tmp_path):
    """The verifier proved ct_window.png unaltered by re-opening the source render zarr -- an external path that the
    disk guard prunes routinely and --delete-renders removes on purpose. The P-DRY package failed for exactly that
    reason. The raw crop now travels inside the package with its own sha256."""
    import shutil
    pkg = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    src = os.path.join(pkg, "ct_window_source.tif")
    assert os.path.exists(src), "the package must carry the CT crop it used"
    man = json.load(open(os.path.join(pkg, "package.json")))["source"]
    got = __import__("hashlib").sha256(np.ascontiguousarray(tifffile.imread(src)).tobytes()).hexdigest()
    assert got == man["ct_window_sha256"]

    checks = vp.verify(pkg)
    assert fails(checks) == [], fails(checks)
    assert nas(checks) == [], "with the render present nothing should be N/A"

    # prune the render exactly as the disk guard does
    shutil.rmtree(os.path.join(str(tmp_path / "read"), "render.zarr"))
    checks = vp.verify(pkg)
    assert fails(checks) == [], fails(checks)
    assert nas(checks) == ["ct_window.png map pixels equal the LIVE render slice crop"], nas(checks)


def test_a_tampered_packaged_ct_crop_is_caught_by_its_sha256(tmp_path):
    pkg = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    src = os.path.join(pkg, "ct_window_source.tif")
    a = tifffile.imread(src); a[0, 0] = 255 - a[0, 0]
    tifffile.imwrite(src, a)
    bad = fails(vp.verify(pkg))
    assert any("sha256" in b for b in bad), bad


def test_a_package_with_no_ct_crop_is_refused_not_skipped(tmp_path):
    """An older package that predates this must FAIL, not quietly pass with the check missing."""
    import os as _os
    pkg = build(tmp_path, "PHerc0175A", "20250521115057", letters12())
    _os.remove(_os.path.join(pkg, "ct_window_source.tif"))
    bad = fails(vp.verify(pkg))
    assert any("ct_window_source.tif" in b for b in bad), bad
