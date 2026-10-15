#!/usr/bin/env python
"""RULES R-ROWS: does a map carry the periodic row structure that written text has?

Rule 5.5 flags on LEVELS, and its levels were validated on w028 — a scroll inside the 9 um model's training corpus.
On an unseen scroll a genuine inked unit may sit below those levels while still being organised in rows, because line
spacing is a property of the scribe and not of the model's confidence. Rule 5.5's own row statistic cannot see that:
it is computed only inside an already-flagged cluster. This looks everywhere.

Statistic: on-sheet mean removed, zeros outside the mask, 2-D autocorrelation by FFT (normalised to 1.0 at zero lag
and corrected for the mask's own overlap so the mask shape does not create a peak). For each direction theta, the
largest autocorrelation value at a lag inside [min_mm, max_mm]. Reported: the maximum over theta, the theta and the
pitch achieving it. Text gives a ridge perpendicular to its lines; fibre texture and blob noise do not.

usage: row_power.py MAP.tif --mask MASK.png --um 9.362 [--min-mm 2] [--max-mm 4] [--region REGION.png] [--out JSON]
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def row_power(mapping, mask, um, min_mm=2.0, max_mm=4.0, n_theta=180, max_px=1600):
    """Peak autocorrelation at a 2-4 mm lag, maximised over direction. Returns a JSON-ready dict."""
    m = np.asarray(mapping, np.float64)
    k = np.asarray(mask, bool)
    if k.sum() < 1000:
        return dict(n_onsheet=int(k.sum()), peak=None, note="fewer than 1000 on-sheet pixels")
    # work at a bounded resolution: the 2-4 mm band is hundreds of microns per sample even after decimation
    step = max(1, int(np.ceil(max(m.shape) / max_px)))
    m, k = m[::step, ::step], k[::step, ::step]
    px_mm = um * step / 1000.0                      # mm per sample after decimation
    lo, hi = min_mm / px_mm, max_mm / px_mm         # lag range in samples
    if hi < 2 or min(m.shape) < 2 * hi:
        return dict(n_onsheet=int(k.sum()), peak=None, note="map too small for the 2-4 mm band after decimation")
    x = np.where(k, m - m[k].mean(), 0.0)
    # autocorrelation of the signal and of the mask, so the mask's own shape is divided out
    F = np.fft.rfft2(x, s=(2 * x.shape[0], 2 * x.shape[1]))
    G = np.fft.rfft2(k.astype(np.float64), s=(2 * x.shape[0], 2 * x.shape[1]))
    ac = np.fft.fftshift(np.fft.irfft2(F * np.conj(F)))
    n = np.fft.fftshift(np.fft.irfft2(G * np.conj(G)))
    c = (ac.shape[0] // 2, ac.shape[1] // 2)
    # The mask-overlap count collapses at large lags, and dividing by it there sends the ratio far above 1.0 (the
    # first run gave 26.6, impossible for a normalised autocorrelation). Evaluate only lags whose overlap is at least
    # 30 % of the zero-lag overlap, and normalise by the zero-lag value AFTER that correction.
    nmax = n[c]
    valid = n >= 0.30 * nmax
    ac = np.where(valid, ac / np.maximum(n, 1.0), np.nan)
    ac = ac / ac[c]                                  # 1.0 at zero lag
    best = dict(peak=None)
    # a full profile per direction, so a genuine local maximum can be told from a monotonic trend: the declared
    # statistic is "the first autocorrelation PEAK at a 2-4 mm lag", not the largest value in the band
    prof_lags = np.arange(2, int(min(c) - 2))
    for t in np.linspace(0, np.pi, n_theta, endpoint=False):
        dy, dx = np.sin(t), np.cos(t)
        yy = np.rint(c[0] + prof_lags * dy).astype(int)
        xx = np.rint(c[1] + prof_lags * dx).astype(int)
        v = ac[yy, xx]
        ok = np.isfinite(v)
        if ok.sum() < 8:
            continue
        # local maxima strictly inside the profile, then keep those whose lag falls in the band
        interior = np.zeros_like(v, bool)
        interior[1:-1] = ok[1:-1] & ok[:-2] & ok[2:] & (v[1:-1] > v[:-2]) & (v[1:-1] > v[2:])
        inband = interior & (prof_lags >= lo) & (prof_lags <= hi)
        if not inband.any():
            continue
        i = int(np.argmax(np.where(inband, v, -np.inf)))
        if best["peak"] is None or v[i] > best["peak"]:
            best = dict(peak=float(v[i]), theta_deg=round(float(np.degrees(t)), 1),
                        pitch_mm=round(float(prof_lags[i] * px_mm), 3))
    if best["peak"] is None:
        return dict(n_onsheet=int(k.sum()), peak=None, um=um, decimation=step, band_mm=[min_mm, max_mm],
                    note="no autocorrelation local maximum inside the 2-4 mm band in any direction")
    best.update(n_onsheet=int(k.sum()), um=um, decimation=step, band_mm=[min_mm, max_mm],
                peak=round(best["peak"], 5))
    return best


def main(argv=None):
    import tifffile
    from PIL import Image
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map"); ap.add_argument("--mask", required=True); ap.add_argument("--um", type=float, required=True)
    ap.add_argument("--min-mm", type=float, default=2.0); ap.add_argument("--max-mm", type=float, default=4.0)
    ap.add_argument("--region", help="further restrict to this 0/255 PNG (e.g. labelled text or labelled blank)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    m = tifffile.imread(a.map).astype(np.float64) / 255.0
    k = np.array(Image.open(a.mask).convert("L")) > 0
    if a.region:
        k = k & (np.array(Image.open(a.region).convert("L")) > 0)
    r = row_power(m, k, a.um, a.min_mm, a.max_mm)
    r["map"] = os.path.abspath(a.map)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(r, open(a.out, "w"), indent=1)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
