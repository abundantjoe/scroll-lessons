# Provenance: Project HERCULES | owner the owner | [id removed]
"""Planted-fault runner: build many random synthetic worlds, inject every fault, run
the full pre-read gate and report the catch rate (and the false-alarm rate on the
matching clean records).

    PYTHONPATH=src python -m hercules.tribunal.runner --worlds 30 \
        --out logs/sib/tribunal/faultsuite.json

Part A (gate level): per world one clean record and one record per fault, each written
to disk exactly as the pipeline would (tifxyz mesh, zarr stack, metadata.json,
manifest with consistent hashes) and passed through ``preread.preread_gate``.
Part B (re-trace at the real grid step): the declared KD-tree rule on 20-vox meshes
at radii 300-3000 vox, re-traces vs neighbouring sheets and far same-sheet segments;
also reports how often the literal nearest-vertex form alone would have caught them.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
import time
from pathlib import Path

import numpy as np

from hercules.geometry.render_synth import cylinder_grid
from hercules.pipeline.window import render_command

from . import PROVENANCE, TRIBUNAL_VERSION, faults as F, preread as P, synth as S

OWN_CHECK = {"offset8": "window_offset", "swap_depth": "depth_order", "mirror": "mirror",
             "off_by_one": "slice_index", "retrace": "retrace", "wrong_voxel": "voxel_size"}
WIN_STEP = 4.0      # synthetic window mesh step (vox); canvas px = 1 vox
TRAIN_STEP = 20.0   # training meshes at the official 20-vox step


def _vol_url(tag: str) -> str:
    return f"s3://vesuvius-challenge-open-data/SYNTH/volumes/{tag}.zarr"


def _decoys(world: S.World, sheet: int, phi_ref: float, rng, arc_w: float) -> dict:
    """Training segments that must NOT trigger the re-trace check: the neighbouring
    sheets over the window and the same sheet far away (no overlap)."""
    out = {}
    for j in (sheet - 1, sheet + 1):
        if 0 <= j < len(world.radii):
            out[f"neighbour_{j}"] = cylinder_grid(world.radii[j], world.centre_xy, (6, 9), TRAIN_STEP,
                                                  float(rng.uniform(-5, 5)), s0=-10.0, z0=4.0,
                                                  phi_ref=phi_ref).astype(np.float64)
    # same sheet, centred in the arc gap the window does not cover (the window spans
    # arc_w vox of arc; on the inner sheets that is > 180 deg, so "opposite side" overlaps)
    r = world.radii[sheet]
    seg_arc = 3 * TRAIN_STEP
    s0 = arc_w + 0.5 * (2 * math.pi * r - arc_w) - 0.5 * seg_arc
    out["same_sheet_far"] = cylinder_grid(r, world.centre_xy, (6, 4), TRAIN_STEP, 0.0,
                                          s0=s0, z0=4.0, phi_ref=phi_ref).astype(np.float64)
    return out


def _record(root: Path, name: str, world: S.World, mesh_dir: Path, stack: np.ndarray, crop: dict, n: int,
            voxel_used: float, meta_path: Path, meta_source: str, vol_url: str) -> dict:
    zdir = root / f"{name}.zarr"
    S.write_stack_zarr(stack, zdir)
    cmd = render_command(vol_url, mesh_dir, zdir, voxel_used,
                         crop_xywh=(crop["x0"], crop["y0"], crop["w"], crop["h"]), num_slices=n)
    return {
        "window_id": name,
        "volume": {"url": vol_url, "metadata_source": meta_source, "metadata_json": str(meta_path),
                   "metadata_sha256": P.file_sha256(meta_path)},
        "voxel_size_um": voxel_used,
        "mesh": {"path": str(mesh_dir), "sha256": P.tree_sha256(mesh_dir)},
        "crop": dict(crop), "n_slices": n, "slice_step": 1.0, "flip_normals": True,
        "stack": {"path": str(zdir), "sha256": P.array_sha256(stack)},
        "render_command": cmd,
        "display": {"scale": 0.5, "px_per_mm_image": 1000.0 * 0.5 / voxel_used},
    }


def _summary(rep: dict) -> dict:
    ch = {c["name"]: c for c in rep["checks"]}
    s = {"passed": rep["passed"], "failed": rep["failed"]}
    if "window_offset" in ch:
        s["shift"] = ch["window_offset"]["details"].get("shift_yx")
        s["best_ncc"] = ch["window_offset"]["details"].get("best_ncc")
    if "mirror" in ch:
        s["mirror_margin"] = ch["mirror"]["details"].get("identity_margin")
        s["transform"] = ch["mirror"]["details"].get("transform")
    if "depth_order" in ch:
        s["depth_margin"] = ch["depth_order"]["details"].get("fwd_minus_rev")
        s["winner"] = ch["depth_order"]["details"].get("winner")
    if "slice_index" in ch:
        s["slice_margin"] = ch["slice_index"]["details"].get("margin")
    if "retrace" in ch:
        s["retrace_same_as"] = ch["retrace"]["details"].get("same_as")
    if "voxel_size" in ch:
        s["voxel_reason"] = ch["voxel_size"]["reason"]
    return s


def world_trials(seed: int, root: Path, *, texture_sigma: float = 1.0, noise_max: float = 6.0) -> list[dict]:
    """One clean record and one record per fault for a random world. ``texture_sigma``
    (vox) sets the CT texture correlation length (larger = adjacent slices more alike,
    i.e. harder depth checks); render noise is drawn from U(0, noise_max) grey levels."""
    rng = np.random.default_rng(seed)
    wdir = root / f"w{seed}"
    wdir.mkdir(parents=True, exist_ok=True)
    world = S.make_volume(seed=seed, voxel_um=float(rng.choice([9.366, 7.91, 2.403, 8.64])),
                          texture_sigma=texture_sigma)
    vol_url = _vol_url(f"v{seed}")
    S.write_volume_zarr(world.vol, wdir / "vol.zarr")
    import zarr

    vol = zarr.open(str(wdir / "vol.zarr"), mode="r")["0"]
    meta = S.write_metadata(wdir / "metadata.json", world.voxel_um)
    sheet = int(rng.integers(1, 4))
    phi_ref = float(rng.uniform(0, 2 * math.pi))
    z0 = float(rng.uniform(6, 10))
    pts = S.sheet_mesh(world, sheet, shape_hw=(24, 40), step=WIN_STEP, z0=z0, phi_ref=phi_ref)
    mesh_dir = S.write_mesh(pts, wdir / "mesh", WIN_STEP, f"synth-{seed}", world.voxel_um)
    n = int(rng.choice([21, 31]))
    crop = {"y0": 16 + int(rng.integers(-4, 5)), "x0": 24 + int(rng.integers(-4, 5)), "h": 64, "w": 112}
    origin = (crop["y0"], crop["x0"])
    noise = float(rng.uniform(0, noise_max))

    def render(org=origin, shift=0):
        st = S.render_delivered(vol, pts, WIN_STEP, org, (crop["h"], crop["w"]), n, slice_shift=shift)
        if noise > 0:
            e = rng.normal(0, noise, st.shape)
            st = np.where(st > 0, np.clip(np.rint(st + e), 1, 255), 0).astype(np.uint8)
        return st

    decoys = _decoys(world, sheet, phi_ref, rng, arc_w=(pts.shape[1] - 1) * WIN_STEP)
    clean = render()
    base = dict(world=world, mesh_dir=mesh_dir, crop=crop, n=n, meta_path=meta,
                meta_source=vol_url + "/metadata.json", vol_url=vol_url)
    out = []

    def run(name, stack, *, voxel=None, training=None, meta_path=None, meta_source=None, info=None):
        rec = _record(wdir, name, world, mesh_dir, stack, crop, n, voxel if voxel is not None else world.voxel_um,
                      meta_path or meta, meta_source or base["meta_source"], vol_url)
        t0 = time.time()
        rep = P.preread_gate(rec, volume=vol, training=training if training is not None else decoys)
        out.append({"seed": seed, "case": name, "texture_sigma": texture_sigma, "n_slices": n,
                    "noise_sd": noise, "sheet": sheet,
                    "voxel_um": world.voxel_um, "seconds": round(time.time() - t0, 3), "info": info or {},
                    **_summary(rep)})

    run("clean", clean)
    org8, d = F.offset_origin(origin, rng)
    run("offset8", render(org8), info={"offset_yx": list(d)})
    run("swap_depth", F.swap_depth(clean))
    mst, kind = F.mirror(clean, rng)
    run("mirror", mst, info={"mirror": kind})
    sh = F.off_by_one_shift(rng)
    run("off_by_one", render(shift=sh), info={"slice_shift": sh})
    rt, rinfo = F.retrace_of(world.radii[sheet], world.centre_xy, pts.shape[:2], WIN_STEP, 0.0, z0, rng,
                             step=TRAIN_STEP, phi_ref=phi_ref)
    run("retrace", clean, training={**decoys, "retrace": rt}, info=rinfo)
    if rng.random() < 0.75:
        wv = F.wrong_voxel(world.voxel_um, rng)
        run("wrong_voxel", clean, voxel=wv, info={"variant": "value", "used_um": wv, "true_um": world.voxel_um})
    else:
        other_um = F.wrong_voxel(world.voxel_um, rng)
        fm = S.write_metadata(wdir / "metadata_other.json", other_um)
        run("wrong_voxel", clean, voxel=other_um, meta_path=fm, meta_source=_vol_url(f"other{seed}") + "/metadata.json",
            info={"variant": "foreign_metadata", "used_um": other_um, "true_um": world.voxel_um})
    shutil.rmtree(wdir, ignore_errors=True)
    return out


def retrace_scale_trials(n_trials: int, seed: int) -> list[dict]:
    """Part B: re-traces and decoys at the official 20-vox grid step, radii 300-3000."""
    rng = np.random.default_rng(seed)
    out = []
    for t in range(n_trials):
        R = float(rng.uniform(300, 3000))
        c = (4000.0, 4000.0)
        phi = float(rng.uniform(0, 2 * math.pi))
        z0 = float(rng.uniform(100, 1000))
        win = cylinder_grid(R, c, (30, 30), TRAIN_STEP, 0.0, s0=0.0, z0=z0, phi_ref=phi).astype(np.float64)
        rt, info = F.retrace_of(R, c, (30, 30), TRAIN_STEP, 0.0, z0, rng, step=TRAIN_STEP, phi_ref=phi)
        gap = float(rng.uniform(3.0, 20.0)) * (1 if rng.random() < 0.5 else -1)
        nb = cylinder_grid(R + gap, c, (30, 30), TRAIN_STEP, float(rng.uniform(-10, 10)),
                           s0=float(rng.uniform(-100, 100)), z0=z0 + float(rng.uniform(-100, 100)),
                           phi_ref=phi).astype(np.float64)
        far = cylinder_grid(R, c, (30, 30), TRAIN_STEP, 0.0, s0=30 * TRAIN_STEP + 200.0, z0=z0,
                            phi_ref=phi).astype(np.float64)
        r_rt = P.check_retrace(win, {"retrace": rt})
        r_nb = P.check_retrace(win, {"neighbour": nb})
        r_far = P.check_retrace(win, {"far": far})
        seg = r_rt.details["per_segment"]["retrace"]
        out.append({"trial": t, "radius": R, "retrace": info, "neighbour_gap_vox": gap,
                    "retrace_caught": not r_rt.passed, "retrace_vertex_only": seg["vertex"]["same"],
                    "retrace_surface_only": seg["surface"]["same"],
                    "retrace_vertex_counts": seg["vertex"]["counts"], "retrace_surface_counts": seg["surface"]["counts"],
                    "neighbour_false_alarm": not r_nb.passed, "far_false_alarm": not r_far.passed})
    return out


def summarise(gate: list[dict], scale: list[dict]) -> dict:
    per: dict = {}
    for f in F.FAULTS:
        rows = [r for r in gate if r["case"] == f]
        own = OWN_CHECK[f]
        per[f] = {"n": len(rows), "caught_by_gate": sum(not r["passed"] for r in rows),
                  "caught_by_own_check": sum(own in r["failed"] for r in rows), "own_check": own,
                  "other_checks_fired": sorted({c for r in rows for c in r["failed"] if c != own})}
        per[f]["catch_rate"] = per[f]["caught_by_own_check"] / max(1, len(rows))
    clean = [r for r in gate if r["case"] == "clean"]

    def mn(key):
        v = [r[key] for r in clean if r.get(key) is not None and math.isfinite(r[key])]
        return min(v) if v else None

    out = {
        "provenance": PROVENANCE, "tribunal_version": TRIBUNAL_VERSION,
        "faults": per,
        "clean": {"n": len(clean), "passed": sum(r["passed"] for r in clean),
                  "false_alarm_rate": sum(not r["passed"] for r in clean) / max(1, len(clean)),
                  "min_mirror_margin": mn("mirror_margin"), "min_depth_margin": mn("depth_margin"),
                  "min_slice_margin": mn("slice_margin"), "min_best_ncc": mn("best_ncc")},
        "retrace_at_20vox": {
            "n": len(scale), "caught": sum(r["retrace_caught"] for r in scale),
            "caught_by_literal_vertex_rule_alone": sum(r["retrace_vertex_only"] for r in scale),
            "caught_by_surface_rule_alone": sum(r["retrace_surface_only"] for r in scale),
            "neighbour_false_alarms": sum(r["neighbour_false_alarm"] for r in scale),
            "far_same_sheet_false_alarms": sum(r["far_false_alarm"] for r in scale),
        },
    }
    all_caught = all(v["catch_rate"] == 1.0 for v in per.values()) and (
        out["retrace_at_20vox"]["caught"] == out["retrace_at_20vox"]["n"])
    no_false = out["clean"]["false_alarm_rate"] == 0.0 and out["retrace_at_20vox"]["neighbour_false_alarms"] == 0 \
        and out["retrace_at_20vox"]["far_same_sheet_false_alarms"] == 0
    out["verdict"] = "PASS" if (all_caught and no_false) else "FAIL"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--worlds", type=int, default=30)
    ap.add_argument("--scale-trials", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rows", type=Path, default=None, help="optional per-trial JSONL")
    ap.add_argument("--texture-sigma", type=float, default=1.0)
    ap.add_argument("--noise-max", type=float, default=6.0)
    a = ap.parse_args(argv)
    tmp = Path(tempfile.mkdtemp(prefix="tribunal_"))
    gate = []
    try:
        for i in range(a.worlds):
            gate += world_trials(a.seed + i, tmp, texture_sigma=a.texture_sigma, noise_max=a.noise_max)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    scale = retrace_scale_trials(a.scale_trials, a.seed + 10_000)
    s = summarise(gate, scale)
    s["args"] = {"worlds": a.worlds, "scale_trials": a.scale_trials, "seed": a.seed,
                 "texture_sigma": a.texture_sigma, "noise_max": a.noise_max}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if a.rows:
        with open(a.rows, "w", encoding="utf-8") as f:
            for r in gate:
                f.write(json.dumps({"part": "gate", **r}, sort_keys=True, default=float) + "\n")
            for r in scale:
                f.write(json.dumps({"part": "retrace20", **r}, sort_keys=True, default=float) + "\n")
    print(json.dumps({"verdict": s["verdict"], "catch": {k: v["catch_rate"] for k, v in s["faults"].items()},
                      "clean_false_alarm_rate": s["clean"]["false_alarm_rate"],
                      "retrace_at_20vox": s["retrace_at_20vox"]}, sort_keys=True))
    return 0 if s["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
