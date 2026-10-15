# Provenance: Project HERCULES | owner the owner | [id removed]
"""D1 scoring glue (RULES.md DECL-D1, -A1 .. -A5): seals per mirror state, display maps per
reader item, answer filtering, and the D1 bars on score_decision outputs.

Frames: each window is scored in the levelled-window px frame of the state it was shown in.
State B = state A mirrored left-right: x_B = (W - 1) - x_A (W = 2136), so state-B arms use
the seal mirrored the same way (identities unchanged) under window id "<w>@B".
Items (scorer-held map, one per reader item): {"left": uuid, "right": uuid | None,
"scored_window": w, "role": "window" | "blank" | "canary"}.  Image key entries give each
uuid's kind (REF0/REF015/REF030/REF045/BASE/RAW), order (fwd/rev, F/B, single) and state.
Side order: a BASE panel is TEXT when its order equals the declared text order, a RAW
panel when its slab equals the declared RAW text side; a single REF image is LEFT = TEXT.
Canary items and items not in the job's item map (e.g. the key sheet) are removed before
scoring and counted.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

from hercules.scorer.constants import NONTEXT, TEXT

WINDOW_PX = 2136


def state_window_id(window: str, state: str) -> str:
    if state not in ("A", "B"):
        raise ValueError(f"state must be A or B, got {state!r}")
    return window if state == "A" else f"{window}@B"


def mirror_letters(letters, width: int = WINDOW_PX) -> list[dict]:
    return [dict(l, x=float(width - 1) - float(l["x"])) for l in letters]


def seals_by_state(seal_windows: Mapping[str, Mapping[str, Any]], width: int = WINDOW_PX) -> dict:
    """{w: seal} in the state-A frame -> {w: seal, w@B: mirrored seal} (scorer letter fields only)."""
    out = {}
    for w, s in seal_windows.items():
        letters = [{"ch": l["ch"], "x": float(l["x"]), "y": float(l["y"]), "firm": bool(l["firm"])} for l in s["letters"]]
        out[state_window_id(w, "A")] = {"blank": bool(s["blank"]), "letters": letters}
        out[state_window_id(w, "B")] = {"blank": bool(s["blank"]), "letters": mirror_letters(letters, width)}
    return out


def _panel_order(img: Mapping[str, Any], text_order: str, raw_text_side: str) -> str:
    kind, order = img["kind"], img["order"]
    if kind == "BASE":
        if order not in ("fwd", "rev"):
            raise ValueError(f"BASE order must be fwd/rev, got {order!r}")
        return TEXT if order == text_order else NONTEXT
    if kind == "RAW":
        if order not in ("F", "B"):
            raise ValueError(f"RAW order must be F/B, got {order!r}")
        return TEXT if order == raw_text_side else NONTEXT
    raise ValueError(f"kind {kind!r} has no panel order")


def display_maps_for_job(job: str, items: Mapping[str, Mapping[str, Any]], image_key: Mapping[str, Mapping[str, Any]],
                         text_order: str, raw_text_side: str) -> list[dict]:
    """DisplayMap dicts for every non-canary item of one reader job."""
    if text_order not in ("fwd", "rev") or raw_text_side not in ("F", "B"):
        raise ValueError("text_order must be fwd/rev and raw_text_side F/B")
    out = []
    for iid in sorted(items):
        it = items[iid]
        if it["role"] == "canary":
            continue
        left = image_key[it["left"]]
        right = image_key[it["right"]] if it.get("right") else None
        state = left["state"]
        if right is not None and right["state"] != state:
            raise ValueError(f"item {iid!r} mixes states")
        if right is None:
            if not left["kind"].startswith("REF"):
                raise ValueError(f"single-image item {iid!r} must be REF")
            sides = (TEXT, NONTEXT)
        else:
            sides = (_panel_order(left, text_order, raw_text_side), _panel_order(right, text_order, raw_text_side))
            if set(sides) != {TEXT, NONTEXT}:
                raise ValueError(f"item {iid!r} needs one text and one non-text panel, got {sides}")
        out.append({"reader_id": job, "item_id": iid, "window_id": state_window_id(it["scored_window"], state),
                    "scale": 2.0, "y0": 0.0, "x0": 0.0, "side_order": list(sides)})
    return out


def filter_answer(answer: Mapping[str, Any], items: Mapping[str, Mapping[str, Any]]) -> tuple[dict, dict]:
    """Keep only non-canary items of the job's map; return (filtered answer, counts)."""
    kept, n_canary_named, n_foreign = [], 0, 0
    for it in answer.get("items", []):
        m = items.get(it.get("id"))
        if m is None:
            n_foreign += 1
            continue
        if m["role"] == "canary":
            n_canary_named += len((it.get("left") or {}).get("letters", [])) + len((it.get("right") or {}).get("letters", []))
            continue
        kept.append(it)
    return dict(answer, items=kept), {"canary_namings": n_canary_named, "foreign_items": n_foreign}


