#!/usr/bin/env python
"""package_submission.py -- build the First Letters submission package (MASTER_PROMPT_v4 5.14, rule 1).

Inputs: a read directory (forward.tif, reverse.tif as stored by the reader, the render zarr with group "0"), the
FLATTENED tifxyz mesh (5.13), the window corner, scroll/volume/um, letters.json, heldout.md, method.md, checkpoint,
exact call, Docker image. The window side is round(20000 / um) px, i.e. 4.00 cm^2. Nothing is enhanced: the
window TIFFs are unaltered crops; the PNGs show the crop as stored with a 1 cm bar of exactly round(10000 / um) px
drawn in a footer margin OUTSIDE the map area, in a unique colour (contact_sheet.BAR_BGR) so a verifier can measure it.
letters.json: list of {"x", "y", "w_px", "h_px", "reading"}; x, y = top-left corner in SOURCE map pixels (forward.tif
coordinates); mm sizes are derived from um. Rows: an explicit "row" field in letters.json when present, else letters
grouped by vertical centre (new row when the centre gap exceeds ROW_GAP_FRAC x median letter height; a layout
heuristic, not a spec constant, recorded in package.json under rows_rule). rows.png draws a thin baseline 2 px below
each row's bottom; if any letter rectangle covers that line it moves into the gap to the next row, and if no free line
exists inside the map the packager fails loudly (never drawn over a letter, never clamped into the map).
The mesh is copied with SHA-256 for every file. Flattened flag: meta.json "flattened" is truthy, or the mesh dir name
ends with _flat, or --flattened-by names the tool (then the COPIED meta.json records it; the source is never touched).
package.json also records the SHA-256 of the source forward.tif so the verifier can prove the source is unchanged.
Idempotent: writes .complete and skips finished work; --force rebuilds. Runs verify_package.py at the end.
usage: package_submission.py --read-dir D --mesh M --window-x X --window-y Y --scroll S --volume V --um UM
       --letters letters.json --heldout heldout.md --method method.md --checkpoint C --call 'CMD'
       --docker-image REF --out packages/<scroll>_<date>/ [--flattened-by 'vc_flatten ABF++'] [--force]
"""
import argparse, hashlib, json, os, shutil, sys, datetime
import numpy as np, cv2, tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contact_sheet import BAR_BGR, TEXT_BGR, BG, FONT, bar_px, gray_to_bgr  # noqa: E402
from verify_package import ROW_BGR  # noqa: E402  baseline colour in rows.png (measured by the verifier)

FOOTER_H = 48           # margin below the map; the bar and the um/px text live here, never over the map
ROW_GAP_FRAC = 0.6      # row grouping heuristic (layout only, no claim depends on it)
ROWS_RULE = "explicit 'row' field if present, else new row when centre gap > %.1f x median h_px; baseline at bottom+2 " \
            "moved into the inter-row gap when a letter covers it, never clamped into the map" % ROW_GAP_FRAC
MESH_FILES = ("x.tif", "y.tif", "z.tif", "meta.json")


def window_side(um):
    """Side in px of the 4.00 cm^2 window: round(20000 / um)."""
    return int(round(20000.0 / float(um)))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def load_map(path):
    a = tifffile.imread(path)
    if a.ndim == 3:
        a = a[0]
    if a.dtype != np.uint8:
        raise SystemExit("%s: expected a uint8 map, got %s" % (path, a.dtype))
    return a


def crop(a, x, y, side):
    if x < 0 or y < 0 or y + side > a.shape[0] or x + side > a.shape[1]:
        raise SystemExit("window (%d,%d) side %d does not fit map %s" % (x, y, side, a.shape))
    return np.ascontiguousarray(a[y:y + side, x:x + side])


def panel(gray, um, label, draw=None):
    """Map as stored (1:1, no stretch) over a footer holding the 1 cm bar (BAR_BGR, exactly bar_px(um) wide)."""
    h, w = gray.shape
    img = np.zeros((h + FOOTER_H, w, 3), np.uint8)
    img[:] = BG
    img[:h, :w] = gray_to_bgr(gray)
    if draw is not None:
        draw(img)
    b = bar_px(um)
    y0 = h + 12
    img[y0:y0 + 8, 8:8 + b] = BAR_BGR
    cv2.putText(img, "1 cm = %d px  (%.3f um/px)  %s" % (b, um, label), (8, h + FOOTER_H - 10), FONT, 0.5,
                TEXT_BGR, 1, cv2.LINE_AA)
    return img


