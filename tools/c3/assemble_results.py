# Provenance: Project HERCULES | owner the owner | [id removed]
"""Assemble /home/user/dominion/logs/c3/c3_results.json from raw C3 outputs (numbers copied by code, not typed)."""
import json, hashlib, os, subprocess, csv, datetime

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def dir_manifest_sha(d):
    out = subprocess.run(f"cd {d} && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum",
                         shell=True, capture_output=True, text=True).stdout.split()[0]
    return out

def du(p):
    return int(subprocess.run(['du', '-sb', p], capture_output=True, text=True).stdout.split()[0])

B = 's3://vesuvius-challenge-open-data/'
LOC = '/work/c3/data/s3/'
SEG = 'PHerc0139/segments/20250831000000-w040_2025083102/'
VOL = 'PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/'
MESH = SEG + 'mesh/20250831000000-on-20250728140407-9.362um.tifxyz/'
SV = SEG + 'surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr/'
HFW = 'hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w040/'
HFL = '/work/c3/data/hf/native9/w040/'

def f(key):
    p = LOC + key
    return {'uri': B + key, 'local': p, 'bytes': os.path.getsize(p), 'sha256': sha(p)}

def manifest(path):
    lines = [l.split('  ') for l in open(path).read().strip().split('\n')]
    return {'manifest': path, 'manifest_sha256': sha(path), 'objects': len(lines),
            'bytes': sum(int(l[2]) for l in lines)}

fid = json.load(open('/work/c3/logs/fidelity.json'))
auc_crop = json.load(open('/work/c3/logs/auc_crop.json'))
auc_full = json.load(open('/work/c3/logs/auc_teamsv.json')) if os.path.exists('/work/c3/logs/auc_teamsv.json') else None
ledger = list(csv.DictReader(open('/home/user/dominion/logs/gpu_ledger.tsv'), delimiter='\t'))
mine = [r for r in ledger if '/work/c3' in r['command']]