def blank_namings_mean(result: Mapping[str, Any], arm_id: str) -> float | None:
    """Mean over scored (reader, blank window) records of an arm of text-order namings on the blank."""
    arm = result["arms"][arm_id]
    vals = []
    for w in arm["windows"]:
        wo = result["windows"][w]
        if not wo["blank"]:
            continue
        for r in arm["readers"]:
            rec = wo["readers"].get(r)
            if rec is not None and rec["status"] == "scored":
                vals.append(rec["blank_namings"])
    return (sum(vals) / len(vals)) if vals else None


def max_mean_fb(result: Mapping[str, Any], arm_id: str) -> float:
    """Largest per-window mean F_B over the arm's scored readers (non-blank windows)."""
    arm = result["arms"][arm_id]
    worst = 0.0
    for w in arm["windows"]:
        wo = result["windows"][w]
        if wo["blank"]:
            continue
        v = [wo["readers"][r]["F_B"] for r in arm["readers"] if r in wo["readers"] and wo["readers"][r]["status"] == "scored"]
        if v:
            worst = max(worst, sum(v) / len(v))
    return worst


def d1_outcome(c_net_best: float, c_all_best: float, c_all_chance: float, p_max: float, fb_max: float,
               blank_mean: float | None, s_prime: int) -> dict:
    """DECL-D1 table on the best family arm (before confirmation passes). Small seal: 20 <= S' < 30
    requires p_max < 0.005 for PASS; S' < 20 is VOID upstream."""
    if s_prime < 20:
        return {"outcome": "VOID", "reason": "S' < 20"}
    p_bar = Fraction(1, 200) if s_prime < 30 else Fraction(1, 100)
    s = Fraction(s_prime)
    cn, ca, cc, p = Fraction(c_net_best), Fraction(c_all_best), Fraction(c_all_chance), Fraction(p_max)
    checks = {
        "c_net_ge_0.30S": cn >= Fraction(3, 10) * s,
        "p_max_lt_bar": p < p_bar,
        "c_all_ge_chance_plus_0.20S": ca >= cc + Fraction(1, 5) * s,
        "mean_F_B_le_2_every_window": Fraction(fb_max) <= 2,
        "blank_namings_mean_le_1": blank_mean is not None and Fraction(blank_mean) <= 1,
    }
    if cn <= Fraction(1, 10) * s or p >= Fraction(1, 20):
        out = "FAIL"
    elif all(checks.values()):
        out = "PASS_PENDING_CONFIRMATION"
    else:
        out = "BETWEEN"
    return {"outcome": out, "checks": checks, "p_bar": float(p_bar)}


def void_check(ref0_summed_mean_c_all: float, s_prime: int) -> bool:
    """True -> VOID: REF sigma 0 summed mean C_all (R 250) < 0.5 S'."""
    return Fraction(ref0_summed_mean_c_all) < Fraction(s_prime, 2)


def sigma_crit(ladder: Mapping[float, float]) -> float | None:
    """Largest sigma whose REF summed mean C_net >= 50 % of sigma 0's (None if sigma 0 <= 0)."""
    base = ladder.get(0.0)
    if base is None or base <= 0:
        return None
    ok = [s for s, v in ladder.items() if Fraction(v) >= Fraction(base) / 2]
    return max(ok) if ok else None
