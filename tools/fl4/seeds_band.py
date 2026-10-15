#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
# DECL-FL-5: seeds on one radial band of PHerc0268 (same method as fl4.py cmd_seeds_inner: centre of the surface-prediction
# hit run nearest t*R within +-0.025 R on the ray). usage: seeds_band.py <inner_seeds.json> <band_t> <z_frac> <out.json>
import sys,json,math; sys.path.insert(0,'tools/fl4'); import fl4
src=json.load(open(sys.argv[1])); t=float(sys.argv[2]); zf=float(sys.argv[3]); out=sys.argv[4]
cps=src['axis_points']; zr=src['umbilicus_z_range']; sf=fl4.Zarr(src['surface'].rstrip('/')+'/0'); ct3=fl4.Zarr(src['ct'].rstrip('/')+'/3')
z=zr[0]+zf*(zr[1]-zr[0]); cx,cy=fl4.umbilicus_xy(cps,z); seeds=[]
for k in range(8):
    az=45*k; th=math.radians(az); dx,dy=math.cos(th),math.sin(th); R=0
    for r3 in range(0,1200):
        x3,y3=(cx+r3*8*dx)/8,(cy+r3*8*dy)/8
        if not (0<=x3<ct3.shape[2] and 0<=y3<ct3.shape[1]): break
        if ct3.at(z/8,y3,x3)>0: R=r3*8
    ent={'band_t':t,'z_frac':zf,'azimuth_deg':az,'z':round(z,1),'umb_x':round(cx,1),'umb_y':round(cy,1),'outer_radius_vox':R}
    lo,hi=int((t-0.025)*R),int((t+0.025)*R); vals=[sf.at(z,cy+r*dy,cx+r*dx) for r in range(lo,hi)]
    vmax=max(vals) if vals else 0; thr=128 if vmax>=128 else (1 if vmax>0 else None); best=None
    if thr is not None:
        runs=[]
        for h in [lo+i for i,v in enumerate(vals) if v>=thr]:
            if runs and h==runs[-1][-1]+1: runs[-1].append(h)
            else: runs.append([h])
        best=min(runs,key=lambda r:abs((r[0]+r[-1])/2-t*R))
    if best is None: ent['result']='no surface on ray'
    else:
        r=(best[0]+best[-1])/2; ent.update(result='seed',r_vox=int(r),r_over_R=round(r/R,3),seed_xyz=[round(cx+r*dx,1),round(cy+r*dy,1),round(z,1)])
    seeds.append(ent); print(ent)
json.dump({'decl':'DECL-FL-5','ct':src['ct'],'surface':src['surface'],'axis_points':cps,'umbilicus_z_range':zr,'seeds':seeds},open(out,'w'),indent=1)
