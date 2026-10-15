#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# Raw-CT cross-sections through a tifxyz patch at 4 heights (level-1 CT, 17 um/px) with the surface drawn, plus the same
# bands marked on an ink map. usage: xsections.py <tifxyz_dir> <ct_level1_url> <out_prefix> [ink_map.png]
import sys,json,numpy as np,tifffile,zarr,s3fs,cv2
T,CT,out=sys.argv[1:4]; ink=sys.argv[4] if len(sys.argv)>4 else None
fs=s3fs.S3FileSystem(anon=True); a=zarr.open(zarr.storage.FSStore(CT,fs=fs,mode='r'),mode='r')
X,Y,Z=[tifffile.imread(f'{T}/{c}.tif').astype(float) for c in 'xyz']; v=(X>0)&(X!=-1)
zs=np.percentile(Z[v],[12,37,62,87]).round().astype(int); cols=[(0,0,255),(0,200,255),(0,255,0),(255,0,255)]; panels=[]; bands=[]
for zi,col in zip(zs,cols):
    m=v&(np.abs(Z-zi)<12); P=np.stack([X[m],Y[m]],1); bands.append((int(zi),col,np.argwhere(m)))
    if len(P)<5: continue
    x0,x1=int(P[:,0].min()/2)-120,int(P[:,0].max()/2)+120; y0,y1=int(P[:,1].min()/2)-120,int(P[:,1].max()/2)+120
    x0,y0=max(x0,0),max(y0,0); sl=np.asarray(a[zi//2,y0:y1,x0:x1]); nz=sl[sl>0]
    if nz.size<100: continue
    lo,hi=np.percentile(nz,[1,99]); g=np.clip((sl.astype(float)-lo)/(hi-lo)*255,0,255).astype(np.uint8); im=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR)
    for x,y in P: cv2.circle(im,(int(x/2-x0),int(y/2-y0)),2,col,-1)
    cv2.putText(im,f'z={zi} raw CT level1 17um/px; dots = surface within +-12 vox',(8,22),cv2.FONT_HERSHEY_SIMPLEX,0.6,col,2); panels.append(im)
if panels:
    W=max(p.shape[1] for p in panels); cv2.imwrite(out+'_xsec.png',np.concatenate([cv2.copyMakeBorder(p,0,6,0,W-p.shape[1],cv2.BORDER_CONSTANT,value=(40,40,40)) for p in panels],0),[cv2.IMWRITE_PNG_COMPRESSION,6])
if ink:
    g=cv2.imread(ink,0); im=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR); s=g.shape[0]/X.shape[0]
    for zi,col,idx in bands:
        for r,c in idx: cv2.circle(im,(int((c+0.5)*s),int((r+0.5)*s)),6,col,2)
    cv2.imwrite(out+'_ink_bands.png',im,[cv2.IMWRITE_PNG_COMPRESSION,6])
json.dump({'z_levels':[int(z) for z in zs]},open(out+'_xsec.json','w')); print('xsections',out,[int(z) for z in zs],len(panels),'panels')
