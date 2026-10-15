# Provenance: Project HERCULES | owner the owner | [id removed]
"""Collect every reg0009b output into logs/sib/reg0009b/summary.json (machine-readable deliverable)."""
import json, os, glob, hashlib
L = '/home/user/dominion/logs/sib/reg0009b'
inv = json.load(open(f'{L}/inventory_raw.json'))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
S = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]', task='reg0009b',
         volumes=dict(v9='PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr (samplePixelSize 0.00864 mm)',
                      v2='PHerc0009B/volumes/20250820154339-2.401um-0.3m-77keV-masked.zarr (samplePixelSize 0.002401 mm)'),
         inventory={}, registration={}, depth={}, files={})
for sid, r in sorted(inv['segments'].items()):
    S['inventory'][sid] = dict(both_frames=r['both_frames'], n_objects=r['n_objects'],
        ink2_bytes=[z for _, z in r['ink2']], labels2=sorted({k.split('/ink-labels/')[1].split('.zarr')[0] + '.zarr' for k, _ in r['labels2']}),
        obj_bytes={os.path.basename(k): z for k, z in r['obj']}, other=[os.path.basename(k) for k, _ in r['other']])
for f in sorted(glob.glob(f'{L}/reg/*.dc.json')):
    r = json.load(open(f)); n = json.load(open(f.replace('.dc.json', '.json'))); d = json.load(open(f.replace('.dc.json', '.depth.json')))
    sid = r['segment']
    g, gn = r.get('gate', {}), n.get('gate', {})
    S['registration'][sid] = dict(N9=r['N9'], N2=r['N2'], ratio=r['ratio'], n_tiles=r['n_tiles'], n_good=r['n_good'],
        shift_nominal_depth=n.get('global_shift_median'), shift_depth_corrected=r.get('global_shift_median'),
        affine_dc=r.get('affine'), resid_after_global_dc=r.get('resid_after_global'),
        gate_nominal=gn, gate_depth_corrected=g, depth_plane=r.get('depth_plane'),
        pass_gate=bool(g.get('pass')))
    S['depth'][sid] = dict(slope_dk_ds9=d.get('slope_dk_ds9'), k_at_s9_15=d.get('k_at_s9_15'),
        depth_offset_9vox_at_centre=d.get('depth_offset_9vox_at_centre'),
        per_s9={k: {kk: vv for kk, vv in v.items() if kk != 'tiles'} for k, v in d['per_s9'].items()})
S['files'] = {}
for f in sorted(glob.glob(f'{L}/*.json')):
    if os.path.basename(f) != 'summary.json': S['files'][os.path.basename(f)] = sha(f)
F = json.load(open(f'{L}/overlap_frame9.json'))
S['grouping'] = dict(rule=F['rule'], n_pairs_within128=F['n_pairs_within128'], n_same=F['n_same'],
    n_same_normal_variant=F['n_same_normal_variant'], units_primary=F['units'],
    units_sensitivity=json.load(open(f'{L}/sensitivity_units.json')),
    sensitivity_added_pairs=json.load(open(f'{L}/sensitivity_added_pairs.json'))['added_pairs'])
DD = json.load(open(f'{L}/windows_dedupe.json'))
S['windows'] = dict(params=json.load(open(f'{L}/windows.json'))['params'],
    n_dense_all_segments=DD['n_dense_windows_all_segments'],
    per_unit_primary_tol10=DD['tol']['10']['per_unit_primary'], per_unit_primary_tol20=DD['tol']['20']['per_unit_primary'],
    per_unit_sensitivity_tol10=DD['tol']['10']['per_unit_sensitivity'], n_accepted_tol10=DD['tol']['10']['n_accepted'])
S['n_segments_both_frames'] = sum(v['both_frames'] for v in S['inventory'].values())
S['n_registered'] = len(S['registration']); S['n_pass'] = sum(v['pass_gate'] for v in S['registration'].values())
json.dump(S, open(f'{L}/summary.json', 'w'), indent=1)
print('registered', S['n_registered'], 'pass', S['n_pass'])
for sid, v in S['registration'].items():
    g = v['gate_depth_corrected']
    print(sid[:14], v['shift_nominal_depth'], v['shift_depth_corrected'], round(g.get('ncc_global_after', 0), 3), round(v['gate_nominal'].get('ncc_global_after', 0), 3),
          round(g.get('ncc_null_offset40', 0), 3), round(g.get('tile_resid_shift_median', 0), 2), round(g.get('frac_tiles_ncc080_shift_le2', 0), 2),
          round(S['depth'][sid]['depth_offset_9vox_at_centre'] or 0, 2), round(S['depth'][sid]['slope_dk_ds9'] or 0, 3), v['pass_gate'])
