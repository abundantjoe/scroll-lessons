# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-22 trace: build c5, L15 preset + gate_fix_resume_points, resumed from /work/p422/resume.tifxyz
(official r5-r8 x c14-c19 + ring, holes removed); 15 generations fill holes up to about 30 grid steps across."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import run_logged, vc_cmd  # noqa: E402
import prep22 as P22  # noqa: E402   (P4_CFG selects the patch: p422 or p424)

REPO = Path("/home/user/dominion")
BIN = "/work/villa-gated/volume-cartographer/build/hrc-gated-c5/bin"
GENS = 15


def main():
    p = json.loads((REPO / "logs/sib/tracer/presets/L15.json").read_text())
    p.update({"generations": 1 + GENS, "normal_grid_path": str(P22.W / "ng"), "voxelsize": 9.6,
              "gate_fix_resume_points": True, "thread_limit": 4, "min_area_cm": 0.0})
    p.pop("mode", None)
    out = Path(f"{P22.W}/runs/trace_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}")
    out.mkdir(parents=True)
    (out / "params.json").write_text(json.dumps(p, indent=1) + "\n")
    cmd = vc_cmd(BIN, "vc_grow_seg_from_seed", ["--volume", str(P22.W / "m7l2_local.zarr"), "--target-dir", str(out),
                 "--params", str(out / "params.json"), "--resume", str(P22.W / "resume.tifxyz"), "--resume-opt", "skip"],
                 cpus=4, threads=4)
    rc = run_logged(f"{P22.CFG}_trace", cmd, out / "trace.log", REPO / "logs/sib/tracer/runs.jsonl")
    print(json.dumps({"rc": rc, "out": str(out)}))


if __name__ == "__main__":
    main()
