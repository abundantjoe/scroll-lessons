#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# OWNER-ORDER-FL4-B: reassemble per-tile GP ink maps into ONE continuous sheet image (tile offsets from tiles.json,
# 20 px per grid cell at render scale 1; overlaps feathered). usage: stitch_sheet.py <sheet_dir> <direction> <out.png>
import sys,json,glob,numpy as np,cv2
S,dirn,out=sys.argv[1],sys.argv[2],sys.argv[3]; meta=json.load(open(f'{S}/tiles.json')); px=20
H,W=meta['grid']; acc=np.zeros((H*px,W*px),np.float32); wt=np.zeros_like(acc); n=0
for t in meta['tiles']:
    f=glob.glob(f"{S}/lane*/{t['tile']}_{dirn}.png")
    if not f: continue
    im=cv2.imread(f[0],cv2.IMREAD_GRAYSCALE).astype(np.float32); h,w=im.shape
    y0,x0=t['y0']*px,t['x0']*px; h=min(h,acc.shape[0]-y0); w=min(w,acc.shape[1]-x0); im=im[:h,:w]
    ry=np.minimum(np.arange(h)+1,np.arange(h)[::-1]+1); rx=np.minimum(np.arange(w)+1,np.arange(w)[::-1]+1)
    f2=np.minimum.outer(np.minimum(ry,160),np.minimum(rx,160)).astype(np.float32)  # feather 160 px = 8 overlap cells
    acc[y0:y0+h,x0:x0+w]+=im*f2; wt[y0:y0+h,x0:x0+w]+=f2; n+=1
img=np.where(wt>0,acc/np.maximum(wt,1e-6),0).astype(np.uint8)
ys,xs=np.nonzero(wt); img=img[ys.min():ys.max()+1,xs.min():xs.max()+1] if n else img
cv2.imwrite(out,img,[cv2.IMWRITE_PNG_COMPRESSION,9]); print(n,'tiles stitched ->',out,img.shape)
