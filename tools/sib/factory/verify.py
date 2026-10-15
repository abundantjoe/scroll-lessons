# Provenance: Project HERCULES | owner the owner | [id removed]
"""Mechanical verifier for a First Letters package made by factory.py. Nobody views the image.

python verify.py PACKAGE_DIR [--eligible data/catalogue/eligible_products.json] [--json OUT]
Exit 0 only if every check passes. Each check returns (ok, detail); the report lists all of them.
The verifier trusts nothing in the package: geometry constants and tool code come from the verifier's own
copies (this directory), eligibility from the repository catalogue, the voxel size from the packaged
metadata.json (whose sha256 must match package.json)."""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import unicodedata

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src"))
import build_image as BI  # noqa: E402
import pngio  # noqa: E402
from factory import FORMAT, LETTER_COLUMNS, PKG_TOOLS, PROV, REPRODUCE_SH, NAME_RE  # noqa: E402
from hercules.records import cf_scan  # noqa: E402

DEFAULT_ELIGIBLE = os.path.join(HERE, "..", "..", "..", "data", "catalogue", "eligible_products.json")
DRY_RE = re.compile(r"DRY[\s_-]*RUN")
HEX40, HEX64 = re.compile(r"^[0-9a-f]{40}$"), re.compile(r"^[0-9a-f]{64}$")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PATH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
TOP_KEYS = {"provenance", "package_format", "package_name", "package_dir", "dry_run", "scroll", "volume_id",
            "volume_url", "volume_metadata", "voxel_size_um", "voxel_size_source", "mesh_name", "mesh", "image",
            "raw_render", "scale_bar", "render", "letter_table", "selection", "commits", "software", "timestamps"}
