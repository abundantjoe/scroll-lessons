#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# OWNER-ORDER-FL4-B: cut a grown tifxyz sheet into overlapping tile tifxyz dirs (valid cells only) and a lane assignment.
# usage: tile_sheet.py <sheet_dir> <out_dir> <n_lanes> [tile_cells=120] [overlap_cells=8]
import sys,os,json,shutil,numpy as np,tifffile
src,out,nl=sys.argv[1],sys.argv[2],int(sys.argv[3]); T=int(sys.argv[4]) if len(sys.argv)>4 else 120; O=int(sys.argv[5]) if len(sys.argv)>5 else 8
X,Y,Z=[tifffile.imread(f'{src}/{c}.tif') for c in 'xyz']; valid=(X>0)&(X!=-1); H,W=X.shape
tiles=[]
for y0 in range(0,H,T-O):
  for x0 in range(0,W,T-O):
    y1,x1=min(H,y0+T),min(W,x0+T); v=valid[y0:y1,x0:x1]
    if v.sum()<0.25*T*T: continue
    name=f't_r{y0:04d}_c{x0:04d}'; d=f'{out}/{name}'; os.makedirs(d,exist_ok=True)
    for c,a in zip('xyz',(X,Y,Z)):
      s=a[y0:y1,x0:x1].copy(); s[~v]=-1; tifffile.imwrite(f'{d}/{c}.tif',s)
    shutil.copy(f'{src}/meta.json',f'{d}/meta.json')
    tiles.append({'tile':name,'y0':y0,'x0':x0,'h':y1-y0,'w':x1-x0,'valid_cells':int(v.sum())})
tiles.sort(key=lambda t:-t['valid_cells'])
assign={i:[] for i in range(nl)}
for i,t in enumerate(tiles): assign[i%nl].append(t['tile'])
json.dump({'source':src,'grid':[H,W],'tile_cells':T,'overlap_cells':O,'tiles':tiles,'assign':assign},open(f'{out}/tiles.json','w'),indent=1)
print(len(tiles),'tiles;',sum(t['valid_cells'] for t in tiles),'valid cells')
