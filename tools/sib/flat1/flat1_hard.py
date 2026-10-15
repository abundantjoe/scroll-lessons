# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-1 HARD set (orchestrator request 2026-09-25T19:11Z): rectangles at the
most curved / least isometric parts of organizer meshes. Geometry only.

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/flat1_hard.py

Rules (fixed in code before any hard-set flattening was run):
* Pools. BANK: every PHerc0139 candidate segment of the primary run (38,
  9.362 um organizer tifxyz). ELIGIBLE: every PHerc0800 and PHerc1447
  segment folder with a ``-on-<volume>-8.64um.tifxyz`` organizer mesh
  (geometry only: no volume, image, label or ink is read; nothing is trained).
* Every mesh is levelled (level_mesh, step 20 vox, median). Windows are
  4.00 cm^2 nominal, aspect 1.5 (w = round(1.5 h)), fully valid.
* Two window scores, computed for every fully valid window position with
  integral images:
  H1 curvature = mean |angle defect| (deg) over the window's interior vertices;
  H2 non-isometry = fraction of window quads NOT having all four 3-D edges
  within +-5 % of the nominal step (i.e. the grid baseline failure rate).
  Per mesh, the argmax window of each score is taken, then the width is
  adjusted (+-1..3 columns) to reach 4.00 cm^2 +-1 %; if impossible the
  next-best window (up to 200) is tried.
* BANK hard set = the 5 meshes with the highest H1 window + the 5 meshes with
  the highest H2 window (a mesh may appear in both). ELIGIBLE set = every
  eligible mesh that fits a 4 cm^2 window, both H1 and H2 windows.
* Amendment A1 (after the first scan showed that no eligible mesh fits a
  fully valid 4 cm^2 aspect-1.5 window, before any eligible flattening):
  for ELIGIBLE meshes only, the target falls back to the largest of 3, 2,
  1 cm^2 that fits; such cases are labelled with their area and are NOT
  FLAT-1-size results.
* Methods: vc_flatten (official ABF++ defaults), SLIM, ARAP (grid init),
  grid baseline; plus the 2 mm margin + trim fallback (SLIM).
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import flat1_run as RUN
import flatlib as FL
from hercules.geometry import level_mesh as LM
from hercules.geometry import tifxyz as T
from hercules.pipeline.window import voxel_size_from_metadata

ASPECT = 1.5
N_TOP = 5
ELIGIBLE = {"PHerc0800": "20250521135224-8.640um-1.2m-116keV-masked.zarr",
            "PHerc1447": "20250521151220-8.640um-1.2m-116keV-masked.zarr"}
HW = RUN.WORK / "hard"


def vertex_defect_deg(points: np.ndarray) -> np.ndarray:
    """(H, W) |angle defect| in degrees at interior vertices whose 6 incident
    triangles all exist (NaN elsewhere)."""
    m = FL.grid_to_mesh(points)
    ang = FL._tri_angles(m.V[m.F])
    s = np.zeros(m.V.shape[0])
    cnt = np.zeros(m.V.shape[0])
    for k in range(3):
        np.add.at(s, m.F[:, k], ang[:, k])
        np.add.at(cnt, m.F[:, k], 1)
    H, W = points.shape[:2]
    out = np.full((H, W), np.nan)
    ok = m.index >= 0
    idx = m.index[ok]
    d = np.where(cnt[idx] == 6, np.degrees(np.abs(2 * np.pi - s[idx])), np.nan)
    out[ok] = d
    out[0, :] = out[-1, :] = np.nan
    out[:, 0] = out[:, -1] = np.nan
    return out


def _box(a: np.ndarray, h: int, w: int) -> np.ndarray:
    S = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
    S[1:, 1:] = a.cumsum(0).cumsum(1)
    return S[h:, w:] - S[:-h, w:] - S[h:, :-w] + S[:-h, :-w]


