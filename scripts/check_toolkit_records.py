"""Check that the inkeval toolkit reproduces the published judge records on every crop and method whose score map is on disk.

  check_toolkit_records.py <out.json> [--jobs N] <seg:crop> [<seg:crop> ...]

For each crop: the judge classes recomputed by inkeval must equal the stored cls_text/cls_blank masks; for each method map present
(s_bot_<tag>.npy, tags e v8 gpr1 v7 team): inkeval's pixel AUC must EQUAL the float in judge_<tag>.json, and inkeval's stroke AUC and
local L, rounded to 4 decimals as the research scripts stored them, must equal stats/stroke_test.json and stats/local_stroke_test.json,
with identical disk counts. Exit code 1 if any comparison fails.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inkeval import judge_classes, local_stroke_auc, pixel_auc, stroke_auc  # noqa: E402

TAGS = ["e", "v8", "gpr1", "v7", "team"]


def check_crop(sp):
    S = json.load(open("stats/stroke_test.json")); L = json.load(open("stats/local_stroke_test.json"))
    seg, crop = sp.split(":"); d = f"data/s1/{seg}/derived/{crop}"
    label = np.load(f"{d}/label.npy")
    mask = (np.load(f"{d}/mask_top.npy") > 0) & (np.load(f"{d}/mask_bot.npy") > 0)
    text, blank = judge_classes(label, mask, 2.4)
    cls_ok = bool((text == np.load(f"{d}/cls_text.npy")).all() and (blank == np.load(f"{d}/cls_blank.npy")).all())
    row, lines = {"classes_equal": cls_ok}, []
    for t in TAGS:
        p = f"{d}/s_bot_{t}.npy"
        if not os.path.exists(p):
            row[t] = "map not on disk"; continue
        s = np.load(p).astype(np.float32)
        px = pixel_auc(s, text, blank); rec_px = json.load(open(f"{d}/judge_{t}.json"))["bot"]["auc_px"]
        a, n1, n0 = stroke_auc(s, label, mask); l, ni, nb, npair = local_stroke_auc(s, label, mask)
        rs, rl = S[sp][t], L[sp][t]
        r = {"pixel": px, "pixel_record": rec_px, "pixel_equal": px == rec_px,
             "stroke": a, "stroke_record": rs["stroke_auc"], "stroke_equal_4dp": (round(a, 4), n1, n0) == (rs["stroke_auc"], rs["n_ink"], rs["n_blank"]),
             "local": l, "local_record": rl["L"], "local_equal_4dp": (round(l, 4), ni, nb, npair) == (rl["L"], rl["n_ink"], rl["n_blank"], rl["n_paired"])}
        row[t] = r
        lines.append(f"{sp:22s} {t:5s} pixel {'==' if r['pixel_equal'] else '!='} {px!r}  stroke {'OK' if r['stroke_equal_4dp'] else 'DIFF'}  "
                     f"local {'OK' if r['local_equal_4dp'] else 'DIFF'}")
    return sp, row, lines


if __name__ == "__main__":
    args = sys.argv[1:]; out = args.pop(0); jobs = 1
    if "--jobs" in args:
        i = args.index("--jobs"); jobs = int(args[i + 1]); del args[i:i + 2]
    specs = args
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as ex:
            res = list(ex.map(check_crop, specs))
    else:
        res = [check_crop(sp) for sp in specs]
    rows, bad = {}, 0
    for sp, row, lines in res:
        rows[sp] = row; print("\n".join(lines), flush=True)
        bad += not row["classes_equal"]
        bad += sum(not (v["pixel_equal"] and v["stroke_equal_4dp"] and v["local_equal_4dp"]) for v in row.values() if isinstance(v, dict))
    n = sum(isinstance(v, dict) for r in rows.values() for v in r.values())
    json.dump({"rule": "pixel AUC must be the identical float; stroke and local equal after rounding to the 4 decimals stored by the research "
                       "scripts, with identical disk counts; judge classes recomputed by inkeval must equal the stored class masks",
               "crops": specs, "methods": TAGS, "comparisons": n, "failures": bad, "rows": rows}, open(out, "w"), indent=1)
    print(f"{n} method-crop comparisons, {bad} failures"); sys.exit(1 if bad else 0)
