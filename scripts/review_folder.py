#!/usr/bin/env python
"""review_folder.py -- the team's review folder (MASTER_PROMPT_v4 5.12), built from read directories.

Scans --reads-root for read directories (each with read_stats.json as written by read_chart.py, or a flat
stats.json; both schemas in scripts/STATS_SCHEMA.md) and writes under --out (default review_sheets/):
  eligible/<scroll>__<segment>__<verdict>.png      contact sheets of reads on eligible scrolls (section 1 list)
  ineligible/<scroll>__<segment>__<verdict>.png    controls (w040, w028, anything not on the list)
  INDEX.md                                          one row per sheet, sorted by largest 0.5 cm^2 cluster (desc),
                                                    then forward - reverse (desc); numbers copied from the stats
  eligible/overlays/<scroll>__<segment>_overlay.png three panels, 1 cm bar and um/px on each:
      1. CT mid slice with purple (alpha blend) where forward > 0.5 AND forward - reverse > 0.10 (5.12) --
         labelled "DERIVED OVERLAY FOR EYES ONLY"; never a claim, never a verdict input
      2. forward - reverse at full resolution, diverging blue/white/red, symmetric limits +-0.30
      3. the forward map as stored (uint8 p*255, no stretch)
  eligible/overlays/<scroll>__<segment>_overlay.json  the numbers behind the overlay (bar px, thresholds, fractions)
Idempotent by mtime: a sheet/overlay is rebuilt only when its sources (stats, sheet png, maps, render) are newer.
--loop N re-runs every N minutes (refresh on a timer). Eligibility = 'eligible' key if the stats carry one, else
scroll on the MASTER_PROMPT_v4 section 1 list (verify_package.ELIGIBLE).
Robustness in loop mode: a read_stats.json without its .read_complete marker (read_chart.py writes the marker last) is
skipped this pass; any exception while copying/overlaying one read is printed and that read is skipped (INDEX still
written). When two reads share (scroll, segment) (other depth offset / checkpoint / order), their sheet and overlay
basenames get the remaining key fields appended so neither read overwrites the other.
Memory: the overlay holds fwd, rev, margin (float32) and three BGR panels; for a 2.4 um render (~9400^2) pass
--max-overlay-px (e.g. 3000) or expect ~2-3 GB peak.
usage: review_folder.py --reads-root reads/ [--out review_sheets] [--loop N] [--max-overlay-px 0]
"""
import argparse, datetime, json, os, shutil, sys, time
import numpy as np, cv2, tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contact_sheet as cs  # noqa: E402
from verify_package import ELIGIBLE  # noqa: E402

OVERLAY_FWD_THR, OVERLAY_MARGIN_THR = 0.5, 0.10       # 5.12: purple where forward > 0.5 AND forward - reverse > 0.10
DIVERGING_LIMIT = 0.30                                 # task spec: symmetric +-0.3 on the forward - reverse panel
PURPLE_BGR, PURPLE_ALPHA = (200, 0, 160), 0.55         # derived view for eyes only
STATS_NAMES = ("read_stats.json", "stats.json")
MARKER = ".read_complete"                              # read_chart.py writes it last; a read_stats.json without it is in progress
INDEX_COLS = ("scroll", "segment", "verdict", "eligible", "um", "fwd_mean", "rev_mean", "fwd-rev", "frac>0.5",
              "frac>0.75", "flagged 0.5cm2", "largest cluster", "flagged 1cm2", "sheet", "overlay")


def find_reads(root):
    """Directories under root holding a stats file (deepest-first order is irrelevant; sorted for determinism)."""
    out = []
    for d, _, files in os.walk(root):
        for n in STATS_NAMES:
            if n in files:
                out.append(os.path.join(d, n)); break
    return sorted(out)


def _resolve(path, read_dir):
    if not path:
        return None
    for cand in (path, os.path.join(read_dir, path), os.path.join(read_dir, os.path.basename(path))):
        if os.path.exists(cand):
            return os.path.abspath(cand)
    return path


