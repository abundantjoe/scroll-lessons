# Provenance: Project HERCULES | owner the owner | [id removed]
"""DEV registry certification v4 under RULES.md CORR-RETRACE-RULE (19:01:33Z). Numbers only.

Applied to the windows chosen by registry.py (rule v3). For every DEV window:
C1 Base-training papyrus (fail-closed): the window mesh (quads inside the window) densified 5 x 5 is tested against
   every base-training trace densified 5 x 5 with BOTH forms (nearest densified vertex, hercules.geometry.
   contamination.same_papyrus; point-to-triangulated-surface, surfdist.same_papyrus_surface). Reported on the whole
   window and on the unmasked part. MASK (v4): every canvas pixel of the window (stride 2) whose point-to-surface
   distance to any base-training trace is < 16 vox is excluded from every metric. The window is REJECTED if the
   unmasked part is SAME (either form) with a base-training trace, or if its unmasked coverage falls below the
   registry's coverage threshold.
C2 DEV windows are pairwise NOT SAME (either form).
C3 Live-blank clearance (0139): minimum distance from the window's canvas points (stride 2) to the live w053 blank
   windows' surfaces sampled at 1 vox (20 x 20 densification) >= 144 vox.
C4 Every other trace of the scroll that is SAME (either form) with a DEV window is listed (training hold-out).
Output: logs/sib/devloop/dev_certificate_v4.json; per-window masks /work/devloop/registry/v4mask_<id>.npz.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))
sys.path.insert(0, HERE)
from hercules.geometry.contamination import same_papyrus  # noqa: E402
from hercules.geometry.tifxyz import densify, valid_mask  # noqa: E402
import registry as R  # noqa: E402
import surfdist as SD  # noqa: E402

SLAB = 16.0
CLEAR = 144.0
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def subgrid(points, w, pad=1):
    q0, q1 = max(w['y0'] // 20 - pad, 0), (w['y0'] + w['h']) // 20 + pad + 1
    r0, r1 = max(w['x0'] // 20 - pad, 0), (w['x0'] + w['w']) // 20 + pad + 1
    return points[q0:q1, r0:r1]


def bbox(p, m=0.0):
    v = p[valid_mask(p)] if p.ndim == 3 else p
    return v.min(0) - m, v.max(0) + m


def near(a, b, m):
    return not ((a[1] < b[0] - m).any() or (a[0] > b[1] + m).any())


def both_forms(A_dense_pts, B_grid):
    lit = same_papyrus(A_dense_pts, B_grid.reshape(-1, 3)[valid_mask(B_grid).ravel()], workers=3)
    srf = SD.same_papyrus_surface(A_dense_pts, B_grid, workers=3)
    return dict(vertex=dict(counts=list(map(int, lit.counts)), n_within_2=int(lit.n_within_2), same=bool(lit.same)),
                surface=dict(counts=srf['counts'], n_within_2=srf['n_within_2'], same=srf['same']),
                same=bool(lit.same or srf['same']))


def main():
    t0 = time.time()
    reg = json.load(open(os.path.join(REPO, 'logs/sib/devloop/dev_registry.json')))
    out = dict(provenance=PROV, rule='RULES.md CORR-RETRACE-RULE (fail-closed vertex OR surface form; point-to-surface '
               'clearances)', script_sha256=sha(__file__), surfdist_sha256=sha(os.path.join(HERE, 'surfdist.py')),
               registry_sha256=sha(os.path.join(REPO, 'logs/sib/devloop/dev_registry.json')), scrolls={})
    for scroll, s in reg['scrolls'].items():
        ids = [x for x in R.seg_dirs(scroll) if os.path.isdir(R.mesh9_path(scroll, x))]
        meshes = {x: R.load_mesh(scroll, x) for x in ids}
        dense = {}

        def dens(x):
            if x not in dense:
                dense[x] = densify(meshes[x].points, 5)
            return dense[x]
        base = set(s['base_training_traces'])
        wins = s['windows'] + s['blanks']
        live = []
        if scroll == 'PHerc0139':
            for (seg, y0, x0) in R.LIVE_BLANKS:
                sid = R.find_seg(scroll, seg)
                g = densify(subgrid(meshes[sid].points, dict(y0=y0, x0=x0, h=R.WIN, w=R.WIN), 0), 20)
                live.append(g[valid_mask(g)])
        ltree = cKDTree(np.concatenate(live)) if live else None
        srec = {}
        wdense = {}
        for w in wins:
            m = meshes[w['segment_id']]
            A = densify(subgrid(m.points, w, 0), 5)
            Apts = A[valid_mask(A)]
            # canvas points of the window at stride 2 (mask resolution)
            sp, _ = R.samples(m.points, m.scale, stride=2, window=(w['y0'], w['x0'], w['h'], w['w']))
            flat = sp.reshape(-1, 3)
            good = np.isfinite(flat).all(1)
            dmin = np.full(flat.shape[0], np.inf)
            dmin_dense = np.full(len(Apts), np.inf)
            base_full = {}
            lo_hi = bbox(Apts)
            for b in sorted(base):
                Bg = dens(b)
                if not near(lo_hi, bbox(Bg), SLAB + 25):
                    continue
                d = SD.surface_distances(flat[good], Bg, max_dist=SLAB, workers=3)
                dmin[good] = np.minimum(dmin[good], d)
                dmin_dense = np.minimum(dmin_dense, SD.surface_distances(Apts, Bg, max_dist=SLAB, workers=3))
                base_full[b] = both_forms(Apts, Bg)
            mask = (dmin < SLAB).reshape(sp.shape[:2])
            keep = dmin_dense >= SLAB
            base_unmasked = {}
            for b in base_full:
                base_unmasked[b] = both_forms(Apts[keep], dens(b)) if keep.sum() else dict(same=False)
            np.savez_compressed(f'/work/devloop/registry/v4mask_{w["id"]}.npz', mask=mask, stride=2)
            ok = good.reshape(sp.shape[:2])
            unmasked_cov = float((ok & ~mask).mean())
            dlive = float(ltree.query(flat[good], k=1, workers=3)[0].min()) if ltree is not None else None
            others = {}
            for x in ids:
                if x == w['segment_id'] or x in base:
                    continue
                Bg = dens(x)
                if not near(lo_hi, bbox(Bg), 5):
                    continue
                r = both_forms(Apts, Bg)
                if r['same'] or r['surface']['n_within_2'] or r['vertex']['n_within_2']:
                    others[x] = r
            cov_bar = R.COV_TEXT[scroll] if w['role'] == 'text' else R.COV_BLANK
            base_same = [b for b, r in base_unmasked.items() if r['same']]
            reasons = []
            if base_same:
                reasons.append(f'unmasked part SAME as base-training {base_same}')
            if unmasked_cov < cov_bar:
                reasons.append(f'unmasked coverage {unmasked_cov:.4f} < {cov_bar}')
            if dlive is not None and dlive < CLEAR:
                reasons.append(f'live-blank clearance {dlive:.1f} < {CLEAR}')
            srec[w['id']] = dict(role=w['role'], v4_mask_frac=round(float((mask & ok).sum() / max(ok.sum(), 1)), 5),
                                 unmasked_coverage=round(unmasked_cov, 5), min_surface_dist_base_vox=round(float(
                                     dmin[good].min()), 3) if np.isfinite(dmin[good]).any() else None,
                                 base_whole_window=base_full, base_unmasked=base_unmasked,
                                 live_blank_min_dist_vox=dlive, same_other_traces=sorted(k for k, v in others.items()
                                                                                         if v['same']),
                                 other_traces_detail=others, accepted=not reasons, reasons=reasons)
            wdense[w['id']] = (w, Apts[keep])
            print(w['id'], 'accepted' if not reasons else reasons, srec[w['id']]['v4_mask_frac'], flush=True)
        # C2 pairwise
        pairs = {}
        ks = list(wdense)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                wi, Ai = wdense[ks[i]]
                wj, _ = wdense[ks[j]]
                if wi['segment_id'] == wj['segment_id']:
                    continue
                Bg = densify(subgrid(meshes[wj['segment_id']].points, wj, 0), 5)
                if not near(bbox(Ai), bbox(Bg), 5):
                    continue
                r = both_forms(Ai, Bg)
                pairs[f'{ks[i]}|{ks[j]}'] = r
                if r['same']:
                    for k in (ks[i], ks[j]):
                        srec[k]['accepted'] = False
                        srec[k]['reasons'].append(f'SAME as DEV window {ks[j] if k == ks[i] else ks[i]}')
        hold = sorted({x for v in srec.values() for x in v['same_other_traces']})
        out['scrolls'][scroll] = dict(windows=srec, dev_pairs=pairs, holdout_same_traces=hold,
                                      n_accepted=sum(v['accepted'] for v in srec.values()))
    out['seconds'] = round(time.time() - t0, 1)
    t = json.dumps(out, indent=1, default=float) + '\n'
    p = os.path.join(REPO, 'logs/sib/devloop/dev_certificate_v4.json')
    open(p, 'w').write(t)
    print('wrote', p, hashlib.sha256(t.encode()).hexdigest())


if __name__ == '__main__':
    main()
