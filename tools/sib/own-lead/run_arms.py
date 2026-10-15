# Provenance: Project HERCULES | owner the owner | [id removed]
"""own-lead fallback driver (orchestrator 15:02Z): run the remaining P4-OWN arms on this container with the verified
data (/work/own/data) and the RECIPE code (6b5bdc5 + RECIPE-A1 train.py). Resumable: every step skips finished work.
Two loops run concurrently:
  trainer:   arms in TRAIN_ORDER, one at a time (--train-threads), after waiting for S1 to finish;
  predictor: arms in PRED_ORDER, each once its model_final.pth exists (--pred-threads); per tile one commit + push
             of logs/sib/own-<arm>/maps/tiles/<tile>.png(.json) + maps/manifest.json (+ arrays/<tile>.npz for col. -1);
             F arms then auc.py; NULL additionally predicts all 72 F held-out tiles (heldout_maps, npz local) + 3 AUCs.
Before training an arm, its worker branch is checked; if that worker shows training started, the arm is skipped.
Git operations are serialised with a file lock. Numbers only: no map is ever opened."""
import argparse
import fcntl
import json
import os
import subprocess
import sys
import threading
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
WORK = '/work/own'
PY = '/opt/ckb/bin/python'
TOOLS = os.path.join(REPO, 'tools', 'sib', 'own-lead')
RECIPE = os.path.join(REPO, 'logs', 'sib', 'own-lead', 'p4own', 'recipe.json')
TRAIN_ORDER = ['F2', 'F3', 'NULL', 'S2', 'S3']        # orchestrator 20:39Z (G1 critical path); S1, F1 already trained
PRED_ORDER = ['S1', 'F1', 'NULL', 'S2', 'F2', 'F3', 'S3']   # sequential mode only
# predictor priority, re-evaluated after every tile (orchestrator 20:39Z): F held-out first (each once its model
# exists), then the rest of S1 X, then NULL (X + 72 held-out + AUCs), then S2, S3
PRIORITY = ['F1', 'F2', 'F3', 'S1', 'NULL', 'S2', 'S3']
FOOT = ('\n\nProvenance: Project HERCULES | owner the owner | [id removed]\n\n'
        'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
        'Claude-Session: https://claude.ai/code/session_013RMBx9vJymzu55FFHNHGfd')
X1 = [(0, 11), (0, 12), (0, 13), (1, 11), (1, 12), (1, 13)]
X2 = [(r, c) for r in range(6) for c in range(14, 18)]
X3 = [(r, c) for r in range(8) for c in range(9, 20) if (r, c) not in X1 + X2]


def log(msg):
    line = json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **msg))
    print(line, flush=True)


