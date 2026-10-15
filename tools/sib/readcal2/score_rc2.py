# Provenance: Project HERCULES | owner the owner | [id removed]
"""READCAL-2 scoring glue (task readcal2 item 4) on the unchanged deterministic scorer
hercules.scorer.score.score_decision (METRIC-HASH-0: C_net against the identity-permutation null, 5000 permutations,
seed 20260924, radius 250 canvas px; blank namings). No reader runs here; this is code plus synthetic tests.

Design (proposal logs/sib/readcal2/proposals/DECL-READCAL2.md):
  cell   = (arm, model, sigma), 3 fresh readers each; arms K_D2 (frozen control), EX, EXPL (placebo), MS, ROW,
           SIG2 (both-sigma key sheet, DECL-P4-2-A2);
           sigma in LADDER (0, 0.15, 0.30, 0.45, 0.60 mm); every reader reads all bank windows + 2 blanks of ONE cell.
  score  one score_decision per (model, sigma) over the 5 arms (bank windows + blanks) -> per-reader, per-window
         C_net and blank namings; arm value = summed-over-windows mean-over-readers C_net (score_decision's own).
  CHANCE per arm, computed (no extra reader): the same reader namings scored against the seal of the next bank
         window in id order (cyclic), i.e. score_decision with display maps re-pointed; C_all(CHANCE) at R250.
  sigma_crit per (arm, model): linear interpolation of the ladder C_net at 50 % of the sigma-0 C_net
         (interp_sigma_crit); the D1 discrete rule (largest ladder sigma >= 50 %) is reported beside it.
  contrast  arm X vs K_D2 (same model): T = sum over sigma in {0.30, 0.45} of (mean_X - mean_K) of per-reader summed
         C_net; exact reader-label permutation p (all C(6,3)^2 = 400 relabelings within the two sigma cells),
         one-sided. EX vs EXPL the same way (the priming control).
MS: a reader's namings from the 5 images of a window (overview scale 2 + quadrants scale 1) are mapped to canvas px
  and merged by rc2lib.ms_merge (same identity within 60 canvas px = one letter) into one synthetic single-image item
  at scale 1, origin 0 (so the scorer's half-pixel map is the identity), before score_decision.
ROW: the answer carries "rows" per item and a "row" index per letter; split_row_answer removes both (reported by
  row_letter_residuals) so the scorer sees a schema-valid answer.
"""
from __future__ import annotations

import itertools
import math
import os
import sys
from fractions import Fraction
from typing import Any, Mapping

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'src'))
import rc2lib as R  # noqa: E402
from hercules.scorer.constants import NONTEXT, TEXT  # noqa: E402
from hercules.scorer.score import radius_key, score_decision  # noqa: E402

R250 = radius_key(250.0)
ARMS = ('K_D2', 'EX', 'EXPL', 'MS', 'ROW', 'SIG2')
CONTRAST_SIGMAS = (0.30, 0.45)


# ------------------------------------------------------------------------------------------ answer preprocessing
def split_row_answer(answer: Mapping[str, Any]) -> tuple[dict, dict]:
    """ROW answer -> (schema answer without 'rows' lists / 'row' fields, {item id: {'rows': [...], 'letters': [...]}})."""
    items, rows = [], {}
    for it in answer.get('items', []):
        left = dict(it['left'])
        rl = left.pop('row_lines', None)
        letters = []
        for l in left.get('letters', []):
            l2 = {k: v for k, v in l.items() if k != 'row'}
            letters.append(l2)
        rows[it['id']] = {'rows': rl or [], 'letters': [dict(l) for l in it['left'].get('letters', [])]}
        left['letters'] = letters
        items.append({'id': it['id'], 'left': left, 'right': it.get('right', {'rows': 'N', 'letters': []})})
    return {'items': items}, rows


def merge_ms_answer(answer: Mapping[str, Any], image_key: Mapping[str, Mapping[str, Any]]) -> tuple[dict, dict]:
    """MS answer (one single-image item per image uuid) -> one synthetic item per window with merged letters in
    canvas px. image_key[uuid] = {'window', 'part', 'scale', 'y0', 'x0'}. Returns (answer, {window: synthetic id})."""
    per_win: dict[str, list] = {}
    rows_y: dict[str, bool] = {}
    for it in answer.get('items', []):
        k = image_key.get(it['id'])
        if k is None:
            continue
        w = k['window']
        per_win.setdefault(w, [])
        rows_y[w] = rows_y.get(w, False) or it['left'].get('rows') == 'Y'
        for l in it['left'].get('letters', []):
            X, Y = R.image_to_canvas(float(l['x']), float(l['y']), float(k['scale']), float(k['x0']), float(k['y0']))
            b = l['box']
            x0b, y0b = R.image_to_canvas(float(b[0]), float(b[1]), float(k['scale']), float(k['x0']), float(k['y0']))
            x1b, y1b = R.image_to_canvas(float(b[2]), float(b[3]), float(k['scale']), float(k['x0']), float(k['y0']))
            per_win[w].append({'ch': l['ch'], 'x': X, 'y': Y, 'box': [x0b, y0b, x1b, y1b], 'conf': l['conf'],
                               'part': k['part']})
    items, ids = [], {}
    for w in sorted(per_win):
        merged = R.ms_merge(per_win[w])
        sid = f'ms::{w}'
        ids[w] = sid
        items.append({'id': sid, 'left': {'rows': 'Y' if rows_y[w] else 'N',
                                          'letters': [{k: m[k] for k in ('ch', 'x', 'y', 'box', 'conf')} for m in merged]},
                      'right': {'rows': 'N', 'letters': []}})
    return {'items': items}, ids


