#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# Independent sheet-following test (no circular-winding assumption): sample the organizer surface prediction at N random
# valid vertices of a tifxyz surface; report the fraction whose 5x5x5 neighbourhood max is >= 128 (vertex on predicted papyrus).
import sys,numpy as np,tifffile,zarr,s3fs
d=sys.argv[1]; N=int(sys.argv[2]) if len(sys.argv)>2 else 250
X,Y,Z=[tifffile.imread(f'{d}/{c}.tif') for c in 'xyz']; v=(X>0)&(X!=-1); idx=np.argwhere(v)
rng=np.random.default_rng(0); sel=idx[rng.choice(len(idx),min(N,len(idx)),replace=False)]
fs=s3fs.S3FileSystem(anon=True)
a=zarr.open(zarr.storage.FSStore('s3://vesuvius-challenge-open-data/PHerc0268/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr/0',fs=fs,mode='r'),mode='r')
cache={}; hits=0
for r,c in sel:
    x,y,z=int(round(X[r,c])),int(round(Y[r,c])),int(round(Z[r,c])); k=(z//192,y//192,x//192)
    if k not in cache: cache[k]=a[k[0]*192:(k[0]+1)*192,k[1]*192:(k[1]+1)*192,k[2]*192:(k[2]+1)*192]
    b=cache[k]; zz,yy,xx=z-k[0]*192,y-k[1]*192,x-k[2]*192
    w=b[max(zz-2,0):zz+3,max(yy-2,0):yy+3,max(xx-2,0):xx+3]; hits+= int(w.size>0 and w.max()>=128)
print(d,'on-sheet fraction',round(hits/len(sel),3),'n',len(sel),'chunks',len(cache))
