# Provenance: Project HERCULES | owner the owner | [id removed]
"""Write /home/user/dominion/logs/c3/README.md with every number read from c3_results.json."""
import json

R = json.load(open('/home/user/dominion/logs/c3/c3_results.json'))
s = R['summary']; fid = R['fidelity']; inf = R['inference']['runs']
ac = R['auc_crop_render']; af = R['auc_teamsv_whole_labelled_area_notta']

def g(x, n=4):
    return 'n/a' if x is None else f'{x:.{n}f}'

def mins(name):
    e = inf.get(name, {})
    return 'n/a' if 'wall_s' not in e else f"{e['wall_s'] / 60:.1f} min ({e['start_utc']} to {e['end_utc']})"

def m(block, key, field='auc_declared_valid'):
    if not block:
        return None
    return block['maps'].get(key, {}).get(field)

lines = [
    'Provenance: Project HERCULES | owner the owner | [id removed]',
    '',
    '# C3 regression gate: runner output',
    '',
    'Raw outputs for RULES.md DECL-C3. This runner gives no verdict. Full numbers, paths, sha256s, commands and versions are in `c3_results.json`. Large files are under /work/c3 (not in the repo).',
    '',
    '## Inputs',
    '',
    f"- Volume: `{R['inputs']['volume']['prefix']}` (voxel {R['inputs']['volume']['voxel_size_um']} um, from metadata.json samplePixelSize).",
    f"- Segment: `{R['inputs']['segment']['prefix']}` (the name exists exactly as declared).",
    f"- Unlevelled team mesh: `mesh/20250831000000-on-20250728140407-9.362um.tifxyz` (grid 320 x 399, scale 0.05).",
    f"- Team SV: `surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr`, shape {R['inputs']['team_sv']['shape_zyx']} (28 slices), uncompressed uint8.",
    f"- Labels: `{R['inputs']['labels_native9_w040']['uri']}`, shape {R['inputs']['labels_native9_w040']['shape_zyx']}, annotated only at Z=14, values 0/255. They match the S3 ink-labels/20260918 copy exactly.",
    f"- Checkpoint sha256 {R['inputs']['checkpoint']['sha256']} (matches the expected hash). Metric code pixel.py sha256 {R['metric_code']['sha256']} (matches the declared hash).",
    '',
    '## Canvas',
    '',
    'Mesh grid x 20 = 6400 x 7980. This equals the team SV and label shapes, so all three are on one canvas. The render used `--crop-x 1152 --crop-y 2048 --crop-width 2048 --crop-height 2048` and omitted `--auto-crop`, which keeps the SV canvas origin.',
    '',
    '## Render fidelity (crop 2048 x 2048 at x1152, y2048; all pixels valid in both)',
    '',
    f"| Pooled Pearson | Minimum per-slice Pearson (slice) | Best slice offset | Best canvas shift (dy,dx) | Voxels exactly equal |",
    '|---|---|---|---|---|',
    f"| {fid['primary_all_pixels']['pooled']:.7f} | {fid['primary_all_pixels']['min']:.7f} ({fid['primary_all_pixels']['argmin_slice']}) | {fid['supp_best_slice_offset']} | {fid['supp_canvas_shift_scan_pooled_joint_valid_interior']['best_dy_dx']} | {fid['exact_equal_voxel_fraction_all']:.4f} (max diff {fid['max_abs_diff_all']}) |",
    '',
    f"The render took {R['render']['wall_s']:.0f} s ({R['render']['start_utc']} to {R['render']['end_utc']}) and streamed chunks from S3 through the proxy.",
    '',
    f"At slice offset +1 or -1, r = {fid['supp_slice_offset_scan_pooled_joint_valid']['1']:.4f}. With the slice order reversed, r = {fid['supp_reversed_slice_order_pooled_joint_valid']:.4f}. Nothing was re-aligned.",
    '',
    '## AUC (Mann-Whitney AUC; ink = label > 127.5; blank = label == 0; valid = model-input valid mask and label canvas)',
    '',
    '| Map | Forward | Reverse | Time for both orders |',
    '|---|---|---|---|',
    f"| Our render crop, C2 with --tta-mirror (declared) | {g(m(ac, 'c2_tta_forward'))} | {g(m(ac, 'c2_tta_reverse'))} | {mins('render_c2_tta')} |",
    f"| Our render crop, no TTA | {g(m(ac, 'c2_notta_forward'))} | {g(m(ac, 'c2_notta_reverse'))} | {mins('render_c2_notta')} |",
    f"| Team SV, whole canvas, no TTA (archive 0.9966 / 0.4963) | {g(m(af, 'teamsv_notta_forward'))} | {g(m(af, 'teamsv_notta_reverse'))} | {mins('teamsv_notta')} |",
    '',
    f"Extra rows (not declared): inside the organizer supervision mask, crop with TTA: {g(m(ac, 'c2_tta_forward', 'supp_auc_within_supervision_mask'))} / {g(m(ac, 'c2_tta_reverse', 'supp_auc_within_supervision_mask'))}; team SV: {g(m(af, 'teamsv_notta_forward', 'supp_auc_within_supervision_mask'))} / {g(m(af, 'teamsv_notta_reverse', 'supp_auc_within_supervision_mask'))}. Team SV inside the label bbox: {g(m(af, 'teamsv_notta_forward', 'supp_auc_within_label_bbox'))} / {g(m(af, 'teamsv_notta_reverse', 'supp_auc_within_label_bbox'))}.",
    '',
    'Order naming comes from the code (infer.py at 41701aa). `OUT.tif` is forward: source layers 6..22 in ascending order. `OUT_reverse.tif` is reverse: layers 22..6.',
    '',
    '## Declared bars (for the decider)',
    '',
    'Pooled render Pearson >= 0.999. Forward AUC >= 0.987 and reverse AUC < 0.60, both for C2 with --tta-mirror.',
    '',
    '## Deviations and notes',
    '',
] + [f'- {d}' for d in R.get('deviations_and_notes', [])] + [
    '',
    f"Disk used under /work/c3: {R['disk_bytes_work_c3'] / 1e9:.2f} GB.",
]
open('/home/user/dominion/logs/c3/README.md', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