SUB_KEYS = {
    "volume_metadata": {"file", "source", "sha256"},
    "mesh": {"dir", "files_sha256", "grid_shape", "source"},
    "image": {"file", "sha256", "shape", "pixels_sha256", "panel_rows", "panel_shape", "panel_sha256", "scale",
              "px_per_mm", "display", "header_rows", "footer_rows", "stamp"},
    "raw_render": {"file", "sha256", "shape", "dtype", "pixels_sha256"},
    "scale_bar": {"length_px", "length_exact_px", "rows", "x0", "height_px", "represents_mm", "formula"},
    "letter_table": {"columns", "units", "rows"},
    "commits": {"hercules_repo", "villa"},
    "software": {"python", "numpy", "opencv"},
    "timestamps": {"package_utc", "render_start_utc", "render_end_utc"},
}
MESH_META_KEYS = {"bbox", "format", "scale", "type", "uuid"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    with open(p, "rb") as f:
        return f.read()


class Ctx:
    def __init__(self, d, eligible):
        self.d = os.path.abspath(d)
        self.eligible = eligible
        self.pkg = None
        self.files = []
        self.img = None
        self.raw = None
        self.voxel = None


def _walk(d):
    out, dirs = [], []
    for dp, dns, fns in os.walk(d):
        for n in dns:
            dirs.append(os.path.relpath(os.path.join(dp, n), d))
        for n in fns:
            out.append(os.path.relpath(os.path.join(dp, n), d))
    return sorted(out), sorted(dirs)


def c_package_json(c):
    p = os.path.join(c.d, "package.json")
    if not os.path.isfile(p):
        return False, "package.json missing"
    try:
        c.pkg = json.loads(read(p).decode("ascii"))
    except Exception as e:  # noqa: BLE001
        return False, f"package.json unreadable as ASCII JSON: {e}"
    k = set(c.pkg)
    if k != TOP_KEYS:
        return False, f"top-level keys differ: extra {sorted(k - TOP_KEYS)}, missing {sorted(TOP_KEYS - k)}"
    for s, keys in SUB_KEYS.items():
        if not isinstance(c.pkg[s], dict) or set(c.pkg[s]) != keys:
            got = set(c.pkg[s]) if isinstance(c.pkg[s], dict) else set()
            return False, f"{s}: extra {sorted(got - keys)}, missing {sorted(keys - got)}"
    if c.pkg["package_format"] != FORMAT:
        return False, f"package_format {c.pkg['package_format']!r} != {FORMAT!r}"
    if not isinstance(c.pkg["dry_run"], bool):
        return False, "dry_run is not a boolean"
    return True, "strict key sets match"


def c_layout(c):
    files, dirs = _walk(c.d)
    c.files = files
    n = c.pkg["mesh_name"]
    want = {f"{n}.png", f"mesh/{n}/x.tif", f"mesh/{n}/y.tif", f"mesh/{n}/z.tif", f"mesh/{n}/meta.json",
            f"render/{n}_raw.npy", "inputs/volume_metadata.json", "reproduce.sh", "package.json", "README.txt",
            "SHA256SUMS"} | {f"tools/{t}" for t in PKG_TOOLS}
    want_dirs = {"mesh", f"mesh/{n}", "render", "inputs", "tools"}
    links = [f for f in files + dirs if os.path.islink(os.path.join(c.d, f))]
    if links:
        return False, f"symlinks present: {links}"
    extra, missing = set(files) - want, want - set(files)
    xd = set(dirs) - want_dirs
    if extra or missing or xd:
        return False, f"extra files {sorted(extra)}, missing {sorted(missing)}, extra dirs {sorted(xd)}"
    return True, f"{len(files)} files, exactly the allowed set"


def c_manifest(c):
    try:
        lines = read(os.path.join(c.d, "SHA256SUMS")).decode("ascii").splitlines()
    except Exception as e:  # noqa: BLE001
        return False, f"SHA256SUMS unreadable: {e}"
    listed = {}
    for ln in lines:
        m = re.match(r"^([0-9a-f]{64})  (\S+)$", ln)
        if not m:
            return False, f"malformed manifest line {ln!r}"
        listed[m.group(2)] = m.group(1)
    others = set(c.files) - {"SHA256SUMS"}
    if set(listed) != others:
        return False, f"manifest covers {sorted(set(listed) ^ others)} wrongly"
    bad = [f for f, hsh in listed.items() if sha(read(os.path.join(c.d, f))) != hsh]
    if bad:
        return False, f"sha256 mismatch: {bad}"
    return True, f"{len(listed)} files hashed and matching"


def c_names(c):
    n = c.pkg["mesh_name"]
    if not NAME_RE.match(n):
        return False, f"mesh name not plain ASCII [A-Za-z0-9._-]: {cf_scan.display(n)!r}"
    bad = [cf_scan.display(f) for f in c.files if not PATH_RE.match(f)]
    if bad:
        return False, f"non-plain-ASCII path names: {bad}"
    if c.pkg["image"]["file"] != n + ".png" or c.pkg["mesh"]["dir"] != f"mesh/{n}":
        return False, "image basename or mesh dir does not equal the mesh name"
    mm = json.loads(read(os.path.join(c.d, "mesh", n, "meta.json")))
    if mm.get("uuid") != n:
        return False, f"mesh meta.json uuid {mm.get('uuid')!r} != mesh name"
    return True, f"image basename == mesh name == {n}"


def _json_cf(o, path="$"):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            out += _json_cf(k, path + ".<key>") + _json_cf(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += _json_cf(v, f"{path}[{i}]")
    elif isinstance(o, str):
        out += [f"{path}: U+{ord(ch):04X}" for ch in o if unicodedata.category(ch) == "Cf"]
    return out


def c_cf(c):
    findings = []
    for path, name_part, is_dir in cf_scan.iter_targets(c.d):
        if is_dir:
            findings += cf_scan.scan_name(path, name_part)
        else:
            findings += [f for f in cf_scan.scan_file(path, name_part=name_part) if f.kind.startswith("cf")]
    txt = [f.format() for f in findings]
    for f in c.files:
        if f.endswith(".json"):
            try:
                txt += [f"{f} (decoded) {x}" for x in _json_cf(json.loads(read(os.path.join(c.d, f))))]
            except Exception as e:  # noqa: BLE001
                txt.append(f"{f}: JSON unreadable ({e})")
    if txt:
        return False, f"{len(txt)} Cf finding(s): {txt[:5]}"
    return True, "no Unicode Cf character in any name, file content or decoded JSON string"


def c_png(c):
    b = read(os.path.join(c.d, c.pkg["image"]["file"]))
    try:
        chunks, trailing = pngio.parse_png_chunks(b)
        c.img = pngio.decode_canonical_png(b)
    except Exception as e:  # noqa: BLE001
        return False, f"PNG rejected: {e}"
    others = [f for f in c.files if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"))]
    if others != [c.pkg["image"]["file"]]:
        return False, f"unexpected image files: {others}"
    if list(c.img.shape) != c.pkg["image"]["shape"] or sha(b) != c.pkg["image"]["sha256"]:
        return False, "PNG shape or sha256 differs from package.json"
    return True, f"canonical PNG, chunks {[t.decode() for t, *_ in chunks]}, no trailing bytes, shape {c.img.shape}"


def c_mesh(c):
    n = c.pkg["mesh_name"]
    md = os.path.join(c.d, "mesh", n)
    shape = None
    for t in ("x.tif", "y.tif", "z.tif"):
        b = read(os.path.join(md, t))
        try:
            tags = pngio.tiff_tags(b)
        except Exception as e:  # noqa: BLE001
            return False, f"{t}: {e}"
        extra = set(tags) - set(pngio.TIFF_TAGS_ALLOWED)
        if extra:
            return False, f"{t}: non-structural TIFF tags {sorted(extra)} (metadata)"
        shp = (tags[257][2], tags[256][2])
        if shape and shp != shape:
            return False, "coordinate TIFF shapes differ"
        shape = shp
        if c.pkg["mesh"]["files_sha256"].get(t) != sha(b):
            return False, f"{t} sha256 differs from package.json"
    mm = json.loads(read(os.path.join(md, "meta.json")))
    if set(mm) != MESH_META_KEYS:
        return False, f"mesh meta.json keys {sorted(mm)} != {sorted(MESH_META_KEYS)}"
    if list(shape) != c.pkg["mesh"]["grid_shape"]:
        return False, "mesh grid shape differs from package.json"
    return True, f"tifxyz grid {shape}, TIFF tags structural only, meta.json keys exact"


def c_voxel(c):
    mp = os.path.join(c.d, c.pkg["volume_metadata"]["file"])
    b = read(mp)
    if sha(b) != c.pkg["volume_metadata"]["sha256"]:
        return False, "volume metadata.json sha256 differs from package.json"
    md = json.loads(b)
    c.voxel = round(float(md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000.0, 6)
    if c.voxel != c.pkg["voxel_size_um"]:
        return False, f"voxel {c.pkg['voxel_size_um']} != metadata {c.voxel}"
    tok = re.search(r"-(\d+\.\d+)um-", c.pkg["volume_url"])
    if not tok or abs(float(tok.group(1)) - c.voxel) > 0.0005:
        return False, f"volume URL voxel token {tok.group(1) if tok else None} disagrees with metadata {c.voxel}"
    radix = md["scan"]["tomo"]["acquisition"].get("scanRadix", "")
    num = c.pkg["scroll"].replace("PHerc", "")
    if f"PHerc_{num}" not in radix and f"PHerc{num}" not in radix:
        return False, f"metadata scanRadix {radix!r} does not name {c.pkg['scroll']}"
    return True, f"voxel {c.voxel} um from metadata.json (URL token and scanRadix agree)"


def c_eligibility(c):
    m = re.match(r"^s3://vesuvius-challenge-open-data/(PHerc[0-9A-Za-z]+)/volumes/([0-9]{14})-[^/]+\.zarr/$",
                 c.pkg["volume_url"])
    if not m:
        return False, f"volume URL is not an official bucket volume: {c.pkg['volume_url']!r}"
    if (m.group(1), m.group(2)) != (c.pkg["scroll"], c.pkg["volume_id"]):
        return False, "scroll/volume_id fields disagree with the volume URL"
    if c.pkg["volume_metadata"]["source"] != c.pkg["volume_url"] + "metadata.json":
        return False, "metadata source is not the volume's own metadata.json"
    src = c.pkg["mesh"]["source"].get("url", "") if isinstance(c.pkg["mesh"]["source"], dict) else ""
    if src and f"-on-{c.pkg['volume_id']}-" not in src:
        return False, f"mesh source {src} is not a mesh on volume {c.pkg['volume_id']}"
    vols = json.load(open(c.eligible))["volumes"]
    hit = [v for v in vols if v["scroll"] == c.pkg["scroll"] and v["volume_id"] == c.pkg["volume_id"]
           and v["volume_zarr_s3"] == c.pkg["volume_url"]]
    if hit:
        return True, f"{c.pkg['scroll']} {c.pkg['volume_id']} is eligible ({len(vols)} in catalogue)"
    if c.pkg["dry_run"]:
        return True, f"NOT ELIGIBLE ({c.pkg['scroll']} {c.pkg['volume_id']}): allowed only because this is a DRY RUN"
    return False, f"{c.pkg['scroll']} {c.pkg['volume_id']} is not an eligible volume"


def c_dry_run(c):
    dry = c.pkg["dry_run"]
    w = c.img.shape[1]
    header = c.img[0:BI.HEADER]
    if dry:
        probs = []
        if not os.path.basename(c.d).startswith("DRY_RUN_") or c.pkg["package_dir"] != os.path.basename(c.d):
            probs.append("package directory name lacks the DRY_RUN_ prefix")
        if not c.pkg["package_name"].startswith("DRY RUN "):
            probs.append("package_name lacks 'DRY RUN '")
        if not np.array_equal(header, BI.stamp_strip(w)):
            probs.append("image corner stamp differs from the DRY RUN stamp")
        if os.path.basename(os.path.dirname(c.d)) != "dryrun":
            probs.append("dry run not under packages/dryrun/")
        return (not probs), ("; ".join(probs) or "DRY RUN in package dir, package name and image corner (pixel-exact)")
    hits = []
    pinned = {f"tools/{t}" for t in PKG_TOOLS}
    for f in c.files:
        if DRY_RE.search(f):
            hits.append(f"name {f}")
        if f in pinned:
            continue  # tool code is pinned byte-identical to the verifier's copy (c_tools)
        b = read(os.path.join(c.d, f))
        if not cf_scan.is_binary(b) and not b.startswith(pngio.PNG_SIG):
            if DRY_RE.search(b.decode("utf-8", "replace")):
                hits.append(f"text in {f}")
    for k in ("package_name", "package_dir"):
        if DRY_RE.search(c.pkg[k]):
            hits.append(k)
    if header.any():
        hits.append(f"header strip has {int((header > 0).sum())} non-zero px (stamp or text)")
    return (not hits), (f"'DRY RUN' in a non-dry-run package: {hits}" if hits else "no DRY RUN marker anywhere")


def c_tools(c):
    bad = [t for t in PKG_TOOLS if read(os.path.join(c.d, "tools", t)) != read(os.path.join(HERE, t))]
    if read(os.path.join(c.d, "reproduce.sh")).decode("utf-8", "replace") != REPRODUCE_SH:
        bad.append("reproduce.sh")
    return (not bad), (f"differs from the verifier's pinned copies: {bad}" if bad else
                       "package tools byte-identical to the verifier's copies")


def c_linear(c):
    rp = os.path.join(c.d, c.pkg["raw_render"]["file"])
    try:
        c.raw = np.load(rp, allow_pickle=False)
    except Exception as e:  # noqa: BLE001
        return False, f"raw render unreadable without pickle: {e}"
    if c.raw.dtype != np.uint8 or c.raw.ndim != 2 or list(c.raw.shape) != c.pkg["raw_render"]["shape"]:
        return False, f"raw render {c.raw.dtype} {c.raw.shape} is not the declared 2-D uint8"
    if sha(np.ascontiguousarray(c.raw).tobytes()) != c.pkg["raw_render"]["pixels_sha256"]:
        return False, "raw render pixels differ from package.json"
    s = c.pkg["image"]["scale"]
    try:
        p, lo, hi = BI.panel(c.raw, s)
    except Exception as e:  # noqa: BLE001
        return False, f"panel rebuild failed: {e}"
    p0 = BI.HEADER
    got = c.img[p0:p0 + p.shape[0]]
    if got.shape != p.shape or not np.array_equal(got, p):
        nd = int((got != p).sum()) if got.shape == p.shape else -1
        return False, f"CT panel is not the linear 1-99 % window{' + INTER_AREA' if s < 1 else ''} of the raw render ({nd} px differ)"
    d = c.pkg["image"]["display"]
    if (d["window_lo"], d["window_hi"]) != (lo, hi) or c.pkg["image"]["panel_rows"] != [p0, p0 + p.shape[0]]:
        return False, "declared window or panel rows differ from the recomputation"
    if c.img.shape[0] != p0 + p.shape[0] + BI.FOOTER:
        return False, "image height is not header + panel + footer"
    return True, f"panel == linear window [{lo:g}, {hi:g}] of the raw render{' + INTER_AREA' if s < 1 else ''}, pixel-exact"


def c_scale_bar(c):
    s = c.pkg["image"]["scale"]
    exact = 10000.0 / c.voxel * s
    p1 = c.img.shape[0] - BI.FOOTER
    outside = np.zeros_like(c.img)
    outside[:BI.HEADER] = c.img[:BI.HEADER]
    outside[p1:] = c.img[p1:]
    n, lab, st, _ = cv2.connectedComponentsWithStats((outside == 255).astype(np.uint8), connectivity=4)
    bars = [i for i in range(1, n) if st[i, cv2.CC_STAT_HEIGHT] >= 8 and st[i, cv2.CC_STAT_WIDTH] >= 8 * st[i, cv2.CC_STAT_HEIGHT]
            and st[i, cv2.CC_STAT_AREA] == st[i, cv2.CC_STAT_WIDTH] * st[i, cv2.CC_STAT_HEIGHT]]
    if len(bars) != 1:
        return False, f"{len(bars)} solid bar candidates outside the CT panel (need exactly 1)"
    i = bars[0]
    L = int(st[i, cv2.CC_STAT_WIDTH])
    y = int(st[i, cv2.CC_STAT_TOP])
    if y < p1:
        return False, "scale bar is not in the footer"
    if abs(L - exact) > 0.5:
        return False, f"measured bar {L} px != 1 cm = {exact:.3f} px at {c.voxel} um x scale {s}"
    if abs(c.pkg["image"]["px_per_mm"] - exact / 10.0) > 1e-9 or c.pkg["scale_bar"]["length_px"] != L:
        return False, "declared px_per_mm or bar length disagree with the measurement"
    footer_ok = np.array_equal(c.img[p1:], BI.footer_strip(c.img.shape[1], c.voxel, s))
    if not footer_ok:
        return False, "footer strip is not exactly bar + '1 cm' label (hidden content?)"
    return True, f"measured bar {L} px; 1 cm = {exact:.3f} px ({exact / 10:.4f} px/mm); footer pixel-exact"


def c_letters(c):
    t = c.pkg["letter_table"]
    if t["columns"] != LETTER_COLUMNS:
        return False, "letter table columns differ"
    ppm = c.pkg["image"]["px_per_mm"]
    ph, pw = c.pkg["image"]["panel_shape"]
    rows = t["rows"]
    for r in rows:
        if not isinstance(r, dict) or set(r) != set(LETTER_COLUMNS):
            return False, f"row keys {list(r) if isinstance(r, dict) else r} != columns"
        if not (isinstance(r["identity"], str) and len(r["identity"]) == 1 and unicodedata.category(r["identity"]).startswith("L")):
            return False, f"row {r['letter_id']}: identity must be one letter"
        x, y, w, h = (r[k] for k in ("bbox_x_px", "bbox_y_px", "bbox_w_px", "bbox_h_px"))
        if not all(isinstance(v, int) for v in (x, y, w, h)) or w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > pw or y + h > ph:
            return False, f"row {r['letter_id']}: bbox outside the CT panel"
        if r["height_mm"] != round(h / ppm, 3) or r["width_mm"] != round(w / ppm, 3):
            return False, f"row {r['letter_id']}: mm sizes != px / {ppm:.4f}"
        if not isinstance(r["firm"], bool) or not isinstance(r["evidence"], str):
            return False, f"row {r['letter_id']}: firm/evidence types"
    if not c.pkg["dry_run"]:
        if len(rows) < 10:
            return False, f"{len(rows)} letters < 10 (First Letters needs 10 in one 4 cm^2 area)"
        xs0 = min(r["bbox_x_px"] for r in rows); ys0 = min(r["bbox_y_px"] for r in rows)
        xs1 = max(r["bbox_x_px"] + r["bbox_w_px"] for r in rows); ys1 = max(r["bbox_y_px"] + r["bbox_h_px"] for r in rows)
        area = (xs1 - xs0) * (ys1 - ys0) / ppm ** 2
        if area > 400.0:
            return False, f"letters' joint bbox {area:.1f} mm^2 > 400 mm^2"
    return True, f"{len(rows)} row(s); columns and mm/px consistency OK" + (" (dry run: table fields only)" if c.pkg["dry_run"] else "")


def c_provenance(c):
    if c.pkg["provenance"] != PROV:
        return False, "package.json provenance differs"
    first = read(os.path.join(c.d, "README.txt")).decode("ascii", "replace").split("\n", 1)[0]
    if first != PROV:
        return False, "README.txt first line is not the provenance line"
    return True, "provenance line present as visible text (package.json, README.txt line 1)"


def c_fields(c):
    p = c.pkg
    probs = []
    for k, v in p["commits"].items():
        if not HEX40.match(str(v)):
            probs.append(f"commit {k}")
    for k, v in p["timestamps"].items():
        if not ISO.match(str(v)):
            probs.append(f"timestamp {k}={v!r}")
    for k in ("sha256", "pixels_sha256", "panel_sha256"):
        if not HEX64.match(p["image"][k]):
            probs.append(f"image.{k}")
    for k, v in p["mesh"]["files_sha256"].items():
        if not HEX64.match(v):
            probs.append(f"mesh {k}")
    r = p["render"]
    for k in ("app", "villa_commit", "binary_sha256", "deps_image", "command", "utc_start", "utc_end"):
        if k not in r:
            probs.append(f"render.{k}")
    if isinstance(r, dict) and set(r) - {"app", "villa_commit", "binary_sha256", "deps_image", "command", "utc_start", "utc_end"}:
        probs.append("render has extra keys")
    return (not probs), ("; ".join(probs) or "commits, timestamps, hashes and render inputs well-formed")


CHECKS = [("package_json_strict", c_package_json), ("file_layout", c_layout), ("sha256_manifest", c_manifest),
          ("names_ascii_basename", c_names), ("no_cf_characters", c_cf), ("png_no_metadata", c_png),
          ("mesh_no_metadata", c_mesh), ("voxel_from_metadata", c_voxel), ("volume_eligible", c_eligibility),
          ("dry_run_marking", c_dry_run), ("tools_pinned", c_tools), ("linear_display", c_linear),
          ("scale_bar_measured", c_scale_bar), ("letter_table", c_letters), ("provenance_visible", c_provenance),
          ("fields_wellformed", c_fields)]


def verify(pkg_dir, eligible=DEFAULT_ELIGIBLE):
    c = Ctx(pkg_dir, eligible)
    res, stop = [], False
    for name, fn in CHECKS:
        if stop:
            res.append(dict(check=name, ok=False, detail="not run (an earlier structural check failed)"))
            continue
        try:
            ok, det = fn(c)
        except Exception as e:  # noqa: BLE001 - a crash is a failure, never a pass
            ok, det = False, f"check crashed: {type(e).__name__}: {e}"
        res.append(dict(check=name, ok=bool(ok), detail=det))
        if not ok and name in ("package_json_strict", "file_layout", "png_no_metadata", "voxel_from_metadata"):
            stop = True
    return dict(package=os.path.basename(os.path.abspath(pkg_dir)), passed=all(r["ok"] for r in res), checks=res)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--eligible", default=DEFAULT_ELIGIBLE)
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    r = verify(a.package, a.eligible)
    s = json.dumps(r, indent=1)
    if a.json:
        open(a.json, "w").write(s + "\n")
    print(s)
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
