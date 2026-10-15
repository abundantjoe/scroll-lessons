# Provenance: Project HERCULES | owner the owner | [id removed]
"""Re-evaluate every pair of the same-papyrus table under CORR-RETRACE-RULE
(SAME iff vertex form OR surface form, either direction) and rebuild the
papyrus units under it. Resumable: one JSONL row per pair. Mesh geometry only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam3d as C  # noqa: E402
from units_run import k_for  # noqa: E402

from hercules.geometry.tifxyz import read_tifxyz  # noqa: E402


class P:  # minimal PairResult stand-in for papyrus_units
    def __init__(self, a, b, same):
        self.a, self.b, self.same = a, b, same


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--meshes", default="/work/sib_contam/meshes")
    ap.add_argument("--extra", action="append", default=[])
    ap.add_argument("--rows", required=True, help="resumable JSONL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    u = json.loads(Path(a.units).read_text())
    man = json.loads(Path(a.manifest).read_text())
    dirs = {s: Path(a.meshes) / man["scroll"] / s for s in u["segments"] if s in man["segments"]}
    dirs.update({n: Path(d) for n, d in (e.split("=", 1) for e in a.extra)})
    done = {}
    rows = Path(a.rows)
    if rows.exists():
        for line in rows.read_text().splitlines():
            r = json.loads(line)
            done[(r["a"], r["b"])] = r
    meshes: dict = {}

    def mesh(n):
        if n not in meshes:
            if len(meshes) > 6:
                meshes.pop(next(iter(meshes)))
            meshes[n] = read_tifxyz(dirs[n])
        return meshes[n]

    t0 = time.time()
    with rows.open("a") as fh:
        for p in u["pairs_tested"]:
            key = (p["a"], p["b"])
            if key in done:
                continue
            ma, mb = mesh(p["a"]), mesh(p["b"])
            r = C.corrected_pair(ma.points, mb.points, k_for(ma, 5), kB=k_for(mb, 5), workers=a.workers)
            row = {"a": p["a"], "b": p["b"], "same_nd": p["same"],
                   "corr": r, "same_corr": bool(r and (r["a_in_b"]["same"] or r["b_in_a"]["same"]))}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done[key] = row
            print(f"[{time.time() - t0:7.1f}s] {p['a'][:30]} {p['b'][:30]} corr={row['same_corr']} nd={p['same']}",
                  flush=True)
    names = sorted(u["segments"])
    res = [done[(p["a"], p["b"])] for p in u["pairs_tested"]]
    units_corr = C.papyrus_units(names, [P(r["a"], r["b"], r["same_corr"]) for r in res])
    units_union = C.papyrus_units(names, [P(r["a"], r["b"], r["same_corr"] or r["same_nd"]) for r in res])
    out = {"provenance": C.PROVENANCE, "rule": "CORR-RETRACE-RULE: SAME iff vertex form OR surface form "
           "(densify 5 x 5, >= 1000 A points within 2 vox and count[0,1) >= 2 count[2,3)), either direction",
           "units_sha256": C.sha256_file(a.units), "manifest_sha256": C.sha256_file(a.manifest),
           "n_pairs": len(res), "n_same_corr": sum(r["same_corr"] for r in res),
           "n_same_nd": sum(r["same_nd"] for r in res),
           "n_same_vertex_only": sum(bool(r["corr"]) and (r["corr"]["a_in_b"]["vertex"]["same"] or
                                                          r["corr"]["b_in_a"]["vertex"]["same"]) for r in res),
           "n_same_surface": sum(bool(r["corr"]) and (r["corr"]["a_in_b"]["surface"]["same"] or
                                                      r["corr"]["b_in_a"]["surface"]["same"]) for r in res),
           "disagreements_corr_vs_nd": [{"a": r["a"], "b": r["b"], "corr": r["same_corr"], "nd": r["same_nd"]}
                                        for r in res if r["same_corr"] != r["same_nd"]],
           "units_corr": units_corr, "units_corr_or_nd": units_union, "pairs": res}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print("pairs", len(res), "same_corr", out["n_same_corr"], "same_nd", out["n_same_nd"],
          "units_corr", len(units_corr), "units_union", len(units_union))
    return 0


if __name__ == "__main__":
    sys.exit(main())
