"""p4-purple-de B3/B4: calibration, papyrus-line decomposition, patch statistic, and control validation.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python analyze.py fit <scratch>       (FIT sites only -> logs/sib/p4-purple/de/fit.json)
       python analyze.py validate <scratch>  (HELD-OUT sites; reads fit.json unchanged -> validation.json)
Numbers only: grey profiles are reduced to patch means; nothing is displayed.
"""
import json
import os
import sys
import time

import numpy as np
import xraylib as xr
from scipy import ndimage as ndi
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

mode, scr = sys.argv[1], sys.argv[2]
_dumps, _dump = json.dumps, json.dump
_j = lambda o: o.item() if hasattr(o, "item") else str(o)
json.dumps = lambda *a, **k: _dumps(*a, **{"default": _j, **k})
json.dump = lambda *a, **k: _dump(*a, **{"default": _j, **k})
OUT = os.path.join(D.REPO, "logs/sib/p4-purple/de")
SITES = json.load(open(os.path.join(OUT, "sites.json")))["sites"]
WIN = {"78": (-0.04, 0.22), "137": (0.01, 0.16)}
S, PS, NS, C0 = 498, 83, 51, 25
SL15 = slice(C0 - 6, C0 + 7)
UM = 2.4


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def tof(g, e):
    w0, w1 = WIN[e]
    return w0 + g * (w1 - w0) / 255.0


def load_site(sid):
    z = np.load(os.path.join(scr, "sites", sid + ".npz"))
    return {k: z[k].astype(np.float32) for k in ("g78", "g137", "g137m")}


def patch_means(f, valid, sl=slice(None)):
    """(6,6) patch means of f over valid px and depth slice sl; also valid fraction."""
    col = f[:, :, sl].mean(2)
    v = valid[:6 * PS, :6 * PS].reshape(6, PS, 6, PS)
    c = (col[:6 * PS, :6 * PS] * valid[:6 * PS, :6 * PS]).reshape(6, PS, 6, PS)
    n = v.sum((1, 3))
    return c.sum((1, 3)) / np.maximum(n, 1), n / PS ** 2


def site_patches(g78, g137, sl=slice(None)):
    valid = (g78.min(2) > 0.5) & (g137.min(2) > 0.5)
    c78, fv = patch_means(tof(g78, "78"), valid, sl)
    c137, _ = patch_means(tof(g137, "137"), valid, sl)
    return c78, c137, fv


def otsu_modes(h):
    x = np.arange(256)
    h = h.astype(np.float64)
    h[0] = 0
    best, tb = -1, 0
    for t in range(2, 254):
        w0, w1 = h[:t].sum(), h[t:].sum()
        if w0 == 0 or w1 == 0:
            continue
        m0, m1 = (x[:t] * h[:t]).sum() / w0, (x[t:] * h[t:]).sum() / w1
        v = w0 * w1 * (m0 - m1) ** 2
        if v > best:
            best, tb = v, t
    return int(np.argmax(h[:tb])), int(tb + np.argmax(h[tb:])), tb


PAP = "C0.70O0.25H0.05"


def mu_rho_pap(E):
    return 0.70 * xr.CS_Total_CP("C", E) + 0.25 * xr.CS_Total_CP("O", E) + 0.05 * xr.CS_Total_CP("H", E)


