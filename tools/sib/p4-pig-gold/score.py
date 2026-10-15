"""Score a material's tiles with the frozen params (DECL-P4-10 item 4). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

Reads run_tiles.py output (<outdir>/<MAT>/tiles.jsonl and r*_c*.npz). Per tile: A_hot (Z > tau), component stats.
For every tile with A_hot > A_p99: the same detector on the two gap windows at full coverage, f_in = A_sheet /
(A_sheet + A_gap_lo + A_gap_hi). Flags: labelled_adjacent from the given excl json (union flag) or 'pending'.
Usage: python score.py <params.json> <MAT> <outdir> <scratch> <out.json> [--excl <excl.json>] [--procs 4]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gold as G  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("params")
    ap.add_argument("mat")
    ap.add_argument("outdir")
    ap.add_argument("scratch")
    ap.add_argument("out")
    ap.add_argument("--excl", default=None)
    ap.add_argument("--threads", type=int, default=64)
    a = ap.parse_args()
    P = json.load(open(a.params))
    mp_ = P["materials"][a.mat]
    tau, a99 = mp_["tau"], mp_["A_p99_mm2"]
    m = G.MATERIALS[a.mat]
    px_mm = m["px_um"] * m["B"] / 1000.0
    excl = None
    if a.excl:
        excl = json.load(open(a.excl))["tiles"]
    recs = [json.loads(l) for l in open(os.path.join(a.outdir, a.mat, "tiles.jsonl"))]
    mat = None
    rows = []
    for r in sorted(recs, key=lambda d: (d["r"], d["c"])):
        d = np.load(os.path.join(a.outdir, a.mat, f"r{r['r']}_c{r['c']}.npz"))
        maps = {"P": d["P"], "S": np.zeros_like(d["P"]), "n": d["n"].astype(np.float32)}
        Z, _, res = G.score_maps(maps, px_mm, P["core"]["radius_mm"], tau=tau)
        key = f"r{r['r']}_c{r['c']}"
        row = {"tile": key, "r": r["r"], "c": r["c"], "valid_fraction_src": r["valid_fraction_src"],
               "chunks": r["chunks"], "absent": r["absent"], "usable_px": r["usable_px"]["sheet"],
               "A_hot_mm2": res["A_hot_mm2"], "largest_comp_mm2": res["largest_comp_mm2"],
               "n_comp_letter_scale": res["n_comp_letter_scale"], "Z_max": res.get("Z_max"),
               "Z_p50": res.get("Z_p50"), "Z_p99": res.get("Z_p99"), "Zs_max": r.get("Zs_max"),
               "over_A_p99": res["A_hot_mm2"] > a99}
        stored_Z = d["Z"].astype(np.float32)
        row["recompute_matches_stored_Z"] = bool(np.allclose(np.nan_to_num(Z, nan=-999), np.nan_to_num(stored_Z, nan=-999), atol=0.1))
        if excl is not None:
            e = excl.get(key)
            row["labelled_adjacent"] = None if e is None else bool(e["labelled_adjacent"])
        else:
            row["labelled_adjacent"] = "pending"
        if row["over_A_p99"]:
            if mat is None:
                mat = G.load_material(a.mat, a.scratch)
            gw = P["gap_windows"][a.mat]
            wins = {"gap_lo": tuple(gw[0]), "gap_hi": tuple(gw[1])}
            gm, gmeta = G.tile_work_maps(mat, r["r"], r["c"], wins, P["core"]["sat"], threads=a.threads)
            ga = {}
            for k in wins:
                _, _, gres = G.score_maps(gm[k], px_mm, P["core"]["radius_mm"], tau=tau)
                ga[k] = gres["A_hot_mm2"]
            tot = res["A_hot_mm2"] + ga["gap_lo"] + ga["gap_hi"]
            row["A_gap_lo_mm2"], row["A_gap_hi_mm2"] = ga["gap_lo"], ga["gap_hi"]
            row["f_in"] = res["A_hot_mm2"] / tot if tot > 0 else None
        row["hotspot"] = bool(row["over_A_p99"] and row.get("f_in") is not None and row["f_in"] >= 0.8
                              and row["labelled_adjacent"] is False)
        row["hotspot_if_flag_pending"] = bool(row["over_A_p99"] and row.get("f_in") is not None and row["f_in"] >= 0.8)
        rows.append(row)
        print(key, round(row["A_hot_mm2"], 4), row.get("f_in"), row["hotspot"], flush=True)
    out = {"provenance": G.PROV, "material": a.mat, "tau": tau, "A_p99_mm2": a99, "px_mm": px_mm,
           "excl": a.excl, "n_tiles": len(rows), "n_over_A_p99": sum(r["over_A_p99"] for r in rows),
           "n_hotspots": sum(r["hotspot"] for r in rows), "tiles": rows}
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
