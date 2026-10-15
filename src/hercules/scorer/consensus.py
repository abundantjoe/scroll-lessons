# Provenance: Project HERCULES | owner the owner | [id removed]
"""Specs F, G, H, I: consensus groups, seal rule, identity-shuffle null, SG 1c, discovery.

Namings passed to this module are in CANVAS coordinates:
``{"ch": str, "x": float, "y": float, "conf": "firm"|"tentative" (optional)}``;
``namings_by_reader`` maps reader_id (str) -> list of namings on one image.

Greedy clustering (``agreed_letters``), fully deterministic:
  1. unknown namings are dropped; the rest are ranked by (reader_id as str, index in that
     reader's list);
  2. candidate edges are pairs of namings with the same kind, from different readers, at
     distance <= radius; they are processed in order (distance, rank_a, rank_b);
  3. an edge whose two namings are both still unused seeds a group;
  4. the group is extended with unused namings of the same kind from readers not yet in
     it that lie within radius of EVERY member (complete linkage), choosing the one with
     the smallest maximum distance to the members, ties by rank, until none is left;
  5. each naming is used at most once; group position = mean of member positions.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, Sequence

import numpy as np

from .constants import (
    CONF_FIRM,
    CONFS,
    CONSENSUS_MIN_READERS,
    CONSENSUS_RADIUS,
    DISCOVERY_K_DEFAULT,
    DISCOVERY_N_READERS,
    DISCOVERY_NONTEXT_MAX,
    N_PERM_DEFAULT,
    N_SEALERS,
    SG1C_MARGIN,
    SG1C_MIN_NULL_TILES,
    SG1C_PERCENTILE,
    SG1C_PERCENTILE_METHOD,
    SHUFFLE_SEED_DEFAULT,
)
from .letters import CANONICAL_KINDS, normalize_letter
from .matching import distance_matrix


class _Prepared:
    """Known namings of several readers, flattened in canonical rank order."""

    def __init__(self, namings_by_reader: Mapping[str, Sequence[Mapping[str, Any]]]):
        if not isinstance(namings_by_reader, Mapping):
            raise ValueError("namings_by_reader must be a mapping reader_id -> namings")
        for rid in namings_by_reader:
            if not isinstance(rid, str):
                raise ValueError("reader ids must be strings")
        self.reader_ids = sorted(namings_by_reader)
        xy, kinds, rpos, index, conf = [], [], [], [], []
        self.n_named = {}
        self.n_unknown = {}
        for p, rid in enumerate(self.reader_ids):
            namings = namings_by_reader[rid]
            self.n_named[rid] = len(namings)
            self.n_unknown[rid] = 0
            for i, n in enumerate(namings):
                k = normalize_letter(n.get("ch"))
                if k is None:
                    self.n_unknown[rid] += 1
                    continue
                x, y = n.get("x"), n.get("y")
                for v in (x, y):
                    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                        raise ValueError(f"naming {rid}[{i}] has a non-finite coordinate")
                xy.append((float(x), float(y)))
                kinds.append(CANONICAL_KINDS.index(k))
                rpos.append(p)
                index.append(i)
                conf.append(n.get("conf"))
        self.xy = np.asarray(xy, dtype=float).reshape(-1, 2)
        self.kinds = np.asarray(kinds, dtype=np.int64)
        self.rpos = np.asarray(rpos, dtype=np.int64)
        self.index = index
        self.conf = conf
        self.dist = distance_matrix(self.xy, self.xy)

    def edges(self, radius: float) -> tuple[np.ndarray, np.ndarray]:
        """Cross-reader pairs (a < b) within radius, sorted by (distance, a, b); kind ignored."""
        n = len(self.kinds)
        if n < 2:
            return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
        a, b = np.triu_indices(n, k=1)
        keep = (self.dist[a, b] <= radius) & (self.rpos[a] != self.rpos[b])
        a, b = a[keep], b[keep]
        order = np.lexsort((b, a, self.dist[a, b]))
        return a[order].astype(np.int64), b[order].astype(np.int64)


def _greedy(prep: _Prepared, kinds: np.ndarray, ea: np.ndarray, eb: np.ndarray, radius: float):
    """Greedy complete-linkage grouping; returns (groups as sorted rank lists, used mask)."""
    n = len(kinds)
    used = np.zeros(n, dtype=bool)
    groups: list[list[int]] = []
    same = kinds[ea] == kinds[eb]
    D, rpos = prep.dist, prep.rpos
    for a, b in zip(ea[same].tolist(), eb[same].tolist()):
        if used[a] or used[b]:
            continue
        members = [a, b]
        used[a] = used[b] = True
        k = kinds[a]
        while True:
            cand = (~used) & (kinds == k)
            for m in members:
                cand &= (D[m] <= radius) & (rpos != rpos[m])
            if not cand.any():
                break
            idx = np.flatnonzero(cand)
            worst = D[np.ix_(idx, members)].max(axis=1)
            c = int(idx[np.lexsort((idx, worst))[0]])
            members.append(c)
            used[c] = True
        groups.append(sorted(members))
    return groups, used


def _count(groups, used, min_readers: int) -> int:
    count = sum(1 for g in groups if len(g) >= min_readers)
    if min_readers <= 1:
        count += int((~used).sum())
    return count


def _check_min_readers(min_readers: int) -> None:
    if isinstance(min_readers, bool) or not isinstance(min_readers, int) or min_readers < 1:
        raise ValueError("min_readers must be an int >= 1")


def agreed_letters(
    namings_by_reader: Mapping[str, Sequence[Mapping[str, Any]]],
    radius: float = CONSENSUS_RADIUS,
    min_readers: int = CONSENSUS_MIN_READERS,
) -> list[dict]:
    """Groups of same-kind namings within ``radius`` from >= ``min_readers`` distinct readers.

    Returns groups in formation order (then singletons in rank order when
    ``min_readers <= 1``): ``{"ch", "x", "y", "n_readers", "members": [{"reader",
    "index", "conf"}]}`` with members in reader order and position = member mean.
    """
    _check_min_readers(min_readers)
    prep = _Prepared(namings_by_reader)
    ea, eb = prep.edges(radius)
    groups, used = _greedy(prep, prep.kinds, ea, eb, radius)
    if min_readers <= 1:
        groups = groups + [[i] for i in np.flatnonzero(~used).tolist()]
    out = []
    for g in groups:
        if len(g) < min_readers:
            continue
        out.append(
            {
                "ch": CANONICAL_KINDS[int(prep.kinds[g[0]])],
                "x": math.fsum(prep.xy[i, 0] for i in g) / len(g),
                "y": math.fsum(prep.xy[i, 1] for i in g) / len(g),
                "n_readers": len(g),
                "members": [
                    {"reader": prep.reader_ids[int(prep.rpos[i])], "index": prep.index[i], "conf": prep.conf[i]}
                    for i in g
                ],
            }
        )
    return out


# --------------------------------------------------------------------------- seal rule (F)


def make_seal(
    sealer_outputs: Mapping[str, Sequence[Mapping[str, Any]]], radius: float = CONSENSUS_RADIUS
) -> tuple[list[dict], dict]:
    """Build the seal of one image from exactly three sealers' namings (canvas coords).

    A seal letter is an agreed group from >= 2 of the 3 sealers.  It is firm when all 3
    agree, or when exactly 2 agree and both marked it firm.  Returns ``(letters, stats)``.
    """
    if not isinstance(sealer_outputs, Mapping) or len(sealer_outputs) != N_SEALERS:
        raise ValueError(f"make_seal needs exactly {N_SEALERS} sealers")
    for sid, namings in sealer_outputs.items():
        for i, n in enumerate(namings):
            if n.get("conf") not in CONFS:
                raise ValueError(f"sealer {sid!r} naming {i} needs conf in {CONFS}")
    groups = agreed_letters(sealer_outputs, radius=radius, min_readers=2)
    letters = []
    in_seal = {sid: 0 for sid in sealer_outputs}
    for g in groups:
        n = g["n_readers"]
        confs = [m["conf"] for m in g["members"]]
        firm = n == N_SEALERS or (n == 2 and all(c == CONF_FIRM for c in confs))
        for m in g["members"]:
            in_seal[m["reader"]] += 1
        letters.append(
            {
                "ch": g["ch"],
                "x": float(g["x"]),
                "y": float(g["y"]),
                "firm": bool(firm),
                "n_sealers": n,
                "sealers": [m["reader"] for m in g["members"]],
            }
        )
    per = {}
    for sid in sorted(sealer_outputs):
        namings = sealer_outputs[sid]
        unknown = sum(1 for n in namings if normalize_letter(n.get("ch")) is None)
        per[sid] = {
            "n_named": len(namings),
            "n_unknown": unknown,
            "n_in_seal": in_seal[sid],
            "n_firm_named": sum(1 for n in namings if n.get("conf") == CONF_FIRM),
        }
    stats = {
        "n_sealers": N_SEALERS,
        "radius": float(radius),
        "n_letters": len(letters),
        "n_firm": sum(1 for l in letters if l["firm"]),
        "n_tentative": sum(1 for l in letters if not l["firm"]),
        "n_agree_3": sum(1 for l in letters if l["n_sealers"] == 3),
        "n_agree_2": sum(1 for l in letters if l["n_sealers"] == 2),
        "per_sealer": per,
    }
    return letters, stats


# --------------------------------------------------------------------------- identity-shuffle null (G)


def identity_shuffle_null(
    namings_by_reader: Mapping[str, Sequence[Mapping[str, Any]]],
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SHUFFLE_SEED_DEFAULT,
    radius: float = CONSENSUS_RADIUS,
    min_readers: int = CONSENSUS_MIN_READERS,
) -> dict:
    """SG 1d: shuffle identities within each reader (positions fixed), recount agreement.

    Unknown namings are dropped first.  RNG: ``np.random.default_rng(seed)``; for each
    permutation j, for each reader in sorted-id order, ``rng.permutation`` of that
    reader's kinds.  p = (1 + #{null >= observed}) / (1 + N), exact.
    """
    _check_min_readers(min_readers)
    if isinstance(n_perm, bool) or not isinstance(n_perm, int) or n_perm < 1:
        raise ValueError("n_perm must be an int >= 1")
    prep = _Prepared(namings_by_reader)
    ea, eb = prep.edges(radius)
    observed = _count(*_greedy(prep, prep.kinds, ea, eb, radius), min_readers)
    slices = []
    for p in range(len(prep.reader_ids)):
        idx = np.flatnonzero(prep.rpos == p)
        if idx.size:
            slices.append((int(idx[0]), int(idx[-1]) + 1))
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_perm):
        kinds = prep.kinds.copy()
        for s, e in slices:
            kinds[s:e] = rng.permutation(prep.kinds[s:e])
        null.append(_count(*_greedy(prep, kinds, ea, eb, radius), min_readers))
    p = Fraction(1 + sum(1 for v in null if v >= observed), 1 + n_perm)
    return {
        "observed": observed,
        "null": null,
        "p": p,
        "n_perm": n_perm,
        "seed": seed,
        "radius": float(radius),
        "min_readers": min_readers,
    }


# --------------------------------------------------------------------------- SG 1c (H)


def _num(v: float) -> int | float:
    v = float(v)
    return int(v) if v.is_integer() else v


def sg1c_evaluate(agreed_count: float, null_tile_agreed_counts: Sequence[float]) -> dict:
    """SG 1c against an empirical null of tiles; returns the decision with its numbers."""
    if isinstance(agreed_count, bool) or not isinstance(agreed_count, (int, float)) or not math.isfinite(agreed_count):
        raise ValueError("agreed_count must be a finite number")
    null = np.asarray(list(null_tile_agreed_counts), dtype=float)
    if null.ndim != 1 or not np.isfinite(null).all():
        raise ValueError("null_tile_agreed_counts must be a flat list of finite numbers")
    res = {"n_null": int(null.size), "p99": None, "max_null": None, "margin": None, "agreed": _num(agreed_count)}
    if null.size < SG1C_MIN_NULL_TILES:
        return {**res, "pass": False, "reason": "insufficient_null_tiles"}
    p99 = float(np.percentile(null, SG1C_PERCENTILE, method=SG1C_PERCENTILE_METHOD))
    mx = float(null.max())
    margin = float(agreed_count) - p99
    ok = margin >= SG1C_MARGIN and float(agreed_count) > mx
    reason = "pass" if ok else ("margin_below_threshold" if margin < SG1C_MARGIN else "not_above_null_max")
    return {**res, "p99": _num(p99), "max_null": _num(mx), "margin": _num(margin), "pass": bool(ok), "reason": reason}


def sg1c_pass(agreed_count: float, null_tile_agreed_counts: Sequence[float]) -> bool:
    """True iff >= 40 null tiles, agreed - P99(higher) >= 10 and agreed > max(null)."""
    return sg1c_evaluate(agreed_count, null_tile_agreed_counts)["pass"]


# --------------------------------------------------------------------------- discovery (I)


def discovery(
    text_order_namings_by_reader: Mapping[str, Sequence[Mapping[str, Any]]],
    nontext_order_namings_by_reader: Mapping[str, Sequence[Mapping[str, Any]]],
    k: int = DISCOVERY_K_DEFAULT,
) -> dict:
    """Pass iff agreed(text) >= k and agreed(non-text) <= 1 (>= 2 of 3 readers, 150 px)."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        raise ValueError("k must be a non-negative int")
    for obj in (text_order_namings_by_reader, nontext_order_namings_by_reader):
        if not isinstance(obj, Mapping) or len(obj) != DISCOVERY_N_READERS:
            raise ValueError(f"discovery needs exactly {DISCOVERY_N_READERS} readers per order")
    if sorted(text_order_namings_by_reader) != sorted(nontext_order_namings_by_reader):
        raise ValueError("text and non-text namings must come from the same readers")
    at = len(agreed_letters(text_order_namings_by_reader, CONSENSUS_RADIUS, CONSENSUS_MIN_READERS))
    an = len(agreed_letters(nontext_order_namings_by_reader, CONSENSUS_RADIUS, CONSENSUS_MIN_READERS))
    return {
        "pass": bool(at >= k and an <= DISCOVERY_NONTEXT_MAX),
        "agreed_text": at,
        "agreed_nontext": an,
        "k": k,
        "nontext_max": DISCOVERY_NONTEXT_MAX,
        "radius": CONSENSUS_RADIUS,
        "min_readers": CONSENSUS_MIN_READERS,
    }