# =====================================================================================================  FIT
if mode == "fit":
    fit = [s for s in SITES["fit"]]
    h = {"78": np.zeros(256), "137": np.zeros(256)}
    P = []
    for s in fit:
        d = load_site(s["id"])
        valid = (d["g78"].min(2) > 0.5) & (d["g137"].min(2) > 0.5)
        for e in ("78", "137"):
            h[e] += np.bincount(np.clip(np.rint(d["g" + e][valid]), 0, 255).astype(int).ravel(), minlength=256)
        c78, c137, fv = site_patches(d["g78"], d["g137"])
        a78, a137, _ = site_patches(d["g78"], d["g137"], SL15)
        for i in range(6):
            for j in range(6):
                if fv[i, j] >= 0.5:
                    P.append((s["id"], i, j, c78[i, j], c137[i, j], a78[i, j], a137[i, j]))
        log("fit site", s["id"], len(P))
    modes = {}
    for e in ("78", "137"):
        v, p, t = otsu_modes(h[e])
        modes[e] = {"void_grey": v, "papyrus_grey": p, "otsu_grey": t, "void_cm-1": tof(v, e), "papyrus_cm-1": tof(p, e)}
    C78 = np.array([p[3] for p in P]); C137 = np.array([p[4] for p in P])
    A78 = np.array([p[5] for p in P]); A137 = np.array([p[6] for p in P])
    k, k0, klo, khi = stats.theilslopes(C137, C78)
    k15, k015, _, _ = stats.theilslopes(A137, A78)
    Z = C137 - (k * C78 + k0)
    Z15 = A137 - (k15 * A78 + k015)
    med, mad = float(np.median(Z)), float(1.4826 * np.median(np.abs(Z - np.median(Z))))
    med15, mad15 = float(np.median(Z15)), float(1.4826 * np.median(np.abs(Z15 - np.median(Z15))))
    z = (Z - med) / mad
    T = float(np.percentile(np.abs(z), 99))
    onsheet_thr = 0.25 * modes["78"]["papyrus_cm-1"]
    on = C78 >= onsheet_thr
    rho = {e: modes[e]["papyrus_cm-1"] / mu_rho_pap(float(e)) for e in ("78", "137")}
    k_theory = mu_rho_pap(137.0) / mu_rho_pap(78.0)
    out = {"provenance": D.PROV, "serves": "PROTOCOL.md B3 (FIT sites only; frozen before any held-out number)",
           "n_fit_sites": len(fit), "n_fit_patches": len(P), "modes": modes,
           "calibration_checks": {
               "i_void_near_zero": {e: modes[e]["void_cm-1"] for e in modes},
               "i_pass": all(abs(modes[e]["void_cm-1"]) <= 0.01 for e in modes),
               "ii_implied_papyrus_density_g_cm3": rho,
               "ii_rel_diff": abs(rho["137"] - rho["78"]) / rho["78"],
               "ii_pass": abs(rho["137"] - rho["78"]) / rho["78"] <= 0.20,
               "iii_k_theory_mono": k_theory, "iii_k_measured": k, "iii_rel_diff": abs(k - k_theory) / k_theory,
               "iii_pass": abs(k - k_theory) / k_theory <= 0.15},
           "papyrus_line": {"k": k, "k0": k0, "k_95ci": [klo, khi], "window_um": 122.4},
           "papyrus_line_15um": {"k": k15, "k0": k015},
           "Z_median": med, "Z_mad_scaled": mad, "Z15_median": med15, "Z15_mad_scaled": mad15,
           "T_abs_z_p99": T, "onsheet_C78_min_cm-1": onsheet_thr,
           "fit_patch_onsheet_frac": float(on.mean()),
           "fit_hotspot_rate": float(((np.abs(z) > T) & on).mean()),
           "fit_Z_percentiles_cm-1": {q: float(np.percentile(Z, q)) for q in (1, 5, 50, 95, 99)},
           "fit_C78_percentiles": {q: float(np.percentile(C78, q)) for q in (1, 50, 99)},
           "fit_C137_percentiles": {q: float(np.percentile(C137, q)) for q in (1, 50, 99)},
           "pearson_C78_C137": float(np.corrcoef(C78, C137)[0, 1]),
           "hist_grey": {e: h[e].astype(int).tolist() for e in h},
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(out, open(os.path.join(OUT, "fit.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    log(json.dumps({k_: out[k_] for k_ in ("modes", "calibration_checks", "papyrus_line", "Z_mad_scaled", "T_abs_z_p99",
                                             "fit_hotspot_rate", "pearson_C78_C137")}))
    sys.exit(0)

