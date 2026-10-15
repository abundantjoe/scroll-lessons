# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 stage 2 inference (RULES.md DECL-D3D4, DECL-D3-A1 item 5, DECL-D3-A3 items 1-2). Numbers only; no image is viewed.

A copy of /work/d1/scripts/d1_infer.py (sha256 b2289eae...648e) with ONLY these changes:
  --arm      checkpoint = /work/d3/runs/<ARM>/model_final.pth (ARM in CTRL FA NULLA REVA, or BASE0 = the E1 pre-check
             checkpoint of DECL-D3-A3 item 2). Its sha256 is computed and recorded (not asserted against the base); when
             the arm's summary.json exists, its model_final sha256 is recorded too and must equal the file's.
  --threads  OMP/MKL/OPENBLAS/NUMEXPR threads of the official infer and of the decode (DECL-D3-A3 item 1: 1 while an
             arm trains, 3 after training ends); the count used is recorded per window.
  --windows  optional subset of the 8 D1 windows (default all 8); BASE0 may only run on the canary (never a J window
             or blank).
  outputs    /work/d3/infer/<ARM>/<window>/<window>.tif (+ _reverse.tif, + .npy decodes); record
             /work/d3/work/infer_<ARM>.json; official logs /work/d3/logs/infer_<ARM>_<window>.log; ledger rows (the
             inference and the decode) in /work/d3/work/ledger.tsv (host, cpu, command, start, end, exit, output
             sha256; the run_arms.sh format).
