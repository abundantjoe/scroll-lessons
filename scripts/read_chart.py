#!/usr/bin/env python
"""read_chart.py -- the read step (MASTER_PROMPT_v4 5.10) on EXISTING model output: it never runs the model.

Inputs: the render zarr (group with array "0", axes z y x, uint8) or, with --maps-only, an on-sheet mask image
(tif/png/npy, > 0 = on-sheet); the forward and reverse TIFFs as written by 5.1 (uint8 = p * 255, never resampled).
Steps (all constants from MASTER_PROMPT_v4 5.5 / 5.10 and RULES.md R-5.5):
  1. on-sheet = CT mid slice > 0; assert >= 0.5 cm^2 on-sheet and on-sheet intensity std > 5, else UNREADABLE
     (stats JSON + ledger line are still written, message on stderr, exit code 2).
  2. per-slice mean profile over on-sheet pixels and the crest slice (argmax).
  3. on-sheet forward / reverse means, fractions > 0.5 and > 0.75, connected regions > 0.5 mm^2 at forward > 0.5
     (count, largest in mm^2), forward - reverse mean.
  4. rule 5.5 at 0.5 and 1 cm^2 (rule55.py) and the verdict.
  5. "bright ink visible in the render" (page item 7): fraction of on-sheet CT-mid pixels above the 99.5th percentile
     that lie in elongated connected marks 2-4 mm long (8-connected; long axis 2-4 mm and >= 2x the short axis, an
     implementation decision, recorded in the JSON); flagged for a human look if > 1 %.
  6. contact sheet: CT mid | forward as stored | reverse as stored | forward - reverse per unit, flagged units circled;
     1 cm bar and um/px on every panel; verdict in the title. Bar lengths are recorded in the JSON.
  7. one line appended to the Reads table of LEDGER.md; a duplicate key is refused unless --reason is given.
Idempotent: <out>/.read_complete skips everything (--force re-runs and re-appends only with --reason).
usage: read_chart.py <render.zarr|mask> <forward.tif> <reverse.tif> --um <um> --out <dir>
                     --key '<scroll>|<surface>|<depth offset>|<ckpt+TTA>|both' --ledger read/LEDGER.md [--reason ...]
                     [--maps-only] [--max-panel-px 1000] [--force]
"""
import argparse, datetime, json, os, sys
import numpy as np, tifffile
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55, contact_sheet as cs  # noqa: E402

MIN_ONSHEET_CM2, MIN_ONSHEET_STD = 0.5, 5.0            # 5.10 assertions
# Truncated-map guard (added 2026-09-19 after an inference exited 0 with a reverse map non-zero on only one quadrant).
# These are integrity bars on the FILES, not thresholds on the data: they gate nothing scientific and no result
# depends on their value. See scripts/map_integrity.py for the same two tests applied across the whole corpus.
MAP_PAIR_TOL, MAP_MIN_COVERAGE = 0.02, 0.99
REGION_THR, REGION_MIN_MM2 = 0.5, 0.5                  # connected regions at forward > 0.5, > 0.5 mm^2
BRIGHT_PCT, BRIGHT_LEN_MM, BRIGHT_ELONG, BRIGHT_FLAG_FRAC = 99.5, (2.0, 4.0), 2.0, 0.01
SEG = np.sqrt(12.0)                                    # length of a uniform segment from its std
MARKER, STATS, SHEET = ".read_complete", "read_stats.json", "contact_sheet.png"
LEDGER_HEADER = "| date | key | fwd mean | rev mean | fwd>0.5 | fwd>0.75 | flagged 0.5 cm² | largest cluster | verdict | sheet |"


def load_map(path):
    a = tifffile.imread(path)
    if a.ndim == 3:
        a = a[0]
    if a.dtype != np.uint8:
        raise SystemExit("%s: expected a uint8 map (p * 255), got %s" % (path, a.dtype))
    return a


def load_mask_image(path):
    if path.endswith(".npy"):
        m = np.load(path)
    else:
        m = tifffile.imread(path) if path.lower().endswith((".tif", ".tiff")) else __import__("cv2").imread(path, 0)
    return np.asarray(m)


def load_mask(path):
    return load_mask_image(path) > 0


def mask_panel(img):
    """(image shown in the first contact-sheet panel, its title) in --maps-only mode. A greyscale CT slice passed as
    the mask (> 0 = on-sheet) is shown as the CT; a binary mask is shown as what it is. Display only: no statistic,
    no assertion and no verdict reads this."""
    if img.dtype == np.uint8 and np.unique(img[::7, ::7]).size > 2:
        return img, "CT mid slice (given as the mask)"
    return ((img > 0) * 255).astype(np.uint8), "on-sheet mask (no CT given)"


