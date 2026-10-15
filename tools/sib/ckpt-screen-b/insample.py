#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Per-DEV-window in-sample status (DECL-DEVLOOP-SCREEN item 3) from SPECS.json training lists and the devloop
branch's current dev_registry.json (read with git show; numbers and ids only)."""
import json, subprocess, time, hashlib
REG_REF = 'origin/claude/gifted-bell-gavnl5-sib-devloop:logs/sib/devloop/dev_registry.json'
raw = subprocess.check_output(['git', 'show', REG_REF])
reg = json.loads(raw)
specs = json.load(open('logs/sib/ckpt-screen-b/SPECS.json'))
rows = {}
for scroll, v in reg['scrolls'].items():
    for kind in ('windows', 'blanks'):
        for w in v.get(kind, []):
            wid = w.get('id') or f"{scroll}_{w.get('segment')}_y{w.get('y0')}_x{w.get('x0')}"
            st = {}
            for ck, c in specs['checkpoints'].items():
                tr = c['training_data']['scrolls']
                st[ck] = ('UNKNOWN (scroll in training list; same-papyrus not certified)' if scroll in tr
                          else 'OUT-OF-SAMPLE (scroll absent from every documented training list)')
            rows[wid] = dict(scroll=scroll, segment=w.get('segment'), kind=kind[:-1], status=st)
out = dict(provenance='Provenance: Project HERCULES | owner the owner | [id removed]',
           generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           registry_ref=REG_REF, registry_sha256=hashlib.sha256(raw).hexdigest(),
           registry_generated_utc=reg.get('generated_utc'),
           note='registry is the devloop branch state, not yet frozen under a METRIC-HASH; recompute on the frozen v3',
           windows=rows)
json.dump(out, open('logs/sib/ckpt-screen-b/insample.json', 'w'), indent=1)
print(len(rows), {k: sorted(set(r['status'].values())) for k, r in list(rows.items())[:1]})