Unchanged: the official command `vesuvius.ink_detection.inference.infer <D1 render.zarr> <ckpt> <OUT.tif> --direction
both --batch-size 4 --num-workers 1 --no-compile` (no --tta-mirror; CPU) on the D1 renders (/work/d1/work/prep.json
render_zarr); OUT.tif = forward order, OUT_reverse.tif = reverse order; the LZW TIFFs decoded to <tif>.npy by
tools/c3/tif2npy.py (METRIC-HASH-6, sha256 asserted; /opt/hv-ink python, which has imagecodecs); the source layer
indices of each order recorded from the official log; resumable per (arm, window): a window whose record has
returncode 0 is skipped (and a changed checkpoint sha256 stops the run).
Usage: /opt/hv-ink/bin/python d3_infer.py --arm ARM --threads N [--windows W ...]
"""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/work/d1/scripts')
import d1_common as K
import os, re, json, time, argparse, socket, subprocess, hashlib

PY = '/opt/hv-ink/bin/python'
TIF2NPY = '/home/user/dominion/tools/c3/tif2npy.py'
TIF2NPY_SHA = '998f1b98314b6b7d52ebbca229d48bfcd5a501ee3f2f96478586e901fef5c5e4'
D1_INFER = '/work/d1/scripts/d1_infer.py'
D1_INFER_SHA = 'b2289eae4880ee2bccc3825e9870a3f327697ef47f8dde2e5c470b8d3e65648e'
D3 = '/work/d3'
D3WK = f'{D3}/work'
D3INF = f'{D3}/infer'
D3LOGS = f'{D3}/logs'
LEDGER = f'{D3WK}/ledger.tsv'
ARMS = ('CTRL', 'FA', 'NULLA', 'REVA', 'BASE0')
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
SERVES = ('RULES.md DECL-D3D4, DECL-D3-A1 item 5, DECL-D3-A3 items 1-2: D3 arm maps (official C2-NT-style inference, '
          'both orders, on the D1 renders of J1-J5, the 2 w053 blanks and the canary)')


def cpu_model():
    for ln in open('/proc/cpuinfo'):
        if ln.startswith('model name'):
            return ln.split(':', 1)[1].strip()
    return 'cpu'


def ledger(command, start, end, rc, out_sha, threads):
    row = [socket.gethostname(), f'cpus={threads}/{os.cpu_count()} {cpu_model()}',
           command.replace('\t', ' ').replace('\n', ' '), start, end, str(rc), out_sha]
    with open(LEDGER, 'a', encoding='utf-8') as f:
        f.write('\t'.join(row) + '\n')


def jwrite(path, obj):
    assert path.startswith(D3WK + '/'), path
    d = {'provenance': PROV}
    d.update(obj)
    t = json.dumps(d, indent=1, default=K.jdefault) + '\n'
    assert t.isascii()
    with open(path + '.tmp', 'w', encoding='ascii') as fh:
        fh.write(t)
    os.replace(path + '.tmp', path)
    return hashlib.sha256(t.encode('ascii')).hexdigest()


def main(arm, wids, threads):
    assert K.sha256(D1_INFER) == D1_INFER_SHA
    assert K.sha256(TIF2NPY) == TIF2NPY_SHA
    ck = f'{D3}/runs/{arm}/model_final.pth'
    assert os.path.isfile(ck), ck
    ck_sha = K.sha256(ck)
    summ = f'{D3}/runs/{arm}/summary.json'
    summ_sha = None
    if os.path.exists(summ):
        summ_sha = json.load(open(summ))['model_final']['sha256']
        assert summ_sha == ck_sha, ('model_final differs from its summary.json record', ck_sha, summ_sha)
    elif arm != 'BASE0':
        raise SystemExit(f'arm {arm} has no summary.json (not complete)')
    prep = json.load(open(f'{K.WK}/prep.json'))
    os.makedirs(D3WK, exist_ok=True); os.makedirs(D3LOGS, exist_ok=True)
    path = f'{D3WK}/infer_{arm}.json'
    res = json.load(open(path)) if os.path.exists(path) else dict(generated_utc=K.utc(), serves=SERVES, arm=arm,
                                                                  stage='D3 arm inference (C2-NT-style)',
                                                                  viewing='no image was opened; numbers only', windows={})
    if res.get('checkpoint') and res['checkpoint']['sha256'] != ck_sha:
        raise SystemExit(f"checkpoint of {arm} changed since earlier windows ({res['checkpoint']['sha256']} -> {ck_sha})")
    me = os.path.abspath(__file__)
    res.update(script=dict(path=me, sha256=K.sha256(me)), copy_of=dict(path=D1_INFER, sha256=D1_INFER_SHA),
               checkpoint=dict(path=ck, sha256=ck_sha, summary_model_final_sha256=summ_sha),
               tif2npy=dict(path=TIF2NPY, sha256=TIF2NPY_SHA))
    t = str(int(threads))
    env = dict(os.environ, OMP_NUM_THREADS=t, MKL_NUM_THREADS=t, OPENBLAS_NUM_THREADS=t, NUMEXPR_NUM_THREADS=t,
               PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    envp = f'OMP_NUM_THREADS={t} MKL_NUM_THREADS={t} OPENBLAS_NUM_THREADS={t} NUMEXPR_NUM_THREADS={t} '
    for wid in wids:
        if res['windows'].get(wid, {}).get('returncode') == 0:
            K.log(arm, wid, 'already inferred'); continue
        p = prep['windows'][wid]
        od = f'{D3INF}/{arm}/{wid}'
        os.makedirs(od, exist_ok=True)
        fwd, rev = f'{od}/{wid}.tif', f'{od}/{wid}_reverse.tif'
        for f in (fwd, rev, fwd + '.npy', rev + '.npy'):
            if os.path.exists(f):
                os.remove(f)
        cmd = [PY, '-m', 'vesuvius.ink_detection.inference.infer', p['render_zarr'], ck, fwd, '--direction', 'both',
               '--batch-size', '4', '--num-workers', '1', '--no-compile']
        logp = f'{D3LOGS}/infer_{arm}_{wid}.log'
        start = K.utc(); t0 = time.time()
        with open(logp, 'w') as lf:
            pr = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=od)
        secs = time.time() - t0; end = K.utc()
        ok = pr.returncode == 0 and os.path.exists(fwd) and os.path.exists(rev)
        sha = K.tree_sha256(od) if ok else 'missing'
        ledger(envp + ' '.join(cmd), start, end, pr.returncode, sha, t)
        txt = open(logp, errors='replace').read()
        layers = re.findall(r'Selected source layer indices=(\[[^\]]*\])', txt)
        tta = re.findall(r'tta_mirror=(\w+)', txt)
        ent = dict(command=' '.join(cmd), threads=int(t), checkpoint_sha256=ck_sha, start_utc=start, end_utc=end,
                   seconds=round(secs, 1), returncode=pr.returncode,
                   output_dir_tree_sha256=sha, log=logp, layer_indices_forward=json.loads(layers[0]) if len(layers) > 0 else None,
                   layer_indices_reverse=json.loads(layers[1]) if len(layers) > 1 else None, log_tta_mirror=tta,
                   outputs={})
        if ok:
            dcmd = [PY, TIF2NPY, fwd, rev]
            ds = K.utc()
            d = subprocess.run(dcmd, capture_output=True, text=True, env=env)
            de = K.utc()
            ledger(envp + ' '.join(dcmd), ds, de, d.returncode, K.tree_sha256(od) if d.returncode == 0 else 'missing', t)
            ent['tif2npy_stdout'] = d.stdout.strip()
            assert d.returncode == 0, d.stderr
            for f in (fwd, rev, fwd + '.npy', rev + '.npy'):
                ent['outputs'][os.path.basename(f)] = dict(path=f, bytes=os.path.getsize(f), sha256=K.sha256(f))
        res['windows'][wid] = ent
        jwrite(path, res)
        K.log(arm, wid, 'rc', pr.returncode, 'sec %.1f' % secs, 'threads', t, 'fwd layers', ent['layer_indices_forward'], 'tta', tta)
        if not ok:
            raise SystemExit(f'inference failed for {arm} {wid}')
    res['generated_utc'] = K.utc()
    jwrite(path, res)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', required=True, choices=ARMS)
    ap.add_argument('--threads', type=int, required=True, choices=(1, 2, 3))
    ap.add_argument('--windows', nargs='+', choices=K.WIDS)
    a = ap.parse_args()
    ws = list(a.windows) if a.windows else list(K.WIDS)
    if a.arm == 'BASE0':
        assert ws == [K.CANARY[0]], 'BASE0 (E1 pre-check) runs on the canary only'
    main(a.arm, ws, a.threads)