def open_render(path):
    import zarr
    g = zarr.open_group(path, mode="r")
    arr = g["0"] if "0" in g else g[sorted(g.keys())[0]]
    if arr.ndim != 3:
        raise SystemExit("%s: expected a z y x array, got shape %s" % (path, arr.shape))
    return arr


CREST_MIN_RATIO = 1.20      # RULES R-CREST: max/min of the per-slice on-sheet mean; controls w040 1.76, w028 1.37
CREST_CENTRAL = (0.25, 0.75)  # crest slice must lie within the central half of the stack (w040 12/28, w028 10/21)


def crest_check(profile):
    """RULES R-CREST: a render sits on a sheet only if its per-slice on-sheet mean has a clear crest near the middle.
    Returns a dict with ratio, crest slice, bounds and pass flag; a flat profile (surface cutting through solid
    material, or through air) fails and the read is VOID: it can never be BLANK nor a candidate."""
    n = len(profile)
    lo, hi = max(min(profile), 1e-6), max(profile)
    crest = int(np.nanargmax(profile))
    lo_i, hi_i = int(np.floor(CREST_CENTRAL[0] * (n - 1))), int(np.ceil(CREST_CENTRAL[1] * (n - 1)))
    ratio = hi / lo
    ok = bool(ratio >= CREST_MIN_RATIO and lo_i <= crest <= hi_i)
    return dict(ratio=round(ratio, 3), crest_slice=crest, central_bounds=[lo_i, hi_i], min_ratio=CREST_MIN_RATIO,
                passed=ok, reason=None if ok else "render not centred on a sheet: crest ratio %.2f (bar >= %.2f), crest slice %d (central bounds %d..%d)" % (ratio, CREST_MIN_RATIO, crest, lo_i, hi_i))


def slice_profile(arr, onsheet):
    """Mean of every slice over on-sheet pixels (one slice in memory at a time) and the crest slice."""
    prof = []
    n = float(onsheet.sum())
    for z in range(arr.shape[0]):
        prof.append(float(np.asarray(arr[z])[onsheet].sum()) / n if n else float("nan"))
    return prof, int(np.nanargmax(prof)) if prof else None


def map_stats(forward, reverse, onsheet, um):
    f = forward[onsheet].astype(np.float32) / 255.0
    r = reverse[onsheet].astype(np.float32) / 255.0
    lab, n = ndimage.label((forward > REGION_THR * 255) & onsheet)
    mm2_per_px = (float(um) / 1000.0) ** 2
    sizes = np.bincount(lab.ravel())[1:] * mm2_per_px if n else np.zeros(0)
    big = sizes[sizes > REGION_MIN_MM2]
    return dict(onsheet_px=int(onsheet.sum()), onsheet_cm2=round(rule55.px_to_cm2(onsheet.sum(), um), 4),
                fwd_mean=round(float(f.mean()), 4), rev_mean=round(float(r.mean()), 4),
                fwd_minus_rev_mean=round(float(f.mean() - r.mean()), 4),
                fwd_frac_gt_0p5=round(float((f > 0.5).mean()), 5), fwd_frac_gt_0p75=round(float((f > 0.75).mean()), 5),
                rev_frac_gt_0p5=round(float((r > 0.5).mean()), 5), rev_frac_gt_0p75=round(float((r > 0.75).mean()), 5),
                regions_gt_0p5mm2_at_fwd_gt_0p5=int(big.size), largest_region_mm2=round(float(sizes.max()), 4) if n else 0.0)