def hard_windows(points: np.ndarray, vox: float, target: float = RUN.TARGET_CM2) -> dict:
    q_cm = RUN.STEP_VOX * vox * 1e-4
    h = int(round(math.sqrt(target / ASPECT) / q_cm))
    w0 = int(round(ASPECT * h))
    qv = FL.quad_mask(points)
    if h > qv.shape[0] or w0 > qv.shape[1]:
        return {}
    full = _box(qv.astype(float), h, w0) == h * w0
    if not full.any():
        return {}
    # H1: per-quad mean of its corner defects (NaN -> 0 weight)
    d = vertex_defect_deg(points)
    dq = np.stack([d[:-1, :-1], d[1:, :-1], d[:-1, 1:], d[1:, 1:]], 0)
    dq_v = np.nan_to_num(dq).sum(0)
    dq_n = np.isfinite(dq).sum(0)
    h1 = _box(dq_v, h, w0) / np.maximum(_box(dq_n.astype(float), h, w0), 1)
    # H2: grid baseline failure at the nominal step
    ok = FL.quad_edge_ok(points, np.stack(np.meshgrid(np.arange(points.shape[1]), np.arange(points.shape[0])), -1)
                         .astype(float) * RUN.STEP_VOX, 0.05, 1.0) & qv
    h2 = 1.0 - _box(ok.astype(float), h, w0) / (h * w0)
    vox2 = 1.0 / (vox * 1e-4) ** 2
    out = {}
    for name, score in (("H1_curvature", h1), ("H2_nonisometry", h2)):
        sc = np.where(full, score, -np.inf)
        order = np.argsort(sc, axis=None)[::-1][:200]
        for flat in order:
            if not np.isfinite(sc.flat[flat]):
                break
            r0, c0 = np.unravel_index(flat, sc.shape)
            hit = None
            for dw in (0, 1, -1, 2, -2, 3, -3):
                w = w0 + dw
                if c0 + w > qv.shape[1] or w < h or w > 2 * h or not qv[r0:r0 + h, c0:c0 + w].all():
                    continue
                A = FL.rect_area_vox2(points, r0, c0, h, w) / vox2
                if abs(A - target) <= 0.01 * target:
                    hit = {"r0": int(r0), "c0": int(c0), "h_quads": h, "w_quads": w, "aspect": w / h, "area_cm2": A,
                           "score": float(sc.flat[flat]), "rule": name, "target_cm2": target}
                    break
            if hit:
                out[name] = hit
                break
    return out


def load_levelled(scroll: str, seg: str, vol_zarr: str, vol_tag: str, vol_sha: str | None, c, downloads) -> tuple:
    ts = seg.split("-")[0]
    vol_id = vol_zarr.split("-")[0]
    name = f"{ts}-on-{vol_id}-{vol_tag}.tifxyz"
    key = f"{scroll}/segments/{seg}/mesh/{name}/"
    d = HW / "s3" / scroll / seg / name
    files = ("meta.json", "x.tif", "y.tif", "z.tif")
    have = {o["Key"][len(key):]: o["Size"] for o in c.list_objects_v2(Bucket=RUN.BUCKET, Prefix=key).get("Contents", [])}
    if not all(f in have for f in files):
        return None, None
    d.mkdir(parents=True, exist_ok=True)
    for f in files:
        p = d / f
        if not p.exists() or p.stat().st_size != have[f]:
            c.download_file(RUN.BUCKET, key + f, str(p))
        downloads.append({"key": key + f, "size": p.stat().st_size, "sha256": RUN.sha256_file(p)})
    m = T.read_tifxyz(d)
    lev = LM.level_mesh(m.points, step_vox=RUN.STEP_VOX, method="median")
    return lev, str(d)


def vol_voxel(scroll: str, vol_zarr: str, c) -> tuple[float, str]:
    p = HW / "s3" / f"{scroll}_{vol_zarr}_metadata.json"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(c.get_object(Bucket=RUN.BUCKET, Key=f"{scroll}/volumes/{vol_zarr}/metadata.json")["Body"].read())
    return voxel_size_from_metadata(p), RUN.sha256_file(p)


def run_case(case: dict, lev: np.ndarray, vox: float) -> dict:
    cp = HW / "results" / f"{case['id']}.json"
    if cp.exists():
        return json.loads(cp.read_text())
    r = case["rect"]
    patch = lev[r["r0"]:r["r0"] + r["h_quads"] + 1, r["c0"]:r["c0"] + r["w_quads"] + 1].astype(np.float64)
    qe = FL.quad_mask(patch)
    res = dict(case)
    res["geometry"] = RUN.geometry_diagnostics(patch)
    res["methods"] = RUN.flatten_all(patch, "hard_" + case["id"], vox, qe, sensitivity=False)
    ab = res["methods"]["vc_flatten"]["info"]
    if ab["exit_code"] != 0 and "abfFlatten failed" not in ab.get("stdout_tail", ""):
        raise RuntimeError(f"ABF++ run did not execute (infrastructure, not a method result): {ab}")
    res["fallback"] = RUN.fallback(lev, r, vox, res["methods"]["slim"]["metrics"]["pct_quads_within_5pct"])
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(res, indent=1, default=float))
    print(case["id"], {k: round(v["metrics"]["pct_quads_within_5pct"], 2) for k, v in res["methods"].items()},
          "fb", round(res["fallback"]["after_pct"], 2), flush=True)
    return res