# =====================================================================================================  VALIDATE
F = json.load(open(os.path.join(OUT, "fit.json")))
k, k0 = F["papyrus_line"]["k"], F["papyrus_line"]["k0"]
k15, k015 = F["papyrus_line_15um"]["k"], F["papyrus_line_15um"]["k0"]
MED, MAD, T, ONT = F["Z_median"], F["Z_mad_scaled"], F["T_abs_z_p99"], F["onsheet_C78_min_cm-1"]
LEV = {e: 0.5 * (F["modes"][e]["void_cm-1"] + F["modes"][e]["papyrus_cm-1"]) for e in ("78", "137")}
_cc = F["modes"]
G137 = ((_cc["137"]["papyrus_cm-1"] - _cc["137"]["void_cm-1"]) / (_cc["78"]["papyrus_cm-1"] - _cc["78"]["void_cm-1"])) / \
    F["calibration_checks"]["iii_k_theory_mono"]
LAB = json.load(open(os.path.join(OUT, "labels.json")))

# ---------------- colourants (colourants.json 143e1e6 compositions; recomputed with xraylib 4.3.0)
import subprocess  # noqa: E402
CJ = json.loads(subprocess.check_output(["git", "-C", D.REPO, "show",
                                         "143e1e6:logs/sib/p4-purple/colourants.json"]))
PHI = 0.5
BINDER = [("C", 0.70), ("O", 0.25), ("H", 0.05)]


def mix_props(comps, rho, E):
    """(mu cm^-1, delta) of a mass-fraction mixture at solid density rho."""
    mr = sum(w * xr.CS_Total_CP(c, E) for c, w in comps)
    dr = sum(w * (1 - xr.Refractive_Index_Re(c, E, 1.0)) for c, w in comps)  # delta per g/cm3
    return mr * rho, dr * rho


def layer_props(comps, rho, E):
    mp, dp = mix_props(comps, rho, E)
    mb, db = mix_props(BINDER, 1.0, E)
    return PHI * mp + (1 - PHI) * mb, PHI * dp + (1 - PHI) * db


CLASSES = {
    "Tyrian purple 0% Br loss": "Tyrian purple, 0 % Br loss", "Tyrian purple 50% Br loss": "Tyrian purple, 50 % Br loss",
    "Tyrian purple 90% Br loss": "Tyrian purple, 90 % Br loss",
    "purpurissum (5% dye on CaCO3)": "purpurissum (5 wt% Tyrian dye on CaCO3)",
    "alumina lake": "alumina lake (10 wt% alizarin on Al(OH)3)", "gypsum lake": "gypsum lake (10 wt% alizarin on CaSO4.2H2O)",
    "orpiment": "orpiment As2S3", "lead white": "lead white (hydrocerussite)", "cinnabar": "cinnabar HgS", "gold": "gold",
    "CuO": None, "Fe2O3 (red ochre)": "red ochre (hematite Fe2O3)", "carbon ink": "carbon ink (soot)"}
MAT, XCHECK = {}, {}
for name, key in CLASSES.items():
    if key is None:
        comps, rho = [("CuO", 1.0)], 6.31
    else:
        m = CJ["materials"][key]
        comps, rho = [(c, w) for c, w in m["components_mass_fraction"]], m["solid_density_g_cm3"]
    MAT[name] = {e: layer_props(comps, rho, float(e)) for e in ("78", "137")}
    if key is not None:
        ref = CJ["materials"][key]["phi"]["0.5"]
        XCHECK[name] = {e: {"mu_rel": MAT[name][e][0] / ref[e]["mu_cm-1"] - 1, "delta_rel": MAT[name][e][1] / ref[e]["delta"] - 1}
                        for e in ("78", "137")}
xmax = max(abs(v) for d in XCHECK.values() for e in d.values() for v in e.values())
log("colourant cross-check max rel diff", xmax)
assert xmax <= 0.01, XCHECK

# ---------------- 1-D forward model (linear Paganin, published pipeline), per energy
SC = {"78": {"E": 78.0, "db": 1000.0, "uc": 4.0, "us": 1.2}, "137": {"E": 137.0, "db": 2000.0, "uc": 5.0, "us": 2.5}}
DX = 0.1e-6
NF = 1 << 14
NPH = 20
MLO, MHI = -40, 60     # response support in samples relative to the start sample


