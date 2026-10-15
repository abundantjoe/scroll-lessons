"""E3b: at 2.4 um the along-fibre background subtraction beats the across-fibre one by ~0.07 AUC
(E3). Is that a LOCAL fibre-frame effect, or just a global direction effect because the estimated
'fibre' direction happens to coincide with the text-line direction? Controls on the same window:
a single constant angle, the constant perpendicular angle, a randomised angle field, and the
orientation field estimated from BLANK pixels only (ink cannot steer it there)."""
import os, sys, json, numpy as np, cv2, gc
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import auc, ROOT, cdir
import fb_e3_fullres as E3   # reuse gblur / nconv / orientation / oriented on the same window

PITCH = 2.4; MM = 1000.0 / PITCH
d = cdir("20231005123336", "train")
N = E3.N
S, mf, m, txt, blk = E3.S, E3.mf, E3.m, E3.txt, E3.blk
Spre = E3.Spre
out = {}

# --- which direction is the structure tensor locking onto? ---
lab = txt.astype(np.float32)
for st in (6, 25, 100):
    th, coh = E3.orientation(S, mf, 1.0, st)
    def gdir(sel):
        t = np.mod(th[sel], np.pi)
        c2 = np.cos(2 * t).mean(); s2 = np.sin(2 * t).mean()
        return round(float(np.rad2deg(0.5 * np.arctan2(s2, c2)) % 180), 1), round(float(np.hypot(c2, s2)), 4)
    out[f"st{st}_theta_all"] = gdir(m)
    out[f"st{st}_theta_blank"] = gdir(blk)
    out[f"st{st}_theta_text"] = gdir(txt)
    # the same tensor computed with text pixels REMOVED from the mask (ink cannot steer it)
    mb = (m & ~txt)
    thb, _ = E3.orientation(S, mb.astype(np.float32), 1.0, st)
    dd = np.mod(th - thb, np.pi); dd = np.minimum(dd, np.pi - dd)
    out[f"st{st}_theta_blankmask"] = gdir(m)[0], round(float(np.rad2deg(np.median(dd[m]))), 1)
    out[f"st{st}_coh_text_vs_blank"] = [round(float(np.median(coh[txt])), 4), round(float(np.median(coh[blk])), 4)]
    print(st, {k: v for k, v in out.items() if k.startswith(f"st{st}")}, flush=True)
    if st == 25:
        th25 = th.copy(); th25_blank = thb.copy()
    del th, coh, thb; gc.collect()

# direction of the LABEL field itself (text-line / stroke direction)
gy, gx = np.gradient(E3.gblur(lab, 4.0))
Jxx = E3.gblur(gx * gx, 25); Jyy = E3.gblur(gy * gy, 25); Jxy = E3.gblur(gx * gy, 25)
thl = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy) + np.pi / 2
t = np.mod(thl[m], np.pi); c2 = np.cos(2 * t).mean(); s2 = np.sin(2 * t).mean()
out["label_theta_global"] = [round(float(np.rad2deg(0.5 * np.arctan2(s2, c2)) % 180), 1), round(float(np.hypot(c2, s2)), 4)]
del gy, gx, Jxx, Jyy, Jxy, thl; gc.collect()
print("label dir", out["label_theta_global"], flush=True)

# --- AUC with the estimated field vs constant / random / blank-estimated fields ---
res = {}
def add(name, r):
    for lab_, si in (("0.10", 0.10 * MM), ("0.25", 0.25 * MM)):
        res[f"{name}|int{lab_}"] = round(auc(E3.nconv(r, mf, si), txt, blk), 4)
    print(name, {k: v for k, v in res.items() if k.startswith(name + "|")}, flush=True)

th_g = float(np.mod(np.arctan2(np.sin(2 * np.mod(th25[m], np.pi)).mean(),
                               np.cos(2 * np.mod(th25[m], np.pi)).mean()) / 2, np.pi))
rng = np.random.default_rng(0)
fields = {
    "est":       th25,
    "estblank":  th25_blank,
    "perp":      th25 + np.pi / 2,
    "const":     np.full_like(th25, th_g),
    "constperp": np.full_like(th25, th_g + np.pi / 2),
    "rand":      rng.uniform(0, np.pi, th25.shape).astype(np.float32),
}
for shape in ((6.0, 1.0), (50.0, 2.0)):
    sa, sl = shape
    for name, F in fields.items():
        bg = E3.oriented(Spre, mf, F, sl * MM, sa)
        add(f"{name}|a{sa}px|l{sl}mm", Spre - bg)
        del bg; gc.collect()
out["auc"] = res
out["theta_global_used_deg"] = round(float(np.rad2deg(th_g)), 1)
json.dump(out, open(os.path.join(ROOT, "stats/explore/fb_e3b_whichdir.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
