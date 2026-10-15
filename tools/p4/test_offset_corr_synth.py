# Provenance: Project HERCULES | [id removed]
"""Synthetic test of tools/p4/offset_corr.py (no real data): signal case must be INFORMATIVE, noise case not."""
import os, sys, json, subprocess, numpy as np, cv2, shutil
SEG='20260701183124-w010-027'; T,P=8343,1068; S=P/T
D=sys.argv[1] if len(sys.argv)>1 else '/tmp/oc_test'; shutil.rmtree(D,ignore_errors=True)
rng=np.random.default_rng(1)
# forward mosaic: smoothed random texture (text-like blobs) in 1..254, avoiding 91
M=rng.random((9*P//4,21*P//4)).astype(np.float32); M=cv2.GaussianBlur(M,(0,0),3); M=cv2.resize(M,(21*P,9*P))
M=(M-M.min())/(M.max()-M.min()); M=np.clip(M*250+2,1,254).astype(np.uint8); M[M==91]=92
DY,DX=150.0,3*T+400.0
def facing(r,c,dy,dx):
    cy=r*T+(np.arange(32)+0.5)*T/32; cx=c*T+(np.arange(32)+0.5)*T/32
    F=np.stack(np.meshgrid(cy+dy,cx+dx,indexing='ij'),-1).astype(np.float32); return F
for case in ('signal','noise'):
    for sub in ('v','f','g'): os.makedirs(f'{D}/{case}/{sub}',exist_ok=True)
    for r in range(9):
        for c in range(21):
            f=M[r*P:(r+1)*P,c*P:(c+1)*P]; cv2.imwrite(f'{D}/{case}/f/{SEG}_r{r}_c{c}.png',f)
            Fo=facing(r,c,DY,DX); Fi=facing(r,c,-DY,-DX)
            if c+3>20: Fo[:]=np.nan
            np.savez_compressed(f'{D}/{case}/g/r{r}_c{c}.npz',outer=Fo,inner=Fi)
            if case=='signal':
                yy,xx=np.mgrid[0:P,0:P].astype(np.float32)
                mx=((c*T+(xx+0.5)/S+DX)*S-0.5).astype(np.float32); my=((r*T+(yy+0.5)/S+DY)*S-0.5).astype(np.float32)
                v=cv2.remap(M.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
                v=np.clip(0.4*v+0.6*rng.normal(128,40,v.shape),1,254).astype(np.uint8)
            else: v=np.clip(rng.normal(128,40,(P,P)),1,254).astype(np.uint8)
            v[v==91]=92; cv2.imwrite(f'{D}/{case}/v/{SEG}_r{r}_c{c}.png',v)
    o=subprocess.run(['/opt/hv/bin/python3','tools/p4/offset_corr.py',f'{D}/{case}/v',f'{D}/{case}/f',f'{D}/{case}/g',f'{D}/{case}/out.json','20'],capture_output=True,text=True)
    print(case,o.stdout.strip()[-600:],o.stderr[-800:])
