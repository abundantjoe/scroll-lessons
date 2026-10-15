# Provenance: Project HERCULES | owner the owner | [id removed]
"""Summarise logs/sib/amx/bench_grid*.jsonl into logs/sib/amx/summary.json and markdown tables (stdout).
Speed-up = fp32 median / bf16 median at the same (mode, threads, channels_last); also vs the fp32 contiguous
baseline at the same threads. A replicate file (bench_grid_rep.jsonl), when present, is summarised the same way and
the relative difference of medians between the two passes is reported."""
import json, os, sys
R = "/home/user/dominion/logs/sib/amx"


def rows(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def key(r):
    return (r["mode"], r["dtype"], r["threads"], r["channels_last"])


def table(rs):
    d = {key(r): r for r in rs}
    out = []
    for mode in ("infer", "train"):
        for th in (1, 2, 4):
            for cl in (False, True):
                a, b = d.get((mode, "fp32", th, cl)), d.get((mode, "bf16", th, cl))
                base = d.get((mode, "fp32", th, False))
                if not (a and b):
                    continue
                out.append(dict(mode=mode, threads=th, channels_last=cl, batch=a["batch"],
                                fp32_median_s=a["median_s"], fp32_iqr_s=a["iqr_s"], fp32_peak_rss_mb=a["peak_rss_mb"],
                                bf16_median_s=b["median_s"], bf16_iqr_s=b["iqr_s"], bf16_peak_rss_mb=b["peak_rss_mb"],
                                speedup_bf16_vs_fp32=a["median_s"] / b["median_s"],
                                speedup_bf16_vs_fp32_contiguous=base["median_s"] / b["median_s"] if base else None,
                                speedup_fp32cl_vs_fp32=(base["median_s"] / a["median_s"]) if (base and cl) else None,
                                fp32_s_per_tile=a["median_s"] / a["batch"], bf16_s_per_tile=b["median_s"] / b["batch"],
                                train_loss_last_fp32=a.get("loss_last"), train_loss_last_bf16=b.get("loss_last")))
    return out


main = rows(f"{R}/bench_grid.jsonl")
rep = rows(f"{R}/bench_grid_rep.jsonl")
summ = dict(n_rows=len(main), table=table(main))
if rep:
    dm, dr = {key(r): r for r in main}, {key(r): r for r in rep}
    summ["replicate"] = dict(n_rows=len(rep), table=table(rep), median_rel_diff={
        f"{k[0]}|{k[1]}|t{k[2]}|cl{int(k[3])}": dr[k]["median_s"] / dm[k]["median_s"] - 1 for k in dr if k in dm})
json.dump(summ, open(f"{R}/summary.json", "w"), indent=1)
print("| mode | thr | CL | batch | fp32 median s (IQR) | bf16 median s (IQR) | bf16/fp32 speed-up | vs fp32 contiguous | fp32 CL gain | peak RSS fp32 / bf16 MB |")
print("|---|---|---|---|---|---|---|---|---|---|")
for t in summ["table"]:
    cl = f"{t['speedup_fp32cl_vs_fp32']:.2f}x" if t["speedup_fp32cl_vs_fp32"] else "-"
    print(f"| {t['mode']} | {t['threads']} | {'yes' if t['channels_last'] else 'no'} | {t['batch']} | {t['fp32_median_s']:.3f} ({t['fp32_iqr_s']:.3f}) | "
          f"{t['bf16_median_s']:.3f} ({t['bf16_iqr_s']:.3f}) | {t['speedup_bf16_vs_fp32']:.2f}x | {t['speedup_bf16_vs_fp32_contiguous']:.2f}x | {cl} | "
          f"{t['fp32_peak_rss_mb']:.0f} / {t['bf16_peak_rss_mb']:.0f} |")
if rep:
    v = list(summ["replicate"]["median_rel_diff"].values())
    print(f"\nreplicate pass: {len(v)} configs, median |rel diff| {sorted(abs(x) for x in v)[len(v)//2]:.3%}, max |rel diff| {max(abs(x) for x in v):.3%}")
