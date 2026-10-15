# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic test suite for the rejection-gated tracer (build c).

Criteria (fixed here, 2026-09-25 ~19:00Z, after one exploratory run per config on scene A only):
  T1 no-bridge  (scenes B, B_switch): 0 vertices nearest the second sheet AND 0 grid edges joining
                vertices nearest different sheets, in every repeat.
                Amendment 1 (after the first suite run, 2026-09-25 ~19:40Z): also n_valid >= 20 in
                every repeat (a trace that never grew passes vacuously), and the B_switch seed moved
                from phi 0.2 to 0.15 because at 0.2 every build including villa main died at the seed.
  T2 continue   (scene C, hole of radius 25 vox between the seed and the far part of the sheet):
                >= 1 distance rejection inside the hole (+ one step) AND far-side core coverage >= 0.90
                in every repeat; the negative control (gate_negctl_freeze) must show lower far-side
                coverage (discriminativeness check, reported only).
  T3 full area  (scene A): core coverage >= 0.95 (core = true sheet support eroded by one step,
                20 vox, since a gated tracer must not place vertices past the physical border) AND
                traced-outside-truth fraction <= 0.01 AND max |r - R| <= 2.5 vox, in every repeat.
  T4 no fold    (informational, added 2026-09-25 ~20:00Z after folds were seen in run 2; not one of
                the three task tests): double_covered_frac <= 0.02 on the seed sheet in every repeat,
                all scenes. A fold (the grid traced twice over the same sheet) is invisible to a
                distance gate and is not a transverse crossing.
                Amendment 2 (2026-09-25 ~23:50Z, after run 3): threshold 0.02 -> 0.10. The raster metric
                reads 0.033-0.051 on clean single-layer runs (run 3, 60+ runs: quad rasterisation
                overlap), while folds read 0.37-0.84; 0.02 sat below the no-fold baseline.
Coordinates: vertices (x, y, z); volumes [z, y, x]. Numbers only.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import (BIN_GATED, BIN_VANILLA, Scene, Sheet, find_single_segment, params_json,  # noqa: E402
                   render, run_logged, surface_report, vc_cmd, vertex_cyl, write_zarr)

REPO = Path("/home/user/dominion")
RUNS = REPO / "logs/sib/tracer/runs.jsonl"
WORK = Path("/work/synth")
AXIS = (160.0, -100.0)
SHAPE = (240, 200, 320)
ZR = (20.0, 220.0)


def scenes() -> dict[str, Scene]:
    A = Sheet(R=260, phi=(-0.45, 0.45), z=ZR)
    return {
        "A": Scene(SHAPE, AXIS, [A]),
        "B": Scene(SHAPE, AXIS, [A, Sheet(R=268, phi=(-0.45, 0.45), z=ZR)]),
        # sheet A ends at phi = -0.05, sheet B (8 vox outside) continues: a tangent or attracted
        # continuation past A's end lands on B
        "B_switch": Scene(SHAPE, AXIS, [Sheet(R=260, phi=(-0.05, 0.45), z=ZR),
                                        Sheet(R=268, phi=(-0.45, 0.45), z=ZR)]),
        "C": Scene(SHAPE, AXIS, [Sheet(R=260, phi=(-0.45, 0.45), z=ZR, holes=[(-0.12, 120.0, 25.0)])]),
    }


# B_switch seed moved 0.2 -> 0.15 (amendment 1): at 0.2 even villa main fails at the seed quad
SEED_PHI = {"A": 0.0, "B": 0.0, "B_switch": 0.15, "C": 0.1}


def seed_xyz(scene: Scene, phi: float, z: float = 120.0, R: float = 260.0) -> list[float]:
    return [round(scene.axis_xy[0] + R * math.sin(phi), 3), round(scene.axis_xy[1] + R * math.cos(phi), 3), z]


