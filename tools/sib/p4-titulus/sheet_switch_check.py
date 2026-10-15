# Numbers only: nearest 3-D distance from title-zone tile mesh points to the mesh points of the
# outer (lower-c) tiles of the same canvas. A mesh sheet-switch onto the outer winding would give
# distances ~0 (overlap); a proper adjacent winding gives ~ one pitch (~0.2 mm), limited by sampling.
import sys, numpy as np
from scipy.spatial import cKDTree
z=np.load(sys.argv[1]); v=0.0024
P={tuple(int(s[1:]) for s in k.split('_')):z[k]*v for k in z.files}
spac=[]
for (r,c),p in P.items():
    t=cKDTree(p); d,_=t.query(p,k=2); spac.append(np.median(d[:,1]))
print('median in-tile point spacing mm %.3f'%np.median(spac))
def test(r,c,outer_cols):
    q=P[(r,c)]; ref=np.concatenate([P[(rr,cc)] for rr in range(max(0,r-1),min(8,r+2)) for cc in outer_cols if (rr,cc) in P])
    d,_=cKDTree(ref).query(q); return np.percentile(d,[5,50]), (d<0.05).mean()
print('tile  outer-cols  d_p5  d_p50  frac<0.05mm')
for r in range(0,6):
    for c in [5,6,7,8,11,12,13,14,15,16]:
        oc=list(range(max(0,c-7),c-1))  # tiles >=2 columns outward (skip immediate neighbour, which is contiguous sheet)
        (p5,p50),f=test(r,c,oc)
        print('r%dc%-2d c%d-%d  %.3f  %.3f  %.3f'%(r,c,oc[0],oc[-1],p5,p50,f))
print('INWARD: tile  inner-cols  d_p5  d_p50')
for r in range(0,4):
    for c in [7,8,9,11,12,13]:
        ic=[cc for cc in range(c+2,min(20,c+8))]
        (p5,p50),f=test(r,c,ic); print('r%dc%-2d c%d-%d  %.3f  %.3f  %.3f'%(r,c,ic[0],ic[-1],p5,p50,f))
