"""Post-hoc decomposition D3 (RULES.md): how much of E's gain is ensembling and how much is smoothing?

Variants on each evaluation crop, all judged with the published rules (inkeval = exact ports of the judge, stroke and local tests):
  v8, gpr1                  as published (upsampled from 19.2 um: v8 bilinear, scripts/s1_v5.py:70; GP-R1 nearest-neighbour,
                            scripts/gpr.py:159)
  v8_s, gpr1_s              each alone, rank-normalised and smoothed 0.08 mm (what E does, minus the second model)
  mean_nos                  rank-mean of v8 and GP-R1 with NO smoothing
  e                         as published (rank-mean, smoothed 0.08 mm)
  d3_decompose.py <out.json> <seg:crop> ...
  d3_decompose.py <out.json> --from-json      (statistics only, from the per-crop values already in <out.json>)
"""
import json, sys
import numpy as np
sys.path.insert(0, ".")
from inkeval import local_stroke_auc, paired_bootstrap, bootstrap_ci, pixel_auc, rank_mean, stroke_auc

out, specs = sys.argv[1], sys.argv[2:]
rows = {}
if specs == ["--from-json"]:      # recompute the statistics from the per-crop values already in <out>, without reading any map
    rows = json.load(open(out))["per_crop"]; specs = list(rows)
for sp in ([] if rows else specs):
    seg, crop = sp.split(":"); d = f"data/s1/{seg}/derived/{crop}"
    mask = (np.load(f"{d}/mask_top.npy") > 0) & (np.load(f"{d}/mask_bot.npy") > 0)
    label = np.load(f"{d}/label.npy"); text = np.load(f"{d}/cls_text.npy"); blank = np.load(f"{d}/cls_blank.npy")
    v8 = np.load(f"{d}/s_bot_v8.npy"); g = np.load(f"{d}/s_bot_gpr1.npy"); e = np.load(f"{d}/s_bot_e.npy")
    maps = {"v8": v8, "gpr1": g, "v8_s": rank_mean([v8], mask, 0.08), "gpr1_s": rank_mean([g], mask, 0.08),
            "mean_nos": rank_mean([v8, g], mask, 0.0), "e": e}
    rows[sp] = {}
    for k, m in maps.items():
        m = m.astype(np.float32)
        st = stroke_auc(m, label, mask)[0]; lo = local_stroke_auc(m, label, mask)[0]
        rows[sp][k] = {"pixel": pixel_auc(m, text, blank), "stroke": st, "local": lo}
        print(sp, k, {kk: round(v, 4) for kk, v in rows[sp][k].items()}, flush=True)

keys = ["v8", "gpr1", "v8_s", "gpr1_s", "mean_nos", "e"]
summary = {k: {met: bootstrap_ci([rows[s][k][met] for s in specs]) for met in ("pixel", "stroke", "local")} for k in keys}
pairs = [("e", "v8"), ("v8_s", "v8"), ("gpr1_s", "gpr1"), ("mean_nos", "v8"), ("e", "mean_nos"), ("e", "v8_s"),
         ("gpr1_s", "v8_s")]                                   # like-for-like architecture comparison (both smoothed)
diffs = {f"{a}-{b}": {met: paired_bootstrap([rows[s][a][met] for s in specs], [rows[s][b][met] for s in specs])
                      for met in ("pixel", "stroke", "local")} for a, b in pairs}
json.dump({"status": "post-hoc exploratory (declared after E's result; see RULES.md D3)", "crops": specs, "per_crop": rows,
           "summary": summary, "paired_differences": diffs}, open(out, "w"), indent=1)
print("written", out)
