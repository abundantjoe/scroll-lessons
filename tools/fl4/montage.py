#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# One triage image per ring: for each patch a row of [ink_9um forward | ink_9um reverse | render centre layer | pieces],
# each 480 px, labelled. usage: montage.py <ring> <gathered_dir> <out.png>
import sys,os,glob,numpy as np,cv2
ring,G,out=sys.argv[1:4]; rows=[]
for d in sorted(glob.glob(f'{G}/i*')):
    i=os.path.basename(d); f=f'{d}/ink9um_forward.png'
    if not os.path.exists(f): continue
    def L(fn,cmap=None):
        a=cv2.imread(fn,0) if os.path.exists(fn) else np.zeros((480,480),np.uint8); a=cv2.resize(a,(480,480),interpolation=cv2.INTER_AREA)
        if cmap=='pieces': a=((a.astype(np.int32)*37)%256).astype(np.uint8)
        return cv2.cvtColor(a,cv2.COLOR_GRAY2BGR)
    fw=L(f); rv=L(f'{d}/ink9um_reverse.png'); ce=L(glob.glob(f'{d}/*_centre.png')[0]) if glob.glob(f'{d}/*_centre.png') else L('')
    pc=L(glob.glob(f'{d}/*_pieces.png')[0],'pieces') if glob.glob(f'{d}/*_pieces.png') else L('')
    # stretch ink maps to their own 1-99 percentile for visibility (display only)
    for im in (fw,rv):
        g=im[:,:,0]; nz=g[g>0]
        if nz.size: lo,hi=np.percentile(nz,[1,99]); im[:]=cv2.cvtColor(np.clip((g.astype(float)-lo)/max(hi-lo,1)*255,0,255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
    row=np.concatenate([fw,rv,ce,pc],1); cv2.putText(row,f'{ring} {i}: ink fwd | ink rev | centre layer | pieces (display stretch 1-99%)',(8,24),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,255),2); rows.append(row)
if rows: cv2.imwrite(out,np.concatenate(rows,0),[cv2.IMWRITE_PNG_COMPRESSION,6]); print('montage',out,len(rows),'patches')
else: print('no patches')
