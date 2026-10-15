"""C1 analysis: the pre-registered prediction, checked mechanically, and the shrinkage C1 exists to measure (RULES.md, C1 declaration).

  c1_analysis.py results/stats_evaluation7.json results/stats_confirmation.json results/c1_analysis.json

1. PREDICTION (declared 46a4bfc, verbatim): "E clears both bars on the C1 mean (pixel >= 0.80, stroke >= 0.90) and beats v7 on every
   C1 crop." "Beats v7" is checked on pixel AUC (the primary metric) and, separately, on stroke AUC; both are reported.
2. SHRINKAGE (declared: "its size IS the measurement"): C1 mean minus evaluation mean, per method and metric, with a two-sample
   crop-level percentile bootstrap (10 000 resamples, seed 0; the two crop sets are resampled independently).
3. POST-HOC, labelled as such (written after 4 of the 6 C1 pixel values had been read in the run log, and committed in d2564a7 after 5 of
   the 6 crops had been judged there): the same shrinkage for the team
   model, and the gap team - E on each set. If the team model loses as much as E, the C1 crops are harder, not E overfitted; the
   difference of the two shrinkages is the part attributable to adaptive reuse of the evaluation set (an interpretation).
"""
import json, sys
import numpy as np

B, SEED = 10000, 0
BARS = {"pixel": 0.80, "stroke": 0.90}


def per_crop(r, tag, met):
    return {x["crop"]: x[met] for x in r["per_crop"][tag] if x.get(met) is not None}


def two_sample(a, b, seed=SEED):
    """mean(b) - mean(a) with independent crop-level resampling of each set."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    ma = a[rng.integers(0, len(a), (B, len(a)))].mean(1)
    mb = b[rng.integers(0, len(b), (B, len(b)))].mean(1)
    d = mb - ma
    return {"diff": float(b.mean() - a.mean()), "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "n_eval": int(len(a)), "n_c1": int(len(b))}


def main():
    ev, c1 = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    out = {"source": [sys.argv[1], sys.argv[2]], "bootstrap": {"resamples": B, "seed": SEED, "type": "two-sample crop-level percentile"}}

    # 1. prediction
    s = c1["summary"]["e"]
    clears = {m: {"mean": s[m]["mean"], "ci95": s[m]["ci95"], "bar": BARS[m], "mean_clears": s[m]["mean"] >= BARS[m],
                  "lower_bound_clears": s[m]["ci95"][0] >= BARS[m]} for m in BARS}
    beats = {}
    for m in ("pixel", "stroke"):
        e, v = per_crop(c1, "e", m), per_crop(c1, "v7", m)
        rows = {k: {"e": e[k], "v7": v[k], "e_ahead": e[k] > v[k]} for k in e if k in v}
        beats[m] = {"per_crop": rows, "crops_e_ahead": sum(r["e_ahead"] for r in rows.values()), "n": len(rows),
                    "every_crop": all(r["e_ahead"] for r in rows.values()) and len(rows) == len(c1["crops"])}
    held = clears["pixel"]["mean_clears"] and clears["stroke"]["mean_clears"] and beats["pixel"]["every_crop"]
    out["prediction"] = {"text": "E clears both bars on the C1 mean (pixel >= 0.80, stroke >= 0.90) and beats v7 on every C1 crop.",
                         "bars": clears, "beats_v7": beats,
                         "verdict": "HELD" if held else "NOT HELD",
                         "verdict_rule": "both C1 means at or above their bars AND E above v7 on pixel AUC on every C1 crop"}

    # 2. shrinkage (declared) and 3. team-relative (post-hoc)
    shr = {}
    for tag in ("e", "v8", "gpr1", "v7", "team"):
        shr[tag] = {}
        for m in ("pixel", "stroke", "local"):
            a, b = list(per_crop(ev, tag, m).values()), list(per_crop(c1, tag, m).values())
            if a and b: shr[tag][m] = two_sample(a, b)
    out["shrinkage_c1_minus_eval"] = shr
    gap = {}
    for name, r in (("evaluation", ev), ("c1", c1)):
        gap[name] = {}
        for m in ("pixel", "stroke", "local"):
            e, t = per_crop(r, "e", m), per_crop(r, "team", m)
            d = [t[k] - e[k] for k in e if k in t]
            gap[name][m] = {"mean": float(np.mean(d)), "per_crop": d}
    out["posthoc_team_minus_e"] = gap
    out["posthoc_note"] = ("Team shrinkage and the team-E gap were written after 4 of the 6 C1 pixel values had been read in the run log and committed "
                           "(d2564a7) after 5 of the 6 crops had been judged; "
                           "they are descriptive and carry no verdict.")
    json.dump(out, open(sys.argv[3], "w"), indent=1)

    sys.path.insert(0, ".")
    from inkeval import trunc
    T = lambda x: f"{trunc(x, 3):.3f}"
    print(f"PREDICTION: {out['prediction']['verdict']}")
    for m, c in clears.items():
        print(f"  E C1 {m}: {T(c['mean'])} [{T(c['ci95'][0])}, {T(c['ci95'][1])}]  bar {c['bar']}  mean clears: {c['mean_clears']}")
    for m, b in beats.items():
        print(f"  E > v7 on {m}: {b['crops_e_ahead']}/{b['n']} crops")
    for tag, v in shr.items():
        print(f"  shrinkage {tag}: " + "; ".join(f"{m} {T(x['diff'])} [{T(x['ci95'][0])}, {T(x['ci95'][1])}]" for m, x in v.items()))
    for name, v in gap.items():
        print(f"  team - E ({name}): " + "; ".join(f"{m} {T(x['mean'])}" for m, x in v.items()))


if __name__ == "__main__":
    main()
