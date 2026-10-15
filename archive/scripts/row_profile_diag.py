"""Declared diagnostic: row-mean profile of s vs row-mean profile of the reference. Not a gate."""
import sys, os, json, numpy as np
d, tag, pitch = sys.argv[1], sys.argv[2], float(sys.argv[3])
ref = np.load(os.path.join(d, 'ref.npy'), mmap_mode='r')
out = {}
for f in ('top', 'bot'):
    s = np.load(os.path.join(d, f's_{f}_{tag}.npy'), mmap_mode='r')
    m = np.load(os.path.join(d, f'mask_{f}.npy'), mmap_mode='r') if os.path.exists(os.path.join(d, f'mask_{f}.npy')) else None
    H = s.shape[0]; ds = 8
    prof_s = np.zeros(H // ds); prof_r = np.zeros(H // ds); wt = np.zeros(H // ds)
    for i in range(H // ds):
        blk = np.asarray(s[i*ds:(i+1)*ds]).astype(np.float32)
        mk = np.asarray(m[i*ds:(i+1)*ds]) > 0 if m is not None else np.isfinite(blk) & (blk != 0)
        rb = np.asarray(ref[i*ds:(i+1)*ds]).astype(np.float32)
        if rb.shape != blk.shape:
            rb = rb[:blk.shape[0], :blk.shape[1]]
        n = mk.sum(); wt[i] = n
        if n > 0:
            prof_s[i] = blk[mk].mean(); prof_r[i] = rb[mk].mean()
    ok = wt > 0.2 * ds * s.shape[1]
    a = prof_s[ok] - prof_s[ok].mean(); b = prof_r[ok] - prof_r[ok].mean()
    r0 = float((a*b).sum() / np.sqrt((a*a).sum()*(b*b).sum() + 1e-12))
    L = int(5000 / pitch / ds); rs = []
    for lag in range(-L, L+1):
        x = a[max(0,lag):len(a)+min(0,lag)]; y = b[max(0,-lag):len(b)+min(0,-lag)]
        rs.append(float((x*y).sum()/np.sqrt((x*x).sum()*(y*y).sum()+1e-12)))
    j = int(np.argmax(np.abs(rs)))
    out[f] = dict(r_lag0=round(r0,4), r_best=round(rs[j],4), lag_best_mm=round((j-L)*ds*pitch/1000,3), rows_used=int(ok.sum()), rows=int(len(ok)))
    print(f, out[f])
json.dump(out, open(os.path.join(d, f'rowdiag_{tag}.json'), 'w'), indent=1)
