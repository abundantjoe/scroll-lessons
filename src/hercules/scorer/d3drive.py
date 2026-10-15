# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 (FOLD-0841) bars on score_decision outputs (RULES.md DECL-D3D4, DECL-D3-A1 item 7).

Arms are read in both mirror states; every comparison is made within one state.  The best
FA state is the FA arm with the higher summed mean C_net (ties: state A).  PASS requires all of:
  FA C_net >= CTRL C_net (same state) + max(3, 0.1 S');
  p_max < 0.01 (max-T over FA-A and FA-B, from the D3-FA decision);
  NULLA and REVA C_net <= CTRL C_net + 1 (same state);
  FA F_B per reader <= CTRL F_B per reader + 1 (same state);
  no J window whose FA mean C_net is more than 1 below CTRL's (same state);
  w053 blob-f180 of FA's text-order map <= 0.0272 on every blank window.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

BLOB_BAR = Fraction(272, 10000)


def window_mean_c_net(result: Mapping[str, Any], arm_id: str) -> dict[str, float]:
    """Per non-blank window: mean C_net over the arm's scored readers (missing items count 0, as the scorer)."""
    arm = result["arms"][arm_id]
    out = {}
    for w in arm["windows"]:
        wo = result["windows"][w]
        if wo["blank"]:
            continue
        vals = [wo["readers"][r]["C_net"] for r in arm["readers_scored"] if r in wo["readers"]]
        out[w] = (sum(vals) / len(vals)) if vals else 0.0
    return out


def _state_key(w: str) -> str:
    return w[:-2] if w.endswith("@B") else w


def d3_outcome(arms: Mapping[str, Mapping[str, Any]], p_max_fa: float, per_window: Mapping[str, Mapping[str, float]],
               blob_f180: Mapping[str, float], s_prime: int) -> dict:
    """arms: {arm_id: {'summed_mean_C_net', 'F_B_mean_per_reader'}} for FA-A/B, CTRL-A/B, NULLA-A/B, REVA-A/B.
    per_window: {arm_id: {window: mean C_net}}.  blob_f180: {blank window: FA text-order blob-f180}."""
    for a in ("FA-A", "FA-B", "CTRL-A", "CTRL-B", "NULLA-A", "NULLA-B", "REVA-A", "REVA-B"):
        if a not in arms:
            raise ValueError(f"missing arm {a}")
    if not blob_f180:
        raise ValueError("blob_f180 values required")
    fa = {st: Fraction(arms[f"FA-{st}"]["summed_mean_C_net"]) for st in ("A", "B")}
    st = "A" if fa["A"] >= fa["B"] else "B"
    c = lambda a: Fraction(arms[f"{a}-{st}"]["summed_mean_C_net"])  # noqa: E731
    fb = lambda a: Fraction(arms[f"{a}-{st}"]["F_B_mean_per_reader"])  # noqa: E731
    margin = max(Fraction(3), Fraction(s_prime, 10))
    faw = {_state_key(w): Fraction(v) for w, v in per_window[f"FA-{st}"].items()}
    ctw = {_state_key(w): Fraction(v) for w, v in per_window[f"CTRL-{st}"].items()}
    if set(faw) != set(ctw):
        raise ValueError("FA and CTRL windows differ")
    checks = {
        "fa_ge_ctrl_plus_margin": c("FA") >= c("CTRL") + margin,
        "p_max_lt_0.01": Fraction(p_max_fa) < Fraction(1, 100),
        "nulla_le_ctrl_plus_1": c("NULLA") <= c("CTRL") + 1,
        "reva_le_ctrl_plus_1": c("REVA") <= c("CTRL") + 1,
        "fb_fa_le_ctrl_plus_1": fb("FA") <= fb("CTRL") + 1,
        "no_window_more_than_1_below_ctrl": all(faw[w] >= ctw[w] - 1 for w in faw),
        "blob_f180_le_0.0272": all(Fraction(v) <= BLOB_BAR for v in blob_f180.values()),
    }
    return {"outcome": "PASS" if all(checks.values()) else "NOT PASSED", "best_fa_state": st,
            "margin": float(margin), "checks": checks,
            "fa_minus_ctrl": float(c("FA") - c("CTRL"))}
