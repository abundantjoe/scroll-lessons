"""DECL-P4-13 P4-M item 1: analysis of 1 mm column profiles (numbers only).

Provenance: Project HERCULES | owner the owner | [id removed]
Input: npz files from col_profile.py (S = channel sums, N = mesh-valid pixel counts, per 1 mm row-bin x col-bin).
Tile row r covers canvas rows [r*T, (r+1)*T) (T = 20 mm), so row-bins [20r, 20r+20); same for columns.

Outputs per channel and strip:
- column profile per 1 mm bin: mean over mesh-valid px (sum/count) in text rows r0-r5 and in r0-r1, the sums, and
  the mesh-valid fraction of the bin (count / (px_per_mm^2 x rows in band));
- pitch validation (declared): on the known-text span, the r0-r5 mean profile, linearly detrended, Hann-windowed,
  zero-padded x16 periodogram; the peak between periods 50 and 120 mm; SNR = peak power / median power over
  periods 10-200 mm outside +-2 native frequency bins of the peak; plus the autocorrelation peak lag in 50-120 mm.
  Pass = an interior local maximum of the periodogram inside 50-120 mm with SNR >= 3 (see bar_note).
- intercolumn positions: local minima of the 5 mm boxcar-smoothed r0-r5 profile, at least 0.6 x pitch apart, with a
  per-row-band spread (the same minimum located in each tile row r0..r5 separately, +-10 mm window): median and
  min/max of the six positions -> the +-mm figure.
- c11-c13 block extent (strip a only): the r0-r1 profile, background = mean and sd of the r0-r1 bins of c15-c19
  (blank per census); above-threshold = mean + 3 sd; the contiguous above-threshold run containing the maximum
  within c10.5-c14.5 gives the start/end bin (1 mm quantisation). Its vertical extent: the row-bin profile over
  the run's columns, background = the same row-bins over c15-c19, same 3-sd rule.
Usage: python profile_analyze.py <out.json> a_m1=<npz> [a_e2=<npz>] [b_m1=<npz>] ...
"""
import json, sys
import numpy as np

TILE = 20  # mm


def load(p):
    z = np.load(p)
    return z["S"], z["N"], float(z["px_per_mm"])


def band_profile(S, N, px, r0, r1):
    s = S[TILE * r0:TILE * r1].sum(0)
    n = N[TILE * r0:TILE * r1].sum(0)
    mean = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    vf = n / (px * px * TILE * (r1 - r0))
    return mean, s, vf


