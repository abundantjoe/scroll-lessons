#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Assemble logs/sib/ckpt-screen-b/SPECS.json (numbers, hashes and quoted documentation only).
Inputs: /work/cards (verified card + code files, not committed), downloads.jsonl, lastckpt_check.jsonl, smoke.json, the weights
(bn1 input-scale estimate) and the pinned villa checkout (/work/villa) for the code-side training metadata."""
import hashlib
import json
import os
import subprocess
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
L = os.path.join(REPO, 'logs/sib/ckpt-screen-b')
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
VILLA = '/work/villa'
VILLA_HEAD = 'f4570bfa6c2b357fd24a17b46f8a43becf87ea8d'   # origin/HEAD fetched 2026-09-26
VILLA_PIN = '41701aa0eaa1aa765523db3f9f972b5830abf549'    # docker/env/setup_env.sh


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def jl(p):
    return [json.loads(x) for x in open(p)] if os.path.exists(p) else []


def villa_blob(rev, path):
    b = subprocess.check_output(['git', '-C', VILLA, 'show', f'{rev}:{path}'])
    return b, hashlib.sha256(b).hexdigest()


def bn1_scale(it):
    from safetensors.numpy import load_file
    sd = load_file(f'/work/ckpt/PHerc.1667-iteration-{it}/model.safetensors')
    W = sd['backbone.conv1.weight'].astype(np.float64).reshape(64, -1)
    rm = sd['backbone.bn1.running_mean'].astype(np.float64)
    rv = sd['backbone.bn1.running_var'].astype(np.float64)
    ws = W.sum(1)
    return dict(method='conv1 is linear and bias-free, so bn1.running_mean[c] = sum(w_c) * E[x] for stationary '
                       'input; least squares over the 64 channels gives E[x] in the units the model was trained in',
                est_mean_input=round(float((ws * rm).sum() / (ws * ws).sum()), 4),
                corr_wsum_vs_running_mean=round(float(np.corrcoef(ws, rm)[0, 1]), 4),
                median_sqrt_running_var_over_wnorm=round(float(np.median(np.sqrt(rv) / np.sqrt((W ** 2).sum(1)))), 4),
                verdict='training scale is [0,1]-type (clip 0..200 then /255 gives mean ~0.2-0.3); raw 0..255 '
                        'input (the card snippet as written) would be ~255x off-scale')


def tiles(n):
    p = n + (256 - n % 256)
    return (p - 256) // 128 + 1


def cost(sec_per_tile_62, sec_per_tile_native):
    out = {}
    for name, px in (('text_window_2x2cm', 2136), ('blank_1x1cm', 1068)):
        crop = px + 2 * 256          # devloop render crop = window + 256 px margin each side
        hm = int(round(crop * 9.362 / 2.399))
        ts, tn = tiles(hm) ** 2, tiles(crop) ** 2
        out[name] = dict(render_crop_px=crop,
                         spec=dict(model_grid_px=hm, tiles=ts,
                                   cpu_min_per_order=round(ts * sec_per_tile_62 / 60, 1),
                                   cpu_min_both_orders=round(2 * ts * sec_per_tile_62 / 60, 1)),
                         native=dict(tiles=tn, cpu_min_per_order=round(tn * sec_per_tile_native / 60, 1),
                                     cpu_min_both_orders=round(2 * tn * sec_per_tile_native / 60, 1)))
    out['assumptions'] = ('4 threads, fp32, batch 1, torch CPU; every tile valid (holes only lower the count); '
                          'wall minutes on this 4-vCPU container = the figures (all 4 threads used); '
                          'per-tile seconds measured in smoke.json (spec = 62 layers, native = 16 layers)')
    return out


def main():
    smoke = json.load(open(os.path.join(L, 'smoke.json')))
    dl = {(r['iteration'], r['file']): r for r in jl(os.path.join(L, 'downloads.jsonl')) if r.get('verified')}
    lc = {r['iteration']: r for r in jl(os.path.join(L, 'lastckpt_check.jsonl'))}
    cat = json.load(open(os.path.join(REPO, 'data/catalogue/checkpoints.json')))
    meta_b, meta_sha = villa_blob(VILLA_HEAD, 'deprecated/ink-detection/metadata.json')
    meta = json.loads(meta_b)
    _, tr3d_sha = villa_blob(VILLA_HEAD, 'deprecated/ink-detection/train_resnet3d_3d_decoder.py')
    _, inf3d_sha = villa_blob(VILLA_HEAD, 'deprecated/ink-detection/inference_resnet3d_3d_decoder.py')
    _, dataops_sha = villa_blob(VILLA_HEAD, 'deprecated/ink-detection/train_resnet3d_lib/data_ops.py')
    _, cfg_sha = villa_blob(VILLA_HEAD, 'deprecated/ink-detection/train_resnet3d_lib/config.py')
    spt62 = [smoke['T3'][k]['spec']['seconds_per_tile'] for k in smoke['T3']]
    sptn = [smoke['T3'][k]['native']['seconds_per_tile'] for k in smoke['T3']]
    s62, sn = float(np.median(spt62)), float(np.median(sptn))

    input_spec = dict(
        tensor='(B, 1, D=62, H=256, W=256) float32 (config.json input_depth 62, input_size 256; modeling docstring)',
        dtype_source='uint8 surface-volume layers (card tiling snippet: "(H, W, D) uint8 stack of the 62 layers")',
        normalisation='clip(0, 200) then /255 (card training text: "clipped raw uint8 layers to [0, 200] then '
                      'applied Normalize(mean=0, std=1)"; villa train_resnet3d_lib data_ops.py np.clip(.., 0, 200) '
                      'and config.py A.Normalize(mean=[0]*in_chans, std=[1]*in_chans), albumentations '
                      'max_pixel_value 255). DISCREPANCIES: modeling docstring says "z-score normalised"; the card '
                      'tiling snippet feeds raw 0..255 floats without clip or /255. Resolved by the weights: see '
                      'bn1_input_scale.',
        voxel_size=dict(card='UNKNOWN (not stated in card, config or modeling code)',
                        code='~2 um class: villa deprecated/ink-detection/metadata.json dataset_name "2um_dataset" '
                             '("Collection of 2um resolution segments"), which lists all four iteration-0 training '
                             'segments; train_resnet3d_3d_decoder.py maps l_2 to base_path "2um_dataset/s4_2um". '
                             'Exact per-segment voxel size is not documented.',
                        used_by_wrapper_spec_mode_um=2.399,
                        why_2399='the 2 um-class spacing of the DEV scrolls (dev_registry voxel_um_2 = 2.399 for '
                                 'PHerc0139 and PHerc0814); an assumption inside the documented class, flagged'),
        slices='62 consecutive layers at 1 layer = 1 voxel spacing, centred crop of the segment layer range '
               '(villa _compute_selected_layer_indices / vesuvius select_layer_indices); organizer surface volumes '
               'use layer_range [1, 63) i.e. layers 1..62 around the surface layer ~32 (metadata.json)',
        orientation_order=dict(
            documented='per training segment: l_2 reverse_layers False (inference_resnet3d_3d_decoder.py '
                       "segments_to_infer ('l_2', False, '2um_dataset/s4_2um')); 500p2a and 658 reverse_layers True; "
                       '9b segments False (metadata.json, train_resnet3d_3d_decoder.py); iteration-0 card: '
                       '"l_2 inference uses reverse_layers=True to match the training-segment convention"',
            relative_to_devloop_render='UNDOCUMENTED: no card or code relates organizer layer order to the devloop '
                                       'vc_render_tifxyz -n 31 --flip-normals slice order, so both orders are '
                                       'mapped and reported (DECL-DEVLOOP-SCREEN item 2) and the order is not '
                                       'chosen from DEV. Documented relation inside the family: iteration-0 '
                                       'text order = reverse of the l_2 native order; iterations 1-5 = l_2 native '
                                       'order; i.e. iteration-0 and 1-5 expect OPPOSITE orders on the same input.'),
        tile=dict(window=256, stride=128, output='(B,1,64,64) logits, quarter resolution; sigmoid; '
                  'F.interpolate x4 bilinear; overlap mean; tiles with any fmask==0 pixel skipped; image padded '
                  'to multiples of 256', output_format='uint8 = clip(pred*255) truncated (card); wrapper writes '
                  'the devloop format <wid>.tif (forward) and <wid>_reverse.tif, 2-D uint8, LZW'),
        wrapper_modes=dict(
            spec='render resampled to 2.399 um in x, y and z (zoom 3.9025; 62 layers = 148.7 um centred on '
                 'render slice 15; render slices 7.18..22.82 used); map area-averaged back to the 9.362 um grid',
            native='OUT OF SPEC in voxel size: 16 central render slices (7..22, official centre crop, 150 um) fed '
                   'at 9.362 um; D = 16 instead of 62 (the network is depth-agnostic: max over z per stage)'),
    )

    specs = dict(provenance=PROV, generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                 task='ckpt-screen-b PHASE 1 (RULES.md DECL-DEVLOOP-SCREEN item 1)',
                 viewing='no image was written for viewing, opened or displayed; no CT data was read in PHASE 1; '
                         'preview_*.png files of the HF repos were never downloaded',
                 sources=dict(
                     hf_card_and_code='verbatim copies kept outside the repo (/work/cards; they carry personal names and links); fetched by tools/sib/ckpt-screen-b/fetch.py cards, git blob oids equal to catalogue; sha256 per checkpoint in card_files_sha256',
                     villa_head=VILLA_HEAD, villa_pinned_env=VILLA_PIN,
                     villa_files_sha256={'deprecated/ink-detection/metadata.json': meta_sha,
                                         'deprecated/ink-detection/train_resnet3d_3d_decoder.py': tr3d_sha,
                                         'deprecated/ink-detection/inference_resnet3d_3d_decoder.py': inf3d_sha,
                                         'deprecated/ink-detection/train_resnet3d_lib/data_ops.py': dataops_sha,
                                         'deprecated/ink-detection/train_resnet3d_lib/config.py': cfg_sha}),
                 architecture='ResNet3D-50 (Kinetics-700 r3d50_KM_200ep init, conv1 summed to 1 channel) + per-stage '
                              'torch.max over z + 2-D U-Net decoder; 83,317,825 parameters; all six share '
                              'modeling_inkdetection.py (git oid c75143f2...) and configuration_inkdetection.py',
                 input_spec_common=input_spec,
                 wrapper=dict(path='tools/sib/ckpt-screen-b/infer_1667.py',
                              sha256=sha256(os.path.join(HERE, 'infer_1667.py')),
                              env='python 3.11, torch 2.14.0+cpu, transformers 4.57.6 (config transformers_version; '
                                  '5.x cannot import the official PreTrainedModel file), safetensors, numpy, '
                                  'opencv-python-headless, tifffile + imagecodecs, zarr<3'),
                 smoke_summary=dict(file='logs/sib/ckpt-screen-b/smoke.json', sha256=sha256(os.path.join(L, 'smoke.json')),
                                    T1_resampler_max_abs_err=smoke['T1_resampler']['forward']['max_abs_err'],
                                    T2_card_tiling_vs_direct_max_abs_diff=smoke['T2_tiling_vs_direct']['max_abs_diff']),
                 cost_estimate_2x2cm=cost(s62, sn),
                 sec_per_tile_measured=dict(spec_62_layers_median=s62, native_16_layers_median=sn),
                 open_decisions_for_orchestrator=[
                     'geometry: spec mode (documented ~2 um class, 2.399 um assumed) costs ~394 CPU-min per order per '
                     '2x2 cm window (~13 h both orders); native 9.362 um mode ~7 min per order but is out of the '
                     'documented voxel size (DECL-DEVLOOP-SCREEN item 1 takes the voxel size from card/code)',
                     'text order: undocumented relative to the devloop render; iteration-0 and iterations 1-5 are '
                     'documented to expect opposite orders on the same segment; both orders will be mapped',
                     'in-sample: iteration-0 trained on PHerc0009B, PHerc0500P2 and PHerc0343P segments '
                     '(scroll attribution from villa code): its 0009B/0500P2 DEV windows are UNKNOWN unless certified '
                     'not same-papyrus; iterations 1-5 (l_2, PHerc1667 only) are out-of-sample for every DEV scroll',
                     'normalisation: clip(0,200)/255 (training text, villa code, bn1 statistics) instead of the card '
                     'snippet raw 0..255 input'],
                 checkpoints={})

    fam = {0: dict(train_segments_card=['500p2a', '658', '20250910185200',
                                        '20250919125754-auto_grown_20250919055754487_inp_hr'],
                   train_label='(cross-segment baseline; no l_2 labels)', train_tiles=20075),
           }
    for i in range(1, 6):
        fam[i] = dict(train_segments_card=['l_2'], train_label=('l_2_inklabels.png' if i == 1 else f'l_2_inklabels{i}.png'),
                      train_tiles=[None, 3396, 8970, 15286, 24773, 33061][i])
    seg_scroll = {
        '500p2a': ('PHerc0500P2', "metadata.json base_path '500p2a'; reverse_layers True"),
        '658': ('PHerc0343P', "metadata.json base_path '343P' (original_path train_scrolls/658); reverse_layers True"),
        '20250910185200': ('PHerc0009B', "metadata.json base_path '9b' (original_path new_traces9b/david_9b); "
                                         'layer_range [1,108]'),
        '20250919125754-auto_grown_20250919055754487_inp_hr': ('PHerc0009B', "metadata.json base_path '9b'; "
                                                               "train_resnet3d_3d_decoder.py '2um_dataset/9b_2um'"),
        'l_2': ('PHerc1667', "repo name PHerc.1667; train_resnet3d_3d_decoder.py and inference_resnet3d_3d_decoder.py "
                             "base_path '2um_dataset/s4_2um' (Scroll 4 = PHerc. 1667)"),
    }
    dev_scrolls = ['PHerc0139', 'PHerc0814', 'PHerc0009B', 'PHerc0500P2', 'PHerc0332', 'PHerc1451']
    for it in range(6):
        m = next(x for x in cat['all_scrollprize_hf_models'] if x['repo'] == f'scrollprize/PHerc.1667-iteration-{it}')
        f = fam[it]
        scrolls = sorted({seg_scroll[s][0] for s in f['train_segments_card']})
        guard = {}
        for s in dev_scrolls:
            if s in scrolls:
                guard[s] = ('SCROLL IN TRAINING LIST: IN-SAMPLE for any DEV window same-papyrus (+16 vox) with '
                            f'{[x for x in f["train_segments_card"] if seg_scroll[x][0] == s]}; those segment ids have '
                            'no public organizer mesh identified here, so certification is not possible -> UNKNOWN '
                            '(never counts toward FINALIST) unless the orchestrator certifies otherwise')
            else:
                guard[s] = 'scroll absent from every training list the card or code names -> OUT-OF-SAMPLE'
        sm = smoke['T3'][f'iteration-{it}']
        c = dict(repo=m['repo'], commit=m['commit_sha'], licence=m['card_licence'], gated=m['gated'],
                 weights=dict(file='model.safetensors', bytes=dl[(it, 'model.safetensors')]['bytes'],
                              sha256=dl[(it, 'model.safetensors')]['sha256'],
                              sha256_matches_catalogue=dl[(it, 'model.safetensors')]['verified']),
                 last_ckpt=dict(sha256=lc[it]['sha256_last_ckpt'], verified=lc[it]['verified_download'],
                                tensors_equal_to_safetensors=lc[it].get('max_abs_diff') == 0.0,
                                n_common=lc[it].get('n_common'), only_in_ckpt=lc[it].get('only_ckpt'),
                                global_step=lc[it].get('global_step'), epoch=lc[it].get('epoch'),
                                note='fc head unused by forward(); file deleted after the check'),
                 card_files_sha256={n: sha256(os.path.join('/work/cards', f'it{it}_{n}')) for n in
                                    ('README.md', 'config.json', 'configuration_inkdetection.py', 'modeling_inkdetection.py')},
                 input_spec='see input_spec_common (identical code and config apart from provenance fields)',
                 documented_text_order=('reverse of l_2 native (card: "l_2 inference uses reverse_layers=True to match '
                                        'the training-segment convention")' if it == 0 else
                                        'l_2 native order (reverse_layers False); relation to devloop render: UNDOCUMENTED'),
                 training_data=dict(documented_in='card (Training summary; model family table) and config.json '
                                                  'train_segment / train_inklabels',
                                    segments=f['train_segments_card'], label=f['train_label'], tiles=f['train_tiles'],
                                    steps=12396, scrolls=scrolls,
                                    scroll_attribution={s: seg_scroll[s][1] for s in f['train_segments_card']},
                                    scroll_attribution_source='villa code (not the card), except l_2 whose repo name '
                                                              'also says PHerc.1667',
                                    encoder_pretraining='Kinetics-700 video (no papyrus)',
                                    pherc1667_note='no current DEV window is on PHerc1667 (base-training scroll, '
                                                   'w028 in base training); l_2 could only matter for a 1667 window'),
                 in_sample_guard=guard,
                 bn1_input_scale=bn1_scale(it),
                 smoke=dict(native=dict(k=sm['native']['tiles'], sec_per_tile=sm['native']['seconds_per_tile'],
                                        deterministic=sm['native']['deterministic'],
                                        fwd_ne_rev=sm['native']['fwd_ne_rev'],
                                        zero_where_uncovered=sm['native']['zero_where_uncovered'],
                                        map_shape=sm['native']['map_shape'], fwd_sha=sm['native']['fwd_sha'],
                                        rev_sha=sm['native']['rev_sha']),
                            spec=dict(tiles=sm['spec']['tiles'], sec_per_tile=sm['spec']['seconds_per_tile'],
                                      fwd_ne_rev=sm['spec']['fwd_ne_rev'], map_shape=sm['spec']['map_shape'],
                                      model_grid_hw=sm['spec']['model_grid_hw'],
                                      zero_where_uncovered=sm['spec']['zero_where_uncovered'],
                                      fwd_sha=sm['spec']['fwd_sha'], rev_sha=sm['spec']['rev_sha'])),
                 cost='see cost_estimate_2x2cm (identical architecture; per-checkpoint seconds per tile in smoke)')
        specs['checkpoints'][f'PHerc.1667-iteration-{it}'] = c
    p = os.path.join(L, 'SPECS.json')
    json.dump(specs, open(p, 'w'), indent=1)
    print(p, sha256(p))


if __name__ == '__main__':
    main()
