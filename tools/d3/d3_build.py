# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 stage 2 displays, key, manifest and blob-f180 (RULES.md DECL-D3-A1 items 5 and 7, DECL-D3-A3 items 3-5, with
the D1 BASE v2 display of DECL-D1-A6). Numbers only; no image is opened, displayed or decoded by the builder (PNG
headers are parsed from bytes only; PNG files are only hashed).

Derived from /work/d1/scripts/d1_build_v2.py (sha256 50f8a637...109d), BASE displays only (no REF, no RAW, no AUC).
Reused, not re-implemented: d1_common (window ids, L 2136, margin 256, 31 slices, sha256 / tree_sha256 / utc /
jdefault, check_hashes of the METRIC-HASH-pinned pipeline, display builder and pixel-metric code),
d1_build_v2.png_header, hercules.display.builder (model_map_u8, area_downscale, png_bytes),
hercules.metrics.pixel.blob_f180, hercules.pipeline.window.voxel_size_from_metadata.

Per window   render-valid rv = any of the 31 D1 render slices nonzero on the 2136 px levelled state-A window (render
             px (256, 256) = window px (0, 0)); asserted equal to the D1 render record fraction.
BASE display exactly d1_build_v2: the decoded official map (OUT.tif.npy fwd, OUT_reverse.tif.npy rev; uint8,
             asserted) cropped to the window -> builder.model_map_u8 -> 0 outside rv (state A, before INTER_AREA)
             -> state B = masked state A mirrored left-right -> builder.area_downscale(., 0.5) (cv2.INTER_AREA,
             1068 x 1068 uint8) -> builder.png_bytes (IHDR/IDAT/IEND only, asserted from the bytes).
Write        one flat folder, <uuid4>.png, written in a secrets.SystemRandom-shuffled order with 'xb', equal mtimes;
             no uuid may collide with /work/d1/manifest.json (or the withdrawn D1 v1 manifest). Key O_EXCL, 0400,
             never printed.
Key          {"images": {uuid: {"window", "arm", "kind": "BASE", "order": "fwd"|"rev", "state": "A"|"B"}},
             "windows": {w: {"set": "J"|"blank"|"canary", "gate": {"pass": true|false|null}}}} from /work/d1/work/
             prep.json (set) and /work/d1/work/gate.json (J windows: their gate 'passed'; blanks and canary: null, their
             D1 gate was not binding); the gated J set is asserted equal to D1's (gate.json, /work/d1/jobs_model.json
             gated_J and the D1 build summary pooled_gated_J: J1-J5).

--dry-run-e2 (DECL-D3-A3 item 3): the D1 base maps /work/d1/work/infer/<w>/<w>.tif.npy and _reverse.tif.npy (sha256
             asserted against /work/d1/work/infer.json) stand in for one arm; 32 PNGs (8 windows x 2 orders x 2 states)
             and a key are written ONLY to /work/d3/dryrun_e2/; the 32 PNG sha256 values (in memory and from disk)
             are looked up in /work/d1/manifest.json (count found, count distinct; PASS = all 32 found and 32
             distinct); record /work/d3/work/e2_dryrun.json; the folder is then deleted with rm -rf (nothing in it is
             opened; only hashed above) and the deletion is ledgered. blob_f180 of the D1 base maps on the blanks is
             reported in the record (not written to any blob file).
