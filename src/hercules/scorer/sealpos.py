# Provenance: Project HERCULES | owner the owner | [id removed]
"""Seal letter positions from official human ink labels (RULES.md DECL-SEAL).

"Where official human ink labels exist, a seal letter's position is replaced by the
centroid of labelled ink pixels inside the union of the agreeing sealers' boxes
(unchanged if that union holds no labelled ink)."

Coordinates are canvas px of the seal's frame with pixel centres at integers; a box is
[x0, y0, x1, y1] in the same frame and contains pixel (row r, col c) iff
x0 <= c <= x1 and y0 <= r <= y1.  A labelled ink pixel is ``label_mask > 0``.
The groups are re-derived with ``consensus.agreed_letters`` exactly as ``make_seal``
derives them (same call, same order), and their identity with the seal letters is
asserted, so ``consensus.py`` itself is unchanged.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from hercules.scorer.consensus import CONSENSUS_RADIUS, agreed_letters, make_seal


def _box(n: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    b = n.get("box")
    if not isinstance(b, (list, tuple)) or len(b) != 4:
        return None
    try:
        x0, y0, x1, y1 = (float(v) for v in b)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(v) for v in (x0, y0, x1, y1)) or x1 < x0 or y1 < y0:
        return None
    return x0, y0, x1, y1


def union_mask(boxes: Sequence[tuple[float, float, float, float]], shape: tuple[int, int]) -> np.ndarray:
    """Boolean mask of the union of boxes, clipped to ``shape`` (rows, cols)."""
    m = np.zeros(shape, dtype=bool)
    h, w = shape
    for x0, y0, x1, y1 in boxes:
        c0, c1 = max(0, math.ceil(x0)), min(w - 1, math.floor(x1))
        r0, r1 = max(0, math.ceil(y0)), min(h - 1, math.floor(y1))
        if c0 <= c1 and r0 <= r1:
            m[r0:r1 + 1, c0:c1 + 1] = True
    return m


def label_positions(
    letters: Sequence[Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
    sealer_outputs: Mapping[str, Sequence[Mapping[str, Any]]],
    label_mask: np.ndarray,
) -> list[dict]:
    """Apply the DECL-SEAL label rule to seal ``letters`` (from make_seal) using ``groups``
    (from agreed_letters with the same inputs).  Returns new letter dicts with added keys
    ``pos_source`` ("labels" or "sealers"), ``n_label_px`` and ``sealer_x`` / ``sealer_y``."""
    lab = np.asarray(label_mask)
    if lab.ndim != 2:
        raise ValueError("label_mask must be 2-D")
    if len(letters) != len(groups):
        raise ValueError("letters and groups differ in length")
    ink = lab > 0
    out = []
    for letter, g in zip(letters, groups):
        if (letter["ch"], float(letter["x"]), float(letter["y"])) != (g["ch"], float(g["x"]), float(g["y"])):
            raise ValueError("seal letter and group disagree (order or content)")
        boxes = []
        for m in g["members"]:
            b = _box(sealer_outputs[m["reader"]][m["index"]])
            if b is not None:
                boxes.append(b)
        new = dict(letter)
        new["sealer_x"], new["sealer_y"] = float(letter["x"]), float(letter["y"])
        sel = union_mask(boxes, ink.shape) & ink if boxes else np.zeros(ink.shape, dtype=bool)
        n = int(sel.sum())
        new["n_label_px"] = n
        if n:
            rr, cc = np.nonzero(sel)
            new["x"], new["y"] = float(cc.mean()), float(rr.mean())
            new["pos_source"] = "labels"
        else:
            new["pos_source"] = "sealers"
        out.append(new)
    return out


def make_seal_with_labels(
    sealer_outputs: Mapping[str, Sequence[Mapping[str, Any]]],
    label_mask: np.ndarray | None,
    radius: float = CONSENSUS_RADIUS,
) -> tuple[list[dict], dict]:
    """make_seal, then the label rule when ``label_mask`` is given (else positions unchanged)."""
    letters, stats = make_seal(sealer_outputs, radius=radius)
    if label_mask is None:
        return [dict(l, pos_source="sealers", n_label_px=0, sealer_x=l["x"], sealer_y=l["y"]) for l in letters], stats
    groups = agreed_letters(sealer_outputs, radius=radius, min_readers=2)
    new = label_positions(letters, groups, sealer_outputs, label_mask)
    stats = dict(stats, n_label_positioned=sum(1 for l in new if l["pos_source"] == "labels"))
    return new, stats
