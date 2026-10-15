# Provenance: Project HERCULES | owner the owner | [id removed]
"""Normalise a sibling builder's tile manifest for tools/p4/p4_jobs.py import, applying the declared eligibility
rules. Numbers only; tile bytes are fetched from git and sha256-checked, never opened as images.

usage: norm_manifest.py <git_ref> <manifest_path_in_ref> <tiles_dir_in_ref> <out_dir> [--coverage]

Eligible (DECL-P4-2 item 2, DECL-P4-4-A1, DECL-P4-5 item 3): valid_fraction >= 0.5; with --coverage also
frac_mesh_points_outside_1129_volume < 0.5 (read from stats, else the same name at top level, else top-level
frac_outside; missing -> not eligible; METRIC-HASH-29).
Writes <out_dir>/tiles/<segment>_r<r>_c<c>.png (bytes from git, sha256 == png_sha256) and <out_dir>/manifest_norm.json.
"""
import hashlib
import json
import os
import subprocess
import sys


def main(ref, man_path, tiles_dir, out_dir, coverage=False):
    m = json.loads(subprocess.run(['git', 'show', f'{ref}:{man_path}'], capture_output=True, check=True).stdout)
    seg = m['segment']
    os.makedirs(f'{out_dir}/tiles', exist_ok=True)
    keep, skipped = [], {'mesh_valid': 0, 'coverage': 0}
    for t in m['tiles']:
        if t.get('valid_fraction', 0) < 0.5:
            skipped['mesh_valid'] += 1
            continue
        if coverage:
            fo = (t.get('stats') or {}).get('frac_mesh_points_outside_1129_volume')
            if fo is None:
                fo = t.get('frac_mesh_points_outside_1129_volume', t.get('frac_outside'))
            if fo is None or fo >= 0.5:
                skipped['coverage'] += 1
                continue
        rel = t['file'] if '/' in t['file'] else f"tiles/{t['file']}"
        b = subprocess.run(['git', 'show', f"{ref}:{tiles_dir}/{os.path.basename(rel)}"], capture_output=True,
                           check=True).stdout
        assert hashlib.sha256(b).hexdigest() == t['png_sha256'], (t['r'], t['c'])
        with open(f"{out_dir}/tiles/{seg}_r{t['r']}_c{t['c']}.png", 'xb') as fh:
            fh.write(b)
        keep.append({'r': t['r'], 'c': t['c'], 'sha256': t['png_sha256'], 'git_transport': True})
    out = {'segment': seg, 'source': f'{ref}:{man_path}', 'coverage_rule': bool(coverage),
           'px_per_mm': m.get('px_per_mm'), 'T_canvas_px': m.get('T_px') or m.get('T_canvas_px'), 'tiles': keep,
           'skipped': skipped}
    with open(f'{out_dir}/manifest_norm.json', 'x') as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({'segment': seg, 'eligible': len(keep), 'skipped': skipped,
                      'unique_png': len({k['sha256'] for k in keep})}))


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    main(*a[:4], coverage='--coverage' in sys.argv)
