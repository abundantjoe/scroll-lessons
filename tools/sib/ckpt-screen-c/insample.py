# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-DEVLOOP-SCREEN item 3 guard per checkpoint x DEV window (and blank), from SPECS.json training data and the
devloop registry (read from a git ref; re-run once the registry is frozen and hashed). Rule as written:
IN-SAMPLE if the documented training data includes the window's segment or a same-papyrus segment; UNKNOWN if the
training data is undocumented, unless the window's scroll is absent from every training list the card or code names;
otherwise OUT-OF-SAMPLE. Usage: python insample.py GIT_REF"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
REF = sys.argv[1]
reg_txt = subprocess.run(['git', '-C', ROOT, 'show', f'{REF}:logs/sib/devloop/dev_registry.json'],
                         capture_output=True, text=True, check=True).stdout
commit = subprocess.run(['git', '-C', ROOT, 'rev-parse', REF], capture_output=True, text=True).stdout.strip()
reg = json.loads(reg_txt)
specs = json.load(open(os.path.join(ROOT, 'logs/sib/ckpt-screen-c/SPECS.json')))
# Scrolls each checkpoint's card/code names as training data, and whether every named item resolves to a scroll.
NAMED = {
    'timesformer_scroll5_july_retreat': (['PHerc0172'], True, 'card names PHerc0172 only; segments and any '
                                         'pretraining undocumented'),
    'timesformer_GP_scroll1': (['PHercParis4'], True, 'registry/card: Scroll 1 (PHerc Paris 4) only'),
    'timesformer_large_scroll1_01122024': (['PHercParis4'], True, 'card finetune list is Scroll 1 segments; '
                                           'pretraining undocumented'),
    'resnet50_7.9um_scroll1_frags': (['PHercParis4'], False, '23 of 24 card ids unresolved to any scroll'),
    'fiber_ink_4class_selfdistill': (['PHercParis4'], True, 'card: PHerc Paris 4 2.4 um volume (not screened: '
                                     'input spec mismatch)'),
}
out = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]',
           registry=dict(ref=REF, commit=commit, sha256=hashlib.sha256(reg_txt.encode()).hexdigest(),
                         generated_utc=reg.get('generated_utc'),
                         frozen=False, note='re-run against the METRIC-HASH registry before any screen map'),
           rule='DECL-DEVLOOP-SCREEN item 3', rows=[])
for scroll, s in reg['scrolls'].items():
    for kind in ('windows', 'blanks'):
        for w in s[kind]:
            for ck, (scrolls, resolved, why) in NAMED.items():
                if not resolved:
                    status = 'UNKNOWN'
                elif scroll in scrolls:
                    status = 'IN-SAMPLE-SCROLL (segment check needed)'
                else:
                    status = 'OUT-OF-SAMPLE'
                out['rows'].append(dict(checkpoint=ck, scroll=scroll, kind=kind[:-1], window=w['id'],
                                        segment=w['segment'], status=status, basis=why,
                                        counts_toward_finalist=status == 'OUT-OF-SAMPLE'))
t = json.dumps(out, indent=1) + '\n'
assert t.isascii()
open(os.path.join(ROOT, 'logs/sib/ckpt-screen-c/insample.json'), 'w').write(t)
from collections import Counter
print(commit[:10], Counter((r['checkpoint'], r['status']) for r in out['rows']))
