"""p4-pig-cu analysis (DECL-P4-10 items 3-4): thresholds, false-positive rates, injection sensitivity / detection limit,
scores.json and hotspots.json. Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python analyze.py [--onsheet-dir DIR]
"""
import json
import os
import subprocess
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
L = os.path.join(REPO, "logs/sib/p4-pig-cu")
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
EXCL_REF = "origin/claude/gifted-bell-gavnl5-sib-p4-excl"
EXCL = {"E1": "logs/sib/p4-excl/excl_d_a.json", "E2": "logs/sib/p4-excl/excl_a.json",
        "C1": "logs/sib/p4-excl/excl_d_b.json", "C2": None}
CTRL = {"E1": "C1", "E2": "C2"}


def jl(p):
    return [json.loads(x) for x in open(p)] if os.path.exists(p) else []


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def excl_flags(M):
    if not EXCL.get(M):
        return None, "no flag file for this material"
    try:
        d = json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{EXCL_REF}:{EXCL[M]}"], stderr=subprocess.DEVNULL))
    except subprocess.CalledProcessError:
        return None, f"{EXCL[M]} not yet published on {EXCL_REF}"
    out = {}
    for k, v in d["tiles"].items():
        out[k] = bool(v.get("labelled_adjacent_union", v.get("labelled_adjacent")))
    return out, EXCL[M]