def main() -> None:
    c = RUN.s3()
    downloads, scan = [], []
    sel = json.loads((RUN.OUT / "selection.json").read_text())
    vox39 = sel["voxel_um"]
    levs = {}
    for seg in sel["candidates"]:
        lev, d = load_levelled("PHerc0139", seg, "20250728140407-9.362um-1.2m-113keV-masked.zarr", "9.362um", None, c, downloads)
        if lev is None:
            continue
        hw = hard_windows(lev.points, vox39)
        levs[("PHerc0139", seg)] = (lev.points, vox39)
        scan.append({"pool": "BANK", "scroll": "PHerc0139", "segment": seg, "voxel_um": vox39, "windows": hw,
                     "level_spread_deg": lev.spread_deg})
        print("scan", seg, {k: round(v["score"], 4) for k, v in hw.items()}, flush=True)
    vol_meta = {}
    for scroll, vz in ELIGIBLE.items():
        vox, sh = vol_voxel(scroll, vz, c)
        vol_meta[scroll] = {"volume": vz, "voxel_um": vox, "metadata_sha256": sh}
        r = c.list_objects_v2(Bucket=RUN.BUCKET, Prefix=f"{scroll}/segments/", Delimiter="/")
        for p in r.get("CommonPrefixes", []):
            seg = p["Prefix"].split("/")[-2]
            lev, d = load_levelled(scroll, seg, vz, "8.64um", None, c, downloads)
            if lev is None:
                scan.append({"pool": "ELIGIBLE", "scroll": scroll, "segment": seg, "windows": {}, "note": "no 8.64um tifxyz"})
                continue
            hw = {}
            for tgt in (4.0, 3.0, 2.0, 1.0):
                hw = hard_windows(lev.points, vox, tgt)
                if hw:
                    break
            levs[(scroll, seg)] = (lev.points, vox)
            scan.append({"pool": "ELIGIBLE", "scroll": scroll, "segment": seg, "voxel_um": vox, "windows": hw,
                         "area_cm2": T.area_cm2(lev.points, vox), "level_spread_deg": lev.spread_deg})
            print("scan", scroll, seg, round(T.area_cm2(lev.points, vox), 2), {k: round(v["score"], 4) for k, v in hw.items()}, flush=True)
    cases = []
    bank = [s for s in scan if s["pool"] == "BANK"]
    for rule in ("H1_curvature", "H2_nonisometry"):
        ranked = sorted([s for s in bank if rule in s["windows"]], key=lambda s: -s["windows"][rule]["score"])[:N_TOP]
        for s in ranked:
            tag = s["segment"].split("-")[1].split("_")[0]
            cases.append({"id": f"BANK_{rule[:2]}_{tag}", "pool": "BANK", "scroll": s["scroll"], "segment": s["segment"],
                          "rule": rule, "rect": s["windows"][rule]})
    for s in scan:
        if s["pool"] == "ELIGIBLE":
            for rule, w in s["windows"].items():
                cases.append({"id": f"ELIG_{rule[:2]}_{s['scroll']}_{s['segment'].split('-')[0]}", "pool": "ELIGIBLE",
                              "scroll": s["scroll"], "segment": s["segment"], "rule": rule, "rect": w})
    (RUN.OUT / "hard_selection.json").write_text(json.dumps({"vol_meta": vol_meta, "scan": scan, "cases": cases,
                                                             "downloads": downloads}, indent=1, default=float))
    results = []
    for case in cases:
        pts, vox = levs[(case["scroll"], case["segment"])]
        results.append(run_case(case, pts, vox))
    rows = []
    for r in results:
        rows.append({"id": r["id"], "pool": r["pool"], "rule": r["rule"], "score": r["rect"]["score"],
                     "area_cm2": r["rect"]["area_cm2"], "mean_abs_defect_deg": r["geometry"]["mean_abs_angle_defect_deg"],
                     **{m: r["methods"][m]["metrics"]["pct_quads_within_5pct"] for m in r["methods"]},
                     "flipped": {m: r["methods"][m]["metrics"]["flipped_triangles"] for m in r["methods"]},
                     "fallback_after": r["fallback"]["after_pct"]})
    summ = {"cases": rows}
    for pool in ("BANK", "ELIGIBLE"):
        sub = [x for x in rows if x["pool"] == pool]
        summ[f"n_{pool}"] = len(sub)
        summ[f"n_pass_{pool}"] = {m: int(sum(x[m] >= RUN.ADOPT_PCT for x in sub)) for m in ("vc_flatten", "slim", "arap", "grid_baseline", "fallback_after")}
    (RUN.OUT / "flat1_hard_summary.json").write_text(json.dumps(summ, indent=1, default=float))
    (RUN.OUT / "flat1_hard_results.json").write_text(json.dumps(results, indent=1, default=float))
    print(json.dumps({k: v for k, v in summ.items() if k != "cases"}, indent=1))


if __name__ == "__main__":
    main()
