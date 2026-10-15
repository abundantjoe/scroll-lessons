# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fill the label-dependent PENDING items of RECIPE_DRAFT.md from build numbers only (counts, hashes, tile lists) and
write logs/sib/own-lead/p4own/{RECIPE.md, RECIPE.md.sha256, recipe_final.json, build_manifest.json}. Usage: finalize_recipe.py --data /work/own/data --excl /work/own/excl
F-arm held-out tile list (fixed rule of the draft): tiles of group k with >= 1 labelled (sup) px in p4-excl's
labels_*.json, ordered by n_sup_px descending (ties: strip, row, column), capped at 24."""
import argparse
import glob
import hashlib
import json
import os
import shutil

import numpy as np

import own_common as C
import train as TR

P4 = os.path.join(C.REPO, 'logs', 'sib', 'own-lead', 'p4own')
SHORT = {s.split('-', 1)[1]: s for s in C.SEGS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--excl', required=True)
    a = ap.parse_args()
    man = json.load(open(os.path.join(a.data, 'build_manifest.json')))
    pj = json.load(open(os.path.join(a.data, 'patches.json')))
    rc = json.load(open(os.path.join(P4, 'recipe.json')))
    n = len(pj['patches'])
    perm = TR.derangement(n)
    groups = {(s, int(r), int(c)): int(g) for s, r, c, g in rc['fold_groups']}
    nsup = {}
    for lj in sorted(glob.glob(os.path.join(a.excl, 'labels_*.json'))):
        for f in json.load(open(lj))['files']:
            nsup[(SHORT.get(f['strip'], f['strip']), int(f['r']), int(f['c']))] = int(f['n_sup_px'])
    folds = {}
    for k in range(3):
        cand = [t for t, g in groups.items() if g == k and nsup.get(t, 0) > 0]
        cand.sort(key=lambda t: (-nsup[t], t[0], t[1], t[2]))
        folds[f'F{k + 1}'] = [dict(seg=t[0], r=t[1], c=t[2], n_sup_px=nsup[t]) for t in cand[:24]]
    n_train = {}
    for arm in ('F1', 'F2', 'F3'):
        n_train[arm] = int(len(TR.arm_patches(arm, pj['patches'], groups)))
    shutil.copy(os.path.join(a.data, 'build_manifest.json'), os.path.join(P4, 'build_manifest.json'))
    fin = dict(build_manifest_sha256=C.sha256_file(os.path.join(P4, 'build_manifest.json')),
               patches_json_sha256=man['patches_json_sha256'], n_patches=n, n_qualifying=man.get('n_qualifying'),
               n_ink_patches_ge2pct=man['n_ink_patches_ge2pct'], feasibility=man['feasibility'],
               total_bytes=man['total_bytes'], derangement_n=n, derangement_sha256=C.arr_sha(perm.astype(np.int64)),
               derangement_fixed_points=int(np.sum(perm == np.arange(n))), n_train_patches=dict(S=n, **n_train),
               heldout_tiles=folds,
               code_sha256={f: C.sha256_file(os.path.join(C.HERE, f)) for f in
                            ('own_common.py', 'build_patches.py', 'train.py', 'infer.py', 'auc.py', 'test_own.py',
                             'finalize_recipe.py')},
               ckpt_screen_b_sha256=C.CKB_SHA, recipe_json_sha256=C.sha256_file(os.path.join(P4, 'recipe.json')),
               excl_sha256={os.path.basename(p): C.sha256_file(p) for p in
                            sorted(glob.glob(os.path.join(a.excl, '*.json')))})
    json.dump(fin, open(os.path.join(P4, 'recipe_final.json'), 'w'), indent=1)
    d = open(os.path.join(P4, 'RECIPE_DRAFT.md')).read()
    d = d.replace('# P4-OWN RECIPE — DRAFT (DECL-P4-23 item 4). NOT FROZEN.', '# P4-OWN RECIPE (DECL-P4-23 item 4). FROZEN.')
    d += ('\n## 8. Frozen build numbers (recipe_final.json, sha256 '
          f'{C.sha256_file(os.path.join(P4, "recipe_final.json"))})\n'
          f'- Feasibility: {man["feasibility"]["n_ink_cells_ge2pct"]} ink 64-px cells '
          f'(labelled {man["feasibility"]["n_labelled_cells"]}); bar 2000; feasible={man["feasibility"]["feasible"]}.\n'
          f'- Patches: {n} kept of {man.get("n_qualifying")} qualifying; ink patches {man["n_ink_patches_ge2pct"]}; '
          f'{man["total_bytes"] / 1e9:.2f} GB (workers rebuild and verify).\n'
          f'- build_manifest.json sha256 {fin["build_manifest_sha256"]}; patches.json sha256 {fin["patches_json_sha256"]}.\n'
          f'- NULL derangement: n {n}, sha256 {fin["derangement_sha256"]}, fixed points {fin["derangement_fixed_points"]}.\n'
          f'- Training patches per arm: {fin["n_train_patches"]}.\n'
          + ''.join(f'- {k} held-out tiles ({len(v)}): ' + '; '.join(f'{t["seg"].split("-", 1)[1]}:{t["r"]},{t["c"]}' for t in v)
                    + '\n' for k, v in folds.items())
          + '- Code sha256: ' + ', '.join(f'{k} {v}' for k, v in fin['code_sha256'].items()) + '\n'
          + f'- recipe.json sha256 {fin["recipe_json_sha256"]}\n')
    rp = os.path.join(P4, 'RECIPE.md')
    open(rp, 'w').write(d)
    h = hashlib.sha256(open(rp, 'rb').read()).hexdigest()
    open(rp + '.sha256', 'w').write(f'{h}  RECIPE.md\n')
    print(h)


if __name__ == '__main__':
    main()