def bright_ink_check(ct_mid, onsheet, um):
    """Fraction of on-sheet CT-mid pixels above the 99.5th pct lying in elongated 2-4 mm marks; flag if > 1 %."""
    vals = ct_mid[onsheet]
    thr = float(np.percentile(vals, BRIGHT_PCT))
    bright = (ct_mid > thr) & onsheet
    n_bright = int(bright.sum())
    lab, n = ndimage.label(bright, structure=np.ones((3, 3), int))
    px_per_mm = 1000.0 / float(um)
    lo, hi = BRIGHT_LEN_MM[0] * px_per_mm, BRIGHT_LEN_MM[1] * px_per_mm
    marks, in_marks = [], 0
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        ext = max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start)
        if ext < lo or ext > 1.5 * hi:
            continue
        ys, xs = np.nonzero(lab[sl] == i)
        if len(ys) < 3:
            continue
        ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([ys, xs]))))[::-1]
        # segment-length estimator: a uniform segment of length L has std L / sqrt(12)
        major, minor = SEG * np.sqrt(max(ev[0], 0.0)), SEG * np.sqrt(max(ev[1], 0.0))
        if lo <= major <= hi and major >= BRIGHT_ELONG * max(minor, 1.0):
            in_marks += len(ys)
            marks.append(dict(y0=int(sl[0].start), x0=int(sl[1].start), n_px=int(len(ys)),
                              length_mm=round(major / px_per_mm, 3), width_mm=round(minor / px_per_mm, 3)))
    frac = in_marks / float(n_bright) if n_bright else 0.0
    return dict(percentile=BRIGHT_PCT, threshold=thr, n_bright_px=n_bright, n_elongated_marks=len(marks),
                frac_in_elongated_marks=round(frac, 5), flag_for_human_look=bool(frac > BRIGHT_FLAG_FRAC),
                criteria="8-connected; long axis (sqrt(12) sigma) 2-4 mm and >= %.0fx short axis" % BRIGHT_ELONG,
                marks=marks[:50])


def draw_sheet(ct_mid, forward, reverse, table, um, title_lines, out_png, max_panel_px, ct_label="CT mid slice"):
    f = cs.downsample_factor(forward.shape, max_panel_px)
    panels, bars = [], {}
    for name, img in ((ct_label, ct_mid), ("forward (as stored)", forward), ("reverse (as stored)", reverse)):
        p, b = cs.panel(cs.gray_to_bgr(cs.shown(img, f)), name, um, f)
        panels.append(p); bars[name] = b
    p, b = cs.panel(cs.margin_image(table, forward.shape, f), "forward - reverse per 0.5 cm^2 unit (flagged circled)", um, f)
    panels.append(p); bars["margin"] = b
    __import__("cv2").imwrite(out_png, cs.assemble(panels, title_lines))
    return dict(shown_1_to=f, bar_px_at_shown_scale=bars, bar_px_at_map_scale=cs.bar_px(um))


def ledger_lines(ledger_path):
    return open(ledger_path).read().splitlines() if os.path.exists(ledger_path) else []


def escape_key(key):
    """Key as written in the ledger table: pipes escaped so the row keeps 10 cells."""
    return key.replace("|", "\\|")


def ledger_has_key(ledger_path, key):
    forms = ("| %s |" % escape_key(key), "| %s |" % key)      # escaped (current) and raw (older lines)
    return any(l.startswith("| ") and any(f in l for f in forms) for l in ledger_lines(ledger_path))