def response(mu_cm, delta, t_um, e, absorption_only=False):
    """table[phase, m]: Delta f (cm^-1) at sample (base + m) for a layer starting at (base + phase/NPH) samples."""
    p = SC[e]
    lam = 12.398419843320026e-10 / p["E"]
    z = 0.22
    c = p["db"] * lam / (4 * np.pi)
    kk = 2 * np.pi * np.fft.fftfreq(NF, DX)
    s_un = p["us"] * UM * 1e-6
    U = 1 + p["uc"] * (1 - np.exp(-kk ** 2 * s_un ** 2 / 2))
    PSF = np.exp(-kk ** 2 * (UM * 1e-6) ** 2 / 2)
    tab = np.zeros((NPH, MHI - MLO))
    mu_m = mu_cm * 100.0
    for ph in range(NPH):
        x0 = 2000e-6 * 0 + (ph / NPH) * UM * 1e-6
        x = (np.arange(NF) - NF // 4) * DX            # domain -409.6 .. +1228.8 um
        slab = ((x >= x0) & (x < x0 + t_um * 1e-6)).astype(np.float64)
        Sk = np.fft.fft(slab)
        if absorption_only:
            R = mu_m * Sk * PSF
        else:
            R = (mu_m * Sk + z * kk ** 2 * delta * Sk) / (1 + z * c * kk ** 2) * U * PSF
        r = np.real(np.fft.ifft(R)) / 100.0           # cm^-1
        box = int(round(UM * 1e-6 / DX))
        rb = np.convolve(r, np.ones(box) / box, mode="same")
        centres = (np.arange(MLO, MHI) + 0.0) * UM * 1e-6   # sample m centre relative to base sample centre
        idx = np.clip(np.rint((centres - x[0]) / DX).astype(int), 0, NF - 1)
        tab[ph] = rb[idx]
    return tab


RESP = {}
THK = (5, 10, 20)
for name in MAT:
    for t in THK:
        for e in ("78", "137"):
            for ab in (False, True):
                RESP[(name, t, e, ab)] = response(MAT[name][e][0], MAT[name][e][1], t, e, ab)
log("responses", len(RESP))
self_test = {}
for e in ("78", "137"):  # unit gain at k = 0: integral of the response = mu t
    tab = RESP[("carbon ink", 10, e, False)]
    self_test[e] = float(tab[0].sum() * UM / (MAT["carbon ink"][e][0] * 10))

# ---------------- glyph and helpers
yy, xx = np.mgrid[0:S, 0:S]
GLYPH = ((np.abs(xx - 249) <= 83.3) & (np.abs(yy - 249) <= 208.3)) | ((np.abs(yy - 249) <= 83.3) & (np.abs(xx - 249) <= 208.3))
gfrac = GLYPH[:6 * PS, :6 * PS].reshape(6, PS, 6, PS).mean((1, 3))
INJ = gfrac >= 0.8
gi_, gj_ = np.nonzero(GLYPH)


def crossings(prof, level):
    """Nearest crossing of level on the + and - side of sample C0 (fractional sample index), NaN if none."""
    sm = ndi.gaussian_filter1d(prof, 1.0, axis=-1)
    d = sm - level
    sgn = np.sign(d)
    ch = sgn[..., 1:] != sgn[..., :-1]                   # between j and j+1
    j = np.arange(NS - 1)
    frac = d[..., :-1] / (d[..., :-1] - d[..., 1:] + 1e-12)
    pos = j + frac
    plus = np.where(ch & (j >= C0), pos, np.inf).min(-1)
    minus = np.where(ch & (j + 1 <= C0), pos, -np.inf).max(-1)
    return np.where(np.isfinite(plus), plus, np.nan), np.where(np.isfinite(minus), minus, np.nan)


def zstat(c78, c137):
    return ((c137 - (k * c78 + k0)) - MED) / MAD


def hot(c78, c137):
    return (np.abs(zstat(c78, c137)) > T) & (c78 >= ONT)


def auc(pos, neg):
    if len(pos) == 0 or len(neg) == 0:
        return None
    return float(stats.mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))


