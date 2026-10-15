# Planted-sheet test (DECL-P4-7 item 2). 1-D: real CT noise residuals + planted Gaussian sheets, same smoothing + detector.
import json,numpy as np
from scipy.signal import find_peaks,peak_prominences
from scipy.ndimage import gaussian_filter1d
V=1.129;DIST=int(round(20/V));rng=np.random.default_rng(20260926)
A=json.load(open('analysis_1129.json'));recs=[r for r in json.load(open('rays_1129.json')) if r['ok']];P=np.load('profiles_1129.npz')
out={}
for sig,s in (('A_fwhm20um',20/2.3548/V),('B_sigma20um',20/V)):
    th=A['results'][sig]['calibration_threshold_grey']
    # amplitude model: prominences of detected peaks in labelled zone (smoothed profile), converted to raw amplitude by ratio of smoothing
    proms=[];noises=[];means=[]
    for r in recs:
        lab=r['lab'];r0,r10=int(lab['0']),int(lab['10']);p=P[f"{r['iz']}_{r['ray']}_{sig}"];raw=P[f"{r['iz']}_{r['ray']}_raw"]
        pk=find_peaks(p[r0:r10],prominence=th,distance=DIST)[0]
        if len(pk): proms+=list(peak_prominences(p[r0:r10],pk)[0])
        res=raw-gaussian_filter1d(raw,35/V)
        noises.append(res[:max(r0-20,50)]);means.append(float(np.mean(raw[:max(r0-20,50)])))
    proms=np.array(proms);out[sig]={'threshold':th,'labelled_zone_prominence_grey':{'p25':float(np.percentile(proms,25)),'median':float(np.median(proms)),'p75':float(np.percentile(proms,75))}}
    scen={'wide_pitch_150-250um':(150,250),'labelled_like_180-260um':(180,260),'mid_pitch_100-150um':(100,150),'tight_pitch_70-100um':(70,100),'very_tight_50-70um':(50,70)}
    sres={}
    for name,(p0,p1) in scen.items():
        errs=[];errs0=[]
        for trial in range(400):
            N=int(rng.integers(0,26)) if trial%8 else 0
            pitch=rng.uniform(p0,p1,N)/V;pos=np.cumsum(pitch)+rng.uniform(20,60)/V
            Lr=int((pos[-1] if N else 300/V)+rng.uniform(30,80)/V)
            nz=noises[rng.integers(len(noises))]
            while len(nz)<Lr: nz=np.r_[nz,noises[rng.integers(len(noises))]]
            st=rng.integers(0,len(nz)-Lr+1);x=np.arange(Lr)
            prof=means[rng.integers(len(means))]+nz[st:st+Lr].copy()
            for c in pos[pos<Lr]:
                w=rng.uniform(8,20)/V;amp=rng.choice(proms)*rng.uniform(0.6,1.2)
                # raw amplitude such that after smoothing prominence ~ amp: scale by sqrt(1+(s/w)^2)
                prof+=amp*np.sqrt(1+(s/w)**2)*np.exp(-0.5*((x-c)/w)**2)
            ps=gaussian_filter1d(prof,s);k=len(find_peaks(ps,prominence=th,distance=DIST)[0])
            (errs if N else errs0).append(k-N)
        e=np.array(errs);sres[name]={'n_trials':len(e),'median_err':float(np.median(e)),'mean_abs_err':round(float(np.mean(np.abs(e))),2),'frac_abs_err_le1':round(float(np.mean(np.abs(e)<=1)),3),
          'p5_p95_err':[float(np.percentile(e,5)),float(np.percentile(e,95))],'null_N0_false_peaks_median':float(np.median(errs0)),'null_N0_false_peaks_max':int(np.max(errs0))}
        print(sig,name,sres[name])
    out[sig]['scenarios']=sres
json.dump(out,open('synth_1129.json','w'),indent=1)