# ------------------------------------------------------------------------------------------ display maps
def single_maps(reader: str, item_to_window: Mapping[str, str], scale: float = 2.0) -> list[dict]:
    """K_D2-geometry single-image items: LEFT = text, scale 2, origin 0 (as D1 REF)."""
    return [{'reader_id': reader, 'item_id': iid, 'window_id': w, 'scale': scale, 'y0': 0.0, 'x0': 0.0,
             'side_order': [TEXT, NONTEXT]} for iid, w in sorted(item_to_window.items())]


def chance_maps(maps: list[dict], bank_windows: list[str]) -> list[dict]:
    """Re-point every bank-window item to the next bank window (cyclic, sorted ids); blank items dropped."""
    order = sorted(bank_windows)
    nxt = {w: order[(i + 1) % len(order)] for i, w in enumerate(order)}
    return [dict(m, window_id=nxt[m['window_id']]) for m in maps if m['window_id'] in nxt]


# ------------------------------------------------------------------------------------------ statistics
def interp_sigma_crit(ladder: Mapping[float, float]) -> dict:
    """50 % crossing of the ladder C_net, linearly interpolated between the last sigma >= 50 % and the next.
    {'sigma_crit': float | None, 'censored': bool, 'discrete': D1 rule value}."""
    base = ladder.get(0.0)
    s = sorted(ladder)
    if base is None or base <= 0:
        return {'sigma_crit': None, 'censored': False, 'discrete': None, 'half': None}
    half = base / 2.0
    ok = [x for x in s if ladder[x] >= half]
    discrete = max(ok)
    for a, b in zip(s, s[1:]):
        if ladder[a] >= half > ladder[b]:
            t = (ladder[a] - half) / (ladder[a] - ladder[b])
            return {'sigma_crit': a + t * (b - a), 'censored': False, 'discrete': discrete, 'half': half}
    return {'sigma_crit': s[-1], 'censored': True, 'discrete': discrete, 'half': half}


def reader_summed(result: Mapping[str, Any], arm: str, field: str = 'C_net', bank_only: bool = True) -> dict:
    """{reader: sum over the arm's (non-blank) windows of the per-reader field}."""
    a = result['arms'][arm]
    out = {}
    for r in a['readers_scored']:
        tot = 0.0
        for w in a['windows']:
            wo = result['windows'][w]
            if bank_only and wo['blank']:
                continue
            rec = wo['readers'].get(r)
            if rec is not None and rec['status'] in ('scored', 'missing_item'):
                tot += rec[field] if field != 'C_all' else rec['C_all'][R250]
        out[r] = tot
    return out


def reader_blank_namings(result: Mapping[str, Any], arm: str) -> dict:
    a = result['arms'][arm]
    return {r: sum(result['windows'][w]['readers'][r]['blank_namings'] for w in a['windows']
                   if result['windows'][w]['blank'] and r in result['windows'][w]['readers'])
            for r in a['readers_scored']}


def permutation_contrast(cells_x: list[list[float]], cells_k: list[list[float]]) -> dict:
    """One-sided exact permutation test of T = sum_cells (mean X - mean K) over all within-cell relabelings.
    cells_*: per cell (sigma), the per-reader values. Returns {'T', 'p' (Fraction str), 'p_float', 'n_perm'}."""
    def T(xs, ks):
        return sum(sum(x) / len(x) - sum(k) / len(k) for x, k in zip(xs, ks))
    obs = T(cells_x, cells_k)
    options = []
    for x, k in zip(cells_x, cells_k):
        pool = list(x) + list(k)
        n = len(x)
        opts = []
        for comb in itertools.combinations(range(len(pool)), n):
            s = set(comb)
            opts.append(([pool[i] for i in comb], [pool[i] for i in range(len(pool)) if i not in s]))
        options.append(opts)
    ge = tot = 0
    for choice in itertools.product(*options):
        t = T([c[0] for c in choice], [c[1] for c in choice])
        tot += 1
        ge += t >= obs - 1e-12
    p = Fraction(ge, tot)
    return {'T': obs, 'p': f'{p.numerator}/{p.denominator}', 'p_float': float(p), 'n_perm': tot}