def normalise(stats, stats_path):
    """Flat record from either schema (read_chart.py nested read_stats.json, or the flat stats.json)."""
    d = os.path.dirname(os.path.abspath(stats_path))
    if "key" in stats or "maps" in stats or "rule55" in stats:             # read_chart.py schema (UNREADABLE: key only)
        parts = (stats.get("key", "") + "||||").split("|")
        m, u = stats.get("maps", {}), stats.get("rule55", {}).get("units", {})
        h, one = u.get("0.5cm2", {}), u.get("1cm2", {})
        rec = dict(scroll=parts[0], surface=parts[1], um=stats.get("um_per_px"), verdict=stats.get("verdict"),
                   fwd_mean=m.get("fwd_mean"), rev_mean=m.get("rev_mean"), frac_gt_05=m.get("fwd_frac_gt_0p5"),
                   frac_gt_075=m.get("fwd_frac_gt_0p75"), flagged_05=h.get("n_flagged"), valid_05=h.get("n_valid"),
                   largest_cluster_05=h.get("largest_cluster"), flagged_1=one.get("n_flagged"),
                   sheet_png=stats.get("contact_sheet", {}).get("path"), forward_tif=stats.get("inputs", {}).get("forward"),
                   reverse_tif=stats.get("inputs", {}).get("reverse"), render_zarr=None if stats.get("maps_only") else stats.get("inputs", {}).get("render"),
                   key_tag="_".join(p for p in parts[2:5] if p))
    else:                                                                    # flat schema (STATS_SCHEMA.md)
        rec = {k: stats.get(k) for k in ("scroll", "surface", "verdict", "um", "fwd_mean", "rev_mean", "frac_gt_05", "frac_gt_075",
                                         "flagged_05", "valid_05", "largest_cluster_05", "flagged_1", "sheet_png", "forward_tif",
                                         "reverse_tif", "render_zarr")}
        rec["key_tag"] = stats.get("key_tag") or ""
    rec["eligible"] = bool(stats["eligible"]) if "eligible" in stats else (rec["scroll"] in ELIGIBLE)
    rec["surface"] = rec.get("surface") or os.path.basename(d)
    for k in ("sheet_png", "forward_tif", "reverse_tif", "render_zarr"):
        rec[k] = _resolve(rec.get(k), d)
    rec["stats_path"], rec["read_dir"] = os.path.abspath(stats_path), d
    rec["fwd_minus_rev"] = (None if rec["fwd_mean"] is None or rec["rev_mean"] is None else round(rec["fwd_mean"] - rec["rev_mean"], 4))
    return rec


def _safe(s):
    return "".join(c if (c.isalnum() or c in "-.") else "_" for c in str(s))


def sheet_name(rec):
    return "%s__%s%s__%s.png" % (rec["scroll"], rec["surface"], rec.get("tag", ""), _safe(rec["verdict"] or "NONE"))


def overlay_name(rec):
    return "%s__%s%s_overlay.png" % (rec["scroll"], rec["surface"], rec.get("tag", ""))


def tag_collisions(recs):
    """Reads sharing (scroll, surface) get '__<depth>_<ckpt>_<order>' (sanitised key fields) in their basenames."""
    groups = {}
    for r in recs:
        groups.setdefault((r["scroll"], r["surface"]), []).append(r)
    for g in groups.values():
        if len(g) > 1:
            for i, r in enumerate(g):
                r["tag"] = "__" + (_safe(r.get("key_tag")) if r.get("key_tag") else "read%d" % i)
            print("warning: %d reads share %s/%s; basenames suffixed with key fields" % (len(g), g[0]["scroll"], g[0]["surface"]))


def newer(dst, *srcs):
    """True if dst is missing or any existing src is newer than dst (mtime idempotence)."""
    if not os.path.exists(dst):
        return True
    t = os.path.getmtime(dst)
    return any(os.path.exists(s) and os.path.getmtime(s) > t for s in srcs if s)


def diverging_bgr(x, limit=DIVERGING_LIMIT):
    """Blue (-limit) - white (0) - red (+limit) as BGR uint8; outside the limits saturates."""
    v = np.clip(x / float(limit), -1.0, 1.0)
    g = (255 * (1 - np.abs(v))).astype(np.uint8)
    out = np.empty(x.shape + (3,), np.uint8)
    pos = v >= 0
    out[..., 0] = np.where(pos, g, 255); out[..., 1] = g; out[..., 2] = np.where(pos, 255, g)
    return out


