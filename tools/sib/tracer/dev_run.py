# Provenance: Project HERCULES | owner the owner | [id removed]
"""Dev runs of the gated tracer (build c) on PHerc1203 team surfaces of the 2025 build.

T0 TEST SEEDS ARE REFUSED HERE (auto_grown_20250923163217042, 163219195, 163223390, 163227956,
163230146): this script never reads their files and aborts if asked to run one.

Usage: dev_run.py <config> <seg_id> [<seg_id> ...]    (configs: S15 S20 S25 L15 L20 L25 VAN)
Each run: vc_grow_seg_from_seed --volume <m7 zarr (S3)> --target-dir D --params P --seed X Y Z,
then metrics (selfcross, v2 truncation, area, edges, distance to the team surface).
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import BIN_GATED, BIN_VANILLA, find_single_segment, run_logged, vc_cmd  # noqa: E402
from surfmetrics import analyse  # noqa: E402

REPO = Path("/home/user/dominion")
RUNS = REPO / "logs/sib/tracer/runs.jsonl"
T0 = {"163217042", "163219195", "163223390", "163227956", "163230146"}
M7 = ("s3://vesuvius-challenge-open-data/PHerc1203/representations/predictions/surfaces/"
      "20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr")
M7_META = Path("/work/s3/PHerc1203/representations/predictions/surfaces/"
               "20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr/metadata.json")
NG = "/work/ng1203"
TEAM = Path("/work/s3/PHerc1203/segments/raw")
OUT = Path("/work/dev")

CONFIGS = {
    "S15": {"reject_dist_th": 1.5, "compactness": True},
    "S20": {"reject_dist_th": 2.0, "compactness": True},
    "S25": {"reject_dist_th": 2.5, "compactness": True},
    "L15": {"reject_dist_th": 1.5, "compactness": True, "space_line_weight": 0.1},
    "L20": {"reject_dist_th": 2.0, "compactness": True, "space_line_weight": 0.1},
    "L25": {"reject_dist_th": 2.5, "compactness": True, "space_line_weight": 0.1},
    "VAN": {},
}


def voxel_um() -> float:
    """samplePixelSize (mm) from the m7 store's metadata.json (the tool resolves the same key)."""
    m = json.loads(M7_META.read_text())
    v = m["source"]["metadata"]["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]
    return float(v) * 1000.0


def params(cfg: str, generations: int = 45) -> dict:
    p = {"mode": "seed", "step_size": 20, "min_area_cm": 0.2, "generations": generations, "thread_limit": 1,
         "direction_fields": [], "voxelsize": voxel_um(), "normal_grid_path": NG}
    p.update(CONFIGS[cfg])
    return p


def run(cfg: str, seg_id: str, generations: int = 45, allow_t0: bool = False, results: Path | None = None) -> dict:
    """allow_t0 is set only by t0_run.py after it has verified a declaration in RULES.md."""
    if any(t in seg_id for t in T0) and not allow_t0:
        raise SystemExit(f"REFUSED: {seg_id} is a T0 test seed")
    team = TEAM / seg_id
    meta = json.loads((team / "meta.json").read_text())
    seed = meta["seed"]
    tag = f"{cfg}_{seg_id}"
    d = OUT / tag
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    pj = d / "params.json"
    pj.write_text(json.dumps(params(cfg, generations), indent=1) + "\n")
    tgt = d / "trace"
    tgt.mkdir()
    binary = BIN_VANILLA if cfg == "VAN" else BIN_GATED
    cmd = vc_cmd(binary, "vc_grow_seg_from_seed",
                 ["--volume", M7, "--target-dir", str(tgt), "--params", str(pj), "--seed", *map(str, seed)])
    t0 = time.time()
    rc = run_logged(f"dev_{tag}", cmd, d / "trace.log", RUNS)
    wall = time.time() - t0
    res = {"config": cfg, "segment": seg_id, "seed": seed, "rc": rc, "wall_s": round(wall, 1),
           "params": params(cfg, generations)}
    seg = find_single_segment(tgt) if rc == 0 else None
    if seg is None:
        res["error"] = "no segment saved (rc != 0 or area below min_area_cm)"
    else:
        sm = json.loads((seg / "meta.json").read_text())
        res["trace_meta"] = {k: sm[k] for k in sm if k.startswith("hrc_") or k in ("area_cm2", "max_gen", "elapsed_time_s")}
        res["metrics"] = analyse(seg, d / "metrics", RUNS, voxel_um(), team=team, label=tag)
    (d / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    results = results or REPO / "logs/sib/tracer/dev/results.jsonl"
    results.parent.mkdir(parents=True, exist_ok=True)
    with open(results, "a") as f:
        f.write(json.dumps(res) + "\n")
    return res


if __name__ == "__main__":
    (REPO / "logs/sib/tracer/dev").mkdir(parents=True, exist_ok=True)
    cfg = sys.argv[1]
    for sid in sys.argv[2:]:
        r = run(cfg, sid)
        m = r.get("metrics", {})
        print(cfg, sid, "rc", r["rc"], "wall", r["wall_s"], "raw_area", m.get("raw", {}).get("area_cm2"),
              "v2_area", m.get("v2", {}).get("area_cm2"), "cross", m.get("raw", {}).get("crossings"),
              "team3", m.get("team", {}).get("frac_within_3"), r.get("error", ""), flush=True)
