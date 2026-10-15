# Provenance: Project HERCULES | [id removed]
"""DECL-P4-26-A2: P4-OWN inference in VERSO mode (the facing-surface offset channel P4-OFF, fallback (4) on the
official canvas). Numbers only: maps are written and hashed, never opened.

It runs own-lead's tools/sib/own-lead/infer.py UNCHANGED, with exactly three substitutions:
  1. own_common.read_region reads the same 62 slices (23..84) with p4o_tiles.read_stack(..., 'reverse')
     (the organizers' reverse_layers convention, already implemented in the reader), so the sheet is seen from its
     other face;
  2. band checkpoints go to <WORK>/infer_verso/... instead of <WORK>/infer/... (no forward checkpoint is ever reused);
  3. after the run, every tile record in <out>/tiles/ gets order='reverse' and this wrapper's sha256.
Arguments are infer.py's own (--model --summary --tiles --out [--threads] ...). --out must not be a forward dir.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.join(HERE, '..', 'sib', 'own-lead')
sys.path.insert(0, OWN)
import own_common as C  # noqa: E402
import infer  # noqa: E402

SELF_SHA = hashlib.sha256(open(os.path.abspath(__file__), 'rb').read()).hexdigest()


def _read_region_reverse(seg, y0, y1, x0, x1):
    P = C.p4o(seg)
    return P.read_stack(y0, y1, x0, x1, y1 - y0, x1 - x0, 'reverse')


_predict = infer.predict_tile


def _predict_verso(model, torch, seg, r, c, valid, ckd, log):
    assert '/infer/' in ckd, ckd
    return _predict(model, torch, seg, r, c, valid, ckd.replace('/infer/', '/infer_verso/'), log)


def main():
    out = sys.argv[sys.argv.index('--out') + 1]
    assert 'verso' in out, 'verso maps must go to a dir whose path contains "verso"'
    C.read_region = _read_region_reverse
    infer.predict_tile = _predict_verso
    infer.main()
    td = os.path.join(out, 'tiles')
    for f in sorted(os.listdir(td)):
        if f.endswith('.png.json'):
            p = os.path.join(td, f)
            rec = json.load(open(p))
            if rec.get('order') != 'reverse':
                rec.update(order='reverse', verso_wrapper='tools/p4/infer_verso.py', verso_wrapper_sha256=SELF_SHA,
                           declaration='RULES.md DECL-P4-26-A2')
                json.dump(rec, open(p, 'w'), indent=1)


if __name__ == '__main__':
    main()
