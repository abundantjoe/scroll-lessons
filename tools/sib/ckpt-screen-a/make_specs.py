# Provenance: Project HERCULES | owner the owner | [id removed]
"""Assemble logs/sib/ckpt-screen-a/SPECS.json (task ckpt-screen-a, DECL-DEVLOOP-SCREEN phase 1) from the verified
downloads, the official cards and code, and the synthetic smoke records (wrap.json). Numbers and hashes only.
Cost per DEV window = measured seconds per tile (synthetic, every tile non-empty = worst case) x the tile count of
a 2 x 2 cm window at 9.362 um (2136 px) plus the devloop render margin of 256 px per side (2648 x 2648 px)."""
import datetime
import glob
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'logs/sib/ckpt-screen-a/SPECS.json')
SMOKE = '/work/sa/smoke'
PROV = 'Project HERCULES | owner the owner | [id removed]'
VOX = 9.362
WIN_PX = 2136
CROP_PX = WIN_PX + 2 * 256


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def n_starts(length, patch, stride):
    """Tile origins per axis (official infer _sliding_positions_1d / hecate axis_starts: 0, stride, ..., last)."""
    if length <= patch:
        return 1
    return len(range(0, length - patch, stride)) + 1


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    wrap_sha = sha256(os.path.join(HERE, 'screen_wrap.py'))
    ink = load(f'{SMOKE}/ink9_512/wrap.json')
    hec = load(f'{SMOKE}/hec_512/wrap.json')
    src = os.path.join(REPO, 'logs/sib/ckpt-screen-a/sources')
    sources = {os.path.basename(p): sha256(p) for p in sorted(glob.glob(f'{src}/*'))}

    # ---- ink_9um seed43
    t_ink = n_starts(512, 128, 64) ** 2  # tiles per direction in the 512 px smoke
    ink_s = None
    if ink and ink['returncode'] == 0:
        ink_s = ink['seconds'] / (2 * t_ink)  # includes model load twice (upper bound)
    tw_ink = n_starts(CROP_PX, 128, 64) ** 2
    ink_cost = None if ink_s is None else dict(
        tiles_per_direction=tw_ink, directions=2, seconds_per_tile_measured=round(ink_s, 4),
        wall_minutes_4threads=round(2 * tw_ink * ink_s / 60, 1),
        cpu_minutes_upper=round(4 * 2 * tw_ink * ink_s / 60, 1))

    # ---- hecate 9.6 um
    r = 9.6 / VOX
    hs = int(math.floor(512 / r))
    t_hec = n_starts(hs, 64, 32) ** 2
    hec_s = None
    if hec and hec['returncode'] == 0:
        hec_s = sum(v['seconds'] for v in hec['runs'].values()) / (2 * t_hec)
    hw = int(math.floor(CROP_PX / r))
    tw_hec = n_starts(hw, 64, 32) ** 2
    hec_cost = None if hec_s is None else dict(
        grid_px_9p6=hw, tiles_per_direction=tw_hec, directions=2, seconds_per_tile_measured=round(hec_s, 4),
        wall_minutes_4threads=round(2 * tw_hec * hec_s / 60, 1),
        cpu_minutes_upper=round(4 * 2 * tw_hec * hec_s / 60, 1))

    def smoke_summary(w):
        if not w:
            return None
        if w['kind'] == 'ink9':
            return dict(input='synthetic (31, 512, 512) uint8, seed 20260926 (make_synth.py)', seconds=w['seconds'],
                        threads=w['threads'], returncode=w['returncode'], outputs=w.get('outputs'))
        return dict(input='synthetic (31, 512, 512) uint8, seed 20260926 (make_synth.py)', seconds=w['seconds'],
                    threads=w['threads'], returncode=w['returncode'], resample=w['resample'],
                    input96_sha256=w['input_sha256'],
                    runs={k: dict(seconds=v['seconds'], returncode=v['returncode'], map96=v.get('map96'),
                                  output=v.get('output')) for k, v in w['runs'].items()})

    specs = {
        'provenance': PROV,
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'task': 'ckpt-screen-a (DECL-DEVLOOP-SCREEN phase 1: specs, wrappers, smoke, cost; no DEV map made)',
        'viewing': 'no image, map, render or CT pixel was opened, viewed or described; arrays summarised by hashes and counts',
        'wrapper': dict(path='tools/sib/ckpt-screen-a/screen_wrap.py', sha256=wrap_sha,
                        selftest='screen_wrap.py selftest (geometry; see runs.jsonl label wrap_selftest)'),
        'map_format': ('devloop evaluate.py load_map: <out>/<wid>.tif (forward) and <out>/<wid>_reverse.tif, 2-D uint8 '
                       'TIFF in the Y,X frame of the devloop render.zarr (31 slices, 9.362 um, --flip-normals)'),
        'sources_sha256': sources,
        'window_cost_basis': dict(window_px=WIN_PX, render_crop_px=CROP_PX, voxel_um=VOX,
                                  note='synthetic smoke, every tile non-empty (real windows skip empty tiles: cost '
                                       'is an upper bound); fp32, CPU, 4 threads'),
        'checkpoints': {
            'ink_9um_seed43_step075000': dict(
                repo='scrollprize/ink_9um', commit='7109667e2607db1b90c37c8b09cb876ea7fe7bb1',
                file='hybrid_3d2d-seed43/step-075000.pth', bytes=138360231,
                sha256='2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f',
                sha256_catalogue='2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f',
                sha256_match=True, licence='MIT (card YAML); not gated',
                card_readme_sha256='ef0f3cf3186e9d05c8816718c4024aeb356e27a8c02d7da1bacdee113c5ef273',
                status='SCREENABLE',
                official_code=dict(repo='ScrollPrize/villa', commit='41701aa0eaa1aa765523db3f9f972b5830abf549',
                                   module='vesuvius.ink_detection.inference.infer',
                                   note='card names koine_machines.inference.infer on branch merge-ink-pipelines; the pinned '
                                        'villa commit carries the same checkpoint-driven flat inference as '
                                        'vesuvius.ink_detection.inference.infer (weights load strictly: 0 missing, 0 '
                                        'unexpected keys; same module and flags as the devloop base run)'),
                input_spec=dict(
                    voxel_um='~9 um isotropic surface volume (card: native 9.362 um renders work directly; trained on '
                             '2.399 um pooled to ~9.6 um plus 5 native 9.362 um segments)',
                    slices='checkpoint patch depth 17 (training window 17 of 21 with z jitter +-2); the official infer '
                           'centre-crops 17 of the render slices: indices 7..23 of 31 (centre 15 = mesh surface)',
                    normalisation='robust_mad, percentiles 1/99 (checkpoint config; infer preprocessing tifxyz_robust)',
                    orientation='forward = render slice order (index 7 -> 23); reverse = 23 -> 7 (--direction both); '
                                'the card and code document no ink-side orientation: text order UNDOCUMENTED',
                    tile='128 x 128, stride 64 (infer default overlap 0.5), Hann blend, no TTA, fp32 on CPU',
                    output='2-D uint8 TIFF, probability x 255 truncated; BCE label smoothing 0.5 (card: no-ink floor '
                           'near 0.25 -> ~64)'),
                training_data=dict(
                    status='DOCUMENTED (embedded checkpoint config, datasets[].segments)',
                    source='sources/ink9_seed43_step075000_embedded_config.json',
                    segments={'PHerc0139 (2.399 um pooled)': ['w016', 'w017', 'w028', 'w029', 'w035', 'w039', 'w040',
                                                               'w041', 'w043'],
                              'PHerc0139 (native 9.362 um)': ['w035', 'w039', 'w040', 'w041', 'w044'],
                              'PHerc0814': ['46527'],
                              'PHerc1667': ['w013', 'w018', 'w023', 'w028', 'w029', 'w031'],
                              'PHercParis4': ['w00', 'w01', 'w02', 'w03', 'w05', 'w06', 'w07', 'w09']},
                    reserved_validation_cases=['pherc0139-w016', 'pherc0139-w028', 'pherc0139-w029', 'pherc0814-46527',
                                               'pherc1667-w018', 'pherc1667-w023', 'pherc1667-w028',
                                               'pherc1667-w029', 'pherc1667-w031'],
                    guard_note='fail-closed: every listed segment (validation cases included) is treated as training '
                               'papyrus. DEV scrolls PHerc0139 and PHerc0814 are in the list, so the guard is per '
                               'window: same-papyrus with a listed segment -> IN-SAMPLE. The list equals the devloop '
                               'registry base-training traces (0139 w028-w044, 0814 46527; registry adds w030, w045, '
                               'w046 and marks w016/w017 as having no S3 segment); DEV segments 0139 w024, w047, w053 '
                               'and 0814 165636, 204843 are not in it by name.'),
                smoke=smoke_summary(ink), cost_per_window=ink_cost),
            'hecate_9.6um': dict(
                repo='scrollprize/hecate', commit='9cb86e500e944b11a06a7020403cde5dffb5bcb2',
                file='hecate_9.6um.pth', bytes=522576086,
                sha256='809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d',
                sha256_catalogue='809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d',
                sha256_match=True, licence='MIT (LICENSE file sha256 85b6c05e...; card YAML); not gated',
                card_readme_sha256='17d7f029ffcff421dbf767c89e0e36a91f141fdfb5a647cc254e4c88cffabe9e',
                status='SCREENABLE',
                official_code=dict(file='hecate.py (repo scrollprize/hecate, same commit)',
                                   sha256='c232c18a1a86cfb91257a00db13288202bb8ae33732ba26f7291a9b8adb8da59',
                                   run='unchanged; sha256 checked by the wrapper before every run'),
                input_spec=dict(
                    voxel_um='9.6 um in all three axes (card; script checks --spacing-um within 2 % and does not '
                             'resample)',
                    slices='16 planes (patch 16 x 64 x 64); script takes the central 16 of the input depth. Wrapper '
                           'input = the 16 planes a native vc_render_tifxyz -n 16 --slice-step 9.6 um render holds: '
                           'offsets (j - 7.5) x 9.6 um = -72..+72 um about the mesh (render slices 7.309..22.691 of 31), '
                           'in-plane 9.6 um pixel centres, trilinear from the 9.362 um devloop render',
                    normalisation='divide by 255, no clipping (checkpoint config checked by load_model)',
                    orientation='input Z,Y,X uint8; --reverse flips the full depth before the central planes; card: '
                                '"if the correct direction is unknown, run both": text order UNDOCUMENTED',
                    tile='64 x 64, stride 32 (half patch), floored Hann blend, batch 1, fp32 on CPU; empty CT columns -> 0',
                    output='2-D PNG round(255 p) on the 9.6 um grid -> wrapper maps back to the 9.362 um render grid '
                           '(inverse pixel-centre bilinear, uint8 TIFF)',
                    deviation_from_prior_screen='HECATE-SCREEN (0841) rendered natively at 9.6 um with vc_render_tifxyz; '
                                                'this wrapper resamples the shared 31-slice DEV render (self-test: '
                                                'round-trip centroid shift <= 0.006 px, affine error 2e-5)'),
                training_data=dict(
                    status='UNKNOWN (card names no segment list)',
                    card_says='no new manual labels; 2-D supervision from "the Scroll Prize ink dataset" '
                              '(hf bucket scrollprize/datasets/ink); 3-D teachers ink_3d_dino_guided (Paris 4) and an '
                              'unnamed weaker model on other scrolls; 9.6 um targets from the 2.4 um model; native '
                              'coarse renders aligned where both scans exist (scrolls not named); base '
                              'scrollprize/ink_canonical_2um',
                    named_dataset_listing=dict(
                        top_level=['0009b', '0139', '0500p2', '1667', '814', '841', 'man5', 'phercparis4', 'unused'],
                        PHerc0139=['w016', 'w017', 'w028', 'w029', 'w030', 'w035', 'w039', 'w040', 'w041', 'w043',
                                   'w044'],
                        PHerc0814=['46527'],
                        listing_files='sources/hf_bucket_ink_*.json',
                        refused='listing of ink/unused/0139 was refused by the session permission layer; recorded, '
                                'not worked around'),
                    guard_note='both DEV scrolls (0139, 0814) appear in the named dataset, so per DECL-DEVLOOP-SCREEN '
                               'item 3 every DEV window is UNKNOWN and cannot count toward FINALIST (reported only). '
                               'By name the dataset segments on DEV scrolls are the registry base-training traces '
                               '(already masked by R3), but the card does not say which were used, and the native '
                               'coarse-scan alignment set is unnamed.'),
                smoke=smoke_summary(hec), cost_per_window=hec_cost),
            'ink_3d_dino_guided': dict(
                repo='scrollprize/ink_3d_dino_guided', commit='73a79525466037432191284dfa237baf830c49ec',
                status='NOT SCREENED (card and config document a 2.400 um input only; DECL-DEVLOOP-SCREEN item 1 '
                       'screens it only if the card documents a 9-10 um input)',
                card_readme_sha256='2b83f26a7361dc3e23e20926c404845b26c7990bc3c8cabc94d735880396790e',
                config_json_sha256='7f3e817016c581b1827e1aad076a9c3bb1163c41e68d3ab98e380d06baf63849',
                evidence='config datasets[0].volume_path = PHercParis4 20260411134726-2.400um volume, volume_scale 0; '
                         'patch 256^3 full-3D, percentile_minmax; card: trained on 8-scroll surface labels + Paris 4',
                weights_downloaded=False,
                weights_sha256_catalogue={'ckpt_78k_fullsup.pth': '5a148c2c1bb730bfa683f2b3e3cdfc2000424003605e42300b527ff90118b303'}),
        },
    }
    with open(OUT, 'w') as f:
        json.dump(specs, f, indent=1)
        f.write('\n')
    print(OUT, sha256(OUT))


if __name__ == '__main__':
    main()
