# Provenance: Project HERCULES | [id removed]
"""DECL-P4-26-A2 item 7 as made exact by DECL-P4-26-A2-A2: attribution of positive VERSO census windows of w010-027
to their facing source on the adjacent OUTER winding. Geometry and numbers only.

usage: attrib_verso.py <census_result.json> <facing_dir> <offset_corr_result.json> <out.json>
  census_result.json: post_census output (key 'own_vw_a' -> 'positive' = [[[r, c], count], ...]).
For each positive window (tiles r..r+1 x c..c+1) all finite OUTER facing cells of its 4 tiles (32 x 32 each) are mapped
to the source tile (floor(row / T), floor(col / T)) of the recto canvas. Fractions of cells in the title slot
(c14-c19, any row), in the known-text set (r0-r1 x c9-c13) and elsewhere are reported, plus the max show-through r
of the 4 tiles. Class: SLOT if slot fraction >= 0.5 and max show-through < 0.3; CONTROL if text fraction >= 0.5;
SLOT_SHOWTHROUGH if slot fraction >= 0.5 but show-through >= 0.3; NO_GEOMETRY if < 100 finite cells; else OTHER.
SLOT windows go to tools/p4/win_candidates.py (<= 3 x 3 tile footprint, <= 3 candidates)."""
import json, os, sys
import numpy as np

T = 8343
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main(census, facing_dir, oc, out):
    C = json.load(open(census)); O = json.load(open(oc)); st = O.get('show_through_r', {})
    pos = [((int(rc[0]), int(rc[1])), cnt) for rc, cnt in C['own_vw_a']['positive']]
    rows = []
    for (r, c), cnt in pos:
        cells = []
        for rr, cc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)):
            p = os.path.join(facing_dir, f'r{rr}_c{cc}.npz')
            if os.path.exists(p):
                F = np.load(p)['outer'].reshape(-1, 2)
                cells.append(F[np.all(np.isfinite(F), 1)])
        F = np.concatenate(cells) if cells else np.zeros((0, 2))
        sr, sc = np.floor(F[:, 0] / T).astype(int), np.floor(F[:, 1] / T).astype(int)
        n = len(F)
        slot = float(((sc >= 14) & (sc <= 19)).mean()) if n else 0.0
        text = float(((sr <= 1) & (sr >= 0) & (sc >= 9) & (sc <= 13)).mean()) if n else 0.0
        shw = [st.get(f'r{rr}_c{cc}') for rr, cc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))]
        shw = [x for x in shw if x is not None]; mx = max(shw) if shw else None
        if n < 100: cls = 'NO_GEOMETRY'
        elif slot >= 0.5 and mx is not None and mx < 0.3: cls = 'SLOT'
        elif slot >= 0.5: cls = 'SLOT_SHOWTHROUGH'
        elif text >= 0.5: cls = 'CONTROL'
        else: cls = 'OTHER'
        src = {}
        for a, b in zip(sr, sc): src[f'r{a}_c{b}'] = src.get(f'r{a}_c{b}', 0) + 1
        rows.append({'window': [r, c], 'count': cnt, 'n_cells': n, 'slot_frac': round(slot, 3), 'text_frac': round(text, 3),
                     'max_show_through_r': mx, 'class': cls, 'source_tiles_top3': sorted(src.items(), key=lambda kv: -kv[1])[:3]})
    from win_candidates import candidates
    pw = {tuple(x['window']): x['count'] for x in rows if x['class'] == 'SLOT'}
    cands, over, col = candidates(pw)
    res = {'rule': 'DECL-P4-26-A2 item 7 + A2-A2', 'windows': rows,
           'counts': {k: sum(1 for x in rows if x['class'] == k) for k in ('SLOT', 'SLOT_SHOWTHROUGH', 'CONTROL', 'OTHER', 'NO_GEOMETRY')},
           'candidates': [(x['windows'], x['rows'], x['cols'], x['max_count']) for x in cands],
           'over_cap': [(x['windows'], x['max_count']) for x in over], 'column_like': [(x['rows'], x['cols'], len(x['windows'])) for x in col]}
    json.dump(res, open(out, 'w'), indent=1, default=str)
    print(json.dumps({'counts': res['counts'], 'candidates': res['candidates'], 'over_cap': len(res['over_cap'])}, default=str))


if __name__ == '__main__':
    main(*sys.argv[1:])
