#!/usr/bin/env python
"""verify_package.py -- re-derive every submission check from the package FILES (MASTER_PROMPT_v4 5.14, section 1).

package.json is used only for what files cannot carry (um/px, window corner, source paths, letter list, scroll and
volume id); every number is recomputed from the TIFFs, PNGs, mesh files and text files:
  window area 4.00 +- 1 % cm^2 from the forward_window.tif dimensions and um; side = round(20000 / um)
  1 cm bar = round(10000 / um) +- 1 px measured as the longest run of BAR_BGR pixels in every PNG, located in the
    margin below the map (never over it)
  forward_window.tif byte-identical (pixel bytes) to the crop of the source forward.tif; the source must lie OUTSIDE
    the package dir, be larger than the window or differ from the window file (a file is never compared with itself),
    and its SHA-256 must match the value recorded at packaging time; reverse present, same shape
  the map area of every PNG equals the window TIFF pixels (grey, all three channels): forward PNG vs forward_window,
    reverse PNG vs reverse_window, rows.png vs forward outside its 1 px ROW_BGR baselines (which must lie in no letter
    rectangle), ct_window.png vs the recorded slice of the source render zarr -- an enhanced or redrawn image fails
  mesh present (x/y/z.tif + meta.json), SHA-256 of every file matches, flattened flag from meta.json or the _flat name
  >= 10 letters inside the window, each with w/h in px and mm consistent with um
  held-out text and method present and non-empty (files and package.json), both depth orders present
  scroll on the eligible list with the matching volume id; the forward PNG named after the mesh directory
Prints one line per check (PASS/FAIL) and exits nonzero if any FAIL.
usage: verify_package.py <package dir>
"""
import argparse, hashlib, json, os, sys
import numpy as np, cv2, tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contact_sheet import BAR_BGR, bar_px  # noqa: E402

# Section 1 of MASTER_PROMPT_v4 (saved 2026-09-11): scroll -> eligible volume id.
ELIGIBLE = {
    "PHerc0125": "20250821151825", "PHerc0175A": "20250521115057", "PHerc0175B": "20250521125822",
    "PHerc0191": "20250821151635", "PHerc0211": "20250821151803", "PHerc0257": "20250821151750",
    "PHerc0268": "20251110183117", "PHerc0306B": "20250521133212", "PHerc0343": "20250521140437",
    "PHerc0358": "20250821151737", "PHerc0483A": "20250521140913", "PHerc0483B": "20251124083638",
    "PHerc0490A": "20250521151210", "PHerc0490B": "20250521151215", "PHerc0800": "20250521135224",
    "PHerc0813": "20250821151723", "PHerc0826": "20250821151701", "PHerc0846A": "20250728152254",
    "PHerc0846B": "20250804142305", "PHerc1203": "20250820131727", "PHerc1218": "20250521120456",
    "PHerc1447": "20250521151220", "PHerc1545": "20250821151648"}
