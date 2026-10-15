# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-N runner: resume the gated tracer (build c5, L15 preset + gate_fix_resume_points) from a prep.py patch
in the local m7-L2 frame.

  run.py holdout [--set=key=<json>]...   recovery test inside the official mesh (5 mm held out); allowed at any time
  run.py real      the top-edge extension; REFUSED unless p4-layout edge.json shows continuing sheet
                   above r0 in c9-c15 (edge_gate()), or --edge-json names a file that does.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from synth import run_logged, vc_cmd  # noqa: E402

REPO = Path("/home/user/dominion")
BIN = "/work/villa-gated/volume-cartographer/build/hrc-gated-c5/bin"
VOL = "/work/p4n/m7l2_local.zarr"
NG = "/work/p4n/ng"
PRESET = REPO / "logs/sib/tracer/presets/L15.json"
GENS = {"holdout": 28, "real": 11}     # additional rows at 20 L2 vox = 0.192 mm: 5.4 mm / 2.1 mm
# real = 11: edge.json (p4-layout, 21:26Z) supports sheet to about +2.0 mm only (orchestrator 21:34Z: grow ~2 mm)


def params(mode: str, overrides: dict | None = None) -> dict:
    p = json.loads(PRESET.read_text())
    p.update({"generations": 1 + GENS[mode], "normal_grid_path": NG, "voxelsize": 9.6,
              "gate_fix_resume_points": True, "thread_limit": 4, "min_area_cm": 0.0})
    p.pop("mode", None)
    p.update(overrides or {})
    return p


def edge_gate(path: Path) -> tuple[bool, str]:
    """p4-layout edge.json (DECL-P4-13 item 2): the run is allowed only if its answer for c9-c15 is YES."""
    if not path.exists():
        return False, f"missing {path}"
    j = json.loads(path.read_text())
    a = (j.get("answer") or {}).get("sheet_continues_above_official_top_edge_in_c9_c15", "")
    if isinstance(a, str) and a.upper().startswith("YES"):
        return True, a
    return False, f"answer not YES: {a!r}"


def main():
    mode = sys.argv[1]
    if mode == "real":
        ej = Path(sys.argv[sys.argv.index("--edge-json") + 1]) if "--edge-json" in sys.argv else \
            REPO / "logs/sib/p4-layout/edge.json"
        ok, why = edge_gate(ej)
        print("edge gate:", ok, why, flush=True)
        if not ok:
            raise SystemExit(f"REFUSED (DECL-P4-13: run only if the edge check shows continuing sheet): {why}")
    ov = {}
    for a in sys.argv:
        if a.startswith("--set="):
            k, v = a[6:].split("=", 1)
            ov[k] = json.loads(v)
    tag = "".join(f"_{k}{v}" for k, v in ov.items())
    out = Path(f"/work/p4n/runs/{mode}{tag}_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}")
    out.mkdir(parents=True)
    pj = out / "params.json"
    pj.write_text(json.dumps(params(mode, ov), indent=1) + "\n")
    cmd = vc_cmd(BIN, "vc_grow_seg_from_seed", ["--volume", VOL, "--target-dir", str(out), "--params", str(pj),
                 "--resume", f"/work/p4n/patches/{mode}.tifxyz", "--resume-opt", "skip"], cpus=4, threads=4)
    rc = run_logged(f"p4n_{mode}", cmd, out / "trace.log", REPO / "logs/sib/tracer/runs.jsonl")
    print(json.dumps({"mode": mode, "rc": rc, "out": str(out)}))


if __name__ == "__main__":
    main()
