#!/usr/bin/env python
"""rule55.py -- the frozen candidate rule 5.5 (MASTER_PROMPT_v4 section 5.5, RULES.md R-5.5) as pure functions.

Every constant below is copied from RULES.md R-5.5; nothing is tuned here.
  unit side  = round(sqrt(0.5) * 10000 / um) px  (0.5 cm^2; 737 px at 9.596 um, 755 at 9.362, 818 at 8.64 --
               the prompt's prose says 819 at 8.64 but sqrt(0.5)*10000/8.64 = 818.41; the formula is the rule)
  1 cm^2 side = round(10000 / um) px (reported alongside)
  valid unit  = >= 90 % of its pixels on-sheet (CT mid slice > 0)
  flagged     = forward mean >= 0.36 AND (forward - reverse) mean >= 0.08, maps in [0, 1] (uint8 / 255)
  cluster     = 4-connected flagged units; PROMISING CANDIDATE = >= 3 units in one cluster (section 9 trigger)
  BLANK       = no flagged unit over >= 1.5 cm^2 of valid units, i.e. >= 3 nominal 0.5 cm^2 units (the exact pixel
                area of a rounded side, e.g. 3 * 755^2 px = 1.4988 cm^2 at 9.362 um, is reported but not compared)
Implementation decisions (not thresholds): the grid tiles from (0, 0) and only full squares are units; unit means
are taken over the unit's on-sheet pixels; the row pitch is the lag of the highest local maximum of the linearly
detrended row-profile autocorrelation of the forward map inside the largest cluster's bbox (lags 1 .. n/2).
The 2-4 mm row check is REPORT-ONLY (res['rows'], candidate_rule_geometry): it has no bar in RULES.md and does
not gate the verdict.
"""
import math
import numpy as np
from scipy import ndimage
from scipy.signal import correlate, detrend

UNIT_CM2 = 0.5
VALID_ONSHEET_FRAC = 0.90
FWD_MIN = 0.36
MARGIN_MIN = 0.08
MIN_CLUSTER = 3
BLANK_MIN_VALID_CM2 = 1.5
ROW_PITCH_BAND_MM = (2.0, 4.0)
THRESHOLDS = dict(unit_cm2=UNIT_CM2, valid_onsheet_frac=VALID_ONSHEET_FRAC, fwd_min=FWD_MIN, margin_min=MARGIN_MIN,
                  min_cluster=MIN_CLUSTER, blank_min_valid_cm2=BLANK_MIN_VALID_CM2, row_pitch_band_mm=ROW_PITCH_BAND_MM)
VERDICTS = ("VERIFIED LETTER", "VERIFIED INK-LIKE REGION", "PROMISING CANDIDATE", "BLANK", "NEGATIVE",
            "NOT ESTABLISHED", "VOID", "UNREADABLE")


def unit_side(um, area_cm2=UNIT_CM2):
    """Side in px of a square of `area_cm2` at `um` micrometres per pixel: round(sqrt(area) * 10000 / um)."""
    return int(round(math.sqrt(area_cm2) * 10000.0 / float(um)))


def px_to_cm2(n_px, um):
    return float(n_px) * (float(um) / 1e4) ** 2


def prob_scale(a):
    """Divisor that maps a stored map to [0, 1]: 255 for uint8, 1 for float maps already in [0, 1]."""
    return 255.0 if a.dtype == np.uint8 else 1.0


def block_sums(arr, side, mask=None, origin=(0, 0)):
    """Sum of `arr` (times `mask` if given) over every full side x side block tiled from `origin` (dy, dx); shape (R, C)."""
    oy, ox = origin
    R, C = (arr.shape[0] - oy) // side, (arr.shape[1] - ox) // side
    out = np.zeros((max(R, 0), max(C, 0)), np.float64)
    for r in range(R):  # one unit row at a time keeps memory at side x W float64
        slab = arr[oy + r * side:oy + (r + 1) * side, ox:ox + C * side].astype(np.float64)
        if mask is not None:
            slab *= mask[oy + r * side:oy + (r + 1) * side, ox:ox + C * side]
        out[r] = slab.reshape(side, C, side).sum(axis=(0, 2))
    return out


