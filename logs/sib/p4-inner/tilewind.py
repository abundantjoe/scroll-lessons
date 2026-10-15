import json,numpy as np,sys,re
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
t=json.load(open('tr1129.json'));M=np.array(t['transformation_matrix']);A=M[:,:3];b=M[:,3]
u=json.load(open('umb.json'));U=np.array(sorted([[p['z'],p['x'],p['y']] for p in u['control_points']]))
def rad(P):  # 2.4 frame points -> radius (vox) to umbilicus at same z
    return np.hypot(P[:,0]-np.interp(P[:,2],U[:,0],U[:,1]),P[:,1]-np.interp(P[:,2],U[:,0],U[:,2]))
def colwinding(G):
    """Per-column winding offset from per-z polylines (one point per column where the column crosses z), unwrapped angle about the umbilicus; mode over z-levels whose polyline starts within 20 columns of column 0."""
    from spiral import curve
    H,W,_=G.shape;Z=G[...,2];zlo,zhi=np.nanpercentile(Z,5),np.nanpercentile(Z,95);votes=[]
    for z0 in np.linspace(zlo,zhi,60):
        xy=curve(G.astype(np.float32),z0);ok=np.isfinite(xy[:,0])
        if ok.sum()<0.8*W: continue
        idx=np.where(ok)[0]
        if idx[0]>20: continue
        p=xy[idx];th=np.unwrap(np.arctan2(p[:,1]-np.interp(z0,U[:,0],U[:,2]),p[:,0]-np.interp(z0,U[:,0],U[:,1])))
        sgn=np.sign(th[-1]-th[0]);w=np.full(W,-1);w[idx]=np.floor(sgn*(th-th[0])/(2*np.pi)).astype(int);votes.append(w)
    V=np.array(votes);cw=np.array([np.bincount(V[:,j][V[:,j]>=0]).argmax() if (V[:,j]>=0).any() else -1 for j in range(W)])
    rr=np.nanmedian(np.hypot(G[::25,:,0]-np.interp(G[::25,:,2],U[:,0],U[:,1]),G[::25,:,1]-np.interp(G[::25,:,2],U[:,0],U[:,2])),0)
    k=W//20;outer_first=bool(np.nanmedian(rr[:k])>np.nanmedian(rr[-k:]))
    if outer_first: cw=np.where(cw>=0,cw.max()-cw,-1)
    return cw,len(votes),outer_first
seg,npz,key_suffix,out=sys.argv[1:5]
Q=np.load(f'grid1129_{seg}.npy');G=np.einsum('ij,hwj->hwi',A,Q.astype(np.float64))+b  # back to 2.4 frame
cw,nv,of=colwinding(G);print('rows voting',nv,'outer_first',of,'max winding offset',cw.max(),'monotone cols',np.mean(np.diff(cw[cw>=0])>=0))
H,W,_=G.shape;ii,jj=np.mgrid[0:H:2,0:W:2];S=G[ii,jj];ok=np.isfinite(S[...,0]);tree=cKDTree(S[ok]);cols=jj[ok]
d=np.load(npz);tiles=sorted({k.split('__')[0] for k in d.files})
res={};
for k in tiles:
    P=d[k+key_suffix].astype(np.float64) if key_suffix else d[k].astype(np.float64)
    P=P[np.isfinite(P).all(1)&(P[:,2]>0)]
    if len(P)==0: continue
    r=rad(P)*2.4e-3;dist,ix=tree.query(P);w=10+cw[cols[ix]]
    m=re.match(r'r(\d+)_c(\d+)',k);res[k]={'r':int(m[1]),'c':int(m[2]),'n':int(len(P)),'median_r_mm':round(float(np.median(r)),3),'r_mm_p10_p90':[round(float(np.percentile(r,10)),3),round(float(np.percentile(r,90)),3)],
      'median_z_mm':round(float(np.median(P[:,2]))*2.4e-3,2),'winding_median':float(np.median(w)),'winding_p10_p90':[float(np.percentile(w,10)),float(np.percentile(w,90))],'nn_dist_vox_median':round(float(np.median(dist)),2)}
rows={}
for v in res.values(): rows.setdefault(v['r'],[]).append(v)
summ={}
for r,L in sorted(rows.items()):
    L=sorted(L,key=lambda x:x['c']);c=[x['c'] for x in L];rr=[x['median_r_mm'] for x in L];ww=[x['winding_median'] for x in L]
    summ[r]={'n_tiles':len(L),'spearman_col_vs_radius':round(float(spearmanr(c,rr)[0]),3) if len(L)>2 else None,'spearman_col_vs_winding':round(float(spearmanr(c,ww)[0]),3) if len(L)>2 else None,
             'radius_first_last_col_mm':[rr[0],rr[-1]],'winding_first_last_col':[ww[0],ww[-1]]}
    print(r,summ[r])
json.dump({'segment':seg,'tile_points':npz,'frame':'2.4um 20260411134726 voxels','method':'winding per column from per-z polylines (mode over z-levels); radius = horizontal distance to the official umbilicus (S3 20260411134726-umbilicus-20260524235033.json) at each point z; winding = 10 + column-winding of the nearest vertex of the official 2.4um mesh (per-column winding from unwrapped angle around the umbilicus, mode over rows)',
  'mesh_rows_voting':nv,'mesh_column0_is_outer_end':of,'per_row':summ,'tiles':res},open(out,'w'),indent=1)