CONFIGS = {
    # declared presets (task P): gate at 1.5 / 2.0 / 2.5, compactness on
    "S15": dict(binary="gated", reject_dist_th=1.5, compactness=True),
    "S20": dict(binary="gated", reject_dist_th=2.0, compactness=True),
    "S25": dict(binary="gated", reject_dist_th=2.5, compactness=True),
    # same presets + official villa-main parameter space_line_weight 0.1 (the 2025 space-line weight)
    "L15": dict(binary="gated", reject_dist_th=1.5, compactness=True, space_line_weight=0.1),
    "L20": dict(binary="gated", reject_dist_th=2.0, compactness=True, space_line_weight=0.1),
    "L25": dict(binary="gated", reject_dist_th=2.5, compactness=True, space_line_weight=0.1),
    # controls
    "VAN": dict(binary="vanilla"),
    "VANL": dict(binary="vanilla", space_line_weight=0.1),
    "NEG15L": dict(binary="gated", reject_dist_th=1.5, compactness=True, space_line_weight=0.1, gate_negctl_freeze=True),
    "NEG15": dict(binary="gated", reject_dist_th=1.5, compactness=True, gate_negctl_freeze=True),
}


def prepare(name: str, scene: Scene) -> tuple[Path, Path]:
    vol = render(scene)
    h = hashlib.sha256(vol.tobytes()).hexdigest()
    zp, gp = WORK / f"{name}_{h[:12]}.zarr", WORK / f"{name}_{h[:12]}.grids"
    if not (zp / "0" / ".zarray").exists():
        write_zarr(zp, vol, f"synth{name}_{h[:12]}")
    if not (gp / "metadata.json").exists():
        cmd = vc_cmd(BIN_VANILLA, "vc_gen_normalgrids", ["-i", str(zp), "-o", str(gp), "--spiral-step", "20",
                                                        "--grid-step", "64", "--preview-every", "0"], cpus=4, threads=4)
        rc = run_logged(f"synth_normalgrids_{name}", cmd, WORK / f"{name}_grids.log", RUNS)
        assert rc == 0, f"normal grid generation failed for {name}"
    return zp, gp


def run_one(scene_name: str, cfg_name: str, rep: int, generations: int = 30) -> dict:
    sc = scenes()[scene_name]
    zp, gp = prepare(scene_name, sc)
    cfg = dict(CONFIGS[cfg_name])
    binary = BIN_GATED if cfg.pop("binary") == "gated" else BIN_VANILLA
    tag = f"{scene_name}_{cfg_name}_r{rep}"
    out = WORK / "runs" / tag
    if out.exists():
        import shutil
        shutil.rmtree(out)
    out.mkdir(parents=True)
    p = params_json(WORK / "runs" / f"{tag}.json", generations=generations, normal_grid_path=str(gp), **cfg)
    seed = seed_xyz(sc, SEED_PHI[scene_name])
    cmd = vc_cmd(binary, "vc_grow_seg_from_seed",
                 ["--volume", str(zp), "--target-dir", str(out), "--params", str(p), "--seed", *map(str, seed)])
    rc = run_logged(f"synth_{tag}", cmd, WORK / "runs" / f"{tag}.log", RUNS)
    res = {"scene": scene_name, "config": cfg_name, "rep": rep, "rc": rc, "seed": seed, "params": json.loads(p.read_text())}
    seg = find_single_segment(out) if rc == 0 else None
    if seg is None:
        res["error"] = "no segment"
        return res
    rep_ = surface_report(sc, seg)
    res.update(rep_)
    if scene_name == "C":
        res.update(hole_metrics(sc, seg))
    return res


