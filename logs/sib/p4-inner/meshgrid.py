import json,numpy as np,io,urllib.request,tifffile,sys
S="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/segments/"
t=json.load(open('tr1129.json'));M=np.array(t['transformation_matrix']);A=M[:,:3];b=M[:,3];Ai=np.linalg.inv(A)
s=sys.argv[1];sid=s.split('-')[0];base=S+s+'/mesh/'+sid+'-on-20260411134726-2.4um.tifxyz/'
X={c:tifffile.imread(io.BytesIO(urllib.request.urlopen(base+c+'.tif').read())).astype(np.float64) for c in 'xyz'}
bad=(X['z']<=0)|(X['x']==-1)
P=np.stack([X[c] for c in 'xyz'],-1)-b
Q=np.einsum('ij,hwj->hwi',Ai,P).astype(np.float32);Q[bad]=np.nan
np.save(f'grid1129_{sid}.npy',Q);print(Q.shape,np.nanmin(Q[...,2]),np.nanmax(Q[...,2]))
# is z monotonic along rows?
dz=np.diff(Q[...,2],axis=0);print('frac dz>0 along axis0',np.nanmean(dz>0),'along axis1',np.nanmean(np.diff(Q[...,2],axis=1)>0))
