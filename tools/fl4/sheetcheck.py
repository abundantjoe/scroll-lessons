# Sheet-following check: for a grown tifxyz surface, |cos| between surface normal and the radial direction
# from a vertical axis through the seed's umbilicus. A surface on one papyrus wrap has |cos| near 1 and a narrow
# radius spread; a surface cutting across wraps has low |cos| and a wide radius spread.
import json,sys,glob,os,numpy as np,tifffile
seeds=json.load(open('logs/fl4/seeds_inner_PHerc0268.json'))['seeds']
for d in sys.argv[1:]:
    import re; m=re.findall(r'i(\d+)',d); i=int(os.environ.get('SEED_IDX') or m[-1]); s=seeds[i]   # A7-E1: lane dirs are .../i<N>/seg
    if 'umb_x' not in s: print(d,'no umb'); continue
    X,Y,Z=[tifffile.imread(f'{d}/{c}.tif').astype(float) for c in 'xyz']
    v=(X>0)|(Y>0)|(Z>0); v&=~(np.isnan(X)|(X==-1))
    P=np.stack([X,Y,Z],-1)
    du=np.gradient(P,axis=1); dv=np.gradient(P,axis=0); n=np.cross(du,dv)
    nn=np.linalg.norm(n,axis=-1); ok=v&(nn>0)
    n=n[ok]/nn[ok,None]; p=P[ok]
    r=np.stack([p[:,0]-s['umb_x'],p[:,1]-s['umb_y'],0*p[:,0]],-1); R=np.linalg.norm(r,axis=-1); rh=r/np.maximum(R,1e-6)[:,None]
    c=np.abs((n*rh).sum(-1))
    print(f"i{i:3d} seed r={s.get('r_vox')} R(p10/50/90)={np.percentile(R,10):.0f}/{np.median(R):.0f}/{np.percentile(R,90):.0f} vox  z {p[:,2].min():.0f}-{p[:,2].max():.0f}  |cos(n,radial)| median={np.median(c):.2f} frac>0.8={np.mean(c>0.8):.2f} frac<0.3={np.mean(c<0.3):.2f}")
    if os.environ.get('SHEET_JSON'):
        side_cm=np.sqrt(v.sum())*20*8.64e-4
        g={'seed':i,'median_cos':float(np.median(c)),'frac_gt08':float(np.mean(c>0.8)),'R_p10':float(np.percentile(R,10)),'R_p90':float(np.percentile(R,90)),'side_cm':float(side_cm)}
        g['spread_mm_per_cm']=(g['R_p90']-g['R_p10'])*8.64e-3/max(side_cm,1e-6)
        g['pass']=bool(g['median_cos']>=0.8 and g['frac_gt08']>=0.7 and g['spread_mm_per_cm']<2.0)
        json.dump(g,open(os.environ['SHEET_JSON'],'w'),indent=1); print('GATE',json.dumps(g))
