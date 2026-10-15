"""ca step 2b: does the per-crop optimum vary with measurable crop geometry?

For each TRAINING crop: the AUC of every one of the 22 depth channels at sigma=16, the depth of
the per-face AUC peak, and the crop's physical summaries from topo_stats.json
(t_median = sheet thickness in slices, ktop/kbot median = face depth in the rendered stack,
peak_median = brightness of the sheet's bright band, valid_fraction = 1 - damage fraction,
coverage = mean ds8 mask coverage). Reports Spearman correlations across the 8 crops.
"""
import os, sys, json
import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_lib import TRAIN, auc_vec, NAMES88, cropdir, DELTAS

CACHE = "/home/user/megara/stats/explore/cache"
OUT = "/home/user/megara/stats/explore"
S16 = 3 * 22   # sigma=16 block start in the 88-feature layout


def main():
    rows = {}
    for (s, c) in TRAIN:
        z = np.load(os.path.join(CACHE, f"caB88_{s}_{c}.npz"))
        X, y = z["X"], z["y"]
        a = np.array([auc_vec(X[:, S16 + j], y) for j in range(22)])
        ts = json.load(open(cropdir(s, c) + "/topo_stats.json"))
        cov = float(np.load(cropdir(s, c) + "/ds8_m.npy").mean())
        # depth of the AUC peak on each face (argmax of |AUC-0.5| with sign of the top pick)
        top = a[:11]; bot = a[11:]
        rows[f"{s}/{c}"] = dict(
            auc_by_depth=[round(float(v), 4) for v in a],
            top_peak_delta=int(DELTAS[int(np.argmax(np.abs(top - 0.5)))]),
            bot_peak_delta=int(DELTAS[int(np.argmax(np.abs(bot - 0.5)))]),
            top_peak_auc=round(float(np.abs(top - 0.5).max() + 0.5), 4),
            bot_peak_auc=round(float(np.abs(bot - 0.5).max() + 0.5), 4),
            t_median=ts["t_median"], ktop=ts["ktop_median"], kbot=ts["kbot_median"],
            peak=ts["peak_median"], valid_fraction=ts["valid_fraction"], coverage=round(cov, 4))
        print(f"{s}/{c}: peak deltas T{rows[f'{s}/{c}']['top_peak_delta']:+d} "
              f"B{rows[f'{s}/{c}']['bot_peak_delta']:+d}  aucs "
              f"{rows[f'{s}/{c}']['top_peak_auc']:.3f}/{rows[f'{s}/{c}']['bot_peak_auc']:.3f}  "
              f"t={ts['t_median']:.1f} ktop={ts['ktop_median']:.1f} kbot={ts['kbot_median']:.1f} "
              f"peak={ts['peak_median']:.0f} valid={ts['valid_fraction']:.2f}", flush=True)

    keys = list(rows)
    tgt = {k: np.array([rows[n][k] for n in keys], float)
           for k in ("top_peak_delta", "bot_peak_delta", "top_peak_auc", "bot_peak_auc")}
    pred = {k: np.array([rows[n][k] for n in keys], float)
            for k in ("t_median", "ktop", "kbot", "peak", "valid_fraction", "coverage")}
    corr = {}
    for tk, tv in tgt.items():
        for pk, pv in pred.items():
            r, p = spearmanr(tv, pv)
            corr[f"{tk}~{pk}"] = [round(float(r), 3), round(float(p), 3)]
    print(json.dumps(corr, indent=0))
    json.dump(dict(rows=rows, spearman_n8=corr),
              open(os.path.join(OUT, "ca_step2b_geom.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
