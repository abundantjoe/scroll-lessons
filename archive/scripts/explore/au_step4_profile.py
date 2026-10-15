"""AUDIT step 4: cross-stroke profile of every score map.

For each pixel define the SIGNED distance to the label boundary: +d inside the stroke, -d outside.
Average each score map in bins of that signed distance.  If the labels were mis-registered, our
scores would peak at a non-zero offset or have a flat/asymmetric profile; if the labels are right
and the physics is just weak, the profile peaks on the stroke centreline with a small amplitude.
Also reports amplitude in units of the local noise, which is what sets the achievable AUC.

usage: au_step4_profile.py <seg> <crop>
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import au_lib as A

seg, crop = sys.argv[1], sys.argv[2]
t0 = time.time()
L, text, blank, m = A.load_masks(seg, crop)
d_in = A.edt_mm(L)
d_out = A.edt_mm(~L)
sd = np.where(L, d_in, -d_out).astype(np.float32)          # signed distance, mm
del d_in, d_out

EDGES = np.arange(-1.20, 0.6001, 0.03, dtype=np.float32)
idx = np.digitize(sd[m], EDGES) - 1
nb = len(EDGES) - 1
ok = (idx >= 0) & (idx < nb)
idx = idx[ok]
cnt = np.bincount(idx, minlength=nb)
out = {"seg": seg, "crop": crop,
       "bin_centres_mm": [round(float((EDGES[i] + EDGES[i + 1]) / 2), 4) for i in range(nb)],
       "bin_counts": [int(c) for c in cnt]}
for tag in A.TAGS:
    s = A.load_score(seg, crop, tag)
    if s is None:
        continue
    v = s[m][ok].astype(np.float64)
    mean = np.bincount(idx, weights=v, minlength=nb) / np.maximum(cnt, 1)
    sq = np.bincount(idx, weights=v * v, minlength=nb) / np.maximum(cnt, 1)
    sdv = np.sqrt(np.maximum(sq - mean ** 2, 0))
    good = cnt > 2000
    pk = int(np.argmax(np.where(good, mean, -9e9)))
    far = good & (np.array(out["bin_centres_mm"]) < -0.9)
    base = float(mean[far].mean()) if far.any() else float(mean[good][0])
    noise = float(np.median(sdv[good]))
    out[tag] = {"profile_mean": [round(float(x), 4) for x in mean],
                "profile_sd": [round(float(x), 4) for x in sdv],
                "peak_bin_mm": out["bin_centres_mm"][pk],
                "peak_value": round(float(mean[pk]), 4),
                "baseline_lt_-0.9mm": round(base, 4),
                "amplitude": round(float(mean[pk]) - base, 4),
                "median_within_bin_sd": round(noise, 4),
                "amplitude_over_noise": round((float(mean[pk]) - base) / (noise + 1e-9), 4)}
    print(f"  {tag}: peak at {out[tag]['peak_bin_mm']} mm  amp {out[tag]['amplitude']}  "
          f"amp/noise {out[tag]['amplitude_over_noise']}", flush=True)
    del s, v
A.jwrite(os.path.join(A.ROOT, f"stats/explore/au_step4_{seg}_{crop}.json"), out)
print(f"done {time.time()-t0:.0f}s", flush=True)