def group_rows(letters):
    """Rows by the explicit 'row' field when every letter has one, else by vertical centre (ROW_GAP_FRAC rule)."""
    if not letters:
        return []
    if all(l.get("row") is not None for l in letters):
        keys = sorted({l["row"] for l in letters}); rows = [[l for l in letters if l["row"] == k] for k in keys]
    else:
        med_h = float(np.median([l["h_px"] for l in letters]))
        rows, cur = [], []
        for l in sorted(letters, key=lambda l: l["y_win"] + l["h_px"] / 2.0):
            yc = l["y_win"] + l["h_px"] / 2.0
            if cur and yc - float(np.mean([c["y_win"] + c["h_px"] / 2.0 for c in cur])) > ROW_GAP_FRAC * med_h:
                rows.append(cur); cur = []
            cur.append(l)
        rows.append(cur)
    out = []
    for r in rows:
        out.append({"n_letters": len(r), "top_px": int(min(l["y_win"] for l in r)),
                    "bottom_px": int(max(l["y_win"] + l["h_px"] for l in r)),
                    "x0_px": int(min(l["x_win"] for l in r)), "x1_px": int(max(l["x_win"] + l["w_px"] for l in r)),
                    "readings": "".join(str(l.get("reading", "?")) for l in r)})
    return sorted(out, key=lambda r: r["bottom_px"])


def covered(y, xa, xb, letters):
    """True if any letter rectangle contains scan line y between columns xa..xb (window coordinates)."""
    return any(l["y_win"] <= y < l["y_win"] + l["h_px"] and l["x_win"] <= xb and l["x_win"] + l["w_px"] > xa
               for l in letters)


