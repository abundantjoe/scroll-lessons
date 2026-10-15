#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-O driver for ckpt-screen-c (RULES.md DECL-P4-14, -A2): PHerc.1667-iteration-4 on the strip-a tiles, through
ckpt-screen-b's builder tools/sib/ckpt-screen-b/p4o_tiles.py and infer_1667.py UNCHANGED (imported from a read-only
worktree of that branch, sha256 pinned below), so that the family's materials share one method: level-0 2.4 um slices
23..84, forward order for iterations 1-5, clip(0,200)/255, card tiling (256 / 128), 128 px halo, raw u8 display at
1068 px, 0 outside mesh-valid, 15-minute resumable checkpoints.
The only additions:
  --precision bf16  wraps the model call in torch.autocast('cpu', bfloat16) and returns float32 logits (DECL-P4-14-A2
                    item 2: allowed only after the r0 c5 equivalence check passes; the check is recorded in STATUS.md);
  a precision tag per tile (tiles/<png>.json gains "precision"), and a finalize step that relabels the manifest for
  this builder (material, builder hashes, per-tile precision). No tile is opened or viewed; numbers and hashes only.
Usage: p4o_run.py --tiles "r,c;..." --out DIR [--precision fp32|bf16] [--threads 4] | --finalize --out DIR
       env P4O_WORK (checkpoints; one per precision), CKC_BWT (worktree of ckpt-screen-b, default /work/ckc_bwt)
"""
import hashlib
import json
import os
import sys

BWT = os.environ.get('CKC_BWT', '/work/ckc_bwt')
BDIR = os.path.join(BWT, 'tools/sib/ckpt-screen-b')
PIN = {'p4o_tiles.py': 'a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371',
       'infer_1667.py': '29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12'}
IT = 4
ARMED = [False]


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def main():
    args = sys.argv[1:]
    prec = 'fp32'
    if '--precision' in args:
        i = args.index('--precision')
        prec = args[i + 1]
        del args[i:i + 2]
    assert prec in ('fp32', 'bf16'), prec
    for n, want in PIN.items():
        got = sha256(os.path.join(BDIR, n))
        assert got == want, f'{n}: {got} != pinned {want}'
    sys.path.insert(0, BDIR)
    sys.path.insert(0, os.path.join(BWT, 'src'))
    import p4o_tiles as P
    out = args[args.index('--out') + 1]
    if '--finalize' in args:
        return finalize(P, out)
    if prec == 'bf16':
        import torch
        orig = P.FastModel.__call__

        class _Out:
            def __init__(self, logits):
                self.logits = logits

        def call_bf16(self, t):
            if not ARMED[0]:  # b's startup layout self-test (fp32 vs fp32) runs before any tile, unpatched
                return orig(self, t)
            with torch.autocast('cpu', dtype=torch.bfloat16):
                o = orig(self, t)
            return _Out(o.logits.float())
        P.FastModel.__call__ = call_bf16
    orig_run = P.run_tile

    def run_tile(model, it, r, c, o, valid, log):
        ARMED[0] = prec == 'bf16'
        rec = orig_run(model, it, r, c, o, valid, log)
        jp = f'{o}/tiles/{P.SEG}_r{r}_c{c}.png.json'
        if 'precision' not in rec:
            rec['precision'] = prec
            rec['driver_sha256'] = sha256(os.path.abspath(__file__))
            with open(jp, 'w') as f:
                json.dump(rec, f, indent=1)
        return rec
    P.run_tile = run_tile
    sys.argv = [P.__file__, '--iteration', str(IT)] + args
    P.main()


def finalize(P, out):
    P.finalize(IT, out)
    p = os.path.join(out, 'manifest.json')
    man = json.load(open(p))
    precs = sorted({t.get('precision', 'fp32') for t in man['tiles']})
    man['material'] = f'M-P4O-PHerc.1667-iteration-{IT}'
    man['builder_session'] = 'ckpt-screen-c (driver tools/sib/ckpt-screen-c/p4o_run.py)'
    man['inference'].update(
        builder='ckpt-screen-b tools/sib/ckpt-screen-b/p4o_tiles.py (unchanged, via tools/sib/ckpt-screen-c/p4o_run.py)',
        driver='tools/sib/ckpt-screen-c/p4o_run.py', driver_sha256=sha256(os.path.abspath(__file__)),
        b_files_sha256=PIN, dtype='per tile: ' + ', '.join(precs),
        bf16_rule='DECL-P4-14-A2 item 2; equivalence check on r0 c5 recorded in logs/sib/ckpt-screen-c/STATUS.md')
    man['checkpoint']['eligibility'] = 'RULES.md P4-O-PROVENANCE (ckpt-screen-b provenance.json); iteration ruled in DECL-P4-14-A2 item 3'
    t = json.dumps(man, indent=1) + '\n'
    open(p, 'w').write(t)
    print(p, hashlib.sha256(t.encode()).hexdigest(), man['n_tiles'], precs)


if __name__ == '__main__':
    main()
