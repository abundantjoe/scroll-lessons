# Provenance: Project HERCULES | owner the owner | [id removed]
"""Batch-validity scorer (DECL-EMPNULL TRIBUNAL) and the I16 run-halt rule.

A batch is VOID if any of:
  * a positive canary's rows found < ROWS_MIN (0.8), or its letter recall
    < RECALL_FRAC (0.5) x its REF ceiling recall;
  * a bait gets > BAIT_MAX_PER_4CM2 (0.5) named letters per 4 cm^2, or any firm naming;
  * mirror detection over the batch's mirror canaries < MIRROR_MIN (0.8);
  * fewer than ``min_valid_readers`` schema-valid readers.
I16: more than 1/3 void batches in a run halts reading (exact rational comparison).

Definitions (fixed here, stated in REPORT.md for declaration):
  rows found      = fraction of (valid reader, canary item) panels answered rows = "Y"
                    on the canary's panel; absolute by default (``rows_relative`` makes it
                    relative to the REF ceiling's rows found).
  letter recall   = per reader, one-to-one same-kind matches of the reader's namings
                    (pooled over the canary's items, canvas coordinates) to the canary's
                    seal letters within R (default hercules R_PRIMARY = 250 canvas px),
                    divided by the number of seal letters; averaged over readers.
  bait namings    = every letter a reader names on a bait panel (known or unknown kind),
                    per 4 cm^2 of bait panel area; averaged over readers; any naming with
                    conf "firm" voids.
  mirror detection = fraction of (valid reader, mirror canary) answers that are correct
                    ("mirrored"/"normal"); a missing answer counts as wrong.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

from hercules.scorer.constants import R_PRIMARY
from hercules.scorer.display import DisplayMap, item_namings
from hercules.scorer.matching import match_letters
from hercules.scorer.schema import validate_reader_output

from . import TRIBUNAL_VERSION

ROWS_MIN = 0.8
RECALL_FRAC = 0.5
BAIT_MAX_PER_4CM2 = 0.5
MIRROR_MIN = 0.8
I16_MAX_VOID = Fraction(1, 3)
MIN_VALID_READERS = 3
MIRROR_ANSWERS = ("mirrored", "normal")


def panel_area_cm2(h_px: float, w_px: float, voxel_um: float) -> float:
    """Canvas panel area in cm^2 (one canvas px = one voxel)."""
    if not voxel_um > 0:
        raise ValueError("voxel_um must be > 0 (from metadata.json)")
    return float(h_px) * float(w_px) * (float(voxel_um) * 1e-4) ** 2


def _valid_readers(readers: Mapping[str, Any]) -> tuple[dict, dict]:
    ok, bad = {}, {}
    for rid, obj in readers.items():
        good, errs = validate_reader_output(obj)
        (ok if good else bad)[rid] = obj if good else errs[:5]
    return ok, bad


def _item(obj: Mapping[str, Any], item_id: str):
    for it in obj["items"]:
        if it["id"] == item_id:
            return it
    return None


def _dmap(keys: Mapping[str, Mapping[str, Any]], rid: str, item_id: str) -> DisplayMap:
    return DisplayMap.from_dict(keys[rid][item_id], reader_id=rid, item_id=item_id)


def score_positive_canary(ctrl: Mapping[str, Any], readers: Mapping[str, Any], keys, *, radius: float,
                          rows_relative: bool) -> dict:
    """``ctrl``: {control_id, item_ids, order ("text": the canary sits on the text side),
    seal: [{ch, x, y, firm}], ref_ceiling: {recall, rows_found?}}."""
    order = ctrl.get("order", "text")
    seal = ctrl["seal"]
    rows_y = rows_n = 0
    recalls = []
    for rid, obj in readers.items():
        pooled = []
        for iid in ctrl["item_ids"]:
            it = _item(obj, iid)
            rows_n += 1
            if it is None:
                continue
            panel = item_namings(it, _dmap(keys, rid, iid))[order]
            rows_y += panel["rows"] == "Y"
            pooled += panel["letters"]
        m = match_letters(pooled, seal, radius)
        recalls.append(m["count"] / len(seal) if seal else math.nan)
    rows_found = rows_y / rows_n if rows_n else 0.0
    recall = sum(recalls) / len(recalls) if recalls else 0.0
    ceil_recall = float(ctrl["ref_ceiling"]["recall"])
    rows_bar = ROWS_MIN * float(ctrl["ref_ceiling"]["rows_found"]) if rows_relative else ROWS_MIN
    reasons = []
    if rows_found < rows_bar:
        reasons.append(f"canary {ctrl['control_id']}: rows found {rows_found:.3f} < {rows_bar:.3f}")
    if not (recall >= RECALL_FRAC * ceil_recall):
        reasons.append(f"canary {ctrl['control_id']}: recall {recall:.3f} < {RECALL_FRAC} x ceiling {ceil_recall:.3f}")
    return {"control_id": ctrl["control_id"], "type": "positive_canary", "rows_found": rows_found,
            "rows_bar": rows_bar, "recall": recall, "recall_per_reader": recalls, "ref_ceiling_recall": ceil_recall,
            "recall_bar": RECALL_FRAC * ceil_recall, "radius": radius, "failed": bool(reasons), "reasons": reasons}


def score_bait(ctrl: Mapping[str, Any], readers: Mapping[str, Any], keys) -> dict:
    """``ctrl``: {control_id, kind, item_ids, orders: panel orders that show bait material
    (default both "text" and "nontext"), area_cm2: bait panel area per item}."""
    orders = ctrl.get("orders", ["text", "nontext"])
    area = float(ctrl["area_cm2"])
    if not area > 0:
        raise ValueError("bait area_cm2 must be > 0")
    per_reader, firm = [], 0
    for rid, obj in readers.items():
        count, a_tot = 0, 0.0
        for iid in ctrl["item_ids"]:
            it = _item(obj, iid)
            a_tot += area * len(orders)
            if it is None:
                continue
            nam = item_namings(it, _dmap(keys, rid, iid))
            for o in orders:
                for L in nam[o]["letters"]:
                    count += 1
                    firm += L["conf"] == "firm"
        per_reader.append(count / (a_tot / 4.0))
    rate = sum(per_reader) / len(per_reader) if per_reader else 0.0
    reasons = []
    if rate > BAIT_MAX_PER_4CM2:
        reasons.append(f"bait {ctrl['control_id']}: {rate:.3f} named letters per 4 cm^2 > {BAIT_MAX_PER_4CM2}")
    if firm:
        reasons.append(f"bait {ctrl['control_id']}: {firm} firm naming(s)")
    return {"control_id": ctrl["control_id"], "type": "bait", "kind": ctrl.get("kind"),
            "named_per_4cm2": rate, "per_reader": per_reader, "firm_namings": firm, "failed": bool(reasons),
            "reasons": reasons}


def score_mirror(ctrls: Sequence[Mapping[str, Any]], mirror_answers: Mapping[str, Mapping[str, str]],
                 reader_ids: Sequence[str]) -> dict:
    """``ctrls``: [{control_id, item_id, mirrored: bool}]; ``mirror_answers``: reader_id ->
    {item_id: "mirrored" | "normal"}."""
    n = correct = 0
    for rid in reader_ids:
        ans = mirror_answers.get(rid, {})
        for c in ctrls:
            n += 1
            a = ans.get(c["item_id"])
            if a in MIRROR_ANSWERS and (a == "mirrored") == bool(c["mirrored"]):
                correct += 1
    det = correct / n if n else 0.0
    reasons = [] if det >= MIRROR_MIN else [f"mirror detection {det:.3f} < {MIRROR_MIN}"]
    return {"type": "mirror", "n_answers": n, "correct": correct, "detection": det, "failed": bool(reasons),
            "reasons": reasons}


def score_batch(batch_key: Mapping[str, Any], readers: Mapping[str, Any], keys: Mapping[str, Mapping[str, Any]],
                mirror_answers: Mapping[str, Mapping[str, str]] | None = None, *, radius: float = R_PRIMARY,
                rows_relative: bool = False, min_valid_readers: int = MIN_VALID_READERS) -> dict:
    """Score the TRIBUNAL controls of one batch.

    ``batch_key``: {batch_id, controls: [...]} with control types positive_canary, bait,
    mirror_canary. ``readers``: reader_id -> reader output JSON (schema-validated here;
    invalid readers are excluded and listed). ``keys``: reader_id -> item_id -> display
    key {window_id, scale, y0, x0, side_order}. Every batch must hold >= 1 positive
    canary, >= 1 bait and >= 1 mirror canary, else it is void (a batch without
    controls cannot be shown to be valid).
    """
    valid, invalid = _valid_readers(readers)
    ctrls = batch_key["controls"]
    pos = [c for c in ctrls if c["type"] == "positive_canary"]
    baits = [c for c in ctrls if c["type"] == "bait"]
    mirrors = [c for c in ctrls if c["type"] == "mirror_canary"]
    reasons: list[str] = []
    if len(valid) < min_valid_readers:
        reasons.append(f"{len(valid)} valid readers < {min_valid_readers}")
    for name, lst in (("positive canary", pos), ("bait", baits), ("mirror canary", mirrors)):
        if not lst:
            reasons.append(f"batch has no {name}")
    results = [score_positive_canary(c, valid, keys, radius=radius, rows_relative=rows_relative) for c in pos]
    results += [score_bait(c, valid, keys) for c in baits]
    if mirrors:
        results.append(score_mirror(mirrors, mirror_answers or {}, sorted(valid)))
    for r in results:
        reasons += r["reasons"]
    return {"tribunal_version": TRIBUNAL_VERSION, "batch_id": batch_key["batch_id"], "void": bool(reasons),
            "reasons": reasons, "n_valid_readers": len(valid), "invalid_readers": invalid, "controls": results,
            "thresholds": {"ROWS_MIN": ROWS_MIN, "RECALL_FRAC": RECALL_FRAC, "BAIT_MAX_PER_4CM2": BAIT_MAX_PER_4CM2,
                           "MIRROR_MIN": MIRROR_MIN, "radius": radius, "rows_relative": rows_relative,
                           "min_valid_readers": min_valid_readers}}


def i16_status(batch_results: Sequence[Mapping[str, Any]]) -> dict:
    """I16: HALT when void batches / batches in the run > 1/3 (evaluated after every
    batch, so the run halts as soon as the running fraction exceeds 1/3)."""
    n = len(batch_results)
    nv = sum(bool(b["void"]) for b in batch_results)
    frac = Fraction(nv, n) if n else Fraction(0)
    first_halt = None
    k = kv = 0
    for b in batch_results:
        k += 1
        kv += bool(b["void"])
        if Fraction(kv, k) > I16_MAX_VOID:
            first_halt = k
            break
    return {"n_batches": n, "n_void": nv, "void_fraction": f"{frac.numerator}/{frac.denominator}",
            "halt": first_halt is not None, "halt_after_batch": first_halt, "max_void": "1/3"}


def mirror_answers_from_panels(readers: Mapping[str, Any], mirror_panels: Sequence[Mapping[str, Any]]) -> dict:
    """Adapter for the proposed brief addendum (proposals/MIRROR-ADDENDUM.md): readers answer
    ``"mirrored": "Y"|"N"`` on each panel. ``mirror_panels``: [{control_id, item_id, side}]
    (the scorer-held position of each mirror canary). Returns reader_id -> {control_id:
    "mirrored"|"normal"}; a panel without a Y/N answer gives no answer (scored as wrong)."""
    out: dict = {}
    for rid, obj in readers.items():
        ans = {}
        for mp in mirror_panels:
            it = _item(obj, mp["item_id"])
            v = (it or {}).get(mp["side"], {}).get("mirrored")
            if v in ("Y", "N"):
                ans[mp["control_id"]] = "mirrored" if v == "Y" else "normal"
        out[rid] = ans
    return out