# ------------------------------------------------------------------------------------------ outcome
def arm_outcome(model_res: Mapping[str, Any], arm: str, control: str = 'K_D2', placebo: str | None = None,
                sigma_gain_mm: float = 0.075, alpha: float = 0.05, blank_tol: float = 1.0 / 3.0,
                chance_tol: float = 1.0) -> dict:
    """Declared bars for one arm vs the control within one model (see DECL-READCAL2 proposal, item 6).
    model_res = {'ladder': {arm: {sigma: summed C_net}}, 'reader_cnet': {arm: {sigma: [per-reader summed C_net]}},
                 'blank_mean': {arm: mean blank namings per reader (all sigmas)}, 'chance_c_all': {arm: summed mean},
                 optional 'precision': {arm: {sigma: C_all(R250) / namings}}}"""
    sc_x = interp_sigma_crit(model_res['ladder'][arm])
    sc_k = interp_sigma_crit(model_res['ladder'][control])
    con = permutation_contrast([model_res['reader_cnet'][arm][s] for s in CONTRAST_SIGMAS],
                               [model_res['reader_cnet'][control][s] for s in CONTRAST_SIGMAS])
    checks = {
        'sigma_crit_gain': (sc_x['sigma_crit'] is not None and sc_k['sigma_crit'] is not None
                            and sc_x['sigma_crit'] >= sc_k['sigma_crit'] + sigma_gain_mm),
        'c_net_030_not_below': sum(model_res['reader_cnet'][arm][0.30]) / 3 >= sum(model_res['reader_cnet'][control][0.30]) / 3,
        'c_net_045_not_below': sum(model_res['reader_cnet'][arm][0.45]) / 3 >= sum(model_res['reader_cnet'][control][0.45]) / 3,
        'contrast_p_lt_alpha': con['p_float'] < alpha,
        'blank_namings_not_up': model_res['blank_mean'][arm] <= model_res['blank_mean'][control] + blank_tol,
        'chance_c_all_not_up': model_res['chance_c_all'][arm] <= model_res['chance_c_all'][control] + chance_tol,
    }
    if 'precision' in model_res:
        checks['precision_not_down'] = all(model_res['precision'][arm][s] >= model_res['precision'][control][s] - 0.10
                                           for s in CONTRAST_SIGMAS)
    out = {'arm': arm, 'sigma_crit': sc_x, 'sigma_crit_control': sc_k, 'contrast_vs_control': con, 'checks': checks}
    if placebo is not None:
        sc_p = interp_sigma_crit(model_res['ladder'][placebo])
        con_p = permutation_contrast([model_res['reader_cnet'][arm][s] for s in CONTRAST_SIGMAS],
                                     [model_res['reader_cnet'][placebo][s] for s in CONTRAST_SIGMAS])
        gain_x = (sc_x['sigma_crit'] or 0) - (sc_k['sigma_crit'] or 0)
        gain_p = (sc_p['sigma_crit'] or 0) - (sc_k['sigma_crit'] or 0)
        checks['gain_exceeds_placebo_gain'] = gain_x > gain_p
        checks['contrast_vs_placebo_p_lt_alpha'] = con_p['p_float'] < alpha
        out['placebo'] = {'sigma_crit': sc_p, 'contrast': con_p, 'gain_arm': gain_x, 'gain_placebo': gain_p}
    out['outcome'] = 'GAIN_PENDING_REPLICATION' if all(checks.values()) else 'NO_GAIN'
    return out


def score_cell(arms: Mapping[str, Mapping[str, Any]], seals: Mapping[str, Any], n_perm: int = 5000,
               seed: int = 20260924, decision_id: str = 'READCAL2') -> tuple[dict, dict]:
    """One (model, sigma) decision. arms[arm] = {'readers': {rid: answer}, 'maps': [display map dicts],
    'windows': [...]} with answers already preprocessed (MS merged, ROW split). Returns (result, chance_result)."""
    decl = {'decision_id': decision_id, 'arms': []}
    outs, maps = {}, []
    decl_c = {'decision_id': decision_id + '-CHANCE', 'arms': []}
    maps_c = []
    bank = sorted(w for w in seals if not seals[w]['blank'])
    for arm, a in sorted(arms.items()):
        decl['arms'].append({'arm_id': arm, 'readers': sorted(a['readers']), 'windows': sorted(a['windows'])})
        decl_c['arms'].append({'arm_id': f'CHANCE_{arm}', 'readers': sorted(a['readers']), 'windows': bank})
        outs.update(a['readers'])
        maps += a['maps']
        maps_c += chance_maps(a['maps'], bank)
    res = score_decision(decl, seals, outs, maps, n_perm=n_perm, seed=seed)
    keep = {(m['reader_id'], m['item_id']) for m in maps_c}
    outs_c = {r: {'items': [it for it in a['items'] if (r, it['id']) in keep]} for r, a in outs.items()}
    res_c = score_decision(decl_c, seals, outs_c, maps_c, n_perm=max(1, min(n_perm, 200)), seed=seed)
    return res, res_c


def holm(pvals: Mapping[str, float], alpha: float = 0.05) -> dict:
    """Holm step-down over a family {name: p}: {name: {'p', 'threshold', 'reject'}} (ties by name)."""
    order = sorted(pvals, key=lambda k: (pvals[k], k))
    m = len(order)
    out, stop = {}, False
    for i, k in enumerate(order):
        thr = alpha / (m - i)
        rej = (not stop) and pvals[k] <= thr
        stop = stop or not rej
        out[k] = {'p': pvals[k], 'threshold': thr, 'reject': rej}
    return out
