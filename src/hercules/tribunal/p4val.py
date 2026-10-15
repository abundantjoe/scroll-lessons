# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4 anti-hallucination validation (orchestrator dispatch 2026-09-26 18:48Z; channels P4-L DECL-P4-12
and P4-O DECL-P4-14). The prize asks to "demonstrate the letters and words are not hallucinated -
for example by validating on a held-out region with known ground-truth".

1. ``known_text_windows``: which strip-a tiles hold the published final columns, from numbers only
   (census profile, column pitch, strip join); UNCERTAIN, so it returns candidate column windows.
2. ``score_known_text``: reader namings on known-text tiles vs the published line text. Letter identity
   and position agreement: reader letters are grouped into lines (by y) and ordered by x; each reader
   line is aligned (Smith-Waterman, identity matches only) to a published line; lines map
   monotonically (top to bottom) with at most ``max_line_skip`` skipped published lines between
   consecutive matched reader lines. The statistic is the matched-letter count M, maximised over the
   candidate columns. Nulls: the same statistic against letter-shuffled published text (each column's
   visible letters permuted across its line slots, keeping line lengths and letter frequencies), and
   against identity-shuffled reader namings (positions kept). Restored letters (inside [ ]) are never
   targets. Runs on decrypted answers that only the orchestrator holds; this module never decrypts.
3. P4-L tile checks: manifest checks and a bit-exact pixel verifier for the declared display
   clip(255 (max - T_mid) / (T_hi - T_mid)) of the slab maximum, with planted faults.
