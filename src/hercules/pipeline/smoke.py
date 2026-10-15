# Provenance: Project HERCULES | owner the owner | [id removed]
"""Real-data smoke runs of the window pipeline (numbers only; no image is
viewed).

    python -m hercules.pipeline.smoke w040   # PHerc0139 w040: cut/level/orient/render/gate
    python -m hercules.pipeline.smoke j0841  # PHerc0841 J1-J5: GEOMETRY ONLY (no CT, no render)

The 0841 run reads only the organizer 9 um meshes and the level-0 .zarray
(shape metadata) of the 0841 volume: no CT voxel, SV, label or reference map
is read, as required until the J seal is committed.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from hercules.geometry.level_mesh import chirality, normal_sign_report
from hercules.geometry.tifxyz import read_tifxyz, vertex_normals

from . import canvas as C
from . import centre as Ce
from . import window as Wn

REPO = Path(__file__).resolve().parents[3]
OUT = Path("/work/pipeline")
LEDGER = REPO / "logs" / "gpu_ledger.tsv"
PROV = Wn.PROVENANCE.split(": ", 1)[1]

W040_SEG = "20250831000000-w040_2025083102"
W040_MESH = Path("/work/c3/data/s3/PHerc0139/segments") / W040_SEG / "mesh" / "20250831000000-on-20250728140407-9.362um.tifxyz"
W040_SV = (Path("/work/c3/data/s3/PHerc0139/segments") / W040_SEG / "surface-volumes"
           / "9.362um-1.2m-113keV-volume-20250728140407.zarr" / "0")
W040_VOLUME = ("PHerc0139", "20250728140407-9.362um-1.2m-113keV-masked")
W040_META = Path("/work/c3/data/s3/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/metadata.json")
# 1068 px window with the highest supervision-mask density (0.256; ink 0.116) among
# windows whose +256 px margin is fully on valid mesh; centre (2024, 2524)
W040_WINDOW = Wn.Window(1490, 1990, 1068, 1068)

B0841 = Path("/work/bank/0841/s3/PHerc0841")
V0841 = ("PHerc0841", "20250821151531-9.366um-1.2m-113keV-masked")


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_default(o: Any):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    d = {"provenance": PROV}
    d.update(obj)
    path.write_text(json.dumps(d, indent=1, default=_json_default) + "\n", encoding="utf-8")


def _tree_sha256(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n".encode())
    return h.hexdigest()


def _ledger(command: str, start: str, end: str, rc: int, sha: str) -> None:
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write("\t".join(["vm", "cpu", command, start, end, str(rc), sha]) + "\n")


def _sign_with(points: np.ndarray, centre) -> dict:
    rep = normal_sign_report(points, vertex_normals(points), centre)
    return dict(sign=rep.sign, frac_clear=rep.frac_clear, frac_positive=rep.frac_positive,
                ambiguous=rep.ambiguous, chirality=int(chirality(points, centre)))


def run_w040(render: bool = True, *, z_ascending: bool = True, convention_sign: int = 1) -> dict:
    tag = "" if (z_ascending, convention_sign) == (True, 1) else f"_z{'asc' if z_ascending else 'desc'}_c{convention_sign:+d}"
    out = OUT / "w040"
    out.mkdir(parents=True, exist_ok=True)
    mesh = read_tifxyz(W040_MESH)
    url = Wn.volume_url(*W040_VOLUME)
    vox = Wn.voxel_size_from_metadata(W040_META)
    res: dict[str, Any] = dict(segment=W040_SEG, mesh=str(W040_MESH), volume_url=url, voxel_size_um=vox,
                               window=dict(y0=W040_WINDOW.y0, x0=W040_WINDOW.x0, h=W040_WINDOW.h, w=W040_WINDOW.w))
    umb = Ce.find_official_umbilicus(W040_VOLUME[0], W040_VOLUME[1].split("-")[0])
    res["official_umbilicus"] = umb
    z = mesh.points[..., 2][mesh.valid]
    t0 = time.time()
    mc = Ce.mask_centroid_curve(url, 4, z_range=(float(z.min()) - 512, float(z.max()) + 512), z_stride=1,
                                smooth_sigma_vox=256.0)
    res["centre"] = dict(kind="ct_mask_centroid_level4", seconds=round(time.time() - t0, 1), n_slices=len(mc.z_full),
                         n_requests=mc.n_requests, x_range=[float(np.nanmin(mc.curve.x)), float(np.nanmax(mc.curve.x))],
                         y_range=[float(np.nanmin(mc.curve.y)), float(np.nanmax(mc.curve.y))])
    np.savez(out / "mask_centroid_L4.npz", z=mc.z_full, x=mc.x_raw, y=mc.y_raw, area=mc.area_px,
             zs=mc.curve.z, xs=mc.curve.x, ys=mc.curve.y)
    wr = Wn.run_window(mesh, W040_WINDOW, mc.curve, margin_px=256, z_ascending=z_ascending,
                       convention_sign=convention_sign)
    res["geometry"] = wr.stats
    # fallback centres (no CT) versus the CT-mask centroid on the same cut
    geo, geo_info = Ce.geometric_centre_curve(mesh.points)
    ax, ax_info = Ce.volume_axis_centre(url)
    reg = wr.cut.points[wr.cut.region]
    res["centre_comparison_on_window"] = dict(
        mask_centroid=_sign_with(reg, mc.curve), geometric=_sign_with(reg, geo), volume_axis=_sign_with(reg, ax),
        geometric_centre_xy_median=[float(np.median(geo.x)), float(np.median(geo.y))],
        mask_centroid_xy_median=[float(np.median(mc.curve.x)), float(np.median(mc.curve.y))],
        volume_axis_xy=[ax_info["cx"], ax_info["cy"]])
    lev_dir = out / f"lev_w040_y1490_x1990{tag}.tifxyz"
    Wn.write_levelled_tifxyz(wr, lev_dir, f"lev_w040_y1490_x1990{tag}", voxel_size_um=vox, source=str(W040_MESH),
                             overwrite=True)
    crop = wr.maps.render_crop(256)
    flip = C.flip_normals_after_orient(True, wr.maps.flip_u, wr.maps.flip_v)
    zarr_out = out / f"render_lev_n31{tag}.zarr"
    cmd = Wn.render_command(url, lev_dir, zarr_out, vox, crop_xywh=crop, flip_normals=flip, num_slices=31)
    res["render_command"] = " ".join(cmd)
    res["flip_normals"] = flip
    if render:
        import shutil

        if zarr_out.exists():
            shutil.rmtree(zarr_out)
        env = dict(os.environ, VC_CPUS="2", OMP_NUM_THREADS="2")
        start = _utc()
        t = time.time()
        p = subprocess.run(["/work/bin/vc", *cmd], capture_output=True, text=True, env=env)
        secs = time.time() - t
        end = _utc()
        (out / f"render{tag}.log").write_text(p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-20000:], encoding="utf-8")
        sha = _tree_sha256(zarr_out) if (p.returncode == 0 and zarr_out.exists()) else "missing"
        res["render"] = dict(seconds=round(secs, 1), returncode=p.returncode, output_sha256=sha)
        if secs > 120:
            _ledger("VC_CPUS=2 OMP_NUM_THREADS=2 /work/bin/vc " + " ".join(cmd), start, end, p.returncode, sha)
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-3000:])
    import zarr

    stack = zarr.open(str(zarr_out / "0"), mode="r")
    sv = zarr.open(str(W040_SV), mode="r")
    res["render_shape"] = list(stack.shape)
    ours = np.asarray(stack[:])
    gate = Wn.alignment_gate(ours, sv, wr.maps, render_margin_px=256)
    res["gate"] = {k: v for k, v in gate.items() if k != "ncc_grid"}
    np.save(out / f"gate_ncc_grid{tag}.npy", np.array(gate["ncc_grid"]))
    # slice-direction diagnostic: ours at +2 vs SV at +1.5 (same side) and -1.5 (other side)
    w = W040_WINDOW
    x, y, _, _ = crop
    diag = {}
    for d in (2, -2):
        a = Wn.resample_to_organizer(np.where(ours[15 + d] == 0, np.nan, ours[15 + d]).astype(float), wr.maps, w,
                                     lev_origin=(y, x))
        k_same = 15 if d > 0 else 12
        k_opp = 12 if d > 0 else 15
        s_same = np.asarray(sv[k_same, w.y0:w.y0 + w.h, w.x0:w.x0 + w.w], float)
        s_opp = np.asarray(sv[k_opp, w.y0:w.y0 + w.h, w.x0:w.x0 + w.w], float)
        s_same[s_same == 0] = np.nan
        s_opp[s_opp == 0] = np.nan
        diag[f"ours_{15 + d}_vs_sv_{k_same}"] = Wn.ncc(a, s_same)[0]
        diag[f"ours_{15 + d}_vs_sv_{k_opp}"] = Wn.ncc(a, s_opp)[0]
    res["slice_direction_check"] = diag
    _write_json(out / f"w040_smoke{tag}.json", res)
    _write_json(REPO / "logs" / "pipeline" / f"w040_smoke{tag}.json", res)
    return res


def run_j0841() -> dict:
    url = Wn.volume_url(*V0841)
    ax, ax_info = Ce.volume_axis_centre(url)  # level-0 .zarray only
    res: dict[str, Any] = dict(note="geometry only: organizer meshes + level-0 .zarray shape; no CT, SV, label or render",
                               volume_url=url, volume_axis=ax_info,
                               official_umbilicus=Ce.find_official_umbilicus(V0841[0], V0841[1].split("-")[0]),
                               windows={})
    centres = {}
    meshes = {}
    for short, seg in Wn.SEGMENTS_0841.items():
        ts = seg.split("-")[0]
        mp = B0841 / "segments" / seg / "mesh" / f"{ts}-on-20250821151531-9.366um.tifxyz"
        meshes[short] = read_tifxyz(mp)
        geo, info = Ce.geometric_centre_curve(meshes[short].points)
        centres[short] = geo
        res.setdefault("geometric_centre", {})[short] = dict(
            x_median=float(np.median(geo.x)), y_median=float(np.median(geo.y)), n_bins=len(info["z"]),
            x_range=[float(np.min(geo.x)), float(np.max(geo.x))], y_range=[float(np.min(geo.y)), float(np.max(geo.y))])
    for J, (short, y0, x0) in Wn.J_WINDOWS_0841.items():
        mesh = meshes[short]
        win = Wn.Window(y0, x0, Wn.J_WINDOW_PX, Wn.J_WINDOW_PX)
        wr = Wn.run_window(mesh, win, centres[short], margin_px=Wn.SEALED_CLEARANCE_PX, z_ascending=True,
                           convention_sign=1)
        reg = wr.cut.points[wr.cut.region]
        st = dict(wr.stats)
        st["sign_with_volume_axis"] = _sign_with(reg, ax)
        st["sign_with_geometric"] = _sign_with(reg, centres[short])
        st["axis_and_geometric_agree"] = bool(st["sign_with_volume_axis"]["chirality"]
                                              == st["sign_with_geometric"]["chirality"])
        st["segment"] = Wn.SEGMENTS_0841[short]
        st["window"] = dict(y0=y0, x0=x0, h=win.h, w=win.w)
        res["windows"][J] = st
    _write_json(OUT / "j0841" / "j0841_geometry.json", res)
    _write_json(REPO / "logs" / "pipeline" / "j0841_geometry.json", res)
    return res


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "w040"
    if what == "w040":
        mirror = "--mirror" in sys.argv  # convention_sign -1: exercises the u-mirror on real data
        r = run_w040(render="--no-render" not in sys.argv, convention_sign=-1 if mirror else 1)
    elif what == "j0841":
        r = run_j0841()
    else:
        raise SystemExit("usage: python -m hercules.pipeline.smoke {w040 [--mirror]|j0841}")
    print(json.dumps(r, indent=1, default=_json_default)[:6000])
