# numbers only: fraction of valid tifxyz vertices whose surface-m7 L0 value >= 128 (on sheet), and CT mask value > 0
import sys, json, glob, os, numpy as np
sys.path.insert(0, 'tools/sib/fl-pherc0846b/fl2'); import fl
H='https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0846B/'
sf=fl.Zarr(H+'representations/predictions/surfaces/20250804142305-surface-20260413222639-surface-m7-L0-th0.2.zarr/0')
ct=fl.Zarr(H+'volumes/20250804142305-9.362um-1.2m-113keV-masked.zarr/2')
rng=np.random.default_rng(0); out={}
for d in sorted(glob.glob('logs/sib/fl-pherc0846b/fl2/*/tifxyz')):
    P,V=fl.load_xyz(d); pts=P[V]; pts=pts[rng.choice(len(pts),min(300,len(pts)),replace=False)]
    on=[];inct=[];oob=0
    for x,y,z in pts:
        if not(0<=x<7859 and 0<=y<7859 and 0<=z<13926): oob+=1; continue
        # nearest surface voxel within +-2 vx (sheet thickness tolerance)
        v=max(sf.at(z+dz,y,x) for dz in (-2,0,2)); on.append(v>=128)
        inct.append(ct.at(z/4,y/4,x/4)>0)
    s=os.path.basename(os.path.dirname(d)).split('_')[-1]
    out[s]=dict(n=len(pts),oob=oob,on_sheet=round(float(np.mean(on)),3) if on else None,in_ct_mask=round(float(np.mean(inct)),3) if inct else None,
                bbox_min=P[V].min(0).round(0).tolist(),bbox_max=P[V].max(0).round(0).tolist())
    print(s,out[s],flush=True)
json.dump(out,open('/work/fl2/onsurf.json','w'),indent=1)