"""

from __future__ import annotations

import json
import math
import unicodedata
from typing import Any, Mapping, Sequence

import numpy as np

from hercules.scorer.letters import normalize_letter

from . import tiles as TL

# ----------------------------------------------------------------------------- published text

RESTORE_OPEN, RESTORE_CLOSE = "[", "]"
IGNORED = set("()<>{}⟦⟧⟨⟩'’‘`´·.,:;-–—|/\\ 0123456789" + "†‡")
_UP = {chr(c): chr(c).upper() for c in range(0x3B1, 0x3CA)}
_UP.update({"ς": "Σ", "ϲ": "Ϲ"})  # final sigma, lunate small sigma


def normalize_published_line(line: str) -> list[tuple[str, bool]]:
    """Published (edited) line -> [(kind, visible)]. Diacritics and underdots are removed (an
    underdotted letter is still a physically visible trace, so visible=True); letters inside [ ]
    are editorial restorations (visible=False, never scoring targets); editorial marks, punctuation,
    spaces and numbers are dropped; characters that are not Greek letters are dropped."""
    out, inside = [], False
    for ch in line:
        if ch == RESTORE_OPEN:
            inside = True
            continue
        if ch == RESTORE_CLOSE:
            inside = False
            continue
        if ch in IGNORED:
            continue
        base = "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))
        if not base:
            continue
        base = _UP.get(base, base.upper())
        if base == "Σ":
            base = "Ϲ"
        k = normalize_letter(base)
        if k is not None:
            out.append((k, not inside))
    return out


def normalize_column(lines: Sequence[str]) -> list[list[tuple[str, bool]]]:
    return [normalize_published_line(s) for s in lines]


# ----------------------------------------------------------------------------- reader lines

def reader_lines(letters: Sequence[Mapping[str, Any]], line_tol_frac: float = 0.6) -> list[list[dict]]:
    """Group a reader's letters (displayed-image coordinates, tile unrotated) into lines by y; a new
    line starts where the y gap exceeds line_tol_frac x the median box height. Unknown kinds dropped."""
    L = []
    for l in letters:
        k = normalize_letter(l.get("ch"))
        if k is None:
            continue
        b = l.get("box") or [0, 0, 0, 0]
        L.append({"kind": k, "x": float(l["x"]), "y": float(l["y"]), "h": abs(float(b[3]) - float(b[1])) or 1.0,
                  "conf": l.get("conf")})
    if not L:
        return []
    L.sort(key=lambda d: d["y"])
    tol = line_tol_frac * float(np.median([d["h"] for d in L]))
    lines, cur = [], [L[0]]
    for d in L[1:]:
        if d["y"] - np.mean([e["y"] for e in cur]) > tol:
            lines.append(cur)
            cur = [d]
        else:
            cur.append(d)
    lines.append(cur)
    return [sorted(ln, key=lambda d: d["x"]) for ln in lines]


# ----------------------------------------------------------------------------- alignment

MATCH, MISMATCH, GAP = 2, -1, -1


def sw_matches(a: Sequence[str], b: Sequence[tuple[str, bool]]) -> int:
    """Smith-Waterman local alignment of reader kinds ``a`` against published (kind, visible) ``b``;
    returns the number of identity matches on the best-scoring local alignment. Restored letters
    align only as mismatches (never count)."""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0
    H = np.zeros((n + 1, m + 1))
    C = np.zeros((n + 1, m + 1), dtype=np.int64)
    best, bestc = 0.0, 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            hit = a[i - 1] == b[j - 1][0] and b[j - 1][1]
            d = H[i - 1, j - 1] + (MATCH if hit else MISMATCH)
            u = H[i - 1, j] + GAP
            left = H[i, j - 1] + GAP
            v = max(0.0, d, u, left)
            H[i, j] = v
            if v == 0:
                C[i, j] = 0
            elif v == d:
                C[i, j] = C[i - 1, j - 1] + (1 if hit else 0)
            elif v == u:
                C[i, j] = C[i - 1, j]
            else:
                C[i, j] = C[i, j - 1]
            if v > best or (v == best and C[i, j] > bestc):
                best, bestc = v, int(C[i, j])
    return bestc


def column_matches(rlines: Sequence[Sequence[str]], column: Sequence[Sequence[tuple[str, bool]]],
                   max_line_skip: int = 3) -> tuple[int, list]:
    """Monotone line mapping maximising total matches: reader line i -> published line j, increasing in
    both, with at most ``max_line_skip`` published lines skipped between consecutive mapped lines
    (a reader line may stay unmapped). Returns (M, [(i, j, matches)])."""
    R, P = len(rlines), len(column)
    if R == 0 or P == 0:
        return 0, []
    S = np.array([[sw_matches(rlines[i], column[j]) for j in range(P)] for i in range(R)])
    NEG = -1
    best = np.full((R, P), NEG, dtype=np.int64)  # best total ending with reader i mapped to published j
    prev = {}
    for i in range(R):
        for j in range(P):
            if S[i, j] == 0:
                continue
            cand, arg = S[i, j], None
            for i2 in range(i):
                for j2 in range(max(0, j - 1 - max_line_skip), j):
                    if best[i2, j2] >= 0 and best[i2, j2] + S[i, j] > cand:
                        cand, arg = best[i2, j2] + S[i, j], (i2, j2)
            best[i, j] = cand
            prev[(i, j)] = arg
    if best.max() < 0:
        return 0, []
    i, j = np.unravel_index(int(np.argmax(best)), best.shape)
    path, node = [], (int(i), int(j))
    while node is not None:
        path.append((node[0], node[1], int(S[node])))
        node = prev[node]
    return int(best.max()), path[::-1]


def best_over_columns(rlines, columns: Mapping[str, Sequence], max_line_skip: int = 3) -> dict:
    res = {cid: column_matches(rlines, col, max_line_skip) for cid, col in columns.items()}
    if not res:
        return {"M": 0, "column": None, "path": []}
    cid = max(sorted(res), key=lambda c: res[c][0])
    return {"M": res[cid][0], "column": cid, "path": res[cid][1], "per_column": {c: v[0] for c, v in res.items()}}


def shuffle_column(col, rng):
    """Permute the visible letters of a column across its visible slots (restored slots kept)."""
    flat = [k for line in col for k, v in line if v]
    rng.shuffle(flat)
    it = iter(flat)
    return [[(next(it), True) if v else (k, False) for k, v in line] for line in col]


def score_known_text(reader_letters: Mapping[str, Sequence[Mapping[str, Any]]], columns_text: Mapping[str, Sequence[str]],
                     *, n_perm: int = 1000, seed: int = 20260926, max_line_skip: int = 3,
                     line_tol_frac: float = 0.6) -> dict:
    """reader_letters: reader_id -> letters on ONE known-text tile (displayed-image coords, unrotated);
    columns_text: candidate column id -> published lines. Returns per-reader and pooled M with the
    shuffled-text and reader-identity-shuffle nulls (paired permutations; p = (1 + #null >= obs)/(1 + n))."""
    cols = {c: normalize_column(t) for c, t in columns_text.items()}
    rng = np.random.default_rng(seed)
    RL = {r: [[d["kind"] for d in ln] for ln in reader_lines(ls, line_tol_frac)] for r, ls in reader_letters.items()}
    obs = {r: best_over_columns(rl, cols, max_line_skip) for r, rl in RL.items()}
    null_text = np.zeros((n_perm, len(RL)), dtype=np.int64)
    null_read = np.zeros((n_perm, len(RL)), dtype=np.int64)
    rids = sorted(RL)
    for p in range(n_perm):
        sc = {c: shuffle_column(col, rng) for c, col in cols.items()}
        for q, r in enumerate(rids):
            null_text[p, q] = best_over_columns(RL[r], sc, max_line_skip)["M"]
            flat = [k for ln in RL[r] for k in ln]
            perm = list(rng.permutation(flat)) if flat else []
            it = iter(perm)
            shuffled = [[next(it) for _ in ln] for ln in RL[r]]
            null_read[p, q] = best_over_columns(shuffled, cols, max_line_skip)["M"]
    out = {"readers": {}, "n_perm": n_perm, "seed": seed, "max_line_skip": max_line_skip,
           "columns": sorted(cols), "visible_letters": {c: sum(v for ln in col for _, v in ln) for c, col in cols.items()}}
    for q, r in enumerate(rids):
        M = obs[r]["M"]
        named = sum(len(ln) for ln in RL[r])
        out["readers"][r] = {"M": M, "named_known": named, "precision": (M / named) if named else math.nan,
                             "column": obs[r]["column"], "line_path": obs[r]["path"],
                             "p_text_shuffle": (1 + int((null_text[:, q] >= M).sum())) / (n_perm + 1),
                             "p_reader_shuffle": (1 + int((null_read[:, q] >= M).sum())) / (n_perm + 1)}
    Mtot = sum(v["M"] for v in out["readers"].values())
    out["pooled"] = {"M": Mtot, "p_text_shuffle": (1 + int((null_text.sum(1) >= Mtot).sum())) / (n_perm + 1),
                     "p_reader_shuffle": (1 + int((null_read.sum(1) >= Mtot).sum())) / (n_perm + 1),
                     "null_text_p99": float(np.percentile(null_text.sum(1), 99)) if n_perm else None}
    return out


# ----------------------------------------------------------------------------- known-text windows

def known_text_windows(census_letters: Sequence[Sequence[int | None]], *, pitch_tiles: int = 4,
                       null_max: int = 4) -> dict:
    """Numbers-only column-slot model of strip a from a census profile (rows x cols letter counts, None
    = rows N). Column minima (text-poor tile columns) mark intercolumns; the last text column is the
    innermost tile column whose text-like count (> null_max) holds in >= half of rows r0-r5; published
    columns numbered from the end (col -1 = last) map to slots of ``pitch_tiles`` stepping outward.
    Returns candidate windows with a +-1 tile-column tolerance (UNCERTAIN)."""
    A = np.array([[np.nan if v is None else v for v in row] for row in census_letters], dtype=float)
    rows = A[:6]
    textlike = (rows > null_max).sum(axis=0)
    ncol = A.shape[1]
    colmean = np.nanmean(np.where(np.isnan(A[:6]), 0, A[:6]), axis=0)
    last = int(max(c for c in range(ncol) if textlike[c] >= 3))
    inter = [c for c in range(1, ncol - 1) if colmean[c] < colmean[c - 1] and colmean[c] <= colmean[c + 1]]
    slots, c_hi = [], last
    k = 1
    while c_hi >= 0:
        c_lo = max(0, c_hi - (pitch_tiles - 2))
        slots.append({"col": -k, "tile_cols": list(range(c_lo, c_hi + 1)),
                      "tolerance_cols": list(range(max(0, c_lo - 1), min(ncol, c_hi + 2)))})
        c_hi -= pitch_tiles
        k += 1
    short_block = [c for c in range(last + 1, ncol) if np.nansum(A[:2, c] > null_max) >= 1]
    return {"last_text_col": last, "intercolumn_candidates": inter, "slots": slots,
            "short_block_cols_r0r1": short_block, "grade": "UNCERTAIN (census counts are unconfirmed reads)",
            "alternative": "if the r0-r1 block after the last full column is the short last column, "
                           "shift every published column number by one (col -1 -> the block)"}


# ----------------------------------------------------------------------------- P4-L tile checks

L2_DECLARED = {"T": 8343, "T_mid": 93, "T_hi": 203, "slab_slices": [48, 60], "slab_centre": 54, "side": 1068}


def check_l2_manifest(m: Mapping[str, Any], *, eligible: set | None = None,
                      declared: Mapping[str, Any] = L2_DECLARED) -> dict:
    """Numbers-only checks of a P4-L tile manifest against the declared geometry and display."""
    T = declared["T"]
    g = []

    def rec(name, ok, **d):
        g.append({"check": name, "passed": bool(ok), **d})

    th = m.get("thresholds", {})
    rec("thresholds", th.get("T_mid") == declared["T_mid"] and th.get("T_hi") == declared["T_hi"], got=th)
    sl = m.get("slab", {})
    rec("slab", list(sl.get("slices", [])) == declared["slab_slices"] and sl.get("centre") == declared["slab_centre"]
        and sl.get("n") == declared["slab_slices"][1] - declared["slab_slices"][0] + 1, got=sl)
    rec("display_rule", "T_mid" in str(m.get("display", "")) and "INTER_AREA" in str(m.get("display", ""))
        and f"{T} -> {declared['side']}" in str(m.get("display", "")), got=m.get("display"))
    tiles = m.get("tiles", [])
    seen, bad = set(), []
    for t in tiles:
        r, c = int(t["r"]), int(t["c"])
        f = []
        if (r, c) in seen:
            f.append("duplicate")
        seen.add((r, c))
        if list(t["canvas_rows"]) != [r * T, (r + 1) * T] or list(t["canvas_cols"]) != [c * T, (c + 1) * T]:
            f.append("origin_or_extent")
        if not (TL.READ_MIN_VALID <= float(t["valid_fraction"]) <= 1.0):
            f.append("valid_fraction")
        if eligible is not None and (r, c) not in eligible:
            f.append("not_eligible")
        if not str(t.get("file", "")).endswith(f"_r{r}_c{c}.png"):
            f.append("file_name_rc")
        if f:
            bad.append({"r": r, "c": c, "failed": f})
    rec("tiles", not bad, n=len(tiles), failing=bad)
    rec("manifest_flags", all(bool(v) for k, v in m.get("checks", {}).items() if k not in ("all_ref_eligible_built",)),
        flags=m.get("checks"))
    return {"passed": all(x["passed"] for x in g), "checks": g}


def l2_display(slab_max: np.ndarray, T_mid: float, T_hi: float) -> np.ndarray:
    v = 255.0 * (slab_max.astype(np.float64) - T_mid) / (T_hi - T_mid)
    return np.rint(np.clip(v, 0, 255)).astype(np.uint8)


def expected_l2_tile(stack: np.ndarray, valid: np.ndarray, r: int, c: int, T: int, slab: tuple[int, int],
                     T_mid: float, T_hi: float, side: int = 1068, rotation: int = 0) -> np.ndarray:
    """P4-L display tile: max over slab slices [s0, s1] (inclusive), declared window, 0 outside
    mesh-valid, INTER_AREA, keyed rotation."""
    mx = stack[slab[0]:slab[1] + 1].max(axis=0)
    return TL.expected_tile(l2_display(mx, T_mid, T_hi), valid, r, c, T, side, rotation)


def verify_l2_tile(tile, stack, valid, r, c, T, slab, T_mid, T_hi, side=1068, rotation=0) -> dict:
    exp = expected_l2_tile(stack, valid, r, c, T, slab, T_mid, T_hi, side, rotation)
    if tile.shape != exp.shape:
        return {"passed": False, "reason": "shape"}
    d = np.abs(tile.astype(np.int16) - exp.astype(np.int16))
    return {"passed": int(d.max()) <= TL.PIX_MAX_ABS and float(d.mean()) <= TL.PIX_MEAN_ABS,
            "max_abs": int(d.max()), "mean_abs": float(d.mean())}


def known_text_gate(census: Sequence[Mapping[str, Any]], cols=range(0, 9), min_frac: float = 0.30,
                    min_letters: int = 5) -> dict:
    """DECL-P4-12 item 2 / DECL-P4-14 item 3: >= 30 % of the non-blank known-text tiles (c0-c8) read as
    rows Y with >= 5 letters. ``census``: [{c, blank (bool), rows ('Y'/'N'), letters (int)}]."""
    pool = [t for t in census if int(t["c"]) in set(cols) and not t.get("blank")]
    hit = [t for t in pool if t.get("rows") == "Y" and int(t.get("letters", 0)) >= min_letters]
    frac = len(hit) / len(pool) if pool else 0.0
    return {"n_pool": len(pool), "n_hit": len(hit), "fraction": frac, "passed": bool(pool) and frac >= min_frac,
            "status": "informative" if (pool and frac >= min_frac) else "uninformative"}


# ----------------------------------------------------------------------------- P4-O (DECL-P4-14)

import re as _re  # noqa: E402

_HEX64 = _re.compile(r"\b[0-9a-f]{64}\b")
_YES = _re.compile(r"^\s*(yes|true)\b", _re.I)


def _ckpt_entries(prov: Mapping[str, Any]) -> dict:
    c = prov.get("checkpoints", {})
    if isinstance(c, list):
        return {str(e.get("checkpoint", e.get("name", i))): e for i, e in enumerate(c)}
    return dict(c)


def check_p4o_provenance(prov: Mapping[str, Any]) -> dict:
    """DECL-P4-14 item 1, fail closed: a checkpoint may be eligible only if it has a source URL, a
    64-hex weights sha256, quoted documentation, and no documented Paris 4 / Scroll 1 training data.
    Any entry marked eligible that lacks one of these, or that documents Paris 4 data, is a violation."""
    rows = []
    for name, e in _ckpt_entries(prov).items():
        text = json.dumps(e, ensure_ascii=False)
        elig = e.get("eligible") is True
        p4 = [v for k, v in e.items() if "paris4" in k.lower()]
        p4_yes = any((v is True) or (isinstance(v, str) and _YES.match(v)) for v in p4)
        p4_declared_no = any(v is False or (isinstance(v, str) and v.strip().lower().startswith("no")) for v in p4)
        has_sha = bool(_HEX64.search(str(e.get("weights_sha256", ""))))
        has_src = bool(e.get("source_url") or e.get("weights_url"))
        has_doc = bool(e.get("quoted_training_statement") or e.get("documentation") or e.get("card_sha256"))
        problems = []
        if elig and p4_yes:
            problems.append("eligible_but_paris4_documented")
        if elig and not p4_declared_no:
            problems.append("eligible_without_explicit_no_paris4")
        if elig and not has_sha:
            problems.append("eligible_without_weights_sha256")
        if elig and not has_src:
            problems.append("eligible_without_source")
        if elig and not has_doc:
            problems.append("eligible_without_documentation")
        rows.append({"checkpoint": name, "eligible": elig, "paris4_documented": p4_yes, "problems": problems,
                     "weights_sha256": (_HEX64.search(str(e.get("weights_sha256", ""))) or [None])[0]
                     if has_sha else None, "n_chars": len(text)})
    return {"passed": not any(r["problems"] for r in rows), "checkpoints": rows,
            "eligible_sha256": sorted(r["weights_sha256"] for r in rows if r["eligible"] and r["weights_sha256"])}


P4O_DECLARED = {"T": 8343, "side": 1068, "segment": "20260701183124-w010-027"}


def check_p4o_manifest(m: Mapping[str, Any], eligible_sha256: Sequence[str], *,
                       declared: Mapping[str, Any] = P4O_DECLARED) -> dict:
    """DECL-P4-14 item 2 (numbers only): strip-a grid (T 8343, origin (0, 0)), raw 0-255 prediction at
    1068 px, 0 outside mesh-valid; the checkpoint's weights sha256 must be an eligible one; the
    resampling to the model's native voxel must be recorded; tiles checked as for P4-L."""
    g = []

    def rec(name, ok, **d):
        g.append({"check": name, "passed": bool(ok), **d})

    ck = str(m.get("checkpoint_sha256", m.get("weights_sha256", "")))
    rec("checkpoint_eligible", ck in set(eligible_sha256), checkpoint_sha256=ck)
    rec("segment", m.get("segment") == declared["segment"], got=m.get("segment"))
    disp = str(m.get("display", ""))
    rec("display_raw", ("raw" in disp or "0-255" in disp) and "INTER_AREA" in disp and "T_mid" not in disp, got=disp)
    rec("native_resampling_recorded", bool(m.get("native_voxel_um") or m.get("resampling")), got=m.get("resampling"))
    T = declared["T"]
    bad, seen = [], set()
    for t in m.get("tiles", []):
        r, c = int(t["r"]), int(t["c"])
        f = []
        if (r, c) in seen:
            f.append("duplicate")
        seen.add((r, c))
        if list(t["canvas_rows"]) != [r * T, (r + 1) * T] or list(t["canvas_cols"]) != [c * T, (c + 1) * T]:
            f.append("origin_or_extent")
        if not (TL.READ_MIN_VALID <= float(t["valid_fraction"]) <= 1.0):
            f.append("valid_fraction")
        if not str(t.get("file", "")).endswith(f"_r{r}_c{c}.png"):
            f.append("file_name_rc")
        if f:
            bad.append({"r": r, "c": c, "failed": f})
    rec("tiles", not bad and bool(m.get("tiles")), n=len(m.get("tiles", [])), failing=bad)
    return {"passed": all(x["passed"] for x in g), "checks": g}