rng_b = np.random.default_rng(5)
rng_s = np.random.default_rng(11)
held = SITES["held"]
rec = {"sites": [], "patch": []}
surf = []
inj_rows = []
t0 = time.time()
for s in held:
    d = load_site(s["id"])
    g78, g137, g137m = d["g78"], d["g137"], d["g137m"]
    valid = (g78.min(2) > 0.5) & (g137.min(2) > 0.5)
    validm = (g78.min(2) > 0.5) & (g137m.min(2) > 0.5)
    c78, fv = patch_means(tof(g78, "78"), valid)
    c137, _ = patch_means(tof(g137, "137"), valid)
    a78, _ = patch_means(tof(g78, "78"), valid, SL15)
    a137, _ = patch_means(tof(g137, "137"), valid, SL15)
    m78, fvm = patch_means(tof(g78, "78"), validm)
    m137, _ = patch_means(tof(g137m, "137"), validm)
    lab = np.load(os.path.join(scr, "labels", s["id"] + ".npy"))
    labr = np.rot90(lab)
    for i in range(6):
        for j in range(6):
            blk = lab[i * PS:(i + 1) * PS, j * PS:(j + 1) * PS]
            blr = labr[i * PS:(i + 1) * PS, j * PS:(j + 1) * PS]
            L = lambda b: 1 if (b == 1).mean() >= 0.25 else (-1 if ((b == -1).mean() >= 0.9 and (b == 1).sum() == 0) else 0)
            rec["patch"].append({"site": s["id"], "i": i, "j": j, "fv": float(fv[i, j]), "fvm": float(fvm[i, j]),
                                 "C78": float(c78[i, j]), "C137": float(c137[i, j]),
                                 "z": float(zstat(c78[i, j], c137[i, j])),
                                 "z15": float(((a137[i, j] - (k15 * a78[i, j] + k015)) - F["Z15_median"]) / F["Z15_mad_scaled"]),
                                 "zm": float(zstat(m78[i, j], m137[i, j])), "C78m": float(m78[i, j]),
                                 "label": L(blk), "label_rot90": L(blr), "injected_patch": bool(INJ[i, j])})
    # sheet-surface residual (every 8th px)
    sub = (slice(None, None, 8), slice(None, None, 8))
    p78, m78_ = crossings(tof(g78[sub], "78"), LEV["78"])
    p137, m137_ = crossings(tof(g137[sub], "137"), LEV["137"])
    vs = valid[sub]
    for a, b in ((p137, p78), (m137_, m78_)):
        dd = (a - b)[vs & np.isfinite(a) & np.isfinite(b)] * UM
        surf.append(dd)
    # injection: layer from the + surface of the 78 keV profile outward
    prof78 = tof(g78[gi_, gj_], "78")
    sp, _ = crossings(prof78, LEV["78"])
    start = np.where(np.isfinite(sp), sp, C0 + 30 / UM)
    base0 = np.floor(start).astype(int)
    ph0 = np.minimum(((start - base0) * NPH).astype(int), NPH - 1)
    pvalid = valid[gi_, gj_]
    shifts = rng_s.choice(np.concatenate(surf) if len(np.concatenate(surf)) else np.zeros(1), size=(6, 6)) / UM
    sh_px = shifts[np.minimum(gi_ // PS, 5), np.minimum(gj_ // PS, 5)]
    kk_ = np.arange(NS)

    def inject(g, e, tab, st):
        b = np.floor(st).astype(int)
        ph = np.minimum(((st - b) * NPH).astype(int), NPH - 1)
        m = kk_[None, :] - b[:, None]
        inr = (m >= MLO) & (m < MHI)
        dl = tab[ph[:, None], np.clip(m - MLO, 0, MHI - MLO - 1)] * inr
        w0, w1 = WIN[e]
        old = g[gi_, gj_]
        new = np.clip(old + dl * 255.0 / (w1 - w0), 0, 255)
        return new - old

    def patch_delta(dg, e, vmask):
        """Delta of patch means (cm^-1) from grey deltas on glyph px."""
        w0, w1 = WIN[e]
        col = (dg.mean(1) * (w1 - w0) / 255.0) * vmask[gi_, gj_]
        acc = np.zeros((6, 6))
        ii, jj = gi_ // PS, gj_ // PS
        ok = (ii < 6) & (jj < 6)
        np.add.at(acc, (ii[ok], jj[ok]), col[ok])
        n = np.maximum(vmask[:6 * PS, :6 * PS].reshape(6, PS, 6, PS).sum((1, 3)), 1)
        return acc / n

    for name in MAT:
        for t in THK:
            for variant in ("paganin", "paganin_gain137", "absorption", "paganin_residual_shift", "paganin_misregistered"):
                if variant == "paganin_misregistered" and t != 10:
                    continue
                ab = variant == "absorption"
                t78, t137 = RESP[(name, t, "78", ab)], RESP[(name, t, "137", ab)]
                if variant == "paganin_gain137":
                    t137 = t137 * G137
                st137 = start + (sh_px if variant == "paganin_residual_shift" else 0)
                if variant == "paganin_misregistered":
                    d78 = patch_delta(inject(g78, "78", t78, start), "78", validm)
                    d137 = patch_delta(inject(g137m, "137", t137, start), "137", validm)
                    n78, n137, use = m78 + d78, m137 + d137, fvm
                else:
                    d78 = patch_delta(inject(g78, "78", t78, start), "78", valid)
                    d137 = patch_delta(inject(g137, "137", t137, st137), "137", valid)
                    n78, n137, use = c78 + d78, c137 + d137, fv
                h = hot(n78, n137)
                zz = zstat(n78, n137)
                sel = INJ & (use >= 0.5)
                inj_rows.append({"site": s["id"], "class": name, "t_um": t, "variant": variant,
                                 "n_inj": int(sel.sum()), "n_hot": int((h & sel).sum()),
                                 "z_mean": float(zz[sel].mean()) if sel.any() else None,
                                 "dC78_mean": float(d78[sel].mean()) if sel.any() else None,
                                 "dC137_mean": float(d137[sel].mean()) if sel.any() else None})
    rec["sites"].append({"id": s["id"], "frac_valid": float(valid.mean()), "no_plus_surface_frac": float(np.isnan(sp).mean()),
                         "labels": LAB["sites"].get(s["id"])})
    log("held site", s["id"], round(time.time() - t0))

# ---------------- summaries
pt = [p for p in rec["patch"] if p["fv"] >= 0.5]
un = [p for p in pt if not p["injected_patch"]] + [p for p in pt if p["injected_patch"]]  # uninjected profiles = all
hotf = lambda p, zk="z", ck="C78": abs(p[zk]) > T and p[ck] >= ONT
fpr = float(np.mean([hotf(p) for p in pt]))
fpr15 = float(np.mean([abs(p["z15"]) > T and p["C78"] >= ONT for p in pt]))
ptm = [p for p in rec["patch"] if p["fvm"] >= 0.5]
fpr_m = float(np.mean([hotf(p, "zm", "C78m") for p in ptm]))
sites_ids = sorted({p["site"] for p in pt})


def auc_boot(key, lab_key="label"):
    pos = [p[key] for p in pt if p[lab_key] == 1]
    neg = [p[key] for p in pt if p[lab_key] == -1]
    a = auc(pos, neg)
    bs = []
    by = {sid: [p for p in pt if p["site"] == sid] for sid in sites_ids}
    for _ in range(2000):
        ss = rng_b.choice(sites_ids, len(sites_ids))
        pp = [p for sid in ss for p in by[sid]]
        x = auc([p[key] for p in pp if p[lab_key] == 1], [p[key] for p in pp if p[lab_key] == -1])
        if x is not None:
            bs.append(x)
    return {"auc": a, "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))] if bs else None,
            "n_ink": len(pos), "n_blank": len(neg), "n_boot": len(bs)}


va = {"a_known_text_z": auc_boot("z"), "a_known_text_z15": auc_boot("z15"),
      "a_hotspot_rate_ink": float(np.mean([hotf(p) for p in pt if p["label"] == 1])) if any(p["label"] == 1 for p in pt) else None,
      "a_hotspot_rate_blank": float(np.mean([hotf(p) for p in pt if p["label"] == -1])) if any(p["label"] == -1 for p in pt) else None,
      "a_mean_z_ink": float(np.mean([p["z"] for p in pt if p["label"] == 1])) if any(p["label"] == 1 for p in pt) else None,
      "a_mean_z_blank": float(np.mean([p["z"] for p in pt if p["label"] == -1])) if any(p["label"] == -1 for p in pt) else None,
      "c1_rot90_labels_z": auc_boot("z", "label_rot90"),
      "c2_misregistered_known_text_z": None, "c2_misregistered_fpr": fpr_m,
      "false_positive_rate_heldout": fpr, "false_positive_rate_heldout_15um": fpr15, "n_heldout_patches": len(pt)}
ptm_lab = [p for p in ptm]
pos = [p["zm"] for p in ptm if p["label"] == 1]
neg = [p["zm"] for p in ptm if p["label"] == -1]
va["c2_misregistered_known_text_z"] = auc(pos, neg)
sd = np.concatenate(surf) if surf else np.zeros(0)
surface = {"n": int(len(sd)), "median_abs_um": float(np.median(np.abs(sd))), "p90_abs_um": float(np.percentile(np.abs(sd), 90)),
           "signed_median_um": float(np.median(sd)), "goal_lt_5um_met": bool(np.median(np.abs(sd)) < 5)}
summ = {}
for r in inj_rows:
    key = f"{r['class']}|{r['t_um']}|{r['variant']}"
    a = summ.setdefault(key, {"n_inj": 0, "n_hot": 0, "z": [], "sites": 0})
    a["n_inj"] += r["n_inj"]
    a["n_hot"] += r["n_hot"]
    a["sites"] += 1
    if r["z_mean"] is not None:
        a["z"].append(r["z_mean"])
for key, a in summ.items():
    a["recovery"] = a["n_hot"] / a["n_inj"] if a["n_inj"] else None
    a["detectable_ge_0.8"] = bool(a["recovery"] is not None and a["recovery"] >= 0.8)
    a["z_mean_over_sites"] = float(np.mean(a["z"])) if a["z"] else None
    del a["z"]
out = {"provenance": D.PROV, "serves": "PROTOCOL.md B2 (surface residual) and B4 (HELD-OUT only; fit.json unchanged)",
       "fit_json_sha256": D.sha(open(os.path.join(OUT, "fit.json"), "rb").read()),
       "colourant_crosscheck_max_rel": xmax, "colourant_crosscheck": XCHECK,
       "layer_props_mu_delta": {n: {e: {"mu_cm-1": v[e][0], "delta": v[e][1], "R_mu137_mu78": v["137"][0] / v["78"][0]}
                                    for e in v} for n, v in MAT.items()},
       "forward_model_self_test_integral_over_mu_t": self_test,
       "g137_gain_amendment_B1": G137, "glyph": {"injected_patches_per_site": int(INJ.sum()), "rule": ">= 80 % of patch inside '+' (0.4 mm bars, 1.0 mm long)"},
       "sheet_surface_residual": surface, "validation": va, "injection": summ,
       "per_site": rec["sites"], "injection_rows": inj_rows,
       "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump(out, open(os.path.join(OUT, "validation.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
json.dump(rec["patch"], open(os.path.join(OUT, "heldout_patches.json"), "w"))
log(json.dumps({"surface": surface, "validation": va}, default=str))
for key, a in sorted(summ.items()):
    if key.endswith("|paganin"):
        log(key, a)
