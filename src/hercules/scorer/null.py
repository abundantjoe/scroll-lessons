# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec E: identity-permutation null, arm statistics, per-arm p and max-T p_max.

Null model: for a window, the seal's letter IDENTITIES are permuted over the fixed seal
positions; each reader's C_all is recomputed against the permuted seal.  Permutation j of
window W is a pure function of (seed, W, j) (see ``window_permutations``), so every arm
and every reader sees the same permuted seal at index j, as max-T requires.

All p-values and arm statistics are computed in exact integer / rational arithmetic
(``fractions.Fraction``) so that ties are decided exactly and results are bit-stable.
"""

from __future__ import annotations

import hashlib
import math
from fractions import Fraction
from typing import Mapping

import numpy as np

from .constants import NULL_BLOCK, WINDOW_HASH_WORDS
from .matching import distance_matrix, max_matching_size


def window_seed_sequence(seed: int, window_id: str) -> np.random.SeedSequence:
    """SeedSequence([seed, w0, w1, w2, w3]) with w_i little-endian uint32 words of sha256(window_id)."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative int")
    digest = hashlib.sha256(window_id.encode("utf-8")).digest()
    words = [int.from_bytes(digest[4 * i : 4 * i + 4], "little") for i in range(WINDOW_HASH_WORDS)]
    return np.random.SeedSequence([seed, *words])


def window_permutations(n_seal: int, n_perm: int, seed: int, window_id: str) -> np.ndarray:
    """(n_perm, n_seal) int64 array; row j is permutation j of the seal indices of this window.

    Drawn sequentially with ``rng.permutation`` from
    ``np.random.default_rng(window_seed_sequence(seed, window_id))``, so the first k rows
    do not depend on n_perm.
    """
    rng = np.random.default_rng(window_seed_sequence(seed, window_id))
    perms = np.zeros((n_perm, n_seal), dtype=np.int64)
    if n_seal == 0:
        return perms
    for j in range(n_perm):
        perms[j] = rng.permutation(n_seal)
    return perms


def null_match_counts(
    named_xy: np.ndarray,
    named_kinds: np.ndarray,
    seal_xy: np.ndarray,
    seal_kinds: np.ndarray,
    perms: np.ndarray,
    radius: float,
) -> np.ndarray:
    """C_all of one reader panel against each permuted seal.

    Permutation j assigns kind ``seal_kinds[perms[j, i]]`` to seal position i.  Returns an
    int64 array of length ``len(perms)``.  Uses exactly the matching rule of
    ``matching.match_letters`` (same distances and allowed pairs; the maximum matching size
    is unique, so the cardinality-only solver gives exactly the count match_letters gives).
    """
    n_perm = perms.shape[0]
    out = np.zeros(n_perm, dtype=np.int64)
    if len(named_kinds) == 0 or len(seal_kinds) == 0 or n_perm == 0:
        return out
    dist = distance_matrix(np.asarray(named_xy, float), np.asarray(seal_xy, float))
    near = dist <= radius
    rows = np.flatnonzero(near.any(axis=1))
    cols = np.flatnonzero(near.any(axis=0))
    if rows.size == 0:
        return out
    near = near[np.ix_(rows, cols)]
    nk = np.asarray(named_kinds)[rows]
    permuted = np.asarray(seal_kinds)[perms][:, cols]  # (n_perm, c): kind at kept position
    for start in range(0, n_perm, NULL_BLOCK):
        pk = permuted[start : start + NULL_BLOCK]
        allowed = near[None, :, :] & (nk[None, :, None] == pk[:, None, :])
        counts = allowed.sum(axis=(1, 2)).astype(np.int64)
        simple = (allowed.sum(axis=2) <= 1).all(axis=1) & (allowed.sum(axis=1) <= 1).all(axis=1)
        for b in np.flatnonzero(~simple):
            counts[b] = max_matching_size(allowed[b])
        out[start : start + len(pk)] = counts
    return out


def permutation_p(observed_total: int, null_totals: np.ndarray) -> Fraction:
    """(1 + #{null >= observed}) / (1 + N), exact."""
    null = np.asarray(null_totals)
    return Fraction(1 + int((null >= observed_total).sum()), 1 + len(null))


def arm_summed_mean_cnet(cnet_by_window: Mapping[str, Mapping[str, float]]) -> float:
    """Sum over windows of the mean over readers of C_net.

    ``cnet_by_window[window_id][reader_id] = C_net``.  A window with no readers adds 0.
    Summation is order-independent (sorted keys, math.fsum).
    """
    means = []
    for w in sorted(cnet_by_window):
        vals = [float(cnet_by_window[w][r]) for r in sorted(cnet_by_window[w])]
        if vals:
            means.append(math.fsum(vals) / len(vals))
    return math.fsum(means)


def max_t_p(arm_stats: Mapping[str, tuple[int, np.ndarray, int]]) -> dict:
    """Family-wise (max-T) p over the arms of one decision.

    ``arm_stats[arm_id] = (observed_total, null_totals, n_readers)`` where
    ``observed_total`` = sum over (window, reader) of C_all, ``null_totals[j]`` = the same
    sum under permutation j (same j for every arm), and the arm statistic is
    total / n_readers (sum over windows of the mean over readers).  For each permutation
    the permuted statistic of arm a is (null_totals_a[j] - mean_j null_totals_a) / n_a and
    p_max = (1 + #{j : max_a permuted_a[j] >= max_a observed C_net_a}) / (1 + N).
    An arm with n_readers == 0 is identically 0 (observed and permuted).
    """
    if not arm_stats:
        raise ValueError("max_t_p needs at least one arm")
    arm_ids = sorted(arm_stats)
    lengths = {len(np.asarray(arm_stats[a][1])) for a in arm_ids}
    if len(lengths) != 1:
        raise ValueError("all arms must share the same number of permutations")
    (n_perm,) = lengths
    if n_perm == 0:
        raise ValueError("need at least one permutation")
    denoms = [arm_stats[a][2] if arm_stats[a][2] > 0 else 1 for a in arm_ids]
    lcm = math.lcm(*denoms)
    # Scaled integer statistic: X = (T * N - S) * (lcm / n) = C_net * N * lcm, exact.
    obs_scaled, null_scaled = [], []
    for a, d in zip(arm_ids, denoms):
        obs, null, n_r = arm_stats[a]
        null = np.asarray(null, dtype=np.int64)
        if n_r == 0:
            obs_scaled.append(0)
            null_scaled.append(np.zeros(n_perm, dtype=np.int64))
            continue
        s = int(null.sum())
        w = lcm // d
        bound = (max(abs(int(obs)), int(np.abs(null).max())) * n_perm + abs(s)) * w
        if bound >= 2**62:
            raise OverflowError("max-T statistic exceeds int64 range")
        obs_scaled.append((int(obs) * n_perm - s) * w)
        null_scaled.append((null * n_perm - s) * w)
    obs_max = max(obs_scaled)
    argmax = arm_ids[obs_scaled.index(obs_max)]
    null_max = np.max(np.vstack(null_scaled), axis=0)
    count = int((null_max >= obs_max).sum())
    return {
        "p_max": Fraction(1 + count, 1 + n_perm),
        "observed_max_c_net": Fraction(obs_max, n_perm * lcm),
        "argmax_arm": argmax,
        "count": count,
        "n_perm": n_perm,
    }