def pitch(prof, lo, hi):
    x = prof[lo:hi].astype(float)
    ok = np.isfinite(x)
    idx = np.arange(len(x))
    x = np.where(ok, x, np.interp(idx, idx[ok], x[ok]))
    x = x - np.polyval(np.polyfit(idx, x, 1), idx)
    w = np.hanning(len(x))
    Z = 16
    Fp = np.abs(np.fft.rfft(x * w, n=Z * len(x))) ** 2
    f = np.fft.rfftfreq(Z * len(x), d=1.0)  # cycles per mm
    per = np.where(f > 0, 1 / np.maximum(f, 1e-12), np.inf)
    band = (per >= 50) & (per <= 120)
    k = np.nonzero(band)[0][np.argmax(Fp[band])]
    interior = bool(band[k - 1] and band[k + 1] and Fp[k] >= Fp[k - 1] and Fp[k] >= Fp[k + 1])
    df = 1.0 / len(x)
    ref = (per >= 10) & (per <= 200) & (np.abs(f - f[k]) > 2 * df)
    snr = float(Fp[k] / np.median(Fp[ref]))
    # global max over 10-200 mm (is the 50-120 peak the dominant one?)
    g = (per >= 10) & (per <= 200)
    kg = np.nonzero(g)[0][np.argmax(Fp[g])]
    ac = np.array([np.corrcoef(x[:-L], x[L:])[0, 1] for L in range(1, len(x) // 2)])
    lags = np.arange(1, len(x) // 2)
    m = (lags >= 50) & (lags <= 120)
    la = int(lags[m][np.argmax(ac[m])]) if m.any() else None
    return {"span_bins": [lo, hi], "n_mm": len(x), "native_period_resolution_note": "periods near 80 mm are resolved to about +-%.0f mm (one native bin)" % (80 * 80 / len(x) / 2),
            "peak_period_mm_50_120": round(float(per[k]), 1), "snr": round(snr, 2),
            "dominant_period_mm_10_200": round(float(per[kg]), 1),
            "autocorr_peak_lag_mm_50_120": la, "autocorr_at_peak": round(float(ac[m].max()), 3) if m.any() else None,
            "peak_is_interior_local_max": bool(interior),
            "pass_declared_spectral_peak_50_120mm": bool(snr >= 3 and interior),
            "bar_note": "pass = an interior local maximum of the periodogram within 50-120 mm (not a band-edge value) with SNR >= 3; the interior condition was added after the E2 run showed a band-edge maximum, to match DECL-P4-13's wording 'a spectral peak between 5 and 12 cm' (tightening only)"}


def smooth(x, w=5):
    ok = np.isfinite(x)
    k = np.ones(w)
    s = np.convolve(np.where(ok, x, 0), k, "same")
    c = np.convolve(ok.astype(float), k, "same")
    return np.where(c > 0, s / np.maximum(c, 1), np.nan)


def minima(S, N, px, P, lo, hi):
    prof, _, _ = band_profile(S, N, px, 0, 6)
    sm = smooth(prof)
    cand = [i for i in range(max(lo, 3), min(hi, len(sm) - 3)) if np.isfinite(sm[i]) and sm[i] == np.nanmin(sm[max(i - int(0.3 * P), 0):i + int(0.3 * P) + 1])]
    out = []
    for i in cand:
        per_row = []
        for r in range(6):
            pr, _, _ = band_profile(S, N, px, r, r + 1)
            s = smooth(pr)
            a, b = max(i - 10, 0), min(i + 11, len(s))
            if np.isfinite(s[a:b]).sum() > 10:
                per_row.append(int(a + np.nanargmin(s[a:b])))
        out.append({"bin_mm": i, "tile_col": round(i / TILE, 2), "depth_vs_pm15mm_max": round(float(np.nanmax(sm[max(i - 15, 0):i + 16]) - sm[i]), 2),
                    "per_row_r0_r5_bins": per_row,
                    "per_row_median_mm": float(np.median(per_row)) if per_row else None,
                    "per_row_spread_mm": [int(min(per_row)), int(max(per_row))] if per_row else None})
    return out


def block(S, N, px):
    prof, _, vf = band_profile(S, N, px, 0, 2)
    bg = prof[15 * TILE:20 * TILE]
    bg = bg[np.isfinite(bg)]
    mu, sd = float(bg.mean()), float(bg.std())
    thr = mu + 3 * sd
    lo, hi = int(10.5 * TILE), int(14.5 * TILE)
    seg = prof[lo:hi]
    k = lo + int(np.nanargmax(seg))
    a = k
    while a - 1 >= lo and np.isfinite(prof[a - 1]) and prof[a - 1] > thr:
        a -= 1
    b = k
    while b + 1 < hi and np.isfinite(prof[b + 1]) and prof[b + 1] > thr:
        b += 1
    # all above-threshold bins in window (runs)
    above = np.nonzero(np.nan_to_num(seg, nan=-1) > thr)[0] + lo
    runs = []
    for i in above:
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = int(i)
        else:
            runs.append([int(i), int(i)])
    # vertical extent over the block's columns
    cols = slice(a, b + 1)
    rs = S[:, cols].sum(1)
    rn = N[:, cols].sum(1)
    rprof = np.where(rn > 0, rs / np.maximum(rn, 1), np.nan)
    bgs = S[:, 15 * TILE:20 * TILE].sum(1)
    bgn = N[:, 15 * TILE:20 * TILE].sum(1)
    bgp = np.where(bgn > 0, bgs / np.maximum(bgn, 1), np.nan)
    d = rprof - bgp
    dd = d[np.isfinite(d)]
    # noise of the difference from rows r4-r7 (blank in c11-c13 per census)
    nz = d[4 * TILE:8 * TILE]
    nz = nz[np.isfinite(nz)]
    vthr = float(nz.mean() + 3 * nz.std())
    rows_above = np.nonzero(np.nan_to_num(d, nan=-1e9) > vthr)[0]
    vruns = []
    for i in rows_above:
        if vruns and i == vruns[-1][1] + 1:
            vruns[-1][1] = int(i)
        else:
            vruns.append([int(i), int(i)])
    return {"background_c15_c19_r0_r1": {"mean": round(mu, 3), "sd": round(sd, 3), "thr_mean_plus_3sd": round(thr, 3)},
            "peak_bin_mm": k, "peak_value": round(float(prof[k]), 3),
            "run_containing_peak_mm": [a, b], "run_tile_cols": [round(a / TILE, 2), round((b + 1) / TILE, 2)], "run_width_mm": b - a + 1,
            "all_runs_c10p5_c14p5_mm": runs,
            "vertical": {"diff_vs_c15_c19_noise_thr": round(vthr, 3), "row_bins_above_runs_mm_from_canvas_top": vruns,
                         "note": "row-bin 0 = canvas top (high z); r0 = bins 0-19, r1 = 20-39"},
            "profile_r0_r1_bins_200_300": [None if not np.isfinite(x) else round(float(x), 2) for x in prof[200:300]],
            "valid_frac_r0_r1_bins_200_300": [round(float(x), 3) for x in vf[200:300]]}


def main(out, *specs):
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "declaration": "RULES.md DECL-P4-13 P4-M item 1", "method": __doc__.split("Outputs")[1].split("Usage")[0].strip(), "channels": {}}
    for sp in specs:
        name, path = sp.split("=")
        S, N, px = load(path)
        strip, ch = name.split("_")
        ncol = S.shape[1]
        m05, s05, vf05 = band_profile(S, N, px, 0, 6)
        m01, s01, vf01 = band_profile(S, N, px, 0, 2)
        r = {"px_per_mm": px, "n_col_bins": int(ncol),
             "profile_r0_r5": {"mean": [None if not np.isfinite(x) else round(float(x), 3) for x in m05],
                               "sum": [round(float(x), 1) for x in s05], "valid_frac": [round(float(x), 3) for x in vf05]},
             "profile_r0_r1": {"mean": [None if not np.isfinite(x) else round(float(x), 3) for x in m01],
                               "valid_frac": [round(float(x), 3) for x in vf01]}}
        if strip == "a":
            r["pitch_c0_c9"] = pitch(m05, 0, 10 * TILE)
            r["pitch_c0_c13"] = pitch(m05, 0, 14 * TILE)
            P = r["pitch_c0_c9"]["peak_period_mm_50_120"]
            r["intercolumn_minima_c0_c19"] = minima(S, N, px, P, 0, 20 * TILE)
            r["block_c11_c13"] = block(S, N, px)
        else:
            r["pitch_c0_c20"] = pitch(m05, 0, min(21 * TILE, ncol))
            P = r["pitch_c0_c20"]["peak_period_mm_50_120"]
            r["intercolumn_minima"] = minima(S, N, px, P, 0, ncol)
        res["channels"][name] = r
        print(name, json.dumps({k: v for k, v in r.items() if k.startswith("pitch")}))
        for m in r.get("intercolumn_minima_c0_c19", r.get("intercolumn_minima", [])):
            print("  min", m["bin_mm"], m["tile_col"], m["depth_vs_pm15mm_max"], m["per_row_median_mm"], m["per_row_spread_mm"])
        if "block_c11_c13" in r:
            b = r["block_c11_c13"]
            print("  block", {k: b[k] for k in ("background_c15_c19_r0_r1", "peak_bin_mm", "run_containing_peak_mm", "run_tile_cols", "all_runs_c10p5_c14p5_mm")}, b["vertical"]["row_bins_above_runs_mm_from_canvas_top"])
    json.dump(res, open(out, "w"))


if __name__ == "__main__":
    main(*sys.argv[1:])