def mid_slice(render_zarr):
    import zarr
    g = zarr.open_group(render_zarr, mode="r")
    arr = g["0"] if "0" in g else g[sorted(g.keys())[0]]
    return np.asarray(arr[arr.shape[0] // 2]), int(arr.shape[0])


def build_overlay(rec, out_png, max_px=0):
    """Three panels (CT+purple derived view | fwd-rev diverging | forward as stored); returns the numbers dict."""
    fwd = tifffile.imread(rec["forward_tif"]); rev = tifffile.imread(rec["reverse_tif"])
    fwd = fwd[0] if fwd.ndim == 3 else fwd; rev = rev[0] if rev.ndim == 3 else rev
    if rec["render_zarr"] and os.path.exists(rec["render_zarr"]):
        ct, nz = mid_slice(rec["render_zarr"])
    else:
        ct, nz = np.full(fwd.shape, 128, np.uint8), None
    if fwd.shape != rev.shape or ct.shape != fwd.shape:
        raise ValueError("shape mismatch: forward %s reverse %s render %s" % (fwd.shape, rev.shape, ct.shape))
    margin = fwd.astype(np.float32); margin /= 255.0                      # in place: one float32 copy, not three
    mask = margin > OVERLAY_FWD_THR
    margin -= rev.astype(np.float32) / 255.0
    mask &= margin > OVERLAY_MARGIN_THR
    onsheet = ct > 0
    ctb = cs.gray_to_bgr(ct)
    sel = ctb[mask].astype(np.float32)                                    # blend only the purple pixels
    ctb[mask] = (sel * (1 - PURPLE_ALPHA) + np.array(PURPLE_BGR, np.float32) * PURPLE_ALPHA).astype(np.uint8); del sel
    f = cs.downsample_factor(fwd.shape, max_px) if max_px else 1
    um = float(rec["um"])
    p1, b1 = cs.panel(cs.shown(ctb, f), "CT mid slice + purple: fwd>%.1f & fwd-rev>%.2f  DERIVED OVERLAY FOR EYES ONLY" % (OVERLAY_FWD_THR, OVERLAY_MARGIN_THR), um, f)
    p2, b2 = cs.panel(cs.shown(diverging_bgr(margin), f), "forward - reverse (full res, blue -%.2f .. red +%.2f)" % (DIVERGING_LIMIT, DIVERGING_LIMIT), um, f)
    del margin
    p3, b3 = cs.panel(cs.gray_to_bgr(cs.shown(fwd, f)), "forward (as stored, p*255)", um, f)
    title = ["%s  %s  %s   -- derived overlay for eyes only; the verdict comes from rule 5.5, never from this view" % (rec["scroll"], rec["surface"], rec["verdict"])]
    cv2.imwrite(out_png, cs.assemble([p1, p2, p3], title))
    return dict(scroll=rec["scroll"], surface=rec["surface"], verdict=rec["verdict"], um_per_px=um, map_shape=list(fwd.shape),
                n_slices=nz, shown_1_to=f, bar_px_at_map_scale=cs.bar_px(um), bar_px_in_png=dict(ct_overlay=b1, margin=b2, forward=b3),
                overlay_thresholds=dict(forward_gt=OVERLAY_FWD_THR, margin_gt=OVERLAY_MARGIN_THR), diverging_limit=DIVERGING_LIMIT,
                purple_frac_of_onsheet=round(float(mask[onsheet].mean()), 5) if onsheet.any() else None,
                purple_px=int(mask.sum()), note="derived view for eyes only", generated=datetime.datetime.now().isoformat(timespec="seconds"))


def fmt(v):
    return "-" if v is None else ("%.4f" % v if isinstance(v, float) else str(v))


def write_index(recs, out_dir):
    key = lambda r: (-(r["largest_cluster_05"] or 0), -(r["fwd_minus_rev"] if r["fwd_minus_rev"] is not None else -9))
    rows = sorted(recs, key=key)
    lines = ["# Review sheets index (MASTER_PROMPT_v4 5.12) -- generated by scripts/review_folder.py",
             "", "Sorted by largest 4-connected cluster of flagged 0.5 cm^2 units (desc), then forward - reverse mean (desc).",
             "Numbers are copied from each read's stats JSON (rule 5.5 as implemented in rule55.py). Overlays are derived views for eyes only.", "",
             "| " + " | ".join(INDEX_COLS) + " |", "|" + "---|" * len(INDEX_COLS)]
    for r in rows:
        vals = [r["scroll"], r["surface"], r["verdict"], "yes" if r["eligible"] else "no", fmt(r["um"]), fmt(r["fwd_mean"]), fmt(r["rev_mean"]),
                fmt(r["fwd_minus_rev"]), fmt(r["frac_gt_05"]), fmt(r["frac_gt_075"]), "%s/%s" % (fmt(r["flagged_05"]), fmt(r.get("valid_05"))),
                fmt(r["largest_cluster_05"]), fmt(r["flagged_1"]), r.get("sheet_rel") or "-", r.get("overlay_rel") or "-"]
        lines.append("| " + " | ".join(str(v) for v in vals) + " |")
    open(os.path.join(out_dir, "INDEX.md"), "w").write("\n".join(lines) + "\n")
    return rows


def run_once(reads_root, out_dir, max_px=0):
    for sub in ("eligible", "ineligible", os.path.join("eligible", "overlays")):
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
    recs, n_copied, n_overlays = [], 0, 0
    for sp in find_reads(reads_root):
        if os.path.basename(sp) == STATS_NAMES[0] and not os.path.exists(os.path.join(os.path.dirname(sp), MARKER)):
            print("skip %s: no %s yet (read in progress)" % (sp, MARKER)); continue
        try:
            recs.append(normalise(json.load(open(sp)), sp))
        except Exception as e:                                   # a half-written stats file: skip this pass
            print("skip %s: %s" % (sp, e))
    tag_collisions(recs)
    for rec in recs:
        try:
            sub = "eligible" if rec["eligible"] else "ineligible"
            rel = os.path.join(sub, sheet_name(rec)); dst = os.path.join(out_dir, rel)
            if rec["sheet_png"] and os.path.exists(rec["sheet_png"]):
                if newer(dst, rec["sheet_png"], rec["stats_path"]):
                    shutil.copyfile(rec["sheet_png"], dst); n_copied += 1
                rec["sheet_rel"] = rel
            if rec["eligible"] and rec["forward_tif"] and rec["reverse_tif"] and os.path.exists(rec["forward_tif"]) and os.path.exists(rec["reverse_tif"]):
                orel = os.path.join("eligible", "overlays", overlay_name(rec)); opng = os.path.join(out_dir, orel)
                if newer(opng, rec["forward_tif"], rec["reverse_tif"], rec["stats_path"], rec["render_zarr"]):
                    nums = build_overlay(rec, opng, max_px)
                    json.dump(nums, open(opng[:-4] + ".json", "w"), indent=1); n_overlays += 1
                rec["overlay_rel"] = orel
        except Exception as e:                                   # one bad read (half-written tif, shape mismatch) never kills the loop
            print("skip %s: %s" % (rec["stats_path"], e)); rec["overlay_rel"] = None
    rows = write_index(recs, out_dir)
    summary = dict(reads_root=os.path.abspath(reads_root), n_reads=len(recs),
                   n_eligible=sum(r["eligible"] for r in recs), sheets_copied=n_copied, overlays_built=n_overlays,
                   order=[[r["scroll"], r["surface"], r["verdict"], r["largest_cluster_05"], r["fwd_minus_rev"]] for r in rows])
    json.dump(summary, open(os.path.join(out_dir, "review_index.json"), "w"), indent=1)
    open(os.path.join(out_dir, ".review_complete"), "w").write(
        datetime.datetime.now().isoformat(timespec="seconds") + "\n")   # local marker only; gitignored
    print("review: %d reads (%d eligible), %d sheets copied, %d overlays built -> %s" % (len(recs), summary["n_eligible"], n_copied, n_overlays, out_dir))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reads-root", required=True, help="directory tree containing read directories (read_stats.json / stats.json)")
    ap.add_argument("--out", default="review_sheets")
    ap.add_argument("--loop", type=float, default=0, help="re-run every N minutes (0 = once)")
    ap.add_argument("--max-overlay-px", type=int, default=0, help="0 = full resolution (spec); else integer-factor area resample, factor stated on the panel")
    a = ap.parse_args(argv)
    while True:
        run_once(a.reads_root, a.out, a.max_overlay_px)
        if a.loop <= 0:
            return 0
        time.sleep(a.loop * 60)


if __name__ == "__main__":
    sys.exit(main())
