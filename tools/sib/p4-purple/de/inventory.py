"""p4-purple-de A1: inventory of the 137 keV and 78 keV 2.4 um volumes (metadata only; no voxel read).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python inventory.py
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import dcommon as D  # noqa: E402

out = {"provenance": D.PROV, "serves": "brief_de.md item 1; PROTOCOL.md A1", "volumes": {}, "fetched_files": []}
NP = "not published"


def fetch(key):
    b = D.get(f"{D.BUCKET}/{key}")
    out["fetched_files"].append({"key": key, "bytes": None if b is None else len(b), "sha256": None if b is None else D.sha(b)})
    return b


def dig(d, *ks):
    for k in ks:
        if not isinstance(d, dict) or k not in d:
            return NP
        d = d[k]
    return d


for v in (D.V137, D.V78):
    base = f"PHercParis4/volumes/{v}.zarr"
    md = json.loads(fetch(f"{base}/metadata.json"))
    zat = fetch(f"{base}/.zattrs")
    fetch(f"{base}/.zgroup")
    tr = fetch(f"{base}/transform.json")
    acq = dig(md, "scan", "tomo", "acquisition")
    proc = dig(md, "scan", "tomo", "processing")
    ph = dig(proc, "preprocessing", "phase")
    ex = md.get("zarr_export", {})
    levels = {}
    for L in range(12):
        b = fetch(f"{base}/{L}/.zarray")
        if b is None:
            out["fetched_files"].pop()
            break
        za = json.loads(b)
        levels[str(L)] = {k: za.get(k) for k in ("shape", "chunks", "dtype", "compressor", "filters", "fill_value", "order",
                                               "dimension_separator")}
    E = float(acq["energy"])
    lam_m = 12.398419843320026 / E * 1e-10
    z_m = float(acq["sampleDetectorDistance"]) / 1000.0
    db = float(ph.get("delta_beta")) if isinstance(ph, dict) and "delta_beta" in ph else float("nan")
    a = math.pi * lam_m * z_m * db
    wmin, wmax = float(ex.get("target_window_f32_min", "nan")), float(ex.get("target_window_f32_max", "nan"))
    t = json.loads(tr) if tr else None
    reg = NP
    if t:
        M = np.array(t["transformation_matrix"], float)
        Fl, Ml = np.array(t["fixed_landmarks"], float), np.array(t["moving_landmarks"], float)
        res = np.linalg.norm((M[:, :3] @ Ml.T).T + M[:, 3] - Fl, axis=1)
        reg = {"fixed_volume": t.get("fixed_volume"), "matrix_moving_to_fixed_xyz": M.tolist(), "landmarks": len(Fl),
               "residual_fixed_vox_rms": float(np.sqrt((res ** 2).mean())), "residual_fixed_vox_max": float(res.max()),
               "other_keys": sorted(k for k in t if k not in ("transformation_matrix", "fixed_landmarks", "moving_landmarks"))}
    out["volumes"][v] = {
        "voxel_size_mm": dig(acq, "detector", "samplePixelSize"),
        "energy_keV_nominal": E,
        "energy_note": "BM18 filtered polychromatic beam; 'energy' is the nominal/mean energy; the spectrum is not published",
        "propagation_distance_mm": dig(acq, "sampleDetectorDistance"),
        "source_sample_distance_mm": dig(acq, "sourceSampleDistance"),
        "beamline": dig(acq, "beamline"), "machine_mode": dig(acq, "machineMode"),
        "scan_radix": dig(acq, "scanRadix"), "scan_type": dig(acq, "scanType"), "nb_scans": dig(acq, "nb_scans"),
        "start_date": dig(acq, "start_date"), "end_date": dig(acq, "end_date"),
        "helical_z_start_end_step_mm": [dig(acq, "z_start"), dig(acq, "z_end"), dig(acq, "z_step")],
        "tomo_N": dig(acq, "tomo_N"), "expo_time_s": dig(acq, "expo_time"), "half_acquisition": dig(acq, "half_acquisition"),
        "detector": {k: dig(acq, "detector", k) for k in ("sensor", "sensorPixelSize", "roi_size", "opticsName",
                                                            "optical_magnification", "scintillator", "samplePixelSize")},
        "attenuators_fields": dig(acq, "attenuators"), "attenuators_comment": dig(acq, "comment"),
        "reconstruction": {
            "workflow": dig(proc, "general", "WorkFlowScheme"),
            "phase_retrieval": ph if isinstance(ph, dict) else NP,
            "method": dig(proc, "reconstruction", "method"),
            "rotation_axis_position": dig(proc, "reconstruction", "rotation_axis_position"),
            "flat_field": dig(proc, "general", "FlatField"),
            "double_flat_ring_correction": dig(proc, "general", "DoubleFlatsScheme"),
            "double_flat_params": dig(proc, "preprocessing", "double_flat_field"),
            "detector_distortion_correction": dig(proc, "general", "DetectorDistortionCorrection"),
            "lut_path_scheme": dig(proc, "general", "LutPathScheme"),
            "other_filters": "not published (no explicit ring/other filter fields beyond the above)",
            "float32_histogram": dig(proc, "32bitsData", "histogram"),
            "float32_used_range_for_conversion": dig(proc, "postprocessing", "32BitsConversion"),
            "units_of_float_values": "not published",
        },
        "grey_scaling": {"export": ex, "dtype_level0": levels.get("0", {}).get("dtype"),
                         "u8_to_f32": f"f = {wmin} + g * ({wmax} - {wmin}) / 255",
                         "f32_per_grey_level": (wmax - wmin) / 255.0},
        "masking": md.get("masking", NP),
        "levels": levels,
        "transform": reg,
        "zattrs_sha256": D.sha(zat) if zat else NP,
        "derived": {"wavelength_m": lam_m, "paganin_a_m2": a,
                    "paganin_cutoff_period_um": math.sqrt(a) * 1e6,
                    "paganin_kernel_L_um (exp(-|x|/L) 1-D)": math.sqrt(a) / (2 * math.pi) * 1e6,
                    "transfer": "nabu Paganin 1 / (1 + pi lambda z (delta/beta) f^2), f in cycles/m"},
    }
    out["volumes"][v]["top_level_metadata_keys"] = sorted(md.keys())

json.dump(out, open(os.path.join(D.REPO, "logs/sib/p4-purple/de/inventory.json"), "w"), indent=1, default=str)
for v, d in out["volumes"].items():
    print(v, d["energy_keV_nominal"], d["reconstruction"]["phase_retrieval"], d["grey_scaling"]["u8_to_f32"], d["derived"])
