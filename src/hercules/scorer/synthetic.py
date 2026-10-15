# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic seals and reader outputs with known answers, for validating the scorer.

Nothing here touches real data.  Positions are canvas px; ``reader_item`` converts them
to displayed-image px through a DisplayMap (inverse of the half-pixel convention).
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

from .constants import CONF_FIRM, NONTEXT, TEXT
from .display import DisplayMap
from .letters import CANONICAL_KINDS

# Rough relative letter frequencies of Greek prose (per mille), for synthetic data only.
# Order follows CANONICAL_KINDS (alpha ... omega, lunate sigma in sigma's place).
_FREQ_PER_MILLE = (
    115, 5, 20, 22, 85, 3, 40, 12, 90, 38, 30, 32, 80, 4, 100, 36, 45, 75, 80, 45, 8, 12, 2, 25,
)
LETTER_FREQ = {k: f / sum(_FREQ_PER_MILLE) for k, f in zip(CANONICAL_KINDS, _FREQ_PER_MILLE)}

BOX_HALF = 20.0  # half-size of synthetic letter boxes, canvas px
FIRM_FRAC_DEFAULT = 0.6  # fraction of synthetic seal letters marked firm


def draw_kinds(rng: np.random.Generator, n: int, freq: dict | None = None) -> list[str]:
    freq = LETTER_FREQ if freq is None else freq
    kinds = list(CANONICAL_KINDS)
    p = np.array([freq.get(k, 0.0) for k in kinds], dtype=float)
    p = p / p.sum()
    return [kinds[i] for i in rng.choice(len(kinds), size=n, p=p)]


def grid_positions(
    n: int, spacing: float, per_row: int | None = None, origin: tuple[float, float] = (0.0, 0.0)
) -> list[tuple[float, float]]:
    per_row = per_row or max(1, math.ceil(math.sqrt(n)))
    return [
        (float(origin[0] + (i % per_row) * spacing), float(origin[1] + (i // per_row) * spacing))
        for i in range(n)
    ]


def synthetic_seal(
    rng: np.random.Generator,
    n: int,
    spacing: float = 100.0,
    per_row: int | None = None,
    origin: tuple[float, float] = (0.0, 0.0),
    firm_frac: float = FIRM_FRAC_DEFAULT,
    blank: bool = False,
    freq: dict | None = None,
) -> dict:
    kinds = draw_kinds(rng, n, freq)
    firm = rng.random(n) < firm_frac
    return {
        "blank": bool(blank),
        "letters": [
            {"ch": k, "x": x, "y": y, "firm": bool(f)}
            for k, (x, y), f in zip(kinds, grid_positions(n, spacing, per_row, origin), firm)
        ],
    }


def perfect_text_letters(seal: dict, shift: tuple[float, float] = (0.0, 0.0)) -> list[tuple[str, float, float]]:
    """The seal itself, optionally shifted by (dx, dy) canvas px."""
    return [(l["ch"], l["x"] + shift[0], l["y"] + shift[1]) for l in seal["letters"]]


def random_text_letters(
    rng: np.random.Generator, seal: dict, freq: dict | None = None, jitter: float = 0.0
) -> list[tuple[str, float, float]]:
    """Random kinds (drawn from letter frequencies) at the seal positions."""
    kinds = draw_kinds(rng, len(seal["letters"]), freq)
    out = []
    for k, l in zip(kinds, seal["letters"]):
        dx, dy = (rng.normal(0.0, jitter, size=2) if jitter > 0 else (0.0, 0.0))
        out.append((k, l["x"] + float(dx), l["y"] + float(dy)))
    return out


def reader_item(
    item_id: str,
    dm: DisplayMap,
    text_letters: Iterable[tuple[str, float, float]],
    nontext_letters: Iterable[tuple[str, float, float]] = (),
    rows_text: str = "Y",
    rows_nontext: str = "N",
    conf: str = CONF_FIRM,
) -> dict:
    """A schema-valid reader item placing canvas-coordinate letters on the right panels."""
    panels = {}
    for order, letters, rows in ((TEXT, text_letters, rows_text), (NONTEXT, nontext_letters, rows_nontext)):
        out = []
        for ch, X, Y in letters:
            x, y = dm.from_canvas(X, Y)
            h = BOX_HALF / dm.scale
            out.append({"ch": ch, "x": x, "y": y, "box": [x - h, y - h, x + h, y + h], "conf": conf})
        panels[dm.side_of_order(order)] = {"rows": rows, "letters": out}
    return {"id": item_id, "left": panels["left"], "right": panels["right"]}


def namings_from_letters(letters: Sequence[tuple[str, float, float]], conf: str = CONF_FIRM) -> list[dict]:
    """Canvas-coordinate namings for the consensus functions."""
    return [{"ch": ch, "x": float(x), "y": float(y), "conf": conf} for ch, x, y in letters]
