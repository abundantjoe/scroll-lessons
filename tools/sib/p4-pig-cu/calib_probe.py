import sys,time,json,numpy as np,concurrent.futures as cf
sys.path.insert(0,'tools/sib/p4-pig-cu'); import hz_common as C
seg="20260623142658-w028-037"; url=C.sv_prefix(seg)+"/0/0"
import requests
za=requests.get(C.sv_prefix(seg)+"/0/.zarray").json(); print(za)
H,W=za['shape'][1:]
rng=np.random.default_rng(1)
ys=rng.integers(0,H//128,400); xs=rng.integers(0,W//128,400)
h=np.zeros((116,256),np.int64); t0=time.time(); nb=0
def f(yx):
    b=C.get(f"{url}/{yx[0]}/{yx[1]}"); return b
with cf.ThreadPoolExecutor(32) as ex:
    for b in ex.map(f,list(zip(ys,xs))):
        if b is None: continue
        nb+=len(b); a=np.frombuffer(b,np.uint8).reshape(116,-1)
        if (a>0).mean()<0.9: continue
        for z in range(116): h[z]+=np.bincount(a[z],minlength=256)
print("MB/s",nb/1e6/(time.time()-t0))
tot=h.sum(0); tot[0]=0; c=np.cumsum(tot)/tot.sum()
print("pcts", {q:int(np.searchsorted(c,q)) for q in (0.001,0.01,0.05,0.1,0.25,0.5,0.75,0.9,0.99,0.999,0.9999)})
# coarse histogram
print("hist16",[int(x) for x in np.add.reduceat(tot,np.arange(0,256,16))])
print("mode_lowhalf",int(np.argmax(tot[1:128]))+1)
np.save('/tmp/claude-0/sp/probe_hist.npy',h)
