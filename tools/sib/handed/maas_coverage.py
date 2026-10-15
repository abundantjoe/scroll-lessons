# Provenance: Project HERCULES | owner the owner | [id removed]
"""Coverage numbers of the 0139 human ink labels in the levelled frame (why the column-slant check is underpowered). Numbers only."""
import sys, numpy as np, json
sys.path.insert(0,'tools/sib/handed'); sys.path.insert(0,'src')
import maas_labels as ML, maas as M
from hercules.geometry import level_mesh as L
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
from scipy.ndimage import gaussian_filter1d
out=[]
for tif in sorted(ML.S3.glob("PHerc0139/segments/*/mesh/*-on-20260102150214-2.399um.tifxyz")):
    seg=tif.parts[len(ML.S3.parts)+2]; pre=f"PHerc0139/segments/{seg}/ink-labels/2.399um-volume-20260102150214/20260918/"
    ink=np.asarray(ML.open_level(pre,'inklabels')[:])>0; sup=np.asarray(ML.open_level(pre,'supervision')[:])>0
    m=read_tifxyz(tif); sx,sy=m.scale; lv=L.level_mesh(m.points, step_vox=8.0)
    cx=lv.src_u/sx/8; cy=lv.src_v/sy/8
    ok=valid_mask(lv.points)&(cx>=0)&(cy>=0)&(cx<ink.shape[1]-1)&(cy<ink.shape[0]-1)
    ix=np.clip(np.round(cx).astype(int),0,ink.shape[1]-1); iy=np.clip(np.round(cy).astype(int),0,ink.shape[0]-1)
    lev=ok&ink[iy,ix]&sup[iy,ix]; supl=ok&sup[iy,ix]
    px=19.192e-3
    prof=gaussian_filter1d(lev.sum(0).astype(float),2); occ=prof>0.02*prof.max()
    # runs of occupancy
    d=np.diff(np.r_[0,occ.astype(int),0]); st=np.nonzero(d==1)[0]; en=np.nonzero(d==-1)[0]
    runs=[(round(a*px,1),round((b-a)*px,1)) for a,b in zip(st,en)]
    rowsup=supl.any(1).sum()*px; colsup=supl.any(0).sum()*px
    out.append(dict(segment=seg, ink_frac_of_supervised=float(lev.sum()/max(supl.sum(),1)), supervised_extent_mm_rows=float(rowsup), supervised_extent_mm_cols=float(colsup), ink_x_occupancy_runs_mm=[[float(a),float(b)] for a,b in runs]))
json.dump(dict(level=3,pixel_mm=0.019192,segments=out),open(sys.argv[1],"w"),indent=1); print(len(out))
