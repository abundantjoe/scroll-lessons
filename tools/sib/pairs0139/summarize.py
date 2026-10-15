# Provenance: Project HERCULES | owner the owner | [id removed]
"""Summarise the PHerc0139 D2 pair build (numbers only) into logs/sib/pairs0139/:
  pairs_registry.jsonl   one row per KEPT pair (segment, canvas and 3-D coordinates, gate numbers, label counts,
                         label source, shard file + index + sha256, image / label sha256)
  candidates.csv.gz      one row per candidate tile (kept or not): the gate numbers and reported controls
  summary.json           per-segment counts, gate distributions, controls, label statistics, LABEL-EQUIV vs the
                         official human labels on kept tiles, shard list with sha256
Every shard is re-read and each tile's image / label sha256 is re-checked against the registry."""
import csv, gzip, hashlib, json, os
import numpy as np

OUT = "/work/p139/out"
LOG = "logs/sib/pairs0139"
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"


def pct(a, q=(5, 25, 50, 75, 95)):
    a = np.asarray([x for x in a if x is not None and np.isfinite(x)], float)
    return {f"p{k}": round(float(np.percentile(a, k)), 4) for k in q} if a.size else None


def kappa(tp, fp, fn, tn):
    n = tp + fp + fn + tn
    if n == 0:
        return None
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n / n
    return (po - pe) / (1 - pe) if pe < 1 else None


