#!/usr/bin/env python
"""map_integrity.py -- refuse a pair of prediction maps that is incomplete (regions left at 0).

Found on 2026-09-19: `gates/rdepth/high_reverse.tif` is exactly 25 % non-zero -- one quadrant -- while its own
forward map `high.tif` is 100 % non-zero. It was scored as if complete, so the three quarters with no prediction
were averaged in as if the model had answered zero there (the cause of the gap is unproven). That gave mean_on_ink 0.1122, a margin of
+0.60594 and an ADMITTED verdict on R-DEPTH, every one of them an artefact.

FIRST ATTEMPT AT THIS CHECK WAS WRONG and is recorded so it is not repeated: an absolute bar on the non-zero
fraction flagged 19 perfectly good corpus maps. Our surface renders are AUTO-CROPPED around an irregular surface,
so tiles that hold no surface are never written and a non-zero fraction of 0.60-0.84 is normal there; only the
full-rectangle control renders sit at 1.00. The bar has to be RELATIVE to what that read's own render covers.

Two relative tests, both on data we always have:
  PAIR      the forward and reverse maps of one read are produced by the same tiling over the same render, so their
            non-zero footprints must agree. |nz(fwd) - nz(rev)| > --pair-tol (default 0.02) means one of them is
            incomplete. This needs nothing but the two maps and works after the render has been pruned.
  COVERAGE  where the render is still on disk, every on-sheet pixel must be non-zero:
            mean(map > 0 over the on-sheet mask) >= --min-coverage (default 0.99).
  STALE     one map left over from an earlier, killed run, paired with a fresh one. Added 2026-09-19 after resuming
            R-CREST-POWER found a forward map from the previous day's killed attempt in the read directory.

            THE FIRST VERSION OF THIS TEST WAS WRONG, in the same way the non-zero bar above was wrong, and is
            recorded so the mistake is not made a third time: it used an ABSOLUTE bar (mtime skew > 1 h) on the
            assumption that `--direction both` writes the two maps together. It does not -- it runs forward, then
            reverse, so the two mtimes are separated by one whole inference pass. On four sound pairs the measured
            skew was 3705-6806 s against recorded inference times of 7985-13108 s: a ratio of 0.46-0.52, i.e.
            exactly half, which is what sequential writing means. All four were false positives.

            The test is therefore RELATIVE to the read's own cost: the skew may not exceed that read's total
            inference time (`records/throughput.jsonl`, `s_infer`, matched by ledger key), since two maps produced by
            one call cannot be further apart than the call took. A read with no throughput record is NOT tested --
            the check is skipped rather than guessed.

            It is an AUDIT flag, not a refusal: read_chart.py is unchanged, because a leftover that passes PAIR and
            COVERAGE is genuinely equivalent to a fresh map and refusing it would discard sound work.

usage: map_integrity.py --pair <forward.tif> <reverse.tif> [--render-dir <dir with render.zarr>] [--json out.json]
       map_integrity.py [--json out.json]        (audits every pair under $HERCULES_DATA)
Exit code 1 when any pair is SUSPECT, 0 when all are sound.
"""
import argparse, glob, json, os, sys
import numpy as np, tifffile

PAIR_TOL, MIN_COVERAGE, SKEW_SLACK_S = 0.02, 0.99, 600.0


def nz(path):
    a = tifffile.imread(path)
    return float((a > 0).mean()), a


