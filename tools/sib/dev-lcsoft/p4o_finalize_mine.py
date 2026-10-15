#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Write manifest.json for a dev-lcsoft P4-O material by calling the pinned ckpt-screen-b builder's finalize()
UNCHANGED (tools/sib/dev-lcsoft/p4o_tiles.py = ckpt-screen-b ca732ae byte for byte). The only adaptation is
where it reads ckpt-screen-b SPECS.json: that file is taken from git (ref below) into a scratch copy, because this
session writes only under its own directories. Afterwards the manifest records the dev-lcsoft copy paths and the
upstream pin. Usage: finalize_mine.py ITERATION OUT_DIR"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4o_tiles as P  # noqa: E402
SPECS_REF = 'ca732ae:logs/sib/ckpt-screen-b/SPECS.json'
REAL = P.REPO
it, out = int(sys.argv[1]), sys.argv[2]
tmp = tempfile.mkdtemp()
os.makedirs(f'{tmp}/logs/sib/ckpt-screen-b')
open(f'{tmp}/logs/sib/ckpt-screen-b/SPECS.json', 'wb').write(subprocess.check_output(['git', '-C', REAL, 'show', SPECS_REF]))
P.git_json = lambda ref: json.loads(subprocess.check_output(['git', '-C', REAL, 'show', ref]))
P.REPO = tmp
P.finalize(it, out)
p = os.path.join(out, 'manifest.json')
m = json.load(open(p))
m['inference'].update(wrapper='tools/sib/dev-lcsoft/infer_1667.py', builder='tools/sib/dev-lcsoft/p4o/p4o_tiles.py',
                      upstream='claude/gifted-bell-gavnl5-sib-ckpt-screen-b ca732ae tools/sib/ckpt-screen-b/ (byte-identical)',
                      specs_ref=SPECS_REF)
m['builder_session'] = 'dev-lcsoft (DECL-P4-14-A1 item 1)'
m['harness'] = 'p4-tiles-a (DECL-P4-14-A1 item 2)'
json.dump(m, open(p, 'w'), indent=1)
print(p, m['n_tiles'])
