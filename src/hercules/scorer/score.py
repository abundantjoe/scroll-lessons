# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec K: deterministic scoring of one pre-registered decision.

Inputs
------
declaration : {"decision_id": str,
               "arms": [{"arm_id": str, "readers": [reader_id, ...], "windows": [window_id, ...]}, ...]}
seals       : {window_id: {"blank": bool, "letters": [{"ch", "x", "y", "firm"}, ...]}}  (canvas px)
reader_outputs : {reader_id: <schema-valid reader output>}.  Readers the caller discarded
              are simply absent; the arm mean is then over the remaining readers.
display_maps: iterable of DisplayMap (or their dicts), one per (reader_id, item_id).  A
              window may be shown to a reader as several items (tiles); the reader's
              namings are pooled over all of them in canvas coordinates before matching.

Output: a JSON-serialisable dict (see ``score_decision``); ``canonical_json`` of it is
byte-identical for identical inputs.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Iterable, Mapping

import numpy as np

from .canon import contains_forbidden, hash_json, sha256_hex
from .constants import (
    MISSING_ITEM_POLICY,
    N_PERM_DEFAULT,
    NONTEXT,
    NULL_RADIUS,
    R_PRIMARY,
    R_SECONDARY,
    RADII,
    SCORER_VERSION,
    SEED_DEFAULT,
    TEXT,
    WINDOW_HASH_WORDS,
)
from .display import DisplayMap, as_display_map, item_namings
from .matching import match_arrays, named_arrays, seal_arrays
from .null import max_t_p, null_match_counts, permutation_p, window_permutations
from .schema import validate_reader_output


def radius_key(r: float) -> str:
    """JSON key of a radius, e.g. 250.0 -> 'R250'."""
    return f"R{int(r)}" if float(r).is_integer() else f"R{r}"


