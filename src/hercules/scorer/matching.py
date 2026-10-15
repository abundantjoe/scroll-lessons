# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec D: one-to-one Hungarian matching of named letters to seal letters.

A named letter may be matched to a seal letter only if both have the SAME normalised kind
and their canvas distance is <= R.  Among all one-to-one matchings the scorer takes one
of MAXIMUM CARDINALITY and, among those, one of minimum total distance (lexicographic
objective), computed with ``scipy.optimize.linear_sum_assignment`` on a cost matrix whose
disallowed entries carry a penalty larger than any possible sum of allowed distances.
The matched count is unique (it is the maximum matching size); the particular pairs,
and hence C_firm, follow the documented min-distance tie-break.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from .letters import KIND_INDEX, normalize_letter


def max_matching(allowed: np.ndarray, dist: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Maximum-cardinality, then minimum-total-distance, one-to-one matching.

    ``allowed``: bool (n, m); ``dist``: float (n, m).  Returns (rows, cols) of the matched
    allowed pairs, sorted by row.
    """
    allowed = np.asarray(allowed, dtype=bool)
    if allowed.size == 0 or not allowed.any():
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    r_idx = np.flatnonzero(allowed.any(axis=1))
    c_idx = np.flatnonzero(allowed.any(axis=0))
    a = allowed[np.ix_(r_idx, c_idx)]
    d = np.asarray(dist, dtype=float)[np.ix_(r_idx, c_idx)]
    # Fast path: every remaining row and column has exactly one allowed partner -> the
    # allowed pairs are the unique maximum matching.
    if (a.sum(axis=1) == 1).all() and (a.sum(axis=0) == 1).all():
        rows, cols = np.nonzero(a)
    else:
        # Penalty > (max number of pairs) * (max allowed distance) => lexicographic optimum.
        penalty = (min(a.shape) + 1) * (float(d[a].max()) + 1.0)
        cost = np.where(a, d, penalty)
        rows, cols = linear_sum_assignment(cost)
        keep = a[rows, cols]
        rows, cols = rows[keep], cols[keep]
    order = np.argsort(rows, kind="stable")
    return r_idx[rows[order]].astype(np.int64), c_idx[cols[order]].astype(np.int64)


def max_matching_size(allowed: np.ndarray) -> int:
    """Size of a maximum one-to-one matching of the allowed pairs (cardinality only).

    Equal to ``len(max_matching(allowed, dist)[0])`` for any ``dist`` (the maximum matching
    size is unique); used by the permutation null where only C_all is needed.
    """
    rows = allowed.any(axis=1)
    if not rows.any():
        return 0
    sub = allowed[rows][:, allowed.any(axis=0)].astype(np.float64)
    r, c = linear_sum_assignment(sub, maximize=True)
    return int(sub[r, c].sum())


def seal_arrays(seal_letters: Sequence[Mapping[str, Any]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate seal letters and return (xy float (m,2), kind codes int (m,), firm bool (m,))."""
    xy = np.zeros((len(seal_letters), 2), dtype=float)
    kinds = np.zeros(len(seal_letters), dtype=np.int64)
    firm = np.zeros(len(seal_letters), dtype=bool)
    for j, s in enumerate(seal_letters):
        k = normalize_letter(s.get("ch"))
        if k is None:
            raise ValueError(f"seal letter {j} has an unknown kind {s.get('ch')!r}")
        if not isinstance(s.get("firm"), bool):
            raise ValueError(f"seal letter {j} must carry a boolean 'firm'")
        for key in ("x", "y"):
            v = s.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"seal letter {j} has a non-finite {key!r}")
        xy[j] = (float(s["x"]), float(s["y"]))
        kinds[j] = KIND_INDEX[k]
        firm[j] = s["firm"]
    return xy, kinds, firm


def named_arrays(named: Sequence[Mapping[str, Any]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (xy, kind codes, original indices) of the KNOWN-kind namings.

    A naming's kind is taken from its ``kind`` key when present, else ``normalize_letter(ch)``.
    """
    xy, kinds, idx = [], [], []
    for i, n in enumerate(named):
        k = n["kind"] if "kind" in n else normalize_letter(n.get("ch"))
        if k is None:
            continue
        xy.append((float(n["x"]), float(n["y"])))
        kinds.append(KIND_INDEX[k])
        idx.append(i)
    return (
        np.asarray(xy, dtype=float).reshape(-1, 2),
        np.asarray(kinds, dtype=np.int64),
        np.asarray(idx, dtype=np.int64),
    )


def distance_matrix(a_xy: np.ndarray, b_xy: np.ndarray) -> np.ndarray:
    """Euclidean distances (n, m), computed identically everywhere in the scorer."""
    if len(a_xy) == 0 or len(b_xy) == 0:
        return np.zeros((len(a_xy), len(b_xy)), dtype=float)
    diff = a_xy[:, None, :] - b_xy[None, :, :]
    return np.sqrt((diff * diff).sum(axis=2))


def match_letters(
    named: Sequence[Mapping[str, Any]], seal_letters: Sequence[Mapping[str, Any]], radius: float
) -> dict:
    """Match one panel's namings (canvas coords) to a seal at ``radius``.

    Returns ``{"pairs": [(named_index, seal_index), ...], "count": int, "firm": int}``;
    ``named_index`` refers to the position in ``named`` (unknown namings never match).
    """
    s_xy, s_kind, s_firm = seal_arrays(seal_letters)
    n_xy, n_kind, n_idx = named_arrays(named)
    pairs, firm = match_arrays(n_xy, n_kind, n_idx, s_xy, s_kind, s_firm, radius)
    return {"pairs": pairs, "count": len(pairs), "firm": firm}


def match_arrays(n_xy, n_kind, n_idx, s_xy, s_kind, s_firm, radius: float) -> tuple[list, int]:
    """Array form of ``match_letters``: returns (pairs [(named_index, seal_index)], C_firm)."""
    if len(n_kind) == 0 or len(s_kind) == 0:
        return [], 0
    dist = distance_matrix(n_xy, s_xy)
    allowed = (dist <= radius) & (n_kind[:, None] == s_kind[None, :])
    rows, cols = max_matching(allowed, dist)
    pairs = [(int(n_idx[r]), int(c)) for r, c in zip(rows, cols)]
    return pairs, int(s_firm[cols].sum())
