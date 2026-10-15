import sys, os, json, glob
root, out = sys.argv[1], sys.argv[2]; R = {"crops": {}}
for jp in sorted(glob.glob(os.path.join(root, "derived", "*", "judge_*.json"))):
    j = json.load(open(jp)); R["crops"].setdefault(j["crop"], {})[j["tag"]] = {f: j[f] for f in ("top", "bot") if f in j}
tags = sorted({t for c in R["crops"].values() for t in c})
R["held_out_means"] = {}
for t in tags:
    for f in ("top", "bot"):
        px = [R["crops"][c][t][f]["auc_px"] for c in R["crops"] if c != "train" and t in R["crops"][c] and f in R["crops"][c][t] and R["crops"][c][t][f]["auc_px"] is not None]
        lt = [R["crops"][c][t][f]["auc_letter"] for c in R["crops"] if c != "train" and t in R["crops"][c] and f in R["crops"][c][t] and R["crops"][c][t][f]["auc_letter"] is not None]
        if px: R["held_out_means"][f"{t}_{f}"] = {"auc_px": sum(px) / len(px), "auc_letter": (sum(lt) / len(lt)) if lt else None, "n": len(px)}
json.dump(R, open(out, "w"), indent=1); print(json.dumps(R["held_out_means"], indent=1))
