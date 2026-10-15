# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 stage 2 pre-check E1 (RULES.md DECL-D3-A3 item 2). Numbers only; no image or pixel array is displayed.

make     writes /work/d3/runs/BASE0/model_final.pth = {'model': base state_dict, 'config': the base checkpoint's embedded
         config, 'step': 0, 'd3': {'arm': 'BASE0', 'purpose': 'E1 equivalence pre-check'}}, built exactly as
         /work/d3/scripts/d3_train.py builds its final save: load_checkpoint(base), base_config = deepcopy(config),
         TrainingConfig from the arm mapping (seed 20260925, AdamW lr 2e-5, wd 3e-5, batch 8, 2000 iterations),
         make_model, load_model_state + strict load_state_dict of the base 'model', torch.save of model.state_dict()
         via .tmp + os.replace. Every saved tensor is compared with the base checkpoint's (counts only).
         Run with /opt/hv-ink/bin/python and PYTHONPATH=/work/d3_timing/pylib (the d3_train.py environment).
compare  compares the decoded BASE0 canary maps (/work/d3/infer/BASE0/<canary>/*.tif.npy, from d3_infer.py) with D1's
         (/work/d1/work/infer/<canary>/*.tif.npy): dtype, shape, file sha256, bitwise equality, n_diff px, fraction,
         max |diff|. PASS: both orders bitwise identical, or max |diff| <= 1 on <= 0.1 % of px (uint8; if a map were
         float the rule is applied to builder.model_map_u8 of it, the uint8 the display path uses).
         Output /work/d3/work/e1.json.
"""
import sys
sys.dont_write_bytecode = True
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import json, copy, random, hashlib, datetime

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
CK = '/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth'
CK_SHA = 'e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab'
TRAIN = '/work/d3/scripts/d3_train.py'
OUT = '/work/d3/runs/BASE0'
FINAL = f'{OUT}/model_final.pth'
CAN = 'canary_w044_y2816_x2816'
D1INF = f'/work/d1/work/infer/{CAN}'
D3INF = f'/work/d3/infer/BASE0/{CAN}'
REC = '/work/d3/work/e1.json'
SEED, LR, WD, BATCH, STEPS = 20260925, 2e-5, 3e-5, 8, 2000


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def jwrite(path, obj):
    d = {'provenance': PROV}
    d.update(obj)
    with open(path + '.tmp', 'w', encoding='ascii') as fh:
        fh.write(json.dumps(d, indent=1) + '\n')
    os.replace(path + '.tmp', path)


def make():
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from vesuvius.ink_detection.config import TrainingConfig, resolve_training_mapping
    from vesuvius.ink_detection.models.model import make_model
    from vesuvius.ink_detection.models.checkpoint import load_checkpoint, load_model_state
    assert not os.path.exists(FINAL), 'BASE0 model_final exists'
    os.makedirs(OUT, exist_ok=True)
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    ck_sha = sha256(CK)
    assert ck_sha == CK_SHA, ck_sha
    ck = load_checkpoint(CK)
    base_config = copy.deepcopy(ck['config'])
    mapping = copy.deepcopy(ck['config'])
    mapping.update(optimizer='adamw', learning_rate=LR, weight_decay=WD, batch_size=BATCH, num_iterations=STEPS,
                   seed=SEED, out_dir=OUT)
    mapping['fixed_scroll_prior'] = dict(mapping['fixed_scroll_prior'], seed=SEED)
    tc = TrainingConfig.from_mapping(resolve_training_mapping(mapping))
    model = make_model(tc.ink)
    load_model_state(model, ck['model'])
    strict = str(model.load_state_dict(ck['model'], strict=True))
    sd = model.state_dict()
    keys_equal = list(sd.keys()) == list(ck['model'].keys())
    same_set = set(sd) == set(ck['model'])
    n_equal = sum(1 for k in sd if k in ck['model'] and sd[k].dtype == ck['model'][k].dtype
                  and sd[k].shape == ck['model'][k].shape and torch.equal(sd[k], ck['model'][k]))
    tmp = FINAL + '.tmp'
    torch.save({'model': model.state_dict(), 'config': base_config, 'step': 0,
                'd3': {'arm': 'BASE0', 'purpose': 'E1 equivalence pre-check'}}, tmp)
    os.replace(tmp, FINAL)
    chk = torch.load(FINAL, map_location='cpu', weights_only=False)
    rec = dict(generated_utc=utc(), stage='E1 make BASE0', viewing='no image was opened; numbers only',
               construction='as d3_train.py final save (make_model + load_model_state + strict load of the base model; '
                            'config = deepcopy of the base embedded config; step 0)',
               d3_train=dict(path=TRAIN, sha256=sha256(TRAIN)), base_checkpoint=dict(path=CK, sha256=ck_sha),
               base_top_keys=sorted(ck.keys()), strict_load=strict, n_tensors=len(sd), n_base_tensors=len(ck['model']),
               key_order_equal=keys_equal, key_set_equal=same_set, n_tensors_bitwise_equal_to_base=n_equal,
               config_equal_to_base=(chk['config'] == ck['config']), saved_top_keys=sorted(chk.keys()), saved_step=chk['step'],
               saved_d3=chk['d3'], model_final=dict(path=FINAL, sha256=sha256(FINAL), bytes=os.path.getsize(FINAL)),
               script=dict(path=os.path.abspath(__file__), sha256=sha256(os.path.abspath(__file__))))
    assert same_set and n_equal == len(sd) == len(ck['model']) and rec['config_equal_to_base']
    old = json.load(open(REC)) if os.path.exists(REC) else {}
    old.pop('provenance', None)
    old['make'] = rec
    jwrite(REC, old)
    print(json.dumps({k: v for k, v in rec.items() if k not in ('base_top_keys', 'saved_d3')}))


def compare():
    import numpy as np
    sys.path.insert(0, '/home/user/dominion/src')
    inf = json.load(open('/work/d3/work/infer_BASE0.json'))
    assert inf['windows'][CAN]['returncode'] == 0
    out = dict(generated_utc=utc(), stage='E1 compare', viewing='no image or pixel array was opened or displayed; numbers only',
               d1_threads=2, e1_threads=inf['windows'][CAN]['threads'], base0_checkpoint=inf['checkpoint'],
               rule='PASS if both orders bitwise identical, or max |diff| <= 1 (uint8) on <= 0.1 % of px', orders={})
    passes = []
    for o, suf in (('fwd', ''), ('rev', '_reverse')):
        fa, fb = f'{D1INF}/{CAN}{suf}.tif.npy', f'{D3INF}/{CAN}{suf}.tif.npy'
        a, b = np.load(fa), np.load(fb)
        ent = dict(d1=dict(path=fa, dtype=str(a.dtype), shape=list(a.shape), sha256=sha256(fa),
                           tif_sha256=sha256(fa[:-4])),
                   e1=dict(path=fb, dtype=str(b.dtype), shape=list(b.shape), sha256=sha256(fb),
                           tif_sha256=sha256(fb[:-4])))
        ent['same_dtype_shape'] = (a.dtype == b.dtype and a.shape == b.shape)
        if a.dtype != np.uint8 or b.dtype != np.uint8:
            from hercules.display import builder as DB
            ent['note'] = 'float output; rule applied to builder.model_map_u8 (display uint8)'
            a, b = DB.model_map_u8(a), DB.model_map_u8(b)
        ent['bitwise_equal'] = bool(ent['same_dtype_shape'] and np.array_equal(a, b))
        if a.shape == b.shape:
            d = np.abs(a.astype(np.int16) - b.astype(np.int16))
            nd = int((d > 0).sum())
            ent.update(n_px=int(d.size), n_diff_px=nd, frac_diff=nd / d.size, max_abs_diff=int(d.max()),
                       n_diff_gt1=int((d > 1).sum()), sum_abs_diff=int(d.sum()))
            ok = ent['bitwise_equal'] or (ent['max_abs_diff'] <= 1 and ent['frac_diff'] <= 0.001)
        else:
            ok = False
        ent['pass'] = bool(ok)
        passes.append(ok)
        out['orders'][o] = ent
    out['E1_pass'] = bool(all(passes))
    out['script'] = dict(path=os.path.abspath(__file__), sha256=sha256(os.path.abspath(__file__)))
    old = json.load(open(REC)) if os.path.exists(REC) else {}
    old.pop('provenance', None)
    old['compare'] = out
    jwrite(REC, old)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    {'make': make, 'compare': compare}[sys.argv[1]]()
