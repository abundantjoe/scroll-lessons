"""ca step 4: ONE held-out run on the 7 evaluation crops.

Fits the configuration selected by LOCO on the 8 TRAINING crops (and only those), applies it to the
evaluation crops, and reports ds8 pixel AUC on the pooled mask (x[22] > 0.5) alongside the pooled
baseline B88 and the comparators v1b / v2 / v3 / team measured on identical pixels.

usage: ca_step4_heldout.py <spec> [<spec> ...]
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import TRAIN, EVAL, fit_logistic, auc, pooled_map, load_crop
from ca_step3_local import build_all, SIGL

OUT = "/home/user/megara/stats/explore"


def std(M):
    return (M - M.mean(0)) / (M.std(0) + 1e-6)


def assemble(d, spec, top8):
    parts = []
    base = None
    for tok in spec.split("+"):
        if tok == "INT":
            assert base is not None
            Bm = std(d[base]); G = std(d["GEO"])
            I = np.hstack([Bm[:, top8] * G[:, [g]] for g in range(G.shape[1])])
            parts.append(std(I))
        else:
            parts.append(std(d[tok]))
            if tok != "GEO":
                base = tok
    return np.hstack(parts)


def main():
    specs = sys.argv[1:]
    assert specs, "give at least one spec"
    from ca_lib import NAMES88, auc_vec
    tr = {f"{s}/{c}": build_all(s, c) for (s, c) in TRAIN}
    A = np.zeros(88)
    for k in tr:
        X, y = tr[k]["B88"], tr[k]["y"]
        A += np.array([abs(auc_vec(X[:, j], y) - 0.5) for j in range(88)])
    top8 = np.argsort(-A)[:8]

    models = {}
    for sp in specs:
        Xo = np.concatenate([assemble(tr[k], sp, top8) for k in tr])
        yo = np.concatenate([tr[k]["y"] for k in tr])
        models[sp] = fit_logistic(Xo, yo)
        del Xo, yo
        print("fitted", sp, flush=True)

    res = {}
    for (s, c) in EVAL:
        t0 = time.time()
        d = build_all(s, c)                 # unsupervised feature build, no labels used
        row = {}
        for sp in specs:
            w, b0 = models[sp]
            row[sp] = round(auc_vec(assemble(d, sp, top8) @ w + b0, d["y"]), 4)
        # comparators on identical pixels
        x, m, t, b = load_crop(s, c)
        h8 = m.shape[0]
        for tag in ("v1b", "v2", "v3", "team"):
            p = pooled_map(s, c, tag, h8)
            row[tag] = round(auc(p, t, b), 4) if p is not None else None
        row["n_text"] = int(t.sum()); row["n_blank"] = int(b.sum())
        res[f"{s}/{c}"] = row
        print(f"{s}/{c}: " + "  ".join(f"{k} {v}" for k, v in row.items()) +
              f"  ({time.time()-t0:.0f}s)", flush=True)

    keys = [k for k in res[f"{EVAL[0][0]}/{EVAL[0][1]}"] if not k.startswith("n_")]
    res["_heldout_mean"] = {k: round(float(np.mean([res[c][k] for c in res if not c.startswith("_")
                                                    and res[c][k] is not None])), 4) for k in keys}
    print("MEAN", json.dumps(res["_heldout_mean"]))
    json.dump(res, open(os.path.join(OUT, "ca_step4_heldout.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
