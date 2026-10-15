# DECL-P4-7 items 1-2 analysis. Detector and calibration rule fixed before inner counts are read.
import json,numpy as np,sys
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
V=1.129;DIST=int(round(20/V));THR=[2,3,4,6,8,12,16]
recs=json.load(open('rays_1129.json'));P=np.load('profiles_1129.npz')
ok=[r for r in recs if r['ok'] and all(str(i) in r['lab'] for i in range(11))]
def peaks(p,th): return find_peaks(p,prominence=th,distance=DIST)[0]
def zone(lab):
    r0,r1=lab['0'],lab['1'];r10=lab['10'];r9=lab['9'];r11=lab.get('11',r10+(r10-r9))
    h0=0.5*(r1-r0);return r0,h0,r10,0.5*(r11-r10) if '11' in lab else 0.5*(r10-r9)
def count(r,sig,th):
    p=P[f"{r['iz']}_{r['ray']}_{sig}"];pk=peaks(p,th);lab=r['lab'];r0,h0,r10,h10=zone(lab)
    inner=pk[pk<r0-h0];labz=pk[(pk>=r0+h0)&(pk<r10+h10)]
    return inner,labz,pk
out={'n_rays_total':len(recs),'n_rays_ok':len(ok),'excluded':{}}
for r in recs:
    why=r['why'] if not r['ok'] else ('' if all(str(i) in r['lab'] for i in range(11)) else 'labelled crossings w010-w020 incomplete')
    if why: out['excluded'][why]=out['excluded'].get(why,0)+1
res={}
for sig in ['A_fwhm20um','B_sigma20um']:
    cal={}
    for th in THR:
        lc=[len(count(r,sig,th)[1]) for r in ok];cal[th]=float(np.median(lc))
    best=min(THR,key=lambda t:(abs(cal[t]-10),-t))
    # per ray
    rows=[];insp=[];labsp=[];imgsp=[];hit=[]
    for r in ok:
        inner,labz,pk=count(r,sig,best);lab=r['lab'];r0=lab['0']
        L=np.array([lab[str(i)] for i in range(11) if str(i) in lab])
        labsp+=list(np.diff(L)*V)
        if len(inner): insp+=list(np.diff(np.r_[inner,r0])*V)
        if len(labz)>1: imgsp+=list(np.diff(labz)*V)
        tol=[max(20/V,0.25*(L[i+1]-L[i-1])/2) for i in range(1,len(L)-1)]
        hit+=[bool(len(pk) and np.min(np.abs(pk-L[i]))<=tol[i-1]) for i in range(1,len(L)-1)]
        rows.append({'iz':r['iz'],'ray':r['ray'],'z_mm':round(r['z24']*2.4e-3,2),'r_w010_mm':round(r0*V/1000,3),'n_inner':int(len(inner)),'n_labzone':int(len(labz)),
                     'inner_r_mm':[round(float(x)*V/1000,3) for x in inner]})
    n=np.array([x['n_inner'] for x in rows]);nl=np.array([x['n_labzone'] for x in rows])
    grid={(x['iz'],x['ray']):x['n_inner'] for x in rows}
    dr=[abs(grid[(i,k)]-grid[(i,(k+1)%64)]) for (i,k) in grid if (i,(k+1)%64) in grid]
    dz=[abs(grid[(i,k)]-grid[(i+1,k)]) for (i,k) in grid if (i+1,k) in grid]
    q=lambda a:{'median':round(float(np.median(a)),1),'iqr':[round(float(np.percentile(a,25)),1),round(float(np.percentile(a,75)),1)],'n':len(a)} if len(a) else None
    ratio=np.median(nl)/10
    res[sig]={'calibration_threshold_grey':best,'calibration_median_labzone_counts':cal,
      'labelled_crossing_hit_rate':round(float(np.mean(hit)),3),
      'n_inner':{'median':float(np.median(n)),'iqr':[float(np.percentile(n,25)),float(np.percentile(n,75))],'min':int(n.min()),'max':int(n.max()),
                 'hist':{int(v):int((n==v).sum()) for v in np.unique(n)},'frac_gt10':round(float(np.mean(n>10)),3),'frac_ge10':round(float(np.mean(n>=10)),3),'frac_le2':round(float(np.mean(n<=2)),3)},
      'n_labzone':{'median':float(np.median(nl)),'iqr':[float(np.percentile(nl,25)),float(np.percentile(nl,75))]},
      'n_inner_calibrated_median':round(float(np.median(n)/ratio),2) if ratio>0 else None,
      'per_z_median_n_inner':{str(round(ZZ,1)):float(np.median([x['n_inner'] for x in rows if x['z_mm']==ZZ])) for ZZ in sorted(set(x['z_mm'] for x in rows))},
      'per_z_median_r_w010_mm':{str(round(ZZ,1)):float(np.median([x['r_w010_mm'] for x in rows if x['z_mm']==ZZ])) for ZZ in sorted(set(x['z_mm'] for x in rows))},
      'spacing_um':{'inner_peaks':q(insp),'labelled_w010_w020_mesh':q(labsp),'image_peaks_in_labelled_zone':q(imgsp)},
      'continuity':{'adjacent_ray_step_ge1':round(float(np.mean(np.array(dr)>=1)),3),'adjacent_ray_step_ge2':round(float(np.mean(np.array(dr)>=2)),3),
                    'adjacent_z_step_ge1':round(float(np.mean(np.array(dz)>=1)),3),'adjacent_z_step_ge2':round(float(np.mean(np.array(dz)>=2)),3),'n_pairs':[len(dr),len(dz)]},
      'rows':rows}
    print(sig,'thr',best,cal,'hit',res[sig]['labelled_crossing_hit_rate'],'inner',res[sig]['n_inner'],'lab',res[sig]['n_labzone'],res[sig]['spacing_um'],res[sig]['continuity'])
out['results']=res;json.dump(out,open('analysis_1129.json','w'),indent=1)
