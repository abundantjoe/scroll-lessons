"""hzw2 (DECL-P4-6-A4): run p4-highz's stage_off.py 'tiles' mode, unchanged, on E2 restricted to columns c14-c19.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python run_off.py <p4-highz checkout> <scratch> <o_um,...>
The only change is a tile filter on load_material's eligible-tile list; code, thresholds (thresholds_2p4.json T_hi),
slabs and record format are p4-highz's. Numbers only; no image is written or viewed. Resumable (appends, skips done).
"""
import multiprocessing as mp
import os
import sys

code, scr, offs = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")]
sys.path.insert(0, os.path.join(code, "tools/sib/p4-highz"))
import common as C  # noqa: E402
import stage_off as SO  # noqa: E402

COLS = range(14, 20)
_load = C.load_material


def load_filtered(name, scratch):
    m = _load(name, scratch)
    m["tiles"] = [t for t in m["tiles"] if t["c"] in COLS]
    return m


C.load_material = load_filtered
if __name__ == "__main__":
    os.chdir(code)
    with mp.get_context("fork").Pool(SO.NPROC) as pool:
        SO.run_tiles(scr, code, "E2", offs, pool)