def baseline_y(row, next_top, side, letters):
    """Row baseline: bottom+2, else the midpoint of the gap to the next row; SystemExit if no free line in the map."""
    xa, xb = max(0, row["x0_px"] - 10), min(side - 1, row["x1_px"] + 10)
    for y in (row["bottom_px"] + 2, (row["bottom_px"] + min(next_top, side) - 1) // 2):
        if row["bottom_px"] <= y < side and not covered(y, xa, xb, letters):
            return y
    raise SystemExit("rows.png: no free baseline below row %r (bottom %d, next top %d, side %d)"
                     % (row["readings"], row["bottom_px"], next_top, side))


def draw_rows(img, rows, side, letters):
    """Thin 1 px baseline per row, spanning its letters +-10 px, never over any letter and never clamped into the map."""
    for i, r in enumerate(rows):
        y = baseline_y(r, rows[i + 1]["top_px"] if i + 1 < len(rows) else side, side, letters)
        r["baseline_px"] = y
        cv2.line(img, (max(0, r["x0_px"] - 10), y), (min(side - 1, r["x1_px"] + 10), y), ROW_BGR, 1)


def prepare_letters(raw, x0, y0, side, um):
    out = []
    for i, l in enumerate(raw):
        x, y, w, h = int(l["x"]), int(l["y"]), int(l["w_px"]), int(l["h_px"])
        d = {"index": i, "x_px": x, "y_px": y, "x_win": x - x0, "y_win": y - y0, "w_px": w, "h_px": h,
             "w_mm": round(w * um / 1000.0, 3), "h_mm": round(h * um / 1000.0, 3), "reading": l.get("reading", "")}
        d["inside_window"] = bool(0 <= d["x_win"] and d["x_win"] + w <= side and 0 <= d["y_win"] and d["y_win"] + h <= side)
        if l.get("row") is not None:
            d["row"] = l["row"]
        out.append(d)
    return out


def copy_mesh(mesh_dir, dst, flattened_by):
    """Copy the mesh dir, optionally recording --flattened-by in the COPY's meta.json; return {relpath: sha256}."""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(mesh_dir, dst)
    meta_p = os.path.join(dst, "meta.json")
    meta = json.load(open(meta_p))
    if flattened_by and not meta.get("flattened"):
        meta["flattened"] = {"tool": flattened_by, "recorded_by": "package_submission.py"}
        json.dump(meta, open(meta_p, "w"), indent=2)
    hashes = {}
    for root, _, files in os.walk(dst):
        for f in sorted(files):
            p = os.path.join(root, f)
            hashes[os.path.relpath(p, dst)] = sha256_file(p)
    return hashes, meta


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("--read-dir", "--mesh", "--scroll", "--volume", "--letters", "--heldout", "--method", "--checkpoint",
              "--call", "--docker-image", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--window-x", type=int, required=True); ap.add_argument("--window-y", type=int, required=True)
    ap.add_argument("--um", type=float, required=True, help="um/px from the volume metadata.json (never a default)")
    ap.add_argument("--flattened-by", default=None, help="tool that flattened the mesh, e.g. 'vc_flatten ABF++'")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    if os.path.exists(os.path.join(out, ".complete")) and not a.force:
        print("exists, skipping", out); return 0
    for f in MESH_FILES:
        if not os.path.exists(os.path.join(a.mesh, f)):
            raise SystemExit("mesh %s lacks %s" % (a.mesh, f))
    os.makedirs(out, exist_ok=True)
    side, x0, y0 = window_side(a.um), a.window_x, a.window_y
    fwd_src = os.path.abspath(os.path.join(a.read_dir, "forward.tif"))
    rev_src = os.path.abspath(os.path.join(a.read_dir, "reverse.tif"))
    fwd, rev = crop(load_map(fwd_src), x0, y0, side), crop(load_map(rev_src), x0, y0, side)
    tifffile.imwrite(os.path.join(out, "forward_window.tif"), fwd)
    tifffile.imwrite(os.path.join(out, "reverse_window.tif"), rev)
    mesh_name = os.path.basename(os.path.normpath(a.mesh))
    hashes, meta = copy_mesh(a.mesh, os.path.join(out, "mesh", mesh_name), a.flattened_by)
    flattened = bool(meta.get("flattened")) or mesh_name.endswith("_flat")
    letters = prepare_letters(json.load(open(a.letters)), x0, y0, side, a.um)
    inside = [l for l in letters if l["inside_window"]]
    rows = group_rows(inside)
    lab = "%s %s" % (a.scroll, a.volume)
    cv2.imwrite(os.path.join(out, mesh_name + ".png"), panel(fwd, a.um, "forward " + lab))
    cv2.imwrite(os.path.join(out, "reverse_window.png"), panel(rev, a.um, "reverse " + lab))
    cv2.imwrite(os.path.join(out, "rows.png"), panel(fwd, a.um, "forward, row baselines " + lab,
                                                     draw=lambda im: draw_rows(im, rows, side, inside)))
    import zarr
    render = zarr.open_group(os.path.join(a.read_dir, "render.zarr"), mode="r")["0"]
    zmid = render.shape[0] // 2
    ct = np.asarray(render[zmid, y0:y0 + side, x0:x0 + side], dtype=np.uint8)
    cv2.imwrite(os.path.join(out, "ct_window.png"), panel(ct, a.um, "CT slice %d/%d %s" % (zmid, render.shape[0], lab)))
    # The package must stay VERIFIABLE after the render is gone. The verifier proved ct_window.png unaltered by
    # re-opening the source render zarr -- an external path that our own disk guard prunes routinely and that
    # --delete-renders removes on purpose. On 2026-09-19 the P-DRY package failed that check for exactly that
    # reason. The raw crop now travels inside the package, with its own sha256 in the manifest, so the strong
    # check (against the live render) is kept when possible and a real check survives when it is not.
    tifffile.imwrite(os.path.join(out, "ct_window_source.tif"), ct)
    ct_sha = hashlib.sha256(ct.tobytes()).hexdigest()
    heldout, method = open(a.heldout).read(), open(a.method).read()
    shutil.copyfile(a.heldout, os.path.join(out, "heldout.md")); shutil.copyfile(a.method, os.path.join(out, "method.md"))
    mm = side * a.um / 1000.0
    pkg = {"scroll": a.scroll, "volume": a.volume, "um_per_px": a.um, "created": datetime.datetime.now().isoformat(),
           "window": {"x": x0, "y": y0, "side_px": side, "side_mm": round(mm, 4), "area_cm2": round(mm * mm / 100.0, 4)},
           "bar_px": bar_px(a.um), "bar_bgr": list(BAR_BGR), "footer_px": FOOTER_H,
           "source": {"read_dir": os.path.abspath(a.read_dir), "forward_tif": fwd_src, "reverse_tif": rev_src,
                      "forward_tif_sha256": sha256_file(fwd_src), "reverse_tif_sha256": sha256_file(rev_src),
                      "forward_window_sha256": hashlib.sha256(fwd.tobytes()).hexdigest(),
                      "reverse_window_sha256": hashlib.sha256(rev.tobytes()).hexdigest(), "render_zarr": "render.zarr",
                      "ct_slice": zmid, "ct_window_source_tif": "ct_window_source.tif", "ct_window_sha256": ct_sha, "mesh_dir": os.path.abspath(a.mesh)},
           "orders": {"forward": "forward_window.tif", "reverse": "reverse_window.tif"},
           "images": {"forward_png": mesh_name + ".png", "reverse_png": "reverse_window.png", "ct_png": "ct_window.png",
                      "rows_png": "rows.png"},
           "mesh": {"name": mesh_name, "dir": "mesh/" + mesh_name, "flattened": flattened, "flattened_by": a.flattened_by,
                    "sha256": hashes},
           "checkpoint": a.checkpoint, "call": a.call, "docker_image": a.docker_image,
           "letters": letters, "n_letters_in_window": sum(l["inside_window"] for l in letters), "rows": rows, "rows_rule": ROWS_RULE,
           "heldout_text": heldout, "method_text": method, "heldout_file": "heldout.md", "method_file": "method.md"}
    json.dump(pkg, open(os.path.join(out, "package.json"), "w"), indent=2)
    import verify_package
    checks = verify_package.verify(out)
    report = "\n".join(verify_package.fmt(c) for c in checks) + "\n"
    open(os.path.join(out, "verify_report.txt"), "w").write(report)
    print(report, end="")
    # the marker is written only when every FILE-derived check passed; the two dry-run outcomes (not eligible,
    # fewer than 10 letters) do not block it, any other FAIL leaves the marker absent so the next run rebuilds
    if all(c[1] for c in checks if c[0] not in verify_package.DRY_RUN_CHECKS):
        open(os.path.join(out, ".complete"), "w").write(datetime.datetime.now().isoformat() + "\n")
    return 0 if all(c[1] for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
