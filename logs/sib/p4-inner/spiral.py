import json,numpy as np
t=json.load(open('tr1129.json'));M=np.array(t['transformation_matrix']);A=M[:,:3];b=M[:,3];Ai=np.linalg.inv(A)
u=json.load(open('umb.json'));U=np.array(sorted([[p['z'],p['x'],p['y']] for p in u['control_points']]))
def centre(z24):
    x=np.interp(z24,U[:,0],U[:,1]);y=np.interp(z24,U[:,0],U[:,2]);return Ai@(np.array([x,y,z24])-b)
def curve(G,z0):
    """per column: xy where the column's z crosses z0 (z decreasing along axis0). returns (W,2) with nan."""
    Z=G[...,2];H,W=Z.shape;s=Z-z0
    c=(s[:-1]>=0)&(s[1:]<0)
    i=np.argmax(c,0);ok=c[i,np.arange(W)]
    j=np.arange(W);z1=Z[i,j];z2=Z[i+1,j];f=np.where(ok,(z1-z0)/(z1-z2+1e-9),np.nan)
    xy=G[i,j,:2]*(1-f)[:,None]+G[i+1,j,:2]*f[:,None];xy[~ok]=np.nan;return xy
def crossings(xy,c,nr=64,maxgap=40):
    ok=np.isfinite(xy[:,0]);idx=np.where(ok)[0];p=xy[idx]-c[:2]
    r=np.hypot(p[:,0],p[:,1]);th=np.arctan2(p[:,1],p[:,0])
    # unwrap in segments; break where column gap>maxgap or jump in r > 200 vox
    brk=np.where((np.diff(idx)>maxgap)|(np.abs(np.diff(r))>200))[0]
    segs=np.split(np.arange(len(idx)),brk+1)
    # orient: inner end = smaller r
    if np.median(r[:len(r)//10])>np.median(r[-len(r)//10:]): pass
    out=[[] for _ in range(nr)];nseg=len(segs)
    for sg in segs:
        if len(sg)<5: continue
        tu=np.unwrap(th[sg]);rs=r[sg]
        for k in range(nr):
            a=2*np.pi*k/nr
            # crossings where (tu-a)/(2pi) crosses an integer
            q=(tu-a)/(2*np.pi);n=np.floor(q);w=np.where(np.diff(n)!=0)[0]
            for m in w:
                f=(np.round(max(n[m],n[m+1]))-q[m])/(q[m+1]-q[m]) if q[m+1]!=q[m] else 0
                out[k].append((float(rs[m]+f*(rs[m+1]-rs[m])),int(idx[sg[m]])))
    return [sorted(o) for o in out],nseg,float(np.nanmedian(r)),len(idx)
if __name__=='__main__':
    G=np.load('grid1129_20260623141924.npy')
    ZS=np.linspace(70/2.4e-3,133/2.4e-3,24);res=[]
    for z in ZS:
        c=centre(z);xy=curve(G,c[2]);R,ns,rm,nv=crossings(xy,c)
        n=[len(x) for x in R];r0=[x[0][0]*1.129e-3 for x in R if x]
        # ordering by column index vs by radius agree?
        mono=np.mean([all(np.diff([q[1] for q in x])>0) or all(np.diff([q[1] for q in x])<0) for x in R if len(x)>2])
        print(round(z*2.4e-3,1),'valid cols',nv,'segs',ns,'ncross med',np.median(n),min(n),max(n),'r0 med %.2f [%.2f,%.2f]'%(np.median(r0),min(r0),max(r0)),'col-order monotone frac %.2f'%mono)
        res.append({'z24':float(z),'c':c.tolist(),'R':R,'nseg':ns})
    json.dump(res,open('spiral_rays.json','w'))