def hole_metrics(sc: Scene, seg: Path) -> dict:
    """Rejections inside the hole (+ one step) and far-side core coverage (phi < hole - radius - step)."""
    import tifffile
    s = sc.sheets[0]
    pc, zc, rad = s.holes[0]
    out = {}
    gr = seg / "gate_reject.tif"
    if gr.exists():
        g = tifffile.imread(gr)
        rx, ry, rz = [tifffile.imread(seg / f"gate_rej_{a}.tif") for a in "xyz"]
        m = (g & 1) > 0
        r, phi = np.hypot(rx - sc.axis_xy[0], ry - sc.axis_xy[1]), np.arctan2(rx - sc.axis_xy[0], ry - sc.axis_xy[1])
        d = np.hypot(s.R * (phi - pc), rz - zc)
        out["n_rej_dist_in_hole"] = int((m & (d <= rad + 20)).sum())
    # far-side core coverage: restrict the coverage raster to phi < pc - (rad + 20)/R
    far = Scene(sc.shape, sc.axis_xy, [Sheet(R=s.R, phi=(s.phi[0], pc - (rad + 20) / s.R), z=s.z)])
    import sys as _s
    _s.path.insert(0, str(REPO / "src"))
    from hercules.geometry.tifxyz import read_tifxyz
    from synth import coverage
    mm = read_tifxyz(seg)
    cov = coverage(far, 0, mm.points.astype(np.float64), mm.valid)
    out["far_core_frac"] = cov["covered_core_frac"]
    out["far_core_px"] = cov["core_px"]
    return out


def verdicts(results: list[dict]) -> dict:
    """Apply the fixed criteria per (scene-test, config)."""
    by = {}
    for r in results:
        by.setdefault((r["scene"], r["config"]), []).append(r)
    V = {}
    for (scn, cfg), rs in sorted(by.items()):
        ok = all("error" not in r for r in rs)
        if scn in ("B", "B_switch"):
            test = "T1_no_bridge"
            ok = ok and all(r["n_valid"] >= 20 and r["n_vertices_by_sheet"][1] == 0 and r["n_bridge_edges"] == 0
                            for r in rs)
        elif scn == "C":
            test = "T2_continue"
            ok = ok and all(r.get("n_rej_dist_in_hole", 0) >= 1 and r["far_core_frac"] >= 0.90 for r in rs)
        else:
            test = "T3_full_area"
            ok = ok and all(r["coverage_seed_sheet"]["covered_core_frac"] >= 0.95 and
                            r["coverage_seed_sheet"]["traced_outside_truth_frac"] <= 0.01 and
                            r["max_abs_r_resid"] <= 2.5 for r in rs)
        V[f"{test}|{scn}|{cfg}"] = {"pass": bool(ok), "n": len(rs)}
        fold_ok = all("error" not in r and r["coverage_seed_sheet"].get("double_covered_frac", 1) <= 0.10 for r in rs)
        V[f"T4_no_fold|{scn}|{cfg}"] = {"pass": bool(fold_ok), "n": len(rs),
                                        "double_covered_frac": [r.get("coverage_seed_sheet", {}).get("double_covered_frac") for r in rs]}
    return V


def main(argv: list[str]) -> None:
    reps = int(argv[1]) if len(argv) > 1 else 3
    plan = []
    for cfg in ["S15", "S20", "S25", "L15", "L20", "L25", "VAN", "VANL"]:
        for scn in ["A", "B", "B_switch", "C"]:
            plan.append((scn, cfg))
    plan += [("C", "NEG15"), ("C", "NEG15L")]
    results = []
    outp = REPO / "logs/sib/tracer/synth/results.jsonl"
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w") as f:
        for scn, cfg in plan:
            for rep in range(reps):
                r = run_one(scn, cfg, rep)
                results.append(r)
                f.write(json.dumps(r) + "\n")
                f.flush()
                c = r.get("coverage_seed_sheet", {})
                print(scn, cfg, rep, "valid", r.get("n_valid"), "sheetB", (r.get("n_vertices_by_sheet") or [0, 0])[1:],
                      "bridge", r.get("n_bridge_edges"), "core", round(c.get("covered_core_frac", -1), 3),
                      "far", r.get("far_core_frac"), "rej", r.get("gate_reject_counts"), flush=True)
    V = verdicts(results)
    (REPO / "logs/sib/tracer/synth/verdicts.json").write_text(json.dumps(V, indent=1) + "\n")
    print(json.dumps(V, indent=1))


if __name__ == "__main__":
    main(sys.argv)
