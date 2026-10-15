# Provenance: Project HERCULES | owner the owner | [id removed]
"""The submission gate SG (RULES.md DECL-SG) and the Route Z discovery rule
(RULES.md DECL-EMPNULL) as mechanical code.

Conventions
-----------
* Every naming is in CANVAS coordinates of the candidate render (the harness maps
  displayed-image coordinates to the canvas with hercules.scorer.display.DisplayMap):
  ``{"ch": str, "x": float, "y": float, "conf": "firm"|"tentative", "box": [x0, y0, x1, y1]}``.
  The canvas x axis is the render horizontal.
* ``readers`` always maps reader_id -> list of namings.
* Agreement ("letter of the same identity within 150 px from >= 2 of 3 readers") is
  hercules.scorer.consensus.agreed_letters (METRIC-HASH chain); one-to-one letter
  correspondence between two reads is hercules.scorer.matching.match_letters (same
  kind, distance <= radius, maximum matching).
* Nothing in this module reads, opens or receives an image.  R is a function of the
  discovery namings, the metadata voxel size and the canvas size only.
* Every function cites the DECL-SG item it implements; bars live in constants.py.
"""

from __future__ import annotations

import json
import math
import os
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from hercules.scorer.canon import hash_json, sha256_hex
from hercules.scorer.consensus import agreed_letters, discovery as scorer_discovery, identity_shuffle_null, make_seal
from hercules.scorer.letters import normalize_letter
from hercules.scorer.matching import match_letters

from . import constants as C

PASS, FAIL = "PASS", "FAIL"
NOT_APPLICABLE, NOT_EVALUATED = "NOT_APPLICABLE", "NOT_EVALUATED"
ATTESTED_PASS, ATTESTED_FAIL = "ATTESTED_PASS", "ATTESTED_FAIL"
OK_STATES = (PASS, NOT_APPLICABLE, ATTESTED_PASS)


# =============================================================================== helpers


