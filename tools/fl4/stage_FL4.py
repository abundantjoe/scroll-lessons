"""DECL-FL-4-A2 census stager (numbers and hashes only; nothing displayed): PHerc0268 GP cover windows -> one DECL-FL-3 batch.
usage: stage_FL4.py <wave N> [--dry]. Pre-screen as DECL-FL-3 item 5: valid >= 0.5, ink_score_ge128 in [0.01, 0.40], unread."""
import json, os, subprocess, sys, hashlib
R='/home/user/dominion'; N=int(sys.argv[1]); DRY='--dry' in sys.argv; LOCAL='--local' in sys.argv  # --local: DECL-FL-4-A4 outputs in logs/fl4l
sha=lambda b: hashlib.sha256(b).hexdigest()
a=json.load(open(f'{R}/logs/fl4/assign.json')); W=[w['worker'] for w in a['scrolls']['PHerc0268']['workers']]
def sh(c): return subprocess.run(c,shell=True,capture_output=True,text=True,cwd=R).stdout
subprocess.run('git fetch -q origin '+' '.join(f'claude/gifted-bell-gavnl5-sib-{w}' for w in W),shell=True,cwd=R)
rw=f'{R}/logs/fl2/read_windows.json'; read=set(json.load(open(rw))) if os.path.exists(rw) else set()
rows=[]
import glob as _g
if LOCAL:
    for m in sorted(_g.glob(f'{R}/logs/fl4l/*/cover_gp_B/manifest.json')):
        for x in json.load(open(m)).get('windows',[]): rows.append(dict(x, worker='orchestrator-local', ref=None, path=m.rsplit('/',1)[0][len(R)+1:]+'/'+x['file']))
    W=[]
for w in W:
    b=f'origin/claude/gifted-bell-gavnl5-sib-{w}'
    for m in [f for f in sh(f'git ls-tree -r --name-only {b} logs/sib/{w}/fl4/PHerc0268').split() if f.endswith('cover_gp_B/manifest.json')]:
        try: d=json.loads(sh(f'git show {b}:{m}'))
        except Exception: continue
        for x in d.get('windows',[]): rows.append(dict(x, worker=w, ref=b, path=m.rsplit('/',1)[0]+'/'+x['file']))
# DECL-FL-4-A3 item 2b: segments without any cover window contribute their A1 r0 c0 tile, re-framed at window scale
wseg={r['segment'] for r in rows}
for w in W:
    b=f'origin/claude/gifted-bell-gavnl5-sib-{w}'
    for m in [f for f in sh(f'git ls-tree -r --name-only {b} logs/sib/{w}/fl4/PHerc0268').split() if f.endswith('tiles_gp_B/manifest.json')]:
        try: d=json.loads(sh(f'git show {b}:{m}'))
        except Exception: continue
        for x in d.get('tiles',[]):
            if x.get('segment') in wseg or x.get('r')!=0 or x.get('c')!=0: continue
            rows.append(dict(x, worker=w, ref=b, path=m.rsplit('/',1)[0]+'/'+x['file'], valid_fraction_of_content=x.get('valid_fraction'), a1tile=True))
el=[r for r in rows if (r.get('valid_fraction_of_content') or 0)>=0.5 and 0.01<=(r.get('ink_score_ge128') or 0)<=0.40 and r['png_sha256'] not in read]
el.sort(key=lambda r: (r['segment'], r['direction']))
print(json.dumps({'windows_all':len(rows),'eligible':len(el),'segments':len({r['segment'] for r in el}),'dirs':sorted({r['direction'] for r in el})}))
if DRY or not el: sys.exit(0)
batch=f'fl3w{N}pherc0268'; d=f'/work/fl3/w{N}/{batch}/tiles'; assert not os.path.exists(f'/work/fl3/w{N}'), 'wave exists'; os.makedirs(d)
p=b''.join((lambda b: f'x blob {len(b)}\n'.encode()+b+b'\n')(open(f"{R}/{r['path']}",'rb').read()) for r in el) if LOCAL else subprocess.run(['git','-C',R,'cat-file','--batch'],input=''.join(f"{r['ref']}:{r['path']}\n" for r in el).encode(),capture_output=True).stdout
i=0; man=[]; M={}
for r in el:
    j=p.index(b'\n',i); h=p[i:j].split(); i=j+1; n=int(h[2]); blob=p[i:i+n]; i+=n+1
    assert sha(blob)==r['png_sha256'], r['path']
    k=len(man); fn=f'{d}/{batch}_r{k}_c0.png'
    if r.get('a1tile'):
        import cv2, numpy as np
        t=cv2.imdecode(np.frombuffer(blob,np.uint8),cv2.IMREAD_GRAYSCALE); fr=np.zeros((1068,1068),np.uint8)
        fr[:534,:534]=cv2.resize(t,(534,534),interpolation=cv2.INTER_AREA); cv2.imwrite(fn,fr); blob=open(fn,'rb').read()
    else: open(fn,'wb').write(blob)
    man.append({'r':k,'c':0,'sha256':sha(blob),'valid_fraction':r['valid_fraction_of_content']})
    M[f'{batch}|{k}']={'scroll':'PHerc0268','model':'GP_timesformer_B','worker':r['worker'],'segment':r['segment'],'direction':r['direction'],'r':0,'c':0,
        'window':('A1 r0c0 tile re-framed at 26.7 px/mm (DECL-FL-4-A3)' if r.get('a1tile') else 'whole FL-4 segment canvas (DECL-FL-4-A2)'),'mean_ink_score_ge128':r['ink_score_ge128'],'mean_valid_fraction':r['valid_fraction_of_content'],
        'ref':r['ref'],'src_paths':[r['path']],'window_sha256':sha(blob),'src_png_sha256':r['png_sha256'],'ident':r['png_sha256']}
json.dump({'segment':batch,'kind':'DECL-FL-4-A2 GP cover windows, 26.7 px/mm','tiles':man},open(f'/work/fl3/w{N}/{batch}/manifest_norm.json','w'),indent=1)
json.dump(M,open(f'{R}/logs/fl2/fl3w{N}_windows.json','w'),indent=1); print('staged',len(man),batch)
