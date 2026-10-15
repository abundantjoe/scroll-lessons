"""Release statistics (analysis plan fixed in RULES.md, C1 declaration, 2026-10-15).

For an evaluation set of crops and a list of methods:
  * per-crop pixel AUC (judge_<tag>.json, bottom face), stroke AUC (stats/stroke_test.json), local stroke test L
    (stats/local_stroke_test.json) - read, never recomputed, so the release reports exactly what was judged;
  * crop-level percentile bootstrap CI of every mean (10 000 resamples, seed 0);
  * paired differences between methods with the same bootstrap and a count of crops on which the difference is positive;
  * NEGATIVE control: cross-crop label-swap null - each crop's score map judged against every OTHER crop's text/blank classes
    with the judge's own 5 % subsample rule, so both spatial structures are preserved and only the correspondence is broken;
  * the team model as POSITIVE control.

  release_stats.py <set-name> <out.json> <seg:crop> [<seg:crop> ...]     also writes results/per_crop_<set-name>.csv
  release_stats.py --csv <stats.json> <out.csv>                            the per-crop table only, from an existing stats file
  release_stats.py --from-json <stats.json>                                recompute summaries and pairs in place (keeps the null)
Pixel AUCs are written unrounded. Stroke and L are the toolkit's full-precision values where results/toolkit_vs_records.json has them
(equal to the research records at 4 decimals), otherwise the research records (4 decimals). The documents truncate toward zero.
"""
import json, os, sys, itertools, numpy as np
from scipy.stats import rankdata

METHODS = ["e", "v8", "gpr1", "v6b", "v6c", "v7", "v3", "v2", "v1b", "v0.1b", "team"]
NULL_TAGS = ["e", "v8", "v7", "team"]
B, SEED = 10000, 0


def boot_ci(x, b=B, seed=SEED):
    x = np.asarray(x, float)
    if len(x) == 0: return None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(b, len(x)))
    m = x[idx].mean(axis=1)
    return {"mean": float(x.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], "n": int(len(x))}


def auc(a, b):
    if len(a) == 0 or len(b) == 0: return None
    rk = rankdata(np.concatenate([a, b])); n1, n0 = len(a), len(b)
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def write_csv(res, path):
    """One row per crop, columns <method>_<metric> in the stats file's method order; empty where a value does not exist."""
    cols = [(m, k) for m in res["per_crop"] for k in ("pixel", "stroke", "local")]
    by = {m: {r["crop"]: r for r in rows} for m, rows in res["per_crop"].items()}
    with open(path, "w") as f:
        f.write(",".join(["crop"] + [f"{m}_{k}" for m, k in cols]) + "\n")
        for c in res["crops"]:
            vals = [by[m].get(c, {}).get(k) for m, k in cols]
            f.write(",".join([c] + ["" if v is None else repr(float(v)) for v in vals]) + "\n")


FULL = "results/toolkit_vs_records.json"


def full_precision():
    """Stroke AUC and L at full precision where the toolkit recomputed them (scripts/check_toolkit_records.py); each value is used only
    if it equals its 4-decimal research record after rounding, with identical disk counts (the check's own criterion)."""
    if not os.path.exists(FULL): return {}
    rows = json.load(open(FULL))["rows"]
    return {(c, m): r for c, row in rows.items() for m, r in row.items()
            if isinstance(r, dict) and r.get("stroke_equal_4dp") and r.get("local_equal_4dp")}


def summarise(name, specs, per, null):
    summary = {}
    for m, rows in per.items():
        summary[m] = {}
        for k in ("pixel", "stroke", "local"):
            v = [r[k] for r in rows if r[k] is not None]
            summary[m][k] = boot_ci(v) if len(v) == len(rows) else ({"incomplete": len(v), "of": len(rows)} if v else None)
    pairs = [("e", "v8"), ("e", "gpr1"), ("v8", "gpr1"), ("v8", "v6c"), ("v8", "v6b"), ("v6b", "v6c"),
             ("e", "v7"), ("v8", "v7"), ("team", "e"), ("e", "v2")]
    diffs = {}
    for a, b in pairs:
        if a not in per or b not in per: continue
        diffs[f"{a}-{b}"] = {}
        for k in ("pixel", "stroke", "local"):
            xa = [r[k] for r in per[a]]; xb = [r[k] for r in per[b]]
            if any(v is None for v in xa + xb): continue
            d = np.array(xa) - np.array(xb); ci = boot_ci(d)
            ci["positive_crops"] = int((d > 0).sum()); ci["per_crop"] = [float(v) for v in d]
            diffs[f"{a}-{b}"][k] = ci
    return {"set": name, "crops": specs, "effective_n": {"crops": len(specs), "segments": len({s.split(':')[0] for s in specs})},
            "bootstrap": {"resamples": B, "seed": SEED, "type": "crop-level percentile"},
            "stroke_local_source": {"full_precision": f"{FULL} for (crop, method) pairs the toolkit recomputed (equal to the records "
                                                      "at 4 decimals)", "otherwise": "stats/stroke_test.json, stats/local_stroke_test.json "
                                                      "(4 decimals, rounded half-up by the research scripts)",
                                    "full_precision_pairs": sum(1 for rows in per.values() for r in rows if r.get("full_precision"))},
            "per_crop": per, "summary": summary, "paired_differences": diffs, "negative_control_label_swap": null,
            "positive_control": "team"}