ROW_BGR = (0, 255, 0)   # rows.png baseline colour (pure green: not producible by a grey map)
AREA_CM2, AREA_TOL, MIN_LETTERS, BAR_TOL = 4.00, 0.01, 10, 1
DRY_RUN_CHECKS = ("scroll eligible with matching volume", ">= 10 letters inside the window with sizes")
MESH_FILES = ("x.tif", "y.tif", "z.tif", "meta.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def measure_bar(png_path):
    """(longest horizontal run of BAR_BGR pixels, first row of the bar) measured from the PNG; (0, -1) if absent."""
    img = cv2.imread(png_path, cv2.IMREAD_COLOR)
    if img is None:
        return 0, -1
    m = np.all(img == np.array(BAR_BGR, np.uint8), axis=2)
    best, top = 0, -1
    for r in np.flatnonzero(m.any(axis=1)):
        row = m[r]
        run, cur = 0, 0
        for v in row:
            cur = cur + 1 if v else 0
            run = max(run, cur)
        if run > best:
            best, top = run, int(r)
    return best, top


def map_matches(img, ref, mask=None):
    """True if the PNG's map area (rows 0..h, all 3 channels) equals grey `ref`, ignoring pixels where mask is True."""
    h, w = ref.shape
    if img is None or img.ndim != 3 or img.shape[0] <= h or img.shape[1] != w:
        return False
    m = img[:h, :w]
    eq = (m[:, :, 0] == ref) & (m[:, :, 1] == ref) & (m[:, :, 2] == ref)
    return bool(eq[~mask].all() if mask is not None else eq.all())


def verify(pkg_dir):
    """Return a list of (check name, ok, detail)."""
    out = []
    pkg_dir = os.path.realpath(pkg_dir)
    # ok is True, False, or None for "could not be run". None is NOT a pass: it is printed as N/A, counted
    # separately and never hidden. It exists so that a check whose INPUT is gone (the live render, which the disk
    # guard prunes) does not masquerade as a failure of the package, while a check that genuinely failed still does.
    add = lambda name, ok, detail="": out.append((name, (None if ok is None else bool(ok)), detail))
    pj = os.path.join(pkg_dir, "package.json")
    if not os.path.exists(pj):
        add("package.json present", False, pj); return out
    p = json.load(open(pj))
    um, win = float(p["um_per_px"]), p["window"]
    side, b = int(round(20000.0 / um)), bar_px(um)
    fw_p = os.path.join(pkg_dir, "forward_window.tif")
    fw = tifffile.imread(fw_p) if os.path.exists(fw_p) else None
    if fw is None:
        add("forward_window.tif present", False, fw_p); return out
    h, w = fw.shape[:2]
    area = (h * um / 1e4) * (w * um / 1e4)
    add("window area 4.00 cm^2 +-1%%" % (), abs(area - AREA_CM2) <= AREA_TOL * AREA_CM2 and h == side and w == side,
        "%dx%d px at %.3f um/px = %.4f cm^2 (side round(20000/um) = %d)" % (w, h, um, area, side))
    # source byte identity
    src = p["source"]["forward_tif"]
    x0, y0 = int(win["x"]), int(win["y"])
    if not os.path.exists(src):
        add("forward window byte-identical to source crop", False, "source missing: " + src)
    elif os.path.commonpath([os.path.realpath(src), pkg_dir]) == pkg_dir:
        add("forward window byte-identical to source crop", False, "source lies inside the package: " + src)
    else:
        s = tifffile.imread(src)
        s = s[0] if s.ndim == 3 else s
        sc = np.ascontiguousarray(s[y0:y0 + h, x0:x0 + w])
        ident = sc.shape == fw.shape and sc.dtype == fw.dtype and sc.tobytes() == np.ascontiguousarray(fw).tobytes()
        distinct = (s.shape[0] > h or s.shape[1] > w) or sha256_file(src) != sha256_file(fw_p)
        rec = p["source"].get("forward_tif_sha256")
        unchanged = rec is not None and sha256_file(src) == rec
        add("forward window byte-identical to source crop", ident and distinct and unchanged,
            "%s [%d:%d, %d:%d] vs forward_window.tif; source %s, sha256 %s recorded value"
            % (src, y0, y0 + h, x0, x0 + w, "distinct from window file" if distinct else "IS the window file",
               "matches" if unchanged else "differs from"))
    rv_p = os.path.join(pkg_dir, "reverse_window.tif")
    rv = tifffile.imread(rv_p) if os.path.exists(rv_p) else None
    add("reverse order present", rv is not None and rv.shape == fw.shape and rv.dtype == fw.dtype
        and os.path.exists(os.path.join(pkg_dir, "reverse_window.png")),
        "reverse_window.tif %s, reverse_window.png" % (None if rv is None else rv.shape,))
    add("both orders in package.json", set(p.get("orders", {})) == {"forward", "reverse"}, str(p.get("orders")))
    # mesh
    mdir = os.path.join(pkg_dir, p["mesh"]["dir"])
    mname = os.path.basename(os.path.normpath(mdir))
    present = all(os.path.exists(os.path.join(mdir, f)) for f in MESH_FILES)
    add("mesh present (x/y/z.tif + meta.json)", present, mdir)
    if present:
        rec = p["mesh"]["sha256"]
        found = {}
        for root, _, files in os.walk(mdir):
            for f in files:
                found[os.path.relpath(os.path.join(root, f), mdir)] = sha256_file(os.path.join(root, f))
        bad = sorted(k for k in set(rec) | set(found) if rec.get(k) != found.get(k))
        add("mesh SHA-256 hashes match", not bad and len(found) >= 4, "%d files hashed%s" % (len(found), "; mismatch: %s" % bad if bad else ""))
        meta = json.load(open(os.path.join(mdir, "meta.json")))
        flat = bool(meta.get("flattened")) or mname.endswith("_flat")
        add("mesh flattened flag", flat, "meta.json flattened=%s, dir name %s" % (meta.get("flattened"), mname))
    # PNGs: named after the mesh, bar length, bar in the margin (below the map rows)
    pngs = [mname + ".png", "reverse_window.png", "ct_window.png", "rows.png"]
    add("image named after the mesh", os.path.exists(os.path.join(pkg_dir, mname + ".png")), mname + ".png")
    for name in pngs:
        fp = os.path.join(pkg_dir, name)
        if not os.path.exists(fp):
            add("1 cm bar in %s" % name, False, "missing"); continue
        L, top = measure_bar(fp)
        img_h = cv2.imread(fp, cv2.IMREAD_COLOR).shape[0]
        add("1 cm bar in %s" % name, abs(L - b) <= BAR_TOL and top >= h and img_h > h,
            "measured %d px, expected round(10000/um) = %d +-%d; bar row %d, map rows 0..%d" % (L, b, BAR_TOL, top, h - 1))
    # letters: window coordinates re-derived from the source coordinates and the window corner
    ok_l, n_in, rects = [], 0, []
    for l in p.get("letters", []):
        wpx, hpx = l.get("w_px"), l.get("h_px")
        xw, yw = int(l["x_px"]) - x0, int(l["y_px"]) - y0
        consistent = (xw, yw) == (l.get("x_win"), l.get("y_win"))
        inside = consistent and (0 <= xw and xw + wpx <= w and 0 <= yw and yw + hpx <= h)
        sizes = (wpx and hpx and abs(l.get("w_mm", -1) - wpx * um / 1000.0) < 0.002
                 and abs(l.get("h_mm", -1) - hpx * um / 1000.0) < 0.002 and str(l.get("reading", "")) != "")
        if inside and sizes:
            n_in += 1; rects.append((xw, yw, wpx, hpx))
        ok_l.append(inside and sizes)
    # PNG map areas equal the window TIFF pixels (never enhanced or redrawn)
    rv_ref = rv if rv is not None and rv.shape == fw.shape else None
    for name, ref in ((mname + ".png", fw), ("reverse_window.png", rv_ref)):
        img = cv2.imread(os.path.join(pkg_dir, name), cv2.IMREAD_COLOR)
        add("%s map pixels equal the window TIFF" % name, ref is not None and map_matches(img, ref), name)
    img = cv2.imread(os.path.join(pkg_dir, "rows.png"), cv2.IMREAD_COLOR)
    if img is not None and img.shape[0] > h and img.shape[1] == w:
        rmask = np.all(img[:h, :w] == np.array(ROW_BGR, np.uint8), axis=2)
        rows_with = np.flatnonzero(rmask.any(axis=1))
        thin = len(rows_with) == 0 or np.all(np.diff(rows_with) > 1)
        over = any(rmask[yw:yw + hpx, xw:xw + wpx].any() for xw, yw, wpx, hpx in rects)
        ok = map_matches(img, fw, rmask) and thin and not over
        det = "%d baseline rows, %s, %s" % (len(rows_with), "1 px thin" if thin else "thick", "over a letter" if over else "outside letters")
    else:
        ok, det = False, "missing or wrong size"
    add("rows.png map pixels equal forward window outside 1 px baselines", ok, det)
    # The CT window is checked against the crop the package CARRIES, whose sha256 is in the manifest, and -- when the
    # source render is still on disk -- additionally against the live render. The package must stay verifiable after
    # the render is pruned, which our own disk guard does routinely and --delete-renders does on purpose.
    rz = os.path.join(p["source"].get("read_dir", ""), p["source"].get("render_zarr", "render.zarr"))
    img = cv2.imread(os.path.join(pkg_dir, "ct_window.png"), cv2.IMREAD_COLOR)
    src_name = p["source"].get("ct_window_source_tif")
    src_path = os.path.join(pkg_dir, src_name) if src_name else None
    ct_pkg = None
    if src_path and os.path.exists(src_path):
        ct_pkg = tifffile.imread(src_path)
        want = p["source"].get("ct_window_sha256")
        got = hashlib.sha256(np.ascontiguousarray(ct_pkg).tobytes()).hexdigest()
        add("ct_window_source.tif matches its manifest sha256", bool(want) and got == want,
            "%s vs %s" % (got[:16], (want or "-")[:16]))
        add("ct_window.png map pixels equal the packaged CT crop",
            ct_pkg.shape == fw.shape and map_matches(img, ct_pkg), src_name)
    else:
        add("ct_window_source.tif matches its manifest sha256", False,
            "the package carries no CT crop; repackage with a packager that writes ct_window_source.tif")
        add("ct_window.png map pixels equal the packaged CT crop", False, "ct_window_source.tif missing")
    if os.path.exists(rz):
        import zarr
        arr = zarr.open_group(rz, mode="r")["0"]
        ct = np.asarray(arr[int(p["source"]["ct_slice"]), y0:y0 + h, x0:x0 + w], dtype=np.uint8)
        same_live = ct.shape == fw.shape and map_matches(img, ct)
        if ct_pkg is not None:
            same_live = same_live and ct_pkg.shape == ct.shape and bool(np.array_equal(ct_pkg, ct))
        add("ct_window.png map pixels equal the LIVE render slice crop", same_live,
            "%s slice %s" % (rz, p["source"]["ct_slice"]))
    else:
        add("ct_window.png map pixels equal the LIVE render slice crop", None,
            "render zarr pruned (%s); the packaged crop and its sha256 stand in" % rz)
    add(">= 10 letters inside the window with sizes", n_in >= MIN_LETTERS,
        "%d letters inside with px+mm sizes and a reading (%d listed)%s" % (n_in, len(ok_l), "" if n_in >= MIN_LETTERS else " -- fewer than 10 letters"))
    for key, fn in (("heldout_text", "heldout.md"), ("method_text", "method.md")):
        fp = os.path.join(pkg_dir, fn)
        txt = open(fp).read().strip() if os.path.exists(fp) else ""
        add("%s non-empty" % fn, len(txt) > 0 and p.get(key, "").strip() == txt, "%d chars" % len(txt))
    add("checkpoint and exact call recorded", bool(p.get("checkpoint")) and bool(p.get("call")) and bool(p.get("docker_image")),
        "%s | %s | %s" % (p.get("checkpoint"), p.get("call"), p.get("docker_image")))
    sc, vol = p.get("scroll"), str(p.get("volume"))
    elig = ELIGIBLE.get(sc) == vol
    add("scroll eligible with matching volume", elig, "%s %s%s" % (sc, vol, "" if elig else " -- not eligible (section 1 list)"))
    return out


def fmt(c):
    return "%s %s: %s" % ("N/A " if c[1] is None else ("PASS" if c[1] else "FAIL"), c[0], c[2])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package_dir")
    a = ap.parse_args(argv)
    checks = verify(a.package_dir)
    for c in checks:
        print(fmt(c))
    nf = sum(c[1] is False for c in checks)
    na = sum(c[1] is None for c in checks)
    print("%d checks, %d FAIL%s" % (len(checks), nf, ", %d N/A" % na if na else ""))
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