def git_commit(paths, msg):
    with open(f'{WORK}/git.lock', 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        subprocess.run(['git', '-C', REPO, 'add', '--'] + paths, check=True)
        if subprocess.run(['git', '-C', REPO, 'diff', '--cached', '--quiet']).returncode == 0:
            return
        subprocess.run(['git', '-C', REPO, 'commit', '-qm', msg + FOOT], check=True)
        for i in range(5):
            if subprocess.run(['git', '-C', REPO, 'push', '-q', 'origin', 'HEAD']).returncode == 0:
                return
            time.sleep(2 ** (i + 1))
        log(dict(push_failed=msg))


def worker_training(arm):
    b = f'claude/gifted-bell-gavnl5-sib-own-{arm.lower()}'
    if subprocess.run(['git', '-C', REPO, 'fetch', '-q', 'origin', b]).returncode:
        return False
    for f in (f'logs/sib/own-{arm.lower()}/train/train_log.jsonl', f'logs/sib/own-{arm.lower()}/train_log.jsonl'):
        if subprocess.run(['git', '-C', REPO, 'cat-file', '-e', f'origin/{b}:{f}'],
                          stderr=subprocess.DEVNULL).returncode == 0:
            return True
    st = subprocess.run(['git', '-C', REPO, 'show', f'origin/{b}:logs/sib/own-{arm.lower()}/STATUS.md'],
                        capture_output=True, text=True).stdout.lower()
    return ('training' in st and ('step' in st and '/2500' in st)) and 'blocked' not in st


def done(arm):
    return os.path.exists(f'{WORK}/arm_{arm}/summary.json') and os.path.exists(f'{WORK}/arm_{arm}/model_final.pth')


def train(arm, threads):
    if done(arm):
        return True
    if worker_training(arm):
        log(dict(skip_train=arm, reason='worker branch shows this arm training'))
        return False
    for attempt in range(3):       # resumes from resume_latest.pth after a crash
        log(dict(train_start=arm, attempt=attempt, threads=threads))
        with open(f'{WORK}/train_{arm}.log', 'a') as f:
            subprocess.run([PY, f'{TOOLS}/train.py', '--arm', arm, '--data', f'{WORK}/data', '--recipe', RECIPE,
                            '--out', f'{WORK}/arm_{arm}', '--threads', str(threads)], stdout=f, stderr=f,
                           env=dict(os.environ, OWN_WORK=WORK))
        if done(arm):
            break
    if not done(arm):
        log(dict(train_failed=arm))
        return False
    d = f'{REPO}/logs/sib/own-{arm.lower()}/train'
    os.makedirs(d, exist_ok=True)
    for n in ('summary.json', 'train_manifest.json', 'train_log.jsonl'):
        subprocess.run(['cp', f'{WORK}/arm_{arm}/{n}', d], check=True)
    git_commit([d], f'own-lead: arm {arm} trained (summary, train manifest, log)')
    log(dict(train_done=arm))
    return True


def tiles_for(arm):
    fin = json.load(open(os.path.join(REPO, 'logs/sib/own-lead/p4own/recipe_final.json')))
    if arm.startswith('F'):
        return [('F', f"{t['seg'].split('-', 1)[1]}:{t['r']},{t['c']}") for t in fin['heldout_tiles'][arm]]
    out = [('X1', f'w010-027:{r},{c}') for r, c in X1] + [('X', f'w010-027:{r},{c}') for r, c in X2 + X3]
    if arm == 'NULL':
        out += [('H', f"{t['seg'].split('-', 1)[1]}:{t['r']},{t['c']}")
                for k in ('F1', 'F2', 'F3') for t in fin['heldout_tiles'][k]]
    return out


[line withheld: prize-candidate detail under review]


def region_o(fname, sha):
[line withheld: prize-candidate detail under review]
    ref = f'origin/claude/gifted-bell-gavnl5:logs/p4/{fname}'
    b = subprocess.run(['git', '-C', REPO, 'show', ref], capture_output=True).stdout
    import hashlib
    if hashlib.sha256(b).hexdigest() != sha:
        log(dict(region_o_sha_mismatch=fname))
        return []
    d = json.loads(b)
    return [f"{o['seg'].split('-', 1)[1]}:{o['r']},{o['c']}" for o in (d.get('order') or d['tiles'])]


[line withheld: prize-candidate detail under review]
def x_rest(sha):
    """S1 rest-of-X order (orchestrator logs/p4/X_rest_S1.json, DECL-P4-23-A4), sha256-checked."""
    b = subprocess.run(['git', '-C', REPO, 'show', 'origin/claude/gifted-bell-gavnl5:logs/p4/X_rest_S1.json'],
                       capture_output=True).stdout
    import hashlib
    if hashlib.sha256(b).hexdigest() != sha:
        log(dict(x_rest_sha_mismatch=True))
        return []
    return [f"w010-027:{o['r']},{o['c']}" for o in json.loads(b)['map_order']]


XREST = x_rest('ba6299695e62057c8c62981a8b6a796caa02d9251c5fe9c8f15843709c2e1f74')
[line withheld: prize-candidate detail under review]


def tile_paths(arm, kind, tok):
    a = arm.lower()
    out = f'{REPO}/logs/sib/own-{a}/' + {'H': 'heldout_maps', 'O': 'maps_O'}.get(kind, 'maps')
    seg, rc = tok.split(':')
    r, c = rc.split(',')
    full = [s for s in SEGS_ALL if s.endswith(seg)][0]
    return out, f'{full}_r{r}_c{c}'


def committed(path):
    return subprocess.run(['git', '-C', REPO, 'ls-files', '--error-unmatch', path], capture_output=True).returncode == 0


def do_tile(arm, kind, tok, threads):
    """Predict (unless already predicted) and commit one tile. Returns True on success."""
    out, name = tile_paths(arm, kind, tok)
    if not os.path.exists(f'{out}/tiles/{name}.png.json'):
        cmd = [PY, f'{TOOLS}/infer.py', '--model', f'{WORK}/arm_{arm}/model_final.pth', '--summary',
               f'{WORK}/arm_{arm}/summary.json', '--tiles', tok, '--out', out, '--threads', str(threads)]
        if kind in ('X1', 'F', 'H'):
            cmd.append('--save-npz')
        with open(f'{WORK}/infer_{arm}.log', 'a') as f:
            rcode = subprocess.run(cmd, stdout=f, stderr=f, env=dict(os.environ, OWN_WORK=WORK)).returncode
        if rcode or not os.path.exists(f'{out}/tiles/{name}.png.json'):
            log(dict(infer_failed=arm, tile=tok, rc=rcode))
            return False
    paths = [f'{out}/tiles/{name}.png', f'{out}/tiles/{name}.png.json', f'{out}/manifest.json']
    if kind == 'X1':
        paths.append(f'{out}/arrays/{name}.npz')
    if not committed(f'{out}/tiles/{name}.png.json'):
        git_commit(paths, f'own-lead: {arm} map {name}')
        log(dict(tile_done=arm, tile=name))
    if committed(f'{out}/tiles/{name}.png.json'):   # disk: drop infer.py's band checkpoint of a finished tile
        subprocess.run(['rm', '-rf', f'{WORK}/infer/{arm}/{name}'])
    return True


def auc_sets(arm):
    a = arm.lower()
    fin = json.load(open(os.path.join(REPO, 'logs/sib/own-lead/p4own/recipe_final.json')))
    ht = {k: [f"{t['seg'].split('-', 1)[1]}:{t['r']},{t['c']}" for t in fin['heldout_tiles'][k]] for k in ('F1', 'F2', 'F3')}
    if arm.startswith('F'):
        return [(arm, ht[arm], f'{REPO}/logs/sib/own-{a}/maps', f'{REPO}/logs/sib/own-{a}/heldout_auc.json')]
    if arm == 'NULL':
        return [(k, ht[k], f'{REPO}/logs/sib/own-{a}/heldout_maps', f'{REPO}/logs/sib/own-{a}/heldout_auc_{k}.json')
                for k in ('F1', 'F2', 'F3')]
    return []


def do_auc(arm, k, tl, mdir, outj):
    subprocess.run([PY, f'{TOOLS}/auc.py', '--arrays', f'{mdir}/arrays', '--tiles', ';'.join(tl), '--excl',
                    f'{WORK}/excl', '--out', outj], check=True, env=dict(os.environ, OWN_WORK=WORK),
                   stdout=subprocess.DEVNULL)
    git_commit([outj], f'own-lead: {arm} held-out AUC {k}')
    log(dict(auc=arm, fold=k, pixel_auc=json.load(open(outj))['pixel_auc']))


FAILED = set()
RUNNING = set()
LOCK = threading.Lock()
# X tile groups (orchestrator 21:11Z): title slot = col. -1 + c14-c17 r0-r5 (30); then c11-c13 r2-r5; then c18-c19; rest
XB = [(r, c) for r in range(2, 6) for c in range(11, 14)]
XC = [(r, c) for r in range(8) for c in (18, 19)]
XR = [(r, c) for r in range(8) for c in range(9, 20) if (r, c) not in X1 + X2 + XB + XC]


def xjobs(arm, groups):
    return [(arm, 'X1' if (r, c) in X1 else 'X', f'w010-027:{r},{c}') for g in groups for (r, c) in g]


def hjobs():
    fin = json.load(open(os.path.join(REPO, 'logs/sib/own-lead/p4own/recipe_final.json')))
    return [('NULL', 'H', f"{t['seg'].split('-', 1)[1]}:{t['r']},{t['c']}")
            for k in ('F1', 'F2', 'F3') for t in fin['heldout_tiles'][k]]


def fjobs(arm):
    return [(arm, 'F', tok) for _, tok in tiles_for(arm)]


def tile_done(arm, kind, tok):
    out, name = tile_paths(arm, kind, tok)
    return os.path.exists(f'{out}/tiles/{name}.png.json') and committed(f'{out}/tiles/{name}.png.json')


def all_tiles_done(jobs):
    return all(tile_done(*j) for j in jobs)


def auc_done(arm):
    return all(os.path.exists(o) for _, _, _, o in auc_sets(arm))


def train_running(arm):
    return subprocess.run(['pgrep', '-f', f'^{PY} .*train.py --arm {arm} '], capture_output=True).returncode == 0


def ram_ok():
    """Second concurrent training only if MemAvailable >= peak training RSS (VmHWM of running trainings, else 7.5 GB)
    + 2 GB."""
    avail = int([l for l in open('/proc/meminfo') if l.startswith('MemAvailable')][0].split()[1]) / 1e6
    peaks = []
    for pid in subprocess.run(['pgrep', '-f', f'^{PY} .*train.py --arm'], capture_output=True, text=True).stdout.split():
        try:
            peaks += [int(l.split()[1]) / 1e6 for l in open(f'/proc/{pid}/status') if l.startswith('VmHWM')]
        except OSError:
            pass
    need = (max(peaks) if peaks else 7.5) + 2.0
    ok = avail >= need
    log(dict(ram_check=ok, avail_gb=round(avail, 2), need_gb=round(need, 2)))
    return ok


def candidates():
[line withheld: prize-candidate detail under review]
    (a) S3 title slot + col. -1 (c11-c17 r0-r5, 42 tiles, same set as S2/NULL); (b) S2, S3, NULL maps of the other 24
[line withheld: prize-candidate detail under review]
    for tok in SEED:
        for arm in ('S2', 'S3', 'NULL'):
            yield ('tile', arm, 'O', tok)
    for tok in XREST:                                   # orchestrator 03:34Z (DECL-P4-23-A4)
        yield ('tile', 'S1', 'X', tok)
    yield from (('tile',) + j for j in xjobs('S3', [X1, X2, XB]))
    for tok in TARGET2:
        if tok in SEED:
            continue
        for arm in ('S2', 'S3', 'NULL'):
            yield ('tile', arm, 'O', tok)
    yield from old_candidates()


def old_candidates():
    """Jobs in priority order (orchestrator 21:11Z)."""
    f1 = fjobs('F1')
    yield from (('tile',) + j for j in f1)
    f1_ok = all_tiles_done(f1) and auc_done('F1')
    if not f1_ok:
        yield ('auc', 'F1')
    yield ('train', 'F2')
    if f1_ok:
        yield ('train', 'F3')
    for arm in ('F2', 'F3'):
        if done(arm):
            yield from (('tile',) + j for j in fjobs(arm))
            yield ('auc', arm)
    f3_tiles = done('F3') and all_tiles_done(fjobs('F3'))
    if f3_tiles:
        yield ('train', 'S2')
        yield ('train', 'NULL')
    if done('S2') and done('NULL'):
        yield ('train', 'S3')
    title = [X1, X2]
    for arm in ('S2', 'NULL'):
        if done(arm):
            yield from (('tile',) + j for j in xjobs(arm, title))
    if done('NULL'):
        yield from (('tile',) + j for j in hjobs())
        yield ('auc', 'NULL')
    for g in (XB, XC, XR):
        for arm in ('S2', 'NULL'):
            if done(arm):
                yield from (('tile',) + j for j in xjobs(arm, [g]))
    if done('S3'):
        yield from (('tile',) + j for j in xjobs('S3', [X1, X2, XB, XC, XR]))
    yield from (('tile',) + j for j in xjobs('S1', [X1, X2, X3]))


def pick():
    with LOCK:
        for arm in TRAIN_ORDER:        # a training already running (previous driver) is adopted first
            if ('train', arm) not in RUNNING and train_running(arm):
                RUNNING.add(('train', arm))
                return ('train', arm), ('train', arm)
        for job in candidates():
            key = job[:2] if job[0] != 'tile' else job
            if key in RUNNING or key in FAILED:
                continue
            if job[0] == 'tile':
                arm, kind, tok = job[1:]
                if not done(arm) or tile_done(arm, kind, tok):
                    continue
            elif job[0] == 'train':
                if done(job[1]):
                    continue
                if not train_running(job[1]) and any(k[0] == 'train' for k in RUNNING) and not ram_ok():
                    continue
            elif job[0] == 'auc':
                arm = job[1]
                if auc_done(arm) or not all_tiles_done(fjobs(arm) if arm != 'NULL' else hjobs()):
                    continue
            RUNNING.add(key)
            return job, key
    return None, None


def run_job(job, threads):
    if job[0] == 'tile':
        return do_tile(job[1], job[2], job[3], threads)
    if job[0] == 'auc':
        for k, tl, mdir, outj in auc_sets(job[1]):
            if not os.path.exists(outj):
                do_auc(job[1], k, tl, mdir, outj)
        return True
    arm = job[1]
    while train_running(arm):          # adopt a training already running (e.g. from the previous driver)
        time.sleep(60)
    return train(arm, threads)


def slot(i, threads, wait_pid):
    while wait_pid and os.path.exists(f'/proc/{wait_pid}'):
        time.sleep(20)
    idle = 0
    while True:
        job, key = pick()
        if job is None:
            with LOCK:
                busy = bool(RUNNING)
            if not busy and idle > 3:
                break
            idle += 1
            time.sleep(60)
            continue
        idle = 0
        log(dict(slot=i, start=list(job[:4])))
        try:
            ok = run_job(job, threads)
        except Exception as e:  # noqa: BLE001
            log(dict(slot=i, error=repr(e)[:300], job=list(job[:4])))
            ok = False
        with LOCK:
            RUNNING.discard(key)
            if not ok:
                FAILED.add(key)


def predict(arm, threads):          # sequential mode
    for kind, tok in tiles_for(arm):
        if not do_tile(arm, kind, tok, threads):
            return False
    for k, tl, mdir, outj in auc_sets(arm):
        if not os.path.exists(outj):
            do_auc(arm, k, tl, mdir, outj)
    log(dict(pred_done=arm))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train-threads', type=int, default=2)
    ap.add_argument('--pred-threads', type=int, default=2)
    ap.add_argument('--sequential', action='store_true', help='train then predict each arm, 4 threads, no overlap')
    ap.add_argument('--wait-pid', type=int, default=0, help='predictor starts after this pid exits (orphan infer)')
    a = ap.parse_args()
    if a.sequential:
        while not done('S1'):
            time.sleep(60)
        for arm in PRED_ORDER:
            if arm == 'S1' or train(arm, 4):
                predict(arm, 4)
        log(dict(all_done=True))
        return

    # two slots of --pred-threads each (orchestrator 21:11Z); slot 0 first adopts a running training, if any
    th = [threading.Thread(target=slot, args=(0, a.pred_threads, 0)),
          threading.Thread(target=slot, args=(1, a.pred_threads, a.wait_pid))]
    for t in th:
        t.start()
    for t in th:
        t.join()
    if pick()[0] is None and not FAILED:
        open(f'{WORK}/ALL_DONE', 'w').write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    log(dict(all_done=True))


if __name__ == '__main__':
    sys.exit(main())