def upgrade(per):
    fp = full_precision()
    for m, rows in per.items():
        for r in rows:
            f = fp.get((r["crop"], m))
            if f: r["stroke"], r["local"], r["full_precision"] = f["stroke"], f["local"], True
    return per


def main():
    if sys.argv[1] == "--csv":
        write_csv(json.load(open(sys.argv[2])), sys.argv[3]); print("written", sys.argv[3]); return
    if sys.argv[1] == "--from-json":          # recompute summaries and pairs from an existing stats file; keeps its label-swap null
        r = json.load(open(sys.argv[2]))
        res = summarise(r["set"], r["crops"], upgrade(r["per_crop"]), r["negative_control_label_swap"])
        json.dump(res, open(sys.argv[2], "w"), indent=1)
        write_csv(res, os.path.join(os.path.dirname(sys.argv[2]) or ".", f"per_crop_{r['set']}.csv")); print("written", sys.argv[2]); return
    name, out, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
    S = json.load(open("stats/stroke_test.json")); L = json.load(open("stats/local_stroke_test.json"))
    per = {}
    for m in METHODS:
        rows = []
        for sp in specs:
            seg, crop = sp.split(":"); d = f"data/s1/{seg}/derived/{crop}"
            jp = os.path.join(d, f"judge_{m}.json")
            px = json.load(open(jp))["bot"]["auc_px"] if os.path.exists(jp) else None
            st = S.get(sp, {}).get(m, {}).get("stroke_auc")
            lo = L.get(sp, {}).get(m, {}).get("L")
            rows.append({"crop": sp, "pixel": px, "stroke": st, "local": lo})
        if any(r["pixel"] is not None for r in rows): per[m] = rows
    per = upgrade(per)

    # negative control: cross-crop label swap with the judge's own subsample rule
    null = {}
    cls = {}
    for sp in specs:
        seg, crop = sp.split(":"); d = f"data/s1/{seg}/derived/{crop}"
        cls[sp] = (np.load(os.path.join(d, "cls_text.npy")), np.load(os.path.join(d, "cls_blank.npy")))
    sub = np.random.default_rng(0).random(cls[specs[0]][0].shape) < 0.05
    for t in NULL_TAGS:
        vals = []
        for i, j in itertools.permutations(specs, 2):
            seg, crop = i.split(":"); p = f"data/s1/{seg}/derived/{crop}/s_bot_{t}.npy"
            if not os.path.exists(p): vals = None; break
            s = np.load(p).astype(np.float32)
            dd = f"data/s1/{seg}/derived/{crop}"
            mi = (np.load(f"{dd}/mask_top.npy") > 0) & (np.load(f"{dd}/mask_bot.npy") > 0)   # crop i's own judge mask
            tj, bj = cls[j]
            a = auc(s[tj & mi & sub], s[bj & mi & sub])
            if a is not None: vals.append(a)
            del s
        if vals:
            null[t] = {"pairs": len(vals), "mean": float(np.mean(vals)), "min": float(np.min(vals)), "max": float(np.max(vals)),
                       "abs_dev_from_0.5_mean": float(np.mean(np.abs(np.array(vals) - 0.5))), "values": [float(v) for v in vals]}
        print("null", t, null.get(t), flush=True)

    res = summarise(name, specs, per, null)
    json.dump(res, open(out, "w"), indent=1)
    write_csv(res, os.path.join(os.path.dirname(out) or ".", f"per_crop_{name}.csv"))
    print("written", out)


if __name__ == "__main__":
    main()