def onsheet_of(render_dir):
    import zarr
    g = zarr.open_group(os.path.join(render_dir, "render.zarr"), mode="r")
    arr = g["0"] if "0" in g else g[sorted(g.keys())[0]]
    ct = np.asarray(arr[arr.shape[0] // 2])
    return ct > 0


def infer_seconds(read_dir, throughput=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records", "throughput.jsonl")):
    """That read's own total inference time, from its ledger key in throughput.jsonl; None if unrecorded."""
    try:
        key = json.load(open(os.path.join(read_dir, "read_stats.json")))["key"]
    except Exception:
        return None
    best = None
    try:
        for line in open(throughput):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("key") == key and d.get("s_infer"):
                best = max(best or 0.0, float(d["s_infer"]))
    except OSError:
        return None
    return best


def check_pair(fwd_path, rev_path, pair_tol=PAIR_TOL, min_coverage=MIN_COVERAGE, render_dir=None,
               skew_slack_s=SKEW_SLACK_S, infer_s=None):
    out = dict(forward=fwd_path, reverse=rev_path, problems=[])
    try:
        nf, af = nz(fwd_path)
        nr, ar = nz(rev_path)
    except Exception as e:
        out["problems"].append("unreadable: %s" % e); return out
    out["nonzero_forward"], out["nonzero_reverse"] = round(nf, 6), round(nr, 6)
    if af.shape != ar.shape:
        out["problems"].append("shape mismatch %s vs %s" % (af.shape, ar.shape))
    elif abs(nf - nr) > pair_tol:
        out["problems"].append("PAIR: non-zero footprints differ by %.4f (> %.2f) - one map is incomplete"
                               % (abs(nf - nr), pair_tol))
    try:
        skew = abs(os.path.getmtime(fwd_path) - os.path.getmtime(rev_path))
        out["mtime_skew_s"] = round(skew, 1)
        if infer_s is None:
            infer_s = infer_seconds(os.path.dirname(fwd_path))
        out["infer_s"] = infer_s
        if infer_s and skew > infer_s + skew_slack_s:
            out["problems"].append("STALE: the two maps were written %.0f s apart, more than the %.0f s the whole "
                                   "read's inference took - one is left over from an earlier run"
                                   % (skew, infer_s))
    except OSError as e:
        out["mtime_error"] = str(e)
    if render_dir and os.path.isdir(os.path.join(render_dir, "render.zarr")):
        try:
            m = onsheet_of(render_dir)
            if m.shape == af.shape:
                cf, cr = float((af[m] > 0).mean()), float((ar[m] > 0).mean())
                out["coverage_forward"], out["coverage_reverse"] = round(cf, 6), round(cr, 6)
                for name, c in (("forward", cf), ("reverse", cr)):
                    if c < min_coverage:
                        out["problems"].append("COVERAGE: %s is non-zero on only %.4f of the on-sheet mask" % (name, c))
        except Exception as e:
            out["coverage_error"] = str(e)
    return out


def pairs_on_disk(D):
    found = []
    for f in glob.glob(os.path.join(D, "patches", "*", "*", "read_*", "*.tif")):
        if f.endswith("_reverse.tif"):
            continue
        r = f[:-4] + "_reverse.tif"
        if os.path.exists(r):
            found.append((f, r, os.path.dirname(os.path.dirname(f))))
    for base, tag in ((os.path.join(D, "gates", "gateB"), "render_plain"), (os.path.join(D, "gates", "gateB"), "render_tta"),
                      (os.path.join(D, "gates", "rdepth"), "low"), (os.path.join(D, "gates", "rdepth"), "high")):
        f, r = os.path.join(base, tag + ".tif"), os.path.join(base, tag + "_reverse.tif")
        if os.path.exists(f) and os.path.exists(r):
            found.append((f, r, os.path.join(D, "gates", "gateB")))
    for tag in ("w040_full_plain",):
        f, r = os.path.join(D, "gates", "gateA", tag + ".tif"), os.path.join(D, "gates", "gateA", tag + "_reverse.tif")
        if os.path.exists(f) and os.path.exists(r):
            found.append((f, r, None))
    return sorted(set(found))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair-tol", type=float, default=PAIR_TOL)
    ap.add_argument("--min-coverage", type=float, default=MIN_COVERAGE)
    ap.add_argument("--skew-slack", type=float, default=SKEW_SLACK_S)
    ap.add_argument("--json")
    ap.add_argument("--pair", nargs=2, metavar=("FORWARD_TIF", "REVERSE_TIF"),
                    help="check this one forward/reverse pair instead of scanning $HERCULES_DATA")
    ap.add_argument("--render-dir", help="with --pair: directory holding render.zarr, enables the COVERAGE test")
    a = ap.parse_args(argv)
    if a.pair:
        x = check_pair(a.pair[0], a.pair[1], a.pair_tol, a.min_coverage, a.render_dir, a.skew_slack)
        print(json.dumps({k: v for k, v in x.items() if k != "problems"}))
        print("SUSPECT" if x["problems"] else "SOUND", *x["problems"], sep="\n  ")
        if a.json:
            json.dump(x, open(a.json, "w"), indent=1)
        return 1 if x["problems"] else 0
    D = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")
    rows = [check_pair(f, r, a.pair_tol, a.min_coverage, rd, a.skew_slack) for f, r, rd in pairs_on_disk(D)]
    bad = [x for x in rows if x["problems"]]
    print("checked %d forward/reverse pairs; %d sound, %d SUSPECT" % (len(rows), len(rows) - len(bad), len(bad)))
    for x in bad:
        print("  SUSPECT %s" % x["forward"].replace(D + "/", ""))
        for p in x["problems"]:
            print("          %s" % p)
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)   # a bare file name has no directory part
        json.dump(dict(pair_tol=a.pair_tol, min_coverage=a.min_coverage, skew_slack_s=a.skew_slack,
                       pairs=rows, suspect=bad), open(a.json, "w"), indent=1)
        print("wrote %s" % a.json)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
