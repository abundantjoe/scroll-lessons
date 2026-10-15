# Provenance: Project HERCULES | owner the owner | [id removed]
"""Assemble logs/sib/ckpt-screen-c/SPECS.json (DECL-DEVLOOP-SCREEN phase 1) from: the static facts below (each with
its source: model card, villa code at the pinned SHA, or the official bucket metadata.json), the sha-verified
downloads log, the smoke run records and smoke_check.json, and the fiber smoke record. Numbers and hashes only.
Usage: python make_specs.py SMOKE_OUTDIR FIBER_SMOKE_JSON"""
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
LOGD = os.path.join(ROOT, 'logs/sib/ckpt-screen-c')
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
VILLA_SHA = '41701aa0eaa1aa765523db3f9f972b5830abf549'
ROOT_INDEX = dict(url='https://vesuvius-challenge-open-data.s3.amazonaws.com/metadata.json',
                  sha256='8119d1c2d48b54f880c81bfd7ff9a51eb5edd166c9c06eac754abf15dba7e0ac',
                  note='identical to the index recorded in data/catalogue/checkpoints.json (last_modified 2026-09-23)')
DEV_SCROLLS = ['PHerc0139', 'PHerc0814', 'PHerc0009B', 'PHerc0332', 'PHerc0500P2', 'PHerc1451']

COMMON_TF = dict(
    normalisation=dict(primary='clip 0..200 then /200 (villa ink-detection/optimized_inference inference.py: '
                               'np.clip(tile, 0, 200); A.ToFloat(max_value=200)); this is the production path',
                       training_code='clip 0..200 then /255 (villa deprecated train_timesformer_og.py: '
                                     'A.Normalize(mean=0, std=1), max_pixel_value default 255)',
                       discrepancy='production inference scales inputs 255/200 = 1.275 x the training-code scaling; '
                                   'the screen uses the production path unchanged (not chosen from any DEV result)'),
    tiling='tile 64, stride 16, Hann-window overlap-add, sigmoid, 4 x 4 logits bilinear-resized to 64 x 64; pixels '
           'covered only by Hann-zero tile borders (outermost canvas row/column) come out 0; all-zero tiles skipped',
    output='uint8 = floor(clip(p, 0, 1) * 255) (villa processing.reduce_partitions)',
    in_plane_orientation='no rotation or flip applied by the official code (tiles are square; model is not '
                         'rotation-equivariant by construction); render canvas used as is',
)

