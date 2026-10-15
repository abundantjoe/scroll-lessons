import json,numpy as np,io,urllib.request,tifffile,sys
S="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/segments/"
a=json.load(open('umb.json'));U=np.array(sorted([[p['z'],p['x'],p['y']] for p in a['control_points']]))
def umb(z): return np.interp(z,U[:,0],U[:,1]),np.interp(z,U[:,0],U[:,2])
out={}
# abs winding (9.6um -> x4)
P=np.load('absP.npy')*4;W=np.load('absW.npy')
ux,uy=umb(P[:,2]);r=np.hypot(P[:,0]-ux,P[:,1]-uy)*2.4e-3
out['abs_winding']={'n':len(W),'w':W.tolist(),'r_mm':np.round(r,3).tolist(),'z_mm':np.round(P[:,2]*2.4e-3,2).tolist()}
k=np.polyfit(W,r,1);out['abs_fit_r_mm_per_w']=k.tolist()
print('abs fit r=%.3f*w+%.3f'%tuple(k))
for ww,rr,zz in sorted(zip(W,r,P[:,2]*2.4e-3))[:15]:print(' w',ww,'r_mm %.2f z_mm %.1f'%(rr,zz))
segs=sys.argv[1:]
for s in segs:
    sid=s.split('-')[0]
    base=S+s+'/mesh/'+sid+'-on-20260411134726-2.4um.tifxyz/'
    X={}
    for c in 'xyz':
        X[c]=tifffile.imread(io.BytesIO(urllib.request.urlopen(base+c+'.tif').read())).astype(np.float32)
    m=(X['z']>0)&np.isfinite(X['z'])&(X['x']!=-1)
    x,y,z=X['x'][m],X['y'][m],X['z'][m]
    ux,uy=umb(z);rr=np.hypot(x-ux,y-uy)*2.4e-3
    zb=(z*2.4e-3//10*10)
    per={}
    for b in np.unique(zb):
        q=rr[zb==b]
        if len(q)>1000: per[int(b)]=[round(float(np.percentile(q,p)),2) for p in (0,1,5,50,95,99,100)]
    out[s]={'grid':list(X['x'].shape),'valid':int(m.sum()),'z_mm':[round(float(z.min()*2.4e-3),1),round(float(z.max()*2.4e-3),1)],
      'r_mm_pct_0_1_5_50_95_99_100':[round(float(np.percentile(rr,p)),2) for p in (0,1,5,50,95,99,100)],'per_10mm_z':per}
    print(s,out[s]['grid'],out[s]['z_mm'],out[s]['r_mm_pct_0_1_5_50_95_99_100'])
    del X
json.dump(out,open('radii.json','w'),indent=1)
