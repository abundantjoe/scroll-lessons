# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-11 (P4-K) boundary candidates. Numbers only; no image is opened and no letter content is used
(only the census positive flags, tile geometry and labelled-adjacency flags).

usage: p4k_boundary.py <census_summary.json> <tile_winding.json> <strip> <select_in.json> <select_out.json>

tile_winding.json: per-tile radius from the umbilicus, as a list or dict of records with r, c and a radius field
(first of: radius_median_vox, radius_median, radius_vox, radius_mm, radius).
1. Direction: for each row with >= 3 tiles, Spearman rho of column vs radius; the median over the census rows
   decides: <= -0.5 -> inward = increasing column; >= +0.5 -> inward = decreasing column; else undetermined
   (no B-candidates; the output records why).
2. For each row of <strip> that has a census positive: c_last = the most inward positive column; B-candidates = the
   first 2 census tiles inward of c_last (in inward order) that are neither positive nor labelled-adjacent.
3. Output = select_in with B-candidates appended after its census candidates (role 'boundary'); cap 20 in total;
   'p4k' block records direction, rho per row and the rule.
"""
import json
import sys

import numpy as np

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
RFIELDS = ('radius_median_vox', 'radius_median', 'radius_vox', 'radius_mm', 'radius')
MAX_CAND = 20


def _rank(v):
    """Ranks with ties averaged."""
    v = np.asarray(v, float)
    order = np.argsort(v, kind='mergesort')
    r = np.empty(len(v))
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        r[order[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = _rank(x), _rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return float('nan')
    return float(np.corrcoef(rx, ry)[0, 1])


def load_radius(path):
    w = json.load(open(path))
    recs = w.get('tiles', w) if isinstance(w, dict) else w
    if isinstance(recs, dict):
        recs = [dict(v, key=k) for k, v in recs.items()]
    out = {}
    for t in recs:
        f = next((f for f in RFIELDS if t.get(f) is not None), None)
        if f is None or t.get('r') is None or t.get('c') is None:
            continue
        out[(int(t['r']), int(t['c']))] = float(t[f])
    return out


def direction(radius, rows):
    rho = {}
    for r in rows:
        cs = sorted(c for (rr, c) in radius if rr == r)
        if len(cs) >= 3:
            rho[r] = spearman(np.array(cs, float), np.array([radius[(r, c)] for c in cs]))
    vals = [v for v in rho.values() if v == v]
    med = float(np.median(vals)) if vals else float('nan')
    d = 'increasing' if med <= -0.5 else 'decreasing' if med >= 0.5 else 'undetermined'
    return d, med, rho


def boundary(tiles, strip, d):
    rows = {}
    for u, t in tiles.items():
        if t['strip'] == strip:
            rows.setdefault(t['r'], []).append((t['c'], u, t))
    out = []
    for r in sorted(rows):
        cells = sorted(rows[r], reverse=(d == 'decreasing'))  # inward order
        pos_idx = [i for i, (c, u, t) in enumerate(cells) if t.get('positive')]
        if not pos_idx:
            continue
        got = 0
        for c, u, t in cells[max(pos_idx) + 1:]:
            if got == 2:
                break
            if not t.get('positive') and not t.get('labelled_adjacent'):
                out.append(dict(t, uuid=u, role='boundary'))
                got += 1
    return out


def main(summary, winding, strip, sel_in, sel_out):
    s = json.load(open(summary))
    tiles = s['tiles']
    pos = set(s['positive'])
    for u in tiles:
        tiles[u]['positive'] = u in pos
    radius = load_radius(winding)
    rows = sorted({t['r'] for t in tiles.values() if t['strip'] == strip})
    d, med, rho = direction(radius, rows)
    sel = json.load(open(sel_in))
    b = boundary(tiles, strip, d) if d != 'undetermined' else []
    have = {x['uuid'] for x in sel['candidates']}
    b = [x for x in b if x['uuid'] not in have]
    room = max(0, MAX_CAND - len(sel['candidates']))
    sel['candidates'] = sel['candidates'] + b[:room]
    sel['p4k'] = {'provenance': PROV, 'serves': 'RULES.md DECL-P4-11', 'strip': strip, 'direction_inward': d,
                  'median_rho': med, 'rho_per_row': {str(k): v for k, v in rho.items()},
                  'n_boundary': len(b), 'n_boundary_added': len(b[:room]),
                  'boundary': [{'uuid': x['uuid'], 'r': x['r'], 'c': x['c']} for x in b]}
    with open(sel_out, 'x') as fh:
        json.dump(sel, fh, indent=1)
    print(json.dumps({'direction_inward': d, 'median_rho': med, 'n_boundary_added': len(b[:room]),
                      'n_candidates_total': len(sel['candidates'])}))


if __name__ == '__main__':
    main(*sys.argv[1:6])
