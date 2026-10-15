"""hzw1 (RULES.md DECL-P4-6-A4): E2 offset sweep restricted to a column range, using p4-highz's stage_off.run_tiles
unchanged (p4-highz commit 3e3a5ba). The only change is a filter of the eligible tile list to c0 <= c <= c1.
Records are written by run_tiles itself, so the format is exactly p4-highz's off_*.jsonl. Resumable (run_tiles skips
tiles already in the output file). No screen or verdict is computed here.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python run_cols.py <p4-highz worktree at 3e3a5ba> <scratch> <material> <c0> <c1> <o_um,...>
"""
import multiprocessing as mp
import os
import sys

hz, scr, name, c0, c1, offs = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
sys.path.insert(0, os.path.join(hz, "tools/sib/p4-highz"))
os.chdir(hz)
import common as C  # noqa: E402
import stage_off as SO  # noqa: E402

_load = C.load_material


def load_cols(n, s):
    m = _load(n, s)
    m["tiles"] = [t for t in m["tiles"] if c0 <= t["c"] <= c1]
    return m


C.load_material = load_cols
if __name__ == "__main__":
    with mp.get_context("fork").Pool(SO.NPROC) as pool:
        SO.run_tiles(scr, hz, name, [int(x) for x in offs.split(",")], pool)
