"""edgeshape step 1 (TRAINING crops only): is there ink information in the depth-profile SHAPE?

(a) single-feature pixel AUC of every shape descriptor, per sigma, per training crop;
(b) geometry of the ink direction in the 22-d standardised profile space: its alignment with the
    dominant common-brightness mode (PC1) and the AUC of the component orthogonal to it.
"""
import os, sys, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import es_lib as E

OUT = "/home/user/megara/stats/explore/es_step1_diag.json"
SIGS = [0, 4, 8, 16]
rng = np.random.default_rng(0)
res = {}
t0 = time.time()

for seg, crop in E.TRAIN:
    x, m, t, b = E.load_crop(seg, crop)
    key = f"{seg}/{crop}"
    ent = {"n_text": int(t.sum()), "n_blank": int(b.sum()), "mask_frac": float(m.mean())}
    for sg in SIGS:
        groups = E.build_groups(x, m, sg)
        aucs = {}
        for gname, (F, names) in groups.items():
            for i, nm in enumerate(names):
                aucs[nm] = round(E.auc(F[i], t, b), 4)
        ent[f"auc_s{sg}"] = aucs
        # ---- profile-space geometry on the CH22 features ----
        Q = groups["CH22"][0]
        sel = t | b
        V = Q[:, sel].T.astype(np.float64)                 # n x 22
        y = t[sel]
        mu = V.mean(0); sd = V.std(0) + 1e-9
        Z = (V - mu) / sd
        C = np.cov(Z.T)
        w_, P = np.linalg.eigh(C)
        order = np.argsort(w_)[::-1]
        w_ = w_[order]; P = P[:, order]
        d = Z[y].mean(0) - Z[~y].mean(0)
        dn = d / (np.linalg.norm(d) + 1e-12)
        cos1 = float(abs(dn @ P[:, 0]))
        frac_top3 = float(sum((dn @ P[:, k]) ** 2 for k in range(3)))
        d_orth = dn - (dn @ P[:, 0]) * P[:, 0]
        d_orth /= (np.linalg.norm(d_orth) + 1e-12)
        sc_d = np.zeros(t.shape, np.float32); sc_d[sel] = (Z @ dn).astype(np.float32)
        sc_o = np.zeros(t.shape, np.float32); sc_o[sel] = (Z @ d_orth).astype(np.float32)
        sc_p = np.zeros(t.shape, np.float32); sc_p[sel] = (Z @ P[:, 0]).astype(np.float32)
        # in-crop LDA (shrinkage) - diagnostic only, never used as a score
        Cs = C + 0.1 * np.trace(C) / 22 * np.eye(22)
        wl = np.linalg.solve(Cs, d); wl /= np.linalg.norm(wl)
        sc_l = np.zeros(t.shape, np.float32); sc_l[sel] = (Z @ wl).astype(np.float32)
        ent[f"geom_s{sg}"] = {
            "evr1": round(float(w_[0] / w_.sum()), 4),
            "evr_top3": round(float(w_[:3].sum() / w_.sum()), 4),
            "cos_delta_pc1": round(cos1, 4),
            "frac_delta_in_top3pc": round(frac_top3, 4),
            "auc_delta": round(E.auc(sc_d, t, b), 4),
            "auc_delta_orth_pc1": round(E.auc(sc_o, t, b), 4),
            "auc_pc1": round(E.auc(sc_p, t, b), 4),
            "auc_lda_incrop": round(E.auc(sc_l, t, b), 4),
            "delta": [round(v, 4) for v in d],
            "pc1": [round(v, 4) for v in P[:, 0]],
        }
        del groups, Q, V, Z
    res[key] = ent
    print(f"{key} done {time.time()-t0:.0f}s", flush=True)

# means over training crops
names = sorted(res[f"{E.TRAIN[0][0]}/{E.TRAIN[0][1]}"]["auc_s0"].keys())
summ = {}
for sg in SIGS:
    summ[f"mean_auc_s{sg}"] = {n: round(float(np.mean([res[k][f"auc_s{sg}"][n] for k in res])), 4) for n in names}
    summ[f"mean_geom_s{sg}"] = {g: round(float(np.mean([res[k][f"geom_s{sg}"][g] for k in res])), 4)
                                for g in ("cos_delta_pc1", "frac_delta_in_top3pc", "auc_delta",
                                          "auc_delta_orth_pc1", "auc_pc1", "auc_lda_incrop", "evr1")}
res["_summary"] = summ
json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
for sg in SIGS:
    s = summ[f"mean_auc_s{sg}"]
    top = sorted(s.items(), key=lambda kv: -abs(kv[1] - 0.5))[:12]
    print(f"sigma {sg}: " + "  ".join(f"{k} {v}" for k, v in top))
    print(f"   geom {summ[f'mean_geom_s{sg}']}")
