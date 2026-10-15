"""Build a PARTIAL excl_d file from per-segment checkpoints of a running process_d.py (numbers only)."""
import sys, os, json, time, glob, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from process import SEGS, VOX_MM, FLAG_MM, PROV
st, npz, ckdir, commit, blob, rpath, out = sys.argv[1:8]
z = np.load(npz)
keys = sorted({k.split('__')[0] for k in z.keys()}, key=lambda k: tuple(int(t[1:]) for t in k.split('_')))
def load(lbl):
    d = {}
    for f in glob.glob(f'{ckdir}/{lbl}_*.json'):
        d[os.path.basename(f)[len(lbl) + 1:-5]] = np.array(json.load(open(f))['dmin'], float)
    return d
N, A = load('d-npz'), load('d-all-vertex')
tiles = {}
for n, k in enumerate(keys):
    nm = min((N[s][n], s) for s in N); am = min((A[s][n], s) for s in A) if A else (np.inf, '')
    nf = bool(nm[0] * VOX_MM < FLAG_MM); af = bool(am[0] * VOX_MM < FLAG_MM); u = min(nm, am)
    tiles[k] = {'labelled_adjacent': nf, 'labelled_adjacent_union': nf or af, 'union_final': (nf or af) or len(A) == 8,
                'min_mm': round(u[0] * VOX_MM, 6), 'segment': u[1],
                'npz': {'min_mm': round(nm[0] * VOX_MM, 6), 'segment': nm[1], 'per_segment_mm': {s: round(N[s][n] * VOX_MM, 6) for s in SEGS if s in N}},
                'all_vertex': {'min_mm': round(am[0] * VOX_MM, 6) if A else None, 'segment': am[1],
                               'per_segment_mm': {s: round(A[s][n] * VOX_MM, 6) for s in SEGS if s in A}},
                'per_segment_mm': {s: round(min(N[s][n], A.get(s, [np.inf] * len(keys))[n]) * VOX_MM, 6) for s in SEGS if s in N}}
o = {'provenance': PROV, 'strip': '20260623141924-w010-027', 'partial': True,
     'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
     'partial_state': {'npz_segments_done': sorted(N), 'all_vertex_segments_done': sorted(A),
                       'meaning': 'npz flags final when 8 npz segments done; a union flag that is true is final; a false union flag is final only when union_final is true'},
     'inputs': {'branch': f'claude/gifted-bell-gavnl5-sib-p4-tiles-{st}', 'path': rpath, 'commit': commit, 'git_blob': blob,
                'sha256': hashlib.sha256(open(npz, 'rb').read()).hexdigest()},
     'grids': 'M2a grid == E1 grid, see logs/sib/p4-excl/grid_equality_m2a_e1.json',
     'voxel_mm': VOX_MM, 'flag_rule': 'min_mm < 1.2', 'method': 'as excl_d_b.json (tools/sib/p4-excl/process_d.py)',
     'n_tiles': len(keys), 'n_flagged_npz': sum(t['labelled_adjacent'] for t in tiles.values()),
     'n_flagged_union_so_far': sum(t['labelled_adjacent_union'] for t in tiles.values()),
     'n_unflagged_not_final': sum(not t['union_final'] for t in tiles.values()), 'tiles': tiles}
json.dump(o, open(out, 'w'), indent=1)
print(len(N), len(A), o['n_flagged_npz'], o['n_flagged_union_so_far'], o['n_unflagged_not_final'])