def best_origin(onsheet, side, n_steps=8):
    """Grid origin (dy, dx) in [0, side) that maximises the number of VALID units (>= 90 % on-sheet), searched on an
    n_steps x n_steps lattice of offsets. Depends on the on-sheet MASK only, never on the maps, so it cannot bias which
    units get flagged; ties go to the smallest offset (so (0, 0) wins when nothing beats it)."""
    best, best_n = (0, 0), -1
    step = max(1, side // n_steps)
    for oy in range(0, side, step):
        for ox in range(0, side, step):
            n_on = block_sums(onsheet.astype(np.uint8), side, origin=(oy, ox))
            n = int((n_on / float(side * side) >= VALID_ONSHEET_FRAC).sum()) if n_on.size else 0
            if n > best_n:
                best, best_n = (oy, ox), n
    return best, best_n


def unit_table(forward, reverse, onsheet, side, origin=(0, 0)):
    """Per-unit on-sheet fraction, forward/reverse means over on-sheet pixels, margin, validity, flag."""
    n_on = block_sums(onsheet.astype(np.uint8), side, origin=origin)
    fsum = block_sums(forward, side, onsheet, origin=origin) / prob_scale(forward)
    rsum = block_sums(reverse, side, onsheet, origin=origin) / prob_scale(reverse)
    with np.errstate(invalid="ignore", divide="ignore"):
        fmean, rmean = fsum / n_on, rsum / n_on
    frac = n_on / float(side * side)
    valid = frac >= VALID_ONSHEET_FRAC
    margin = fmean - rmean
    flagged = valid & (np.nan_to_num(fmean, nan=-1.0) >= FWD_MIN) & (np.nan_to_num(margin, nan=-1.0) >= MARGIN_MIN)
    return dict(side=side, origin=tuple(int(v) for v in origin), onsheet_frac=frac, fwd_mean=fmean, rev_mean=rmean, margin=margin, valid=valid, flagged=flagged)


def label_clusters(flagged):
    """4-connected clusters of flagged units: (label array, sizes sorted descending)."""
    lab, n = ndimage.label(flagged)  # default 2-D structure = 4-connectivity
    sizes = np.bincount(lab.ravel())[1:] if n else np.zeros(0, int)
    return lab, sorted((int(s) for s in sizes), reverse=True)


def largest_cluster_bbox(lab, side, origin=(0, 0)):
    """Pixel bbox (y0, y1, x0, x1) of the largest cluster, or None."""
    if lab.max() == 0:
        return None
    oy, ox = origin
    sizes = np.bincount(lab.ravel())[1:]
    rows, cols = np.nonzero(lab == int(np.argmax(sizes)) + 1)
    return (oy + int(rows.min()) * side, oy + (int(rows.max()) + 1) * side, ox + int(cols.min()) * side, ox + (int(cols.max()) + 1) * side)


def row_profile(forward, onsheet, bbox, chunk=1024):
    """Mean forward value per image row over on-sheet pixels inside bbox (rows with no on-sheet pixel = nan)."""
    y0, y1, x0, x1 = bbox
    sums, counts = [], []
    for ys in range(y0, y1, chunk):
        f = forward[ys:min(ys + chunk, y1), x0:x1].astype(np.float32) / prob_scale(forward)
        m = onsheet[ys:min(ys + chunk, y1), x0:x1]
        sums.append((f * m).sum(1)); counts.append(m.sum(1))
    s, c = np.concatenate(sums), np.concatenate(counts)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(c > 0, s / c, np.nan)


def row_pitch(profile, um):
    """Dominant row pitch of a 1-D profile: lag (mm) of the highest local maximum of its detrended autocorrelation."""
    p = np.asarray(profile, np.float64)
    p = np.where(np.isnan(p), np.nanmean(p) if np.isfinite(p).any() else 0.0, p)
    n = len(p)
    if n < 8 or np.allclose(p, p[0]):
        return dict(pitch_mm=None, acf_peak=None, lag_px=None, in_band=False, profile_len=int(n))
    p = detrend(p)
    acf = correlate(p, p, mode="full")[n - 1:]
    acf = acf / acf[0] if acf[0] > 0 else acf
    half = n // 2
    lags = [l for l in range(1, half) if acf[l] > acf[l - 1] and acf[l] >= acf[l + 1]]
    if not lags:
        return dict(pitch_mm=None, acf_peak=None, lag_px=None, in_band=False, profile_len=int(n))
    lag = max(lags, key=lambda l: acf[l])
    pitch = lag * float(um) / 1000.0
    return dict(pitch_mm=round(pitch, 4), acf_peak=round(float(acf[lag]), 4), lag_px=int(lag),
                in_band=bool(ROW_PITCH_BAND_MM[0] <= pitch <= ROW_PITCH_BAND_MM[1]), profile_len=int(n))


def verdict(n_flagged, largest_cluster, n_valid):
    """Verdict label and reason from the 0.5 cm^2 units; n_valid counts nominal 0.5 cm^2 valid units."""
    valid_nominal_cm2 = n_valid * UNIT_CM2
    if n_valid <= 0:
        return "UNREADABLE", "no valid 0.5 cm^2 unit (>= 90 % on-sheet)"
    if n_flagged == 0:
        if valid_nominal_cm2 >= BLANK_MIN_VALID_CM2:
            return "BLANK", "no flagged unit over %d valid units = %.1f cm^2 (>= %.1f)" % (n_valid, valid_nominal_cm2, BLANK_MIN_VALID_CM2)
        return "NOT ESTABLISHED", "no flagged unit but only %d valid units = %.1f cm^2 (< %.1f needed for BLANK)" % (n_valid, valid_nominal_cm2, BLANK_MIN_VALID_CM2)
    if largest_cluster < MIN_CLUSTER:
        return "NOT ESTABLISHED", "%d flagged unit(s), largest 4-connected cluster %d < %d" % (n_flagged, largest_cluster, MIN_CLUSTER)
    return "PROMISING CANDIDATE", "cluster of %d >= %d adjacent flagged 0.5 cm^2 units" % (largest_cluster, MIN_CLUSTER)


def summarise_units(t, um, unit_cm2=UNIT_CM2):
    """JSON-ready summary of a unit table: counts, flagged list, clusters, brightest flagged unit, and every valid
    unit's levels (valid_units) so a near-miss can be told from an isolated spike after the fact."""
    side, flagged = t["side"], t["flagged"]
    lab, sizes = label_clusters(flagged)
    rows, cols = np.nonzero(flagged)
    oy, ox = t.get("origin", (0, 0))
    fl = [dict(row=int(r), col=int(c), y0=oy + int(r) * side, x0=ox + int(c) * side, onsheet_frac=round(float(t["onsheet_frac"][r, c]), 4),
               fwd_mean=round(float(t["fwd_mean"][r, c]), 4), rev_mean=round(float(t["rev_mean"][r, c]), 4),
               margin=round(float(t["margin"][r, c]), 4), cluster=int(lab[r, c])) for r, c in zip(rows, cols)]
    brightest = max(fl, key=lambda d: d["fwd_mean"]) if fl else None
    n_valid = int(t["valid"].sum())
    # Every VALID unit, flagged or not, goes on record. The flagged list alone cannot answer whether a flagged unit is
    # an isolated spike or the peak of a locally elevated region - and ink is spatially organised into strokes and
    # lines while noise is not, so that distinction is physical, not cosmetic. This adds rows to the stats file and
    # changes no threshold, no cluster rule and no verdict: `flagged` above is still exactly what rule 5.5 counts.
    vr, vc = np.nonzero(t["valid"])
    all_valid = [dict(row=int(r), col=int(c), onsheet_frac=round(float(t["onsheet_frac"][r, c]), 4),
                      fwd_mean=round(float(t["fwd_mean"][r, c]), 4), rev_mean=round(float(t["rev_mean"][r, c]), 4),
                      margin=round(float(t["margin"][r, c]), 4), flagged=bool(t["flagged"][r, c]))
                 for r, c in zip(vr, vc)]
    return dict(side_px=int(side), origin=list(t.get("origin", (0, 0))), unit_cm2=round(px_to_cm2(side * side, um), 4), grid_rows=int(flagged.shape[0]),
                grid_cols=int(flagged.shape[1]), n_units=int(flagged.size), n_valid=n_valid,
                valid_area_cm2=round(px_to_cm2(n_valid * side * side, um), 4), valid_area_nominal_cm2=n_valid * unit_cm2,
                n_flagged=len(fl), flagged=fl, valid_units=all_valid,
                n_clusters=len(sizes), cluster_sizes=sizes, largest_cluster=(sizes[0] if sizes else 0),
                largest_cluster_bbox_px=largest_cluster_bbox(lab, side, t.get("origin", (0, 0))), brightest_flagged=brightest)


def evaluate(forward, reverse, onsheet, um, row_check=True, unit_origin="fixed"):
    """Rule 5.5 at 0.5 and 1 cm^2. Returns (json-ready dict, {'0.5cm2': table, '1cm2': table}).
    unit_origin: "fixed" tiles from (0, 0) (the historical grid); "auto" picks the mask-only best_origin per unit size."""
    if not (forward.shape == reverse.shape == onsheet.shape):
        raise ValueError("shape mismatch: forward %s reverse %s onsheet %s" % (forward.shape, reverse.shape, onsheet.shape))
    tables = {}
    for name, area in (("0.5cm2", 0.5), ("1cm2", 1.0)):
        side = unit_side(um, area)
        origin = best_origin(onsheet, side)[0] if unit_origin == "auto" else (0, 0)
        tables[name] = unit_table(forward, reverse, onsheet, side, origin=origin)
    units = {k: summarise_units(t, um, a) for (k, t), a in zip(tables.items(), (0.5, 1.0))}
    half = units["0.5cm2"]
    rows = None
    if row_check and half["largest_cluster_bbox_px"] is not None:
        bbox = half["largest_cluster_bbox_px"]
        rows = dict(bbox_px=list(bbox), **row_pitch(row_profile(forward, onsheet, bbox), um))
    rows_in_band = None if rows is None else rows["in_band"]
    label, reason = verdict(half["n_flagged"], half["largest_cluster"], half["n_valid"])
    geometry = bool(half["largest_cluster"] >= MIN_CLUSTER and rows_in_band is True)   # report-only, never gates
    res = dict(um_per_px=float(um), thresholds=THRESHOLDS, unit_origin=unit_origin,
               grid_origins={k: list(t["origin"]) for k, t in tables.items()}, units=units, rows=rows, rows_check_gates_verdict=False,
               candidate_rule_geometry=geometry, verdict=label, verdict_reason=reason)
    return res, tables


def rule55(forward, reverse, onsheet, um, row_check=True, unit_origin="fixed"):
    """The frozen rule as one call: json-ready dict only (see evaluate for the per-unit tables)."""
    return evaluate(forward, reverse, onsheet, um, row_check, unit_origin)[0]