def main():
    order = json.load(open(f"{OUT}/order.json"))
    segs = [r for r in order["order"] if os.path.exists(f"{OUT}/registry/{r['short']}.summary.json")]
    kept_rows, per_seg, cand_rows = [], {}, []
    for o in segs:
        sh = o["short"]
        rows = [json.loads(l) for l in open(f"{OUT}/registry/{sh}.jsonl")]
        summ = json.load(open(f"{OUT}/registry/{sh}.summary.json"))
        k = [r for r in rows if r["kept"]]
        kept_rows += k
        ctl = [r["reported_controls"] for r in rows if r.get("reported_controls")]
        per_seg[sh] = dict(rank=o["rank"], tier=o["tier"], kappa_map_vs_human=o["kappa"], crispness=o["crispness"],
                           counts={x: summ[x] for x in ("tiles_grid", "fail_render_valid", "fail_rule_s", "fail_valid24",
                                                        "candidates", "pass_ncc", "pass_win", "kept")},
                           seconds=summ["seconds"], render_seconds=summ["render"]["seconds"],
                           sv24_bytes=summ["sv_bytes"],
                           ncc0=pct([r["ncc0"] for r in rows]),
                           tile_ncc_at_best_int_shift=pct([r["reported_tile_ncc_at_best_int_shift"] for r in rows]),
                           window_dy_median=float(np.nanmedian([w["dy"] if w["dy"] is not None else np.nan for r in rows for w in r["windows"]])),
                           window_dx_median=float(np.nanmedian([w["dx"] if w["dx"] is not None else np.nan for r in rows for w in r["windows"]])),
                           n_aligned_hist=np.bincount([r["n_aligned"] for r in rows], minlength=10).tolist(),
                           controls=dict(n=len(ctl),
                                         mismatch_ncc0=pct([c.get("mismatch_ncc0") for c in ctl]),
                                         mismatch_pass_windows=int(sum(c.get("mismatch_n_aligned", 0) >= 7 for c in ctl)),
                                         plain_ncc0=pct([c.get("plain_ncc0") for c in ctl]),
                                         plain_pass_windows=int(sum(c.get("plain_n_aligned", 0) >= 7 for c in ctl)),
                                         plain_pass_both=int(sum(c.get("plain_n_aligned", 0) >= 7 and (c.get("plain_ncc0") or 0) >= 0.8 for c in ctl))),
                           tags_kept=sorted({t for r in k for t in r["tags"]}),
                           kept_with_tags=int(sum(bool(r["tags"]) for r in k)))
        for r in rows:
            c = r.get("reported_controls") or {}
            cand_rows.append([r["tile_id"], sh, r["canvas9_y0"], r["canvas9_x0"], r["ncc0"], r["n_aligned"],
                              int(r["pass_ncc"]), int(r["pass_windows"]), int(r["kept"]),
                              *r["reported_tile_best_int_shift"], r["reported_tile_ncc_at_best_int_shift"],
                              r["map3d_err_vox"]["median"], r["map3d_err_vox"]["max"], r["ink_px"], r["blank_px"],
                              r["ignored_px"], c.get("mismatch_ncc0"), c.get("mismatch_n_aligned"), c.get("plain_ncc0"),
                              c.get("plain_n_aligned"), "|".join(r["tags"])])
    # shards: verify
    shards = {}
    lab = dict(ink=0, blank=0, ignored=0); hum = dict(tp=0, fp=0, fn=0, tn=0)
    by_shard = {}
    for r in kept_rows:
        by_shard.setdefault(r["shard"], []).append(r)
    for name, rs in sorted(by_shard.items()):
        p = f"{OUT}/shards/{name}"
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        assert h == rs[0]["shard_sha256"], name
        z = np.load(p)
        for r in rs:
            i = r["shard_index"]
            assert str(z["tile_id"][i]) == r["tile_id"]
            assert hashlib.sha256(z["images"][i].tobytes()).hexdigest() == r["image_sha256"]
            assert hashlib.sha256(z["label"][i].tobytes()).hexdigest() == r["label_sha256"]
        L = z["label"]; Hm = z["human"]
        lab["ink"] += int((L == 1).sum()); lab["blank"] += int((L == 0).sum()); lab["ignored"] += int((L == 255).sum())
        both = (L != 255) & (Hm != 255)
        hum["tp"] += int((both & (L == 1) & (Hm == 1)).sum()); hum["fp"] += int((both & (L == 1) & (Hm == 0)).sum())
        hum["fn"] += int((both & (L == 0) & (Hm == 1)).sum()); hum["tn"] += int((both & (L == 0) & (Hm == 0)).sum())
        shards[name] = dict(n=len(rs), bytes=os.path.getsize(p), sha256=h, shapes={k: list(z[k].shape) for k in z.files})
    n_both = sum(hum.values())
    label_equiv = dict(hum, n_both=n_both, agreement=(hum["tp"] + hum["tn"]) / n_both if n_both else None,
                       kappa=kappa(hum["tp"], hum["fp"], hum["fn"], hum["tn"]),
                       note="kept tiles only; ink-map label (>=150 / <=100) vs official 2.399 um human label set 20260918 "
                            "(all 16 sub-samples supervised; ink if >= half), pixels where both are defined")
    with open(f"{LOG}/pairs_registry.jsonl", "w") as f:
        for r in kept_rows:
            f.write(json.dumps(r) + "\n")
    with gzip.open(f"{LOG}/candidates.csv.gz", "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tile_id", "segment", "canvas9_y0", "canvas9_x0", "ncc0", "n_aligned", "pass_ncc", "pass_windows",
                    "kept", "tile_best_dy", "tile_best_dx", "tile_ncc_at_best_int_shift", "map3d_err_median",
                    "map3d_err_max", "ink_px", "blank_px", "ignored_px", "ctl_mismatch_ncc0", "ctl_mismatch_n_aligned",
                    "ctl_plain_ncc0", "ctl_plain_n_aligned", "tags"])
        w.writerows(cand_rows)
    tot = {k: sum(s["counts"][k] for s in per_seg.values()) for k in next(iter(per_seg.values()))["counts"]}
    out = dict(provenance=PROV, task="pairs0139", n_kept=len(kept_rows), totals=tot, segments=per_seg,
               labels_kept=lab, label_equiv_kept=label_equiv, shards=shards,
               kept_ncc0=pct([r["ncc0"] for r in kept_rows]),
               kept_map3d_err_max=pct([r["map3d_err_vox"]["max"] for r in kept_rows]),
               kept_ink_frac=pct([r["ink_px"] / (128 * 128) for r in kept_rows]),
               kept_tiles_with_ink_ge_2pct=int(sum(r["ink_px"] >= 0.02 * 128 * 128 for r in kept_rows)),
               kept_with_readcal_probe_tags=int(sum(bool(r["tags"]) for r in kept_rows)),
               order_file=json.load(open(f"{OUT}/order.json")))
    json.dump(out, open(f"{LOG}/summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("segments", "shards", "order_file")}, indent=1))


if __name__ == "__main__":
    main()
