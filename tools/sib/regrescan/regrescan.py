# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task regrescan: CT-to-CT affine registration of two eligible 9.362 um volumes
(PHerc1203, PHerc0846A) onto their official 2.403 um rescans (method C6).

CT ONLY. No ink model is run on any volume here; no image is written or viewed.

Model (c6 conventions, (x, y, z) points, 9 um voxel units):
    q_can = F * (p + t(p) - z0 e_z),  t(p) = M (p - Pm) + b,  q_raw = G q_can + offset
with F = voxel_9 / voxel_r from the two metadata.json files.

Stages (each checkpointed under /work/rr/<scroll>/, compact copies under
logs/sib/regrescan/<scroll>/):
  meta    - bucket paths, metadata sha256, voxel sizes, F
  coarse  - stream 9 um level 4 and rescan level 5 (~150 um); flip / mirror /
            in-plane rotation (remount) search by whole-volume 3-D NCC; z-band by
            whole-slice 3-D NCC profile; coarse local-shift affine (tilt)
  patches - 24 fit + 16 NEW check patch centres (written before any level-0 read)
  mid     - 9 um level 1 vs rescan level 2 (F/2): per-patch 3-D phase correlation,
            affine fit (initialises level 0)
  fine    - level 0: 48x256x256 9 um blocks vs area-downsampled rescan; phase
            correlation at the 24 fit patches -> affine; 16 NEW check patches:
            r, residual shift; control shifted by half the local sheet pitch
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import fft as sfft
from scipy import ndimage as ndi

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from hercules.registration import c6  # noqa: E402

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BUCKET = "vesuvius-challenge-open-data"
PAIRS = {
    "PHerc1203": {
        "v9": "PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr",
        "vr": "PHerc1203/volumes/20260319130212-2.403um-0.2m-77keV-masked.zarr",
        "archive": {"z_band": [7936, 11824], "ncc": 0.984, "heldout_median_r": 0.964},
    },
    "PHerc0846A": {
        "v9": "PHerc0846A/volumes/20250728152254-9.362um-1.2m-113keV-masked.zarr",
        "vr": "PHerc0846A/volumes/20260319102732-2.403um-0.2m-77keV-masked.zarr",
        "archive": {"z_band": [1856, 5744], "ncc": 0.945, "heldout_median_r": 0.946,
                    "tilt_deg": [0.26, 0.12]},
    },
}
WORK = Path(os.environ.get("RR_WORK", "/work/rr"))
LOGS = REPO / "logs" / "sib" / "regrescan"
BLOCK = (48, 256, 256)  # zyx, 9 um voxels
N_FIT, N_CHECK = 24, 16
SEED = 20260925
# control criterion, fixed before any level-0 measurement (see REPORT.md):
CTRL_MIN_MEDIAN_DROP = 0.20      # median over check patches of r - r_ctrl
CTRL_MIN_FRAC_LOWER = 15 / 16    # fraction of check patches with r_ctrl < r


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def say(*a):
    print(f"[{utc()}]", *a, flush=True)