STATIC = {
    'timesformer_scroll5_july_retreat': dict(
        repo='scrollprize/timesformer_scroll5_july_retreat', commit='5b714296b256b8f993ce69e8e57aea585125d782',
        file='timesformer_scroll5_july_retreat_20241113070770_frepoch=9.ckpt', card_licence='mit',
        architecture='TimeSformer small (dim 512, depth 8, heads 6, patch 16, 64 x 64 input, rotary frame embedding: '
                     'the weights do not fix the frame count); villa model_timesformer.RegressionPLModel keys match '
                     'exactly; with_norm False',
        registry=dict(id='20250713185324', compatible_samples=['PHerc0172'], target_resolution_um=[7.0, 10.0],
                      default_layers=27, default_tile_size=64, default_stride=16),
        production=dict(runs_in_index=54, sample='PHerc0172', render='vc_render_tifxyz num-slices 33, flip-normals '
                        'true, scale 1, voxel 7.91 um', ink='start-layer 3, end-layer 30, tile 64, stride 16, '
                        'force-reverse false, image ink-detection:v42'),
        input_spec=dict(voxel_um='7.91 in production (registry range 7-10 um); DEV renders 9.362 um (inside range)',
                        slices='27 centred on the surface: offsets -13..+13 (render indices 2..28 of 31)',
                        centring='surface = centre slice of an odd-count vc_render_tifxyz stack (production 33 -> '
                                 'layers 3..29; devloop 31 -> 2..28)',
                        order='forward = increasing vc_render_tifxyz --flip-normals index (production: flip-normals '
                              'true, force-reverse false)', **COMMON_TF,
                        alt_window='TRAIN26 offsets -15..+10 (deprecated training code); available as --window alt'),
        text_order=dict(value='forward', documented=True,
                        source='official bucket metadata.json production provenance (54 PHerc0172 runs)'),
        training_data=dict(scrolls=['PHerc0172'], segments='UNKNOWN',
                           source='card: "Pherc 172 (Scroll 5) timesformer weights. Trained with papyrologists '
                                  'annotated labels during July text retreat."; ckpt hparams pred_shape (1792, 11520), '
                                  'epoch 9, global_step 43800',
                           lineage='UNKNOWN (the related repo timesformer_scroll5_27112024 was pretrained on '
                                   'PHerc.Paris4; nothing documents this for july_retreat)',
                           dev_scrolls_named=[]),
    ),
    'timesformer_GP_scroll1': dict(
        repo='scrollprize/timesformer_GP_scroll1', commit='61b81d31ddb93c89a2b3b00c66769d18bd96ccb2',
        file='model.safetensors', card_licence='card text "License: MIT" (no YAML licence tag, no LICENSE file)',
        architecture='TimeSformer small (dim 512, depth 8, heads 6), HF repo class TimesformerScrollprizeModel; card: '
                     'expects (B, 1, 26, 64, 64)',
        registry=dict(id='20230702185753', compatible_samples=['PHercParis4'], target_resolution_um=[7.0, 10.0],
                      default_layers=27, default_tile_size=64, default_stride=16),
        production=dict(runs_in_index=0),
        input_spec=dict(voxel_um='7.91 (Scroll 1 2023 segments; registry range 7-10 um); DEV renders 9.362 um',
                        slices='27 centred (registry default_layers 27; same workflow as july_retreat): offsets '
                               '-13..+13; card says 26 frames (rotary embedding accepts either)',
                        centring='as july_retreat', order='registry defaults (no force_reverse) -> forward; no '
                        'production run recorded', **COMMON_TF,
                        alt_window='TRAIN26 offsets -15..+10 (the card names train_timesformer_og.py as its '
                                   'training script); --window alt'),
        text_order=dict(value='forward', documented='registry defaults only (no production run in the index); '
                        'orchestrator to confirm', source='official bucket metadata.json models[20230702185753]'),
        training_data=dict(scrolls=['PHercParis4'], segments='UNKNOWN for this exact checkpoint',
                           source='card: Grand Prize 2023 model, 12 epochs with train_timesformer_og.py; registry '
                                  'compatible_samples PHercParis4; the deprecated train_timesformer_og.py at the '
                                  'pinned villa SHA lists 17 Scroll 1 segment ids (+ "recto"), which may differ from '
                                  'the list used for this checkpoint',
                           code_list=['20231210121321', '20231022170901', '20231106155351', '20231005123336',
                                      '20230820203112', '20230826170124', '20230702185753', '20230522215721',
                                      '20230531193658', '20230903193206', '20230902141231', '20231007101615',
                                      '20230929220926', 'recto', '20231016151000', '20231012184423',
                                      '20231031143850'],
                           dev_scrolls_named=[]),
    ),
    'timesformer_large_scroll1_01122024': dict(
        repo='scrollprize/timesformer_large_scroll1_01122024', commit='7e8b37ce66b2497b4af1ad07ae3d7d8f5c5fa990',
        file='model.safetensors', card_licence='none stated',
        architecture='TimeSformer large (dim 512, depth 16, heads 8), HF repo class; not loadable by villa '
                     'model_timesformer (hard-coded depth 8)',
        registry=None, production=dict(runs_in_index=0),
        input_spec=dict(voxel_um='7.91 (Scroll 1 segments, undocumented on the card); DEV renders 9.362 um',
                        slices='26: offsets -15..+10 (card points to villa ink-detection; training-code window, '
                               'the only documented one for this checkpoint)',
                        centring='legacy 65-layer surface volumes, surface = layer 32',
                        order='UNDOCUMENTED in the flip-normals convention: both orders reported', **COMMON_TF,
                        alt_window='PROD27 offsets -13..+13 (family production convention); --window alt'),
        text_order=dict(value=None, documented=False, rule='both orders reported; not chosen from DEV results'),
        training_data=dict(scrolls=['PHercParis4 (Scroll 1)'], segments_finetune=[
            '20231210121321', '20231022170901', '20231106155351', '20231005123336', '20230820203112',
            '20230826170124', '20230702185753', '20230522215721', '20230531193658', '20230903193206',
            '20230902141231', '20231007101615', '20230929220926', '20231016151000', '20231012184423',
            '20231031143850'], pretraining='UNKNOWN', source='card "Finetuning segments"', dev_scrolls_named=[]),
    ),
    'resnet50_7.9um_scroll1_frags': dict(
        repo='scrollprize/resnet50_7.9um_scroll1_frags', commit='f3975de34d4734dd507360304f828808b7182139',
        file='model.safetensors', card_licence='none stated',
        architecture='3D ResNet-50 encoder (Bottleneck [3,4,6,3]) + 2D decoder after max over depth, HF repo class '
                     'Resnet3DScrollprizeModel; output stride 4',
        registry=None, production=dict(runs_in_index=0),
        input_spec=dict(voxel_um='7.9 (repo name); DEV renders 9.362 um',
                        slices='18 (card/config num_layers=18, interpreted as input layers): offsets -9..+8 '
                               '(render indices 6..23), centring per villa deprecated inference_resnet3d.py '
                               '(start = mid - n // 2)',
                        tiling='tile 256 (card/config window_size=256), stride 64 (wrapper choice, undocumented), '
                               'Hann overlap-add, sigmoid, 64 x 64 logits bilinear to 256',
                        normalisation='clip 0..200, /200 (villa optimized_inference, as for all its models)',
                        output='uint8 = floor(p * 255)', order='UNDOCUMENTED: both orders reported'),
        text_order=dict(value=None, documented=False, rule='both orders reported; not chosen from DEV results'),
        training_data=dict(scrolls='UNKNOWN beyond PHercParis4', ids_card=[
            '20240814211913', '20231210121321', 'frag2', 'frag6', 'frag1', 'frag3', 'frag4', 'frag5',
            '20240813112037', '20240813194718', '20240814122007', '20240814124338', '20240814125124',
            '20240815194445', '20240818211653', '20240820102547', '20240820102554', '20240820103254',
            '20240820133348', '20240816164032', '20240814230136', '20240820150159', '20240906213422',
            '20240907121934'],
            resolved_in_root_index={'20231210121321': 'PHercParis4'},
            unresolved='23 of 24 ids (frag1..frag6 and 21 ids from 2024-08/09) are not in the official root index; '
                       'their scrolls are UNKNOWN, so no DEV scroll can be shown absent',
            source='card "Pretrained on Pherc.Paris4 on Fragments and Fragment Hidden layers"'),
    ),
    'fiber_ink_4class_selfdistill': dict(
        repo='scrollprize/fiber_ink_4class_selfdistill', commit='ec9bbc4dbc65a052fc4d78429f7ce5eff080aafe',
        file='p4_4class_ddp8_20260526_step029000.pth', card_licence='mit (LICENSE file)',
        architecture='vesuvius NetworkFromConfig 3D UNet, 4-class softmax head (0 bg, 1 vertical fiber, 2 '
                     'horizontal fiber, 3 ink); EMA weights recommended by the card',
        outputs_ink_class=True, registry=None, production=dict(runs_in_index=0),
        input_spec=dict(voxel_um='2.4 (PHerc. Paris 4 2.4 um volume)', input='1-channel CT subvolume in scan '
                        'orientation, 256^3 patches', normalisation='per-crop clip to [p1, p99] percentiles then '
                        'min-max to [0, 1] (villa scripts/fiber_5class/dataset.py percentile_minmax_normalize)',
                        output='per-voxel 4-class softmax; no official inference / surface-projection script exists '
                               '(scripts/fiber_5class has train, label generation and visualisation only)'),
        screen_status='SPEC-MISMATCH for the 9 um render screen: its documented input is a 2.4 um CT volume, not a '
                      '9.362 um flattened render. No render wrapper was built (it would be off-spec on voxel size '
                      '(3.9 x) and geometry). A spec-conformant route (run on the DEV scroll 2.4 um volume around the '
                      'organizer 2.4 um mesh, then project class-3 probability onto the 9 um canvas) needs a new '
                      'declaration by the orchestrator; per-patch cost is in fiber_smoke.',
        smoke_notes=['256^3 forward (the documented patch size) was killed by the container memory cgroup '
                     '(anon-rss 14.0 GB of ~15 GB; runs.jsonl smoke_fiber_fp32_b exit 137); 128^3 runs in 5.6 s at '
                     '4 threads fp32 (smoke_fiber_fp32_c). A 256^3 route needs sliding 128^3 inference or a larger '
                     'machine; that is outside the documented spec and is not chosen here.',
                     'first attempt (smoke_fiber_fp32) failed on a float64 input: the smoke script omitted the '
                     'float32 cast that dataset.py applies after normalisation; fixed to match dataset.py'],
        cost_rough='route B only, not built: a 2 x 2 cm window at 2.4 um is ~8333^2 px; with ~128 voxels of depth '
                   'around the sheet and 128^3 patches without overlap that is ~(8333/128)^2 = ~4240 patches x 5.6 s '
                   '= ~6.6 CPU-hours per window before overlap or volume download; indicative only',
        text_order=dict(value='not applicable (volumetric model)'),
        training_data=dict(scrolls=['PHercParis4'], segments='whole 2.4 um volume (random 256^3 crops); '
                           'pseudo-labels from a fiber teacher and an unpublished ink teacher (card: unrecoverable)',
                           source='card', dev_scrolls_named=[]),
    ),
}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    smoke_dir, fiber_json = sys.argv[1], sys.argv[2]
    dl = {}
    for line in open(os.path.join(LOGD, 'downloads.jsonl')):
        r = json.loads(line)
        dl[r['repo'].split('/')[1]] = r
    chk = json.load(open(os.path.join(smoke_dir, 'smoke_check.json')))
    fib = json.load(open(fiber_json)) if os.path.exists(fiber_json) else None
    tag = {'timesformer_scroll5_july_retreat': 'july_fp32', 'timesformer_GP_scroll1': 'gp_fp32',
           'timesformer_large_scroll1_01122024': 'large_fp32', 'resnet50_7.9um_scroll1_frags': 'resnet_fp32'}
    out = dict(provenance=PROV, task='ckpt-screen-c', rule='DECL-DEVLOOP-SCREEN phase 1', villa_sha=VILLA_SHA,
               root_index=ROOT_INDEX, dev_scrolls_considered=DEV_SCROLLS,
               wrapper=dict(path='tools/sib/ckpt-screen-c/screen_infer.py',
                            sha256=sha256_file(os.path.join(ROOT, 'tools/sib/ckpt-screen-c/screen_infer.py'))),
               smoke_input=dict(kind='synthetic smoothed noise (31, 384, 384) uint8, right quarter zero; no CT',
                                generator='tools/sib/ckpt-screen-c/make_smoke.py seed 20260926',
                                sha256=sha256_file('/work/ckscr/smoke/smoke384.npy')),
               cost_basis='DEV window 2136 px (2 cm at 9.362 um) + 256 px margin per side = 2648 px square; CPU '
                          'minutes per depth order = tiles / measured tiles-per-second on the smoke render, 4 threads, '
                          'fp32 (villa autocast disabled), batch 32; a screen needs both orders',
               checkpoints={})
    for name, st in STATIC.items():
        e = dict(st)
        d = dl.get(name)
        e['weights'] = dict(sha256=d['sha256'], sha256_catalogue=d['sha256_expected'], verified=d['verified'],
                            bytes=d['bytes'], url=d['url'], downloaded_utc=d['utc_end']) if d else 'NOT DOWNLOADED'
        if name in tag and tag[name] in chk['runs']:
            r = chk['runs'][tag[name]]
            e['wrapper_sha256'] = r['wrapper_sha256']
            e['smoke'] = r
            if name == 'resnet50_7.9um_scroll1_frags':
                e['cost_note'] = 'rate measured on only 9 tiles of 256 px (smoke canvas 384 px); indicative'
            e['cost_cpu_min_per_dev_window'] = dict(
                per_order={o: v['dev_window_cpu_min_est'] for o, v in r['orders'].items()},
                both_orders=round(sum(v['dev_window_cpu_min_est'] for v in r['orders'].values()), 1))
        if name == 'fiber_ink_4class_selfdistill' and fib:
            e['wrapper_sha256'] = fib['wrapper_sha256']
            e['smoke'] = {k: fib[k] for k in ('config', 'step', 'missing_keys', 'unexpected_keys', 'n_params',
                                              'forward', 'load_s') if k in fib}
        out['checkpoints'][name] = e
    for k in ('determinism_gp_fp32_vs_repeat', 'precision_gp_fp32_vs_official_cpu_autocast'):
        out[k] = chk.get(k)
    out['new_checkpoints_after_2026_09_24'] = json.load(open(os.path.join(LOGD, 'hf_listing_check.json')))
    t = json.dumps(out, indent=1) + '\n'
    assert t.isascii() and not any(0x200b <= ord(c) <= 0x206f or ord(c) == 0xFEFF for c in t)
    open(os.path.join(LOGD, 'SPECS.json'), 'w').write(t)
    print('SPECS.json', hashlib.sha256(t.encode()).hexdigest())


if __name__ == '__main__':
    main()