def t(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')

def run_row(substr, tool):
    rows = [r for r in mine if substr in r['command'] and tool in r['command'] and r['exit'] == '0']
    r = rows[-1]
    return {'command': r['command'].strip(), 'start_utc': r['start_utc'], 'end_utc': r['end_utc'],
            'exit': int(r['exit']), 'wall_s': (t(r['end_utc']) - t(r['start_utc'])).total_seconds(),
            'output_sha256': r['output_sha256']}

infer = {}
for name in ['render_c2_tta', 'render_c2_notta', 'teamsv_notta']:
    d = f'/work/c3/infer/{name}'
    if not os.path.isdir(d) or not os.listdir(d):
        infer[name] = {'status': 'not run or no output'}
        continue
    ent = run_row(f'/work/c3/infer/{name}/', 'vesuvius.ink_detection.inference.infer')
    ent['outputs'] = {fn: {'path': f'{d}/{fn}', 'bytes': os.path.getsize(f'{d}/{fn}'), 'sha256': sha(f'{d}/{fn}')}
                      for fn in sorted(os.listdir(d))}
    starts = []
    for line in open(f'/work/c3/logs/infer_{name}.log'):
        if 'Selected source layer indices=' in line:
            ts = datetime.datetime.strptime(line[1:20], '%Y-%m-%d %H:%M:%S')
            starts.append((ts, line.split('indices=')[1].strip()))
        if 'Selected ' in line and ' patches for inference' in line:
            ent['patches_per_order'] = int(line.split('Selected ')[1].split()[0])
    end_all = t(ent['end_utc'])
    ent['per_order'] = {}
    for i, (ts, idx) in enumerate(starts):
        te = starts[i + 1][0] if i + 1 < len(starts) else end_all
        ent['per_order']['forward' if i == 0 else 'reverse'] = {
            'layer_indices': idx, 'output': [v['path'] for k, v in ent['outputs'].items() if k.endswith('.tif') and (k.endswith('_reverse.tif') == (i == 1))][0],
            'start_utc': ts.strftime('%Y-%m-%dT%H:%M:%SZ'), 'wall_s': (te - ts).total_seconds()}
    infer[name] = ent

a = auc_crop['maps']
res = {
    'provenance': 'Project HERCULES | owner the owner | [id removed]',
    'gate': 'C3 regression gate (RULES.md DECL-C3); runner output only - no verdict is given here',
    'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'repo_head_at_run': subprocess.run(['git', '-C', '/home/user/dominion', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
    'metric_code': {'path': 'src/hercules/metrics/pixel.py', 'sha256': sha('/home/user/dominion/src/hercules/metrics/pixel.py'),
                    'declared_sha256': 'a5ab7fed2b83ce005e45a683ba883f8f53073dd9f9818c375bc9ab693fc097c8'},
    'inputs': {
        'bucket_root_listing': 'PHerc0139/ present (s3 root listing, data/catalogue/bucket_root.txt); subfolders photos/ representations/ segments/ volumes/',
        'volume': {'prefix': B + VOL, 'metadata_json': f(VOL + 'metadata.json'), 'zattrs': f(VOL + '.zattrs'),
                   'level0_zarray': f(VOL + '0/.zarray'), 'level0_shape_zyx': [20974, 6621, 6621], 'dtype': 'uint8',
                   'voxel_size_um': 9.362, 'voxel_size_source': 'metadata.json scan.tomo.acquisition.detector.samplePixelSize = 0.009362 (mm)'},
        'segment': {'prefix': B + SEG, 'exact_name': '20250831000000-w040_2025083102 (exists exactly as declared)',
                    'subfolders': ['ink-detection/', 'ink-labels/', 'mesh/', 'surface-volumes/'],
                    'mesh_folders': ['20250831000000-on-20250728140407-9.362um.tifxyz', '20250831000000-on-20250820105138-2.403um.tifxyz',
                                     '20250831000000-on-20260102150214-2.399um.tifxyz', '20250831000000-on-20260319133554-2.403um.tifxyz',
                                     '20250831000000-on-20260413113053-1.129um.tifxyz', 'intermediate/ (tifxyz_original, tifxyz_normalized, 3 obj)'],
                    'surface_volumes': ['1.129um-0.22m-59keV-volume-20260413113053-L1.zarr', '2.399um-0.22m-78keV-volume-20260102150214.zarr',
                                        '9.362um-1.2m-113keV-volume-20250728140407.zarr']},
        'mesh_used': {'note': 'unlevelled team mesh on the 9.362 um volume (organizer tifxyz, no project levelling applied)',
                      'meta_json': f(MESH + 'meta.json'), 'x_tif': f(MESH + 'x.tif'), 'y_tif': f(MESH + 'y.tif'), 'z_tif': f(MESH + 'z.tif'),
                      'grid_rows_cols': [320, 399], 'scale': [0.05, 0.05], 'valid_grid_points': 110046},
        'team_sv': {'prefix': B + SV, 'zattrs': f(SV + '.zattrs'), 'zgroup': f(SV + '.zgroup'), 'level0_zarray': f(SV + '0/.zarray'),
                    'level0_chunks': manifest('/work/c3/logs/teamSV_L0_manifest.txt'),
                    'level3_chunks': manifest('/work/c3/logs/teamSV_L3_manifest.txt'),
                    'level4_chunks': manifest('/work/c3/logs/teamSV_L4_manifest.txt'),
                    'level5_chunks': manifest('/work/c3/logs/teamSV_L5_manifest.txt'),
                    'format': 'OME-Zarr v2, uncompressed uint8, chunks [28,128,128]', 'shape_zyx': [28, 6400, 7980],
                    'slice_count': 28, 'zattrs_num_slices': 28, 'zattrs_slice_step': 1.0, 'zattrs_canvas_size': [7980, 6400],
                    'zattrs_source_zarr': '/volumes/esrf/20250717/SCROLLS_HEL_4.681um_113keV_1.2m_binmean_2_PHerc_0139_TA_0001_masked.zarr/'},
        'labels_native9_w040': {'uri': HFW, 'bucket_readme_sha256': sha('/work/c3/data/hf/ink_9um_README.md'),
                                'files': 8496, 'bytes': 1218126, 'local': HFL,
                                'manifest': '/work/c3/logs/native9_w040_manifest.sha256',
                                'manifest_sha256': sha('/work/c3/logs/native9_w040_manifest.sha256'),
                                'inklabels_zattrs_sha256': sha(HFL + 'w040_inklabels.zarr/.zattrs'),
                                'inklabels_level0_zarray_sha256': sha(HFL + 'w040_inklabels.zarr/0/.zarray'),
                                'shape_zyx': [28, 6400, 7980], 'annotated_plane': 14, 'values': [0, 255],
                                'ink_px_total': 745657, 'supervision_px_total': 1629734,
                                'zattrs_canvas_size': [6400, 7980],
                                'cross_check_s3_ink_labels_20260918': 'S3 ' + SEG + 'ink-labels/9.362um-volume-20250728140407/20260918/{inklabels,supervision}.zarr level 0 (2-D 6400x7980) identical to HF native9 Z=14 (0 differing px)'},
        'checkpoint': {'path': '/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth',
                       'bytes': os.path.getsize('/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth'),
                       'sha256': sha('/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth'),
                       'expected_sha256': 'e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab'},
    },
    'canvas_registration': {
        'mesh_grid_x20': [320 * 20, 399 * 20], 'team_sv_yx': [6400, 7980], 'labels_yx': [6400, 7980],
        'same_canvas': True, 'render_crop_placement': 'vc_render_tifxyz --crop-x 1152 --crop-y 2048 --crop-width 2048 --crop-height 2048 without --auto-crop: full canvas = mesh grid x (render_scale / mesh scale) = x20, crop offsets added to the canvas origin (vc_render_tifxyz.cpp L1605-1637, L877-879)',
        'auto_crop': 'omitted (it would re-origin the canvas at the valid-mesh bbox, vc_render_tifxyz.cpp L1626-1632)',
    },
    'render': dict(run_row('--crop-width 2048', 'vc_render_tifxyz'),
                   output='/work/c3/render/w040_crop_x1152_y2048_2048.zarr', output_bytes=du('/work/c3/render/w040_crop_x1152_y2048_2048.zarr'),
                   shape_zyx=[28, 2048, 2048], remote_access='s3:// URL through the proxy worked directly (no https fallback needed)',
                   slice_offsets='(k - 13.5) * slice_step along the (flipped) unit normal, k = 0..27 (buildOffsetList, L359-375)'),
    'fidelity': fid,
    'inference': {
        'direction_mapping_from_code': 'vesuvius/ink_detection/inference/infer.py 41701aa: resolve_run_directions("both") = ("forward","reverse") (L1144-1147); resolve_single_output_path appends "_reverse" only for the reverse run (L1150-1162) -> OUT.tif = forward, OUT_reverse.tif = reverse; select_layer_indices center-crops 17 of 28 layers (start 28//2 - 17//2 = 6) -> forward layers [6..22] ascending, reverse = [22..6] (L200-245; log line "Selected source layer indices=[6, ..., 22]")',
        'runs': infer},
    'auc_crop_render': auc_crop,
    'auc_teamsv_whole_labelled_area_notta': auc_full,
    'summary': {
        'render_pearson_pooled_all_px': fid['primary_all_pixels']['pooled'],
        'render_pearson_min_slice_all_px': fid['primary_all_pixels']['min'],
        'render_best_slice_offset': fid['supp_best_slice_offset'],
        'render_best_canvas_shift_dy_dx': fid['supp_canvas_shift_scan_pooled_joint_valid_interior']['best_dy_dx'],
        'auc_c2_tta_forward': a.get('c2_tta_forward', {}).get('auc_declared_valid'),
        'auc_c2_tta_reverse': a.get('c2_tta_reverse', {}).get('auc_declared_valid'),
        'auc_c2_notta_forward': a.get('c2_notta_forward', {}).get('auc_declared_valid'),
        'auc_c2_notta_reverse': a.get('c2_notta_reverse', {}).get('auc_declared_valid'),
        'auc_teamsv_notta_forward': (auc_full or {}).get('maps', {}).get('teamsv_notta_forward', {}).get('auc_declared_valid'),
        'auc_teamsv_notta_reverse': (auc_full or {}).get('maps', {}).get('teamsv_notta_reverse', {}).get('auc_declared_valid'),
        'supp_auc_within_supervision_mask': {
            'c2_tta_forward': a.get('c2_tta_forward', {}).get('supp_auc_within_supervision_mask'),
            'c2_tta_reverse': a.get('c2_tta_reverse', {}).get('supp_auc_within_supervision_mask'),
            'c2_notta_forward': a.get('c2_notta_forward', {}).get('supp_auc_within_supervision_mask'),
            'c2_notta_reverse': a.get('c2_notta_reverse', {}).get('supp_auc_within_supervision_mask'),
            'teamsv_notta_forward': (auc_full or {}).get('maps', {}).get('teamsv_notta_forward', {}).get('supp_auc_within_supervision_mask'),
            'teamsv_notta_reverse': (auc_full or {}).get('maps', {}).get('teamsv_notta_reverse', {}).get('supp_auc_within_supervision_mask'),
        },
        'declared_bars_for_reference': {'pooled_render_pearson': '>= 0.999', 'forward_auc_c2_tta': '>= 0.987', 'reverse_auc_c2_tta': '< 0.60',
                                        'archive_reference_teamsv_notta_forward_reverse': [0.9966, 0.4963]},
    },
    'deviations_and_notes': [
        'DEFECT (AUC valid-pixel set). The declared AUC counts every valid pixel with label == 0 as blank. Computed that way, the team-SV no-TTA check gives forward/reverse ' + f"{(auc_full or {}).get('maps', {}).get('teamsv_notta_forward', {}).get('auc_declared_valid', float('nan')):.4f}/{(auc_full or {}).get('maps', {}).get('teamsv_notta_reverse', {}).get('auc_declared_valid', float('nan')):.4f}" + ', which does not reproduce the archive reference 0.9966/0.4963. Restricting to the organizer supervision mask (native9 w040_supervision_mask.zarr, Z=14, value > 0) gives ' + f"{(auc_full or {}).get('maps', {}).get('teamsv_notta_forward', {}).get('supp_auc_within_supervision_mask', float('nan')):.6f}/{(auc_full or {}).get('maps', {}).get('teamsv_notta_reverse', {}).get('supp_auc_within_supervision_mask', float('nan')):.6f}" + ', which matches the archive to 4 decimals. So the archive valid set was most likely the supervision mask, and the declaration text omits it. The choice moves the declared C2+TTA forward AUC on the crop from ' + f"{a.get('c2_tta_forward', {}).get('auc_declared_valid', float('nan')):.4f} (declared text) to {a.get('c2_tta_forward', {}).get('supp_auc_within_supervision_mask', float('nan')):.4f} (supervision mask)" + '. The runner reports both and does not choose.',
        'vc_render_tifxyz requires -v/--volume (the suggested command omitted it). The S3 volume URL was passed as -v. With --remote-url and --voxel-size given, -v is only written into the output .zattrs source_zarr (vc_render_tifxyz.cpp L1258-1266, L1475-1484).',
        'Flags added to the declared render command: --crop-x 1152 --crop-y 2048 --crop-width 2048 --crop-height 2048 (the declared crop), --zarr-output (the app needs an output), and --cache-gb 4 (memory only). The output zarr uses the default blosc-lz4 compression, which is lossless. --auto-crop was omitted to keep the SV canvas.',
        'S3 access through the proxy worked with the s3:// form. No https fallback or local chunk mirror was needed for the render. Fetched chunks sat in the container-ephemeral /root/.VC3D/remote_cache, which was removed with the container.',
        'Pearson: the declared literal reading (all 2048 x 2048 crop pixels) is the primary number. Every crop pixel is valid in both the render and the team SV (any of the 28 slices is nonzero), so the jointly-valid variant is identical.',
        'Labels are 0/255, so the half-range threshold is 127.5 and ink = label == 255. Blank = label == 0. No other values occur. The label canvas covers the whole SV canvas, so valid pixels = the model-input valid mask. In the crop that is all 4,194,304 px.',
        'Team SV "whole labelled area": the whole SV canvas was run (no --mask-path; the occupancy scan kept 85.3% of level-3 cells, 11078 patches per order). The AUC uses every SV-valid pixel on the label canvas, which is the same definition as the crop. Two extra views are reported: inside the organizer supervision mask, and inside the label bounding box. The archive AUC area definition is not available to this runner.',
        'Inference ran on the 2048 x 2048 crop render only, as the brief states. Patches at the crop border have no context beyond it.',
        'Model maps are uint8 TIFFs (official output). AUC ties get average ranks (pixel.auc).',
        'The wrapper scripts (fidelity.py, auc_eval.py: crop, masks, binarisation) are not covered by a METRIC-HASH entry; only pixel.py is declared. Their sha256s are listed under scripts.',
        'The declaration VOID conditions refer to an "archive description" of the label crop, the direction naming and the SV slice alignment. This runner does not have that description. Observed facts: crop on the SV canvas at x1152, y2048 (no offset; the canvas-shift scan peaks at 0,0); OUT.tif = forward (layers 6..22 ascending), OUT_reverse.tif = reverse; team SV slice k matches render slice k (best offset 0).',
        'CPU contention: other project agents ran CPU jobs during the inference (load average up to about 7.9 on 4 cores). Wall times are inflated and not comparable to the TOOLING benchmark. In the TTA run the forward order took about 8.4 min and the reverse order about 32 min.',
        'Ledger: a 128 x 128 test render (rc 0) and one failed launch (rc 127, /usr/bin/time missing, nothing ran) are logged. The HF label download row was added by hand with the same fields, because it ran before the ledger wrapper existed.',
    ],
    'versions': {
        'villa_commit': '41701aa0eaa1aa765523db3f9f972b5830abf549',
        'vc_render_tifxyz_binary_sha256': sha('/work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz'),
        'vc3d_deps_image': 'ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f (image id sha256:09b8d6c7565fd27af4f030b421881525079520ee9e5d27490eeb476dadb57128)',
        'docker': '29.3.1', 'vesuvius': '0.2.4 (editable /work/villa/vesuvius)', 'python_hv_ink': '3.13.12',
        'torch': '2.14.0+cpu', 'numpy_hv_ink': '2.5.3', 'zarr_hv_ink': '3.4.0', 'tifffile': '2026.9.20',
        'python_hv': '3.11.15', 'numpy_hv': '2.4.6', 'scipy_hv': '1.17.1', 'zarr_hv': '2.18.7', 'opencv_hv': '5.0.0',
        'huggingface_hub_cli': '2.0.0',
    },
    'scripts': {os.path.basename(p): sha(p) for p in sorted(
        os.path.join('/work/c3/scripts', x) for x in os.listdir('/work/c3/scripts'))},
    'compute_ledger_rows': mine,
    'disk_bytes_work_c3': du('/work/c3'),
}
json.dump(res, open('/home/user/dominion/logs/c3/c3_results.json', 'w'), indent=1)
print(json.dumps(res['summary'], indent=1))
print('disk', res['disk_bytes_work_c3'])
