# Provenance: Project HERCULES | owner the owner | [id removed]
"""Registry-extension proposal for 0009B DEV windows (DECL-DEVLOOP-A1 item 7; orchestrator ruling
2026-09-26 05:59Z: clearance 144 vox point-to-surface in the native unit of the volume where the KTLB-M
windows are defined = 2.401 um). Primary: exclusion set ALL76 (every dense KTLB-M candidate window),
threshold 173 2.4-um vox = 144 + 2h vertex-sampling margin (h = 14.2), so vertex distance >= 173 implies
point-to-surface distance >= 144. Alternative listed: POOL23. Allowed 2 x 2 cm windows and 1 x 1 cm blanks
are greedily deduplicated in 3-D (reject if >= 10 % of its vertices lie within 10 2.4-um vox of an
accepted item), 2 cm windows first, by ink150 descending; blanks by clearance descending.
Numbers only; no map exists or is made."""
import hashlib, json, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/user/dominion/src')
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
L = '/home/user/dominion/logs/sib/reg0009b'; DATA = '/work/reg0009b/data'
Z = json.load(open(f'{L}/devzone.json'))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
mesh = {}
def pts(s, box):
    if s not in mesh:
        P = read_tifxyz(f'{DATA}/{s}/mesh/{s.split("-")[0]}-on-20250820154339-2.401um.tifxyz').points.astype(np.float64)
        mesh[s] = (P, valid_mask(P))
    P, V = mesh[s]; x0, y0, x1, y1 = [b // 20 for b in box]
    return P[y0:y1, x0:x1][V[y0:y1, x0:x1]]
out = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]',
           rule='DECL-DEVLOOP-A1 item 7; ruling 2026-09-26 05:59Z (native 2.401 um vox, point-to-surface)',
           threshold_2p4vox=173.0, clearance_vox=144, margin_2h_2p4vox=28.4, lists={})
for key in ('ALL76/native_2p4vox', 'POOL23/native_2p4vox'):
    items = [dict(segment=s, **w) for s, r in Z['results'][key]['per_segment'].items() for w in r['windows']]
    items.sort(key=lambda w: (w['kind'] != '2cm', -w['ink150'] if w['kind'] == '2cm' else -w['min_vertex_dist_2p4vox']))
    acc, trees = [], []
    for w in items:
        c = pts(w['segment'], w['canvas2_px_x0y0x1y1'])
        if any(np.isfinite(t.query(c, k=1, distance_upper_bound=10.0)[0]).mean() >= 0.10 for t in trees): continue
        trees.append(cKDTree(c)); acc.append(w)
    out['lists'][key] = dict(n_2cm=sum(w['kind'] == '2cm' for w in acc), n_blanks=sum(w['kind'] == 'blank1cm' for w in acc),
                             n_2cm_ink150_ge_0p05=sum(w['kind'] == '2cm' and w['ink150'] >= 0.05 for w in acc),
                             min_clearance_2p4vox=min((w['min_vertex_dist_2p4vox'] for w in acc), default=None), items=acc)
    print(key, {k: v for k, v in out['lists'][key].items() if k != 'items'})
out['hashes'] = {p: sha(f'/home/user/dominion/{p}') for p in (
    'tools/sib/reg0009b/devzone.py', 'tools/sib/reg0009b/devreg_proposal.py', 'tools/sib/reg0009b/windows.py',
    'tools/sib/reg0009b/dedupe.py', 'logs/sib/reg0009b/devzone.json', 'logs/sib/reg0009b/windows.json',
    'logs/sib/reg0009b/windows_dedupe.json', 'logs/sib/reg0009b/overlap_frame9.json')}
json.dump(out, open(f'{L}/proposals/devreg_0009b_extension.json', 'w'), indent=1)
