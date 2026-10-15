# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec C: the display mapping held by the scorer for every (reader, item).

Half-pixel convention
---------------------
Pixel centres sit at integer coordinates and pixel ``i`` spans ``[i - 0.5, i + 0.5)``, in
both the displayed image and the canvas.  A displayed-image pixel covers ``scale`` canvas
pixels per axis, so its centre maps to the centre of that block:

    X = x0 + (x + 0.5) * scale - 0.5
    Y = y0 + (y + 0.5) * scale - 0.5

where ``(y0, x0)`` is the canvas position of the displayed image's origin (the top-left
edge of image pixel (0, 0) sits at canvas ``(x0 - 0.5, y0 - 0.5)``).  With scale 2 the
image pixel 0 maps to canvas 0.5, between canvas pixels 0 and 1.  Image edges map to
canvas edges.

Side order
----------
The display builder randomises, per reader item, which order (``text`` or ``nontext``) is
shown on the LEFT panel.  ``side_order = (order_on_left, order_on_right)``.  Both panels
share the same scale and crop offset.  A window may be shown as several items (tiles,
each with its own crop offset and side order); the scorer pools a reader's namings over
all items of a window in canvas coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from .constants import LEFT, NONTEXT, ORDERS, RIGHT, SIDES, TEXT
from .letters import normalize_letter

_VALID_SIDE_ORDERS = ((TEXT, NONTEXT), (NONTEXT, TEXT))


@dataclass(frozen=True)
class DisplayMap:
    """Scorer-held key for one reader item.

    reader_id, item_id: identify the item in a reader's output.
    window_id: the canvas window the item shows.
    scale: canvas px per displayed-image px (2.0 for a 1/2-scale display).
    y0, x0: canvas position of the displayed image origin.
    side_order: (order shown LEFT, order shown RIGHT); a {"left": .., "right": ..} mapping
        (the display builder's key format) is accepted and normalised to the tuple.
    """

    reader_id: str
    item_id: str
    window_id: str
    scale: float
    y0: float
    x0: float
    side_order: tuple[str, str]

    def __post_init__(self) -> None:
        for name in ("reader_id", "item_id", "window_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"DisplayMap.{name} must be a non-empty string")
        for name in ("scale", "y0", "x0"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"DisplayMap.{name} must be a finite number")
            object.__setattr__(self, name, float(v))
        if self.scale <= 0:
            raise ValueError("DisplayMap.scale must be > 0")
        so = self.side_order
        if isinstance(so, Mapping):
            # Display-builder form {"left": order, "right": order}.
            if set(so) != set(SIDES):
                raise ValueError(f"DisplayMap.side_order mapping needs exactly the keys {SIDES}, got {so!r}")
            so = (so[LEFT], so[RIGHT])
        if isinstance(so, str) or not isinstance(so, (tuple, list)) or tuple(so) not in _VALID_SIDE_ORDERS:
            raise ValueError(f"DisplayMap.side_order must be one of {_VALID_SIDE_ORDERS}, got {so!r}")
        object.__setattr__(self, "side_order", tuple(so))

    # -- geometry ----------------------------------------------------------------------
    def to_canvas(self, x: float, y: float) -> tuple[float, float]:
        """Displayed-image (x, y) -> canvas (X, Y), half-pixel convention (see module doc)."""
        return (self.x0 + (x + 0.5) * self.scale - 0.5, self.y0 + (y + 0.5) * self.scale - 0.5)

    def from_canvas(self, X: float, Y: float) -> tuple[float, float]:
        """Inverse of ``to_canvas`` (used to build synthetic reads)."""
        return ((X - self.x0 + 0.5) / self.scale - 0.5, (Y - self.y0 + 0.5) / self.scale - 0.5)

    # -- side / order key ----------------------------------------------------------------
    def order_of_side(self, side: str) -> str:
        if side not in SIDES:
            raise ValueError(f"side must be one of {SIDES}")
        return self.side_order[SIDES.index(side)]

    def side_of_order(self, order: str) -> str:
        if order not in ORDERS:
            raise ValueError(f"order must be one of {ORDERS}")
        return SIDES[self.side_order.index(order)]

    # -- serialisation -------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "reader_id": self.reader_id,
            "item_id": self.item_id,
            "window_id": self.window_id,
            "scale": self.scale,
            "y0": self.y0,
            "x0": self.x0,
            "side_order": list(self.side_order),
        }

    @classmethod
    def from_dict(
        cls, d: Mapping[str, Any], reader_id: str | None = None, item_id: str | None = None
    ) -> "DisplayMap":
        """Build from a dict; extra keys (e.g. the display builder's layout, px_per_mm_image,
        PNG hashes) are ignored.  ``reader_id`` / ``item_id`` override or supply those fields
        (the builder's key carries neither)."""
        return cls(
            reader_id=d["reader_id"] if reader_id is None else reader_id,
            item_id=d["item_id"] if item_id is None else item_id,
            window_id=d["window_id"],
            scale=d["scale"],
            y0=d["y0"],
            x0=d["x0"],
            side_order=d["side_order"],
        )


def as_display_map(obj: DisplayMap | Mapping[str, Any]) -> DisplayMap:
    return obj if isinstance(obj, DisplayMap) else DisplayMap.from_dict(obj)


def item_namings(item: Mapping[str, Any], display_map: DisplayMap) -> dict:
    """Split a (schema-valid) reader item into text / non-text namings in canvas coords.

    Returns ``{order: {"rows": "Y"|"N", "side": "left"|"right", "letters": [...]}}`` where
    each letter is ``{"index", "ch", "kind", "x", "y", "conf"}``; ``index`` is the position
    in that panel's letter list and ``kind`` is the normalised kind or None (unknown).
    """
    out = {}
    for side in (LEFT, RIGHT):
        order = display_map.order_of_side(side)
        panel = item[side]
        letters = []
        for i, letter in enumerate(panel["letters"]):
            X, Y = display_map.to_canvas(letter["x"], letter["y"])
            letters.append(
                {
                    "index": i,
                    "ch": letter["ch"],
                    "kind": normalize_letter(letter["ch"]),
                    "x": X,
                    "y": Y,
                    "conf": letter["conf"],
                }
            )
        out[order] = {"rows": panel["rows"], "side": side, "letters": letters}
    return out