def main():
    P = json.load(open(os.path.join(L, "params.json")))
    S = {M: jl(os.path.join(L, "scores", M, f"scores_{M}.jsonl")) for M in ("C1", "E1", "C2", "E2")}
    INJ = {M: jl(os.path.join(L, "injection", f"inj_{M}.jsonl")) for M in ("C1", "E1", "C2", "E2")}
    ONS = {M: {(d["r"], d["c"]): d for d in jl(os.path.join(L, "onsheet", f"onsheet_{M}.jsonl"))} for M in S}
    res = {"provenance": PROV, "params_sha256_file": "params_freeze.json", "tiles_scored": {M: len(v) for M, v in S.items()},
           "thresholds": {}, "false_positive": {}, "injection": {}, "nulls": {}}
    thr = {}
    for E, C in CTRL.items():
        cs = [d["det"]["score"] for d in S[C]] + [d["rot90"]["score"] for d in S[C]]
        if len(S[C]) >= 10:
            thr[E] = thr[C] = float(np.percentile(cs, 99))
            res["thresholds"][E] = {"from": C, "n_control_tiles": len(S[C]), "thr_p99": thr[E],
                                    "control_score_pcts": {q: float(np.percentile(cs, q)) for q in (50, 90, 95, 99)},
                                    "control_max": float(max(cs))}
            # leave-one-out control FP
            sc = np.array([d["det"]["score"] for d in S[C]])
            r9 = np.array([d["rot90"]["score"] for d in S[C]])
            loo = 0
            for i in range(len(sc)):
                pool = np.concatenate([np.delete(sc, i), np.delete(r9, i)])
                loo += sc[i] > np.percentile(pool, 99)
            res["false_positive"][C] = {"leave_one_out_rate": loo / len(sc), "n": len(sc),
                                        "rot90_exceed_rate": float((r9 > thr[E]).mean()),
                                        "rot90_vs_score_max_abs_diff": float(np.max(np.abs(r9 - sc))),
                                        "note": "detector is isotropic up to the even/odd filter origin; rot90 is a check, not independent"}
    for M, v in S.items():
        if not v or M not in thr:
            continue
        sc = np.array([d["det"]["score"] for d in v])
        pm = np.array([d["perm"]["score"] for d in v])
        res["nulls"][M] = {"perm_exceed_thr_rate": float((pm > thr[M]).mean()), "perm_max": float(pm.max()),
                           "perm_mean": float(pm.mean()), "score_exceed_thr": int((sc > thr[M]).sum()),
                           "score_median": float(np.median(sc)), "score_max": float(sc.max()), "n": len(v)}
    # injection
    for M, recs in INJ.items():
        if not recs or M not in thr:
            continue
        t = thr[M]
        blank = np.array([r["blank"]["score"] for r in recs])
        out = {"n_sites": len(recs), "thr": t, "blank_block_fp_rate": float((blank > t).mean()),
               "blank_block_fp_ci95": wilson(int((blank > t).sum()), len(recs)), "blank_scores": blank.tolist(),
               "blank_letter_zone_scores": [r["blank"]["letter_zone_score"] for r in recs], "variants": {}}
        for vk in recs[0]["variants"]:
            ls = np.array([r["variants"][vk]["letter_score"] for r in recs])
            k = int((ls > t).sum())
            out["variants"][vk] = {"sensitivity": k / len(recs), "k": k, "ci95": wilson(k, len(recs)),
                                   "letter_score_median": float(np.median(ls)), "letter_score_min": float(ls.min()),
                                   "n_grains_median": float(np.median([r["variants"][vk]["n_grains"] for r in recs]))}
        order = ["S2", "F1", "S1", "D1", "F2", "D2", "D3", "D4"]
        for ck in P["injection"]["contrast"]:
            dl = None
            for lv in order:
                vv = out["variants"].get(f"{lv}_{ck}")
                if vv and vv["sensitivity"] >= 0.8:
                    dl = lv
                    break
            out[f"lowest_level_with_sens_ge_0.8_{ck}"] = dl
        pv = out["variants"].get("D3_conservative", {}).get("sensitivity")
        out["verdict_plausible"] = None if pv is None else ("SENSITIVE" if pv >= 0.8 else "INSENSITIVE")
        res["injection"][M] = out
    # scores.json and hotspots
    rows, hot = [], []
    for M in ("E1", "E2", "C1", "C2"):
        fl, fsrc = excl_flags(M)
        for d in S[M]:
            key = f"r{d['r']}_c{d['c']}"
            la = None if fl is None else fl.get(key)
            top = d["det"]["clusters"][0] if d["det"]["clusters"] else None
            ons = ONS[M].get((d["r"], d["c"]))
            row = {"material": M, "r": d["r"], "c": d["c"], "score": d["det"]["score"], "rot90": d["rot90"]["score"],
                   "perm": d["perm"]["score"], "n_clusters": d["det"]["n_clusters"], "top_cluster": top,
                   "grains": d.get("grains"), "valid_cells": d["valid_cells"], "chunks_absent": d["chunks_absent"],
                   "labelled_adjacent": la, "flag_source": fsrc, "thr": thr.get(M),
                   "above_thr": (d["det"]["score"] > thr[M]) if M in thr else None,
                   "f_in": ons["f_in"] if ons else None}
            rows.append(row)
            if M in ("E1", "E2") and row["above_thr"]:
                status = []
                if ons is None:
                    status.append("f_in not computed")
                elif ons["f_in"] is None or ons["f_in"] < 0.8:
                    status.append("f_in < 0.8")
                # DECL-P4-12 item 3: model-free channel, the labelled-adjacency flag is reported, not excluding
                row["hotspot"] = not status
                row["hotspot_blockers"] = status
                hot.append(row)
    json.dump({"provenance": PROV, "tiles": rows}, open(os.path.join(L, "scores.json"), "w"), indent=1)
    json.dump({"provenance": PROV, "rule": P["hotspot"], "above_threshold": hot,
               "hotspots": [h for h in hot if h.get("hotspot")]}, open(os.path.join(L, "hotspots.json"), "w"), indent=1)
    # DECL-P4-12: E2 title zone c10-c17 reported separately
    tz = [r for r in rows if r["material"] == "E2" and 10 <= r["c"] <= 17]
    res["E2_title_zone_c10_c17"] = {"n_tiles": len(tz), "thr": thr.get("E2"),
                                    "above_thr": [(r["r"], r["c"], r["score"]) for r in tz if r["above_thr"]],
                                    "score_max": max([r["score"] for r in tz], default=None),
                                    "tiles": [{k: r[k] for k in ("r", "c", "score", "perm", "n_clusters", "labelled_adjacent", "f_in")} for r in tz]}
    kt = [r for r in rows if r["material"] == "E2" and r["c"] <= 8]
    res["E2_known_text_c0_c8"] = {"n_tiles": len(kt), "above_thr": sum(1 for r in kt if r["above_thr"]),
                                  "score_median": float(np.median([r["score"] for r in kt])) if kt else None}
    json.dump(res, open(os.path.join(L, "summary.json"), "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("tiles_scored", "thresholds", "false_positive", "nulls")}, indent=1))
    for M, o in res["injection"].items():
        print(M, "sites", o["n_sites"], "blankFP", o["blank_block_fp_rate"], "verdict", o["verdict_plausible"],
              {k: v["sensitivity"] for k, v in o["variants"].items()})
    print("above-thr E tiles:", len(hot), "hotspots:", sum(1 for h in hot if h.get("hotspot")))


if __name__ == "__main__":
    main()
