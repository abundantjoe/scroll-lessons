"""AUDIT step 2: does the 0.65-0.68 ceiling come from label-edge slop?

(a) pixel AUC of every score map restricted to label INTERIORS (distance d inside the stroke)
    vs blank interiors (distance 0.3 mm + d from any stroke), for a ladder of d.
(b) the same for the team model, which is the empirical answer to "is the reference good enough".
(c) reference-cleaning: the negative class restricted to pixels the team model is confident are
    blank, the positive class restricted to pixels the team model is confident are ink -- this
    removes unlabelled ink and over-drawn label from the reference and shows what our AUC would
    be against a cleaner reference.  (Circular for the team tag itself; reported as such.)
(d) agreement of our scores with the team model where the label says nothing.

usage: au_step2_erosion.py <seg> <crop>
"""
import os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import au_lib as A
from scipy.stats import rankdata

seg, crop = sys.argv[1], sys.argv[2]
MARG = [0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 1.0]     # mm of erosion applied to BOTH classes
T_HI, T_LO = 0.8, 0.2                            # team-model confidence gates (bimodal at 0.13 / 0.90)
rng = np.random.default_rng(12345)
t0 = time.time()

L, text, blank, m = A.load_masks(seg, crop)
d_in = A.edt_mm(L)
d_out = A.edt_mm(~L)
team = A.load_score(seg, crop, "team")

out = {"seg": seg, "crop": crop, "pitch_um": A.PITCH,
       "n_text": int(text.sum()), "n_blank": int(blank.sum()),
       "team_mean_on_text": round(float(team[text].mean()), 4),
       "team_mean_on_blank": round(float(team[blank].mean()), 4),
       "frac_blank_team_gt_hi": round(float((team[blank] > T_HI).mean()), 4),
       "frac_text_team_lt_lo": round(float((team[text] < T_LO).mean()), 4)}

# ---------- (a)+(b) erosion ladder ----------
lad = {}
for d in MARG:
    pos = text & (d_in >= d)
    neg = blank & (d_out >= 0.3 + d)
    ent = {"n_pos": int(pos.sum()), "n_neg": int(neg.sum())}
    if ent["n_pos"] >= 200 and ent["n_neg"] >= 200:
        for tag in A.TAGS:
            s = A.load_score(seg, crop, tag)
            if s is None:
                continue
            v, n1, n0 = A.auc_masked(s, pos, neg, rng)
            ent[tag] = round(v, 4) if v is not None else None
            del s
    lad[f"{d:g}"] = ent
    print(f"  margin {d}: {ent}", flush=True)
out["erosion_ladder"] = lad

# ---------- (c) reference cleaning (team-gated classes) ----------
clean = {}
variants = {
    "raw":         (text, blank),
    "clean_blank": (text, blank & (team < T_LO)),
    "clean_text":  (text & (team > T_HI), blank),
    "clean_both":  (text & (team > T_HI), blank & (team < T_LO)),
    # the opposite experiment: the pixels the reference and the team model DISAGREE on
    "disagree":    (text & (team < T_LO), blank & (team > T_HI)),
}
for name, (pos, neg) in variants.items():
    ent = {"n_pos": int(pos.sum()), "n_neg": int(neg.sum())}
    if ent["n_pos"] >= 200 and ent["n_neg"] >= 200:
        for tag in A.TAGS:
            s = A.load_score(seg, crop, tag)
            if s is None:
                continue
            v, _, _ = A.auc_masked(s, pos, neg, rng)
            ent[tag] = round(v, 4) if v is not None else None
            del s
    clean[name] = ent
    print(f"  {name}: {ent}", flush=True)
out["reference_cleaning"] = clean

# ---------- (d) agreement with the team model where the label is silent ----------
U = m & (~L) & (d_out > 0.3)            # on-sheet, unlabelled, outside the 0.3 mm label margin
pos_u = U & (team > T_HI)               # team says ink but nobody labelled it
neg_u = U & (team < T_LO)
agree = {"n_unlabelled": int(U.sum()),
         "n_unlabelled_team_ink": int(pos_u.sum()),
         "n_unlabelled_team_blank": int(neg_u.sum())}
idx = np.flatnonzero(U.ravel())
if idx.size > 300000:
    idx = rng.choice(idx, 300000, replace=False)
tv = team.ravel()[idx].astype(np.float64)
tr = rankdata(tv)
for tag in A.TAGS:
    if tag == "team":
        continue
    s = A.load_score(seg, crop, tag)
    if s is None:
        continue
    sv = s.ravel()[idx].astype(np.float64)
    agree[f"pearson_{tag}"] = round(float(np.corrcoef(sv, tv)[0, 1]), 4)
    agree[f"spearman_{tag}"] = round(float(np.corrcoef(rankdata(sv), tr)[0, 1]), 4)
    v, _, _ = A.auc_masked(s, pos_u, neg_u, rng)
    agree[f"auc_vs_teamink_unlabelled_{tag}"] = round(v, 4) if v is not None else None
    del s, sv
out["unlabelled_agreement"] = agree
print("  unlabelled:", agree, flush=True)

A.jwrite(os.path.join(A.ROOT, f"stats/explore/au_step2_{seg}_{crop}.json"), out)
print(f"done {time.time()-t0:.0f}s", flush=True)
