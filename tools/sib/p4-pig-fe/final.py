"""p4-pig-fe step 4 aggregation (numbers only): injection summary, FP rates, scores.json and hotspots.json.

Provenance: Project HERCULES | owner the owner | [id removed]

Usage (repo root): python tools/sib/p4-pig-fe/final.py
Inputs: logs/sib/p4-pig-fe/{1129,24}/{scores_<ctrl>.json, injection_<ctrl>.json, injection_<title>.json,
        scores_<title>.json}; labelled-adjacency flags per params.json (E2: logs/p4/excl/excl_a_union_e2.json on
        origin/claude/gifted-bell-gavnl5; E1: excl_d_a if published, else 'pending').
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import fe  # noqa: E402

OD = os.path.join("logs", "sib", "p4-pig-fe")
FAMS = {"1129": ("C", "E1"), "24": ("C2", "E2")}


def excl_flags(title):
    if title == "E2":
        try:
            d = json.loads(subprocess.check_output(["git", "show", "origin/claude/gifted-bell-gavnl5:logs/p4/excl/excl_a_union_e2.json"]))
            return {k: v["labelled_adjacent"] for k, v in d["tiles"].items()}, "logs/p4/excl/excl_a_union_e2.json"
        except Exception:
            return None, "unavailable"
    for ref, path in (("origin/claude/gifted-bell-gavnl5", "logs/p4/excl/excl_d_a.json"),
                      ("origin/claude/gifted-bell-gavnl5-sib-p4-excl", "logs/sib/p4-excl/excl_d_a.json")):
        try:
            d = json.loads(subprocess.check_output(["git", "show", f"{ref}:{path}"], stderr=subprocess.DEVNULL))
            return {k: v["labelled_adjacent"] for k, v in d["tiles"].items()}, f"{ref}:{path}"
        except Exception:
            pass
    return None, "excl_d_a not published yet: E1 adjacency pending"


def inj_summary(inj, theta):
    out = {}
    locs = inj["locations"]
    base = [l["baseline"]["z"] for l in locs if l["baseline"]]
    out["n_locations"] = len(locs)
    out["baseline_window_fp"] = {"fp": int(sum(z > theta for z in base)), "n": len(base),
                                 "z_median": float(np.median(base)) if base else None}
    tab = {}
    for l in locs:
        for p in l["planted"]:
            k = f"{p['regime']}|{p['t_um']}"
            d = tab.setdefault(k, {"regime": p["regime"], "R": p["R"], "t_um": p["t_um"], "z": [], "det": 0, "det_in": 0, "dz": []})
            d["z"].append(p["z"])
            d["dz"].append(p["z"] - (l["baseline"]["z"] if l["baseline"] else 0))
            d["det"] += int(p["detected"])
            d["det_in"] += int(p["detected_and_in_sheet"])
    for d in tab.values():
        n = len(d["z"])
        d.update({"n": n, "sensitivity": d["det"] / n, "sensitivity_with_f_in": d["det_in"] / n,
                  "z_median": float(np.median(d["z"])), "dz_median": float(np.median(d["dz"]))})
        del d["z"], d["dz"]
    out["by_regime_thickness"] = sorted(tab.values(), key=lambda d: (d["R"], d["t_um"]))
    lim = {}
    for reg in sorted({d["regime"] for d in tab.values()}):
        ok = [d["t_um"] for d in tab.values() if d["regime"] == reg and d["sensitivity"] >= 0.8]
        lim[reg] = min(ok) if ok else None
    out["detection_limit_um_sens_ge_0.8"] = lim
    return out


def main():
    P = fe.load_params()
    allscores, hot, summ = {}, [], {}
    for fam, (ctrl, title) in FAMS.items():
        d = os.path.join(OD, fam)
        cs = os.path.join(d, f"scores_{ctrl}.json")
        if not os.path.exists(cs):
            summ[fam] = "missing"
            continue
        C = json.load(open(cs))
        theta, sigma0 = C["theta"], C["sigma0"]
        s = {"control": ctrl, "title": title, "sigma0": sigma0, "theta": theta,
             "control_fp_leave_one_out": C["control_fp_leave_one_out"], "rot90_max_abs_diff_z": C["rot90_max_abs_diff_z"],
             "control_z": {"n": C["n_eligible_control_tiles"],
                           "max": max(t["z"] for t in C["tiles"] if "z" in t),
                           "median": float(np.median([t["z"] for t in C["tiles"] if "z" in t]))}}
        for mat in (ctrl, title):
            ip = os.path.join(d, f"injection_{mat}.json")
            if os.path.exists(ip):
                s[f"injection_{mat}"] = inj_summary(json.load(open(ip)), theta)
        ts = os.path.join(d, f"scores_{title}.json")
        if os.path.exists(ts):
            T = json.load(open(ts))
            if T.get("sigma0") == 1.0 and sigma0 != 1.0:      # raw scores from sub-sibling 2
                for t in T["tiles"]:
                    if "r_max" in t:
                        t["z"], t["z_rot90"] = t["r_max"] / sigma0, t["r_rot90_max"] / sigma0
                T["sigma0"] = sigma0
            flags, src = excl_flags(title)
            s["labelled_adjacency_source"] = src
            rows = []
            for t in T["tiles"]:
                key = f"r{t['r']}_c{t['c']}"
                la = None if flags is None else flags.get(key)
                row = {"material": title, "tile": key, "eligible": t.get("eligible"), "z": t.get("z"), "z_rot90": t.get("z_rot90"),
                       "f_in": t.get("f_in"), "argmax_block": t.get("argmax_block"), "orientation_deg": t.get("orientation_deg"),
                       "valid_block_frac": t.get("valid_block_frac"), "labelled_adjacent": la}
                row["above_theta"] = bool(t.get("z") is not None and t["z"] > theta)
                # DECL-P4-12 item 3: model-free channel, so the labelled-adjacency flag is reported, not excluding.
                row["hotspot"] = bool(row["above_theta"] and (t.get("f_in") or 0) >= 0.8)
                row["hotspot_non_adjacent_decl_p4_10"] = bool(row["hotspot"] and la is False)
                row["title_zone_c10_c17"] = bool(title == "E2" and 10 <= t["c"] <= 17)
                rows.append(row)
                if row["hotspot"]:
                    hot.append(row)
            allscores[title] = rows
            zz = [r["z"] for r in rows if r["z"] is not None]
            s["title_z"] = {"n": len(zz), "max": max(zz) if zz else None, "median": float(np.median(zz)) if zz else None,
                            "n_above_theta": sum(r["above_theta"] for r in rows),
                            "n_hotspots": sum(r["hotspot"] for r in rows),
                            "n_hotspots_non_adjacent": sum(r["hotspot_non_adjacent_decl_p4_10"] for r in rows)}
            if title == "E2":
                tz = [r for r in rows if r["title_zone_c10_c17"] and r["z"] is not None]
                s["title_zone_c10_c17"] = {"n_tiles": len(tz), "max_z": max(r["z"] for r in tz) if tz else None,
                                           "median_z": float(np.median([r["z"] for r in tz])) if tz else None,
                                           "n_above_theta": sum(r["above_theta"] for r in tz),
                                           "n_hotspots": sum(r["hotspot"] for r in tz),
                                           "top5": sorted(({"tile": r["tile"], "z": round(r["z"], 3), "f_in": r["f_in"]} for r in tz),
                                                          key=lambda d: -d["z"])[:5]}
        summ[fam] = s
    json.dump({"provenance": fe.PROV, "serves": "DECL-P4-10 item 4 (FE)", "params_sha256": fe.sha_file(fe.PARAMS),
               "tiles": allscores}, open(os.path.join(OD, "scores.json"), "w"), indent=1)
    json.dump({"provenance": fe.PROV, "rule": "z > theta AND f_in >= 0.8; labelled adjacency reported, not excluding (DECL-P4-12 item 3, which supersedes the params.json non-adjacency clause for this model-free channel)", "hotspots": hot},
              open(os.path.join(OD, "hotspots.json"), "w"), indent=1)
    json.dump({"provenance": fe.PROV, "families": summ}, open(os.path.join(OD, "summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1)[:6000])


if __name__ == "__main__":
    main()