def voxel_size_um_from_metadata(metadata: Mapping[str, Any] | str | os.PathLike) -> float:
    """Voxel size (um) from the volume's metadata.json (never assumed).

    Same field as hercules.pipeline.window.voxel_size_from_metadata:
    scan.tomo.acquisition.detector.samplePixelSize (mm).
    """
    if not isinstance(metadata, Mapping):
        metadata = json.loads(Path(metadata).read_text(encoding="utf-8"))
    mm = float(metadata["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    if not (mm > 0 and math.isfinite(mm)):
        raise ValueError("metadata voxel size must be a positive finite number")
    return round(mm * 1000.0, 6)


def px_per_mm(voxel_size_um: float, display_scale: float = 1.0, canvas_px_per_voxel: float = 1.0) -> float:
    """Pixels per mm of a display.

    ``voxel_size_um`` from metadata.json; ``canvas_px_per_voxel`` = render samples per voxel
    along the surface (1 for vc_render_tifxyz at the metadata voxel size);
    ``display_scale`` = displayed px per canvas px (0.5 for a 1/2-scale display; 1 for
    canvas coordinates).
    """
    for v in (voxel_size_um, display_scale, canvas_px_per_voxel):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (v > 0) or not math.isfinite(v):
            raise ValueError("voxel size and scales must be positive finite numbers")
    return 1000.0 / float(voxel_size_um) * float(canvas_px_per_voxel) * float(display_scale)


def _agreed(readers: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict]:
    return agreed_letters(readers, C.CONSENSUS_RADIUS_PX, C.MIN_READERS_AGREE)


def _check_readers(readers: Any, n: int | None = C.N_READERS, what: str = "read") -> None:
    if not isinstance(readers, Mapping):
        raise ValueError(f"{what}: readers must be a mapping reader_id -> namings")
    if n is not None and len(readers) != n:
        raise ValueError(f"{what}: exactly {n} readers are required, got {len(readers)}")


def in_rect(x: float, y: float, rect: Mapping[str, float]) -> bool:
    """Closed rectangle test in canvas coordinates."""
    return rect["x0"] <= x <= rect["x1"] and rect["y0"] <= y <= rect["y1"]


def namings_in_rect(readers: Mapping[str, Sequence[Mapping[str, Any]]], rect: Mapping[str, float]) -> dict:
    """Keep only namings whose point lies in R (letters in R)."""
    return {rid: [n for n in ns if in_rect(float(n["x"]), float(n["y"]), rect)] for rid, ns in readers.items()}


def _as_seal(letters: Sequence[Mapping[str, Any]]) -> list[dict]:
    return [{"ch": l["ch"], "x": float(l["x"]), "y": float(l["y"]), "firm": bool(l.get("firm", False))} for l in letters]


def reproduced(sg_letters: Sequence[Mapping[str, Any]], other_letters: Sequence[Mapping[str, Any]],
               radius: float = C.CONSENSUS_RADIUS_PX) -> dict:
    """How many SG letters are named again (same kind, <= radius, one-to-one) in another read."""
    n = len(sg_letters)
    if n == 0:
        return {"n_sg": 0, "reproduced": 0, "fraction": 0.0}
    named = [{"ch": l["ch"], "x": float(l["x"]), "y": float(l["y"])} for l in other_letters]
    m = match_letters(named, _as_seal(sg_letters), radius)
    return {"n_sg": n, "reproduced": m["count"], "fraction": m["count"] / n}


def _sha(obj: Any) -> str:
    """sha256 of the scorer's ASCII canonical JSON (hercules.scorer.canon.hash_json)."""
    return sha256_hex(hash_json(obj).encode("ascii"))


def _num(v: float) -> float | int:
    v = float(v)
    return int(v) if v.is_integer() else v


def _frac(p: Fraction) -> dict:
    return {"float": float(p), "exact": f"{p.numerator}/{p.denominator}"}


def model_mix_ok(reader_models: Mapping[str, str] | None, available_models: Sequence[str] | None) -> dict:
    """DECL-EMPNULL: where two reader model versions exist, every SG and discovery read uses
    at least one of each.  Not applicable when fewer than two versions are declared."""
    if not available_models or len(set(available_models)) < 2:
        return {"status": NOT_APPLICABLE}
    if not reader_models:
        return {"status": FAIL, "reason": "reader_models_missing"}
    missing = sorted(set(available_models) - set(reader_models.values()))
    return {"status": PASS if not missing else FAIL, "missing_models": missing}


def collect_reads(inputs: Mapping[str, Any]) -> dict[str, list[str]]:
    """Reader ids of every SG read present in ``inputs`` (C.FRESH_READS; ASK.md Q2 default).

    The opposite-order namings (SG 3) and batch blank/canary namings (SG 2) come from the
    readers of the read they accompany (paired display) and are not separate reads."""
    g = lambda *ks: _dig(inputs, ks)  # noqa: E731
    reads = {
        "discovery": g("discovery", "readers"),
        "confirmation": g("confirmation", "readers"),
        "slice_-1": g("slice_rereads", "-1"),
        "slice_+1": g("slice_rereads", "+1"),
        "second_lineage": g("second_lineage", "readers"),
        "retrace": g("retrace", "readers"),
        "rotation": g("rotation", "readers"),
        "arm_NULL": g("arms", "NULL"),
        "arm_REV": g("arms", "REV"),
        "arm_CTRL": g("arms", "CTRL"),
        "band_sealers": g("band_1203_0846A", "sealers"),
    }
    assert tuple(reads) == C.FRESH_READS
    return {k: sorted(v) for k, v in reads.items() if isinstance(v, Mapping)}


def _dig(obj: Any, keys: Sequence[str]) -> Any:
    for k in keys:
        if not isinstance(obj, Mapping) or k not in obj:
            return None
        obj = obj[k]
    return obj


def readers_fresh(reads: Mapping[str, Sequence[str]]) -> dict:
    """Ruling B13: every reader of every SG read is fresh: no reader id is in two reads."""
    seen: dict[str, list[str]] = {}
    for read, ids in reads.items():
        for rid in ids:
            seen.setdefault(rid, []).append(read)
    reused = {rid: r for rid, r in sorted(seen.items()) if len(r) > 1}
    return {"status": PASS if not reused else FAIL, "n_reads": len(reads), "n_readers": len(seen), "reused": reused}


def model_mix_all(reads: Mapping[str, Sequence[str]], reader_models: Mapping[str, str] | None,
                  available_models: Sequence[str] | None) -> dict:
    """Ruling B14 (DECL-EMPNULL): when >= 2 reader model versions exist, every SG read
    (discovery included) uses at least one reader of each.  ``reader_models``: reader id ->
    model version for every reader; a reader without a recorded version fails the read."""
    if not available_models or len(set(available_models)) < 2:
        return {"status": NOT_APPLICABLE}
    per = {}
    for read, ids in reads.items():
        per[read] = model_mix_ok({rid: (reader_models or {}).get(rid) for rid in ids}
                                 if reader_models and all(rid in reader_models for rid in ids) else None,
                                 available_models)
    bad = sorted(r for r, v in per.items() if v["status"] == FAIL)
    return {"status": PASS if not bad else FAIL, "failed_reads": bad, "per_read": per}


# =============================================================================== discovery (DECL-EMPNULL)


def discovery_rule(readers: Mapping[str, Mapping[str, Sequence]], k: int) -> dict:
    """DECL-EMPNULL discovery rule (Route Z): >= 2 of 3 readers name >= k letters of the same
    identity within 150 px in the text order, and the non-text-order agreed count <= 1,
    AND (ruling B1) every reader's F_B (known namings in the non-text order, as in
    hercules.scorer.score) <= 1.

    ``readers``: reader_id -> {"text": namings, "nontext": namings}.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k < C.DISCOVERY_K0:
        raise ValueError(f"k must be an int >= {C.DISCOVERY_K0} (DECL-EMPNULL; k only rises)")
    _check_readers(readers, what="discovery")
    text = {rid: r["text"] for rid, r in readers.items()}
    nontext = {rid: r["nontext"] for rid, r in readers.items()}
    res = scorer_discovery(text, nontext, k=k)
    assert res["nontext_max"] == C.DISCOVERY_NONTEXT_AGREED_MAX and res["radius"] == C.CONSENSUS_RADIUS_PX
    fb = {rid: sum(1 for n in ns if normalize_letter(n.get("ch")) is not None) for rid, ns in sorted(nontext.items())}
    fb_max = max(fb.values()) if fb else 0
    ok = res["pass"] and fb_max <= C.DISCOVERY_FB_MAX  # ruling B1: both bind
    return {"status": PASS if ok else FAIL, "agreed_text": res["agreed_text"],
            "agreed_nontext": res["agreed_nontext"], "k": k, "nontext_agreed_max": C.DISCOVERY_NONTEXT_AGREED_MAX,
            "F_B_per_reader": fb, "F_B_max": fb_max, "F_B_max_bar": C.DISCOVERY_FB_MAX}


def calibrate_discovery_k(null_tiles: Sequence[Mapping[str, Any]]) -> dict:
    """DECL-EMPNULL calibration: apply the discovery rule to >= 200 empirical-null tiles;
    while the false-discovery rate (fraction of null tiles passing) exceeds 1 %, raise k by 1.

    ``null_tiles``: [{"tile_id": str, "readers": {rid: {"text": [...], "nontext": [...]}}}].
    Every null tile is a false discovery by construction, so FDR(k) = #pass(k) / #tiles.
    """
    if len(null_tiles) < C.DISCOVERY_MIN_NULL_TILES:
        return {"status": FAIL, "reason": "insufficient_null_tiles", "n_tiles": len(null_tiles),
                "min_tiles": C.DISCOVERY_MIN_NULL_TILES, "k": None}
    ids = [t["tile_id"] for t in null_tiles]
    if len(set(ids)) != len(ids):
        raise ValueError("null tile ids must be unique")
    at, an, fbm = [], [], []
    for t in null_tiles:
        r = discovery_rule(t["readers"], C.DISCOVERY_K0)
        at.append(r["agreed_text"])
        an.append(r["agreed_nontext"])
        fbm.append(r["F_B_max"])
    at_a, an_a, fb_a = np.asarray(at), np.asarray(an), np.asarray(fbm)
    n = len(null_tiles)
    k, trail = C.DISCOVERY_K0, []
    # the full rule applied to candidates (ruling B1 included) is the rule calibrated (ASK Q3)
    ctrl_ok = (an_a <= C.DISCOVERY_NONTEXT_AGREED_MAX) & (fb_a <= C.DISCOVERY_FB_MAX)
    while True:
        passes = int(((at_a >= k) & ctrl_ok).sum())
        fdr = passes / n
        trail.append({"k": k, "null_passes": passes, "fdr": fdr})
        if fdr <= C.DISCOVERY_FDR_MAX:
            break
        k += 1
    return {"status": PASS, "k": k, "n_tiles": n, "fdr_max": C.DISCOVERY_FDR_MAX, "trail": trail,
            "null_agreed_text_max": int(at_a.max()), "tile_ids_sha256": _sha(sorted(ids))}


# =============================================================================== R (DECL-SG preamble)


def r_shape_ok(rect: Mapping[str, float], ppm: float) -> dict:
    """R = 4.00 cm^2 +-1 %, aspect <= 2:1 (DECL-SG preamble)."""
    w, h = rect["x1"] - rect["x0"], rect["y1"] - rect["y0"]
    if not (w > 0 and h > 0):
        return {"ok": False, "area_cm2": 0.0, "aspect": math.inf}
    area_cm2 = (w / ppm) * (h / ppm) / 100.0
    aspect = max(w / h, h / w)
    ok = abs(area_cm2 - C.R_AREA_CM2) <= C.R_AREA_TOL * C.R_AREA_CM2 + 1e-12 and aspect <= C.R_ASPECT_MAX + 1e-12
    return {"ok": bool(ok), "area_cm2": area_cm2, "aspect": aspect}


def _place(lo: float, hi: float) -> float:
    """Midpoint of a feasible translation interval (lo > hi cannot happen for a valid set)."""
    return (lo + hi) / 2.0


def compute_R(discovery_text_readers: Mapping[str, Sequence[Mapping[str, Any]]], ppm: float,
              canvas_wh: tuple[float, float] | None = None) -> dict:
    """R from the discovery namings (text order) by a fixed rule (DECL-SG preamble).

    Points = agreed discovery letters (>= 2 of 3 readers, same identity, 150 px).  Shapes:
    axis-aligned rectangles (render horizontal) of area exactly 4.00 cm^2 with aspect <= 2:1,
    widths scanned in R_WIDTH_STEP_MM steps plus the exact square and both 2:1 limits.
    Candidate placements have the left (or right) edge on a letter's x and the top (or
    bottom) edge on a letter's y, clamped to the canvas; every set of letters that any
    placement can enclose is enclosed by one of these.  R is the first by:
      1. most agreed letters inside (closed rectangle)            [maximises agreed namings];
      2. most 3-reader letters inside;
      3. largest margin: the set is centred in its feasible translation range (canvas
         clamped) and the smallest letter-to-edge distance is maximised;
      4. aspect closest to 1;  5. wider before taller;  6. smallest y0, then x0.
    Moving R within the feasible range never changes the enclosed set (a gain would
    contradict rule 1).  Inputs: namings, px/mm (from metadata) and canvas size only; no
    image is involved.  Result is independent of reader and naming order.
    """
    groups = _agreed(discovery_text_readers)
    if not groups:
        return {"status": FAIL, "reason": "no_agreed_discovery_letters", "rect": None}
    pts = sorted((float(g["x"]), float(g["y"]), int(g["n_readers"]), g["ch"]) for g in groups)
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    w3 = np.array([1.0 if p[2] >= 3 else 0.0 for p in pts])
    area = C.R_AREA_CM2 * 100.0 * ppm * ppm
    wmin, wmax = math.sqrt(area / C.R_ASPECT_MAX), math.sqrt(area * C.R_ASPECT_MAX)
    step = C.R_WIDTH_STEP_MM * ppm
    widths = sorted(set([wmin + i * step for i in range(int((wmax - wmin) // step) + 1)] + [wmax, math.sqrt(area)]))
    cw = ch = math.inf
    if canvas_wh is not None:
        cw, ch = float(canvas_wh[0]), float(canvas_wh[1])
        widths = [w for w in widths if w <= cw + 1e-9 and area / w <= ch + 1e-9]
        if not widths:
            return {"status": FAIL, "reason": "canvas_smaller_than_R", "rect": None}
    tol = 1e-9 * max(1.0, float(np.abs(xs).max()), float(np.abs(ys).max()), wmax)
    best_key, best = None, None
    for w in widths:
        h = area / w
        lefts = np.unique(np.concatenate([xs, xs - w]))
        tops = np.unique(np.concatenate([ys, ys - h]))
        if canvas_wh is not None:
            lefts = np.unique(np.clip(lefts, 0.0, cw - w))
            tops = np.unique(np.clip(tops, 0.0, ch - h))
        ix = (xs[None, :] >= lefts[:, None] - tol) & (xs[None, :] <= lefts[:, None] + w + tol)
        iy = (ys[None, :] >= tops[:, None] - tol) & (ys[None, :] <= tops[:, None] + h + tol)
        ixf, iyf = ix.astype(np.float64), iy.astype(np.float64)
        cnt = ixf @ iyf.T
        c3 = (ixf * w3) @ iyf.T
        top_cnt = cnt.max()
        top_c3 = c3[cnt == top_cnt].max()
        cand = np.argwhere((cnt == top_cnt) & (c3 == top_c3))
        seen = set()
        aspect = round(max(w / h, h / w), 9)
        for a, b in cand.tolist():
            inside = ix[a] & iy[b]
            key_set = inside.tobytes()
            if key_set in seen:
                continue
            seen.add(key_set)
            mnx, mxx = float(xs[inside].min()), float(xs[inside].max())
            mny, mxy = float(ys[inside].min()), float(ys[inside].max())
            x0 = _place(max(mxx - w, 0.0), min(mnx, cw - w))
            y0 = _place(max(mxy - h, 0.0), min(mny, ch - h))
            rect = {"x0": x0, "y0": y0, "x1": x0 + w, "y1": y0 + h}
            # the enclosed set must be unchanged by centring (guaranteed by rule 1)
            now = (xs >= x0 - tol) & (xs <= x0 + w + tol) & (ys >= y0 - tol) & (ys <= y0 + h + tol)
            assert int(now.sum()) == int(top_cnt), "centring changed the enclosed set"
            margin = round(min(mnx - x0, x0 + w - mxx, mny - y0, y0 + h - mxy), 6)
            key = (-top_cnt, -top_c3, -margin, aspect, -round(w, 6), round(y0, 6), round(x0, 6))
            if best_key is None or key < best_key:
                best_key, best = key, rect
    shape = r_shape_ok(best, ppm)
    assert shape["ok"], shape
    return {"status": PASS, "rect": best, "area_cm2": shape["area_cm2"], "aspect": shape["aspect"],
            "px_per_mm": ppm, "n_agreed_discovery": len(pts), "n_inside": int(-best_key[0]),
            "n_inside_3readers": int(-best_key[1]), "min_margin_mm": float(-best_key[2]) / ppm,
            "n_widths_scanned": len(widths), "rect_sha256": _sha({k: repr(v) for k, v in best.items()})}


# =============================================================================== SG 1


def sg1_letters(confirmation_readers: Mapping[str, Sequence], rect: Mapping[str, float]) -> list[dict]:
    """SG letters: agreed letters of the confirmation reads, from namings inside R."""
    return _agreed(namings_in_rect(confirmation_readers, rect))


def _firm_count(g: Mapping[str, Any]) -> int:
    return sum(1 for m in g["members"] if m.get("conf") == "firm")


def sg1(confirmation_readers: Mapping[str, Sequence], rect: Mapping[str, float],
        null_tiles: Sequence[Mapping[str, Any]], m: int, n_perm: int | None = None,
        discovery_reader_ids: Sequence[str] = ()) -> dict:
    """DECL-SG 1 (a)-(d) on the confirmation reads only.

    (a) >= 12 agreed letters (same identity, 150 px, >= 2 of 3 fresh readers) in R;
    (b) >= 8 of them firm for >= 2 readers;
    (c) agreed - P99(>= 40 empirical-null tiles, 'higher') >= 10 and agreed > null max
        (hercules.scorer.consensus.sg1c_evaluate logic, bars from DECL-SG);
    (d) between-reader identity-shuffle p < 0.01 / m (m = candidates escalated on this
        scroll so far), exact p = (1 + #null >= obs) / (1 + N).
    Readers must be fresh: no confirmation reader id may appear among the discovery readers.
    """
    _check_readers(confirmation_readers, what="SG 1 confirmation")
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        raise ValueError("m must be an int >= 1")
    stale = sorted(set(confirmation_readers) & set(discovery_reader_ids))
    inside = namings_in_rect(confirmation_readers, rect)
    letters = _agreed(inside)
    n_agreed = len(letters)
    n_firm = sum(1 for g in letters if _firm_count(g) >= C.SG1B_MIN_FIRM_READERS)
    a = {"status": PASS if n_agreed >= C.SG1A_MIN_AGREED else FAIL, "agreed": n_agreed, "bar": C.SG1A_MIN_AGREED}
    b = {"status": PASS if n_firm >= C.SG1B_MIN_FIRM else FAIL, "firm_2readers": n_firm, "bar": C.SG1B_MIN_FIRM}
    # (c)
    null_counts = [len(_agreed(t["readers"])) for t in null_tiles]
    if len(null_counts) < C.SG1C_MIN_NULL_TILES:
        c = {"status": FAIL, "reason": "insufficient_null_tiles", "n_null": len(null_counts)}
    else:
        arr = np.asarray(null_counts, dtype=float)
        p99 = float(np.percentile(arr, C.SG1C_PERCENTILE, method="higher"))
        mx = float(arr.max())
        margin = n_agreed - p99
        ok = margin >= C.SG1C_MARGIN and n_agreed > mx
        c = {"status": PASS if ok else FAIL, "n_null": len(null_counts), "p99": _num(p99), "null_max": _num(mx),
             "margin": _num(margin), "bar_margin": C.SG1C_MARGIN}
    # (d)
    alpha = Fraction(1, 100 * m)  # 0.01 / m exactly
    if n_perm is None:
        n_perm = max(C.SG1D_MIN_PERM, C.SG1D_PERM_PER_ALPHA * 100 * m)
    if Fraction(1, 1 + n_perm) >= alpha:
        d = {"status": FAIL, "reason": "too_few_permutations_to_resolve_alpha", "n_perm": n_perm}
    else:
        sh = identity_shuffle_null(inside, n_perm=n_perm, radius=C.CONSENSUS_RADIUS_PX,
                                   min_readers=C.MIN_READERS_AGREE)
        assert sh["observed"] == n_agreed
        d = {"status": PASS if sh["p"] < alpha else FAIL, "p": _frac(sh["p"]), "alpha": _frac(alpha), "m": m,
             "n_perm": n_perm, "seed": sh["seed"], "null_max": max(sh["null"]),
             "null_mean": float(np.mean(sh["null"]))}
    fresh = {"status": PASS if not stale else FAIL, "stale_reader_ids": stale}
    status = PASS if all(x["status"] == PASS for x in (a, b, c, d, fresh)) else FAIL
    return {"status": status, "a": a, "b": b, "c": c, "d": d, "fresh_readers": fresh, "letters": letters}


# =============================================================================== SG 2-4


def _naming_total(readers: Mapping[str, Sequence]) -> int:
    return sum(len(v) for v in readers.values())


def sg2_batch_controls(batches: Sequence[Mapping[str, Any]]) -> dict:
    """DECL-SG 2: in every batch the sealed known-text positive reaches >= 70 % of its REF
    ceiling and the blank gets <= 1 naming; else the batch is VOID and is re-read.

    Batch: {"batch_id", "canary": {"score", "ref_ceiling"} (numbers from the scorer; this
    code never opens a seal), "blank": {"readers": {rid: namings}}}.  A blank's namings are
    counted over all readers of the batch and include unknown characters (stricter reading).
    """
    if not batches:
        return {"status": FAIL, "reason": "no_batches"}
    out = []
    for b in batches:
        s, ceil = float(b["canary"]["score"]), float(b["canary"]["ref_ceiling"])
        canary_ok = ceil > 0 and s >= C.SG2_CANARY_FRACTION * ceil
        blank_n = _naming_total(b["blank"]["readers"])
        blank_ok = blank_n <= C.SG2_BLANK_MAX_NAMINGS
        out.append({"batch_id": b["batch_id"], "canary_fraction": (s / ceil) if ceil > 0 else None,
                    "canary_ok": bool(canary_ok), "blank_namings": blank_n, "blank_ok": bool(blank_ok),
                    "void": not (canary_ok and blank_ok)})
    void = [o["batch_id"] for o in out if o["void"]]
    return {"status": PASS if not void else FAIL, "consequence": "VOID_AND_REREAD" if void else None,
            "void_batches": void, "batches": out}


def sg3_opposite_order(opposite_readers: Mapping[str, Sequence], rect: Mapping[str, float]) -> dict:
    """DECL-SG 3: the opposite (non-text) order has <= 2 namings in R (all readers summed,
    unknown characters included: stricter reading)."""
    inside = namings_in_rect(opposite_readers, rect)
    n = _naming_total(inside)
    return {"status": PASS if n <= C.SG3_OPPOSITE_MAX_NAMINGS else FAIL, "namings_in_R": n,
            "agreed_in_R": len(_agreed(inside)), "bar": C.SG3_OPPOSITE_MAX_NAMINGS}


def sg4_slice(sg_letters: Sequence[Mapping], slice_rereads: Mapping[str, Mapping[str, Sequence]]) -> dict:
    """DECL-SG 4: a +-1 slice re-read re-confirms >= 80 % of the SG letters; both the -1 and
    the +1 re-read must hold (stricter reading).  Re-confirmed = an agreed re-read letter of
    the same kind within 150 px (one-to-one)."""
    per = {}
    for off in C.SG4_SLICE_OFFSETS:
        key = f"{off:+d}"
        if key not in slice_rereads:
            per[key] = {"status": FAIL, "reason": "missing_reread"}
            continue
        rep = reproduced(sg_letters, _agreed(slice_rereads[key]))
        per[key] = {**rep, "status": PASS if rep["n_sg"] > 0 and rep["fraction"] >= C.SG4_RECONFIRM_FRACTION else FAIL}
    return {"status": PASS if all(p["status"] == PASS for p in per.values()) else FAIL,
            "bar": C.SG4_RECONFIRM_FRACTION, "per_offset": per}


# =============================================================================== SG 5-6


def sg5_second_lineage(sg_letters: Sequence[Mapping], lineage: Mapping[str, Any], primary: Mapping[str, Any]) -> dict:
    """DECL-SG 5: a second lineage (different seed AND fold, never trained on this scroll)
    names >= 50 % of the SG letters at the same places (same kind, 150 px).  The base model
    counts as a second lineage only if it is USABLE."""
    meta = lineage["meta"]
    checks = {
        "different_seed": meta.get("seed") is not None and meta.get("seed") != primary.get("seed"),
        "different_fold": meta.get("fold") is not None and meta.get("fold") != primary.get("fold"),
        "never_trained_on_scroll": meta.get("trained_on_this_scroll") is False,
        "base_usable_if_base": (not meta.get("is_base", False)) or meta.get("base_usable") is True,
    }
    rep = reproduced(sg_letters, _agreed(lineage["readers"]))
    ok = all(checks.values()) and rep["n_sg"] > 0 and rep["fraction"] >= C.SG5_FRACTION
    return {"status": PASS if ok else FAIL, "lineage_checks": checks, **rep, "bar": C.SG5_FRACTION}


def overlap_fraction(r_mask: np.ndarray, retrace_mask: np.ndarray) -> float:
    """Fraction of R's (boolean) canvas mask covered by the re-trace mapped to the canvas."""
    r_mask, retrace_mask = np.asarray(r_mask, bool), np.asarray(retrace_mask, bool)
    if r_mask.shape != retrace_mask.shape or not r_mask.any():
        raise ValueError("masks must share a shape and R must be non-empty")
    return float((r_mask & retrace_mask).sum() / r_mask.sum())


def sg6_retrace(sg_letters: Sequence[Mapping], retrace: Mapping[str, Any]) -> dict:
    """DECL-SG 6: an independent re-trace with >= 60 % overlap reproduces >= 50 % of the SG
    letters (same kind, 150 px); a contradicting neighbouring sheet vetoes."""
    ov = float(retrace["overlap_fraction"])
    veto = bool(retrace.get("neighbour_contradiction", True))  # missing -> veto (fail closed)
    rep = reproduced(sg_letters, _agreed(retrace["readers"]))
    ok = ov >= C.SG6_OVERLAP_MIN and not veto and rep["n_sg"] > 0 and rep["fraction"] >= C.SG6_FRACTION
    return {"status": PASS if ok else FAIL, "overlap_fraction": ov, "overlap_bar": C.SG6_OVERLAP_MIN,
            "neighbour_veto": veto, **rep, "bar": C.SG6_FRACTION}


# =============================================================================== SG 9, 13


def sg9_arms(arms: Mapping[str, Mapping[str, Sequence]] | None, trained_on_this_scroll: bool,
             rect: Mapping[str, float]) -> dict:
    """DECL-SG 9: if trained on this scroll, NULL, REV and CTRL each name <= 1 (agreed) letter in R."""
    if not trained_on_this_scroll:
        return {"status": NOT_APPLICABLE}
    per = {}
    for arm in C.SG9_ARMS:
        if not arms or arm not in arms:
            per[arm] = {"status": FAIL, "reason": "missing_arm"}
            continue
        n = len(_agreed(namings_in_rect(arms[arm], rect)))
        per[arm] = {"status": PASS if n <= C.SG9_ARM_MAX_LETTERS else FAIL, "agreed_in_R": n}
    return {"status": PASS if all(p["status"] == PASS for p in per.values()) else FAIL, "per_arm": per}


def sg13_band(sg_letters: Sequence[Mapping], band: Mapping[str, Any] | None) -> dict:
    """DECL-SG 13: inside the 1203/0846A band only, fresh sealers name letters on the 2.4 um
    map (mapped to the 9 um canvas by the caller) blind to the 9 um namings; >= 50 % of the SG
    letters must be confirmed (same kind within 250 px), else ALARM and no submission."""
    if band is None or not band.get("in_band", False):
        return {"status": NOT_APPLICABLE}
    seal, stats = make_seal(band["sealers"], radius=C.CONSENSUS_RADIUS_PX)
    rep = reproduced(sg_letters, seal, radius=C.SG13_RADIUS_PX)
    ok = rep["n_sg"] > 0 and rep["fraction"] >= C.SG13_FRACTION
    return {"status": PASS if ok else FAIL, "alarm": not ok, **rep, "n_sealed": stats["n_letters"],
            "bar": C.SG13_FRACTION}


# =============================================================================== SG 11 layout


def _group_box(g: Mapping[str, Any], readers: Mapping[str, Sequence]) -> list[float] | None:
    boxes = []
    for m in g["members"]:
        b = readers[m["reader"]][m["index"]].get("box")
        if b is None or len(b) != 4:
            return None
        boxes.append([float(v) for v in b])
    x0, y0, x1, y1 = np.median(np.asarray(boxes), axis=0).tolist()
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def find_rows(boxes: Sequence[Sequence[float]]) -> list[list[int]]:
    """Coded row finder on letter boxes: two letters are row neighbours when their centres
    are <= 2.5 mean heights apart horizontally and <= 0.5 mean heights vertically; rows are
    connected components with >= 3 letters, ordered by mean centre y."""
    b = np.asarray(boxes, dtype=float).reshape(-1, 4)
    n = len(b)
    cx, cy, h = (b[:, 0] + b[:, 2]) / 2, (b[:, 1] + b[:, 3]) / 2, b[:, 3] - b[:, 1]
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            hm = (h[i] + h[j]) / 2
            if hm > 0 and abs(cx[i] - cx[j]) <= C.SG11_LINK_DX_H * hm and abs(cy[i] - cy[j]) <= C.SG11_LINK_DY_H * hm:
                parent[find(j)] = find(i)
    comps: dict[int, list[int]] = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(i)
    rows = [sorted(c, key=lambda i: (cx[i], cy[i])) for c in comps.values() if len(c) >= C.SG11_ROW_MIN_LETTERS]
    return sorted(rows, key=lambda r: (float(np.mean(cy[r])), float(np.mean(cx[r]))))


def layout_metrics(boxes: Sequence[Sequence[float]], ppm: float) -> dict:
    """DECL-SG 11 from letter boxes in canvas px, with rulings B8 and B9: >= 3 rows (B9;
    DECL-SG says >= 2) whose fitted baselines lie within 10 deg of the render horizontal;
    row-pitch CV <= 20 %; letter heights measured by code: median of the letters in
    qualifying rows in 2-4 mm (literal DECL-SG 11; ruling B8 revised: the fraction of letters
    in 2-4 mm and every height are reported, with no bar until one is declared)."""
    b = np.asarray(boxes, dtype=float).reshape(-1, 4)
    rows = find_rows(b)
    fits = []
    for r in rows:
        x = (b[r, 0] + b[r, 2]) / 2
        y = b[r, 3]  # baseline = box bottoms
        slope, icpt = np.polyfit(x, y, 1)
        fits.append({"letters": r, "n": len(r), "slope": float(slope), "intercept": float(icpt),
                     "angle_deg": math.degrees(math.atan(slope))})
    good = [f for f in fits if abs(f["angle_deg"]) <= C.SG11_BASELINE_MAX_DEG * (1 + C.BAR_REL_EPS)]
    res = {"n_letters": len(b), "n_rows": len(fits), "n_rows_within_10deg": len(good),
           "row_angles_deg": [round(f["angle_deg"], 6) for f in fits],
           "letter_heights_mm": [float(v) for v in (b[:, 3] - b[:, 1]) / ppm]}  # ruling B8: every letter
    # DECL-SG 11 needs >= 2 rows; ruling B9: with exactly 2 rows the pitch CV is not
    # evaluable, so >= 3 qualifying rows are required.
    rows_ok = len(good) >= max(C.SG11_MIN_ROWS, C.SG11_MIN_ROWS_FOR_CV)
    pitch_ok, heights_ok = False, False
    if len(good) == C.SG11_MIN_ROWS_FOR_CV - 1:
        res["pitch_cv_status"] = NOT_EVALUATED
    if rows_ok:
        allx = np.concatenate([(b[f["letters"], 0] + b[f["letters"], 2]) / 2 for f in good])
        xref = float(allx.mean())
        ang = math.radians(float(np.mean([f["angle_deg"] for f in good])))
        ybase = sorted(f["slope"] * xref + f["intercept"] for f in good)
        pitches = [(ybase[i + 1] - ybase[i]) * math.cos(ang) for i in range(len(ybase) - 1)]
        mean_p = float(np.mean(pitches))
        cv = float(np.std(pitches) / mean_p) if mean_p > 0 else math.inf
        pitch_ok = cv <= C.SG11_PITCH_CV_MAX * (1 + C.BAR_REL_EPS)
        idx = sorted(i for f in good for i in f["letters"])
        hmm = (b[idx, 3] - b[idx, 1]) / ppm
        med = float(np.median(hmm))
        lo, hi = C.SG11_HEIGHT_MM[0] * (1 - C.BAR_REL_EPS), C.SG11_HEIGHT_MM[1] * (1 + C.BAR_REL_EPS)
        frac = float(np.mean((hmm >= lo) & (hmm <= hi)))
        # ruling B8 (revised): the median of the letters in qualifying rows lies in 2-4 mm; a
        # fraction bar applies only once declared (constants.SG11_HEIGHT_FRACTION_MIN)
        heights_ok = lo <= med <= hi
        if C.SG11_HEIGHT_FRACTION_MIN is not None:
            heights_ok = heights_ok and frac >= C.SG11_HEIGHT_FRACTION_MIN * (1 - C.BAR_REL_EPS)
        res.update(pitches_px=pitches, n_pitches=len(pitches), pitch_mm_mean=mean_p / ppm, pitch_cv=cv,
                   letter_height_mm_median=med,
                   letter_height_mm_frac_in_band=frac, letter_height_frac_bar=C.SG11_HEIGHT_FRACTION_MIN,
                   row_letter_heights_mm=[float(v) for v in hmm])
    res.update(rows_ok=rows_ok, pitch_ok=bool(pitch_ok), heights_ok=bool(heights_ok),
               status=PASS if rows_ok and pitch_ok and heights_ok else FAIL)
    return res


def sg11_layout(sg_letters: Sequence[Mapping], confirmation_readers: Mapping[str, Sequence],
                rect: Mapping[str, float], ppm: float) -> dict:
    """DECL-SG 11 on the agreed SG letters; each letter's box = median of its members' boxes."""
    inside = namings_in_rect(confirmation_readers, rect)
    boxes = []
    for g in sg_letters:
        bx = _group_box(g, inside)
        if bx is None:
            return {"status": FAIL, "reason": "letter_box_missing"}
        boxes.append(bx)
    return layout_metrics(boxes, ppm)


# =============================================================================== SG 14


def _invert_affine(m: Sequence[Sequence[float]]) -> np.ndarray:
    a = np.asarray(m, dtype=float).reshape(2, 3)
    full = np.vstack([a, [0.0, 0.0, 1.0]])
    return np.linalg.inv(full)[:2]


def rotation_angle_deg(m: Sequence[Sequence[float]]) -> float | None:
    """Angle of a 2x3 affine if it is a pure rotation (+translation), else None."""
    a = np.asarray(m, dtype=float).reshape(2, 3)[:, :2]
    if not np.allclose(a.T @ a, np.eye(2), atol=1e-6) or np.linalg.det(a) < 0:
        return None
    return math.degrees(math.atan2(a[1, 0], a[0, 0]))


def map_back(readers: Mapping[str, Sequence], canvas_to_display: Sequence[Sequence[float]]) -> dict:
    """Map namings from the rotated display back to canvas coordinates."""
    inv = _invert_affine(canvas_to_display)
    out = {}
    for rid, ns in readers.items():
        out[rid] = []
        for n in ns:
            x, y = float(n["x"]), float(n["y"])
            out[rid].append({**n, "x": inv[0, 0] * x + inv[0, 1] * y + inv[0, 2],
                             "y": inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]})
    return out


def sg14_rotation(sg_letters: Sequence[Mapping], rotation: Mapping[str, Any]) -> dict:
    """DECL-SG 14 (rotation part): a 15 deg render rotation keeps >= 50 % of the letters.

    ``rotation``: {"canvas_to_display": 2x3 affine used to make the rotated render (e.g. the
    cv2.getRotationMatrix2D matrix), "readers": namings in the rotated display}.  The matrix
    must be a rotation by 15 deg (either sense); namings are mapped back and matched."""
    ang = rotation_angle_deg(rotation["canvas_to_display"])
    ang_ok = ang is not None and abs(abs(ang) - C.SG14_ROT_DEG) <= 1e-6
    rep = reproduced(sg_letters, _agreed(map_back(rotation["readers"], rotation["canvas_to_display"])))
    ok = ang_ok and rep["n_sg"] > 0 and rep["fraction"] >= C.SG14_FRACTION
    return {"status": PASS if ok else FAIL, "angle_deg": ang, "angle_ok": bool(ang_ok), **rep, "bar": C.SG14_FRACTION}


# =============================================================================== runner


def _attested(att: Mapping[str, Any] | None, key: str) -> dict:
    a = (att or {}).get(key)
    if not a:
        return {"status": NOT_EVALUATED, "reason": "no_attestation"}
    if not isinstance(a.get("record"), str) or not a["record"]:
        return {"status": NOT_EVALUATED, "reason": "attestation_without_record"}
    return {"status": ATTESTED_PASS if a.get("status") == PASS else ATTESTED_FAIL, "record": a["record"]}


def _guard(fn, *args, **kw) -> dict:
    try:
        return fn(*args, **kw)
    except (KeyError, ValueError, TypeError) as e:
        return {"status": FAIL, "reason": "invalid_input", "error": f"{type(e).__name__}: {e}"}


def _strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "letters"}


