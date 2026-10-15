# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters submission-package factory (dry-run capable).

make_package(...) writes one package directory:
  <mesh_name>.png                 canonical PNG (pngio), linear display, 1 cm scale bar, DRY RUN stamp if dry run
  mesh/<mesh_name>/{x,y,z}.tif    the mesh the image was rendered from (official C++ tifxyz layout, 10 tags only)
  mesh/<mesh_name>/meta.json
  render/<mesh_name>_raw.npy      the renderer's uint8 surface slice (so the verifier can recheck the display)
  inputs/volume_metadata.json     the volume's own metadata.json (voxel size source), byte copy
  tools/{pngio,build_image,render_build,reproduce_check}.py, reproduce.sh
  package.json, README.txt, SHA256SUMS (sha256 of every other file)
The image is generated programmatically; nobody views it.

CLI (the real render; needs the official renderer from setup_renderer.sh):
  python factory.py --volume-url URL --mesh-src OFFICIAL.tifxyz --rows R0 R1 --cols C0 C1 --mesh-name NAME
                    --out-root packages/dryrun [--dry-run] [--scale 1.0] [--selection JSON]"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_image as BI  # noqa: E402
import pngio  # noqa: E402
import render_build as RB  # noqa: E402

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
FORMAT = "hercules-fl-package/1"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")
PKG_TOOLS = ("pngio.py", "build_image.py", "render_build.py", "reproduce_check.py")
LETTER_COLUMNS = ["letter_id", "identity", "bbox_x_px", "bbox_y_px", "bbox_w_px", "bbox_h_px", "height_mm",
                  "width_mm", "firm", "evidence"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def git_head(repo: str) -> str:
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "0" * 40


def write_mesh(points: np.ndarray, scale, mesh_name: str, dst: str) -> dict:
    """Write a tifxyz (official C++ layout) with meta.json {bbox, format, scale, type, uuid}; returns sha256s."""
    os.makedirs(dst, exist_ok=False)
    pts = np.asarray(points, np.float32)
    shas = {}
    for i, n in enumerate(("x.tif", "y.tif", "z.tif")):
        b = pngio.encode_tiff_f32(pts[..., i])
        open(os.path.join(dst, n), "wb").write(b)
        shas[n] = sha256_bytes(b)
    v = (pts != -1).all(-1) & np.isfinite(pts).all(-1) & (pts[..., 2] > 0)
    q = pts[v].astype(np.float64)
    meta = dict(bbox=[q.min(0).tolist(), q.max(0).tolist()], format="tifxyz",
                scale=[float(scale[0]), float(scale[1])], type="seg", uuid=mesh_name)
    mb = (json.dumps(meta, indent=4, sort_keys=True) + "\n").encode("ascii")
    open(os.path.join(dst, "meta.json"), "wb").write(mb)
    shas["meta.json"] = sha256_bytes(mb)
    return shas


def empty_letter_table():
    return dict(columns=LETTER_COLUMNS,
                units=dict(bbox="image px, origin = top-left of the CT panel", height_mm="bbox_h_px / px_per_mm, 3 dp",
                           width_mm="bbox_w_px / px_per_mm, 3 dp"),
                rows=[])


def readme_text(pkg: dict) -> str:
    d = "yes (DRY RUN: not a submission)" if pkg["dry_run"] else "no"
    return "\n".join([
        PROV,
        "",
        f"Package: {pkg['package_name']}",
        f"Dry run: {d}",
        f"Volume: {pkg['volume_url']} (volume id {pkg['volume_id']}, voxel {pkg['voxel_size_um']} um from its metadata.json)",
        f"Mesh: mesh/{pkg['mesh_name']} (tifxyz)",
        f"Image: {pkg['image']['file']} ({pkg['image']['px_per_mm']:.4f} px/mm; 1 cm bar = {pkg['scale_bar']['length_px']} px)",
        "",
        "Display: linear 1-99 % window of the renderer's surface slice; cv2.INTER_AREA only if scale < 1; no",
        "other operation. The image was generated programmatically and verified mechanically.",
        "",
        "Reproduce (needs the official vc_render_tifxyz, villa 41701aa, via /work/bin/vc):",
        f"  bash reproduce.sh '{pkg['volume_url']}' mesh/{pkg['mesh_name']}",
        "It re-renders in a fresh temporary directory and compares sha256 of the raw render, the CT panel and the",
        "whole PNG with package.json.",
        "",
        "SHA256SUMS lists every other file of this package.",
        "",
    ])


REPRODUCE_SH = """#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# reproduce.sh VOLUME_URL MESH_DIR : re-render MESH_DIR from VOLUME_URL with the official renderer in a fresh
# temporary directory, rebuild the image, and compare sha256 with package.json. Exit 0 only if byte-identical.
set -euo pipefail
PKG=$(cd "$(dirname "$0")" && pwd)
VOL=${1:?volume URL}; MESH=${2:?mesh dir}
case "$MESH" in /*) ;; *) MESH="$PKG/$MESH";; esac
PY=${HRC_PYTHON:-/opt/hv/bin/python}
# the renderer runs in Docker via /work/bin/vc, which mounts only /work and /home/user: stay under /work
BASE=${HRC_REPRO_BASE:-/work/repro}; mkdir -p "$BASE"
CLEAN=$(mktemp -d "$BASE/hrc_repro_XXXXXX")
cp -r "$MESH" "$CLEAN/mesh"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$PKG/tools/reproduce_check.py" --package "$PKG" --volume-url "$VOL" --mesh "$CLEAN/mesh" --workdir "$CLEAN/work"
"""


def make_package(raw: np.ndarray, *, mesh_points, mesh_scale, mesh_name: str, volume_url: str,
                 volume_metadata_path: str, out_root: str, dry_run: bool, scale: float = 1.0,
                 render_info: dict | None = None, selection: dict | None = None, mesh_source: dict | None = None,
                 letter_rows=None, created_utc: str | None = None, repo: str | None = None) -> str:
    if not NAME_RE.match(mesh_name) or re.search(r"DRY[\s_-]*RUN", mesh_name, re.I):
        raise ValueError(f"mesh name must be plain ASCII [A-Za-z0-9._-] without a DRY RUN marker: {mesh_name!r}")
    scroll, volume_id = RB.parse_volume_url(volume_url)
    voxel_um = RB.voxel_um_from_metadata(volume_metadata_path)
    pkg_dir_name = ("DRY_RUN_" if dry_run else "") + mesh_name
    pkg_dir = os.path.join(out_root, pkg_dir_name)
    if os.path.exists(pkg_dir):
        raise FileExistsError(pkg_dir)
    os.makedirs(pkg_dir)
    img, info = BI.compose(raw, voxel_um, scale, dry_run)
    png = pngio.encode_png_gray8(img)
    open(os.path.join(pkg_dir, mesh_name + ".png"), "wb").write(png)
    mesh_shas = write_mesh(mesh_points, mesh_scale, mesh_name, os.path.join(pkg_dir, "mesh", mesh_name))
    os.makedirs(os.path.join(pkg_dir, "render"))
    raw_path = os.path.join(pkg_dir, "render", mesh_name + "_raw.npy")
    np.save(raw_path, np.ascontiguousarray(raw), allow_pickle=False)
    os.makedirs(os.path.join(pkg_dir, "inputs"))
    shutil.copyfile(volume_metadata_path, os.path.join(pkg_dir, "inputs", "volume_metadata.json"))
    os.makedirs(os.path.join(pkg_dir, "tools"))
    for t in PKG_TOOLS:
        shutil.copyfile(os.path.join(HERE, t), os.path.join(pkg_dir, "tools", t))
    open(os.path.join(pkg_dir, "reproduce.sh"), "w").write(REPRODUCE_SH)
    os.chmod(os.path.join(pkg_dir, "reproduce.sh"), 0o755)
    p0, p1 = info["panel_rows"]
    import cv2
    pkg = dict(
        provenance=PROV,
        package_format=FORMAT,
        package_name=("DRY RUN " if dry_run else "") + f"{scroll} {mesh_name}",
        package_dir=pkg_dir_name,
        dry_run=bool(dry_run),
        scroll=scroll,
        volume_id=volume_id,
        volume_url=volume_url,
        volume_metadata=dict(file="inputs/volume_metadata.json", source=volume_url + "metadata.json",
                             sha256=sha256_file(volume_metadata_path)),
        voxel_size_um=voxel_um,
        voxel_size_source="metadata.json scan.tomo.acquisition.detector.samplePixelSize (mm) x 1000",
        mesh_name=mesh_name,
        mesh=dict(dir=f"mesh/{mesh_name}", files_sha256=mesh_shas, grid_shape=list(np.asarray(mesh_points).shape[:2]),
                  source=mesh_source or {}),
        image=dict(file=mesh_name + ".png", sha256=sha256_bytes(png), shape=info["image_shape"],
                   pixels_sha256=sha256_bytes(np.ascontiguousarray(img).tobytes()),
                   panel_rows=info["panel_rows"], panel_shape=info["panel_shape"],
                   panel_sha256=sha256_bytes(np.ascontiguousarray(img[p0:p1]).tobytes()),
                   scale=float(scale), px_per_mm=info["px_per_mm"],
                   display=dict(kind="linear", lo_pct=BI.LO_PCT, hi_pct=BI.HI_PCT, valid="render > 0",
                                window_lo=info["window_lo"], window_hi=info["window_hi"],
                                downscale="cv2.INTER_AREA" if scale < 1 else "none"),
                   header_rows=[0, BI.HEADER], footer_rows=[p1, p1 + BI.FOOTER],
                   stamp=dict(text=BI.STAMP_TEXT if dry_run else "", org=list(BI.STAMP_ORG))),
        raw_render=dict(file=f"render/{mesh_name}_raw.npy", sha256=sha256_file(raw_path), shape=list(raw.shape),
                        dtype="uint8", pixels_sha256=sha256_bytes(np.ascontiguousarray(raw).tobytes())),
        scale_bar=dict(length_px=info["bar_length_px"], length_exact_px=info["bar_length_exact_px"],
                       rows=info["bar_rows"], x0=info["bar_x0"], height_px=BI.BAR_H, represents_mm=10.0,
                       formula="round(10000 / voxel_size_um * scale)"),
        render=render_info or {},
        letter_table=dict(empty_letter_table(), rows=list(letter_rows or [])),
        selection=selection or {},
        commits=dict(hercules_repo=git_head(repo or os.path.join(HERE, "..", "..", "..")),
                     villa="41701aa0eaa1aa765523db3f9f972b5830abf549"),
        software=dict(python=platform.python_version(), numpy=np.__version__, opencv=cv2.__version__),
        timestamps=dict(package_utc=created_utc or RB.utc(),
                        render_start_utc=(render_info or {}).get("utc_start", ""),
                        render_end_utc=(render_info or {}).get("utc_end", "")),
    )
    open(os.path.join(pkg_dir, "package.json"), "w").write(json.dumps(pkg, indent=1, sort_keys=True) + "\n")
    open(os.path.join(pkg_dir, "README.txt"), "w").write(readme_text(pkg))
    write_manifest(pkg_dir)
    return pkg_dir


def write_manifest(pkg_dir: str):
    rows = []
    for dp, dns, fns in os.walk(pkg_dir):
        dns.sort()
        for f in sorted(fns):
            rel = os.path.relpath(os.path.join(dp, f), pkg_dir)
            if rel != "SHA256SUMS":
                rows.append(f"{sha256_file(os.path.join(dp, f))}  {rel}")
    open(os.path.join(pkg_dir, "SHA256SUMS"), "w").write("\n".join(sorted(rows, key=lambda r: r[66:])) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume-url", required=True)
    ap.add_argument("--mesh-src", required=True, help="official tifxyz directory (local copy)")
    ap.add_argument("--mesh-src-url", default="")
    ap.add_argument("--rows", type=int, nargs=2, required=True)
    ap.add_argument("--cols", type=int, nargs=2, required=True)
    ap.add_argument("--mesh-name", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--selection", default="")
    a = ap.parse_args(argv)
    if a.dry_run and not os.path.abspath(a.out_root).rstrip("/").endswith("packages/dryrun"):
        raise SystemExit("dry runs are written under packages/dryrun/ only")
    sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src"))
    from hercules.geometry.tifxyz import read_tifxyz
    src = read_tifxyz(a.mesh_src)
    pts = src.points[a.rows[0]:a.rows[1], a.cols[0]:a.cols[1]]
    os.makedirs(a.workdir, exist_ok=False)
    mdp = os.path.join(a.workdir, "metadata.json")
    RB.fetch_metadata(a.volume_url, mdp)
    voxel_um = RB.voxel_um_from_metadata(mdp)
    mesh_tmp = os.path.join(a.workdir, "mesh", a.mesh_name)
    write_mesh(pts, src.scale, a.mesh_name, mesh_tmp)
    raw, cmd, t0, t1 = RB.render(a.volume_url, mesh_tmp, os.path.join(a.workdir, "render"), voxel_um)
    vc_bin = "/work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz"
    render_info = dict(app="vc_render_tifxyz", villa_commit="41701aa0eaa1aa765523db3f9f972b5830abf549",
                       binary_sha256=sha256_file(vc_bin) if os.path.exists(vc_bin) else "",
                       deps_image="ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f",
                       command=[os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)],
                       utc_start=t0, utc_end=t1)
    src_files = {n: sha256_file(os.path.join(a.mesh_src, n)) for n in ("x.tif", "y.tif", "z.tif", "meta.json")}
    mesh_source = dict(url=a.mesh_src_url, files_sha256=src_files, grid_rows=a.rows, grid_cols=a.cols)
    sel = json.load(open(a.selection)) if a.selection else {}
    d = make_package(raw, mesh_points=pts, mesh_scale=src.scale, mesh_name=a.mesh_name, volume_url=a.volume_url,
                     volume_metadata_path=mdp, out_root=a.out_root, dry_run=a.dry_run, scale=a.scale,
                     render_info=render_info, selection=sel, mesh_source=mesh_source)
    print(d)


if __name__ == "__main__":
    main()
