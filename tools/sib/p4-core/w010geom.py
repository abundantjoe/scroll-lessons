import numpy as np, json
from scipy.spatial import cKDTree
a=json.load(open("umb.json")); U=np.array(sorted([[p['z'],p['x'],p['y']] for p in a['control_points']]))
x,y,z=[np.load(f"{c}.npy",mmap_mode='r') for c in "xyz"]
H,W=x.shape
out=[]
for r in range(60,H-40,120):
    m=(x[r]!=-1)&(z[r]>0); cols=np.where(m)[0]
    if len(cols)<1000: continue
    X=np.stack([x[r,cols],y[r,cols]],1).astype(np.float64); zz=float(np.median(z[r,cols]))
    ux=np.interp(zz,U[:,0],U[:,1]); uy=np.interp(zz,U[:,0],U[:,2])
    th=np.unwrap(np.arctan2(X[:,1]-uy,X[:,0]-ux)); s=(th-th[-1])/(2*np.pi)  # turns outward from inner end (sign fixed below)
    if s[0]<0: s=-s
    w=np.floor(s).astype(int)  # 0 -> w010
    def curve(k): return X[w==k]
    L0=curve(0)
    # polygon area (closed by chord)
    P=L0; A=0.5*abs(np.dot(P[:,0],np.roll(P[:,1],-1))-np.dot(P[:,1],np.roll(P[:,0],-1)))*(2.4e-3)**2
    c=P.mean(0); ev,evec=np.linalg.eigh(np.cov((P-c).T)); pr=(P-c)@evec
    ext=pr.max(0)-pr.min(0)
    # umbilicus inside? winding number of closed polygon
    d=P-[ux,uy]; ang=np.arctan2(d[:,1],d[:,0]); wn=np.sum(np.angle(np.exp(1j*np.diff(np.r_[ang,ang[0]]))))/(2*np.pi)
    dumb=np.hypot(*(P-[ux,uy]).T).min()*2.4e-3
    # normal spacing between consecutive windings k,k+1 : nearest distance from curve k points to curve k+1
    sp={}
    for k in range(0,17):
        A_=curve(k);B_=curve(k+1)
        if len(A_)<20 or len(B_)<20: continue
        dd,_=cKDTree(B_).query(A_); sp[k+10]=float(np.median(dd)*2.4e-3)
    out.append(dict(row=r,z_mm=round(zz*2.4e-3,2),turns=round(float(s[0]),2),w010_area_mm2=round(A,3),
        w010_width_major_minor_mm=[round(float(ext[1])*2.4e-3,3),round(float(ext[0])*2.4e-3,3)],
        umb_inside_w010=int(round(abs(wn))),umb_min_dist_to_w010_mm=round(float(dumb),3),
        umb_offset_from_w010_centroid_mm=round(float(np.hypot(c[0]-ux,c[1]-uy))*2.4e-3,3),
        spacing_mm={k:round(v,3) for k,v in sp.items()}))
json.dump(out,open("w010geom.json","w"),indent=0)
for o in out:
    s=o['spacing_mm']; v=list(s.values())
    print(o['z_mm'],o['turns'],"A",o['w010_area_mm2'],"maj/min",o['w010_width_major_minor_mm'],"umbIn",o['umb_inside_w010'],"dUmb",o['umb_min_dist_to_w010_mm'],"off",o['umb_offset_from_w010_centroid_mm'],"sp10-11 %.3f med10-20 %.3f"%(s.get(10,np.nan),np.median([s[k] for k in s if k<20])))
