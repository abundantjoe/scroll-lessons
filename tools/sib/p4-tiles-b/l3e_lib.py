"""P4-L3 at 1.129 um (RULES.md DECL-P4-12-A4, method of DECL-P4-12-A3): depth calibration.

Provenance: Project HERCULES | owner the owner | [id removed]

Pure functions, no I/O. calibrate() takes per-slice voxel counts and returns the verdict.
Rule (A3 item 1): f(o) = fraction of in-slice voxels above T_hi; d* = the offset of the largest
f(o) - median_o f(o) over ALL offsets; PASS only if that offset lies within +-100 um and its
excess is >= 3 robust SD (1.4826 x MAD of f over offsets). Otherwise STOP. MAD = 0 -> STOP
(the robust SD is undefined, so no peak can be certified).
"""
import numpy as np

MAD_K = 1.4826


def slice_counts(chunk, mask, t_hi):
    """chunk: (n_slices, h, w) uint8; mask: (h, w) bool. Returns (n_hi, n_pos, n_all) per slice,
    counting only voxels at mask pixels; n_pos counts voxels > 0, n_hi voxels > t_hi."""
    v = chunk[:, mask]
    return (v > t_hi).sum(1).astype(np.int64), (v > 0).sum(1).astype(np.int64), np.full(v.shape[0], v.shape[1], np.int64)


def calibrate(n_hi, n_den, step_um, centre, window_um=100.0, z_min=3.0):
    n_hi = np.asarray(n_hi, np.float64)
    n_den = np.asarray(n_den, np.float64)
    k = np.arange(n_hi.size)
    o = (k - centre) * step_um
    ok = n_den > 0
    f = np.full(n_hi.size, np.nan)
    f[ok] = n_hi[ok] / n_den[ok]
    fv = f[ok]
    med = float(np.median(fv))
    mad = float(np.median(np.abs(fv - med)))
    rsd = MAD_K * mad
    exc = f - med
    kg = int(np.nanargmax(exc))
    inwin = ok & (np.abs(o) <= window_um)

    def z(kk):
        return float(exc[kk] / rsd) if rsd > 0 else (float("inf") if exc[kk] > 0 else 0.0)

    def side(sel):
        sel = sel & inwin
        if not sel.any():
            return None
        kk = int(np.nanargmax(np.where(sel, exc, -np.inf)))
        return {"slice": kk, "offset_um": float(o[kk]), "f": float(f[kk]), "excess": float(exc[kk]), "z": z(kk)}

    reasons = []
    if rsd <= 0:
        reasons.append("MAD = 0: robust SD undefined")
    if abs(o[kg]) > window_um:
        reasons.append("global max of f - median lies outside +-%g um" % window_um)
    if rsd > 0 and z(kg) < z_min:
        reasons.append("peak excess %.3f robust SD < %g" % (z(kg), z_min))
    verdict = "PASS" if not reasons else "STOP"
    # diagnostic (not the declared d*): centroid of the contiguous run of offsets around the global
    # peak whose excess is >= half the peak excess; resolves flat-topped layers the argmax cannot
    lo_k = hi_k = kg
    half = exc[kg] / 2.0
    while lo_k - 1 >= 0 and ok[lo_k - 1] and exc[lo_k - 1] >= half:
        lo_k -= 1
    while hi_k + 1 < n_hi.size and ok[hi_k + 1] and exc[hi_k + 1] >= half:
        hi_k += 1
    run = np.arange(lo_k, hi_k + 1)
    w = exc[run]
    centroid = float((o[run] * w).sum() / w.sum()) if w.sum() > 0 else float(o[kg])
    return {
        "verdict": verdict, "reasons": reasons,
        "d_star_um": float(o[kg]) if verdict == "PASS" else None,
        "global_peak": {"slice": kg, "offset_um": float(o[kg]), "f": float(f[kg]), "excess": float(exc[kg]), "z": z(kg)},
        "halfmax_centroid_um": centroid, "halfmax_width_um": float((hi_k - lo_k + 1) * step_um),
        "median_f": med, "mad_f": mad, "robust_sd_f": rsd,
        "side_negative": side(o < 0), "side_positive": side(o > 0), "side_zero": side(o == 0),
        "profile": [{"slice": int(kk), "offset_um": float(o[kk]), "f": (None if np.isnan(f[kk]) else float(f[kk]))} for kk in k],
        "rule": "d* = argmax_o (f(o) - median f); PASS iff |d*| <= %g um and excess >= %g x 1.4826 MAD" % (window_um, z_min),
    }


def slab_slices(d_star_um, step_um, centre, n_slices, half_um=10.0):
    """Slices whose offset lies within [d* - half, d* + half]."""
    o = (np.arange(n_slices) - centre) * step_um
    return [int(k) for k in np.nonzero(np.abs(o - d_star_um) <= half_um + 1e-9)[0]]
