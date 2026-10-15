"""Per-depth, per-face AUC (text vs blank) from the pooled 19.2 um stacks: which depth carries the verified-ink contrast in each crop."""
import sys, os, numpy as np
from scipy.stats import rankdata
for d in sys.argv[1:]:
    X = np.load(os.path.join(d, "ds8_x.npy")); Y = np.load(os.path.join(d, "ds8_y.npy")); t = Y == 1; b = Y == 0
    def auc(x):
        a, c = x[t], x[b]; rk = rankdata(np.concatenate([a, c])); n1, n0 = len(a), len(c); return (rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    out = {f: [round(float(auc(X[i + 11 * fi])), 3) for i in range(11)] for fi, f in enumerate(("top", "bot"))}
    print(os.path.basename(d), "n_text", int(t.sum()), "n_blank", int(b.sum())); print("  top δ=-4..6", out["top"]); print("  bot δ=-4..6", out["bot"])