--full       arms FA, NULLA, REVA, CTRL from /work/d3/infer/<ARM>/<w>/*.npy: each arm's record
             /work/d3/work/infer_<ARM>.json must have returncode 0 on all 8 windows and the checkpoint sha256 of the
             arm's summary.json model_final (and of the file on disk); map npy sha256 re-checked on disk. 128 PNGs to
             /work/d3/img/<uuid4>.png, key /srv/scorer/d3_key.json, manifest /work/d3/manifest.json {"provenance",
             "generated_utc", "n_images", "images": [{"path": "img/<uuid>.png", "sha256"}]}.
             blob-f180 (DECL-D3-A3 item 5): hercules.metrics.pixel.blob_f180(map_u8, area_cm2, valid=rv) on the
             decoded official map cropped to the 2136 px state-A window (before masking and downscale); area_cm2 =
             n_valid x (voxel mm)^2 / 100, voxel from the PHerc0139 volume metadata.json (build_r2.META = build_jseal
             META0139, read by hercules.pipeline.window.voxel_size_from_metadata as d1_prep does; asserted equal to the
             D1 prep voxel_size_um of the blanks). /work/d3/blob_f180.json = {blank id: FA forward value} (exactly the
             2 blank ids; the input format of tools/d1/score_d3.py); full table (4 arms x 2 orders x 2 blanks, n_valid,
             area_cm2, voxel size and its source) /home/user/dominion/logs/d1/d3_blob_f180.json. Build record
             /work/d3/work/build_full.json (map hashes, thread counts, key and manifest sha256).
Every build and the dry-run deletion append a row to /work/d3/work/ledger.tsv.
Usage: /opt/hv/bin/python d3_build.py --dry-run-e2|--full [--threads N]
"""
import sys
sys.dont_write_bytecode = True
import os, argparse
ap = argparse.ArgumentParser()
_g = ap.add_mutually_exclusive_group(required=True)
_g.add_argument('--dry-run-e2', action='store_true')
_g.add_argument('--full', action='store_true')
ap.add_argument('--threads', type=int, default=1, choices=(1, 2, 3))
ARGS = ap.parse_args()
sys.path.insert(0, '/work/d1/scripts')
import d1_common as K  # sets the thread env to 2 at import; overridden before numpy is imported
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = str(ARGS.threads)
import json, time, uuid, hashlib, secrets, stat, socket, subprocess
sys.path.insert(0, '/home/user/dominion/src'); sys.path.insert(0, '/work/handed/scripts')
import numpy as np
import cv2
import zarr
import d1_build_v2 as B1  # png_header; its import sets cv2 threads to 2, reset next
cv2.setNumThreads(ARGS.threads)
from hercules.display import builder as DB
from hercules.metrics import pixel as PX
from hercules.metrics.pixel import blob_f180
from hercules.pipeline import window as Wn
import build_r2 as B2  # META = PHerc0139 9.362 um volume metadata.json (= build_jseal.META0139, used by d1_prep)

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
SERVES = 'RULES.md DECL-D3D4, DECL-D3-A1 items 5 and 7, DECL-D3-A3 items 3-5 (displays as DECL-D1-A6 BASE v2)'
L, M = K.L, K.MARGIN
D3 = '/work/d3'
D3WK = f'{D3}/work'
IMG = f'{D3}/img'
MANIFEST = f'{D3}/manifest.json'
KEY = '/srv/scorer/d3_key.json'
DRY = f'{D3}/dryrun_e2'
E2REC = f'{D3WK}/e2_dryrun.json'
FULLREC = f'{D3WK}/build_full.json'
BLOB = f'{D3}/blob_f180.json'
BLOB_FULL = '/home/user/dominion/logs/d1/d3_blob_f180.json'
LEDGER = f'{D3WK}/ledger.tsv'
ARMS = ('FA', 'NULLA', 'REVA', 'CTRL')
D1_MANIFEST = '/work/d1/manifest.json'
D1_WD_MANIFEST = '/work/d1/withdrawn_v1/manifest.json'
PINS = {  # D1 sources, unchanged since the D1 build (D1 summary.json scripts / stage_files / manifest)
    '/work/d1/scripts/d1_common.py': '3ff3eb01753a568fdb65cee67f165cd9f4fd524e968d43f0ee373ade44b8848e',
    '/work/d1/scripts/d1_build_v2.py': '50f8a637d86cacc2fbc1b154f4eaba47ed36a7b52fd624b1fe1fe7f773fd109d',
    '/work/d1/scripts/d1_infer.py': 'b2289eae4880ee2bccc3825e9870a3f327697ef47f8dde2e5c470b8d3e65648e',
    '/work/d1/work/prep.json': '57da9ff24ed982527791a2579d52d8886d5c493ca217f172a9e7417fa7e09b05',
    '/work/d1/work/render.json': 'cf92fe882382be408fb05d4060c7033f8964acee4eb7fb8cbc0db9618e6fc2e0',
    '/work/d1/work/gate.json': '9cd88a987345401ddd6b5eb09eb135286decd50e96b86efdc1f91d862bccd4bd',
    '/work/d1/work/infer.json': '67ce1baf7bca8ef1815a006d1061c5c4595a93924cf2a83074f7e8bbb5f35893',
    D1_MANIFEST: '61708f722188665663d516906c489f09d77e8698cb828a829b64b3cbdab7cf0a',
}
VOX_EXPECTED_UM = 9.362


def cpu_model():
    for ln in open('/proc/cpuinfo'):
        if ln.startswith('model name'):
            return ln.split(':', 1)[1].strip()
    return 'cpu'


def ledger(command, start, end, rc, out_sha):
    row = [socket.gethostname(), f'cpus={ARGS.threads}/{os.cpu_count()} {cpu_model()}',
           command.replace('\t', ' ').replace('\n', ' '), start, end, str(rc), out_sha]
    with open(LEDGER, 'a', encoding='utf-8') as f:
        f.write('\t'.join(row) + '\n')


def jtext(obj, prov=True):
    d = {'provenance': PROV} if prov else {}
    d.update(obj)
    t = json.dumps(d, indent=1, default=K.jdefault) + '\n'
    assert t.isascii()
    return t


def jwrite(path, obj, prov=True):
    t = jtext(obj, prov)
    with open(path + '.tmp', 'w', encoding='ascii') as fh:
        fh.write(t)
    os.replace(path + '.tmp', path)
    return hashlib.sha256(t.encode('ascii')).hexdigest()


def check_inputs():
    got = {p: K.sha256(p) for p in PINS}
    bad = {p: got[p] for p in PINS if got[p] != PINS[p]}
    assert not bad, bad
    return dict(pinned_d1=got, code_and_input_sha256=K.check_hashes())


def windows_key(prep, gate):
    wins = prep['windows']
    assert tuple(wins) == K.WIDS and tuple(gate['windows']) == K.WIDS, (list(wins), list(gate['windows']))
    exp_set = dict({w: 'J' for w in K.JIDS}, **{b[0]: 'blank' for b in K.BLANKS}, **{K.CANARY[0]: 'canary'})
    out = {}
    for w in K.WIDS:
        s = wins[w]['set']
        assert s == exp_set[w], (w, s)
        g = gate['windows'][w]
        assert g['binding'] == (s == 'J'), (w, g['binding'])
        out[w] = {'set': s, 'gate': {'pass': (bool(g['passed']) if s == 'J' else None)}}
    gated = [w for w in K.JIDS if out[w]['gate']['pass']]
    d1_jobs = json.load(open('/work/d1/jobs_model.json'))['gated_J']
    d1_sum = json.load(open(f'{K.WK}/summary.json'))['auc']['pooled_gated_J']['windows']
    assert gated == list(d1_jobs) == list(d1_sum) == list(K.JIDS), (gated, d1_jobs, d1_sum)
    return out, gated


def window_rv(wid, prep, rend):
    p, r = prep['windows'][wid], rend['windows'][wid]
    assert r['returncode'] == 0
    st = zarr.open(f"{p['render_zarr']}/0", mode='r')
    x, y, w, h = p['render_crop_xywh']
    assert st.shape == (K.NSLICE, h, w) == (K.NSLICE, L + 2 * M, L + 2 * M)
    win = np.asarray(st[:, M:M + L, M:M + L])
    rv = (win > 0).any(0)
    del win
    assert abs(float(rv.mean()) - r['render_valid_frac_window']) < 1e-12
    return rv, (h, w)


def load_map(path, hw):
    mm = np.load(path)
    assert mm.shape == hw and mm.dtype == np.uint8, (mm.shape, mm.dtype)
    return np.ascontiguousarray(mm[M:M + L, M:M + L])


def base_pngs(wid, arm, maps, rv):
    """DECL-D1-A6 BASE displays, exactly the d1_build_v2 lines: model_map_u8, 0 outside render-valid (state A, before
    INTER_AREA), state B = mirrored state A, 1/2 INTER_AREA, PNG (IHDR/IDAT/IEND)."""
    inv = ~rv
    out = []
    for o in ('fwd', 'rev'):
        u8 = DB.model_map_u8(maps[o]).copy()
        u8[inv] = 0
        for state in ('A', 'B'):
            sq = u8 if state == 'A' else np.ascontiguousarray(u8[:, ::-1])
            im = DB.area_downscale(sq, 0.5)
            assert im.dtype == np.uint8 and im.shape == (1068, 1068), im.shape
            png = DB.png_bytes(im)
            types, ih = B1.png_header(png)
            assert set(types) <= {'IHDR', 'IDAT', 'IEND'} and ih['width'] == ih['height'] == 1068 and ih['bit_depth'] == 8 \
                and ih['color_type'] == 0, (types, ih)
            out.append(dict(png=png, sha256=hashlib.sha256(png).hexdigest(),
                            key=dict(window=wid, arm=arm, kind='BASE', order=o, state=state)))
    return out


def voxel(prep):
    vox = Wn.voxel_size_from_metadata(B2.META)
    assert abs(vox - VOX_EXPECTED_UM) < 1e-9, vox
    for b in K.BLANKS:
        assert prep['windows'][b[0]]['voxel_size_um'] == vox, (b[0], prep['windows'][b[0]]['voxel_size_um'], vox)
    return dict(voxel_size_um=vox, voxel_size_mm=vox / 1000.0, metadata_json=B2.META, metadata_sha256=K.sha256(B2.META),
                reader='hercules.pipeline.window.voxel_size_from_metadata (scan.tomo.acquisition.detector.samplePixelSize, mm)',
                same_as_d1='build_jseal.META0139 = build_r2.META, read the same way in d1_prep.py (asserted 9.362); '
                           'equal to /work/d1/work/prep.json voxel_size_um of both blanks')


def blob(map_u8, rv, vox_mm):
    n_valid = int(rv.sum())
    area = n_valid * vox_mm ** 2 / 100.0
    return dict(value=blob_f180(map_u8, area, valid=rv), n_valid=n_valid, area_cm2=area,
                k_components=max(1, int(round(10.0 * area / PX.BLOB_AREA_UNIT_CM2))))


def write_set(imgs, img_dir, key_path, key_obj):
    """Shuffled write order (secrets.SystemRandom), new uuid4 names, 'xb', equal mtimes; key O_EXCL 0400 (never
    printed). No uuid may collide with the D1 manifests."""
    d1_uuids = set()
    for mp in (D1_MANIFEST, D1_WD_MANIFEST):
        d1_uuids |= {os.path.basename(e['path'])[:-4] for e in json.load(open(mp))['images']}
    rng = secrets.SystemRandom()
    rng.shuffle(imgs)
    keyimgs = {}
    for it in imgs:
        u = str(uuid.uuid4())
        assert u not in keyimgs and u not in d1_uuids
        it['u'] = u
        keyimgs[u] = it['key']
    key_obj = dict(key_obj, images=keyimgs)
    key_text = jtext(key_obj)
    kk = json.loads(key_text)
    per = {}
    for v in kk['images'].values():
        t = (v['window'], v['arm'], v['kind'], v['order'], v['state'])
        per[t] = per.get(t, 0) + 1
    assert len(kk['images']) == len(imgs) and all(n == 1 for n in per.values())
    del kk
    os.makedirs(img_dir, exist_ok=False)
    for it in imgs:
        with open(f"{img_dir}/{it['u']}.png", 'xb') as fh:
            fh.write(it['png'])
    tnow = time.time()
    for it in imgs:
        os.utime(f"{img_dir}/{it['u']}.png", (tnow, tnow))
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(fd, 'w', encoding='ascii') as fh:
        fh.write(key_text)
    os.chmod(key_path, 0o400)
    key_sha = hashlib.sha256(key_text.encode('ascii')).hexdigest()
    ver = dict(key_mode_octal=oct(stat.S_IMODE(os.stat(key_path).st_mode)), key_size_equals_text=os.stat(key_path).st_size == len(key_text),
               uuid_collisions_with_d1=0, n_d1_uuids_checked=len(d1_uuids))
    assert ver['key_mode_octal'] == '0o400' and ver['key_size_equals_text']
    return key_sha, ver


def disk_hashes(img_dir, imgs):
    files = sorted(os.listdir(img_dir))
    pngs = [f for f in files if f.endswith('.png')]
    disk = {f[:-4]: K.sha256(f'{img_dir}/{f}') for f in pngs}
    mem = {it['u']: it['sha256'] for it in imgs}
    return files, disk, dict(n_png_files=len(pngs), memory_equals_disk=(disk == mem))


def dry_run_e2():
    t0 = time.time(); start = K.utc()
    assert not os.path.exists(DRY), 'dry-run folder exists'
    hashes = check_inputs()
    prep = json.load(open(f'{K.WK}/prep.json'))
    rend = json.load(open(f'{K.WK}/render.json'))
    gate = json.load(open(f'{K.WK}/gate.json'))
    inf = json.load(open(f'{K.WK}/infer.json'))
    wkey, gated = windows_key(prep, gate)
    vx = voxel(prep)
    imgs, blobs = [], {}
    for wid in K.WIDS:
        assert inf['windows'][wid]['returncode'] == 0
        rv, hw = window_rv(wid, prep, rend)
        maps = {}
        for o, f in (('fwd', f'{K.INF}/{wid}/{wid}.tif.npy'), ('rev', f'{K.INF}/{wid}/{wid}_reverse.tif.npy')):
            assert K.sha256(f) == inf['windows'][wid]['outputs'][os.path.basename(f)]['sha256'], f
            maps[o] = load_map(f, hw)
        imgs += base_pngs(wid, 'D1BASE_DRYRUN', maps, rv)
        if wid in [b[0] for b in K.BLANKS]:
            blobs[wid] = {o: blob(maps[o], rv, vx['voxel_size_mm']) for o in ('fwd', 'rev')}
        K.log(wid, 'dry-run displays', 't %.1f' % (time.time() - t0))
        del maps, rv
    assert len(imgs) == 32
    key_sha, ver = write_set(imgs, DRY, f'{DRY}/key.json', dict(serves=SERVES + ' | E2 DRY RUN (scratch, deleted unread)',
                                                               windows=wkey))
    files, disk, dver = disk_hashes(DRY, imgs)
    tree = K.tree_sha256(DRY)
    end = K.utc()
    ledger(f'/opt/hv/bin/python {os.path.abspath(__file__)} --dry-run-e2 --threads {ARGS.threads} (write phase: '
           f'32 PNG + key to {DRY})', start, end, 0, tree)
    d1_sha = [e['sha256'] for e in json.load(open(D1_MANIFEST))['images']]
    d1_set = set(d1_sha)
    vals = list(disk.values())
    found = sum(1 for s in vals if s in d1_set)
    n_distinct = len(set(vals))
    per = {}
    for it in imgs:
        c = f"{it['key']['order']}|{it['key']['state']}"
        e = per.setdefault(c, dict(n=0, found_in_d1_manifest=0))
        e['n'] += 1
        e['found_in_d1_manifest'] += int(it['sha256'] in d1_set)
    rec = dict(generated_utc=K.utc(), serves=SERVES, stage='E2 dry run (DECL-D3-A3 item 3)',
               viewing='no image or pixel array was opened, displayed or described; the dry-run PNGs were only hashed; numbers only',
               inputs=hashes, maps='D1 base maps /work/d1/work/infer/<w>/<w>.tif.npy and _reverse.tif.npy (sha256 = infer.json)',
               n_windows=len(K.WIDS), n_png=len(vals), n_files_in_folder=len(files), disk_check=dver,
               n_sha_found_in_d1_manifest=found, n_distinct_sha=n_distinct, n_d1_manifest_images=len(d1_sha),
               n_d1_manifest_distinct_sha=len(d1_set), per_order_state=per,
               E2_pass=bool(found == 32 and n_distinct == 32 and len(vals) == 32 and dver['memory_equals_disk']),
               key=dict(path=f'{DRY}/key.json', sha256=key_sha, verify=ver, windows=wkey, gated_J=gated),
               dryrun_tree_sha256=tree, voxel=vx,
               blob_f180_d1_base_reported_only=blobs, threads=ARGS.threads,
               script=dict(path=os.path.abspath(__file__), sha256=K.sha256(os.path.abspath(__file__))),
               seconds_build=round(time.time() - t0, 1))
    jwrite(E2REC, rec)
    # ---- delete the scratch folder (nothing in it is opened) and ledger the deletion ----
    cmd = ['rm', '-rf', DRY]
    ds = K.utc()
    pr = subprocess.run(cmd)
    de = K.utc()
    ledger(' '.join(cmd), ds, de, pr.returncode, '-')
    rec['deletion'] = dict(command=' '.join(cmd), start_utc=ds, end_utc=de, returncode=pr.returncode,
                           folder_exists_after=os.path.exists(DRY), deleted_tree_sha256=tree)
    jwrite(E2REC, rec)
    K.log('E2', 'png', len(vals), 'found', found, 'distinct', n_distinct, 'pass', rec['E2_pass'],
          'deleted', not rec['deletion']['folder_exists_after'])
    assert pr.returncode == 0 and not os.path.exists(DRY)


def full():
    t0 = time.time(); start = K.utc()
    for p in (IMG, MANIFEST, BLOB, BLOB_FULL, FULLREC):
        assert not os.path.exists(p), p
    assert not os.path.exists(KEY), 'key exists'   # stat only, as d1_build_v2; nothing under /srv/scorer is read
    hashes = check_inputs()
    prep = json.load(open(f'{K.WK}/prep.json'))
    rend = json.load(open(f'{K.WK}/render.json'))
    gate = json.load(open(f'{K.WK}/gate.json'))
    wkey, gated = windows_key(prep, gate)
    vx = voxel(prep)
    arm_rec = {}
    for arm in ARMS:
        ck = f'{D3}/runs/{arm}/model_final.pth'
        ms = json.load(open(f'{D3}/runs/{arm}/summary.json'))['model_final']['sha256']
        assert K.sha256(ck) == ms, arm
        rec = json.load(open(f'{D3WK}/infer_{arm}.json'))
        assert rec['arm'] == arm and rec['checkpoint']['sha256'] == ms and rec['checkpoint']['summary_model_final_sha256'] == ms
        ws = {}
        for w in K.WIDS:
            e = rec['windows'][w]
            assert e['returncode'] == 0 and e['checkpoint_sha256'] == ms, (arm, w)
            ws[w] = dict(threads=e['threads'], seconds=e['seconds'], output_dir_tree_sha256=e['output_dir_tree_sha256'],
                         layer_indices_forward=e['layer_indices_forward'], layer_indices_reverse=e['layer_indices_reverse'],
                         npy_sha256={k: v['sha256'] for k, v in e['outputs'].items() if k.endswith('.npy')},
                         tif_sha256={k: v['sha256'] for k, v in e['outputs'].items() if k.endswith('.tif')})
        arm_rec[arm] = dict(model_final=dict(path=ck, sha256=ms), infer_record=f'{D3WK}/infer_{arm}.json',
                            infer_record_sha256=K.sha256(f'{D3WK}/infer_{arm}.json'), infer_script_sha256=rec['script']['sha256'],
                            windows=ws)
    imgs, table = [], {a: {'fwd': {}, 'rev': {}} for a in ARMS}
    blank_info = {}
    for wid in K.WIDS:
        rv, hw = window_rv(wid, prep, rend)
        for arm in ARMS:
            maps = {}
            for o, f in (('fwd', f'{D3}/infer/{arm}/{wid}/{wid}.tif.npy'), ('rev', f'{D3}/infer/{arm}/{wid}/{wid}_reverse.tif.npy')):
                assert K.sha256(f) == arm_rec[arm]['windows'][wid]['npy_sha256'][os.path.basename(f)], f
                maps[o] = load_map(f, hw)
            imgs += base_pngs(wid, arm, maps, rv)
            if wid in [b[0] for b in K.BLANKS]:
                for o in ('fwd', 'rev'):
                    b = blob(maps[o], rv, vx['voxel_size_mm'])
                    table[arm][o][wid] = b['value']
                    blank_info[wid] = dict(n_valid=b['n_valid'], area_cm2=b['area_cm2'], k_components=b['k_components'],
                                           render_valid_frac=float(rv.mean()))
            del maps
        K.log(wid, 'displays', 't %.1f' % (time.time() - t0))
        del rv
    assert len(imgs) == 128
    key_sha, ver = write_set(imgs, IMG, KEY, dict(windows=wkey))
    files, disk, dver = disk_hashes(IMG, imgs)
    assert dver['memory_equals_disk'] and dver['n_png_files'] == 128 and len(files) == 128
    man = sorted((dict(path=f'img/{u}.png', sha256=s) for u, s in disk.items()), key=lambda e: e['path'])
    gen = K.utc()
    man_sha = jwrite(MANIFEST, dict(generated_utc=gen, n_images=len(man), images=man))
    blanks = [b[0] for b in K.BLANKS]
    deciding = {w: table['FA']['fwd'][w] for w in blanks}
    blob_sha = jwrite(BLOB, deciding, prov=False)     # exactly {blank id: FA forward value} (score_d3.py input)
    full_tab = dict(generated_utc=gen, serves='RULES.md DECL-D3-A1 item 7, DECL-D3-A3 item 5',
                    rule='hercules.metrics.pixel.blob_f180(map_u8, area_cm2, valid) on the decoded official map (uint8) '
                         'cropped to the 2136 px levelled state-A window (before masking and downscale); valid = render-valid '
                         '(any of 31 slices nonzero); area_cm2 = n_valid x (voxel mm)^2 / 100; threshold %d, K = max(1, '
                         'round(10 area_cm2 / %.3f))' % (PX.BLOB_THRESHOLD, PX.BLOB_AREA_UNIT_CM2),
                    deciding=dict(arm='FA', order='fwd (text order, TEXT-ORDER-D1)', values=deciding, file=BLOB, file_sha256=blob_sha),
                    values=table, blanks=blank_info, voxel=vx)
    full_sha = jwrite(BLOB_FULL, full_tab)
    ver.update(dver, n_files=len(files), manifest_sha256=K.sha256(MANIFEST))
    counts = {}
    for it in imgs:
        c = f"{it['key']['arm']}|{it['key']['state']}"
        counts[c] = counts.get(c, 0) + 1
    rec = dict(generated_utc=gen, serves=SERVES, stage='D3 display build (full)',
               viewing='no image or pixel array was opened, displayed or described; numbers only',
               inputs=hashes, arms=arm_rec, n_images=len(man), counts_arm_state=counts, key_path=KEY, key_sha256=key_sha,
               verify=ver, manifest=dict(path=MANIFEST, sha256=man_sha), windows=wkey, gated_J=gated,
               blob_f180=dict(file=BLOB, sha256=blob_sha, full_table=BLOB_FULL, full_table_sha256=full_sha),
               threads=ARGS.threads, seconds=round(time.time() - t0, 1),
               script=dict(path=os.path.abspath(__file__), sha256=K.sha256(os.path.abspath(__file__))))
    jwrite(FULLREC, rec)
    ledger(f'/opt/hv/bin/python {os.path.abspath(__file__)} --full --threads {ARGS.threads}', start, K.utc(), 0, man_sha)
    K.log('build done', 'images', len(man), counts, 'manifest', man_sha, 'key', key_sha, 't %.1f' % (time.time() - t0))


if __name__ == '__main__':
    if ARGS.dry_run_e2:
        dry_run_e2()
    else:
        full()
