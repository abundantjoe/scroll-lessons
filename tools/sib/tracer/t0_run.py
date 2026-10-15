# Provenance: Project HERCULES | owner the owner | [id removed]
"""T0 runner for the gated tracer (build c3). PREPARED, NOT RUN.

  t0_run.py --declaration <RULES.md ID> --family L|S [--presets 15,20,25]      (T0: once, when declared)
  t0_run.py --selftest-dev <dev seg id> --family L                                (pipeline check on a dev seed)

The T0 seeds (auto_grown_20250923163217042, 163219195, 163223390, 163227956, 163230146) are read only
when --declaration names an existing '## <ID>' heading in RULES.md. Per seed: sync the normal-grid
band (seed +- (generations*20 + 100) vox in each axis), run the presets, compute metrics and the
half-pitch control, clear the remote chunk cache. generations = the seed's meta.json value
(vc_gsfs_params.generations), per DECL-TSURF, unless --generations is given.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_run  # noqa: E402

REPO = Path("/home/user/dominion")
T0_IDS = ["auto_grown_20250923163217042", "auto_grown_20250923163219195", "auto_grown_20250923163223390",
          "auto_grown_20250923163227956", "auto_grown_20250923163230146"]
NG_PREFIX = ("PHerc1203/representations/predictions/surfaces/"
             "20250820131727-surface-20260413222639-surface-m7-L0-th0.2.normal-grids/")
SHAPE_ZYX = (18977, 6844, 6844)


def declared(decl: str) -> bool:
    return any(line.strip() == f"## {decl}" for line in open(REPO / "RULES.md"))


def fetch_team(seg_id: str) -> Path:
    d = Path("/work/s3/PHerc1203/segments/raw") / seg_id
    if not (d / "meta.json").exists():
        subprocess.check_call(["/opt/hv/bin/python", "/work/scripts/s3get.py",
                               str(REPO / "logs/sib/tracer/downloads_sha256.jsonl"), "/work/s3",
                               f"PHerc1203/segments/raw/{seg_id}/"])
    return d


def sync_band(seed, gens: int, manifest: Path) -> None:
    r = gens * 20 + 100
    x, y, z = seed
    rng = lambda c, n: f"{max(0, int(c - r))}-{min(n - 1, int(c + r))}"
    subprocess.check_call(["/opt/hv/bin/python", str(REPO / "tools/sib/tracer/sync_normalgrids.py"), NG_PREFIX,
                           dev_run.NG, str(manifest),
                           f"xy:{rng(z, SHAPE_ZYX[0])}", f"xz:{rng(y, SHAPE_ZYX[1])}", f"yz:{rng(x, SHAPE_ZYX[2])}"])


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--declaration")
    g.add_argument("--selftest-dev")
    ap.add_argument("--family", choices=["L", "S"], required=True)
    ap.add_argument("--presets", default="15,20,25")
    ap.add_argument("--generations", type=int)
    a = ap.parse_args()
    if a.declaration:
        if not declared(a.declaration):
            raise SystemExit(f"REFUSED: no '## {a.declaration}' heading in RULES.md")
        seeds, tag = T0_IDS, "t0"
        os.environ["HRC_T0_DECLARATION"] = a.declaration
    else:
        if any(t in a.selftest_dev for t in dev_run.T0):
            raise SystemExit("REFUSED: self-test must use a dev seed")
        seeds, tag = [a.selftest_dev], "t0selftest"
    dev_run.OUT = Path(f"/work/{tag}")
    for seg in seeds:
        team = fetch_team(seg)
        meta = json.loads((team / "meta.json").read_text())
        gens = a.generations or int(meta.get("vc_gsfs_params", {}).get("generations", 45))
        sync_band(meta["seed"], gens, Path(f"/work/logs/ng1203_{tag}_manifest.jsonl"))
        for p in a.presets.split(","):
            cfg = f"{a.family}{p}"
            r = dev_run.run(cfg, seg, generations=gens, allow_t0=bool(a.declaration),
                            results=REPO / f"logs/sib/tracer/{tag}/results.jsonl")
            print(cfg, seg, r["rc"], r["wall_s"], r.get("error", ""), flush=True)
        shutil.rmtree("/work/vchome/.VC3D/remote_cache", ignore_errors=True)


if __name__ == "__main__":
    main()
