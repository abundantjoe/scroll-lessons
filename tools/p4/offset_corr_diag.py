# Provenance: Project HERCULES | [id removed]
"""EXPLORATORY (post hoc, not part of the DECL-P4-26-A2-A1 verdict): does show-through explain the OUTER facing correlation?
(a) forward-forward: r(forward(L), forward(L') via OUTER facing) on the same pixel rule;
(b) partial: r(resid(verso(L) | forward(L)), forward(L') via OUTER facing), resid by per-tile least squares;
(c) same for INNER. Numbers only."""
import sys, json, numpy as np, cv2
sys.path.insert(0, 'tools/p4')
import offset_corr as oc
X = '20260701183124-w010-027'
V = oc.load_tiles(f'/work/p4/src_vt/{X}/tiles'); F = oc.load_tiles(f'/work/p4/src_ft/{X}/tiles')
Mf, Mv, Mt = oc.mosaic(F)
out = {}
for direction in ('outer', 'inner'):
    res = {}
    for L in sorted(V):
        p = f'/work/p4/facing_all/r{L[0]}_c{L[1]}.npz'
        try: fld = np.load(p)[direction].astype(np.float64)
        except Exception: continue
        U = oc.upsample(fld)
        if U is None or not oc.touches_text(U[3], U[4], 0, 0) or L not in F: continue
        mx, my, pv, _, _ = U
        f = cv2.remap(Mf, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        fv = cv2.remap(Mv, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0.999
        ft = cv2.remap(Mt, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(bool)
        v = V[L][0].astype(np.float64); w = F[L][0].astype(np.float64)
        m = oc.valid(V[L][0]) & oc.valid(F[L][0]) & pv & fv & ft
        if m.sum() < oc.MIN_PX: continue
        a, b, c = v[m], w[m], f[m].astype(np.float64)
        A = np.stack([b, np.ones_like(b)], 1); coef = np.linalg.lstsq(A, a, rcond=None)[0]; resid = a - A @ coef
        res[f'r{L[0]}_c{L[1]}'] = {'verso_vs_facing': round(oc.pearson(a, c), 4), 'fwd_vs_facing': round(oc.pearson(b, c), 4),
                                   'resid_verso_vs_facing': round(oc.pearson(resid, c), 4), 'show_through': round(oc.pearson(a, b), 4), 'n_px': int(m.sum())}
    med = lambda k: float(np.median([x[k] for x in res.values()])) if res else None
    out[direction] = {'pairs': res, 'median': {k: med(k) for k in ('verso_vs_facing', 'fwd_vs_facing', 'resid_verso_vs_facing', 'show_through')}}
json.dump(out, open('logs/p4/offset_corr_diag.json', 'w'), indent=1)
for d in out: print(d, len(out[d]['pairs']), out[d]['median'])
for k, x in out['outer']['pairs'].items(): print(' ', k, x)