def jdump(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(c6._jsonify(obj), indent=1)
    path.write_text(txt + "\n")
    return hashlib.sha256((txt + "\n").encode()).hexdigest()


def jload(path):
    return json.loads(Path(path).read_text())


def open_level(path, level):
    import zarr
    store = zarr.storage.FSStore(f"s3://{BUCKET}/{path}", mode="r", anon=True)
    return zarr.open_group(store, mode="r")[str(level)]


class ZReader:
    """c6-style box reader over a zarr level (NaN outside the volume)."""

    def __init__(self, arr):
        self.arr = arr
        self.shape = tuple(int(s) for s in arr.shape)
        self.inner = c6.ArrayReader(arr)
        self.bytes = 0
        self.lock = threading.Lock()

    def __call__(self, lo, hi):
        out = self.inner(lo, hi)
        with self.lock:
            self.bytes += out.size
        return out


class BlockReader:
    """Reader over an in-memory raw block placed at ``lo`` in a volume of ``shape``."""

    def __init__(self, block, lo, shape):
        self.block = block
        self.lo = np.asarray(lo, int)
        self.shape = tuple(int(s) for s in shape)
        self.inner = c6.ArrayReader(block)

    def __call__(self, lo, hi):
        lo = np.asarray(lo, int) - self.lo
        hi = np.asarray(hi, int) - self.lo
        if np.any(lo < 0) or np.any(hi > np.asarray(self.block.shape)):
            raise ValueError(f"box {lo}..{hi} outside cached block {self.block.shape}")
        return self.inner(lo, hi)


def level_transform(tr: c6.C6Transform, k9: int, kr: int) -> c6.C6Transform:
    """Level-0 C6 transform -> equivalent transform between 9 um level k9 and
    rescan level kr (pyramid voxel i of level k centred at level-0 2^k i + (2^k-1)/2)."""
    s9, sr = 2.0 ** k9, 2.0 ** kr
    c9, cr = (s9 - 1) / 2.0, (sr - 1) / 2.0
    F = tr.F * s9 / sr
    Pm = (tr.Pm - c9) / s9
    b = (tr.b + c9) / s9 - cr / (tr.F * s9)
    raw = None if tr.raw_shape is None else tuple(int(math.ceil(n / sr)) for n in tr.raw_shape)
    return c6.C6Transform(F, tr.z0 / s9, tr.M.copy(), b, Pm, tr.orientation, raw)


def level0_transform(trk: c6.C6Transform, F0: float, k9: int, kr: int, raw0) -> c6.C6Transform:
    """Inverse of ``level_transform``."""
    s9, sr = 2.0 ** k9, 2.0 ** kr
    c9, cr = (s9 - 1) / 2.0, (sr - 1) / 2.0
    Pm = trk.Pm * s9 + c9
    b = trk.b * s9 - c9 + cr / F0
    return c6.C6Transform(F0, trk.z0 * s9, trk.M.copy(), b, Pm, trk.orientation, tuple(raw0))


def tr_json(tr: c6.C6Transform):
    return {"F": tr.F, "z0": tr.z0, "M": tr.M, "b": tr.b, "Pm": tr.Pm,
            "orientation": tr.orientation.to_json(tr.raw_shape)}


def rot_z(theta_deg):
    """Rotation about z by theta in (x, y, z)."""
    t = math.radians(theta_deg)
    return np.array([[math.cos(t), -math.sin(t), 0.0], [math.sin(t), math.cos(t), 0.0],
                     [0.0, 0.0, 1.0]])


# --------------------------------------------------------------------------
# stage: meta
# --------------------------------------------------------------------------
def stage_meta(scroll):
    import s3fs
    fs = s3fs.S3FileSystem(anon=True)
    pr = PAIRS[scroll]
    out = {"scroll": scroll, "utc": utc(), "bucket": f"s3://{BUCKET}/"}
    for key in ("v9", "vr"):
        p = pr[key]
        listing = sorted(x.split("/")[-1] for x in fs.ls(f"{BUCKET}/{p}"))
        mj = fs.cat(f"{BUCKET}/{p}/metadata.json")
        md = json.loads(mj)
        acq = md["scan"]["tomo"]["acquisition"]
        vox_mm = float(acq["detector"]["samplePixelSize"])
        levels = {}
        for lv in range(6):
            za = fs.cat(f"{BUCKET}/{p}/{lv}/.zarray")
            zj = json.loads(za)
            levels[str(lv)] = {"shape": zj["shape"], "chunks": zj["chunks"], "dtype": zj["dtype"],
                               "compressor": zj["compressor"],
                               "zarray_sha256": hashlib.sha256(za).hexdigest()}
        za = fs.cat(f"{BUCKET}/{p}/.zattrs")
        out[key] = {
            "path": f"s3://{BUCKET}/{p}/", "listing": listing,
            "metadata_json_sha256": hashlib.sha256(mj).hexdigest(),
            "metadata_json_bytes": len(mj),
            "zattrs_sha256": hashlib.sha256(za).hexdigest(),
            "voxel_um": vox_mm * 1000.0,
            "voxel_field": "scan.tomo.acquisition.detector.samplePixelSize (mm)",
            "stage_z_start_mm": acq.get("z_start"), "stage_z_end_mm": acq.get("z_end"),
            "detector_roi": acq["detector"].get("roi_size"),
            "zarr_export": md.get("zarr_export"),
            "rotation_axis_position": md["scan"]["tomo"].get("processing", {})
                .get("reconstruction", {}).get("rotation_axis_position"),
            "levels": levels,
        }
    out["F"] = c6.scale_factor(out["v9"]["voxel_um"], out["vr"]["voxel_um"])
    # stage-position prior for z0 (hint only; the fit does not use it)
    try:
        roi = {k: out[k]["detector_roi"] for k in ("v9", "vr")}
        roi = {k: json.loads(v) if isinstance(v, str) else v for k, v in roi.items()}
        h9 = roi["v9"][1] * out["v9"]["voxel_um"] / 1000.0
        hr = roi["vr"][1] * out["vr"]["voxel_um"] / 1000.0
        d_mm = ((out["vr"]["stage_z_start_mm"] - hr / 2) - (out["v9"]["stage_z_start_mm"] - h9 / 2))
        out["z0_stage_prior_9um_slices"] = d_mm / (out["v9"]["voxel_um"] / 1000.0)
        out["z0_stage_prior_note"] = ("(rescan z_start - h_r/2) - (9um z_start - h_9/2) in mm / voxel_9; "
                                      "ignores zarr_export z crops and remount; hint only")
    except Exception as e:  # noqa: BLE001
        out["z0_stage_prior_error"] = repr(e)
    jdump(out, WORK / scroll / "meta.json")
    jdump(out, LOGS / scroll / "meta.json")
    say(scroll, "F =", out["F"], "prior z0 ~", out.get("z0_stage_prior_9um_slices"))
    return out


# --------------------------------------------------------------------------
# stage: coarse (remount test, z-band, tilt)
# --------------------------------------------------------------------------
def fetch_level(scroll, key, level):
    f = WORK / scroll / f"{key}_L{level}.npy"
    if f.exists():
        return np.load(f, mmap_mode="r")
    arr = open_level(PAIRS[scroll][key], level)
    say("fetch", scroll, key, "level", level, arr.shape)
    t0 = time.time()
    out = np.empty(arr.shape, arr.dtype)
    step = 128
    for z in range(0, arr.shape[0], step):
        out[z:z + step] = arr[z:z + step]
    np.save(str(f) + ".tmp.npy", out)
    os.replace(str(f) + ".tmp.npy", f)
    say("fetched", f.name, f"{out.nbytes / 1e6:.0f} MB in {time.time() - t0:.0f} s")
    return np.load(f, mmap_mode="r")


_NCC_CACHE = {}


def _boxsum(X, tshape):
    c = X
    for ax in range(3):
        c = np.cumsum(c, axis=ax)
        pad = [(0, 0)] * 3
        pad[ax] = (1, 0)
        c = np.pad(c, pad)
        m = tshape[ax]
        c = np.take(c, np.arange(m, c.shape[ax]), axis=ax) - np.take(c, np.arange(0, c.shape[ax] - m), axis=ax)
    return c


def _ncc_map(A, T, workers=4, cache_key=None):
    """Normalised cross-correlation of template T (full, zyx) at every valid
    placement inside A (FFT; 'valid' mode). Returns array of shape A-T+1.
    With ``cache_key``, the FFT and local sums of A are reused across calls
    (same A and template shape)."""
    T = np.asarray(T, np.float64)
    n = T.size
    Tc = T - T.mean()
    tss = float((Tc ** 2).sum())
    key = None if cache_key is None else (cache_key, T.shape)
    if key is not None and key in _NCC_CACHE:
        FA, fshape, var, ashape = _NCC_CACHE[key]
    else:
        A = np.asarray(A, np.float64)
        ashape = A.shape
        shape = [a + t - 1 for a, t in zip(A.shape, T.shape)]
        fshape = [sfft.next_fast_len(s_, real=True) for s_ in shape]
        FA = sfft.rfftn(A, fshape, workers=workers)
        s1 = _boxsum(A, T.shape)
        s2 = _boxsum(A * A, T.shape)
        var = np.maximum(s2 - s1 * s1 / n, 0.0)
        if key is not None:
            _NCC_CACHE.clear()
            _NCC_CACHE[key] = (FA, fshape, var, ashape)
    FT = sfft.rfftn(Tc[::-1, ::-1, ::-1], fshape, workers=workers)
    num = sfft.irfftn(FA * FT, fshape, workers=workers)
    sl = tuple(slice(t - 1, a) for a, t in zip(ashape, T.shape))
    num = num[sl]
    den = np.sqrt(var * tss)
    return np.where(den > 1e-9 * max(den.max(), 1e-300), num / np.maximum(den, 1e-300), 0.0)


def _orient_template(R, zflip, mirror, theta):
    """Canonical-frame candidate of the coarse rescan: z flip, x mirror, then
    in-plane rotation by theta (deg, about the slice centre)."""
    X = R
    if zflip:
        X = X[::-1]
    if mirror:
        X = X[:, :, ::-1]
    X = np.ascontiguousarray(X, dtype=np.float32)
    if theta % 360:
        X = ndi.rotate(X, theta, axes=(2, 1), reshape=False, order=1, mode="constant", cval=0.0)
    return X


def _bin3(x, k):
    return c6._bin(np.asarray(x, np.float32), k)


def _crop(A, lo, shape):
    """A[lo:lo+shape] (zyx) with zeros (air) outside A."""
    lo = np.asarray(lo, int)
    shape = np.asarray(shape, int)
    out = np.zeros(tuple(shape), np.float32)
    src = tuple(slice(max(l, 0), min(l + s, n)) for l, s, n in zip(lo, shape, A.shape))
    if all(x.stop > x.start for x in src):
        dst = tuple(slice(x.start - l, x.stop - l) for x, l in zip(src, lo))
        out[dst] = A[src]
    return out


def _search(A, T, lo, hi, cache_key=None):
    """Best NCC placement of template T with its voxel 0 at A-coords in [lo, hi]
    (zyx, inclusive; zeros outside A). Returns (ncc, pos, ncc map)."""
    lo = np.asarray(lo, int)
    hi = np.asarray(hi, int)
    ck = None if cache_key is None else (cache_key, tuple(lo), tuple(hi))
    hit = ck is not None and ((ck, T.shape) in _NCC_CACHE)
    Ac = None if hit else _crop(A, lo, hi - lo + np.array(T.shape))
    m = _ncc_map(Ac, T, cache_key=ck)
    i = np.unravel_index(int(np.argmax(m)), m.shape)
    return float(m[i]), lo + np.array(i), m


def stage_coarse(scroll):
    meta = jload(WORK / scroll / "meta.json")
    F = float(meta["F"])
    A4 = np.asarray(fetch_level(scroll, "v9", 4), np.float32)
    R5 = fetch_level(scroll, "vr", 5)
    F45 = F * 16 / 32
    t0 = time.time()
    Rc = c6.downsample_area(np.asarray(R5), F45)  # rescan on the 9 um level-4 grid
    Rc = np.nan_to_num(Rc, nan=0.0).astype(np.float32)
    say("Rc", Rc.shape, f"{time.time() - t0:.1f}s")
    res = {"scroll": scroll, "utc": utc(), "F": F, "F45": F45, "A4_shape": A4.shape,
           "R5_shape": R5.shape, "Rc_shape": Rc.shape,
           "pyramid_convention": "level-k voxel i centred at level-0 2^k i + (2^k - 1)/2 (mean pooling)"}

    # --- 1. remount search at ~600 um (bin 4): z flip x x mirror x theta (2 deg), full xyz search
    k = 4
    Ab = _bin3(A4, k)
    Rb = _bin3(Rc, k)
    padxy = int(round(0.4 * Ab.shape[1]))
    lo = np.array([-Rb.shape[0] // 2, -padxy, -padxy])
    hi = np.array([Ab.shape[0] - Rb.shape[0] // 2, Ab.shape[1] - Rb.shape[1] + padxy,
                   Ab.shape[2] - Rb.shape[2] + padxy])
    rows = []
    t0 = time.time()
    for zflip in (False, True):
        for mirror in (False, True):
            for th in np.arange(0.0, 360.0, 2.0):
                T = _orient_template(Rb, zflip, mirror, th)
                v, pos, _ = _search(Ab, T, lo, hi, cache_key="bin4")
                rows.append({"zflip": zflip, "mirror": mirror, "theta": float(th),
                             "ncc": v, "pos_bin4": pos})
    say("remount search", len(rows), f"{time.time() - t0:.0f}s")
    rows.sort(key=lambda r: -r["ncc"])
    best = rows[0]

    def distinct(r):
        dth = abs((r["theta"] - best["theta"] + 180) % 360 - 180)
        return r["zflip"] != best["zflip"] or r["mirror"] != best["mirror"] or dth > 10
    runner = next((r for r in rows if distinct(r)), None)
    res["remount_600um"] = {
        "n_candidates": len(rows), "theta_step_deg": 2.0, "best": best, "runner_up_distinct": runner,
        "margin": best["ncc"] - (runner["ncc"] if runner else float("nan")), "top10": rows[:10],
        "per_flip_best": {f"zflip={zf},mirror={mi}": max(
            (r for r in rows if r["zflip"] == zf and r["mirror"] == mi), key=lambda r: r["ncc"])
            for zf in (False, True) for mi in (False, True)}}
    say("best", best, "runner", runner)

    # --- 2. refine theta at ~300 um (0.5 deg) and ~150 um (0.1 deg), local search
    zflip, mirror = best["zflip"], best["mirror"]
    theta = best["theta"]
    pos = np.array(best["pos_bin4"]) * 4  # level-4 coords of template voxel 0
    # (a 150 um NCC-map pass needs > 14 GB; the full affine M is fitted downstream)
    for ipass, (kk, span, step) in enumerate(((2, 3.0, 0.5), (2, 0.5, 0.1))):
        Ab = _bin3(A4, kk)
        Rb = _bin3(Rc, kk)
        pk = np.round(pos / kk).astype(int)
        mg = 4
        rr = []
        for th in np.arange(theta - span, theta + span + 1e-9, step):
            T = _orient_template(Rb, zflip, mirror, th)
            v, p, _ = _search(Ab, T, pk - mg, pk + mg, cache_key=f"bin{kk}p{ipass}")
            rr.append({"theta": float(th), "ncc": v, "pos": p * kk})
        bi = max(range(len(rr)), key=lambda j: rr[j]["ncc"])
        theta_b = rr[bi]["theta"]
        if 0 < bi < len(rr) - 1:
            cm, c0, cp = rr[bi - 1]["ncc"], rr[bi]["ncc"], rr[bi + 1]["ncc"]
            den = cm - 2 * c0 + cp
            if den < 0:
                theta_b += 0.5 * (cm - cp) / den * step
        theta = theta_b
        pos = np.array(rr[bi]["pos"])
        res[f"theta_refine_pass{ipass + 1}_bin{kk}"] = {"scan": rr, "theta": theta, "best_ncc": rr[bi]["ncc"]}
        say(f"theta refine bin{kk}: theta {theta:.3f} ncc {rr[bi]['ncc']:.4f} pos {pos}")

    # --- 3. z-band: whole-slice 3-D NCC at every z placement over the whole 9 um volume
    #        (~300 um, xy within +-4 of the best placement)
    Ab = _bin3(A4, 2)
    Rb = _bin3(Rc, 2)
    T = _orient_template(Rb, zflip, mirror, theta)
    pk = np.round(pos / 2).astype(int)
    lo = np.array([0, pk[1] - 4, pk[2] - 4])
    hi = np.array([Ab.shape[0] - T.shape[0], pk[1] + 4, pk[2] + 4])
    v, p2, m = _search(Ab, T, lo, hi)
    prof = m.reshape(m.shape[0], -1).max(1)
    iz = int(np.argmax(prof))
    far = [float(x) for j, x in enumerate(prof) if abs(j - iz) > 4]
    res["zband_300um"] = {
        "profile_max_ncc_per_z_bin2": prof, "z_bin2_offset": int(lo[0]), "best_z_bin2": int(p2[0]),
        "best_ncc": v, "second_best_ncc_gt4bins": max(far) if far else None,
        "fwhm_bins": int(np.sum(prof >= (prof.max() + np.median(prof)) / 2)),
        "best_z9_level0_of_rescan_top": float(p2[0] * 2 * 16)}
    say(f"z-band: z_bin2={p2[0]} ncc={v:.4f} second={max(far) if far else None}")

    # --- 4. level-0 transform from the coarse placement: try both rotation sign
    #        conventions and keep the one with the higher coarse local NCC
    T = _orient_template(Rc, zflip, mirror, theta)
    ori = c6.Orientation((0, 1, 2), (bool(zflip), False, bool(mirror)))
    raw0 = tuple(meta["vr"]["levels"]["0"]["shape"])
    Tc = (np.array(T.shape) - 1) / 2.0                  # template centre (rotation centre), zyx
    p4_c = pos.astype(float) + Tc                      # its level-4 9 um coords
    p0_c = 16 * p4_c + 7.5                             # level-0 9 um coords (zyx)
    o45 = (F45 - 1) / 2.0
    q5_raw = o45 + F45 * Tc                            # raw R5 coords (centre is flip-invariant)
    q0_raw = 32 * q5_raw + 15.5                        # raw level-0 rescan coords
    q0_can = ori.raw_to_can(q0_raw, raw0)              # canonical level-0 rescan coords (zyx)
    z0 = float(round(p0_c[0] - q0_can[0] / F))
    Pm = p0_c[::-1].copy()
    b = q0_can[::-1] / F - Pm + np.array([0.0, 0.0, z0])
    cands = {}
    for sgn in (+1, -1):
        M = rot_z(sgn * theta) - np.eye(3)
        tr0 = c6.C6Transform(F, z0, M, b, Pm, ori, raw0)
        tilt = coarse_tilt(A4, R5, tr0, meta)
        med = float(np.nanmedian([r["r"] if r["r"] is not None else np.nan for r in tilt["summary"]["rows"]]))
        cands[sgn] = (med, tr0, tilt)
        say(f"rotation sign {sgn:+d}: coarse local median r {med:.3f}, fit rms L4 {tilt['summary']['fit_rms_L4']}")
    sgn = max(cands, key=lambda s: cands[s][0])
    med, tr0, tilt = cands[sgn]
    res["initial_transform"] = tr_json(tr0)
    res["rotation_sign_test"] = {str(s): {"median_r": cands[s][0], "summary": cands[s][2]["summary"]}
                                 for s in cands}
    res["remount"] = {"zflip": bool(zflip), "x_mirror": bool(mirror), "theta_deg": float(theta),
                      "rotation_sign": sgn}
    res["band_initial"] = band_extents(tr0, meta)
    res["coarse_tilt"] = tilt["summary"]
    tr1 = c6.C6Transform.from_fit(tilt["transform"])
    res["coarse_transform"] = tr_json(tr1)
    res["band_coarse"] = band_extents(tr1, meta)
    jdump(res, WORK / scroll / "coarse.json")
    jdump(res, LOGS / scroll / "coarse.json")
    return res


def _rot_index(theta_deg):
    return rot_z(theta_deg)


def band_extents(tr: c6.C6Transform, meta):
    """9 um extents covered by the rescan array (its top and bottom planes over
    the inscribed disc and the centre column)."""
    raw = np.array(meta["vr"]["levels"]["0"]["shape"], float)  # zyx
    cy, cx = (raw[1] - 1) / 2, (raw[2] - 1) / 2
    rad = min(cy, cx)
    ang = np.linspace(0, 2 * np.pi, 72, endpoint=False)
    xy = np.vstack([[cx, cy], np.c_[cx + rad * np.cos(ang), cy + rad * np.sin(ang)]])
    top = c6.map_r_to_9(np.c_[xy, np.zeros(len(xy))], tr_json(tr), frame="raw")
    bot = c6.map_r_to_9(np.c_[xy, np.full(len(xy), raw[0] - 1)], tr_json(tr), frame="raw")
    zlo = np.minimum(top[:, 2], bot[:, 2])
    zhi = np.maximum(top[:, 2], bot[:, 2])
    return {"rescan_centre_column_z9": [float(zlo[0]), float(zhi[0])],
            "rescan_centre_xy9": ((top[0, :2] + bot[0, :2]) / 2).tolist(),
            "z9_range_any_column": [float(zlo.min()), float(zhi.max())],
            "z9_common_all_columns": [float(zlo.max()), float(zhi.min())],
            "rescan_disc_radius_9um_vox": float(rad / tr.F),
            "volume9_shape_zyx": meta["v9"]["levels"]["0"]["shape"]}


def coarse_tilt(A4, R5, tr0, meta):
    """Local shifts of 2 (z) x 3 x 3 sub-blocks at 150 um under tr0; affine fit."""
    trk = level_transform(tr0, 4, 5)
    trk.raw_shape = tuple(R5.shape)
    rr = c6.OrientedReader(c6.ArrayReader(np.asarray(R5)), R5.shape, trk.orientation)
    r9 = c6.ArrayReader(np.asarray(A4))
    band = band_extents(tr0, meta)
    z_lo, z_hi = band["rescan_centre_column_z9"]
    cxy = np.array(band["rescan_centre_xy9"])
    rad = band["rescan_disc_radius_9um_vox"]
    blk = np.array([48, 64, 64])  # level-4 voxels (7.2 x 9.6 x 9.6 mm)
    cents = []
    for fz in (0.3, 0.7):
        z = z_lo + fz * (z_hi - z_lo)
        for fy in (-0.45, 0.0, 0.45):
            for fx in (-0.45, 0.0, 0.45):
                p0 = np.array([cxy[0] + fx * rad, cxy[1] + fy * rad, z])
                cents.append((p0 - 7.5) / 16.0)
    rows = [c6._measure_patch(r9, rr, trk, c, blk, 10, True) for c in cents]
    C = np.array([r["centre"] for r in rows])
    T = np.array([r["t_meas"] for r in rows])
    ok = np.array([r["ok"] and np.all(np.isfinite(r["t_meas"])) and r["r"] > 0.3 for r in rows])
    Mk = trk.M
    if ok.sum() >= 6:
        af = c6.fit_affine(C[ok], T[ok], Pm=trk.Pm)
        # keep the rotation linearisation: new M = measured M (absolute)
        trk_new = c6.C6Transform(trk.F, trk.z0, af["M"], af["b"], trk.Pm, trk.orientation, trk.raw_shape)
    else:
        af = {"rms": float("nan"), "M": Mk, "b": trk.b}
        trk_new = trk
    tr1 = level0_transform(trk_new, tr0.F, 4, 5, tr0.raw_shape)
    return {"transform": tr_json(tr1),
            "summary": {"n_blocks": len(rows), "n_ok": int(ok.sum()), "block_L4": blk,
                        "rows": [{"centre_L4": r["centre"], "r": r["r"], "peak": r["peak"],
                                  "delta_L4": r["delta"], "ok": bool(o)} for r, o in zip(rows, ok)],
                        "fit_rms_L4": af["rms"], "M": af["M"]}}


# --------------------------------------------------------------------------
# stage: patches (fixed before any level-0 read)
# --------------------------------------------------------------------------
def stage_patches(scroll):
    meta = jload(WORK / scroll / "meta.json")
    co = jload(WORK / scroll / "coarse.json")
    tr = c6.C6Transform.from_fit(co["coarse_transform"])
    A4 = np.asarray(fetch_level(scroll, "v9", 4), np.float32)
    band = co["band_coarse"]
    z_lo, z_hi = band["z9_common_all_columns"]
    cxy = np.array(band["rescan_centre_xy9"])
    rad = band["rescan_disc_radius_9um_vox"]
    half = np.array(BLOCK[::-1]) / 2.0  # xyz half-extent
    margin_z = half[2] + 24  # keep blocks and control margins inside the band
    # papyrus score at level 4: local mean over the block footprint
    sm = ndi.uniform_filter(A4, size=(3, 16, 16))
    thr = np.percentile(A4[A4 > 0], 50) if (A4 > 0).any() else 0
    rng = np.random.default_rng(SEED)
    cand = []
    for _ in range(40000):
        z = rng.uniform(z_lo + margin_z, z_hi - margin_z)
        r = rad * math.sqrt(rng.uniform(0.0, 0.80 ** 2))  # stay inside 80 % of the rescan disc
        a = rng.uniform(0, 2 * math.pi)
        p = np.array([cxy[0] + r * math.cos(a), cxy[1] + r * math.sin(a), z])
        i4 = np.round((p[::-1] - 7.5) / 16.0).astype(int)
        if np.any(i4 < 0) or np.any(i4 >= np.array(A4.shape)):
            continue
        if sm[tuple(i4)] < thr:
            continue
        # the 9 um block must be inside the 9 um volume
        lo = p - half
        hi = p + half
        if np.any(lo < 0) or np.any(hi > np.array(meta["v9"]["levels"]["0"]["shape"][::-1]) - 1):
            continue
        cand.append(p)
    cand = np.array(cand)
    # farthest-point sampling of 40 locations, scaled z so layers spread evenly
    sc = np.array([1.0, 1.0, 2.0])
    chosen = [int(rng.integers(len(cand)))]
    d = np.linalg.norm((cand - cand[chosen[0]]) * sc, axis=1)
    while len(chosen) < N_FIT + N_CHECK:
        j = int(np.argmax(d))
        chosen.append(j)
        d = np.minimum(d, np.linalg.norm((cand - cand[j]) * sc, axis=1))
    P = np.round(cand[chosen], 1)
    idx = rng.permutation(len(P))
    fit = P[idx[:N_FIT]]
    chk = P[idx[N_FIT:]]
    dmin = float(np.min(np.linalg.norm(chk[:, None] - fit[None], axis=2)))
    out = {"scroll": scroll, "utc": utc(), "seed": SEED, "block_zyx": BLOCK,
           "fit_centres_xyz": fit, "check_centres_xyz": chk,
           "min_check_to_fit_distance_vox": dmin,
           "selection": "uniform in the rescan band (z inside common band - 48 vox, r <= 0.8 disc), "
                        "papyrus mean >= median of non-zero 9um L4, farthest-point 40, random 24/16 split",
           "n_candidates": len(cand), "control_criterion": {
               "min_median_drop": CTRL_MIN_MEDIAN_DROP, "min_frac_lower": CTRL_MIN_FRAC_LOWER}}
    jdump(out, WORK / scroll / "patches.json")
    jdump(out, LOGS / scroll / "patches.json")
    say(scroll, "patches", len(fit), len(chk), "min check-fit distance", dmin)
    return out


# --------------------------------------------------------------------------
# stage: mid (9 um level 1 vs rescan level 2)
# --------------------------------------------------------------------------
def stage_mid(scroll, iters=2):
    meta = jload(WORK / scroll / "meta.json")
    co = jload(WORK / scroll / "coarse.json")
    pt = jload(WORK / scroll / "patches.json")
    tr0 = c6.C6Transform.from_fit(co["coarse_transform"])
    r9 = ZReader(open_level(PAIRS[scroll]["v9"], 1))
    rrw = ZReader(open_level(PAIRS[scroll]["vr"], 2))
    Pf0 = np.array(pt["fit_centres_xyz"])
    blk = (32, 128, 128)  # level-1 voxels = 64 x 256 x 256 level-0 9 um voxels
    hist = []
    tr = tr0
    for it in range(iters):
        trk = level_transform(tr, 1, 2)
        trk.raw_shape = rrw.shape
        rr = c6.OrientedReader(rrw, rrw.shape, trk.orientation)
        Pk = (Pf0 - 0.5) / 2.0
        with ThreadPoolExecutor(3) as ex:
            rows = list(ex.map(lambda c: c6._measure_patch(r9, rr, trk, c, blk, 10, True), Pk))
        C = np.array([r["centre"] for r in rows])
        T = np.array([r["t_meas"] for r in rows])
        ok = np.array([r["ok"] and r["r"] > 0.3 and np.all(np.isfinite(r["t_meas"])) for r in rows])
        af = c6.fit_affine(C[ok], T[ok], Pm=trk.Pm)
        e = np.linalg.norm(T - ((C - trk.Pm) @ af["M"].T + af["b"]), axis=1)
        thr = max(1.0, 3 * 1.4826 * float(np.median(e[ok])))
        keep = ok & (e <= thr)
        if 6 <= keep.sum() < ok.sum():
            af = c6.fit_affine(C[keep], T[keep], Pm=trk.Pm)
        new = c6.C6Transform(trk.F, trk.z0, af["M"], af["b"], trk.Pm, trk.orientation, trk.raw_shape)
        tr = level0_transform(new, tr0.F, 1, 2, tr0.raw_shape)
        hist.append({"iteration": it + 1, "n_ok": int(ok.sum()), "n_used": int(keep.sum()),
                     "rms_L1": af["rms"], "median_r": float(np.median([r["r"] for r in rows if r["ok"]])),
                     "rows": [{"centre_L1": r["centre"], "r": r["r"], "peak": r["peak"],
                               "delta_L1": r["delta"], "used": bool(k)} for r, k in zip(rows, keep)]})
        say(f"mid iter {it + 1}: ok {ok.sum()} used {keep.sum()} rms_L1 {af['rms']:.3f} "
            f"median r {hist[-1]['median_r']:.3f}  bytes {rrw.bytes / 1e9:.2f} GB")
    out = {"scroll": scroll, "utc": utc(), "block_L1": blk, "history": hist,
           "transform": tr_json(tr), "band": band_extents(tr, meta)}
    jdump(out, WORK / scroll / "mid.json")
    jdump(out, LOGS / scroll / "mid.json")
    return out


# --------------------------------------------------------------------------
# stage: fine (level 0)
# --------------------------------------------------------------------------
def local_pitch(A, max_lag=40):
    """Local sheet pitch (9 um voxels) and sheet-normal unit vector (x, y, z).

    Normal: dominant eigenvector of the gradient structure tensor (sigma 1.5).
    Pitch: first local maximum (lag 4..max_lag) of the block's windowed
    autocorrelation sampled along the normal (profile smoothed over 3 lags);
    if there is none, twice the lag of the first local minimum; if neither,
    the 3-D power-spectrum peak (periods 4-60).  Returns (pitch, normal, info).
    """
    X = np.asarray(A, np.float64)
    X = np.where(np.isfinite(X), X, np.nanmean(X))
    g = np.gradient(ndi.gaussian_filter(X, 1.5))
    J = np.array([[np.mean(gi * gj) for gj in g] for gi in g])
    w, v = np.linalg.eigh(J)
    n_zyx = v[:, -1]
    Xc = (X - X.mean()) * c6._window3(X.shape)
    P = np.abs(sfft.fftn(Xc, workers=2)) ** 2
    ac = np.fft.fftshift(np.real(sfft.ifftn(P, workers=2)))
    ac /= ac.max()
    lags = np.arange(0, max_lag + 1, 1.0)
    ctr = np.array(ac.shape) // 2
    prof = ndi.map_coordinates(ac, (np.outer(lags, n_zyx) + ctr).T, order=1)
    sm = np.convolve(prof, np.ones(3) / 3, mode="same")
    info = {"eig_ratio": (w / w.max()).tolist(), "ac_profile": np.round(prof, 4).tolist()}
    pitch = None
    for L in range(4, max_lag):
        if sm[L] > sm[L - 1] and sm[L] >= sm[L + 1]:
            # parabolic peak
            den = sm[L - 1] - 2 * sm[L] + sm[L + 1]
            pitch = L + (0.5 * (sm[L - 1] - sm[L + 1]) / den if den < 0 else 0.0)
            info["method"] = "autocorrelation_first_max"
            break
    if pitch is None:
        for L in range(2, max_lag // 2):
            if sm[L] < sm[L - 1] and sm[L] <= sm[L + 1]:
                pitch = 2.0 * L
                info["method"] = "autocorrelation_2x_first_min"
                break
    if pitch is None:
        fz, fy, fx = np.meshgrid(*[sfft.fftfreq(n) for n in X.shape], indexing="ij")
        f = np.sqrt(fz ** 2 + fy ** 2 + fx ** 2)
        Pb = np.where((f >= 1 / 60) & (f <= 1 / 4), P, 0)
        i = np.unravel_index(int(np.argmax(Pb)), P.shape)
        pitch = 1.0 / f[i]
        info["method"] = "spectrum_peak"
    info["ac_at_half_pitch"] = float(np.interp(pitch / 2, lags, prof))
    n_xyz = n_zyx[::-1] / np.linalg.norm(n_zyx)
    return float(pitch), n_xyz, info


def measure_fine(r9, rrw, tr, centre_xyz, do_control, ctrl_margin=48):
    """Level-0 measurement at one patch. The raw rescan block (with a margin for
    the control) is read once; aligned and control samples come from it."""
    t0 = time.perf_counter()
    block = np.asarray(BLOCK, int)
    lo9 = c6._block_lo(centre_xyz, block)
    A = r9(lo9, lo9 + block)
    pitch, kdir, pinfo = local_pitch(A)
    ctrl_off = 0.5 * pitch * kdir
    # raw box covering aligned + control sampling, with margin
    corners = np.array([[lo9[2] + dx, lo9[1] + dy, lo9[0] + dz]
                        for dz in (0, block[0]) for dy in (0, block[1]) for dx in (0, block[2])], float)
    q = c6.map_9_to_r(np.vstack([corners, corners + ctrl_off]), tr_json(tr), frame="raw")  # xyz
    m = ctrl_margin
    rlo = np.floor(q.min(0)[::-1]).astype(int) - m
    rhi = np.ceil(q.max(0)[::-1]).astype(int) + m
    raw = rrw(rlo, rhi)
    br = BlockReader(raw, rlo, rrw.shape)
    rr = c6.OrientedReader(br, rrw.shape, tr.orientation)
    t_read = time.perf_counter() - t0
    row = c6._measure_patch(r9_cached(A, lo9), rr, tr, centre_xyz, block, 10, True)
    row["pitch"] = pitch
    row["pitch_dir_xyz"] = kdir
    row["pitch_info"] = pinfo
    row["read_seconds"] = t_read
    row["raw_box_zyx"] = [rlo, rhi]
    if do_control:
        D = c6._sample_rescan(rr, tr.with_offset(ctrl_off), lo9, block)
        row["r_ctrl"] = c6.ncc(A, D)
        row["ctrl_offset_xyz"] = ctrl_off
    row["seconds"] = time.perf_counter() - t0
    return row


def r9_cached(A, lo9):
    def rd(lo, hi):
        lo = np.asarray(lo) - lo9
        hi = np.asarray(hi) - lo9
        return A[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    return rd


def stage_fine(scroll, phase):
    """phase 'fit': 24 fit patches at the mid transform -> affine (iterated once
    more if the update exceeds 0.25 vox); phase 'check': 16 NEW patches + control."""
    meta = jload(WORK / scroll / "meta.json")
    pt = jload(WORK / scroll / "patches.json")
    r9 = ZReader(open_level(PAIRS[scroll]["v9"], 0))
    rrw = ZReader(open_level(PAIRS[scroll]["vr"], 0))
    ck = WORK / scroll / f"fine_{phase}_rows.json"
    done = jload(ck) if ck.exists() else {}
    iteration = 1
    if phase == "refit":
        prev = jload(WORK / scroll / "fine_fit.json")
        iteration = int(prev.get("iteration", 1)) + 1
        jdump(prev, WORK / scroll / f"fine_fit_iter{iteration - 1}.json")
        jdump(prev, LOGS / scroll / f"fine_fit_iter{iteration - 1}.json")
        tr = c6.C6Transform.from_fit(prev["transform"])
        P = np.array(pt["fit_centres_xyz"])
        do_ctrl = True
        phase = "fit"
        ck = WORK / scroll / "fine_fit_rows.json"
        done = jload(ck) if ck.exists() else {}
    elif phase == "fit":
        mid = jload(WORK / scroll / "mid.json")
        tr = c6.C6Transform.from_fit(mid["transform"])
        P = np.array(pt["fit_centres_xyz"])
        do_ctrl = True
    elif phase == "check_fititer1":
        # orchestrator 2026-09-26: check with the committed iteration-1 fit (sha256 bcb9c43f...)
        fit = jload(WORK / scroll / "fine_fit_iter1.json")
        tr = c6.C6Transform.from_fit(fit["transform"])
        P = np.array(pt["check_centres_xyz"])
        do_ctrl = True
    else:
        fit = jload(WORK / scroll / "fine_fit.json")
        tr = c6.C6Transform.from_fit(fit["transform"])
        P = np.array(pt["check_centres_xyz"])
        do_ctrl = True
    key = hashlib.sha256(json.dumps(c6._jsonify(tr_json(tr)), sort_keys=True).encode()).hexdigest()[:16]
    if done.get("transform_key") != key:
        done = {"transform_key": key, "rows": {}}
    todo = [i for i in range(len(P)) if str(i) not in done["rows"]]
    say(scroll, phase, "patches to do", len(todo), "of", len(P))
    with ThreadPoolExecutor(2) as ex:
        futs = {i: ex.submit(measure_fine, r9, rrw, tr, P[i], do_ctrl) for i in todo}
        for i in todo:
            row = futs[i].result()
            done["rows"][str(i)] = c6._jsonify(row)
            jdump(done, ck)
            say(f"{scroll} {phase} #{i}: r={row['r']:.3f} ctrl={row.get('r_ctrl', float('nan')):.3f} "
                f"delta={np.round(row['delta'], 2)} pitch={row['pitch']:.1f} peak={row['peak']:.3f} "
                f"{row['seconds']:.0f}s ({row['read_seconds']:.0f}s read) GB={rrw.bytes / 1e9:.1f}")
    rows = [done["rows"][str(i)] for i in range(len(P))]
    C = np.array([r["centre"] for r in rows], float)
    T = np.array([[np.nan] * 3 if r["t_meas"] is None else r["t_meas"] for r in rows], float)
    rs = np.array([np.nan if r["r"] is None else r["r"] for r in rows])
    rc = np.array([np.nan if r.get("r_ctrl") is None else r["r_ctrl"] for r in rows])
    out = {"scroll": scroll, "utc": utc(), "phase": phase, "iteration": iteration,
           "transform_used": tr_json(tr),
           "rows": rows, "median_r": float(np.nanmedian(rs)), "median_r_ctrl": float(np.nanmedian(rc)),
           "median_drop": float(np.nanmedian(rs - rc)),
           "frac_ctrl_lower": float(np.mean(rc < rs))}
    if phase == "fit":
        ok = np.array([r["ok"] for r in rows]) & np.all(np.isfinite(T), axis=1)
        af = c6.fit_affine(C[ok], T[ok], Pm=tr.Pm)
        e = np.linalg.norm(T - ((C - tr.Pm) @ af["M"].T + af["b"]), axis=1)
        thr = max(1.0, 3 * 1.4826 * float(np.nanmedian(e[ok])))
        used = ok & (e <= thr)
        if 6 <= used.sum() < ok.sum():
            af = c6.fit_affine(C[used], T[used], Pm=tr.Pm)
        new = c6.C6Transform(tr.F, tr.z0, af["M"], af["b"], tr.Pm, tr.orientation, tr.raw_shape)
        change = float(np.max(np.linalg.norm(new.t(C[used]) - tr.t(C[used]), axis=1)))
        res = T - new.t(C)
        out.update({"transform": tr_json(new), "fit_rms": af["rms"], "n_used": int(used.sum()),
                    "used": used, "fit_residuals_xyz": res, "update_max_vox": change,
                    "band": band_extents(new, meta)})
        say(f"{scroll} fit: rms {af['rms']:.3f} used {used.sum()} update {change:.3f} vox")
    else:
        res = np.array([[np.nan] * 3 if r["delta"] is None else r["delta"] for r in rows], float)
        ok = np.array([r["ok"] for r in rows]) & np.all(np.isfinite(res), axis=1)
        rms = float(np.sqrt(np.mean(np.sum(res[ok] ** 2, axis=1))))
        med = float(np.nanmedian(rs[ok]))
        drop_ok = (out["median_drop"] >= CTRL_MIN_MEDIAN_DROP) and (out["frac_ctrl_lower"] >= CTRL_MIN_FRAC_LOWER)
        out.update({"n_ok": int(ok.sum()), "heldout_median_r": med, "heldout_rms_vox": rms,
                    "median_abs_residual_xyz": np.median(np.abs(res[ok]), axis=0),
                    "bars": {"median_r_min": c6.BAR_MEDIAN_R, "rms_max": c6.BAR_RMS_VOX,
                             "median_r_ok": med >= c6.BAR_MEDIAN_R, "rms_ok": rms <= c6.BAR_RMS_VOX,
                             "control_drop_ok": bool(drop_ok),
                             "pass": bool(med >= c6.BAR_MEDIAN_R and rms <= c6.BAR_RMS_VOX and drop_ok)}})
        say(f"{scroll} CHECK: median r {med:.4f} rms {rms:.3f} ctrl median {out['median_r_ctrl']:.3f} "
            f"drop {out['median_drop']:.3f} frac {out['frac_ctrl_lower']:.2f} pass {out['bars']['pass']}")
    name = {"fit": "fine_fit.json", "check_fititer1": "fine_check_fititer1.json"}.get(phase, "fine_check.json")
    jdump(out, WORK / scroll / name)
    jdump(out, LOGS / scroll / name)
    return out


def stage_ceiling(scroll):
    """DIAGNOSTIC ONLY (does not change any verdict): r at each check patch's own
    measured optimum (final affine + that patch's residual shift), i.e. the
    best r any registration could give on that block. Separates registration
    error from contrast differences between the two scans."""
    chk = jload(WORK / scroll / "fine_check.json")
    fit = jload(WORK / scroll / "fine_fit.json")
    tr = c6.C6Transform.from_fit(fit["transform"])
    r9 = ZReader(open_level(PAIRS[scroll]["v9"], 0))
    rrw = ZReader(open_level(PAIRS[scroll]["vr"], 0))

    def one(row):
        d = np.array(row["delta"], float)
        t2 = tr.with_offset(d)  # constant offset: exact at this patch centre
        m = measure_fine(r9, rrw, t2, row["centre"], False)
        return {"centre": row["centre"], "r_affine": row["r"], "r_at_own_optimum": m["r"],
                "residual_after_xyz": m["delta"]}
    with ThreadPoolExecutor(2) as ex:
        out = list(ex.map(one, chk["rows"]))
    ra = np.array([o["r_affine"] for o in out])
    ro = np.array([o["r_at_own_optimum"] for o in out])
    res = {"scroll": scroll, "utc": utc(), "diagnostic_only": True, "rows": out,
           "median_r_affine": float(np.median(ra)), "median_r_own_optimum": float(np.median(ro)),
           "median_gain": float(np.median(ro - ra))}
    jdump(res, WORK / scroll / "ceiling.json")
    jdump(res, LOGS / scroll / "ceiling.json")
    say(scroll, f"ceiling: median r affine {res['median_r_affine']:.4f} own-optimum {res['median_r_own_optimum']:.4f}")
    return res


def homogeneous(tr: c6.C6Transform):
    """4x4 matrices (x, y, z, 1): 9 um voxel -> stored rescan voxel, and inverse."""
    I = np.eye(3)
    lin = tr.F * (I + tr.M)
    off = tr.F * (tr.b - tr.M @ tr.Pm - tr.z0 * np.array([0.0, 0.0, 1.0]))
    G = tr.orientation.G_xyz().astype(float)
    raw_xyz = np.array(tr.raw_shape[::-1], float)
    o = np.where(np.array(tr.orientation.flip_signs_xyz()) < 0, raw_xyz - 1, 0.0)
    # q_raw = G q_can + o' where o' is o placed on the raw axes
    o_raw = np.zeros(3)
    for k, (a, sgn) in enumerate(zip(tr.orientation.perm_xyz(), tr.orientation.flip_signs_xyz())):
        o_raw[a] = (raw_xyz[a] - 1) if sgn < 0 else 0.0
    H = np.eye(4)
    H[:3, :3] = G @ lin
    H[:3, 3] = G @ off + o_raw
    return H, np.linalg.inv(H)


def stage_final(scroll):
    meta = jload(WORK / scroll / "meta.json")
    co = jload(WORK / scroll / "coarse.json")
    mid = jload(WORK / scroll / "mid.json")
    fit = jload(WORK / scroll / "fine_fit.json")
    chk = jload(WORK / scroll / "fine_check.json")
    tr = c6.C6Transform.from_fit(fit["transform"])
    H, Hi = homogeneous(tr)
    # self-check: homogeneous == c6.map_9_to_r
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 6000, (100, 3))
    q1 = c6.map_9_to_r(p, fit["transform"], frame="raw")
    q2 = (np.c_[p, np.ones(len(p))] @ H.T)[:, :3]
    Mm = tr.M
    # small-angle decomposition of M (for reporting): rotation vector and strain
    W = 0.5 * (Mm - Mm.T)
    S = 0.5 * (Mm + Mm.T)
    rotvec_deg = np.degrees([W[2, 1], W[0, 2], W[1, 0]])
    zaxis = (np.eye(3) + Mm) @ np.array([0.0, 0.0, 1.0])
    tilt_deg = np.degrees(np.arctan2(np.linalg.norm(zaxis[:2]), zaxis[2]))
    out = {
        "scroll": scroll, "utc": utc(), "provenance": PROV,
        "volume_9um": meta["v9"]["path"], "volume_rescan": meta["vr"]["path"],
        "voxel_9um_um": meta["v9"]["voxel_um"], "voxel_rescan_um": meta["vr"]["voxel_um"],
        "metadata_sha256": {"v9": meta["v9"]["metadata_json_sha256"], "vr": meta["vr"]["metadata_json_sha256"]},
        "F_from_metadata": meta["F"],
        "model": "q_can = F (p + M (p - Pm) + b - z0 e_z); q_raw = G q_can + o; p, q in (x, y, z) voxel "
                 "centres of level 0 (9 um volume / stored rescan array)",
        "transform": fit["transform"],
        "H_9um_to_rescan_raw_xyz1": H, "H_rescan_raw_to_9um_xyz1": Hi,
        "homogeneous_selfcheck_max_abs_diff": float(np.abs(q1 - q2).max()),
        "remount": co["remount"], "remount_600um_best": co["remount_600um"]["best"],
        "remount_600um_margin": co["remount_600um"]["margin"],
        "remount_600um_runner_up": co["remount_600um"]["runner_up_distinct"],
        "zband_300um": {k: v for k, v in co["zband_300um"].items() if k != "profile_max_ncc_per_z_bin2"},
        "M_decomposition": {"rotation_vector_deg_xyz": rotvec_deg, "symmetric_strain": S,
                            "z_axis_tilt_deg": float(tilt_deg), "trace_M": float(np.trace(Mm))},
        "band": fit["band"],
        "fit": {"n": len(fit["rows"]), "n_used": fit["n_used"], "rms_vox": fit["fit_rms"],
                "update_max_vox": fit["update_max_vox"], "median_r": fit["median_r"],
                "patches": [{"centre_xyz": r["centre"], "r": r["r"], "r_ctrl": r.get("r_ctrl"),
                             "residual_xyz": res, "used": bool(u), "pitch_vox": r["pitch"],
                             "peak": r["peak"]}
                            for r, res, u in zip(fit["rows"], fit["fit_residuals_xyz"], fit["used"])]},
        "check": {"n": len(chk["rows"]), "n_ok": chk["n_ok"], "heldout_median_r": chk["heldout_median_r"],
                  "heldout_rms_vox": chk["heldout_rms_vox"],
                  "median_abs_residual_xyz": chk["median_abs_residual_xyz"],
                  "control_median_r": chk["median_r_ctrl"], "control_median_drop": chk["median_drop"],
                  "control_frac_lower": chk["frac_ctrl_lower"],
                  "patches": [{"centre_xyz": r["centre"], "r": r["r"], "r_ctrl": r.get("r_ctrl"),
                               "residual_xyz": r["delta"], "ctrl_offset_xyz": r.get("ctrl_offset_xyz"),
                               "pitch_vox": r["pitch"], "peak": r["peak"], "valid_frac": r["valid_frac"]}
                              for r in chk["rows"]]},
        "bars": chk["bars"],
        "mid_level_history": [{k: v for k, v in h.items() if k != "rows"} for h in mid["history"]],
    }
    # model comparison on the held-out patches (no extra reads): measured t at the
    # check centres = t_final + residual; compare with a translation-only model and
    # a rigid-free affine fitted to the same 24 fit patches (final iteration).
    Cf = np.array([r["centre"] for r in fit["rows"]], float)
    Tf = np.array([r["t_meas"] for r in fit["rows"]], float)
    uf = np.array(fit["used"], bool)
    Cc = np.array([r["centre"] for r in chk["rows"]], float)
    Tc = np.array([np.nan * np.ones(3) if r["delta"] is None else np.array(r["t_est"]) + np.array(r["delta"])
                   for r in chk["rows"]], float)
    okc = np.all(np.isfinite(Tc), axis=1)
    b_tr = Tf[uf].mean(0)
    rms = lambda R_: float(np.sqrt(np.mean(np.sum(R_ ** 2, axis=1))))
    out["model_comparison_heldout"] = {
        "translation_only_rms_vox": rms(Tc[okc] - b_tr),
        "translation_only_max_vox": float(np.max(np.linalg.norm(Tc[okc] - b_tr, axis=1))),
        "affine_rms_vox": rms(Tc[okc] - tr.t(Cc[okc])),
        "note": "residual shifts of the 16 check patches vs each model fitted to the 24 fit patches"}
    jdump(out, LOGS / scroll / "final_affine.json")
    say(scroll, "final: pass", out["bars"]["pass"], "selfcheck", out["homogeneous_selfcheck_max_abs_diff"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["meta", "coarse", "patches", "mid", "fit", "refit", "check", "check_fititer1", "final", "ceiling"])
    ap.add_argument("scroll", choices=sorted(PAIRS))
    a = ap.parse_args(argv)
    say("start", a.stage, a.scroll)
    if a.stage == "meta":
        stage_meta(a.scroll)
    elif a.stage == "coarse":
        stage_coarse(a.scroll)
    elif a.stage == "patches":
        stage_patches(a.scroll)
    elif a.stage == "mid":
        stage_mid(a.scroll)
    elif a.stage == "final":
        stage_final(a.scroll)
    elif a.stage == "ceiling":
        stage_ceiling(a.scroll)
    else:
        stage_fine(a.scroll, a.stage)
    say("done", a.stage, a.scroll)


if __name__ == "__main__":
    main()