def _frac_str(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"


def _check_id(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty string")
    if contains_forbidden(value):
        raise ValueError(f"{what} {value!r} contains a format (Cf) character")
    return value


def _parse_declaration(declaration: Any) -> tuple[str, list[dict]]:
    if not isinstance(declaration, Mapping):
        raise ValueError("declaration must be a mapping")
    decision_id = _check_id(declaration.get("decision_id"), "decision_id")
    arms = declaration.get("arms")
    if not isinstance(arms, (list, tuple)) or not arms:
        raise ValueError("declaration.arms must be a non-empty list")
    parsed, seen = [], set()
    for i, arm in enumerate(arms):
        if not isinstance(arm, Mapping):
            raise ValueError(f"arm {i} must be a mapping")
        aid = _check_id(arm.get("arm_id"), f"arm {i} arm_id")
        if aid in seen:
            raise ValueError(f"duplicate arm_id {aid!r}")
        seen.add(aid)
        lists = {}
        for key in ("readers", "windows"):
            vals = arm.get(key)
            if not isinstance(vals, (list, tuple)) or not vals:
                raise ValueError(f"arm {aid!r} needs a non-empty list of {key}")
            vals = [_check_id(v, f"arm {aid!r} {key[:-1]} id") for v in vals]
            if len(set(vals)) != len(vals):
                raise ValueError(f"arm {aid!r} lists a {key[:-1]} twice")
            lists[key] = sorted(vals)
        parsed.append({"arm_id": aid, "readers": lists["readers"], "windows": lists["windows"]})
    parsed.sort(key=lambda a: a["arm_id"])
    return decision_id, parsed


def _match_counts(n_xy, n_kind, n_idx, s_xy, s_kind, s_firm, radius) -> tuple[int, int, list]:
    pairs, firm = match_arrays(n_xy, n_kind, n_idx, s_xy, s_kind, s_firm, radius)
    return len(pairs), firm, [list(p) for p in pairs]


def score_decision(
    declaration: Mapping[str, Any],
    seals: Mapping[str, Mapping[str, Any]],
    reader_outputs: Mapping[str, Any],
    display_maps: Iterable[DisplayMap | Mapping[str, Any]],
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SEED_DEFAULT,
) -> dict:
    """Score one decision.  Deterministic: identical inputs give identical output.

    Per (window, reader): C_all / C_firm at R=250 and R=150 (text order), E_null, C_net and
    single-pair p at R=250, F_B (known namings in the non-text order), F_B_unknown,
    F_B_matched, blank_namings, n_named / n_unknown (text order), matched pairs.
    Per arm: sums over windows of the mean over readers, E_null, C_net, p.
    Decision: max-T p_max over arms.  ``input_sha256`` hashes the canonical inputs.
    """
    if isinstance(n_perm, bool) or not isinstance(n_perm, int) or n_perm < 1:
        raise ValueError("n_perm must be an int >= 1")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative int")
    decision_id, arms = _parse_declaration(declaration)

    # ---------------------------------------------------------------- display maps
    dm_index: dict[tuple[str, str], DisplayMap] = {}
    for obj in display_maps:
        dm = as_display_map(obj)
        for what, v in (("reader_id", dm.reader_id), ("item_id", dm.item_id), ("window_id", dm.window_id)):
            _check_id(v, f"display map {what}")
        key = (dm.reader_id, dm.item_id)
        if key in dm_index:
            raise ValueError(f"duplicate display map for reader {key[0]!r} item {key[1]!r}")
        dm_index[key] = dm

    # ---------------------------------------------------------------- reader outputs
    if not isinstance(reader_outputs, Mapping):
        raise ValueError("reader_outputs must be a mapping reader_id -> output")
    for rid in sorted(reader_outputs):
        _check_id(rid, "reader id")
        ok, errors = validate_reader_output(reader_outputs[rid])
        if not ok:
            raise ValueError(f"reader {rid!r} output is malformed; the caller must discard it: {errors[:5]}")

    # ---------------------------------------------------------------- seals
    if not isinstance(seals, Mapping):
        raise ValueError("seals must be a mapping window_id -> seal")
    windows = sorted({w for a in arms for w in a["windows"]})
    seal_data = {}
    for w in windows:
        if w not in seals:
            raise ValueError(f"no seal for declared window {w!r}")
        seal = seals[w]
        if not isinstance(seal, Mapping) or not isinstance(seal.get("blank"), bool):
            raise ValueError(f"seal of window {w!r} needs a boolean 'blank'")
        if not isinstance(seal.get("letters"), (list, tuple)):
            raise ValueError(f"seal of window {w!r} needs a 'letters' list")
        seal_data[w] = seal_arrays(seal["letters"]) + (seal["blank"],)

    # ---------------------------------------------------------------- input hash
    canonical_inputs = {
        "scorer_version": SCORER_VERSION,
        "declaration": declaration,
        "seals": {w: seals[w] for w in sorted(seals)},
        "reader_outputs": reader_outputs,
        "display_maps": [dm_index[k].to_dict() for k in sorted(dm_index)],
        "n_perm": n_perm,
        "seed": seed,
    }
    input_sha256 = sha256_hex(hash_json(canonical_inputs).encode("ascii"))

    # ---------------------------------------------------------------- items per (reader, window)
    declared_readers = sorted({r for a in arms for r in a["readers"]})
    scored_readers = [r for r in declared_readers if r in reader_outputs]
    needed = {(r, w) for a in arms for r in a["readers"] for w in a["windows"]}
    # A window may be shown to a reader as several items (tiles); all are pooled.
    items: dict[tuple[str, str], list[tuple[dict, DisplayMap]]] = {}
    readers_out = {}
    for rid in declared_readers:
        arm_ids = [a["arm_id"] for a in arms if rid in a["readers"]]
        if rid not in reader_outputs:
            readers_out[rid] = {"status": "missing", "arms": arm_ids, "n_items": 0, "ignored_items": []}
            continue
        ignored = []
        for item in reader_outputs[rid]["items"]:
            dm = dm_index.get((rid, item["id"]))
            if dm is None:
                raise ValueError(f"reader {rid!r} item {item['id']!r} has no display map")
            if (rid, dm.window_id) not in needed:
                ignored.append(item["id"])
                continue
            items.setdefault((rid, dm.window_id), []).append((item, dm))
        readers_out[rid] = {
            "status": "scored",
            "arms": arm_ids,
            "n_items": len(reader_outputs[rid]["items"]),
            "ignored_items": sorted(ignored),
        }

    # ---------------------------------------------------------------- per (window, reader)
    perms_cache: dict[str, np.ndarray] = {}
    null_by_pair: dict[tuple[str, str], np.ndarray] = {}
    windows_out = {}
    zero_null = np.zeros(n_perm, dtype=np.int64)
    for w in windows:
        s_xy, s_kind, s_firm, blank = seal_data[w]
        recs = {}
        for rid in scored_readers:
            if (rid, w) not in needed:
                continue
            if (rid, w) not in items:
                recs[rid] = {
                    "status": "missing_item",
                    "items": [],
                    "n_named": 0,
                    "n_unknown": 0,
                    "C_all": {radius_key(r): 0 for r in RADII},
                    "C_firm": {radius_key(r): 0 for r in RADII},
                    "E_null": 0.0,
                    "C_net": 0.0,
                    "p": 1.0,
                    "F_B": 0,
                    "F_B_unknown": 0,
                    "F_B_matched": {radius_key(r): 0 for r in RADII},
                    "blank_namings": 0,
                    "matches": [],
                }
                null_by_pair[(rid, w)] = zero_null
                continue
            # Pool the reader's namings over every item (tile) of this window, in canvas
            # coordinates, items in item_id order.  Matched pairs are reported as
            # [item_id, index in that item's text-order panel, seal letter index].
            text, nontext, item_recs = [], [], []
            for item, dm in sorted(items[(rid, w)], key=lambda t: t[0]["id"]):
                nam = item_namings(item, dm)
                text += [dict(l, item_id=item["id"]) for l in nam[TEXT]["letters"]]
                nontext += [dict(l, item_id=item["id"]) for l in nam[NONTEXT]["letters"]]
                item_recs.append(
                    {
                        "item_id": item["id"],
                        "side_order": list(dm.side_order),
                        "rows": {TEXT: nam[TEXT]["rows"], NONTEXT: nam[NONTEXT]["rows"]},
                    }
                )
            t_xy, t_kind, t_idx = named_arrays(text)
            f_xy, f_kind, f_idx = named_arrays(nontext)
            c_all, c_firm, fb_matched = {}, {}, {}
            matches = []
            for r in RADII:
                c, cf, pairs = _match_counts(t_xy, t_kind, t_idx, s_xy, s_kind, s_firm, r)
                c_all[radius_key(r)], c_firm[radius_key(r)] = c, cf
                if r == NULL_RADIUS:
                    matches = [[text[i]["item_id"], text[i]["index"], j] for i, j in pairs]
                fb_matched[radius_key(r)] = _match_counts(f_xy, f_kind, f_idx, s_xy, s_kind, s_firm, r)[0]
            if w not in perms_cache:
                perms_cache[w] = window_permutations(len(s_kind), n_perm, seed, w)
            null = null_match_counts(t_xy, t_kind, s_xy, s_kind, perms_cache[w], NULL_RADIUS)
            null_by_pair[(rid, w)] = null
            obs = c_all[radius_key(NULL_RADIUS)]
            s_null = int(null.sum())
            recs[rid] = {
                "status": "scored",
                "items": item_recs,
                "n_named": len(text),
                "n_unknown": len(text) - len(t_idx),
                "C_all": c_all,
                "C_firm": c_firm,
                "E_null": float(Fraction(s_null, n_perm)),
                "C_net": float(Fraction(obs * n_perm - s_null, n_perm)),
                "p": float(permutation_p(obs, null)),
                "F_B": len(f_idx),
                "F_B_unknown": len(nontext) - len(f_idx),
                "F_B_matched": fb_matched,
                "blank_namings": len(t_idx) if blank else 0,
                "matches": matches,
            }
        windows_out[w] = {
            "blank": blank,
            "n_seal": int(len(s_kind)),
            "n_seal_firm": int(s_firm.sum()),
            "readers": recs,
        }

    # ---------------------------------------------------------------- arms
    arms_out = {}
    max_t_input = {}
    for arm in arms:
        aid = arm["arm_id"]
        rs = [r for r in arm["readers"] if r in reader_outputs]
        n_r = len(rs)
        pairs = [(r, w) for w in arm["windows"] for r in rs]
        recs = [windows_out[w]["readers"][r] for r, w in pairs]
        tot = {radius_key(r): sum(rec["C_all"][radius_key(r)] for rec in recs) for r in RADII}
        tot_firm = {radius_key(r): sum(rec["C_firm"][radius_key(r)] for rec in recs) for r in RADII}
        tot_null = np.zeros(n_perm, dtype=np.int64)
        for p in pairs:
            tot_null = tot_null + null_by_pair[p]
        s_null = int(tot_null.sum())
        obs = tot[radius_key(NULL_RADIUS)]
        max_t_input[aid] = (obs, tot_null, n_r)

        def mean(total: int, extra: int = 1) -> float:
            return float(Fraction(total, n_r * extra)) if n_r else 0.0

        p_arm = permutation_p(obs, tot_null)
        fb_total = sum(rec["F_B"] for rec in recs)
        arms_out[aid] = {
            "readers": arm["readers"],
            "readers_scored": rs,
            "readers_missing": [r for r in arm["readers"] if r not in reader_outputs],
            "windows": arm["windows"],
            "blank_windows": [w for w in arm["windows"] if windows_out[w]["blank"]],
            "n_readers": n_r,
            "missing_items": [[r, w] for r, w in sorted(pairs) if windows_out[w]["readers"][r]["status"] == "missing_item"],
            "summed_mean_C_all": {k: mean(v) for k, v in tot.items()},
            "summed_mean_C_firm": {k: mean(v) for k, v in tot_firm.items()},
            "summed_mean_E_null": mean(s_null, n_perm),
            "summed_mean_C_net": mean(obs * n_perm - s_null, n_perm),
            "p": float(p_arm),
            "p_exact": _frac_str(p_arm),
            "F_B_total": fb_total,
            "F_B_mean_per_reader": mean(fb_total),
            "F_B_matched_total": {radius_key(r): sum(rec["F_B_matched"][radius_key(r)] for rec in recs) for r in RADII},
            "blank_namings_total": sum(rec["blank_namings"] for rec in recs),
            "n_named_total": sum(rec["n_named"] for rec in recs),
            "n_unknown_total": sum(rec["n_unknown"] for rec in recs),
        }

    mt = max_t_p(max_t_input)
    best_arm = min(arms_out, key=lambda a: (Fraction(arms_out[a]["p_exact"]), a))
    decision = {
        "p_max": float(mt["p_max"]),
        "p_max_exact": _frac_str(mt["p_max"]),
        "argmax_arm": mt["argmax_arm"],
        "observed_max_summed_mean_C_net": float(mt["observed_max_c_net"]),
        "n_arms": len(arms_out),
        "best_single_arm": best_arm,
        "best_single_arm_p": arms_out[best_arm]["p"],
    }

    return {
        "scorer_version": SCORER_VERSION,
        "decision_id": decision_id,
        "input_sha256": input_sha256,
        "params": {
            "n_perm": n_perm,
            "seed": seed,
            "radius_primary": R_PRIMARY,
            "radius_secondary": R_SECONDARY,
            "null_radius": NULL_RADIUS,
            "missing_item_policy": MISSING_ITEM_POLICY,
            "p_formula": "(1 + #{perm >= observed}) / (1 + n_perm)",
            "p_max_method": "max-T over arms; shared permutation index per window",
            "window_rng": f"default_rng(SeedSequence([seed, *sha256(window_id)[:{4 * WINDOW_HASH_WORDS}] as uint32 LE]))",
        },
        "readers": readers_out,
        "undeclared_readers": sorted(r for r in reader_outputs if r not in readers_out),
        "windows": windows_out,
        "arms": arms_out,
        "decision": decision,
    }
