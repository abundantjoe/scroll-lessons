# Provenance: Project HERCULES | owner the owner | [id removed]
"""Sensitivity grouping (not the primary): task-rule SAME pairs plus pairs that are SAME after local
offset removal under a strict criterion (overlap_offset.py): within-cell MAD <= 0.8 vox and
>= 20000 residual points within 2 vox, in either direction. Writes sensitivity_units.json (S01..)."""
import json
L = '/home/user/dominion/logs/sib/reg0009b'
o = json.load(open(f'{L}/overlap_offset_frame9.json')); P = json.load(open(f'{L}/overlap_frame9.json'))
segs = sorted(s for u in P['units'] for s in u['segments'])
strict = lambda x: bool(x) and x['same_after_offset'] and x['cell_mad_median'] <= 0.8 and (x['resid_counts'][0] + x['resid_counts'][1]) >= 20000
par = {s: s for s in segs}
def f(x):
    while par[x] != x: x = par[x]
    return x
edges = []
for p in o['pairs']:
    st = strict(p['ab']) or strict(p['ba'])
    if p['same_rule'] or st: par[f(p['a'])] = f(p['b'])
    if st and not p['same_rule']: edges.append([p['a'], p['b']])
U = {}
for s in segs: U.setdefault(f(s), []).append(s)
U = sorted((sorted(v) for v in U.values()), key=lambda v: (-len(v), v[0]))
res = [dict(unit=f'S{k+1:02d}', segments=u) for k, u in enumerate(U)]
json.dump(res, open(f'{L}/sensitivity_units.json', 'w'), indent=1)
json.dump(dict(added_pairs=edges, n_added=len(edges)), open(f'{L}/sensitivity_added_pairs.json', 'w'), indent=1)
print([[s[:14] for s in u['segments']] for u in res], 'added', len(edges))
