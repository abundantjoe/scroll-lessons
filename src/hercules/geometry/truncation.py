# Provenance: Project HERCULES | owner the owner | [id removed]
"""v2 truncation of a traced surface at its first self-contact.

Given a per-vertex generation grid ``g`` (the tracer's growth generation of
each vertex; the official tracer stores it as the uint16 ``generations.tif``
channel) and self-contact pairs (i, j) of flat (row-major) vertex indices:

    cutoff = min over contacts of max(g_i, g_j)
    keep   = g < cutoff             (all vertices if there are no contacts)

i.e. everything grown at or after the generation in which the surface first
touched itself is removed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .tifxyz import SENTINEL, valid_mask


@dataclass
class TruncationResult:
    keep: np.ndarray  # bool, same shape as g
    cutoff: float | None  # None when there are no contacts
    n_contacts: int
    n_removed: int


def _contacts_array(contacts: Iterable) -> np.ndarray:
    c = np.asarray(list(contacts) if not isinstance(contacts, np.ndarray) else contacts)
    if c.size == 0:
        return np.zeros((0, 2), dtype=np.int64)
    c = c.reshape(-1, 2)
    if not np.issubdtype(c.dtype, np.integer):
        if not np.all(np.equal(np.mod(c, 1), 0)):
            raise ValueError("contact indices must be integers")
        c = c.astype(np.int64)
    return c.astype(np.int64)


def v2_truncation(
    g: np.ndarray,
    contacts: Iterable,
    *,
    valid: np.ndarray | None = None,
) -> TruncationResult:
    """Apply v2 truncation. ``contacts`` is an iterable / (N, 2) array of flat
    vertex indices into ``g`` (``np.ravel_multi_index((row, col), g.shape)``).
    If ``valid`` is given, invalid vertices are never kept."""
    g = np.asarray(g)
    c = _contacts_array(contacts)
    n = g.size
    if c.size and (c.min() < 0 or c.max() >= n):
        raise IndexError(f"contact vertex index out of range [0, {n})")
    gf = g.ravel().astype(np.float64)
    if c.shape[0] == 0:
        keep = np.ones(g.shape, dtype=bool)
        cutoff = None
    else:
        cutoff = float(np.min(np.maximum(gf[c[:, 0]], gf[c[:, 1]])))
        keep = g.astype(np.float64) < cutoff
    if valid is not None:
        keep = keep & np.asarray(valid, dtype=bool)
    removed = int(g.size - keep.sum()) if valid is None else int(np.asarray(valid, bool).sum() - keep.sum())
    return TruncationResult(keep=keep, cutoff=cutoff, n_contacts=int(c.shape[0]), n_removed=removed)


def v2_cutoff(g: np.ndarray, contacts: Iterable) -> float | None:
    """Just the cutoff generation (None if no contacts)."""
    return v2_truncation(g, contacts).cutoff


def apply_truncation(points: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """Copy of an (H, W, 3) grid with non-kept vertices set to (-1, -1, -1)."""
    out = np.array(points, dtype=np.float32, copy=True)
    out[~np.asarray(keep, dtype=bool)] = SENTINEL
    return out


def truncate_mesh_points(points: np.ndarray, g: np.ndarray, contacts: Iterable) -> tuple[np.ndarray, TruncationResult]:
    """Convenience: truncate an (H, W, 3) grid with its generation grid."""
    res = v2_truncation(g, contacts, valid=valid_mask(points))
    return apply_truncation(points, res.keep), res