def sg_check(inputs: Mapping[str, Any], copy_crops=None, copy_patches=None) -> dict:
    """Evaluate DECL-SG items 0-14 plus discovery and R; per-item PASS/FAIL JSON.

    ``inputs`` keys (all namings in canvas coordinates):
      volume_metadata (metadata.json content or path), canvas_px_per_voxel (default 1),
      canvas_wh [w, h], m,
      discovery {"readers": {rid: {"text", "nontext"}}, "reader_models"?},
      discovery_calibration {"null_tiles": [...]} or {"k": int, "record": str},
      available_reader_models? [..], reader_models? {rid: version} (every reader of every read),
      R_declared {"rect": {x0, y0, x1, y1}, "record": str} (required; must equal the recomputed R),
      confirmation {"readers", "reader_models"?}, empirical_null {"tiles": [{"tile_id", "readers"}]},
      batches [...], opposite_order {"readers"}, slice_rereads {"-1": readers, "+1": readers},
      second_lineage {"meta", "readers"}, primary_lineage {"seed", "fold"},
      retrace {"overlap_fraction", "neighbour_contradiction", "readers"},
      copy_test {"result": copy_test() output} (or pass copy_crops / copy_patches arrays),
      trained_on_this_scroll bool, arms {"NULL", "REV", "CTRL": readers},
      band_1203_0846A {"in_band", "sealers"}, rotation {"canvas_to_display", "readers"},
      copy_test_null {"status", "n_null_tiles", "false_flags", "record"} (ruling B7),
      attestations {"0", "8", "10", "12", "14_profile", "14_tests": {"status", "record"}}.
    Missing inputs make the item NOT_EVALUATED (not passing).  SG passes only if discovery,
    its calibration, R, reader freshness (B13), the model mix (B14) and every item 0-14 are
    PASS, NOT_APPLICABLE or ATTESTED_PASS.
    """
    out: dict[str, Any] = {"sg_version": C.SG_VERSION, "declaration": "RULES.md DECL-SG, DECL-EMPNULL"}
    items: dict[str, Any] = {}
    att = inputs.get("attestations")
    # scale
    vox = voxel_size_um_from_metadata(inputs["volume_metadata"])
    ppm = px_per_mm(vox, 1.0, float(inputs.get("canvas_px_per_voxel", 1.0)))
    out["scale"] = {"voxel_size_um": vox, "canvas_px_per_mm": ppm}
    canvas_wh = tuple(inputs["canvas_wh"]) if inputs.get("canvas_wh") else None
    avail = inputs.get("available_reader_models")
    # discovery calibration + rule
    cal_in = inputs.get("discovery_calibration") or {}
    if "null_tiles" in cal_in:
        cal = _guard(calibrate_discovery_k, cal_in["null_tiles"])
    elif isinstance(cal_in.get("k"), int) and cal_in.get("record"):
        cal = {"status": ATTESTED_PASS if cal_in["k"] >= C.DISCOVERY_K0 else FAIL, "k": cal_in["k"],
               "record": cal_in["record"]}
    else:
        cal = {"status": NOT_EVALUATED, "reason": "discovery_not_calibrated", "k": None}
    out["discovery_calibration"] = cal
    disc_in = inputs.get("discovery")
    disc_ids: list[str] = []
    if disc_in and cal.get("k"):
        disc_ids = sorted(disc_in["readers"])
        disc = _guard(discovery_rule, disc_in["readers"], cal["k"])
    else:
        disc = {"status": NOT_EVALUATED, "reason": "missing_discovery_or_k"}
    out["discovery"] = disc
    # R
    rect = None
    if disc_in:
        rr = _guard(compute_R, {rid: r["text"] for rid, r in disc_in["readers"].items()}, ppm, canvas_wh)
        # DECL-SG: R is declared before the confirmation reads.  The declared rectangle and
        # its record id are required (fail closed) and must equal the recomputed R.
        decl_in = inputs.get("R_declared")
        if rr["status"] == PASS and (not isinstance(decl_in, Mapping) or not decl_in.get("record")):
            rr.update(status=FAIL, reason="R_not_declared", declared_matches=None)
        elif rr["status"] == PASS:
            decl = {k: float(decl_in["rect"][k]) for k in ("x0", "y0", "x1", "y1")}
            same = all(abs(decl[k] - rr["rect"][k]) <= 1e-6 for k in decl)
            rr.update(declared_matches=same, declared_record=decl_in["record"])
            if not same:
                rr.update(status=FAIL, reason="declared_R_differs_from_recomputed")
        if rr["status"] == PASS:
            rect = rr["rect"]
    else:
        rr = {"status": NOT_EVALUATED, "reason": "missing_discovery"}
    out["R"] = rr
    # items
    items["0"] = _attested(att, "0")
    sg_letters: list[dict] = []
    conf = inputs.get("confirmation")
    if rect is not None and conf and inputs.get("empirical_null") and inputs.get("m"):
        r1 = _guard(sg1, conf["readers"], rect, inputs["empirical_null"]["tiles"], inputs["m"],
                    discovery_reader_ids=disc_ids)
        if r1.get("status") in (PASS, FAIL) and "letters" in r1:
            sg_letters = r1["letters"]
        items["1"] = _strip(r1)
    else:
        items["1"] = {"status": NOT_EVALUATED, "reason": "missing_R_confirmation_null_or_m"}

    def need(key, fn, *args):
        if rect is None or not sg_letters or inputs.get(key) is None:
            return {"status": NOT_EVALUATED, "reason": f"missing_{key}_or_R_or_letters"}
        return _guard(fn, *args)

    items["2"] = _guard(sg2_batch_controls, inputs["batches"]) if inputs.get("batches") else \
        {"status": NOT_EVALUATED, "reason": "missing_batches"}
    items["3"] = _guard(sg3_opposite_order, inputs["opposite_order"]["readers"], rect) \
        if rect is not None and inputs.get("opposite_order") else {"status": NOT_EVALUATED, "reason": "missing_opposite_order_or_R"}
    items["4"] = need("slice_rereads", sg4_slice, sg_letters, inputs.get("slice_rereads"))
    items["5"] = need("second_lineage", sg5_second_lineage, sg_letters, inputs.get("second_lineage"),
                      inputs.get("primary_lineage") or {})
    items["6"] = need("retrace", sg6_retrace, sg_letters, inputs.get("retrace"))
    if copy_crops is not None and copy_patches is not None:
        from .copytest import copy_test
        r7 = _guard(copy_test, copy_crops, copy_patches)
        items["7"] = {k: v for k, v in r7.items() if k != "per_letter"}
        if len(copy_crops) != len(sg_letters) or not sg_letters:
            items["7"].update(status=FAIL, reason="crop_count_differs_from_sg_letters",
                              n_sg_letters=len(sg_letters))
    elif inputs.get("copy_test") and isinstance(inputs["copy_test"].get("result"), Mapping):
        r7 = inputs["copy_test"]["result"]
        num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)  # noqa: E731
        ok = (r7.get("status") == PASS and num(r7.get("max_abs_ncc")) and r7["max_abs_ncc"] < C.SG7_NCC_MAX
              and num(r7.get("n_eff_min")) and r7["n_eff_min"] >= C.SG7_NEFF_MIN
              and r7.get("neff_floor_enforced") is True
              and r7.get("n_rotations") == len(C.SG7_ROTATIONS_DEG) and r7.get("n_letters") == len(sg_letters) > 0)
        items["7"] = {"status": PASS if ok else FAIL, "max_abs_ncc": r7.get("max_abs_ncc"),
                      "max_signed_ncc": r7.get("max_signed_ncc"), "min_signed_ncc": r7.get("min_signed_ncc"),
                      "n_eff_min": r7.get("n_eff_min"), "n_letters": r7.get("n_letters"),
                      "n_patches": r7.get("n_patches"), "source": "precomputed copy_test result"}
    else:
        items["7"] = {"status": NOT_EVALUATED, "reason": "missing_copy_test"}
    # ruling B7: the copy-test null against the real label-patch set must be informative
    ctn = inputs.get("copy_test_null")
    if items["7"]["status"] == PASS:
        if not isinstance(ctn, Mapping) or not ctn.get("record"):
            items["7"].update(status=FAIL, reason="copy_test_null_missing")
        elif not (isinstance(ctn.get("n_null_tiles"), int) and ctn["n_null_tiles"] >= C.SG7_NULL_MIN_TILES
                  and isinstance(ctn.get("false_flags"), int) and ctn["false_flags"] <= C.SG7_NULL_MAX_FALSE_FLAGS
                  and ctn.get("status") == "INFORMATIVE"):
            items["7"].update(status=FAIL, reason="copy_test_uninformative")
    if isinstance(ctn, Mapping):
        items["7"]["copy_test_null"] = {k: ctn.get(k) for k in ("status", "n_null_tiles", "false_flags", "record")}
    items["8"] = _attested(att, "8")
    if "trained_on_this_scroll" not in inputs:
        items["9"] = {"status": NOT_EVALUATED, "reason": "missing_trained_on_this_scroll"}
    elif rect is None:
        items["9"] = {"status": NOT_EVALUATED, "reason": "missing_R"}
    else:
        items["9"] = _guard(sg9_arms, inputs.get("arms"), bool(inputs["trained_on_this_scroll"]), rect)
    items["10"] = _attested(att, "10")
    items["11"] = _guard(sg11_layout, sg_letters, conf["readers"], rect, ppm) if rect is not None and sg_letters \
        else {"status": NOT_EVALUATED, "reason": "missing_R_or_letters"}
    items["12"] = _attested(att, "12")
    if "band_1203_0846A" not in inputs:
        items["13"] = {"status": NOT_EVALUATED, "reason": "missing_band_flag"}
    else:
        items["13"] = _guard(sg13_band, sg_letters, inputs["band_1203_0846A"]) if sg_letters or \
            not inputs["band_1203_0846A"].get("in_band") else {"status": FAIL, "reason": "no_sg_letters"}
    rot = need("rotation", sg14_rotation, sg_letters, inputs.get("rotation"))
    p14, t14 = _attested(att, "14_profile"), _attested(att, "14_tests")
    s14 = PASS if rot["status"] == PASS and p14["status"] == ATTESTED_PASS and t14["status"] == ATTESTED_PASS else \
        (FAIL if FAIL in (rot["status"],) or ATTESTED_FAIL in (p14["status"], t14["status"]) else NOT_EVALUATED)
    items["14"] = {"status": s14, "rotation": rot, "raw_fb_profile": p14, "unit_tests": t14}
    out["items"] = items
    out["sg_letters"] = [{"ch": g["ch"], "x": g["x"], "y": g["y"], "n_readers": g["n_readers"],
                          "firm_readers": _firm_count(g)} for g in sg_letters]
    reads = collect_reads(inputs)
    out["readers_fresh"] = readers_fresh(reads)
    out["model_mix"] = model_mix_all(reads, inputs.get("reader_models"), avail)
    gate = [disc["status"], cal["status"], rr["status"], out["readers_fresh"]["status"], out["model_mix"]["status"]] + \
        [items[i]["status"] for i in C.SG_ITEMS]
    failed = [i for i in C.SG_ITEMS if items[i]["status"] not in OK_STATES]
    for name, st in (("model_mix", out["model_mix"]["status"]), ("readers_fresh", out["readers_fresh"]["status"]),
                     ("discovery", disc["status"]), ("discovery_calibration", cal["status"]), ("R", rr["status"])):
        if st not in OK_STATES:
            failed.insert(0, name)
    out["not_passed"] = failed
    out["overall"] = PASS if all(s in OK_STATES for s in gate) else FAIL
    out["K7"] = "no form unless SG 0-14 all pass AND the owner is present (owner presence is not evaluated by code)"
    out["computed_by_code"] = list(C.COMPUTED_ITEMS)
    out["partial"] = C.PARTIAL_ITEMS
    out["inputs_sha256"] = _sha(_hashable(inputs))
    return out


def _hashable(obj: Any) -> Any:
    """JSON-safe copy for hashing (floats kept; tuples to lists)."""
    if isinstance(obj, Mapping):
        return {str(k): _hashable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_hashable(v) for v in obj]
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return obj
