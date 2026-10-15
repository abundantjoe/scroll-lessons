#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4-A7 item 3: unroll sheet-following patches of one winding band into ONE continuous strip.
# Every ink-map pixel gets its 3D position by bilinear interpolation of the patch tifxyz (render scale 1: 20 px per cell),
# then lands at (azimuth about the umbilicus x R_ref, z) in voxel units; overlaps are averaged and 1-3 px holes closed.
# usage: unroll_ring.py <direction> <out.png> <umb_x> <umb_y> <R_ref> <patch_dir>...   (patch_dir holds tifxyz/ and gp_B_<dir>.png)
import sys,os,json,numpy as np,cv2,tifffile
dirn,out,ux,uy,Rr=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:6]); dirs=[d for d in sys.argv[6:] if not d.startswith('--')]
PAT=os.environ.get('MAP_PATTERN','gp_B_{dir}.png')
pts=[]
for d in dirs:
    T=d+'/tifxyz' if os.path.isdir(d+'/tifxyz') else d
    f=f'{d}/'+PAT.format(dir=dirn)
    if not os.path.exists(f): print('skip (no map)',d); continue
    X,Y,Z=[tifffile.imread(f'{T}/{c}.tif').astype(np.float32) for c in 'xyz']; im=cv2.imread(f,cv2.IMREAD_GRAYSCALE)
    h,w=im.shape; gh,gw=X.shape; v=((X>0)&(X!=-1)).astype(np.float32)
    up=lambda a: cv2.resize(a,(w,h),interpolation=cv2.INTER_LINEAR)
    Xu,Yu,Zu,Vu=up(X),up(Y),up(Z),up(v); ok=(Vu>0.999)&(im>0)
    th=np.arctan2(Yu[ok]-uy,Xu[ok]-ux); pts.append((th,Zu[ok],im[ok].astype(np.float32),d))
    print(d,'pixels',int(ok.sum()),'grid',X.shape,'render',im.shape)
if not pts: sys.exit('no maps')
th_all=np.concatenate([p[0] for p in pts]); ref=np.angle(np.mean(np.exp(1j*th_all)))+np.pi   # cut the circle opposite the mean
zs=np.concatenate([p[1] for p in pts]); z0=np.floor(zs.min())
U=[np.mod(p[0]-ref,2*np.pi)*Rr for p in pts]; u0=np.floor(min(u.min() for u in U))
W=int(max(u.max() for u in U)-u0)+2; H=int(zs.max()-z0)+2
acc=np.zeros((H,W),np.float32); cnt=np.zeros((H,W),np.float32)
for (th,z,val,d),u in zip(pts,U):
    xi=np.round(u-u0).astype(int); yi=np.round(z-z0).astype(int)
    np.add.at(acc,(yi,xi),val); np.add.at(cnt,(yi,xi),1)
img=np.where(cnt>0,acc/np.maximum(cnt,1),0).astype(np.uint8)
m=(cnt>0).astype(np.uint8); mc=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
fill=cv2.inpaint(img,((mc>0)&(m==0)).astype(np.uint8),3,cv2.INPAINT_TELEA); img=np.where(mc>0,fill,0).astype(np.uint8)
img=img[::-1]   # z up
cv2.imwrite(out,img,[cv2.IMWRITE_PNG_COMPRESSION,9])
json.dump({'direction':dirn,'umb':[ux,uy],'R_ref':Rr,'cut_azimuth_rad':float(ref),'z0':float(z0),'u0':float(u0),'size':[H,W],'patches':[p[3] for p in pts],
  'coverage_px':int((mc>0).sum())},open(out.rsplit('.',1)[0]+'.json','w'),indent=1)
print('strip',img.shape,'->',out)