def append_ledger(ledger_path, line):
    """Insert `line` at the end of the Reads table (creating the section if the file lacks it)."""
    lines = ledger_lines(ledger_path)
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("## Reads"))
    except StopIteration:
        lines += ["", "## Reads (one line per read; key = scroll|surface|depth offset|checkpoint+TTA|order; a duplicate key is refused without a written reason)",
                  LEDGER_HEADER, "|" + "---|" * 10]
        start = len(lines) - 3
    end = start + 1
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    lines.insert(end, line)
    open(ledger_path, "w").write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("render", help="render zarr (group, array '0', z y x) or, with --maps-only, an on-sheet mask image")
    ap.add_argument("forward"); ap.add_argument("reverse")
    ap.add_argument("--um", type=float, required=True, help="um/px from the volume's metadata.json (never a default)")
    ap.add_argument("--out", required=True); ap.add_argument("--key", required=True); ap.add_argument("--ledger", required=True)
    ap.add_argument("--reason", help="written reason that allows a duplicate ledger key")
    ap.add_argument("--note", default="", help="provenance note appended to the ledger line and stored in the stats "
                                               "(e.g. that a QC pre-check was superseded by a published render)")
    ap.add_argument("--maps-only", action="store_true", help="first argument is a mask, not a render")
    ap.add_argument("--unit-origin", choices=("auto", "fixed"), default="auto", help="rule 5.5 grid origin: auto = mask-only best_origin (default), fixed = (0, 0)")
    ap.add_argument("--max-panel-px", type=int, default=1000); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    marker = os.path.join(a.out, MARKER)
    if os.path.exists(marker) and not a.force:
        print("skip (complete): %s" % a.out); return 0
    if a.key.count("|") != 4:
        raise SystemExit("--key must be scroll|surface|depth offset|checkpoint+TTA|order")
    if ledger_has_key(a.ledger, a.key) and not a.reason:
        raise SystemExit("REFUSED: key already in %s: %s (pass --reason to write a duplicate)" % (a.ledger, a.key))
    forward, reverse = load_map(a.forward), load_map(a.reverse)
    if a.maps_only:
        raw = load_mask_image(a.render); onsheet = raw > 0; profile, crest, nz = None, None, None
        ct_mid, ct_label = mask_panel(raw)
    else:
        arr = open_render(a.render); nz = int(arr.shape[0])
        ct_mid = np.asarray(arr[nz // 2]); onsheet = ct_mid > 0; ct_label = "CT mid slice"
    if not (forward.shape == reverse.shape == onsheet.shape):
        raise SystemExit("shape mismatch: forward %s reverse %s render/mask %s" % (forward.shape, reverse.shape, onsheet.shape))
    # An incomplete map must never be read. On 2026-09-19 an inference exited 0 with a reverse map non-zero on
    # exactly one quadrant; the zeros where it had no prediction were then averaged in as if the model had
    # answered zero there, and produced a margin of +0.60594 and an ADMITTED verdict out of nothing. The two maps of
    # one read come from the same tiling over the same render, so their footprints must agree, and every on-sheet
    # pixel must carry a prediction. There is no flag to switch this off.
    nzf, nzr = float((forward > 0).mean()), float((reverse > 0).mean())
    if abs(nzf - nzr) > MAP_PAIR_TOL:
        raise SystemExit("REFUSED: truncated map. forward non-zero %.4f, reverse %.4f, differ by %.4f > %.2f -- one "
                         "of the two maps is incomplete (regions left at 0). Delete both maps and the .infer_complete marker and "
                         "re-run the inference." % (nzf, nzr, abs(nzf - nzr), MAP_PAIR_TOL))
    cov = [float((m[onsheet] > 0).mean()) for m in (forward, reverse)] if onsheet.any() else [1.0, 1.0]
    if min(cov) < MAP_MIN_COVERAGE:
        raise SystemExit("REFUSED: truncated map. on-sheet coverage forward %.4f, reverse %.4f (bar %.2f) -- a "
                         "map is zero on part of the on-sheet area (incomplete). Delete both maps and the .infer_complete "
                         "marker and re-run it." % (cov[0], cov[1], MAP_MIN_COVERAGE))
    onsheet_cm2 = rule55.px_to_cm2(onsheet.sum(), a.um)
    std = float(ct_mid[onsheet].std()) if (onsheet.any() and not a.maps_only) else None
    fails = []
    if onsheet_cm2 < MIN_ONSHEET_CM2:
        fails.append("on-sheet %.3f cm^2 < %.1f" % (onsheet_cm2, MIN_ONSHEET_CM2))
    if std is not None and std <= MIN_ONSHEET_STD:
        fails.append("on-sheet CT std %.2f <= %.0f" % (std, MIN_ONSHEET_STD))
    stats = dict(key=a.key, date=datetime.date.today().isoformat(), um_per_px=a.um, maps_only=a.maps_only,
                 inputs=dict(render=a.render, forward=a.forward, reverse=a.reverse), map_shape=list(forward.shape),
                 n_slices=nz, onsheet_cm2=round(onsheet_cm2, 4), onsheet_ct_std=std, assertions_failed=fails,
                 assertion_bars=dict(min_onsheet_cm2=MIN_ONSHEET_CM2, min_onsheet_std=MIN_ONSHEET_STD))
    if fails:
        stats.update(verdict="UNREADABLE", verdict_reason="; ".join(fails))
    else:
        if not a.maps_only:
            profile, crest = slice_profile(arr, onsheet)
            stats["bright_ink_in_render"] = bright_ink_check(ct_mid, onsheet, a.um)
        stats.update(slice_mean_profile=profile, crest_slice=crest, maps=map_stats(forward, reverse, onsheet, a.um))
        rule, tables = rule55.evaluate(forward, reverse, onsheet, a.um, unit_origin=a.unit_origin)
        # RULES R-FLIP: rule 5.5 flags on a SIGNED margin, and "forward" is a property of the SURFACE's normal, which
        # vc_grow_seg_from_seed picks by its own growth. A mirrored surface carrying ink would put its whole signal in
        # the map we label "reverse", with a large negative margin, and the signed rule would never see it. The swapped
        # evaluation is therefore recorded on every read as a TRIPWIRE. It changes no verdict and creates no candidate:
        # what it obliges, when it fires, is an orientation check in the geometry and, if the surface really is
        # mirrored, a separate re-read under its own ledger key with a +flip tag.
        swapped = rule55.evaluate(reverse, forward, onsheet, a.um, row_check=False, unit_origin=a.unit_origin)[0]
        stats["rule55_depth_swapped"] = swapped["units"]
        stats["depth_swap_tripwire"] = bool(swapped["units"]["0.5cm2"]["n_flagged"])
        if a.unit_origin == "auto":                                   # the historical (0, 0) tiling is evaluated too
            fixed = rule55.evaluate(forward, reverse, onsheet, a.um, row_check=False, unit_origin="fixed")[0]
            stats["rule55_fixed_origin"] = fixed["units"]
            # RULES R-5.5 tiling note: the verdict is the CONSERVATIVE combination of both tilings. A grid placement can
            # never dismiss a flag: any flagged unit on either grid rules out BLANK; a >= 3 cluster on either grid is a
            # candidate; BLANK needs no flagged unit on both grids.
            fh = fixed["units"]["0.5cm2"]
            if fixed["verdict"] == "PROMISING CANDIDATE" and rule["verdict"] != "PROMISING CANDIDATE":
                rule = dict(rule, verdict="PROMISING CANDIDATE", verdict_reason="(0, 0)-grid: " + fixed["verdict_reason"] + " | mask-origin grid: " + rule["verdict_reason"])
            # (a (0, 0)-grid NOT ESTABLISHED that comes only from too few valid units never overrides: the valid-unit
            # count belongs to the mask-origin grid; only FLAGS and CLUSTERS carry over)
            if fh["n_flagged"] and rule["verdict"] == "BLANK":
                rule = dict(rule, verdict="NOT ESTABLISHED", verdict_reason="%d unit(s) flagged on the (0, 0) grid (%s) | mask-origin grid: %s" % (
                    fh["n_flagged"], "; ".join("fwd %.3f margin %+.3f" % (u["fwd_mean"], u["margin"]) for u in fh["flagged"]), rule["verdict_reason"]))
            rule["flagged_any_grid"] = int(fh["n_flagged"]) + int(rule["units"]["0.5cm2"]["n_flagged"])
        stats["rule55"] = rule; stats.update(verdict=rule["verdict"], verdict_reason=rule["verdict_reason"])
        try:
            __import__("cv2").imwrite(os.path.join(a.out, "onsheet_mask.png"), onsheet.astype(np.uint8) * 255)
        except Exception as exc:  # pragma: no cover
            stats["onsheet_mask_error"] = str(exc)
        if profile is not None:
            cc = crest_check(profile); stats["crest_check"] = cc
            if not cc["passed"]:
                stats.update(verdict="VOID", verdict_reason=cc["reason"] + " (rule 5.5 said: %s)" % rule["verdict"])
        h = rule["units"]["0.5cm2"]
        title = ["%s   [%s]" % (stats["verdict"], a.key),
                 "fwd %.3f rev %.3f  flagged %d/%d valid 0.5cm2 units, largest cluster %d; %s" % (
                     stats["maps"]["fwd_mean"], stats["maps"]["rev_mean"], h["n_flagged"], h["n_valid"], h["largest_cluster"], rule["verdict_reason"])]
        stats["contact_sheet"] = dict(path=os.path.join(a.out, SHEET),
                                      **draw_sheet(ct_mid, forward, reverse, tables["0.5cm2"], a.um, title, os.path.join(a.out, SHEET), a.max_panel_px, ct_label))
    json.dump(stats, open(os.path.join(a.out, STATS), "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    m, h = stats.get("maps", {}), stats.get("rule55", {}).get("units", {}).get("0.5cm2", {})
    if a.note:
        stats["provenance_note"] = a.note.strip()
    sheet = stats.get("contact_sheet", {}).get("path", "-") + ("; reason: %s" % a.reason if a.reason else "") + (a.note or "")
    line = "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        stats["date"], escape_key(a.key), m.get("fwd_mean", "-"), m.get("rev_mean", "-"), m.get("fwd_frac_gt_0p5", "-"),
        m.get("fwd_frac_gt_0p75", "-"), "%s/%s" % (h.get("n_flagged", "-"), h.get("n_valid", "-")), h.get("largest_cluster", "-"),
        stats["verdict"], sheet)
    append_ledger(a.ledger, line)
    open(marker, "w").write(stats["verdict"] + "\n")
    print(line)
    if fails:
        print("UNREADABLE: " + "; ".join(fails), file=sys.stderr)
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
