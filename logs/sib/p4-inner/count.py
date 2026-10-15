# DECL-P4-7 items 1-2, 1.129 um volume. Numeric only; no image is written or viewed.
import json,numpy as np,time,sys
from scipy.ndimage import gaussian_filter,map_coordinates
from spiral import centre,curve
from plane import plane
NR=64;ZS=np.linspace(70/2.4e-3,133/2.4e-3,24);V=1.129
SIG={'A_fwhm20um':20/2.3548/V,'B_sigma20um':20/V}
G=np.load('grid1129_20260623141924.npy')
def labelled(xy,c,nr=NR):
    ok=np.isfinite(xy[:,0]);idx=np.where(ok)[0];p=xy[idx]-c[:2]
    r=np.hypot(p[:,0],p[:,1]);tu=np.unwrap(np.arctan2(p[:,1],p[:,0]));t0=tu[0]
    sgn=np.sign(tu[-1]-tu[0]);k10=max(len(r)//20,1);outer_first=bool(np.median(r[:k10])>np.median(r[-k10:]))
    out=[]
    for k in range(nr):
        a=2*np.pi*k/nr;q=sgn*(tu-a)/(2*np.pi);n=np.floor(q);w=np.where(np.diff(n)!=0)[0];cr={}
        for m in w:
            f=(max(n[m],n[m+1])-q[m])/(q[m+1]-q[m]);rr=r[m]+f*(r[m+1]-r[m]);tt=tu[m]+f*(tu[m+1]-tu[m])
            off=int(np.floor(sgn*(tt-t0)/(2*np.pi)+1e-9))  # winding offset from column 0
            if outer_first: off=17-off  # column 0 is the outer end (w027): re-key so 0 -> w010
            if abs(r[m+1]-r[m])<100: cr[off]=float(rr)
        out.append(cr)
    return out
recs=[];prof={}
t00=time.time()
for iz,z in enumerate(ZS):
    c=centre(z);zc=int(round(c[2]));xy=curve(G,c[2]);L=labelled(xy,c)
    rmax=max([d.get(10,0) for d in L]+[0])+60
    rmax=int(min(rmax,4500));x0=int(c[0]-rmax);y0=int(c[1]-rmax)
    t=time.time();img,pres=plane(zc,y0,y0+2*rmax,x0,x0+2*rmax)
    img=img.astype(np.float32);tf=time.time()-t
    sm={k:gaussian_filter(img,s) for k,s in SIG.items()}
    for k in range(NR):
        a=2*np.pi*k/NR;d=L[k]
        if 0 not in d or 10 not in d: recs.append({'iz':iz,'ray':k,'ok':False,'why':'no w010 or w020 crossing','have':sorted(d)});continue
        R=d[10]+60;rs=np.arange(0,R,1.0)
        yy=c[1]+rs*np.sin(a)-y0;xx=c[0]+rs*np.cos(a)-x0
        pr=map_coordinates(pres.astype(np.float32),[yy,xx],order=0)
        raw=map_coordinates(img,[yy,xx],order=1)
        key=f'{iz}_{k}';prof[key+'_raw']=raw.astype(np.float32)
        for s in SIG: prof[key+'_'+s]=map_coordinates(sm[s],[yy,xx],order=1).astype(np.float32)
        recs.append({'iz':iz,'ray':k,'ok':bool(pr.min()>0),'why':'' if pr.min()>0 else 'missing chunk on ray','lab':{str(o):round(v,2) for o,v in sorted(d.items())},
                     'z24':float(z),'zc1129':zc,'c':[float(c[0]),float(c[1])]})
    print(iz,round(z*2.4e-3,1),'box',2*rmax,'fetch %.0fs'%tf,'elapsed %.0fs'%(time.time()-t00),flush=True)
    np.savez_compressed('profiles_1129.npz',**prof);json.dump(recs,open('rays_1129.json','w'))
print('done')
